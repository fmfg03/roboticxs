from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.action_packet_approval import ActionPacketDecision, apply_action_packet_decision, create_action_packet, submit_action_packet_for_approval
from app.async_delegation_authority import (
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    build_async_delegation_action_packet_request,
    build_completion_event,
    create_async_delegation_authority_state,
    register_async_delegation_handle,
)
from app.async_delegation_inbox import AsyncDelegationCompletionInbox, AsyncDelegationInboxRecord, create_async_delegation_registry
from app.async_result_surface import AsyncResultMessageEnvelope, AsyncResultSurface, build_async_result_surface, render_async_result_surface_text
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    CostTraceRecord,
    ModelRouteDecision,
    TaskCostRequest,
    TokenUsageEstimate,
    evaluate_cost_preflight,
)
from app.telegram_async_result_delivery import (
    OWNER_ASYNC_RESULT_NOTIFICATION,
    TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE,
    TelegramAsyncResultDeliveryRegistry,
    TelegramOwnerBinding,
    deliver_async_result_message_envelope_to_telegram,
    deliver_async_result_surface_to_telegram,
    find_telegram_owner_binding,
)
from app.telegram_policy_chain import POLICY_CHAIN_STAGE


REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERY_PATH = REPO_ROOT / "app/telegram_async_result_delivery.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramTransport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, tuple[str, ...]]] = []

    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict:
        self.calls.append((chat_id, text, buttons))
        if self.fail:
            raise RuntimeError("local transport failure")
        return {
            "transport": "fake_telegram_local",
            "chat_id": chat_id,
            "button_count": len(buttons),
            "message_fingerprint": f"{len(text)}:{len(buttons)}",
        }


def delegation_request(**overrides) -> AsyncDelegationRequest:
    values = {
        "delegation_id": "delegation-105p",
        "source_stage": "98P",
        "owner_id": "owner-105p",
        "robot_id": "robot-105p",
        "actor_id": "actor-105p",
        "actor_role": "owner_admin",
        "task_class": "async_delegation",
        "requested_capability": "Preparar resumen del documento NDA",
        "requested_route_mode": "balanced",
        "request_payload": {"summary": "Preparar resumen del documento NDA"},
        "required_policy_trace": (
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        ),
        "required_memory_projection_request_id": None,
        "required_routine_run_id": "routine-105p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-105p",
        "owner_id": "owner-105p",
        "robot_id": "robot-105p",
        "task_class": "async_delegation",
        "routing_mode": "balanced",
        "sensitivity": "ordinary",
        "requires_tools": False,
        "requires_long_context": False,
        "input_chars_estimate": 1200,
        "expected_output_chars": 800,
        "context_item_count": 2,
        "active_skill_id": "basic_assistant",
        "memory_context_used": True,
        "routine_requested": True,
        "async_delegation_requested": True,
        "authority_expansion_requested": False,
    }
    values.update(overrides)
    return TaskCostRequest(**values)


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-105p",
        "owner_id": "owner-105p",
        "robot_id": "robot-105p",
        "routing_mode_allowlist": ("economy", "balanced", "premium", "byok"),
        "default_routing_mode": "balanced",
        "max_estimated_cost_usd": 0.08,
        "confirmation_cost_usd": 0.02,
        "max_input_tokens": 4000,
        "max_output_tokens": 1800,
        "long_context_confirmation_tokens": 2400,
        "byok_allowed": False,
        "async_delegation_allowed": True,
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


def approval_decision(packet_state, *, choice: str, occurred_at: str = "2026-06-17T14:00:00Z") -> ActionPacketDecision:
    return ActionPacketDecision(
        packet_id=packet_state.packet.packet_id,
        packet_version=packet_state.packet.packet_version,
        decision=choice,
        actor_id=packet_state.packet.actor_id,
        actor_role=packet_state.packet.actor_role,
        owner_id=packet_state.packet.owner_id,
        robot_id=packet_state.packet.robot_id,
        reason_code=f"{choice}_async_delegation",
        edit_payload=None,
        resume_token_id=None,
        occurred_at=occurred_at,
    )


def synthetic_allow_preflight(request: TaskCostRequest) -> CostPreflightResult:
    token_estimate = TokenUsageEstimate(
        estimated_input_tokens=300,
        estimated_output_tokens=220,
        estimated_total_tokens=520,
        estimation_basis="test_fixture",
        long_context_applied=False,
    )
    route = ModelRouteDecision(
        selected_provider_id="local_fixture",
        selected_model_id="local-test-model",
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=("local-test-model",),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id="local-test-model",
        candidate_model_ids=("local-test-model",),
        decision="allow",
        reason_code="allow_selected_eligible_route",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.03,
        budget_state="within_budget",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision="allow",
        budget_policy_id="policy-105p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def create_and_approve_async_action_packet(
    *,
    request: AsyncDelegationRequest,
    task_request: TaskCostRequest,
    policy: BudgetPolicy,
    preflight: CostPreflightResult,
):
    packet_request = build_async_delegation_action_packet_request(
        request=request,
        cost_preflight=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )
    approval_state = create_action_packet(request=packet_request, occurred_at="2026-06-17T12:00:00Z")
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=request.owner_id,
        actor_role="owner_admin",
        occurred_at="2026-06-17T12:05:00Z",
    )
    return apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )


