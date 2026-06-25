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


TODAY_COMMAND_STAGE = "152P"
MAX_TODAY_MEMORY_LINES = 3
MAX_TODAY_SUGGESTION_LINES = 3


@dataclass(frozen=True, slots=True)
class TodayCommandRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    calendar_status: str
    memory_status: str
    suggestion_status: str
    calendar_lines: tuple[str, ...]
    memory_lines: tuple[str, ...]
    suggestion_lines: tuple[str, ...]
    open_loop_lines: tuple[str, ...]
    waiting_lines: tuple[str, ...]
    blocked_source_lines: tuple[str, ...]
    suggested_next_action: str
    next_steps: tuple[str, ...]
    read_only: bool
    calendar_write_allowed: bool
    memory_write_allowed: bool
    proposed_memory_written: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    proactive_send_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != TODAY_COMMAND_STAGE:
            raise ValueError("152P Today records must identify the 152P stage.")
        if not self.read_only:
            raise ValueError("152P Today records must be read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.memory_write_allowed,
                self.proposed_memory_written,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.proactive_send_allowed,
            )
        ):
            raise ValueError("152P Today records must not expand authority.")


def build_today_command_record(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> TodayCommandRecord:
    if suggestion_scan.owner_id != owner_id or suggestion_scan.robot_id != robot_id:
        raise ValueError("rejected_today_suggestion_owner_robot_mismatch")
    if memory_snapshot.owner_id != owner_id or memory_snapshot.robot_id != robot_id:
        raise ValueError("rejected_today_memory_owner_robot_mismatch")

    calendar_lines = _calendar_lines_from_suggestion_scan(suggestion_scan)
    suggestion_lines = _suggestion_lines_from_suggestion_scan(suggestion_scan)
    memory_lines = _memory_lines_from_snapshot(memory_snapshot)
    next_steps = _next_steps_from_sources(
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    open_loop_lines = _open_loop_lines_from_sources(
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    waiting_lines = _waiting_lines_from_sources(memory_snapshot)
    blocked_source_lines = _blocked_source_lines_from_sources(suggestion_scan)
    status = "partial_calendar_unavailable" if suggestion_scan.status == "blocked_calendar_unavailable" else "completed"
    memory_status = "visible" if memory_snapshot.approved_total_count or memory_snapshot.pending_total_count else "empty"

    return TodayCommandRecord(
        stage=TODAY_COMMAND_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=status,
        calendar_status=suggestion_scan.status,
        memory_status=memory_status,
        suggestion_status=suggestion_scan.status,
        calendar_lines=calendar_lines,
        memory_lines=memory_lines,
        suggestion_lines=suggestion_lines,
        open_loop_lines=open_loop_lines,
        waiting_lines=waiting_lines,
        blocked_source_lines=blocked_source_lines,
        suggested_next_action=next_steps[0],
        next_steps=next_steps,
        read_only=True,
        calendar_write_allowed=False,
        memory_write_allowed=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        proactive_send_allowed=False,
    )


def run_today_command(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> TodayCommandRecord:
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
    return build_today_command_record(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )


def render_today_command(record: TodayCommandRecord) -> str:
    return "\n".join(
        [
            "Today",
            "",
            f"Status: {record.status}",
            f"Calendar status: {record.calendar_status}",
            f"Memory status: {record.memory_status}",
            f"Suggestion status: {record.suggestion_status}",
            "Read-only: true",
            "",
            "Meetings:",
            *(f"- {line}" for line in record.calendar_lines),
            "",
            "Open loops:",
            *(f"- {line}" for line in record.open_loop_lines),
            "",
            "Things waiting for you:",
            *(f"- {line}" for line in record.waiting_lines),
            "",
            "Brief options:",
            *(f"- {line}" for line in record.suggestion_lines),
            "",
            "Known memory:",
            *(f"- {line}" for line in record.memory_lines),
            "",
            "Suggested next action:",
            f"- {record.suggested_next_action}",
            "",
            "Blocked / unavailable sources:",
            *(f"- {line}" for line in record.blocked_source_lines),
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Memory writes: disabled",
            "ProposedMemory writes: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "Proactive outbound: disabled",
            "",
            "No external action was taken.",
        ]
    )


def _calendar_lines_from_suggestion_scan(record: ProactiveMeetingSuggestionScanRecord) -> tuple[str, ...]:
    if record.status == "blocked_calendar_unavailable":
        return (
            f"Read-only Calendar context unavailable: {record.error_code or 'unknown_error'}.",
            "Today continued with local Memory Center visibility only.",
        )
    if not record.suggestions:
        return ("No upcoming Calendar meeting currently needs Today prep.",)
    return tuple(
        f"{suggestion.event_start} - {suggestion.event_summary}"
        for suggestion in record.suggestions[:MAX_TODAY_SUGGESTION_LINES]
    )


def _suggestion_lines_from_suggestion_scan(record: ProactiveMeetingSuggestionScanRecord) -> tuple[str, ...]:
    if record.status == "blocked_calendar_unavailable":
        return ("No meeting brief suggestions were generated because Calendar failed closed.",)
    if not record.suggestions:
        return ("No owner-requestable meeting brief suggestions are available right now.",)
    return tuple(
        f"Run /brief {suggestion.suggestion_id} if you want a read-only brief for {suggestion.event_summary}."
        for suggestion in record.suggestions[:MAX_TODAY_SUGGESTION_LINES]
    )


def _memory_lines_from_snapshot(snapshot: TelegramMemoryCenterSnapshot) -> tuple[str, ...]:
    lines = [
        f"Approved visible memories: {snapshot.approved_total_count}",
        f"Pending memory proposals: {snapshot.pending_total_count}",
    ]
    if snapshot.approved_memories:
        lines.extend(
            f"{memory.memory_kind}: {memory.summary}"
            for memory in snapshot.approved_memories[:MAX_TODAY_MEMORY_LINES]
        )
    else:
        lines.append("No approved Memory Center items are visible in this local snapshot.")
    if snapshot.pending_total_count:
        lines.append("Review /memory_pending before treating pending memory as fact.")
    return tuple(lines)


def _next_steps_from_sources(
    *,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> tuple[str, ...]:
    steps: list[str] = []
    if suggestion_scan.suggestions:
        first = suggestion_scan.suggestions[0]
        steps.append(f"Use /brief {first.suggestion_id} only if you want the first suggested meeting brief.")
    if memory_snapshot.pending_total_count:
        steps.append("Review /memory_pending for user-approved memory decisions.")
    if not steps:
        steps.append("No urgent local prep action was found.")
    steps.append("No action was taken automatically.")
    return tuple(steps)


def _open_loop_lines_from_sources(
    *,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
    memory_snapshot: TelegramMemoryCenterSnapshot,
) -> tuple[str, ...]:
    loops: list[str] = []
    if suggestion_scan.suggestions:
        first = suggestion_scan.suggestions[0]
        loops.append(f"Prepare for {first.event_summary} before {first.event_start}.")
    if memory_snapshot.pending_total_count:
        loops.append("Pending memory proposals need owner review before they become facts.")
    if not loops:
        loops.append("No open loops were found in the local Today context.")
    return tuple(loops)


def _waiting_lines_from_sources(snapshot: TelegramMemoryCenterSnapshot) -> tuple[str, ...]:
    if snapshot.pending_total_count:
        return (f"{snapshot.pending_total_count} pending memory proposal(s) need review.",)
    return ("Nothing is waiting for owner approval in the local Memory Center snapshot.",)


def _blocked_source_lines_from_sources(record: ProactiveMeetingSuggestionScanRecord) -> tuple[str, ...]:
    if record.status == "blocked_calendar_unavailable":
        return (f"Calendar read-only source unavailable: {record.error_code or 'unknown_error'}.",)
    return ("No blocked sources detected in this local Today view.",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.today_command")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_today_command(owner_id=args.owner_id, robot_id=args.robot_id)
    print(render_today_command(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
