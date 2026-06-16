from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.cost_governor import (
    COST_GOVERNOR_STAGE,
    BudgetPolicy,
    ModelCatalogEntry,
    TaskCostRequest,
    can_dispatch_async_delegation,
    default_budget_policy,
    default_model_catalog,
    evaluate_cost_preflight,
)
from app.hermes_os_contract import build_hermes_os_runtime_contract
from app.memory_center_projection import MemoryCenterItem, MemoryProjectionRequest, project_memory
from app.models import MemoryItem, Robot, User
from app.routine_execution_engine import RoutineDefinition, execute_routine_locally
from app.telegram_policy_chain import run_telegram_policy_chain


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/cost_governor.py"


def request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "request-100p",
        "owner_id": "owner-1",
        "robot_id": "robot-1",
        "task_class": "drafting",
        "routing_mode": "balanced",
        "sensitivity": "ordinary",
        "requires_tools": False,
        "requires_long_context": False,
        "input_chars_estimate": 800,
        "expected_output_chars": 400,
        "context_item_count": 1,
        "active_skill_id": "basic_assistant",
        "memory_context_used": False,
        "routine_requested": False,
        "async_delegation_requested": False,
        "authority_expansion_requested": False,
    }
    values.update(overrides)
    return TaskCostRequest(**values)


def policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-100p",
        "owner_id": "owner-1",
        "robot_id": "robot-1",
        "routing_mode_allowlist": ("economy", "balanced", "premium", "byok"),
        "default_routing_mode": "balanced",
        "max_estimated_cost_usd": 0.08,
        "confirmation_cost_usd": 0.02,
        "max_input_tokens": 4000,
        "max_output_tokens": 1800,
        "long_context_confirmation_tokens": 2400,
        "byok_allowed": False,
        "async_delegation_allowed": False,
        "premium_allowed_without_confirmation": False,
        "allowed_task_classes": (
            "simple_classification",
            "extraction",
            "drafting",
            "research",
            "reasoning",
            "tool_planning",
            "sensitive_review",
            "long_context",
            "creative",
            "routine",
            "async_delegation",
        ),
        "sensitive_task_min_tier": "advanced",
        "unsafe_model_block": True,
        "untrusted_model_block": True,
        "requires_trace": True,
    }
    values.update(overrides)
    return BudgetPolicy(**values)


