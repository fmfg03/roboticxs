from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime

from app.google_calendar_readonly_connector import (
    CalendarEventSnapshot,
    CalendarReadResult,
    GoogleCalendarHttpClientProtocol,
    run_google_calendar_readonly_connector,
)


REAL_CALENDAR_MEETING_BRIEF_STAGE = "135P"
DEFAULT_OWNER_ID = "local-owner"
DEFAULT_ROBOT_ID = "roboticxs-dev"
DEFAULT_CREATED_AT = "2026-06-24T00:00:00Z"
DEFAULT_MAX_MEETINGS = 3


@dataclass(frozen=True, slots=True)
class RealCalendarMeetingBriefRecord:
    stage: str
    owner_id: str
    robot_id: str
    calendar_id: str
    window_start: str
    window_end: str
    status: str
    selected_events: tuple[CalendarEventSnapshot, ...]
    headline: str
    meeting_summaries: tuple[str, ...]
    preparation_checklist: tuple[str, ...]
    watchpoints: tuple[str, ...]
    boundary_summary: tuple[str, ...]
    local_render_text: str
    read_only: bool
    calendar_writes: bool
    external_writes: bool
    memory_mutation: bool
    model_calls: bool
    tool_calls: bool
    worker_dispatch: bool
    error_code: str | None
    error_message: str | None
    created_at: str

    def __post_init__(self) -> None:
        if self.stage != REAL_CALENDAR_MEETING_BRIEF_STAGE:
            raise ValueError("rejected_invalid_stage")
        if not self.owner_id:
            raise ValueError("rejected_missing_owner_id")
        if not self.robot_id:
            raise ValueError("rejected_missing_robot_id")
        if any(
            (
                not self.read_only,
                self.calendar_writes,
                self.external_writes,
                self.memory_mutation,
                self.model_calls,
                self.tool_calls,
                self.worker_dispatch,
            )
        ):
            raise ValueError("rejected_unsafe_authority")


def _format_event_start(event: CalendarEventSnapshot) -> str:
    if event.all_day:
        return f"{event.start} (all day)"
    try:
        parsed = datetime.fromisoformat(event.start)
    except ValueError:
        return event.start
    return parsed.strftime("%Y-%m-%d %H:%M")


def _event_meeting_summary(event: CalendarEventSnapshot) -> str:
    location = event.location or "No location provided"
    attendees = f"{event.attendee_count} attendee(s)"
    return f"{_format_event_start(event)} - {event.summary} | {location} | {attendees}"


def _build_preparation_checklist(events: tuple[CalendarEventSnapshot, ...]) -> tuple[str, ...]:
    if not events:
        return ("No Calendar-backed meeting preparation is needed for this window.",)

    first = events[0]
    checklist = [
        f"Review the objective for {first.summary}.",
        "Check local context and prior notes before the meeting.",
        "List open questions that should be resolved during the meeting.",
        "Keep the brief local and do not modify Calendar or external systems.",
    ]
    if first.description_preview:
        checklist.insert(1, "Review the Calendar description preview for owner-provided context.")
    return tuple(checklist)


def _build_watchpoints(
    *,
    events: tuple[CalendarEventSnapshot, ...],
    result: CalendarReadResult,
) -> tuple[str, ...]:
    if not result.ok:
        return (
            f"Calendar read failed closed: {result.error_code or 'unknown_error'}.",
            "No external write was attempted.",
        )
    if not events:
        return ("No upcoming Calendar events were available in the configured window.",)

    watchpoints = []
    if any(event.attendee_count == 0 for event in events):
        watchpoints.append("At least one selected event has no attendee list in Calendar.")
    if any(event.location is None for event in events):
        watchpoints.append("At least one selected event has no location or meeting link.")
    if not watchpoints:
        watchpoints.append("No deterministic Calendar watchpoints were found.")
    return tuple(watchpoints)


