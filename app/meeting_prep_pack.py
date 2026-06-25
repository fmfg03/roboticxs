from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol
from app.proactive_meeting_suggestion import (
    PROACTIVE_MEETING_SUGGESTION_STAGE,
    ProactiveMeetingSuggestionScanRecord,
    run_proactive_meeting_suggestion_scan,
)
from app.suggested_meeting_brief_request import (
    SUGGESTED_MEETING_BRIEF_REQUEST_STAGE,
    SuggestedMeetingBriefRequestRecord,
    build_suggested_meeting_brief_request,
)
from app.setup_capability_status_component import render_compact_setup_capability_block
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSnapshot,
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


MEETING_PREP_PACK_STAGE = "151P"
MAX_MEMORY_CONTEXT_LINES = 3


@dataclass(frozen=True, slots=True)
class MeetingPrepPackRecord:
    stage: str
    owner_id: str
    robot_id: str
    suggestion_id: str
    status: str
    source_stages: tuple[str, ...]
    suggested_brief: SuggestedMeetingBriefRequestRecord
    memory_snapshot_status: str
    meeting_lines: tuple[str, ...]
    agenda_lines: tuple[str, ...]
    memory_context_lines: tuple[str, ...]
    open_loop_lines: tuple[str, ...]
    missing_input_lines: tuple[str, ...]
    suggested_action_lines: tuple[str, ...]
    safe_next_step: str
    watchpoints: tuple[str, ...]
    next_steps: tuple[str, ...]
    owner_requested: bool
    suggestion_validated: bool
    read_only: bool
    calendar_write_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    followup_intent_created: bool
    scheduler_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    proactive_send_allowed: bool
    error_code: str | None

    def __post_init__(self) -> None:
        if self.stage != MEETING_PREP_PACK_STAGE:
            raise ValueError("151P meeting prep packs must identify the 151P stage.")
        if SUGGESTED_MEETING_BRIEF_REQUEST_STAGE not in self.source_stages:
            raise ValueError("151P meeting prep packs must include 139P suggested brief lineage.")
        if not self.owner_requested:
            raise ValueError("151P meeting prep packs require explicit owner request.")
        if not self.read_only:
            raise ValueError("151P meeting prep packs must be read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.followup_intent_created,
                self.scheduler_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.proactive_send_allowed,
            )
        ):
            raise ValueError("151P meeting prep packs must not expand authority.")


def build_meeting_prep_pack(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> MeetingPrepPackRecord:
    if suggestion_scan.owner_id != owner_id or suggestion_scan.robot_id != robot_id:
        raise ValueError("rejected_meeting_prep_suggestion_owner_robot_mismatch")
    if memory_snapshot.owner_id != owner_id or memory_snapshot.robot_id != robot_id:
        raise ValueError("rejected_meeting_prep_memory_owner_robot_mismatch")

    suggested_brief = build_suggested_meeting_brief_request(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        suggestion_scan=suggestion_scan,
    )
    completed = suggested_brief.status == "completed" and suggested_brief.selected_suggestion is not None
    memory_context_lines = _memory_context_lines(memory_snapshot)
    return MeetingPrepPackRecord(
        stage=MEETING_PREP_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id.strip(),
        status="completed" if completed else suggested_brief.status,
        source_stages=(
            PROACTIVE_MEETING_SUGGESTION_STAGE,
            SUGGESTED_MEETING_BRIEF_REQUEST_STAGE,
            "136P",
        ),
        suggested_brief=suggested_brief,
        memory_snapshot_status="visible" if memory_context_lines else "empty",
        meeting_lines=_meeting_lines(suggested_brief),
        agenda_lines=_agenda_lines(suggested_brief),
        memory_context_lines=memory_context_lines or ("No approved Memory Center context is visible for this prep pack.",),
        open_loop_lines=_open_loop_lines(suggested_brief),
        missing_input_lines=_missing_input_lines(suggested_brief, memory_context_lines=memory_context_lines),
        suggested_action_lines=_suggested_action_lines(suggested_brief),
        safe_next_step=_safe_next_step(suggested_brief),
        watchpoints=_watchpoints(suggested_brief),
        next_steps=_next_steps(suggested_brief),
        owner_requested=True,
        suggestion_validated=suggested_brief.suggestion_validated,
        read_only=True,
        calendar_write_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        followup_intent_created=False,
        scheduler_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        proactive_send_allowed=False,
        error_code=suggested_brief.error_code,
    )


def run_meeting_prep_pack(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    suggestion_id: str,
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> MeetingPrepPackRecord:
    suggestion_scan = run_proactive_meeting_suggestion_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_http_client=calendar_http_client,
    )
    memory_snapshot = build_memory_center_telegram_snapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        source_bundle=memory_source_bundle,
    )
    return build_meeting_prep_pack(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )


