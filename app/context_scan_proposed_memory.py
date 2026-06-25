from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.calendar_context_scan import (
    CALENDAR_CONTEXT_SCAN_STAGE,
    CalendarContextScanRecord,
)
from app.gmail_readonly_context_scan import (
    GMAIL_READONLY_CONTEXT_SCAN_STAGE,
    GmailReadonlyContextScanRecord,
)


CONTEXT_SCAN_PROPOSED_MEMORY_STAGE = "164P"
CONTEXT_SCAN_PROPOSED_MEMORY_STATUS = "pending_owner_review"
MAX_PROPOSALS = 12
MAX_MEMORY_TEXT_CHARS = 240


@dataclass(frozen=True, slots=True)
class ContextScanProposedMemoryCandidate:
    candidate_id: str
    owner_id: str
    robot_id: str
    stage: str
    source_stage: str
    source_type: str
    source_id: str
    proposal_type: str
    proposed_memory_text: str
    review_reason: str
    confidence: str
    status: str
    approval_command: str
    rejection_command: str
    edit_command: str
    treated_as_fact: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CONTEXT_SCAN_PROPOSED_MEMORY_STAGE:
            raise ValueError("164P context scan memory candidates must identify the 164P stage.")
        if self.source_stage not in {CALENDAR_CONTEXT_SCAN_STAGE, GMAIL_READONLY_CONTEXT_SCAN_STAGE}:
            raise ValueError("164P context scan memory candidates require an approved context scan source stage.")
        if self.status != CONTEXT_SCAN_PROPOSED_MEMORY_STATUS:
            raise ValueError("164P context scan memory candidates must remain pending owner review.")
        if self.treated_as_fact:
            raise ValueError("164P context scan memory candidates must not be treated as facts.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.external_write_allowed,
            )
        ):
            raise ValueError("164P context scan memory candidates must not expand authority.")