def registered_state(*, require_approval: bool = False):
    request = delegation_request()
    task_request = task_cost_request()
    if require_approval:
        policy = budget_policy(async_delegation_allowed=True)
        preflight = evaluate_cost_preflight(request=task_request, budget_policy=policy)
        awaiting = create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=policy,
            cost_preflight=preflight,
            occurred_at="2026-06-17T12:00:00Z",
        )
        approved = create_and_approve_async_action_packet(
            request=request,
            task_request=task_request,
            policy=policy,
            preflight=preflight,
        )
        return register_async_delegation_handle(
            authority_state=bind_async_delegation_approval(
                authority_state=awaiting,
                approval_state=approved,
                occurred_at="2026-06-17T14:00:00Z",
            ),
            occurred_at="2026-06-17T14:05:00Z",
        )
    return register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_request),
            occurred_at="2026-06-17T12:00:00Z",
        ),
        occurred_at="2026-06-17T12:05:00Z",
    )


def accepted_record(
    *,
    completion_status: str = "completed",
    completion_payload_summary: dict[str, object] | None = None,
    require_approval: bool = False,
) -> AsyncDelegationInboxRecord:
    state = registered_state(require_approval=require_approval)
    event = build_completion_event(
        authority_state=state,
        completion_status=completion_status,
        source_stage="simulated_import",
        completion_payload_summary=completion_payload_summary
        or {
            "highlights": [
                "El documento contiene obligaciones de confidencialidad amplias.",
                "La duracion principal parece ser de 3 anos.",
                "No se detecto clausula de exclusividad.",
                "Requiere revision humana antes de firma.",
            ]
        },
        reason_code="completed_local_record" if completion_status == "completed" else "failed_local_record",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def quarantined_record() -> AsyncDelegationInboxRecord:
    state = registered_state()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "Resumen listo"},
            reason_code="completed_local_record",
        ),
        owner_id="other-owner",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-105p",
        "robot_id": "robot-105p",
        "telegram_chat_id": "telegram-chat-105p",
        "channel": "telegram",
        "enabled": True,
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def surface_for_delivery(**kwargs) -> AsyncResultSurface:
    surface = build_async_result_surface(accepted_record(**kwargs))
    assert surface is not None
    return surface


def test_105p_completed_surface_delivers_owner_telegram_result():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()
    registry = TelegramAsyncResultDeliveryRegistry()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    assert record.status == "delivered"
    assert record.delivery_kind == OWNER_ASYNC_RESULT_NOTIFICATION
    assert record.telegram_chat_id == "telegram-chat-105p"
    assert "Resultado listo" in record.text
    assert transport.calls == [("telegram-chat-105p", record.text, record.button_labels)]


def test_105p_failed_surface_delivers_owner_telegram_result():
    surface = surface_for_delivery(
        completion_status="failed",
        completion_payload_summary={"summary": "La tarea no pudo completarse bajo la autoridad registrada."},
    )
    transport = FakeTelegramTransport()
    registry = TelegramAsyncResultDeliveryRegistry()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    assert record.status == "delivered"
    assert "Resultado no disponible" in record.text
    assert "autoridad registrada" in record.text


