from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_boundary_confirmation_gate import (
    ACTION_BOUNDARY_CONFIRMATION_GATE_STAGE,
    ACTION_BOUNDARY_DECISIONS,
    ActionBoundaryDecisionRecord,
    classify_action_boundary,
    render_action_boundary_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/ACTION_BOUNDARY_CONFIRMATION_GATE_167P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def decision(action_type: str, label: str = "Prepare today's brief"):
    return classify_action_boundary(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        action_id=f"action-{action_type}",
        action_type=action_type,
        action_label=label,
    )


def test_167p_allows_local_preparation_without_external_authority():
    record = decision("prepare", "Prepare a meeting pack")

    assert record.stage == ACTION_BOUNDARY_CONFIRMATION_GATE_STAGE
    assert record.decision == "ALLOW"
    assert record.reason_code == "local_preparation_only"
    assert record.local_preparation_allowed is True
    assert record.requires_confirmation is False
    assert record.action_packet_required is False
    assert record.execution_authorized is False
    assert record.external_write_allowed is False
    assert record.connector_activation_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False


def test_167p_keeps_customer_outputs_draft_only():
    record = decision("draft_message", "Draft a follow-up to Victor")

    assert record.decision == "DRAFT_ONLY"
    assert record.draft_only is True
    assert record.local_preparation_allowed is True
    assert "will not send" in record.safe_user_message
    assert record.execution_authorized is False
    assert record.external_write_allowed is False


@pytest.mark.parametrize(
    "action_type",
    ["send_message", "schedule_event", "update_record", "publish_content", "calendar_update"],
)
def test_167p_requires_confirmation_and_action_packet_for_external_changes(action_type: str):
    record = decision(action_type, "Send or change something outside the local draft")

    assert record.decision == "ASK_CONFIRMATION"
    assert record.requires_confirmation is True
    assert record.action_packet_required is True
    assert "cannot send it or change anything without your confirmation" in record.safe_user_message
    assert record.execution_authorized is False
    assert record.external_write_allowed is False


@pytest.mark.parametrize(
    "action_type",
    ["legal_review_request", "medical_review_request", "tax_review_request", "financial_review_request"],
)
def test_167p_escalates_professional_review_requests(action_type: str):
    record = decision(action_type, "Review this with professional context")

    assert record.decision == "ESCALATE"
    assert record.escalation_required is True
    assert record.professional_decision_allowed is False
    assert "qualified human review" in record.safe_user_message


@pytest.mark.parametrize(
    "action_type",
    [
        "payment",
        "sign_document",
        "legal_decision",
        "medical_decision",
        "tax_decision",
        "financial_decision",
        "delete_data",
        "deploy_production",
        "credential_change",
    ],
)
def test_167p_blocks_sensitive_destructive_and_payment_actions(action_type: str):
    record = decision(action_type, "Take a protected action")

    assert record.decision == "BLOCK"
    assert record.blocked is True
    assert record.local_preparation_allowed is False
    assert record.payment_allowed is False
    assert record.destructive_action_allowed is False
    assert record.professional_decision_allowed is False
    assert "protected boundary" in record.safe_user_message


def test_167p_text_context_blocks_sensitive_decision_language():
    record = classify_action_boundary(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        action_id="action-sensitive-text",
        action_type="draft",
        action_label="Tell me whether I should sign this contract",
        risk_context="legal decision requested",
    )

    assert record.decision == "BLOCK"
    assert record.blocked is True
    assert record.draft_only is False


def test_167p_unknown_actions_require_confirmation_not_execution():
    record = decision("custom_external_action", "Do something not classified yet")

    assert record.decision == "ASK_CONFIRMATION"
    assert record.action_packet_required is True
    assert record.execution_authorized is False
    assert record.external_write_allowed is False


def test_167p_record_rejects_authority_expansion():
    valid = decision("prepare")

    with pytest.raises(ValueError, match="must not authorize execution or external authority"):
        ActionBoundaryDecisionRecord(**{**asdict(valid), "external_write_allowed": True})

    with pytest.raises(ValueError, match="must require an action packet"):
        ActionBoundaryDecisionRecord(**{**asdict(valid), "decision": "ASK_CONFIRMATION", "action_packet_required": False})


def test_167p_rendered_decision_names_all_labels_and_boundaries():
    rendered = render_action_boundary_decision(decision("send_message", "Send the follow-up"))

    assert "Action Boundary" in rendered
    assert "Stage: 167P" in rendered
    assert "Decision: ASK_CONFIRMATION" in rendered
    assert "Decision labels: ALLOW, DRAFT_ONLY, ASK_CONFIRMATION, ESCALATE, BLOCK" in rendered
    assert "Action packet required: true" in rendered
    assert "Execution authorized: false" in rendered
    assert "External writes: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Gmail writes: disabled" in rendered
    assert "Payments/destructive/professional decisions: disabled" in rendered


def test_167p_reference_and_roadmap_close_gate_without_execution_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "167P is Action Boundary Confirmation Gate v0 only." in reference
    assert "ALLOW, DRAFT_ONLY, ASK_CONFIRMATION, ESCALATE, BLOCK" in reference
    assert "does not authorize execution" in reference
    assert '"stage_id":"167P","stage_name":"Action Boundary Confirmation Gate v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "186P and later remain unauthorized" in roadmap


def test_167p_exports_exact_decision_set():
    assert ACTION_BOUNDARY_DECISIONS == ("ALLOW", "DRAFT_ONLY", "ASK_CONFIRMATION", "ESCALATE", "BLOCK")
