from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.telegram_memory_center_commands import (
    TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE,
    TelegramMemoryCenterPendingProposal,
    TelegramMemoryCenterSnapshot,
)


MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE = "173P"
MEMORY_APPROVAL_CHOICES = frozenset({"approve", "reject", "edit"})
MEMORY_REVIEW_STATUS_EMPTY = "empty"
MEMORY_REVIEW_STATUS_PENDING = "pending"
MEMORY_RECEIPT_STATUS_APPROVED = "approved_pending_writeback_local_receipt"
MEMORY_RECEIPT_STATUS_REJECTED = "rejected_local_receipt"
MEMORY_RECEIPT_STATUS_EDIT_PENDING = "edit_pending_local_receipt"
MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID = "blocked_missing_candidate_id"
MEMORY_RECEIPT_STATUS_CANDIDATE_NOT_FOUND = "blocked_candidate_not_found"
MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT = "blocked_missing_edit_text"


@dataclass(frozen=True, slots=True)
class MemoryReviewInbox:
    stage: str
    owner_id: str
    robot_id: str
    source_stage: str
    status: str
    candidates: tuple[TelegramMemoryCenterPendingProposal, ...]
    local_read_only: bool
    no_memory_written: bool
    memory_store_written: bool
    memory_center_mutated: bool
    source_evidence_deleted: bool
    model_call_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE:
            raise ValueError("173P memory review inbox must identify the 173P stage.")
        if self.source_stage != TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE:
            raise ValueError("173P memory review inbox must derive from Telegram Memory Center visibility.")
        if self.status not in {MEMORY_REVIEW_STATUS_EMPTY, MEMORY_REVIEW_STATUS_PENDING}:
            raise ValueError("173P memory review inbox status must be supported.")
        if not self.local_read_only or not self.no_memory_written:
            raise ValueError("173P memory review inbox must remain local read-only with no memory write.")
        if any(
            (
                self.memory_store_written,
                self.memory_center_mutated,
                self.source_evidence_deleted,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("173P memory review inbox must not expand authority.")


@dataclass(frozen=True, slots=True)
class MemoryApprovalTelegramReceipt:
    stage: str
    owner_id: str
    robot_id: str
    candidate_id: str
    source_stage: str
    decision_id: str
    choice: str
    decision_status: str
    proposed_memory_text: str
    edited_memory_text: str
    local_receipt_created: bool
    owner_requested: bool
    no_memory_written: bool
    memory_store_written: bool
    memory_center_mutated: bool
    source_evidence_deleted: bool
    proposed_memory_written: bool
    writeback_executed: bool
    model_call_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE:
            raise ValueError("173P memory approval receipts must identify the 173P stage.")
        if self.source_stage != TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE:
            raise ValueError("173P memory approval receipts must derive from Telegram Memory Center visibility.")
        if self.choice not in MEMORY_APPROVAL_CHOICES:
            raise ValueError("173P memory approval receipts require approve, reject, or edit.")
        if self.decision_status not in {
            MEMORY_RECEIPT_STATUS_APPROVED,
            MEMORY_RECEIPT_STATUS_REJECTED,
            MEMORY_RECEIPT_STATUS_EDIT_PENDING,
            MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID,
            MEMORY_RECEIPT_STATUS_CANDIDATE_NOT_FOUND,
            MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT,
        }:
            raise ValueError("173P memory approval receipt status must be supported.")
        if not self.local_receipt_created or not self.owner_requested or not self.no_memory_written:
            raise ValueError("173P memory approval receipts require owner request, local receipt, and no memory write.")
        if any(
            (
                self.memory_store_written,
                self.memory_center_mutated,
                self.source_evidence_deleted,
                self.proposed_memory_written,
                self.writeback_executed,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("173P memory approval receipts must not expand authority.")


def build_memory_review_inbox(*, snapshot: TelegramMemoryCenterSnapshot) -> MemoryReviewInbox:
    return MemoryReviewInbox(
        stage=MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE,
        owner_id=snapshot.owner_id,
        robot_id=snapshot.robot_id,
        source_stage=snapshot.stage,
        status=MEMORY_REVIEW_STATUS_PENDING if snapshot.pending_proposals else MEMORY_REVIEW_STATUS_EMPTY,
        candidates=snapshot.pending_proposals,
        local_read_only=True,
        no_memory_written=True,
        memory_store_written=False,
        memory_center_mutated=False,
        source_evidence_deleted=False,
        model_call_allowed=False,
        external_write_allowed=False,
    )


def build_memory_approval_telegram_receipt(
    *,
    owner_id: str,
    robot_id: str,
    candidate_id: str,
    choice: str,
    inbox: MemoryReviewInbox,
    edited_memory_text: str = "",
) -> MemoryApprovalTelegramReceipt:
    normalized_candidate_id = candidate_id.strip()
    normalized_choice = choice.strip().lower()
    normalized_edit_text = " ".join(edited_memory_text.split())
    if normalized_choice not in MEMORY_APPROVAL_CHOICES:
        raise ValueError("rejected_invalid_memory_approval_choice")
    if inbox.owner_id != owner_id or inbox.robot_id != robot_id:
        raise ValueError("rejected_memory_review_inbox_owner_robot_mismatch")
    if not normalized_candidate_id:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            candidate_id="",
            choice=normalized_choice,
            decision_status=MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID,
            candidate=None,
            edited_memory_text="",
        )
    candidate = next(
        (item for item in inbox.candidates if item.proposal_id == normalized_candidate_id),
        None,
    )
    if candidate is None:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            candidate_id=normalized_candidate_id,
            choice=normalized_choice,
            decision_status=MEMORY_RECEIPT_STATUS_CANDIDATE_NOT_FOUND,
            candidate=None,
            edited_memory_text="",
        )
    if normalized_choice == "edit" and not normalized_edit_text:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            candidate_id=normalized_candidate_id,
            choice=normalized_choice,
            decision_status=MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT,
            candidate=candidate,
            edited_memory_text="",
        )
    status_by_choice = {
        "approve": MEMORY_RECEIPT_STATUS_APPROVED,
        "reject": MEMORY_RECEIPT_STATUS_REJECTED,
        "edit": MEMORY_RECEIPT_STATUS_EDIT_PENDING,
    }
    return _receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        candidate_id=normalized_candidate_id,
        choice=normalized_choice,
        decision_status=status_by_choice[normalized_choice],
        candidate=candidate,
        edited_memory_text=normalized_edit_text if normalized_choice == "edit" else "",
    )