def test_105p_delivery_uses_104p_rendered_text():
    surface = surface_for_delivery()
    envelope = surface.telegram_envelope
    assert envelope is not None
    transport = FakeTelegramTransport()

    record = deliver_async_result_message_envelope_to_telegram(
        surface=surface,
        envelope=envelope,
        owner_binding=owner_binding(),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.text == render_async_result_surface_text(surface)
    assert record.text == envelope.text


def test_105p_delivery_preserves_100p_101p_102p_103p_104p_lineage():
    surface = surface_for_delivery(require_approval=True)
    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    upstream = record.lineage_summary["upstream_lineage"]
    assert record.lineage_summary["delivery_stage"] == TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE
    assert record.lineage_summary["surface_stage"] == "104P"
    assert record.lineage_summary["telegram_policy_boundary_stage"] == POLICY_CHAIN_STAGE
    assert upstream["inbox_stage"] == "103P"
    assert upstream["request_evidence"] == surface.lineage_summary["request_evidence"]
    assert upstream["cost_preflight_evidence"] == surface.lineage_summary["cost_preflight_evidence"]
    assert upstream["approval_evidence"] == surface.lineage_summary["approval_evidence"]


def test_105p_owner_mismatch_blocks_delivery():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(owner_id="other-owner"),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_owner_mismatch"
    assert transport.calls == []


def test_105p_robot_mismatch_blocks_delivery():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(robot_id="other-robot"),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_robot_mismatch"
    assert transport.calls == []


def test_105p_unknown_telegram_binding_blocks_delivery():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=find_telegram_owner_binding(bindings=(), owner_id=surface.owner_id, robot_id=surface.robot_id),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_telegram_binding"
    assert transport.calls == []


def test_105p_disabled_telegram_binding_blocks_delivery():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(enabled=False),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_disabled_telegram_binding"
    assert transport.calls == []


def test_105p_third_party_recipient_blocks_delivery():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()

    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=TelegramAsyncResultDeliveryRegistry(),
        telegram_chat_id="telegram-chat-third-party",
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_third_party_recipient"
    assert transport.calls == []


def test_105p_quarantined_source_cannot_be_delivered_as_success():
    assert build_async_result_surface(quarantined_record()) is None

    fabricated_surface = surface_for_delivery()
    fabricated_surface = replace(
        fabricated_surface,
        lineage_summary={**fabricated_surface.lineage_summary, "inbox_stage": "quarantined"},
    )

    record = deliver_async_result_surface_to_telegram(
        surface=fabricated_surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_missing_103p_104p_lineage"


def test_105p_raw_async_event_cannot_be_delivered_directly():
    with pytest.raises(TypeError):
        deliver_async_result_surface_to_telegram(
            surface={"event_id": "raw-event"},  # type: ignore[arg-type]
            owner_binding=owner_binding(),
            transport=FakeTelegramTransport(),
            registry=TelegramAsyncResultDeliveryRegistry(),
        )


def test_105p_duplicate_delivery_is_idempotent():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()
    registry = TelegramAsyncResultDeliveryRegistry()

    first = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )
    second = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    assert first.delivery_id == second.delivery_id
    assert first.transport_receipt == second.transport_receipt
    assert len(registry.list_deliveries()) == 1


def test_105p_duplicate_delivery_does_not_call_transport_twice():
    surface = surface_for_delivery()
    transport = FakeTelegramTransport()
    registry = TelegramAsyncResultDeliveryRegistry()

    deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )
    deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    assert len(transport.calls) == 1


def test_105p_buttons_are_passive_labels_only():
    surface = surface_for_delivery()
    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.button_labels == tuple(option.label for option in surface.action_options)
    assert "Pedir seguimiento" in record.button_labels
    assert "callback_data" not in str(record.transport_receipt)


def test_105p_request_followup_button_does_not_create_delegation():
    text = DELIVERY_PATH.read_text()
    surface = surface_for_delivery()
    followup = next(option for option in surface.action_options if option.action_kind == "request_followup")

    assert "register_async_delegation_handle" not in text
    assert "delegate_task" not in text
    assert followup.label == "Pedir seguimiento"
    assert followup.local_only is True
    assert followup.creates_authority is False


def test_105p_acknowledge_button_does_not_mutate_memory():
    text = DELIVERY_PATH.read_text()

    assert "memory_center" not in text
    assert "writeback" not in text
    assert "mutate" not in text


def test_105p_delivery_does_not_create_action_packet_or_approval():
    text = DELIVERY_PATH.read_text()

    for forbidden in [
        "create_action_packet",
        "submit_action_packet_for_approval",
        "apply_action_packet_decision",
        "bind_async_delegation_approval",
    ]:
        assert forbidden not in text


def test_105p_no_live_telegram_api_call_is_used():
    text = DELIVERY_PATH.read_text()

    for forbidden in [
        "send_message",
        "telegram.Bot",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "subprocess",
    ]:
        assert forbidden not in text


def test_105p_delivery_does_not_dump_raw_private_evidence():
    surface = surface_for_delivery(
        completion_payload_summary={
            "original_request_evidence": {"secret": "value"},
            "approval_evidence": {"token": "private"},
        }
    )
    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert "original_request_evidence" not in record.text
    assert "approval_evidence" not in record.text
    assert "cost_preflight_evidence" not in record.text
    assert "packet" not in record.text


def test_105p_telegram_policy_chain_boundaries_remain_intact():
    surface = surface_for_delivery()
    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.lineage_summary["telegram_policy_boundary_stage"] == POLICY_CHAIN_STAGE
    assert record.delivery_kind == OWNER_ASYNC_RESULT_NOTIFICATION


def test_105p_transport_failure_is_recorded_locally():
    surface = surface_for_delivery()
    record = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(fail=True),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )

    assert record.status == "failed"
    assert record.rejection_reason == "transport_delivery_failed"
    assert record.transport_receipt is None


def test_105p_106p_plus_remains_unauthorized():
    roadmap_text = ROADMAP_PATH.read_text()

    assert "108P and later remain unauthorized" in roadmap_text or "108P+ remains unauthorized" in roadmap_text


def test_105p_module_exposes_only_local_delivery_surface():
    text = DELIVERY_PATH.read_text()

    assert TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE == "105P"
    assert "OWNER_ASYNC_RESULT_NOTIFICATION" in text
    assert "OWNER_ASYNC_RESULT_NOTIFICATION" == OWNER_ASYNC_RESULT_NOTIFICATION
