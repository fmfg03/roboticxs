from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.brief_memory_proposal import BRIEF_MEMORY_PROPOSAL_STAGE


BRIEF_MEMORY_APPROVAL_STAGE = "145P"
APPROVAL_CHOICES = frozenset({"approve", "reject"})
DECISION_STATUS_BY_CHOICE = {
    "approve": "approved_pending_writeback",
    "reject": "rejected_no_write",
}


@dataclass(frozen=True, slots=True)
class BriefMemoryApprovalDecisionRecord:
    stage: str
    owner_id: str
    robot_id: str
    candidate_id: str
    source_stage: str
    decision_id: str
    choice: str
    decision_status: str
    local_audit_created: bool
    owner_requested: bool
    read_only_candidate: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    writeback_executed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != BRIEF_MEMORY_APPROVAL_STAGE:
            raise ValueError("145P brief memory decisions must identify the 145P stage.")
        if self.source_stage != BRIEF_MEMORY_PROPOSAL_STAGE:
            raise ValueError("145P brief memory decisions must originate from 144P candidates.")
        if self.choice not in APPROVAL_CHOICES:
            raise ValueError("145P brief memory decisions require approve or reject.")
        if self.decision_status != DECISION_STATUS_BY_CHOICE[self.choice]:
            raise ValueError("145P brief memory decision status must match the owner choice.")
        if not self.owner_requested or not self.local_audit_created:
            raise ValueError("145P brief memory decisions require explicit owner request and local audit.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.writeback_executed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("145P brief memory decisions must not expand authority.")


def build_brief_memory_approval_decision(
    *,
    owner_id: str,
    robot_id: str,
    candidate_id: str,
    choice: str,
) -> BriefMemoryApprovalDecisionRecord:
    normalized_candidate_id = candidate_id.strip()
    normalized_choice = choice.strip().lower()
    if not normalized_candidate_id:
        raise ValueError("rejected_missing_brief_memory_candidate_id")
    if normalized_choice not in APPROVAL_CHOICES:
        raise ValueError("rejected_invalid_brief_memory_approval_choice")
    return BriefMemoryApprovalDecisionRecord(
        stage=BRIEF_MEMORY_APPROVAL_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        candidate_id=normalized_candidate_id,
        source_stage=BRIEF_MEMORY_PROPOSAL_STAGE,
        decision_id=_stable_decision_id(owner_id, robot_id, normalized_candidate_id, normalized_choice),
        choice=normalized_choice,
        decision_status=DECISION_STATUS_BY_CHOICE[normalized_choice],
        local_audit_created=True,
        owner_requested=True,
        read_only_candidate=True,
        memory_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        writeback_executed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_brief_memory_approval_decision(record: BriefMemoryApprovalDecisionRecord) -> str:
    return "\n".join(
        [
            "Brief Memory Decision",
            "",
            f"Stage: {record.stage}",
            f"Decision id: {record.decision_id}",
            f"Candidate id: {record.candidate_id}",
            f"Choice: {record.choice}",
            f"Decision status: {record.decision_status}",
            f"Source stage: {record.source_stage}",
            "Owner requested: true",
            "Local audit created: true",
            "Memory writes: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Writeback executed: false",
            "Calendar writes: disabled",
            "LLM/model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No memory was written.",
        ]
    )


def _stable_decision_id(owner_id: str, robot_id: str, candidate_id: str, choice: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"roboticxs:brief-memory-approval:{owner_id}:{robot_id}:{candidate_id}:{choice}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.brief_memory_approval")
    parser.add_argument("choice", choices=sorted(APPROVAL_CHOICES))
    parser.add_argument("candidate_id")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = build_brief_memory_approval_decision(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        candidate_id=args.candidate_id,
        choice=args.choice,
    )
    print(render_brief_memory_approval_decision(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