def render_meeting_prep_pack(record: MeetingPrepPackRecord) -> str:
    return "\n".join(
        [
            "Meeting Prep Pack",
            "",
            f"Status: {record.status}",
            f"Suggestion id: {record.suggestion_id}",
            "Owner requested: true",
            f"Suggestion validated: {'true' if record.suggestion_validated else 'false'}",
            "Read-only: true",
            "",
            "Meeting context:",
            *(f"- {line}" for line in record.meeting_lines),
            "",
            "Agenda:",
            *(f"- {line}" for line in record.agenda_lines),
            "",
            "Known memory:",
            *(f"- {line}" for line in record.memory_context_lines),
            "",
            "Open loops:",
            *(f"- {line}" for line in record.open_loop_lines),
            "",
            "Missing inputs:",
            *(f"- {line}" for line in record.missing_input_lines),
            "",
            *render_compact_setup_capability_block(),
            "",
            "Suggested actions:",
            *(f"- {line}" for line in record.suggested_action_lines),
            "",
            "Safe next step:",
            f"- {record.safe_next_step}",
            "",
            "Watchpoints:",
            *(f"- {line}" for line in record.watchpoints),
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Memory writes: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Follow-up intents: disabled",
            "Scheduler/reminders: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "Proactive outbound: disabled",
            "",
            "No external action was taken.",
        ]
    )


def _meeting_lines(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if record.selected_suggestion is None:
        return (record.headline,)
    suggestion = record.selected_suggestion
    return (
        f"{suggestion.event_start} - {suggestion.event_summary}",
        f"Reason: {suggestion.reason}",
    )


def _agenda_lines(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if not record.preparation_checklist:
        return ("No prep agenda was generated because the suggestion was not available.",)
    return tuple(record.preparation_checklist[:4])


def _memory_context_lines(snapshot: TelegramMemoryCenterSnapshot) -> tuple[str, ...]:
    lines = [
        f"{item.memory_kind}: {item.summary}"
        for item in snapshot.approved_memories[:MAX_MEMORY_CONTEXT_LINES]
    ]
    if snapshot.approved_total_count > len(lines):
        lines.append(f"Plus {snapshot.approved_total_count - len(lines)} more approved memory item(s) hidden by the local bound.")
    return tuple(lines)


def _watchpoints(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if record.status != "completed":
        return (
            "The requested suggestion could not be converted into a prep pack.",
            "No external action was taken.",
        )
    return (
        "This prep pack is a local read-only composition of Calendar suggestion and Memory Center visibility.",
        "Pending memory proposals are not treated as facts.",
        "No follow-up, reminder, writeback, model call, tool call, or worker dispatch was attempted.",
    )


def _next_steps(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if record.status != "completed":
        return ("Use /suggest_brief to request the current available meeting suggestions.",)
    return (
        "Review agenda and memory context before the meeting.",
        "Use a separate approved command path for any follow-up or memory change.",
    )


def _open_loop_lines(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if record.status != "completed":
        return ("No open loops were prepared because the meeting suggestion was unavailable.",)
    open_loop_candidates = tuple(
        item for item in record.preparation_checklist if "question" in item.lower() or "resolve" in item.lower()
    )
    if open_loop_candidates:
        return open_loop_candidates[:4]
    return ("No open loops were found in the local prep context.",)


def _missing_input_lines(
    record: SuggestedMeetingBriefRequestRecord,
    *,
    memory_context_lines: tuple[str, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    if record.status != "completed":
        missing.append("Current meeting suggestion id.")
    if not memory_context_lines:
        missing.append("Approved Memory Center context for this meeting.")
    if not record.preparation_checklist:
        missing.append("Agenda candidates from the selected suggestion.")
    return tuple(missing) if missing else ("No missing inputs detected in the local prep context.",)


def _suggested_action_lines(record: SuggestedMeetingBriefRequestRecord) -> tuple[str, ...]:
    if record.status != "completed":
        return ("Run /suggest_brief, then request /prep <suggestion_id> for one current suggestion.",)
    return (
        "Review the agenda before the meeting.",
        "Check the open loops and decide what needs owner action.",
        "Use a separate approved command for any memory approval or task decision.",
    )


def _safe_next_step(record: SuggestedMeetingBriefRequestRecord) -> str:
    if record.status != "completed":
        return "Run /suggest_brief to get current meeting suggestions."
    return "Review this prep pack and take any external action yourself unless a later approved command explicitly supports it."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.meeting_prep_pack")
    parser.add_argument("suggestion_id")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_meeting_prep_pack(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        suggestion_id=args.suggestion_id,
    )
    print(render_meeting_prep_pack(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