@dataclass(frozen=True, slots=True)
class ContextScanProposedMemoryRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    source_stages: tuple[str, ...]
    candidates: tuple[ContextScanProposedMemoryCandidate, ...]
    read_only: bool
    owner_review_required: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    approval_decision_created: bool
    calendar_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CONTEXT_SCAN_PROPOSED_MEMORY_STAGE:
            raise ValueError("164P context scan proposed memory records must identify the 164P stage.")
        if not self.read_only:
            raise ValueError("164P context scan proposed memory records must be read-only.")
        if not self.owner_review_required:
            raise ValueError("164P context scan proposed memory records require owner review.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.approval_decision_created,
                self.calendar_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("164P context scan proposed memory records must not expand authority.")


def build_context_scan_proposed_memory_record(
    *,
    owner_id: str,
    robot_id: str,
    calendar_scan: CalendarContextScanRecord | None = None,
    gmail_scan: GmailReadonlyContextScanRecord | None = None,
) -> ContextScanProposedMemoryRecord:
    if calendar_scan is None and gmail_scan is None:
        raise ValueError("rejected_missing_context_scan_source")

    candidates: list[ContextScanProposedMemoryCandidate] = []
    source_stages: list[str] = []
    if calendar_scan is not None:
        if calendar_scan.scan_stage != CALENDAR_CONTEXT_SCAN_STAGE:
            raise ValueError("rejected_calendar_context_scan_source_stage")
        source_stages.append(calendar_scan.scan_stage)
        candidates.extend(_calendar_candidates(owner_id=owner_id, robot_id=robot_id, scan=calendar_scan))
    if gmail_scan is not None:
        if gmail_scan.stage != GMAIL_READONLY_CONTEXT_SCAN_STAGE:
            raise ValueError("rejected_gmail_context_scan_source_stage")
        source_stages.append(gmail_scan.stage)
        candidates.extend(_gmail_candidates(owner_id=owner_id, robot_id=robot_id, scan=gmail_scan))

    bounded_candidates = tuple(candidates[:MAX_PROPOSALS])
    return ContextScanProposedMemoryRecord(
        stage=CONTEXT_SCAN_PROPOSED_MEMORY_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="completed_with_candidates" if bounded_candidates else "empty",
        source_stages=tuple(dict.fromkeys(source_stages)),
        candidates=bounded_candidates,
        read_only=True,
        owner_review_required=True,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        approval_decision_created=False,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_context_scan_proposed_memory_record(record: ContextScanProposedMemoryRecord) -> str:
    lines = [
        "Context-Derived Memory Proposals",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Source stages: {', '.join(record.source_stages) if record.source_stages else 'none'}",
        "Owner review required: true",
        "Read-only: true",
        "Treated as facts: false",
        "Memory writes: disabled",
        "Memory Center mutation: disabled",
        "ProposedMemory writes: disabled",
        "Approval decisions: disabled in 164P",
        "Calendar writes: disabled",
        "Gmail send/modify: disabled",
        "LLM/model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "",
        "Candidates:",
    ]
    lines.extend(_candidate_lines(record))
    lines.extend(
        [
            "",
            "These are review suggestions only. Your robot does not remember them as facts yet.",
            "No memory was written.",
        ]
    )
    return "\n".join(lines)


def _calendar_candidates(
    *,
    owner_id: str,
    robot_id: str,
    scan: CalendarContextScanRecord,
) -> tuple[ContextScanProposedMemoryCandidate, ...]:
    candidates = []
    for candidate in scan.candidates:
        memory_text = _bounded_text(f"Calendar context: {candidate.proposed_context}")
        candidates.append(
            _candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                source_stage=CALENDAR_CONTEXT_SCAN_STAGE,
                source_type="calendar_context_candidate",
                source_id=candidate.candidate_id,
                proposal_type=candidate.candidate_type,
                proposed_memory_text=memory_text,
                review_reason=f"Derived from Calendar event '{candidate.event_summary}' after read-only context scan.",
                confidence=candidate.confidence,
            )
        )
    return tuple(candidates)


def _gmail_candidates(
    *,
    owner_id: str,
    robot_id: str,
    scan: GmailReadonlyContextScanRecord,
) -> tuple[ContextScanProposedMemoryCandidate, ...]:
    candidates = []
    for signal in scan.signals:
        memory_text = _bounded_text(f"Gmail context: {signal.summary}")
        candidates.append(
            _candidate(
                owner_id=owner_id,
                robot_id=robot_id,
                source_stage=GMAIL_READONLY_CONTEXT_SCAN_STAGE,
                source_type="gmail_context_signal",
                source_id=signal.signal_id,
                proposal_type=signal.signal_type,
                proposed_memory_text=memory_text,
                review_reason=f"Derived from Gmail message {signal.message_id} metadata/snippet after read-only context scan.",
                confidence=signal.confidence,
            )
        )
    return tuple(candidates)


def _candidate(
    *,
    owner_id: str,
    robot_id: str,
    source_stage: str,
    source_type: str,
    source_id: str,
    proposal_type: str,
    proposed_memory_text: str,
    review_reason: str,
    confidence: str,
) -> ContextScanProposedMemoryCandidate:
    candidate_id = _stable_id(owner_id, robot_id, source_stage, source_type, source_id, proposed_memory_text)
    return ContextScanProposedMemoryCandidate(
        candidate_id=candidate_id,
        owner_id=owner_id,
        robot_id=robot_id,
        stage=CONTEXT_SCAN_PROPOSED_MEMORY_STAGE,
        source_stage=source_stage,
        source_type=source_type,
        source_id=source_id,
        proposal_type=proposal_type,
        proposed_memory_text=proposed_memory_text,
        review_reason=review_reason,
        confidence=confidence,
        status=CONTEXT_SCAN_PROPOSED_MEMORY_STATUS,
        approval_command=f"/memory_approve {candidate_id}",
        rejection_command=f"/memory_reject {candidate_id}",
        edit_command=f"/memory_edit {candidate_id}",
        treated_as_fact=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        external_write_allowed=False,
    )


def _candidate_lines(record: ContextScanProposedMemoryRecord) -> list[str]:
    if not record.candidates:
        return ["- No context-derived memory candidates are available yet."]
    return [
        (
            f"- {candidate.candidate_id}: {candidate.proposed_memory_text} "
            f"(pending owner review; approve with {candidate.approval_command}, "
            f"edit with {candidate.edit_command}, or reject with {candidate.rejection_command})"
        )
        for candidate in record.candidates
    ]


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_MEMORY_TEXT_CHARS:
        return stripped
    return stripped[: MAX_MEMORY_TEXT_CHARS - 3].rstrip() + "..."


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:context-scan-proposed-memory:" + ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.context_scan_proposed_memory")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = ContextScanProposedMemoryRecord(
        stage=CONTEXT_SCAN_PROPOSED_MEMORY_STAGE,
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        status="empty",
        source_stages=(),
        candidates=(),
        read_only=True,
        owner_review_required=True,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        approval_decision_created=False,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_context_scan_proposed_memory_record(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
