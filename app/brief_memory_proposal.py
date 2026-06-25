from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol
from app.meeting_prep_pack import (
    MEETING_PREP_PACK_STAGE,
    MeetingPrepPackRecord,
    run_meeting_prep_pack,
)
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


BRIEF_MEMORY_PROPOSAL_STAGE = "144P"
BRIEF_MEMORY_PROPOSAL_STATUS = "pending_owner_review"


@dataclass(frozen=True, slots=True)
class BriefMemoryProposalCandidate:
    candidate_id: str
    owner_id: str
    robot_id: str
    stage: str
    source_stage: str
    suggestion_id: str
    proposal_type: str
    proposed_memory_text: str
    review_reason: str
    status: str
    approval_command: str
    rejection_command: str
    treated_as_fact: bool

    def __post_init__(self) -> None:
        if self.stage != BRIEF_MEMORY_PROPOSAL_STAGE:
            raise ValueError("144P brief memory candidates must identify the 144P stage.")
        if self.source_stage != MEETING_PREP_PACK_STAGE:
            raise ValueError("144P brief memory candidates must originate from the active Meeting Prep Pack stage.")
        if self.status != BRIEF_MEMORY_PROPOSAL_STATUS:
            raise ValueError("144P brief memory candidates must remain pending owner review.")
        if self.treated_as_fact:
            raise ValueError("144P brief memory candidates must not be treated as facts.")


@dataclass(frozen=True, slots=True)
class BriefMemoryProposalRecord:
    stage: str
    owner_id: str
    robot_id: str
    source_stage: str
    suggestion_id: str
    status: str
    candidates: tuple[BriefMemoryProposalCandidate, ...]
    read_only: bool
    owner_review_required: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    approval_decision_created: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != BRIEF_MEMORY_PROPOSAL_STAGE:
            raise ValueError("144P brief memory proposal records must identify the 144P stage.")
        if self.source_stage != MEETING_PREP_PACK_STAGE:
            raise ValueError("144P brief memory proposal records must originate from the active Meeting Prep Pack stage.")
        if not self.read_only:
            raise ValueError("144P brief memory proposal records must be read-only.")
        if not self.owner_review_required:
            raise ValueError("144P brief memory proposal records require owner review.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.approval_decision_created,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("144P brief memory proposal records must not expand authority.")


def build_brief_memory_proposal_record(
    *,
    prep_pack: MeetingPrepPackRecord,
) -> BriefMemoryProposalRecord:
    if prep_pack.stage != MEETING_PREP_PACK_STAGE:
        raise ValueError("rejected_brief_memory_proposal_source_stage")
    candidates = _candidates_from_prep_pack(prep_pack)
    return BriefMemoryProposalRecord(
        stage=BRIEF_MEMORY_PROPOSAL_STAGE,
        owner_id=prep_pack.owner_id,
        robot_id=prep_pack.robot_id,
        source_stage=MEETING_PREP_PACK_STAGE,
        suggestion_id=prep_pack.suggestion_id,
        status="completed_with_candidates" if candidates else "empty",
        candidates=candidates,
        read_only=True,
        owner_review_required=True,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        approval_decision_created=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def run_brief_memory_proposal_record(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    suggestion_id: str,
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> BriefMemoryProposalRecord:
    prep_pack = run_meeting_prep_pack(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        calendar_http_client=calendar_http_client,
        memory_source_bundle=memory_source_bundle,
    )
    return build_brief_memory_proposal_record(prep_pack=prep_pack)


def render_brief_memory_proposal_record(record: BriefMemoryProposalRecord) -> str:
    return "\n".join(
        [
            "Brief Memory Proposals",
            "",
            f"Stage: {record.stage}",
            f"Status: {record.status}",
            f"Source stage: {record.source_stage}",
            f"Suggestion id: {record.suggestion_id}",
            "Owner review required: true",
            "Read-only: true",
            "Treated as facts: false",
            "Memory writes: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Approval decisions: disabled in 144P",
            "Calendar writes: disabled",
            "LLM/model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "Candidates:",
            *_candidate_lines(record),
            "",
            "No memory was written.",
        ]
    )


def render_brief_memory_candidate_section(record: BriefMemoryProposalRecord) -> tuple[str, ...]:
    return (
        "Memory candidates:",
        *_candidate_lines(record),
        "Memory candidates are pending owner review and are not treated as facts.",
        "No memory was written.",
    )


def _candidates_from_prep_pack(prep_pack: MeetingPrepPackRecord) -> tuple[BriefMemoryProposalCandidate, ...]:
    if prep_pack.status != "completed" or not prep_pack.suggestion_validated:
        return ()
    meeting_line = prep_pack.meeting_lines[0] if prep_pack.meeting_lines else prep_pack.suggestion_id
    proposed_text = f"For {meeting_line}, prepare agenda, open questions, watchpoints, and relevant memory context before the meeting."
    candidate_id = _stable_id(
        prep_pack.owner_id,
        prep_pack.robot_id,
        prep_pack.suggestion_id,
        proposed_text,
    )
    return (
        BriefMemoryProposalCandidate(
            candidate_id=candidate_id,
            owner_id=prep_pack.owner_id,
            robot_id=prep_pack.robot_id,
            stage=BRIEF_MEMORY_PROPOSAL_STAGE,
            source_stage=MEETING_PREP_PACK_STAGE,
            suggestion_id=prep_pack.suggestion_id,
            proposal_type="meeting_prep_preference_candidate",
            proposed_memory_text=proposed_text,
            review_reason="Derived from an owner-requested Meeting Prep Pack.",
            status=BRIEF_MEMORY_PROPOSAL_STATUS,
            approval_command=f"/memory_approve {candidate_id}",
            rejection_command=f"/memory_reject {candidate_id}",
            treated_as_fact=False,
        ),
    )


def _candidate_lines(record: BriefMemoryProposalRecord) -> tuple[str, ...]:
    if not record.candidates:
        return ("No brief-derived memory candidates are available for this prep pack.",)
    return tuple(
        f"{candidate.candidate_id}: {candidate.proposed_memory_text} "
        f"(pending owner review; approve with {candidate.approval_command} or reject with {candidate.rejection_command})"
        for candidate in record.candidates
    )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:brief-memory-proposal:" + ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.brief_memory_proposal")
    parser.add_argument("suggestion_id")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_brief_memory_proposal_record(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        suggestion_id=args.suggestion_id,
    )
    print(render_brief_memory_proposal_record(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