def render_memory_review_inbox(inbox: MemoryReviewInbox) -> str:
    lines = [
        "Memory Approval Review",
        "",
        f"Stage: {inbox.stage}",
        f"Status: {inbox.status}",
        f"Pending candidates: {len(inbox.candidates)}",
        "Read-only: true",
        "",
        "Candidates:",
    ]
    if not inbox.candidates:
        lines.append("- Empty: no pending memory proposals are visible right now.")
    else:
        for candidate in inbox.candidates:
            lines.append(
                f"- {candidate.proposal_id} | {candidate.proposal_type}: {candidate.proposed_memory_text} "
                f"(approve: /memory_approve {candidate.proposal_id}; "
                f"reject: /memory_reject {candidate.proposal_id}; "
                f"edit: /memory_edit {candidate.proposal_id} <text>)"
            )
    lines.extend(
        [
            "",
            "No memory was written.",
            "Memory Store write: disabled",
            "Memory Center mutation: disabled",
            "Source evidence deletion: disabled",
            "Model calls: disabled",
            "External writes: disabled",
        ]
    )
    return "\n".join(lines)


def render_memory_approval_telegram_receipt(record: MemoryApprovalTelegramReceipt) -> str:
    lines = [
        "Memory Approval Decision",
        "",
        f"Stage: {record.stage}",
        f"Decision id: {record.decision_id}",
        f"Candidate id: {record.candidate_id or 'none'}",
        f"Choice: {record.choice}",
        f"Status: {record.decision_status}",
        f"Proposed memory: {record.proposed_memory_text or 'not available'}",
    ]
    if record.edited_memory_text:
        lines.append(f"Edited memory text: {record.edited_memory_text}")
    lines.extend(
        [
            "Owner requested: true",
            "Local receipt created: true",
            "",
            *_meaning_lines(record),
            "",
            "No memory was written.",
            "Memory Store write: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Writeback executed: false",
            "Source evidence deleted: false",
            "Model calls: disabled",
            "External writes: disabled",
        ]
    )
    return "\n".join(lines)


