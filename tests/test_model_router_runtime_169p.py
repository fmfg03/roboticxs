from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.model_router_runtime import (
    MODEL_ROUTER_RUNTIME_STAGE,
    ModelRouterRuntimeDecision,
    render_model_router_decision,
    route_model_for_task,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MODEL_ROUTER_RUNTIME_169P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def route(task_class: str, text: str = "Prepare the next useful output"):
    return route_model_for_task(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id=f"route-{task_class.lower()}",
        task_class=task_class,
        text=text,
    )


@pytest.mark.parametrize(
    ("task_class", "expected_mode"),
    [
        ("SIMPLE_CLASSIFICATION", "economy"),
        ("EXTRACTION", "economy"),
        ("DRAFTING", "balanced"),
        ("DOCUMENT_REVIEW", "balanced"),
        ("SENSITIVE_REVIEW", "premium"),
    ],
)
def test_169p_routes_supported_task_classes_to_expected_modes(task_class: str, expected_mode: str):
    decision = route(task_class)

    assert decision.stage == MODEL_ROUTER_RUNTIME_STAGE
    assert decision.task_class == task_class
    assert decision.mode == expected_mode
    assert decision.provider
    assert decision.model
    assert decision.estimated_input_tokens > 0
    assert decision.estimated_output_tokens > 0
    assert decision.estimated_cost_usd >= 0
    assert decision.local_estimate_only is True
    assert decision.provider_call_made is False
    assert decision.raw_provider_switching_allowed is False
    assert decision.connector_activation_allowed is False
    assert decision.external_write_allowed is False
    assert decision.billing_reconciliation_authorized is False


def test_169p_document_review_uses_long_context_class_without_premium_escalation():
    decision = route("DOCUMENT_REVIEW", "Review this long contract and prepare meeting notes.")

    assert decision.mode == "balanced"
    assert decision.route_task_class == "LONG_CONTEXT"
    assert decision.long_context_required is True
    assert "long-context" in decision.reason


def test_169p_sensitive_review_uses_premium_with_boundary_flag():
    decision = route("SENSITIVE_REVIEW", "Review a sensitive legal or medical decision boundary.")

    assert decision.mode == "premium"
    assert decision.route_task_class == "SENSITIVE_REVIEW"
    assert decision.sensitive_boundary_required is True
    assert "boundary" in decision.reason


def test_169p_rendered_decision_explains_why_and_boundaries():
    rendered = render_model_router_decision(route("DRAFTING", "Draft a short follow-up."))

    assert "Model Router" in rendered
    assert "Stage: 169P" in rendered
    assert "Task class: DRAFTING" in rendered
    assert "Mode: Balanced" in rendered
    assert "Why:" in rendered
    assert "Provider calls: disabled" in rendered
    assert "Raw provider switching: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Billing reconciliation: disabled" in rendered


def test_169p_rejects_unknown_task_class_and_authority_expansion():
    with pytest.raises(ValueError, match="task class must be known"):
        route("UNKNOWN")

    valid = route("EXTRACTION")
    with pytest.raises(ValueError, match="must not expand provider"):
        ModelRouterRuntimeDecision(**{**asdict(valid), "provider_call_made": True})


def test_169p_reference_and_roadmap_close_router_without_provider_calls():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "169P is Model Router Runtime v0 only." in reference
    assert "Economy, Balanced, and Premium" in reference
    assert "does not authorize provider calls" in reference
    assert '"stage_id":"169P","stage_name":"Model Router Runtime v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "207P and later remain unauthorized" in roadmap
