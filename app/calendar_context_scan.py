from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.google_calendar_readonly_connector import (
    CalendarEventSnapshot,
    CalendarReadResult,
    GoogleCalendarHttpClientProtocol,
    run_google_calendar_readonly_connector,
)


CALENDAR_CONTEXT_SCAN_STAGE = "137P"
MAX_CONTEXT_CANDIDATES = 10
MAX_CONTEXT_TEXT_CHARS = 220
BUSINESS_CONTEXT_MARKERS = frozenset(
    {
        "client",
        "customer",
        "prospect",
        "opportunity",
        "follow-up",
        "follow up",
        "demo",
        "proposal",
        "asisint",
        "trakit",
    }
)
PREP_CONTEXT_MARKERS = frozenset(
    {
        "meeting",
        "brief",
        "prep",
        "review",
        "follow-up",
        "follow up",
        "demo",
        "presentation",
    }
)


@dataclass(frozen=True, slots=True)
class CalendarContextCandidateRecord:
    candidate_id: str
    owner_id: str
    robot_id: str
    scan_stage: str
    source_stage: str
    event_id: str
    event_summary: str
    event_start: str
    candidate_type: str
    proposed_context: str
    confidence: str
    source: str
    proposed_memory: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    worker_dispatch_allowed: bool
    lineage_summary: dict[str, object]

    def __post_init__(self) -> None:
        if self.scan_stage != CALENDAR_CONTEXT_SCAN_STAGE:
            raise ValueError("137P candidates must identify the 137P scan stage.")
        if self.source_stage != "133P":
            raise ValueError("137P Calendar context candidates must originate from the 133P connector.")
        if self.proposed_memory:
            raise ValueError("137P context candidates must not become proposed memory automatically.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.external_write_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("137P Calendar context scan must not expand authority.")


@dataclass(frozen=True, slots=True)
class CalendarContextScanRecord:
    owner_id: str
    robot_id: str
    scan_stage: str
    status: str
    calendar_id: str
    window_start: str
    window_end: str
    candidates: tuple[CalendarContextCandidateRecord, ...]
    watchpoints: tuple[str, ...]
    read_only: bool
    proposed_memory_count: int
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    worker_dispatch_allowed: bool
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.scan_stage != CALENDAR_CONTEXT_SCAN_STAGE:
            raise ValueError("137P scans must identify the 137P stage.")
        if not self.read_only:
            raise ValueError("137P Calendar context scans must be read-only.")
        if self.proposed_memory_count != 0:
            raise ValueError("137P scans must not create proposed memories.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.external_write_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("137P Calendar context scans must not expand authority.")


def build_calendar_context_scan_record(
    *,
    owner_id: str,
    robot_id: str,
    calendar_result: CalendarReadResult,
) -> CalendarContextScanRecord:
    if not calendar_result.ok:
        return CalendarContextScanRecord(
            owner_id=owner_id,
            robot_id=robot_id,
            scan_stage=CALENDAR_CONTEXT_SCAN_STAGE,
            status="blocked_calendar_unavailable",
            calendar_id=calendar_result.calendar_id,
            window_start=calendar_result.window_start,
            window_end=calendar_result.window_end,
            candidates=(),
            watchpoints=(
                f"Calendar read failed closed: {calendar_result.error_code or 'unknown_error'}.",
                "No context candidate was written to Memory Center.",
            ),
            read_only=True,
            proposed_memory_count=0,
            memory_write_allowed=False,
            memory_center_mutated=False,
            external_write_allowed=False,
            calendar_write_allowed=False,
            model_call_allowed=False,
            worker_dispatch_allowed=False,
            error_code=calendar_result.error_code,
        )

    candidates: list[CalendarContextCandidateRecord] = []
    for event in calendar_result.events:
        candidates.extend(_candidates_for_event(owner_id=owner_id, robot_id=robot_id, event=event))
        if len(candidates) >= MAX_CONTEXT_CANDIDATES:
            candidates = candidates[:MAX_CONTEXT_CANDIDATES]
            break

    status = "completed" if candidates else "no_context_candidates"
    watchpoints = [
        "No Memory Center write was attempted.",
        "Context candidates are review material only, not canonical memory.",
        "Calendar create/update/delete remains disabled.",
        "LLM/model calls, tools, workers, and external writes remain disabled.",
    ]
    if len(candidates) == MAX_CONTEXT_CANDIDATES:
        watchpoints.append("Candidate output was bounded by the local 137P limit.")

    return CalendarContextScanRecord(
        owner_id=owner_id,
        robot_id=robot_id,
        scan_stage=CALENDAR_CONTEXT_SCAN_STAGE,
        status=status,
        calendar_id=calendar_result.calendar_id,
        window_start=calendar_result.window_start,
        window_end=calendar_result.window_end,
        candidates=tuple(candidates),
        watchpoints=tuple(watchpoints),
        read_only=True,
        proposed_memory_count=0,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def run_calendar_context_scan(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
) -> CalendarContextScanRecord:
    calendar_result = run_google_calendar_readonly_connector(http_client=calendar_http_client)
    return build_calendar_context_scan_record(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_result=calendar_result,
    )


def render_calendar_context_scan(record: CalendarContextScanRecord) -> str:
    lines = [
        "Calendar Context Scan",
        "",
        f"Stage: {record.scan_stage}",
        f"Status: {record.status}",
        f"Calendar: {record.calendar_id}",
        f"Window: {record.window_start} -> {record.window_end}",
        f"Candidates: {len(record.candidates)}",
        "Proposed memories written: 0",
        "Memory Center mutation: disabled",
        "Calendar writes: disabled",
        "LLM/model calls: disabled",
        "External writes: disabled",
        "",
        "Context candidates:",
    ]
    if not record.candidates:
        lines.append("- No Calendar context candidates were produced.")
    else:
        for candidate in record.candidates:
            lines.append(f"- {candidate.candidate_type}: {candidate.proposed_context}")
    lines.extend(["", "Watchpoints:"])
    lines.extend(f"- {watchpoint}" for watchpoint in record.watchpoints)
    return "\n".join(lines)


def _candidates_for_event(
    *,
    owner_id: str,
    robot_id: str,
    event: CalendarEventSnapshot,
) -> tuple[CalendarContextCandidateRecord, ...]:
    normalized = _normalized_event_text(event)
    candidates: list[CalendarContextCandidateRecord] = []
    if any(marker in normalized for marker in BUSINESS_CONTEXT_MARKERS):
        subject = _subject_from_event(event)
        candidates.append(
            _candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                event=event,
                candidate_type="business_context_candidate",
                proposed_context=f"{subject} may be active business context from Calendar event '{event.summary}'.",
                confidence="medium",
            )
        )
    if any(marker in normalized for marker in PREP_CONTEXT_MARKERS):
        candidates.append(
            _candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                event=event,
                candidate_type="meeting_prep_context_candidate",
                proposed_context=f"Meeting '{event.summary}' may need a brief or prep checklist before {event.start}.",
                confidence="medium",
            )
        )
    if event.attendee_count > 0 or event.location:
        candidates.append(
            _candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                event=event,
                candidate_type="relationship_context_candidate",
                proposed_context=f"Calendar event '{event.summary}' has relationship signals: attendees={event.attendee_count}, location={event.location or 'not provided'}.",
                confidence="low",
            )
        )
    return tuple(candidates)


