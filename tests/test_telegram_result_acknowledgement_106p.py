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
from app.async_result_surface import AsyncResultSurface, build_async_result_surface
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
    TelegramAsyncResultDeliveryRecord,
    TelegramAsyncResultDeliveryRegistry,
    TelegramOwnerBinding,
    deliver_async_result_surface_to_telegram,
)
from app.telegram_policy_chain import POLICY_CHAIN_STAGE
from app.telegram_result_acknowledgement import (
    OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT,
    TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE,
    TelegramAcknowledgementResponseEnvelope,
    TelegramResultAcknowledgementRegistry,
    TelegramResultCallbackPayload,
    bind_telegram_result_acknowledgement,
    build_acknowledgement_response_envelope,
    build_safe_lineage_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ACK_PATH = REPO_ROOT / "app/telegram_result_acknowledgement.py"
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
        "delegation_id": "delegation-106p",
        "source_stage": "98P",
        "owner_id": "owner-106p",
        "robot_id": "robot-106p",
        "actor_id": "actor-106p",
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
        "required_routine_run_id": "routine-106p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-106p",
        "owner_id": "owner-106p",
        "robot_id": "robot-106p",
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
        "policy_id": "policy-106p",
        "owner_id": "owner-106p",
        "robot_id": "robot-106p",
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
        budget_policy_id="policy-106p",
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


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-106p",
        "robot_id": "robot-106p",
        "telegram_chat_id": "telegram-chat-106p",
        "channel": "telegram",
        "enabled": True,
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def delivered_record(**kwargs) -> TelegramAsyncResultDeliveryRecord:
    surface = build_async_result_surface(accepted_record(**kwargs))
    assert surface is not None
    return deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )


def delivery_registry_with(record: TelegramAsyncResultDeliveryRecord) -> TelegramAsyncResultDeliveryRegistry:
    registry = TelegramAsyncResultDeliveryRegistry()
    registry.store(record)
    return registry


def callback_payload(record: TelegramAsyncResultDeliveryRecord, **overrides) -> TelegramResultCallbackPayload:
    values = {
        "delivery_id": record.delivery_id,
        "surface_id": record.surface_id,
        "owner_id": record.owner_id,
        "robot_id": record.robot_id,
        "telegram_chat_id": record.telegram_chat_id,
        "action": "acknowledge",
    }
    values.update(overrides)
    return TelegramResultCallbackPayload(**values)


def test_106p_acknowledge_callback_records_local_acknowledgement():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="acknowledge"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "recorded"
    assert record.callback_action == "acknowledge"
    assert record.response_text == "Listo. Marque este resultado como revisado."


def test_106p_dismiss_callback_records_local_acknowledgement():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="dismiss"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "recorded"
    assert record.callback_action == "dismiss"
    assert record.response_text == "Listo. Descarte este resultado de tu vista."


def test_106p_view_lineage_summary_callback_records_safe_summary():
    delivery = delivered_record(require_approval=True)

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="view_lineage_summary"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "recorded"
    assert record.callback_action == "view_lineage_summary"
    assert "Resumen de trazabilidad:" in record.response_text
    assert "No se ejecuto ninguna accion externa." in record.response_text


def test_106p_request_followup_records_pending_intent_only():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="request_followup_pending"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "recorded"
    assert record.callback_action == "request_followup_pending"
    assert "seguimiento como pendiente" in record.response_text


def test_106p_request_followup_does_not_create_delegation():
    text = ACK_PATH.read_text()

    assert "register_async_delegation_handle" not in text
    assert "delegate_task" not in text


def test_106p_request_followup_does_not_call_model_or_tool():
    text = ACK_PATH.read_text()

    for forbidden in ["openai", "anthropic", "tool_call", "run_tool", "httpx", "requests"]:
        assert forbidden not in text


def test_106p_acknowledge_does_not_mutate_memory():
    text = ACK_PATH.read_text()

    assert "memory_center" not in text
    assert "writeback" not in text
    assert "mutate" not in text


def test_106p_dismiss_does_not_delete_source_data():
    text = ACK_PATH.read_text()

    assert "delete" not in text
    assert "drop" not in text


def test_106p_owner_mismatch_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, owner_id="other-owner"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_owner_mismatch"


def test_106p_robot_mismatch_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, robot_id="other-robot"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_robot_mismatch"


def test_106p_chat_mismatch_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, telegram_chat_id="other-chat"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_chat_mismatch"


