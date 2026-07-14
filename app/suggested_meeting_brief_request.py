from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol
from app.proactive_meeting_suggestion import (
    PROACTIVE_MEETING_SUGGESTION_STAGE,
    ProactiveMeetingBriefSuggestionRecord,
    ProactiveMeetingSuggestionScanRecord,
    run_proactive_meeting_suggestion_scan,
)


SUGGESTED_MEETING_BRIEF_REQUEST_STAGE = "139P"


@dataclass(frozen=True, slots=True)
class SuggestedMeetingBriefRequestRecord:
    stage: str
    owner_id: str
    robot_id: str
    suggestion_id: str
    status: str
    source_stage: str
    selected_suggestion: ProactiveMeetingBriefSuggestionRecord | None
    headline: str
    meeting_summary: str | None
    preparation_checklist: tuple[str, ...]
    watchpoints: tuple[str, ...]
    boundary_summary: tuple[str, ...]
    local_render_text: str
    owner_requested: bool
    suggestion_validated: bool
    read_only: bool
    automatic_execution: bool
    callback_binding_allowed: bool
    followup_intent_created: bool
    async_delegation_allowed: bool
    worker_dispatch_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    external_write_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    error_code: str | None

    def __post_init__(self) -> None:
        if self.stage != SUGGESTED_MEETING_BRIEF_REQUEST_STAGE:
            raise ValueError("139P requested suggested briefs must identify the 139P stage.")
        if self.source_stage != PROACTIVE_MEETING_SUGGESTION_STAGE:
            raise ValueError("139P requested suggested briefs must originate from 138P suggestions.")
        if not self.owner_requested:
            raise ValueError("139P requested suggested briefs require explicit owner request.")
        if not self.read_only:
            raise ValueError("139P requested suggested briefs must be read-only.")
        if any(
            (
                self.automatic_execution,
                self.callback_binding_allowed,
                self.followup_intent_created,
                self.async_delegation_allowed,
                self.worker_dispatch_allowed,
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.external_write_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
            )
        ):
            raise ValueError("139P requested suggested briefs must not expand authority.")


def build_suggested_meeting_brief_request(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
) -> SuggestedMeetingBriefRequestRecord:
    normalized_suggestion_id = suggestion_id.strip()
    if suggestion_scan.owner_id != owner_id or suggestion_scan.robot_id != robot_id:
        raise ValueError("rejected_suggestion_scan_owner_robot_mismatch")
    if suggestion_scan.suggestion_stage != PROACTIVE_MEETING_SUGGESTION_STAGE:
        raise ValueError("rejected_invalid_suggestion_scan_stage")
    if not normalized_suggestion_id:
        return _blocked_record(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id=normalized_suggestion_id,
            status="blocked_missing_suggestion_id",
            headline="No suggestion id was provided for the requested meeting brief.",
            error_code="missing_suggestion_id",
        )
    if suggestion_scan.status == "blocked_calendar_unavailable":
        return _blocked_record(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id=normalized_suggestion_id,
            status="blocked_calendar_unavailable",
            headline="Calendar context is unavailable; no suggested meeting brief was prepared.",
            error_code=suggestion_scan.error_code or "calendar_unavailable",
        )

    selected = next(
        (
            suggestion
            for suggestion in suggestion_scan.suggestions
            if suggestion.suggestion_id == normalized_suggestion_id
        ),
        None,
    )
    if selected is None:
        return _blocked_record(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id=normalized_suggestion_id,
            status="blocked_suggestion_not_found",
            headline="That suggestion is no longer available in the current Calendar context scan.",
            error_code="suggestion_not_found",
        )

    checklist = (
        f"Review the objective for {selected.event_summary}.",
        "Check local context and prior notes before the meeting.",
        "List open questions to resolve during the meeting.",
        "Run no external action from this brief without a separate approval path.",
    )
    watchpoints = (
        "The suggestion was revalidated against the current 138P scan.",
        "This brief was rendered only because the owner requested the suggestion id.",
        "No callback, follow-up intent, worker, Memory Center write, model call, or Calendar write was attempted.",
    )
    boundary_summary = _boundary_summary()
    record_without_render = SuggestedMeetingBriefRequestRecord(
        stage=SUGGESTED_MEETING_BRIEF_REQUEST_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=normalized_suggestion_id,
        status="completed",
        source_stage=PROACTIVE_MEETING_SUGGESTION_STAGE,
        selected_suggestion=selected,
        headline=f"Prepared an owner-requested brief for {selected.event_summary}.",
        meeting_summary=f"{selected.event_start} - {selected.event_summary}",
        preparation_checklist=checklist,
        watchpoints=watchpoints,
        boundary_summary=boundary_summary,
        local_render_text="",
        owner_requested=True,
        suggestion_validated=True,
        read_only=True,
        automatic_execution=False,
        callback_binding_allowed=False,
        followup_intent_created=False,
        async_delegation_allowed=False,
        worker_dispatch_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        error_code=None,
    )
    return _with_render(record_without_render)


