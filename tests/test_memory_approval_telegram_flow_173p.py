from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pytest

from app.memory_approval_telegram_flow import (
    MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE,
    MEMORY_RECEIPT_STATUS_APPROVED,
    MEMORY_RECEIPT_STATUS_CANDIDATE_NOT_FOUND,
    MEMORY_RECEIPT_STATUS_EDIT_PENDING,
    MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID,
    MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT,
    MEMORY_RECEIPT_STATUS_REJECTED,
    MemoryApprovalTelegramReceipt,
    build_memory_approval_telegram_receipt,
    build_memory_review_inbox,
    render_memory_approval_telegram_receipt,
    render_memory_review_inbox,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_APPROVAL_TELEGRAM_FLOW_173P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


@dataclass(frozen=True, slots=True)
class PendingProposal:
    proposal_id: str = "candidate-173p"
    owner_id: str = "local-owner"
    robot_id: str = "roboticxs-dev"
    proposal_type: str = "business_context_candidate"
    proposed_memory_text: str = "Victor prefers ROI-first proposals."
    confidence: str = "high"
    review_reason: str = "Useful for future meeting prep."
    status: str = "pending_user_review"
    source_stage: str = "164P"


def review_inbox(*proposals: object):
    return build_memory_review_inbox(
        snapshot=build_memory_center_telegram_snapshot(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            source_bundle=TelegramMemoryCenterSourceBundle(pending_memory_proposals=proposals),
        )
    )


def test_173p_memory_review_inbox_renders_empty_state_without_writes():
    inbox = review_inbox()
    rendered = render_memory_review_inbox(inbox)

    assert inbox.stage == MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE
    assert inbox.status == "empty"
    assert inbox.candidates == ()
    assert inbox.local_read_only is True
    assert inbox.no_memory_written is True
    assert inbox.memory_store_written is False
    assert inbox.memory_center_mutated is False
    assert inbox.source_evidence_deleted is False
    assert inbox.model_call_allowed is False
    assert inbox.external_write_allowed is False
    assert "Empty: no pending memory proposals" in rendered
    assert "No memory was written." in rendered


def test_173p_memory_review_inbox_lists_visible_pending_candidates():
    inbox = review_inbox(PendingProposal())
    rendered = render_memory_review_inbox(inbox)

    assert inbox.status == "pending"
    assert len(inbox.candidates) == 1
    assert "candidate-173p | business_context_candidate: Victor prefers ROI-first proposals." in rendered
    assert "/memory_approve candidate-173p" in rendered
    assert "/memory_reject candidate-173p" in rendered
    assert "/memory_edit candidate-173p <text>" in rendered


@pytest.mark.parametrize(
    ("choice", "status"),
    [
        ("approve", MEMORY_RECEIPT_STATUS_APPROVED),
        ("reject", MEMORY_RECEIPT_STATUS_REJECTED),
        ("edit", MEMORY_RECEIPT_STATUS_EDIT_PENDING),
    ],
)
def test_173p_memory_decisions_create_local_receipts_only(choice: str, status: str):
    receipt = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-173p",
        choice=choice,
        inbox=review_inbox(PendingProposal()),
        edited_memory_text="Victor prefers short ROI-first prep." if choice == "edit" else "",
    )

    assert receipt.stage == MEMORY_APPROVAL_TELEGRAM_FLOW_STAGE
    assert receipt.choice == choice
    assert receipt.decision_status == status
    assert receipt.proposed_memory_text == "Victor prefers ROI-first proposals."
    assert receipt.local_receipt_created is True
    assert receipt.owner_requested is True
    assert receipt.no_memory_written is True
    assert receipt.memory_store_written is False
    assert receipt.memory_center_mutated is False
    assert receipt.source_evidence_deleted is False
    assert receipt.proposed_memory_written is False
    assert receipt.writeback_executed is False
    assert receipt.model_call_allowed is False
    assert receipt.external_write_allowed is False


def test_173p_blocks_missing_unknown_and_edit_without_text():
    inbox = review_inbox(PendingProposal())

    missing = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="",
        choice="approve",
        inbox=inbox,
    )
    unknown = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="missing",
        choice="approve",
        inbox=inbox,
    )
    edit_without_text = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-173p",
        choice="edit",
        inbox=inbox,
    )

    assert missing.decision_status == MEMORY_RECEIPT_STATUS_MISSING_CANDIDATE_ID
    assert unknown.decision_status == MEMORY_RECEIPT_STATUS_CANDIDATE_NOT_FOUND
    assert edit_without_text.decision_status == MEMORY_RECEIPT_STATUS_MISSING_EDIT_TEXT


def test_173p_rejects_owner_robot_mismatch_invalid_choice_and_authority_expansion():
    inbox = review_inbox(PendingProposal())
    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_memory_approval_telegram_receipt(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            candidate_id="candidate-173p",
            choice="approve",
            inbox=inbox,
        )
    with pytest.raises(ValueError, match="invalid_memory_approval_choice"):
        build_memory_approval_telegram_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            candidate_id="candidate-173p",
            choice="pin",
            inbox=inbox,
        )
    valid = build_memory_approval_telegram_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-173p",
        choice="reject",
        inbox=inbox,
    )
    with pytest.raises(ValueError, match="must not expand authority"):
        MemoryApprovalTelegramReceipt(**{**asdict(valid), "memory_center_mutated": True})


def test_173p_render_declares_no_memory_written():
    rendered = render_memory_approval_telegram_receipt(
        build_memory_approval_telegram_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            candidate_id="candidate-173p",
            choice="edit",
            inbox=review_inbox(PendingProposal()),
            edited_memory_text="Victor prefers short ROI-first prep.",
        )
    )

    assert "Memory Approval Decision" in rendered
    assert "Stage: 173P" in rendered
    assert "Choice: edit" in rendered
    assert "Status: edit_pending_local_receipt" in rendered
    assert "Edited memory text: Victor prefers short ROI-first prep." in rendered
    assert "No memory was written." in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_173p_reference_and_roadmap_close_memory_approval_flow_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "173P is Memory Approval Telegram Flow v0 only." in reference
    assert "No memory was written" in reference
    assert "does not authorize Memory Store writes" in reference
    assert '"stage_id":"173P","stage_name":"Memory Approval Telegram Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "203P and later remain unauthorized" in roadmap
