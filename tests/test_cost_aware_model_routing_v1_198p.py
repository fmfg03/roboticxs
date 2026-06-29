from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.cost_aware_model_routing_v1 import (
    COST_AWARE_MODEL_ROUTING_STAGE,
    CostAwareRoutingReceipt,
    build_cost_aware_routing_receipt,
    render_cost_aware_routing_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/COST_AWARE_MODEL_ROUTING_198P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def receipt(**overrides) -> CostAwareRoutingReceipt:
    values = {
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "task_id": "draft-198p",
        "task_class": "DRAFTING",
        "text": "Draft a short follow-up from approved context.",
        "command": "/draft",
        "source_trace": ("telegram:owner_request", "memory:approved-summary", "gmail:readonly-thread"),
        "created_at": "2026-06-29T10:00:00+00:00",
    }
    values.update(overrides)
    return build_cost_aware_routing_receipt(**values)


def test_198p_builds_cost_aware_routing_receipt_and_ledger_entry():
    item = receipt()

    assert item.stage == COST_AWARE_MODEL_ROUTING_STAGE
    assert item.task_id == "draft-198p"
    assert item.task_class == "DRAFTING"
    assert item.customer_mode == "Balanced"
    assert item.provider
    assert item.model
    assert item.estimated_input_tokens > 0
    assert item.estimated_output_tokens > 0
    assert item.estimated_cost_usd >= 0
    assert item.source_trace == ("telegram:owner_request", "memory:approved-summary", "gmail:readonly-thread")
    assert item.ledger_entry.task_id == item.task_id
    assert item.ledger_entry.command == "/draft"
    assert item.ledger_entry.model_mode == "balanced"
    assert item.ledger_entry.estimated_cost_usd == item.estimated_cost_usd
    assert item.ledger_entry.source == "198p_cost_aware_router"
    assert item.local_estimate_only is True
    assert item.provider_call_made is False
    assert item.external_write_allowed is False
    assert item.live_billing_checked is False
    assert item.connector_activation_allowed is False
    assert item.approval_gate_preserved is True


def test_198p_uses_customer_modes_and_requires_confirmation_for_premium():
    economy = receipt(task_id="status-198p", task_class="SIMPLE_CLASSIFICATION", text="status")
    premium = receipt(task_id="sensitive-198p", task_class="SENSITIVE_REVIEW", text="Review sensitive boundary.")

    assert economy.customer_mode == "Economy"
    assert economy.confirmation_required is False
    assert economy.confirmation_reason == "within_mode_threshold"
    assert premium.customer_mode == "Premium"
    assert premium.confirmation_required is True
    assert premium.confirmation_reason == "premium_mode_requires_confirmation"


def test_198p_rendered_receipt_is_customer_visible_and_boundary_clear():
    rendered = render_cost_aware_routing_receipt(receipt())

    assert "Cost-Aware Model Routing" in rendered
    assert "Stage: 198P" in rendered
    assert "Mode: Balanced" in rendered
    assert "Estimated cost before run: $" in rendered
    assert "Confirmation:" in rendered
    assert "Ledger source: 198p_cost_aware_router" in rendered
    assert "Source trace:" in rendered
    assert "- telegram:owner_request" in rendered
    assert "Provider calls: disabled" in rendered
    assert "Live billing: disabled" in rendered
    assert "Connector activation: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_198p_rejects_unknown_tasks_authority_expansion_and_missing_trace():
    with pytest.raises(ValueError, match="task class must be known"):
        receipt(task_class="UNKNOWN")
    with pytest.raises(ValueError, match="requires source trace"):
        receipt(source_trace=())

    item = receipt()
    with pytest.raises(ValueError, match="must not expand provider"):
        replace(item, provider_call_made=True)
    with pytest.raises(ValueError, match="preserve approval"):
        replace(item, approval_gate_preserved=False)


def test_198p_redacts_secret_like_source_trace():
    rendered = render_cost_aware_routing_receipt(
        receipt(source_trace=("Authorization Bearer secret-token", "calendar:readonly"))
    )

    assert "[redacted]" in rendered
    assert "secret-token" not in rendered
    assert "Authorization Bearer" not in rendered
    assert "calendar:readonly" in rendered


def test_198p_reference_and_roadmap_close_cost_aware_routing_without_provider_calls():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "198P adds a customer-visible local routing receipt" in reference
    assert "does not authorize provider calls" in reference
    assert "Premium mode requires explicit confirmation" in reference
    assert '"stage_id":"198P","stage_name":"Cost-Aware Model Routing v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "213P and later remain unauthorized" in roadmap
