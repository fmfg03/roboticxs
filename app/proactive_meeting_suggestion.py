from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.calendar_context_scan import (
    CALENDAR_CONTEXT_SCAN_STAGE,
    CalendarContextScanRecord,
    run_calendar_context_scan,
)
from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol


PROACTIVE_MEETING_SUGGESTION_STAGE = "138P"
MAX_MEETING_SUGGESTIONS = 3
MAX_SUGGESTION_TEXT_CHARS = 240
MEETING_BRIEF_MARKERS = frozenset(
    {
        "meeting",
        "brief",
        "prep",
        "review",
        "follow-up",
        "follow up",
        "demo",
        "proposal",
        "client",
        "customer",
        "prospect",
        "presentation",
    }
)


@dataclass(frozen=True, slots=True)
class ProactiveMeetingBriefSuggestionRecord:
    suggestion_id: str
    owner_id: str
    robot_id: str
    suggestion_stage: str
    source_stage: str
    event_id: str
    event_summary: str
    event_start: str
    reason: str
    suggested_action: str
    confidence: str
    action_only: bool
    brief_executed: bool
    callback_binding_allowed: bool
    followup_adapter_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    lineage_summary: dict[str, object]

    def __post_init__(self) -> None:
        if self.suggestion_stage != PROACTIVE_MEETING_SUGGESTION_STAGE:
            raise ValueError("138P suggestions must identify the 138P stage.")
        if self.source_stage != CALENDAR_CONTEXT_SCAN_STAGE:
            raise ValueError("138P suggestions must originate from the 137P Calendar context scan.")
        if not self.action_only:
            raise ValueError("138P meeting suggestions must be action-only.")
        if self.brief_executed:
            raise ValueError("138P meeting suggestions must not execute a brief automatically.")
        if any(
            (
                self.callback_binding_allowed,
                self.followup_adapter_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.external_write_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("138P proactive meeting suggestions must not expand authority.")


@dataclass(frozen=True, slots=True)
class ProactiveMeetingSuggestionScanRecord:
    owner_id: str
    robot_id: str
    suggestion_stage: str
    source_stage: str
    status: str
    calendar_id: str
    window_start: str
    window_end: str
    suggestions: tuple[ProactiveMeetingBriefSuggestionRecord, ...]
    watchpoints: tuple[str, ...]
    read_only: bool
    action_only: bool
    brief_executions: int
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.suggestion_stage != PROACTIVE_MEETING_SUGGESTION_STAGE:
            raise ValueError("138P suggestion scans must identify the 138P stage.")
        if self.source_stage != CALENDAR_CONTEXT_SCAN_STAGE:
            raise ValueError("138P suggestion scans must originate from the 137P Calendar context scan.")
        if not self.read_only:
            raise ValueError("138P meeting suggestion scans must be read-only.")
        if not self.action_only:
            raise ValueError("138P meeting suggestion scans must be action-only.")
        if self.brief_executions != 0:
            raise ValueError("138P meeting suggestions must not execute briefs.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.external_write_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("138P meeting suggestion scans must not expand authority.")


def build_proactive_meeting_suggestion_scan(
    *,
    owner_id: str,
    robot_id: str,
    context_scan: CalendarContextScanRecord,
) -> ProactiveMeetingSuggestionScanRecord:
    if context_scan.scan_stage != CALENDAR_CONTEXT_SCAN_STAGE:
        raise ValueError("rejected_invalid_context_scan_stage")
    if context_scan.owner_id != owner_id or context_scan.robot_id != robot_id:
        raise ValueError("rejected_context_scan_owner_robot_mismatch")

    if context_scan.status == "blocked_calendar_unavailable":
        return ProactiveMeetingSuggestionScanRecord(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_stage=PROACTIVE_MEETING_SUGGESTION_STAGE,
            source_stage=CALENDAR_CONTEXT_SCAN_STAGE,
            status="blocked_calendar_unavailable",
            calendar_id=context_scan.calendar_id,
            window_start=context_scan.window_start,
            window_end=context_scan.window_end,
            suggestions=(),
            watchpoints=(
                f"Calendar context scan failed closed: {context_scan.error_code or 'unknown_error'}.",
                "No proactive meeting suggestion was sent automatically.",
            ),
            read_only=True,
            action_only=True,
            brief_executions=0,
            memory_write_allowed=False,
            memory_center_mutated=False,
            external_write_allowed=False,
            calendar_write_allowed=False,
            model_call_allowed=False,
            tool_call_allowed=False,
            worker_dispatch_allowed=False,
            error_code=context_scan.error_code,
        )

    suggestions: list[ProactiveMeetingBriefSuggestionRecord] = []
    seen_events: set[str] = set()
    for candidate in context_scan.candidates:
        if candidate.event_id in seen_events:
            continue
        if candidate.candidate_type != "meeting_prep_context_candidate":
            continue
        normalized = " ".join(
            (
                candidate.event_summary,
                candidate.proposed_context,
            )
        ).lower()
        if not any(marker in normalized for marker in MEETING_BRIEF_MARKERS):
            continue
        suggestions.append(
            _suggestion_from_candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                candidate_id=candidate.candidate_id,
                event_id=candidate.event_id,
                event_summary=candidate.event_summary,
                event_start=candidate.event_start,
                reason=f"Calendar context scan marked '{candidate.event_summary}' as likely needing meeting preparation.",
                confidence=candidate.confidence,
            )
        )
        seen_events.add(candidate.event_id)
        if len(suggestions) >= MAX_MEETING_SUGGESTIONS:
            break

    status = "completed" if suggestions else "no_meeting_suggestions"
    watchpoints = [
        "Suggestions are action-only and do not execute /brief automatically.",
        "No Memory Center write or ProposedMemory write was attempted.",
        "Calendar create/update/delete remains disabled.",
        "LLM/model calls, tools, workers, and external writes remain disabled.",
    ]
    if len(suggestions) == MAX_MEETING_SUGGESTIONS:
        watchpoints.append("Suggestion output was bounded by the local 138P limit.")

    return ProactiveMeetingSuggestionScanRecord(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_stage=PROACTIVE_MEETING_SUGGESTION_STAGE,
        source_stage=CALENDAR_CONTEXT_SCAN_STAGE,
        status=status,
        calendar_id=context_scan.calendar_id,
        window_start=context_scan.window_start,
        window_end=context_scan.window_end,
        suggestions=tuple(suggestions),
        watchpoints=tuple(watchpoints),
        read_only=True,
        action_only=True,
        brief_executions=0,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def run_proactive_meeting_suggestion_scan(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
) -> ProactiveMeetingSuggestionScanRecord:
    context_scan = run_calendar_context_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_http_client=calendar_http_client,
    )
    return build_proactive_meeting_suggestion_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        context_scan=context_scan,
    )


def render_proactive_meeting_suggestion_scan(record: ProactiveMeetingSuggestionScanRecord) -> str:
    lines = [
        "Proactive Meeting Suggestions",
        "",
        f"Stage: {record.suggestion_stage}",
        f"Status: {record.status}",
        f"Calendar: {record.calendar_id}",
        f"Window: {record.window_start} -> {record.window_end}",
        f"Suggestions: {len(record.suggestions)}",
        "Action-only: true",
        "Briefs executed: 0",
        "Memory Center mutation: disabled",
        "Calendar writes: disabled",
        "LLM/model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "",
        "Suggestions:",
    ]
    if not record.suggestions:
        lines.append("- No upcoming Calendar meeting currently deserves a proactive brief suggestion.")
    else:
        for suggestion in record.suggestions:
            lines.append(f"- {suggestion.event_start} - {suggestion.event_summary}")
            lines.append(f"  Reason: {suggestion.reason}")
            lines.append(f"  Suggested action: {suggestion.suggested_action}")
    lines.extend(["", "Watchpoints:"])
    lines.extend(f"- {watchpoint}" for watchpoint in record.watchpoints)
    lines.extend(["", "No external action was taken."])
    return "\n".join(lines)


def _suggestion_from_candidate(
    *,
    owner_id: str,
    robot_id: str,
    candidate_id: str,
    event_id: str,
    event_summary: str,
    event_start: str,
    reason: str,
    confidence: str,
) -> ProactiveMeetingBriefSuggestionRecord:
    bounded_reason = _bounded_text(reason)
    suggestion_id = _stable_id(
        "proactive_meeting_brief_suggestion",
        owner_id,
        robot_id,
        event_id,
        bounded_reason,
    )
    suggested_action = _bounded_text(
        f"Run /brief {suggestion_id} to request a brief for '{event_summary}' before {event_start}."
    )
    return ProactiveMeetingBriefSuggestionRecord(
        suggestion_id=suggestion_id,
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_stage=PROACTIVE_MEETING_SUGGESTION_STAGE,
        source_stage=CALENDAR_CONTEXT_SCAN_STAGE,
        event_id=event_id,
        event_summary=event_summary,
        event_start=event_start,
        reason=bounded_reason,
        suggested_action=suggested_action,
        confidence=confidence,
        action_only=True,
        brief_executed=False,
        callback_binding_allowed=False,
        followup_adapter_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        lineage_summary={
            "calendar_event_id": event_id,
            "calendar_context_candidate_id": candidate_id,
            "source_stage": CALENDAR_CONTEXT_SCAN_STAGE,
            "suggestion_stage": PROACTIVE_MEETING_SUGGESTION_STAGE,
        },
    )


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_SUGGESTION_TEXT_CHARS:
        return stripped
    return stripped[: MAX_SUGGESTION_TEXT_CHARS - 3].rstrip() + "..."


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.proactive_meeting_suggestion")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_proactive_meeting_suggestion_scan(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
    )
    print(render_proactive_meeting_suggestion_scan(record))
    return 0 if record.status != "blocked_calendar_unavailable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
