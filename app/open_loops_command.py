from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol
from app.proactive_meeting_suggestion import (
    ProactiveMeetingSuggestionScanRecord,
    run_proactive_meeting_suggestion_scan,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSnapshot,
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


OPEN_LOOPS_COMMAND_STAGE = "142P"
MAX_OPEN_LOOP_SUGGESTIONS = 3


@dataclass(frozen=True, slots=True)
class OpenLoopsCommandRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    calendar_status: str
    memory_status: str
    suggestion_status: str
    pending_memory_lines: tuple[str, ...]
    meeting_suggestion_lines: tuple[str, ...]
    calendar_lines: tuple[str, ...]
    next_steps: tuple[str, ...]
    read_only: bool
    calendar_write_allowed: bool
    memory_write_allowed: bool
    proposed_memory_written: bool
    followup_intent_created: bool
    reminder_scheduled: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    proactive_send_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != OPEN_LOOPS_COMMAND_STAGE:
            raise ValueError("142P Open Loops records must identify the 142P stage.")
        if not self.read_only:
            raise ValueError("142P Open Loops records must be read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.memory_write_allowed,
                self.proposed_memory_written,
                self.followup_intent_created,
                self.reminder_scheduled,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.proactive_send_allowed,
            )
        ):
            raise ValueError("142P Open Loops records must not expand authority.")


def build_open_loops_command_record(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> OpenLoopsCommandRecord:
    if suggestion_scan.owner_id != owner_id or suggestion_scan.robot_id != robot_id:
        raise ValueError("rejected_open_loops_suggestion_owner_robot_mismatch")
    if memory_snapshot.owner_id != owner_id or memory_snapshot.robot_id != robot_id:
        raise ValueError("rejected_open_loops_memory_owner_robot_mismatch")

    pending_memory_lines = _pending_memory_lines_from_snapshot(memory_snapshot)
    meeting_suggestion_lines = _meeting_suggestion_lines_from_scan(suggestion_scan)
    calendar_lines = _calendar_lines_from_scan(suggestion_scan)
    next_steps = _next_steps_from_sources(
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    has_open_loops = bool(memory_snapshot.pending_total_count or suggestion_scan.suggestions)
    if suggestion_scan.status == "blocked_calendar_unavailable":
        status = "partial_calendar_unavailable"
    elif has_open_loops:
        status = "completed_with_open_loops"
    else:
        status = "empty"
    memory_status = "pending" if memory_snapshot.pending_total_count else "empty"

    return OpenLoopsCommandRecord(
        stage=OPEN_LOOPS_COMMAND_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=status,
        calendar_status=suggestion_scan.status,
        memory_status=memory_status,
        suggestion_status=suggestion_scan.status,
        pending_memory_lines=pending_memory_lines,
        meeting_suggestion_lines=meeting_suggestion_lines,
        calendar_lines=calendar_lines,
        next_steps=next_steps,
        read_only=True,
        calendar_write_allowed=False,
        memory_write_allowed=False,
        proposed_memory_written=False,
        followup_intent_created=False,
        reminder_scheduled=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        proactive_send_allowed=False,
    )


def run_open_loops_command(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> OpenLoopsCommandRecord:
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
    return build_open_loops_command_record(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )


def render_open_loops_command(record: OpenLoopsCommandRecord) -> str:
    return "\n".join(
        [
            "Open Loops",
            "",
            f"Stage: {record.stage}",
            f"Status: {record.status}",
            f"Calendar status: {record.calendar_status}",
            f"Memory status: {record.memory_status}",
            f"Suggestion status: {record.suggestion_status}",
            "Read-only: true",
            "Calendar writes: disabled",
            "Memory writes: disabled",
            "ProposedMemory writes: disabled",
            "Follow-up intents: disabled",
            "Reminders/scheduler: disabled",
            "LLM/model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "Proactive outbound: disabled",
            "",
            "Pending memory proposals:",
            *(f"- {line}" for line in record.pending_memory_lines),
            "",
            "Meeting suggestions:",
            *(f"- {line}" for line in record.meeting_suggestion_lines),
            "",
            "Calendar:",
            *(f"- {line}" for line in record.calendar_lines),
            "",
            "Suggested next steps:",
            *(f"- {step}" for step in record.next_steps),
            "",
            "No external action was taken.",
        ]
    )


def _pending_memory_lines_from_snapshot(snapshot: TelegramMemoryCenterSnapshot) -> tuple[str, ...]:
    if not snapshot.pending_proposals:
        return ("No pending memory proposals are visible in this local snapshot.",)
    lines = [
        f"{proposal.proposal_type}: {proposal.proposed_memory_text} (pending review; not treated as fact)"
        for proposal in snapshot.pending_proposals
    ]
    if snapshot.pending_total_count > len(snapshot.pending_proposals):
        remaining = snapshot.pending_total_count - len(snapshot.pending_proposals)
        lines.append(f"Plus {remaining} more pending proposal(s) hidden by the local bound.")
    return tuple(lines)


def _meeting_suggestion_lines_from_scan(record: ProactiveMeetingSuggestionScanRecord) -> tuple[str, ...]:
    if record.status == "blocked_calendar_unavailable":
        return ("No meeting suggestion loop was generated because Calendar failed closed.",)
    if not record.suggestions:
        return ("No owner-requestable meeting brief suggestion loops are available right now.",)
    return tuple(
        f"{suggestion.event_start} - {suggestion.event_summary}: /brief {suggestion.suggestion_id}"
        for suggestion in record.suggestions[:MAX_OPEN_LOOP_SUGGESTIONS]
    )


def _calendar_lines_from_scan(record: ProactiveMeetingSuggestionScanRecord) -> tuple[str, ...]:
    if record.status == "blocked_calendar_unavailable":
        return (
            f"Read-only Calendar context unavailable: {record.error_code or 'unknown_error'}.",
            "Open Loops continued with local Memory Center visibility only.",
        )
    return (f"Calendar scan status: {record.status}.",)


def _next_steps_from_sources(
    *,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> tuple[str, ...]:
    steps: list[str] = []
    if memory_snapshot.pending_total_count:
        steps.append("Use /memory_pending to review pending memory proposals before treating them as facts.")
    if suggestion_scan.suggestions:
        steps.append("Use /suggest_brief to re-list current meeting suggestions or /brief <suggestion_id> for one selected read-only brief.")
    if not steps:
        steps.append("No unresolved local loops were found.")
    steps.append("No action was taken automatically.")
    return tuple(steps)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.open_loops_command")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_open_loops_command(owner_id=args.owner_id, robot_id=args.robot_id)
    print(render_open_loops_command(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