def _render_brief(record: RealCalendarMeetingBriefRecord) -> str:
    lines = [
        "Real Calendar Meeting Brief",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Calendar: {record.calendar_id}",
        f"Window: {record.window_start} -> {record.window_end}",
        "Read-only: true",
        "Calendar writes: disabled",
        "External writes: disabled",
        "Memory mutation: disabled",
        "LLM/model calls: disabled",
        "Tools/workers: disabled",
        "",
        "Headline:",
        f"- {record.headline}",
        "",
        "Meetings:",
    ]
    if record.meeting_summaries:
        lines.extend(f"- {summary}" for summary in record.meeting_summaries)
    else:
        lines.append("- No meetings selected.")

    lines.extend(["", "Preparation checklist:"])
    lines.extend(f"- {item}" for item in record.preparation_checklist)
    lines.extend(["", "Watchpoints:"])
    lines.extend(f"- {item}" for item in record.watchpoints)
    lines.extend(["", "Boundaries:"])
    lines.extend(f"- {item}" for item in record.boundary_summary)
    lines.extend(["", "No external action was taken."])
    return "\n".join(lines)


def compose_real_calendar_meeting_brief(
    *,
    owner_id: str,
    robot_id: str,
    calendar_result: CalendarReadResult,
    created_at: str = DEFAULT_CREATED_AT,
    max_meetings: int = DEFAULT_MAX_MEETINGS,
) -> RealCalendarMeetingBriefRecord:
    if max_meetings <= 0:
        raise ValueError("rejected_invalid_max_meetings")

    selected_events = calendar_result.events[:max_meetings] if calendar_result.ok else ()
    meeting_summaries = tuple(_event_meeting_summary(event) for event in selected_events)

    if not calendar_result.ok:
        status = "blocked_calendar_unavailable"
        headline = "Calendar read was unavailable; no real Calendar meeting brief was composed."
    elif not selected_events:
        status = "completed_no_events"
        headline = "No upcoming meetings were found in the configured Calendar window."
    else:
        status = "completed"
        headline = f"Prepared a deterministic brief for {len(selected_events)} upcoming Calendar event(s)."

    boundary_summary = (
        "Used Google Calendar read-only snapshot only.",
        "Did not create, update, or delete Calendar events.",
        "Did not mutate Memory Center.",
        "Did not call an LLM, tool, or worker.",
        "Did not send Telegram, email, or any nonlocal message.",
    )

    record_without_render = RealCalendarMeetingBriefRecord(
        stage=REAL_CALENDAR_MEETING_BRIEF_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_id=calendar_result.calendar_id,
        window_start=calendar_result.window_start,
        window_end=calendar_result.window_end,
        status=status,
        selected_events=selected_events,
        headline=headline,
        meeting_summaries=meeting_summaries,
        preparation_checklist=_build_preparation_checklist(selected_events),
        watchpoints=_build_watchpoints(events=selected_events, result=calendar_result),
        boundary_summary=boundary_summary,
        local_render_text="",
        read_only=True,
        calendar_writes=False,
        external_writes=False,
        memory_mutation=False,
        model_calls=False,
        tool_calls=False,
        worker_dispatch=False,
        error_code=calendar_result.error_code,
        error_message=calendar_result.error_message,
        created_at=created_at,
    )

    return RealCalendarMeetingBriefRecord(
        **{
            field_name: getattr(record_without_render, field_name)
            for field_name in record_without_render.__dataclass_fields__
            if field_name != "local_render_text"
        },
        local_render_text=_render_brief(record_without_render),
    )


def run_real_calendar_meeting_brief(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
    http_client: GoogleCalendarHttpClientProtocol | None = None,
    created_at: str = DEFAULT_CREATED_AT,
) -> RealCalendarMeetingBriefRecord:
    calendar_result = run_google_calendar_readonly_connector(http_client=http_client)
    return compose_real_calendar_meeting_brief(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_result=calendar_result,
        created_at=created_at,
    )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = []
    if argv:
        print("Real Calendar Meeting Brief: failed", file=sys.stderr)
        print("Reason: this command does not accept arguments in 135P.", file=sys.stderr)
        return 2

    record = run_real_calendar_meeting_brief()
    print(record.local_render_text)
    return 0 if record.status in {"completed", "completed_no_events"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