def _candidate(
    *,
    owner_id: str,
    robot_id: str,
    event: CalendarEventSnapshot,
    candidate_type: str,
    proposed_context: str,
    confidence: str,
) -> CalendarContextCandidateRecord:
    bounded_context = _bounded_text(proposed_context)
    candidate_id = _stable_id(
        "calendar_context_candidate",
        owner_id,
        robot_id,
        event.event_id,
        candidate_type,
        bounded_context,
    )
    return CalendarContextCandidateRecord(
        candidate_id=candidate_id,
        owner_id=owner_id,
        robot_id=robot_id,
        scan_stage=CALENDAR_CONTEXT_SCAN_STAGE,
        source_stage="133P",
        event_id=event.event_id,
        event_summary=event.summary,
        event_start=event.start,
        candidate_type=candidate_type,
        proposed_context=bounded_context,
        confidence=confidence,
        source="google_calendar_readonly_context_scan",
        proposed_memory=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        worker_dispatch_allowed=False,
        lineage_summary={
            "calendar_event_id": event.event_id,
            "calendar_source": event.source,
            "source_stage": "133P",
            "scan_stage": CALENDAR_CONTEXT_SCAN_STAGE,
        },
    )


def _normalized_event_text(event: CalendarEventSnapshot) -> str:
    return " ".join(
        part.lower()
        for part in (
            event.summary,
            event.description_preview or "",
            event.location or "",
            event.organizer_email or "",
        )
        if part
    )


def _subject_from_event(event: CalendarEventSnapshot) -> str:
    for token in event.summary.replace("-", " ").replace("/", " ").split():
        cleaned = token.strip(".,:;()[]{}")
        if len(cleaned) >= 3 and cleaned.upper() == cleaned and any(char.isalpha() for char in cleaned):
            return cleaned
    return event.summary.strip() or "This Calendar event"


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_CONTEXT_TEXT_CHARS:
        return stripped
    return stripped[: MAX_CONTEXT_TEXT_CHARS - 3].rstrip() + "..."


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.calendar_context_scan")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_calendar_context_scan(owner_id=args.owner_id, robot_id=args.robot_id)
    print(render_calendar_context_scan(record))
    return 0 if record.status != "blocked_calendar_unavailable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