def run_suggested_meeting_brief_request(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    suggestion_id: str,
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
) -> SuggestedMeetingBriefRequestRecord:
    suggestion_scan = run_proactive_meeting_suggestion_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_http_client=calendar_http_client,
    )
    return build_suggested_meeting_brief_request(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        suggestion_scan=suggestion_scan,
    )


def render_suggested_meeting_brief_request(record: SuggestedMeetingBriefRequestRecord) -> str:
    if record.local_render_text:
        return record.local_render_text
    return _render_record(record)


def _blocked_record(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    status: str,
    headline: str,
    error_code: str,
) -> SuggestedMeetingBriefRequestRecord:
    record_without_render = SuggestedMeetingBriefRequestRecord(
        stage=SUGGESTED_MEETING_BRIEF_REQUEST_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        status=status,
        source_stage=PROACTIVE_MEETING_SUGGESTION_STAGE,
        selected_suggestion=None,
        headline=headline,
        meeting_summary=None,
        preparation_checklist=(),
        watchpoints=(
            "No suggested meeting brief was rendered.",
            "No external action was taken.",
        ),
        boundary_summary=_boundary_summary(),
        local_render_text="",
        owner_requested=True,
        suggestion_validated=False,
        read_only=True,
        automatic_execution=False,
        callback_binding_allowed=False,
        followup_intent_created=False,
        async_delegation_allowed=False,
        worker_dispatch_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        error_code=error_code,
    )
    return _with_render(record_without_render)


def _with_render(record: SuggestedMeetingBriefRequestRecord) -> SuggestedMeetingBriefRequestRecord:
    return SuggestedMeetingBriefRequestRecord(
        **{
            field_name: getattr(record, field_name)
            for field_name in record.__dataclass_fields__
            if field_name != "local_render_text"
        },
        local_render_text=_render_record(record),
    )


def _render_record(record: SuggestedMeetingBriefRequestRecord) -> str:
    lines = [
        "Suggested Meeting Brief",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Source stage: {record.source_stage}",
        f"Suggestion id: {record.suggestion_id or 'none'}",
        "Owner requested: true",
        f"Suggestion validated: {'true' if record.suggestion_validated else 'false'}",
        "Read-only: true",
        "Automatic execution: disabled",
        "Callback binding: disabled",
        "Follow-up intent: disabled",
        "Memory Center mutation: disabled",
        "Calendar writes: disabled",
        "LLM/model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "",
        "Headline:",
        f"- {record.headline}",
        "",
        "Meeting:",
    ]
    lines.append(f"- {record.meeting_summary}" if record.meeting_summary else "- No meeting selected.")
    lines.extend(["", "Preparation checklist:"])
    if record.preparation_checklist:
        lines.extend(f"- {item}" for item in record.preparation_checklist)
    else:
        lines.append("- No preparation checklist was created.")
    lines.extend(["", "Watchpoints:"])
    lines.extend(f"- {watchpoint}" for watchpoint in record.watchpoints)
    lines.extend(["", "Boundaries:"])
    lines.extend(f"- {item}" for item in record.boundary_summary)
    lines.extend(["", "No external action was taken."])
    return "\n".join(lines)


def _boundary_summary() -> tuple[str, ...]:
    return (
        "Used the current 138P proactive meeting suggestion scan only.",
        "Did not execute /brief automatically.",
        "Did not create callbacks or follow-up intents.",
        "Did not mutate Memory Center or ProposedMemory.",
        "Did not create, update, or delete Calendar events.",
        "Did not call an LLM, tool, or worker.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.suggested_meeting_brief_request")
    parser.add_argument("suggestion_id")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_suggested_meeting_brief_request(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        suggestion_id=args.suggestion_id,
    )
    print(render_suggested_meeting_brief_request(record))
    return 0 if record.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
