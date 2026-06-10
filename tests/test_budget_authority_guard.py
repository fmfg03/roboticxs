from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

from app.budget_authority import (
    BILLING_TRUTH_DISCLAIMER,
    BudgetAuthorityDecision,
    BudgetAuthorityRequest,
    BudgetAuthorityResult,
    DEFAULT_BUDGET_AUTHORITY_POLICY,
    evaluate_budget_authority,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/BUDGET_AUTHORITY_GUARD_v0_1.md"


def test_budget_authority_decision_taxonomy_is_explicit():
    assert set(get_args(BudgetAuthorityDecision)) == {
        "ALLOW",
        "ALLOW_WITH_CAP",
        "ASK_CONFIRMATION",
        "DOWNGRADE_MODEL",
        "DEFER",
        "BLOCK",
    }


def test_guard_returns_structured_decision_object_with_required_fields():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="SIMPLE_CLASSIFICATION",
            estimated_input_tokens=12,
            estimated_output_tokens=32,
            estimated_cost=0.000001,
            model_tier="economy",
        )
    )

    assert isinstance(result, BudgetAuthorityResult)
    assert {field.name for field in fields(result)} >= {
        "decision",
        "task_class",
        "reason",
        "estimated_input_tokens",
        "estimated_output_tokens",
        "estimated_cost",
        "model_tier",
        "cap_applied",
        "confirmation_required",
        "blocked_reason",
        "downgrade_target",
        "retry_cap",
        "tool_call_cap",
    }
    assert result.decision == "ALLOW"
    assert result.task_class == "SIMPLE_CLASSIFICATION"
    assert result.cost_basis == BILLING_TRUTH_DISCLAIMER
    assert BILLING_TRUTH_DISCLAIMER in result.reason


def test_premium_model_escalation_cannot_silently_allow_without_confirmation():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="GENERAL_TASK",
            estimated_cost=0.03,
            model_tier="premium",
            premium_requested=True,
            confirmation_present=False,
        )
    )

    assert result.decision in {"ASK_CONFIRMATION", "DOWNGRADE_MODEL"}
    assert result.decision != "ALLOW"
    assert result.downgrade_target == "balanced"


def test_confirmed_premium_model_can_continue_under_default_policy():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="GENERAL_TASK",
            estimated_cost=0.03,
            model_tier="premium",
            premium_requested=True,
            confirmation_present=True,
        )
    )

    assert result.decision == "ALLOW_WITH_CAP"
    assert result.confirmation_required is False


def test_byok_premium_escalation_requires_confirmation_when_unconfirmed():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="GENERAL_TASK",
            estimated_cost=0.03,
            model_tier="premium",
            mode="BYOK",
            premium_requested=True,
            confirmation_present=False,
        )
    )

    assert result.decision == "ASK_CONFIRMATION"
    assert result.confirmation_required is True
    assert result.downgrade_target is None


def test_long_context_task_applies_cap_without_silent_unbounded_spend():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="DOCUMENT_REVIEW",
            estimated_input_tokens=24_000,
            estimated_output_tokens=2_000,
            estimated_cost=0.02,
            model_tier="balanced",
        )
    )

    assert result.decision == "ALLOW_WITH_CAP"
    assert result.cap_applied is True
    assert "Long context threshold" in result.reason


def test_retry_cap_defers_repeated_attempts():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="GENERAL_TASK",
            retry_count=DEFAULT_BUDGET_AUTHORITY_POLICY.default_retry_cap,
        )
    )

    assert result.decision in {"DEFER", "BLOCK"}
    assert result.blocked_reason == "RETRY_CAP_REACHED"
    assert result.retry_cap == DEFAULT_BUDGET_AUTHORITY_POLICY.default_retry_cap


def test_tool_call_cap_applies_local_policy_without_authorizing_tools():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="ACTION_APPROVAL_PACKET",
            tool_call_count=DEFAULT_BUDGET_AUTHORITY_POLICY.default_tool_call_cap + 1,
            tool_classes=("LOCAL_METADATA",),
        )
    )

    assert result.decision in {"ALLOW_WITH_CAP", "ASK_CONFIRMATION", "DEFER", "BLOCK"}
    assert result.decision == "ALLOW_WITH_CAP"
    assert result.cap_applied is True
    assert result.tool_call_cap == DEFAULT_BUDGET_AUTHORITY_POLICY.default_tool_call_cap
    assert "connectors" in result.denied_authorizations
    assert "external_writes" in result.denied_authorizations


def test_blocked_tool_classes_always_block_before_other_decisions():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="SIMPLE_CLASSIFICATION",
            tool_classes=("LOCAL_METADATA", "LIVE_RETRIEVAL"),
            retry_count=DEFAULT_BUDGET_AUTHORITY_POLICY.default_retry_cap,
            model_tier="premium",
            premium_requested=True,
        )
    )

    assert result.decision == "BLOCK"
    assert result.blocked_reason == "BLOCKED_TOOL_CLASS:LIVE_RETRIEVAL"
    assert result.confirmation_required is False


def test_future_task_classes_return_defer_or_block():
    expected = {
        "CONVERSATION_CONTINUITY_FUTURE": "DEFER",
        "CAREGIVER_FUTURE": "DEFER",
        "VOICE_FUTURE": "DEFER",
        "RESEARCH_RADAR_FUTURE": "DEFER",
        "EXTERNAL_SKILL_FUTURE": "BLOCK",
    }

    for task_class, decision in expected.items():
        result = evaluate_budget_authority(BudgetAuthorityRequest(task_class=task_class))
        assert result.decision == decision
        assert result.decision in {"DEFER", "BLOCK"}


def test_document_review_expensive_task_requires_confirmation():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="DOCUMENT_REVIEW",
            estimated_input_tokens=1_000,
            estimated_output_tokens=500,
            estimated_cost=DEFAULT_BUDGET_AUTHORITY_POLICY.premium_model_confirmation_threshold,
            model_tier="balanced",
        )
    )

    assert result.decision == "ASK_CONFIRMATION"
    assert result.confirmation_required is True


def test_cost_over_daily_authority_cap_blocks():
    result = evaluate_budget_authority(
        BudgetAuthorityRequest(
            task_class="GENERAL_TASK",
            estimated_cost=DEFAULT_BUDGET_AUTHORITY_POLICY.daily_estimated_cost_cap + 0.01,
            confirmation_present=True,
        )
    )

    assert result.decision == "BLOCK"
    assert result.blocked_reason == "ESTIMATED_COST_CAP_EXCEEDED"


def test_doc_states_estimates_are_not_billing_truth_and_no_external_execution_is_authorized():
    text = DOC_PATH.read_text()

    assert "local estimates only, not billing truth" in text
    for forbidden_surface in [
        "connectors",
        "live retrieval",
        "browser",
        "email",
        "WhatsApp",
        "CRM",
        "lead-gen",
        "handoff",
        "payment",
        "external writes",
    ]:
        assert forbidden_surface in text
    assert "does not authorize" in text
