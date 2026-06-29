from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_draft_queue import build_action_draft_queue
from app.proactive_suggestion_loop import (
    ProactiveSuggestionSignal,
    build_proactive_suggestion_loop_records,
)
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox
from app.user_confirmation_runtime import (
    CONFIRMATION_STATUS_APPROVED,
    CONFIRMATION_STATUS_DRAFT_NOT_FOUND,
    CONFIRMATION_STATUS_EDIT_PENDING,
    CONFIRMATION_STATUS_MISSING_DRAFT_ID,
    CONFIRMATION_STATUS_MISSING_EDIT_TEXT,
    USER_CONFIRMATION_RUNTIME_STAGE,
    UserConfirmationReceipt,
    build_user_confirmation_receipt,
    render_user_confirmation_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/USER_CONFIRMATION_RUNTIME_178P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def draft_queue():
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-178p",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="email_thread_no_followup",
                title="Draft client follow-up",
                summary="thread needs follow-up",
                source_refs=("gmail:thread-178p",),
            ),
        ),
    )
    inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=suggestions,
    )
    decision = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=inbox.items[0].suggestion_id,
        choice="create_draft",
        inbox=inbox,
    )
    return build_action_draft_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        decisions=(decision,),
    )


@pytest.mark.parametrize("choice", ["approve", "reject", "edit", "expire"])
def test_178p_records_supported_confirmation_receipts_without_execution(choice: str):
    queue = draft_queue()
    draft = queue.drafts[0]
    receipt = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=draft.draft_id,
        choice=choice,
        queue=queue,
        edited_text="Shorter follow-up text" if choice == "edit" else "",
    )

    assert receipt.stage == USER_CONFIRMATION_RUNTIME_STAGE
    assert receipt.choice == choice
    assert receipt.draft_title == "Draft for: Draft client follow-up"
    assert receipt.local_receipt_created is True
    assert receipt.owner_requested is True
    assert receipt.action_executed is False
    assert receipt.approved_output_exported is False
    assert receipt.gmail_draft_created is False
    assert receipt.gmail_send_allowed is False
    assert receipt.gmail_modify_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.task_persisted is False
    assert receipt.memory_center_mutated is False
    assert receipt.model_call_allowed is False
    assert receipt.tool_call_allowed is False
    assert receipt.worker_dispatch_allowed is False
    assert receipt.external_write_allowed is False


def test_178p_blocks_missing_unknown_and_missing_edit_text_as_local_receipts():
    queue = draft_queue()
    draft = queue.drafts[0]

    missing = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id="",
        choice="approve",
        queue=queue,
    )
    unknown = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id="missing-draft",
        choice="approve",
        queue=queue,
    )
    missing_edit = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=draft.draft_id,
        choice="edit",
        queue=queue,
    )

    assert missing.confirmation_status == CONFIRMATION_STATUS_MISSING_DRAFT_ID
    assert unknown.confirmation_status == CONFIRMATION_STATUS_DRAFT_NOT_FOUND
    assert missing_edit.confirmation_status == CONFIRMATION_STATUS_MISSING_EDIT_TEXT
    assert missing.action_executed is False
    assert unknown.action_executed is False
    assert missing_edit.action_executed is False


def test_178p_edit_and_approve_statuses_are_local_only():
    queue = draft_queue()
    draft = queue.drafts[0]

    approved = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=draft.draft_id,
        choice="approve",
        queue=queue,
    )
    edited = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=draft.draft_id,
        choice="edit",
        queue=queue,
        edited_text="Use a warmer opener.",
    )

    assert approved.confirmation_status == CONFIRMATION_STATUS_APPROVED
    assert edited.confirmation_status == CONFIRMATION_STATUS_EDIT_PENDING
    assert edited.edited_text == "Use a warmer opener."
    assert approved.approved_output_exported is False
    assert edited.approved_output_exported is False


def test_178p_rejects_owner_robot_mismatch_invalid_choice_and_authority_expansion():
    queue = draft_queue()
    draft = queue.drafts[0]

    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_user_confirmation_receipt(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            draft_id=draft.draft_id,
            choice="approve",
            queue=queue,
        )
    with pytest.raises(ValueError, match="invalid_user_confirmation_choice"):
        build_user_confirmation_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            draft_id=draft.draft_id,
            choice="send",
            queue=queue,
        )

    valid = build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=draft.draft_id,
        choice="approve",
        queue=queue,
    )
    with pytest.raises(ValueError, match="must not expand authority"):
        UserConfirmationReceipt(**{**asdict(valid), "external_write_allowed": True})


def test_178p_render_declares_confirmation_receipt_and_boundaries():
    queue = draft_queue()
    rendered = render_user_confirmation_receipt(
        build_user_confirmation_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            draft_id=queue.drafts[0].draft_id,
            choice="approve",
            queue=queue,
        )
    )

    assert "User Confirmation Receipt" in rendered
    assert "Stage: 178P" in rendered
    assert "Status: approved_pending_export_local_receipt" in rendered
    assert "Action executed: false" in rendered
    assert "Approved output export: disabled" in rendered
    assert "Gmail draft creation: disabled" in rendered
    assert "Gmail send: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_178p_reference_and_roadmap_close_confirmation_runtime_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "178P is User Confirmation Runtime v0 only." in reference
    assert "Approved output export" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"178P","stage_name":"User Confirmation Runtime v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "196P and later remain unauthorized" in roadmap
