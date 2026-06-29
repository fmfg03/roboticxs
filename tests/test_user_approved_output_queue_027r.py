from __future__ import annotations

from dataclasses import asdict

import pytest

from app.user_approved_output_queue import (
    APPROVAL_DECISION_APPROVED,
    APPROVAL_DECISION_NOT_FOUND,
    APPROVAL_DECISION_REJECTED,
    USER_APPROVED_OUTPUT_QUEUE_STAGE,
    UserApprovedOutputDecisionReceipt,
    build_user_approved_output_decision_receipt,
    build_user_approved_output_item,
    build_user_approved_output_queue,
    render_user_approved_output_decision_receipt,
    render_user_approved_output_queue,
)


def approval_item(**overrides):
    values = {
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "output_type": "email_reply",
        "title": "Follow up with client",
        "body_preview": "Thanks for the meeting. Here are the next steps.",
        "source": "local_fixture",
        "approval_id": "approval-027r",
    }
    values.update(overrides)
    return build_user_approved_output_item(**values)


def test_027r_approvals_empty_state_is_local_only():
    queue = build_user_approved_output_queue(owner_id="local-owner", robot_id="roboticxs-dev")
    rendered = render_user_approved_output_queue(queue)

    assert queue.stage == USER_APPROVED_OUTPUT_QUEUE_STAGE
    assert queue.status == "empty"
    assert queue.items == ()
    assert queue.email_send_allowed is False
    assert queue.gmail_draft_creation_allowed is False
    assert queue.calendar_write_allowed is False
    assert queue.external_api_write_allowed is False
    assert "No pending approvals." in rendered
    assert "Approve means record local approval; it does not execute." in rendered
    assert "No external action was taken." in rendered


def test_027r_approvals_lists_pending_items_without_external_actions():
    queue = build_user_approved_output_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(approval_item(),),
    )
    rendered = render_user_approved_output_queue(queue)

    assert queue.status == "pending_approvals"
    assert queue.items[0].approval_id == "approval-027r"
    assert queue.items[0].email_sent is False
    assert queue.items[0].gmail_draft_created is False
    assert queue.items[0].calendar_event_created is False
    assert queue.items[0].external_action_performed is False
    assert "approval-027r | email_reply | pending_user_approval" in rendered
    assert "Follow up with client" in rendered
    assert "External API writes: disabled" in rendered


def test_027r_approve_records_local_receipt_without_execution():
    queue = build_user_approved_output_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(approval_item(),),
    )

    receipt = build_user_approved_output_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        approval_id="approval-027r",
        decision="approve",
        queue=queue,
    )
    rendered = render_user_approved_output_decision_receipt(receipt)

    assert receipt.status == APPROVAL_DECISION_APPROVED
    assert receipt.queue_state_updated_locally is True
    assert receipt.email_sent is False
    assert receipt.gmail_draft_created is False
    assert receipt.calendar_event_created is False
    assert receipt.external_action_performed is False
    assert "Approved locally." in rendered
    assert "No email sent." in rendered
    assert "No Gmail draft created." in rendered
    assert "No calendar event created." in rendered
    assert "No external action performed." in rendered
    assert "Receipt recorded." in rendered


def test_027r_reject_records_local_receipt_without_execution():
    queue = build_user_approved_output_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(approval_item(),),
    )

    receipt = build_user_approved_output_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        approval_id="approval-027r",
        decision="reject",
        queue=queue,
    )
    rendered = render_user_approved_output_decision_receipt(receipt)

    assert receipt.status == APPROVAL_DECISION_REJECTED
    assert receipt.queue_state_updated_locally is True
    assert receipt.email_sent is False
    assert receipt.calendar_event_created is False
    assert "Decision recorded locally." in rendered
    assert "No email sent." in rendered
    assert "No external action performed." in rendered


def test_027r_invalid_approval_id_fails_closed():
    queue = build_user_approved_output_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(approval_item(),),
    )

    receipt = build_user_approved_output_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        approval_id="missing-approval",
        decision="approve",
        queue=queue,
    )

    assert receipt.status == APPROVAL_DECISION_NOT_FOUND
    assert receipt.queue_state_updated_locally is False
    assert receipt.email_sent is False
    assert receipt.gmail_draft_created is False
    assert receipt.calendar_event_created is False
    assert receipt.external_action_performed is False


def test_027r_receipt_rejects_authority_expansion():
    queue = build_user_approved_output_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(approval_item(),),
    )
    receipt = build_user_approved_output_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        approval_id="approval-027r",
        decision="approve",
        queue=queue,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        UserApprovedOutputDecisionReceipt(**{**asdict(receipt), "email_sent": True})