def _meaning_lines(record: MemoryApprovalTelegramReceipt) -> tuple[str, ...]:
    if record.decision_status == MEMORY_RECEIPT_STATUS_APPROVED:
        return (
            "Meaning:",
            "- Approval intent was recorded locally.",
            "- The memory is not a fact until a later writeback stage is approved.",
        )
    if record.decision_status == MEMORY_RECEIPT_STATUS_REJECTED:
        return (
            "Meaning:",
            "- Rejection intent was recorded locally.",
            "- Source evidence was not deleted.",
        )
    if record.decision_status == MEMORY_RECEIPT_STATUS_EDIT_PENDING:
        return (
            "Meaning:",
            "- Edited memory text was recorded as a local pending intent.",
            "- The original proposal was not mutated.",
        )
    if record.decision_status == MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT:
        return (
            "Meaning:",
            "- Edit was blocked because no replacement text was provided.",
            "- Use /memory_edit <candidate_id> <text>.",
        )
    if record.decision_status == MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID:
        return (
            "Meaning:",
            "- No candidate id was provided.",
            "- Use /memory_review to inspect visible pending candidates.",
        )
    return (
        "Meaning:",
        "- That candidate is not available in the current local memory review inbox.",
        "- No memory decision was applied.",
    )


def _receipt(
    *,
    owner_id: str,
    robot_id: str,
    candidate_id: str,
    choice: str,
    decision_status: str,
    candidate: TelegramMemoryCenterPendingProposal | None,
    edited_memory_text: str,
) -> MemoryApprovalTelegramReceipt:
    proposed_memory_text = "" if candidate is None else candidate.proposed_memory_text
    return MemoryApprovalTelegramReceipt(
        stage=MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        candidate_id=candidate_id,
        source_stage=TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE,
        decision_id=_stable_decision_id(owner_id, robot_id, candidate_id, choice, decision_status, edited_memory_text),
        choice=choice,
        decision_status=decision_status,
        proposed_memory_text=proposed_memory_text,
        edited_memory_text=edited_memory_text,
        local_receipt_created=True,
        owner_requested=True,
        no_memory_written=True,
        memory_store_written=False,
        memory_center_mutated=False,
        source_evidence_deleted=False,
        proposed_memory_written=False,
        writeback_executed=False,
        model_call_allowed=False,
        external_write_allowed=False,
    )


def _stable_decision_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:memory-approval-telegram-flow:" + ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.memory_approval_telegram_flow")
    parser.add_argument("choice", nargs="?", choices=sorted(MEMORY_APPROVAL_CHOICES))
    parser.add_argument("candidate_id", nargs="?", default="")
    parser.add_argument("edited_memory_text", nargs="*", default=())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    from app.telegram_memory_center_commands import build_memory_center_telegram_snapshot

    inbox = build_memory_review_inbox(
        snapshot=build_memory_center_telegram_snapshot(owner_id="local-owner", robot_id="roboticxs-dev")
    )
    if args.choice is None:
        if args.as_json:
            print(json.dumps(asdict(inbox), sort_keys=True, indent=2))
        else:
            print(render_memory_review_inbox(inbox))
        return 0
    receipt = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id=args.candidate_id,
        choice=args.choice,
        inbox=inbox,
        edited_memory_text=" ".join(args.edited_memory_text),
    )
    if args.as_json:
        print(json.dumps(asdict(receipt), sort_keys=True, indent=2))
    else:
        print(render_memory_approval_telegram_receipt(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
