from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import (
    CalendarReadResult,
    GoogleCalendarHttpClientProtocol,
    run_google_calendar_readonly_connector,
)
from app.meeting_prep_pack import build_meeting_prep_pack, render_meeting_prep_pack
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)
from app.today_command import build_today_command_record, render_today_command


CALENDAR_BACKED_TODAY_PREP_STAGE = "162P"


@dataclass(frozen=True, slots=True)
class CalendarBackedTodayPrepRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    calendar_connected: bool
    calendar_id: str
    calendar_event_count: int
    prep_available: bool
    selected_suggestion_id: str | None
    source_lines: tuple[str, ...]
    unavailable_source_lines: tuple[str, ...]
    today_reply: str
    prep_reply: str
    read_only: bool
    calendar_write_allowed: bool
    gmail_read_allowed: bool
    gmail_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CALENDAR_BACKED_TODAY_PREP_STAGE:
            raise ValueError("162P Calendar-backed Today/Prep records must identify the 162P stage.")
        if not self.read_only:
            raise ValueError("162P Calendar-backed Today/Prep must be read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.gmail_read_allowed,
                self.gmail_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("162P Calendar-backed Today/Prep must not expand authority.")


def build_calendar_backed_today_prep_record(
    *,
    owner_id: str,
    robot_id: str,
    calendar_result: CalendarReadResult,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> CalendarBackedTodayPrepRecord:
    context_scan = build_calendar_context_scan_record(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_result=calendar_result,
    )
    suggestion_scan = build_proactive_meeting_suggestion_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        context_scan=context_scan,
    )
    memory_snapshot = build_memory_center_telegram_snapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        source_bundle=memory_source_bundle,
    )
    today_record = build_today_command_record(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    selected_suggestion_id = suggestion_scan.suggestions[0].suggestion_id if suggestion_scan.suggestions else None
    if selected_suggestion_id:
        prep_record = build_meeting_prep_pack(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id=selected_suggestion_id,
            suggestion_scan=suggestion_scan,
            memory_snapshot=memory_snapshot,
        )
        prep_reply = render_meeting_prep_pack(prep_record)
    else:
        prep_reply = _render_prep_unavailable(calendar_result=calendar_result)
    source_lines = _source_lines(calendar_result=calendar_result)
    unavailable_source_lines = _unavailable_source_lines(calendar_result=calendar_result)
    status = "calendar_connected" if calendar_result.ok else "calendar_unavailable"
    if calendar_result.ok and not selected_suggestion_id:
        status = "calendar_connected_no_prep_suggestion"
    return CalendarBackedTodayPrepRecord(
        stage=CALENDAR_BACKED_TODAY_PREP_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=status,
        calendar_connected=calendar_result.ok,
        calendar_id=calendar_result.calendar_id,
        calendar_event_count=len(calendar_result.events),
        prep_available=selected_suggestion_id is not None,
        selected_suggestion_id=selected_suggestion_id,
        source_lines=source_lines,
        unavailable_source_lines=unavailable_source_lines,
        today_reply=render_today_command(today_record),
        prep_reply=prep_reply,
        read_only=True,
        calendar_write_allowed=False,
        gmail_read_allowed=False,
        gmail_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def run_calendar_backed_today_prep(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> CalendarBackedTodayPrepRecord:
    calendar_result = run_google_calendar_readonly_connector(http_client=calendar_http_client)
    return build_calendar_backed_today_prep_record(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_result=calendar_result,
        memory_source_bundle=memory_source_bundle,
    )


def render_calendar_backed_today_prep_record(record: CalendarBackedTodayPrepRecord) -> str:
    lines = [
        "Calendar-Backed Today / Prep",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Calendar: {'connected' if record.calendar_connected else 'unavailable'}",
        f"Calendar id: {record.calendar_id}",
        f"Calendar events: {record.calendar_event_count}",
        f"Prep available: {'true' if record.prep_available else 'false'}",
        "",
        "Sources used:",
        *(f"- {line}" for line in record.source_lines),
        "",
        "Sources not connected:",
        *(f"- {line}" for line in record.unavailable_source_lines),
        "",
        "Today reply:",
        record.today_reply,
        "",
        "Prep reply:",
        record.prep_reply,
        "",
        "Boundaries:",
        "Calendar reads: read-only",
        "Calendar writes: disabled",
        "Gmail reads: disabled",
        "Gmail writes: disabled",
        "Memory Center mutation: disabled",
        "ProposedMemory writes: disabled",
        "Model calls: disabled",
        "Tools: disabled",
        "Worker dispatch: disabled",
        "External writes: disabled",
        "",
        "No external action was taken.",
    ]
    return "\n".join(lines)


def _source_lines(*, calendar_result: CalendarReadResult) -> tuple[str, ...]:
    if calendar_result.ok:
        return (
            f"Google Calendar read-only: connected ({len(calendar_result.events)} event(s)).",
            "Memory Center: local approval-mode visibility.",
        )
    return ("Memory Center: local approval-mode visibility.",)


def _unavailable_source_lines(*, calendar_result: CalendarReadResult) -> tuple[str, ...]:
    lines = ["Gmail: not connected."]
    if not calendar_result.ok:
        lines.insert(
            0,
            f"Google Calendar read-only: unavailable ({calendar_result.error_code or 'unknown_error'}).",
        )
    return tuple(lines)


def _render_prep_unavailable(*, calendar_result: CalendarReadResult) -> str:
    reason = "no Calendar-backed prep suggestion is available"
    if not calendar_result.ok:
        reason = f"Calendar read-only source unavailable: {calendar_result.error_code or 'unknown_error'}"
    return "\n".join(
        [
            "Meeting Prep Pack",
            "",
            "Status: blocked_calendar_backed_prep_unavailable",
            f"Reason: {reason}.",
            "",
            "Setup status:",
            "- Calendar: not connected; read-only setup required." if not calendar_result.ok else "- Calendar: connected read-only.",
            "- Gmail: not connected to the robot task inbox.",
            "- Memory: approval mode active.",
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Gmail reads: disabled",
            "Gmail writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.calendar_backed_today_prep")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = run_calendar_backed_today_prep()
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_calendar_backed_today_prep_record(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