def build_update(text: str, user_id: int = 100001) -> dict:
    return {
        "update_id": 100001,
        "message": {
            "message_id": 1000,
            "date": 1710000000,
            "chat": {"id": user_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Cost", "username": "cost"},
            "text": text,
        },
    }


def run_chain(session, text: str, user_id: int = 100001):
    return run_telegram_policy_chain(
        update=build_update(text, user_id=user_id),
        settings=Settings(),
        session=session,
    )


def test_allowed_task_selects_eligible_model():
    result = evaluate_cost_preflight(request=request(), budget_policy=policy(), model_catalog=default_model_catalog())

    assert result.decision == "allow"
    assert result.route_decision is not None
    assert result.route_decision.selected_model_id == "balanced_standard_v1"
    assert result.blocked is False
    assert result.data_only is True


def test_economy_mode_selects_cheapest_adequate_model():
    result = evaluate_cost_preflight(
        request=request(routing_mode="economy", task_class="drafting"),
        budget_policy=policy(),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "allow"
    assert result.route_decision is not None
    assert result.route_decision.selected_model_id == "economy_basic_v1"


def test_balanced_and_premium_modes_respect_capability_requirements():
    balanced = evaluate_cost_preflight(
        request=request(task_class="reasoning", routing_mode="balanced"),
        budget_policy=policy(),
        model_catalog=default_model_catalog(),
    )
    premium = evaluate_cost_preflight(
        request=request(task_class="reasoning", routing_mode="premium"),
        budget_policy=policy(premium_allowed_without_confirmation=True),
        model_catalog=default_model_catalog(),
    )

    assert balanced.route_decision is not None
    assert balanced.route_decision.selected_model_id == "advanced_reasoning_v1"
    assert premium.route_decision is not None
    assert premium.route_decision.selected_model_id == "premium_strong_v1"


def test_over_budget_task_blocks_before_execution():
    result = evaluate_cost_preflight(
        request=request(input_chars_estimate=50000, expected_output_chars=15000),
        budget_policy=policy(max_input_tokens=2000, max_output_tokens=1000),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "block"
    assert result.trace[-1].reason_code in {"blocked_over_budget", "blocked_long_context_limit"}


def test_expensive_task_requires_confirmation():
    result = evaluate_cost_preflight(
        request=request(task_class="research", input_chars_estimate=4000, expected_output_chars=5000),
        budget_policy=policy(confirmation_cost_usd=0.003, max_estimated_cost_usd=0.2),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "require_confirmation"
    assert result.confirmation_required is True
    assert result.trace[-1].reason_code == "confirmation_cost_threshold"


def test_downgrade_selects_cheaper_adequate_model():
    result = evaluate_cost_preflight(
        request=request(task_class="drafting", routing_mode="premium", input_chars_estimate=1500, expected_output_chars=1200),
        budget_policy=policy(confirmation_cost_usd=0.01, premium_allowed_without_confirmation=False),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "downgrade"
    assert result.route_decision is not None
    assert result.route_decision.selected_model_id == "balanced_standard_v1"
    assert result.route_decision.downgrade_from_model_id == "premium_strong_v1"


def test_sensitive_task_cannot_use_unsafe_or_low_trust_model():
    catalog = (
        ModelCatalogEntry(
            provider_id="fixture",
            model_id="unsafe_sensitive_v1",
            display_name="Unsafe Sensitive",
            enabled=True,
            availability="available",
            routing_modes=("balanced",),
            task_classes=("sensitive_review",),
            max_context_tokens=8000,
            capability_tier="advanced",
            trust_level="unsafe",
            safe_for_sensitive=False,
            supports_tools=True,
            supports_long_context=False,
            estimated_input_cost_per_1k_usd=0.002,
            estimated_output_cost_per_1k_usd=0.003,
            selection_priority=1,
        ),
    )
    result = evaluate_cost_preflight(
        request=request(task_class="sensitive_review", sensitivity="medical"),
        budget_policy=policy(),
        model_catalog=catalog,
    )

    assert result.decision == "block"
    assert result.route_decision is not None
    assert result.route_decision.selected_model_id is None
    assert result.trace[-1].reason_code == "blocked_no_eligible_model"


def test_unknown_task_class_blocks():
    result = evaluate_cost_preflight(
        request=request(task_class="unknown_task"),
        budget_policy=policy(),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "block"
    assert result.trace[-1].reason_code == "blocked_unknown_task_class"


def test_unknown_routing_mode_blocks():
    result = evaluate_cost_preflight(
        request=request(routing_mode="turbo"),
        budget_policy=policy(),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "block"
    assert result.trace[-1].reason_code == "blocked_unknown_routing_mode"


def test_missing_or_invalid_budget_policy_blocks():
    missing = evaluate_cost_preflight(
        request=request(),
        budget_policy=None,
        model_catalog=default_model_catalog(),
    )
    invalid = evaluate_cost_preflight(
        request=request(),
        budget_policy=object(),
        model_catalog=default_model_catalog(),
    )

    assert missing.decision == "block"
    assert missing.trace[-1].reason_code == "blocked_invalid_budget_policy"
    assert invalid.decision == "block"
    assert invalid.trace[-1].reason_code == "blocked_invalid_budget_policy"


def test_no_eligible_model_blocks():
    result = evaluate_cost_preflight(
        request=request(task_class="reasoning"),
        budget_policy=policy(),
        model_catalog=(
            ModelCatalogEntry(
                provider_id="fixture",
                model_id="basic_only_v1",
                display_name="Basic Only",
                enabled=True,
                availability="available",
                routing_modes=("balanced",),
                task_classes=("drafting",),
                max_context_tokens=1000,
                capability_tier="basic",
                trust_level="trusted",
                safe_for_sensitive=False,
                supports_tools=False,
                supports_long_context=False,
                estimated_input_cost_per_1k_usd=0.0001,
                estimated_output_cost_per_1k_usd=0.0001,
                selection_priority=1,
            ),
        ),
    )

    assert result.decision == "block"
    assert result.trace[-1].reason_code == "blocked_no_eligible_model"


def test_long_context_task_over_limit_requires_confirmation_or_blocks():
    confirmation = evaluate_cost_preflight(
        request=request(task_class="long_context", requires_long_context=True, input_chars_estimate=7000, expected_output_chars=2000),
        budget_policy=policy(max_input_tokens=5000, max_output_tokens=2000, long_context_confirmation_tokens=2300),
        model_catalog=default_model_catalog(),
    )
    block = evaluate_cost_preflight(
        request=request(task_class="long_context", requires_long_context=True, input_chars_estimate=20000, expected_output_chars=5000),
        budget_policy=policy(max_input_tokens=2000, max_output_tokens=800),
        model_catalog=default_model_catalog(),
    )

    assert confirmation.decision in {"require_confirmation", "block"}
    assert confirmation.trace[-1].reason_code in {"confirmation_long_context_threshold", "blocked_over_budget", "blocked_long_context_limit"}
    assert block.decision == "block"


def test_byok_without_local_allowance_blocks():
    result = evaluate_cost_preflight(
        request=request(routing_mode="byok"),
        budget_policy=policy(byok_allowed=False),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "block"
    assert result.trace[-1].reason_code == "blocked_byok_not_allowed"


def test_cost_result_cannot_expand_tool_action_or_external_authority():
    result = evaluate_cost_preflight(request=request(), budget_policy=policy(), model_catalog=default_model_catalog())

    assert result.tool_action_authorization is False
    assert result.permission_expansion_authorized is False
    assert result.memory_access_authorized is False
    assert result.external_effect_authorized is False
    assert result.model_provider_access_authorized is False
    assert result.execution_authorized is False
    assert all(trace.authority_expanded is False for trace in result.trace)


@pytest.mark.anyio
async def test_95p_consumes_bounded_cost_result_without_bypassing_existing_policies(client):
    response = await client.post("/api/telegram/policy-chain/webhook", json=build_update("Draft a short local summary"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["cost_preflight"]["decision"] == "allow"
    assert body["tool_authority_policy"]["decision"] == "ALLOW"
    assert body["hermes_adapter"]["called"] is True
    assert body["cost_preflight"]["execution_authorized"] is False


@pytest.mark.anyio
async def test_96p_binding_is_non_authority_expanding(client):
    with client.app.state.db.session() as session:
        policy_result = run_chain(session, "Draft a short local summary")
        contract = build_hermes_os_runtime_contract(policy_result=policy_result)

    assert contract.cost_preflight_result is not None
    assert contract.cost_preflight_result.execution_authorized is False
    assert contract.task_run_record.cost_preflight_decision == "allow"
    assert contract.task_run_record.selected_model_id == "balanced_standard_v1"


@pytest.mark.anyio
async def test_98p_routine_cost_block_does_not_call_hermes_adapter(client):
    with client.app.state.db.session() as session:
        run = execute_routine_locally(
            definition=RoutineDefinition(
                routine_id="routine_long_context",
                label="Expensive routine",
                trigger_text="Long context long context long context " * 600,
            ),
            update=build_update("Long context long context long context " * 600),
            settings=Settings(),
            session=session,
        )

    assert run.state in {"blocked", "needs_confirmation"}
    assert run.policy_result.cost_preflight is not None
    assert run.policy_result.hermes_adapter.called is False
    assert run.task_run_record.hermes_adapter_called is False


def test_99p_memory_projection_remains_separate_from_cost_authority():
    memories = (
        MemoryCenterItem(
            item_id="memory-1",
            owner_id="owner-1",
            robot_id="robot-1",
            memory_kind="BOUNDARY_MEMORY",
            status="active",
            scopes=("telegram",),
            sensitivity="ordinary",
            allowed_uses=("telegram_context",),
            skill_ids=(),
            content="Requires approval before external sends.",
            bounded_summary="Requires approval before external sends.",
            source="test",
        ),
    )
    projection = project_memory(
        request=MemoryProjectionRequest(
            request_id="projection-1",
            actor_id="owner-1",
            actor_role="owner_admin",
            owner_id="owner-1",
            robot_id="robot-1",
            target_scope="telegram",
            allowed_use="telegram_context",
        ),
        items=memories,
    )
    result = evaluate_cost_preflight(
        request=request(memory_context_used=True, context_item_count=len(projection.summaries)),
        budget_policy=policy(),
        model_catalog=default_model_catalog(),
    )

    assert projection.tool_action_authorization is False
    assert projection.permission_expansion_authorized is False
    assert result.decision == "allow"
    assert result.execution_authorized is False


def test_async_delegation_task_cannot_dispatch_without_cost_preflight():
    assert can_dispatch_async_delegation(None) is False

    result = evaluate_cost_preflight(
        request=request(task_class="async_delegation", async_delegation_requested=True),
        budget_policy=policy(async_delegation_allowed=True, premium_allowed_without_confirmation=True),
        model_catalog=default_model_catalog(),
    )

    assert result.decision == "require_confirmation"
    assert can_dispatch_async_delegation(result) is False


def test_no_provider_network_billing_or_credential_calls_occur():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "billing",
        "invoice api",
        "credential check",
        "api.openai.com",
        "anthropic",
        "openrouter",
        "stripe",
    ]:
        assert forbidden not in text.lower()


def test_trace_is_deterministic_and_inspectable():
    first = evaluate_cost_preflight(request=request(), budget_policy=policy(), model_catalog=default_model_catalog())
    second = evaluate_cost_preflight(request=request(), budget_policy=policy(), model_catalog=default_model_catalog())

    assert first == second
    assert first.trace
    assert first.trace[-1].request_id == "request-100p"
    assert first.trace[-1].task_class == "drafting"
    assert first.trace[-1].routing_mode == "balanced"


def test_101p_and_later_remain_unauthorized():
    roadmap = (REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md").read_text()

    assert "101P and later remain unauthorized" in roadmap
    assert COST_GOVERNOR_STAGE == "100P"