def test_106p_unknown_delivery_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=TelegramAsyncResultDeliveryRegistry(),
        callback_payload=callback_payload(delivery),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_delivery_id"


def test_106p_unknown_action_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="execute_followup_now"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_callback_action"


def test_106p_blocked_delivery_cannot_be_acknowledged_as_normal():
    delivery = replace(delivered_record(), status="blocked", rejection_reason="rejected_owner_mismatch")

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_blocked_delivery_record"


def test_106p_failed_delivery_cannot_create_normal_acknowledgement():
    delivery = replace(delivered_record(), status="failed", rejection_reason="transport_delivery_failed")

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_failed_delivery_record"


def test_106p_surface_mismatch_blocks_callback():
    delivery = delivered_record()

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, surface_id="other-surface"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_surface_mismatch"


def test_106p_duplicate_callback_is_idempotent():
    delivery = delivered_record()
    callback = callback_payload(delivery, action="dismiss")
    registry = TelegramResultAcknowledgementRegistry()
    deliveries = delivery_registry_with(delivery)

    first = bind_telegram_result_acknowledgement(
        delivery_registry=deliveries,
        callback_payload=callback,
        registry=registry,
    )
    second = bind_telegram_result_acknowledgement(
        delivery_registry=deliveries,
        callback_payload=callback,
        registry=registry,
    )

    assert first.acknowledgement_id == second.acknowledgement_id
    assert len(registry.list_acknowledgements()) == 1


def test_106p_acknowledgement_preserves_100p_101p_102p_103p_104p_105p_lineage():
    delivery = delivered_record(require_approval=True)

    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="acknowledge"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    assert record.lineage_summary["acknowledgement_stage"] == TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE
    assert record.lineage_summary["callback_category"] == OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT
    assert record.lineage_summary["delivery_stage"] == "105P"
    assert record.lineage_summary["delivery_id"] == delivery.delivery_id
    upstream = record.lineage_summary["upstream_lineage"]
    assert upstream["surface_stage"] == "104P"
    assert upstream["upstream_lineage"]["inbox_stage"] == "103P"
    assert upstream["upstream_lineage"]["cost_preflight_evidence"] is not None
    assert upstream["upstream_lineage"]["approval_evidence"] is not None


def test_106p_visible_lineage_summary_does_not_dump_raw_private_evidence():
    delivery = delivered_record(require_approval=True)
    summary = build_safe_lineage_summary(delivery)

    assert "request_evidence" not in summary
    assert "approval_evidence" not in summary
    assert "cost_preflight_evidence" not in summary
    assert "packet" not in summary


def test_106p_response_envelope_is_local_and_send_disallowed():
    delivery = delivered_record()
    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="acknowledge"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    envelope = build_acknowledgement_response_envelope(record)

    assert isinstance(envelope, TelegramAcknowledgementResponseEnvelope)
    assert envelope.channel == "telegram"
    assert envelope.telegram_chat_id == delivery.telegram_chat_id
    assert envelope.send_allowed is False


def test_106p_does_not_create_action_packet_or_approval():
    text = ACK_PATH.read_text()

    for forbidden in [
        "create_action_packet",
        "submit_action_packet_for_approval",
        "apply_action_packet_decision",
        "bind_async_delegation_approval",
    ]:
        assert forbidden not in text


def test_106p_no_live_telegram_api_call_is_used():
    text = ACK_PATH.read_text()

    for forbidden in [
        "send_message",
        "telegram.Bot",
        "requests",
        "httpx",
        "subprocess",
    ]:
        assert forbidden not in text


def test_106p_telegram_policy_boundaries_remain_intact():
    delivery = delivered_record()
    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, action="view_lineage_summary"),
        registry=TelegramResultAcknowledgementRegistry(),
    )

    upstream = record.lineage_summary["upstream_lineage"]
    assert upstream["telegram_policy_boundary_stage"] == POLICY_CHAIN_STAGE
    assert upstream["delivery_stage"] == "105P"


def test_106p_107p_plus_remains_unauthorized():
    roadmap_text = ROADMAP_PATH.read_text()

    assert (
        "108P and later remain unauthorized" in roadmap_text
        or "108P+ remains unauthorized" in roadmap_text
        or "109P and later remain unauthorized" in roadmap_text
        or "110P and later remain unauthorized" in roadmap_text
        or "109P+ remains unauthorized" in roadmap_text
        or "110P+ remains unauthorized" in roadmap_text
    )
