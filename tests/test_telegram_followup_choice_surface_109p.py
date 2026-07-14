from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

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
from app.async_result_surface import build_async_result_surface
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate, evaluate_cost_preflight
from app.followup_draft_planner import FollowUpDraftPlanRegistry, create_followup_draft_plan
from app.followup_intent_review import FollowUpIntentReviewQueue, create_followup_intent_from_acknowledgement
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord, TelegramAsyncResultDeliveryRegistry, TelegramOwnerBinding, deliver_async_result_surface_to_telegram
from app.telegram_followup_choice_surface import (
    TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE,
    TelegramFollowUpChoiceEnvelope,
    TelegramFollowUpChoiceSurfaceRegistry,
    build_telegram_followup_choice_envelope,
    create_telegram_followup_choice_surface,
    deliver_telegram_followup_choice_surface,
)
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord, TelegramResultAcknowledgementRegistry, TelegramResultCallbackPayload, bind_telegram_result_acknowledgement


REPO_ROOT = Path(__file__).resolve().parents[1]
SURFACE_PATH = REPO_ROOT / "app/telegram_followup_choice_surface.py"
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
        "delegation_id": "delegation-109p",
        "source_stage": "98P",
        "owner_id": "owner-109p",
        "robot_id": "robot-109p",
        "actor_id": "actor-109p",
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
        "required_routine_run_id": "routine-109p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-109p",
        "owner_id": "owner-109p",
        "robot_id": "robot-109p",
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
        budget_policy_id="policy-109p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-109p",
        "owner_id": "owner-109p",
        "robot_id": "robot-109p",
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
    return apply_action_packet_decision(approval_state=submitted, decision=approval_decision(submitted, choice="approve"))


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
        "owner_id": "owner-109p",
        "robot_id": "robot-109p",
        "telegram_chat_id": "telegram-chat-109p",
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
        "action": "request_followup_pending",
    }
    values.update(overrides)
    return TelegramResultCallbackPayload(**values)


def followup_acknowledgement(
    *,
    delivery: TelegramAsyncResultDeliveryRecord | None = None,
    delivery_kwargs: dict[str, object] | None = None,
    **callback_overrides,
) -> TelegramResultAcknowledgementRecord:
    if delivery is None:
        delivery = delivered_record(**(delivery_kwargs or {}))
    return bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, **callback_overrides),
        registry=TelegramResultAcknowledgementRegistry(),
    )


def pending_followup_intent(**kwargs):
    return create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(**kwargs),
        queue=FollowUpIntentReviewQueue(),
    )


def drafted_plan(**kwargs):
    return create_followup_draft_plan(
        followup_intent_record=pending_followup_intent(**kwargs),
        registry=FollowUpDraftPlanRegistry(),
    )


def test_109p_drafted_plan_creates_telegram_choice_surface():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.status == "rendered"
    assert "Tengo estas opciones de seguimiento:" in record.text
    assert record.button_labels == (
        "Resumen mas profundo",
        "Preguntas pendientes",
        "Checklist de revision",
        "Cancelar",
    )


def test_109p_blocked_plan_does_not_create_normal_choice_surface():
    plan = replace(drafted_plan(), status="blocked", rejection_reason="blocked_upstream")

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_non_drafted_plan_status_blocked"


def test_109p_duplicate_plan_is_idempotent():
    registry = TelegramFollowUpChoiceSurfaceRegistry()
    plan = drafted_plan()

    first = create_telegram_followup_choice_surface(draft_plan_record=plan, registry=registry)
    duplicate = create_telegram_followup_choice_surface(draft_plan_record=plan, registry=registry)

    assert first.status == "rendered"
    assert duplicate.status == "duplicate"
    assert len(registry.list_active()) == 1


def test_109p_unknown_plan_blocks_choice_surface_creation():
    record = create_telegram_followup_choice_surface(
        draft_plan_record={"draft_plan_id": "unknown"},
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_followup_draft_plan_record"


def test_109p_missing_owner_blocks_choice_surface_creation():
    source = drafted_plan()
    plan = replace(source, owner_id="", lineage_summary={**source.lineage_summary, "owner_id": ""})

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.rejection_reason == "rejected_missing_owner_id"


def test_109p_missing_robot_blocks_choice_surface_creation():
    source = drafted_plan()
    plan = replace(source, robot_id="", lineage_summary={**source.lineage_summary, "robot_id": ""})

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.rejection_reason == "rejected_missing_robot_id"


def test_109p_missing_chat_blocks_choice_surface_creation():
    source = drafted_plan()
    plan = replace(source, telegram_chat_id="", lineage_summary={**source.lineage_summary, "telegram_chat_id": ""})

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.rejection_reason == "rejected_missing_telegram_chat_id"


def test_109p_missing_intent_ack_delivery_surface_or_inbox_lineage_blocks_choice_surface():
    source = drafted_plan()
    missing_intent = replace(source, followup_intent_id="", lineage_summary={**source.lineage_summary, "followup_intent_id": ""})
    missing_ack = replace(source, acknowledgement_id="", lineage_summary={**source.lineage_summary, "acknowledgement_id": ""})
    missing_delivery = replace(source, delivery_id="", lineage_summary={**source.lineage_summary, "delivery_id": ""})
    missing_surface = replace(source, surface_id="", lineage_summary={**source.lineage_summary, "surface_id": ""})
    missing_inbox = replace(source, inbox_record_id="", lineage_summary={**source.lineage_summary, "inbox_record_id": ""})
    missing_lineage = replace(source, lineage_summary={})

    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_intent,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_followup_intent_id"
    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_ack,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_acknowledgement_id"
    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_delivery,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_delivery_id"
    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_surface,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_surface_id"
    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_inbox,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_inbox_record_id"
    assert create_telegram_followup_choice_surface(
        draft_plan_record=missing_lineage,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    ).rejection_reason == "rejected_missing_lineage_summary"


def test_109p_option_that_creates_authority_blocks_choice_surface():
    source = drafted_plan()
    plan = replace(
        source,
        options=(SimpleNamespace(option_id="bad", label="Bad", option_kind="deeper_summary", local_only=True, creates_authority=True),),
    )

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.rejection_reason == "rejected_authority_creating_followup_option"


def test_109p_option_that_implies_execution_blocks_choice_surface():
    source = drafted_plan()
    plan = replace(
        source,
        options=(SimpleNamespace(option_id="bad", label="Bad", option_kind="deeper_summary", local_only=True, creates_authority=False, implies_execution=True),),
    )

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert record.rejection_reason == "rejected_execution_implying_followup_option"


def test_109p_choice_surface_preserves_100p_101p_102p_103p_104p_105p_106p_107p_108p_lineage():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(delivery_kwargs={"require_approval": True}),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    lineage = record.lineage_summary
    draft_lineage = lineage["upstream_lineage"]
    delivery_lineage = draft_lineage["upstream_lineage"]
    surface_lineage = delivery_lineage["upstream_lineage"]

    assert lineage["choice_surface_stage"] == TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE
    assert lineage["draft_planner_stage"] == "108P"
    assert lineage["followup_stage"] == "107P"
    assert lineage["acknowledgement_stage"] == "106P"
    assert lineage["delivery_stage"] == "105P"
    assert lineage["source_surface_stage"] == "104P"
    assert lineage["inbox_stage"] == "103P"
    assert surface_lineage["cost_preflight_evidence"]["request_id"] == "cost-request-109p"
    assert surface_lineage["approval_evidence"]["action_packet_id"]


def test_109p_visible_choice_text_does_not_dump_raw_private_evidence():
    plan = drafted_plan(
        delivery_kwargs={
            "completion_payload_summary": {
                "summary": "Resumen seguro",
                "request_payload": {"secret": "value"},
                "approval_evidence": {"private": "value"},
            }
        }
    )

    record = create_telegram_followup_choice_surface(
        draft_plan_record=plan,
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert "request_payload" not in record.text
    assert "approval_evidence" not in record.text
    assert "secret" not in record.text


def test_109p_button_labels_are_passive_only():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert all("." not in label for label in record.button_labels)
    assert record.button_labels == tuple(dict.fromkeys(record.button_labels))
    assert "Todavia no ejecute nada" in record.text


def test_109p_buttons_do_not_bind_selected_option():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert "selected" not in record.lineage_summary
    assert record.rejection_reason is None


def test_109p_buttons_do_not_create_async_delegation():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert "delegation" not in record.lineage_summary
    assert record.status == "rendered"


def test_109p_buttons_do_not_create_action_packet_or_approval():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    assert "action_packet" not in record.text.lower()
    assert "approval" not in record.text.lower()


def test_109p_does_not_call_model_or_tool():
    transport = FakeTelegramTransport()
    registry = TelegramFollowUpChoiceSurfaceRegistry()

    create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=registry,
    )

    assert transport.calls == []
    source = SURFACE_PATH.read_text()
    assert "from app.cost_governor import" not in source
    assert "from app.model_router import" not in source


def test_109p_does_not_mutate_memory():
    create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    source = SURFACE_PATH.read_text()
    assert "memory_center" not in source
    assert "write_memory" not in source


def test_109p_no_live_telegram_api_call_is_used():
    create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    source = SURFACE_PATH.read_text()
    assert "requests." not in source
    assert "httpx." not in source
    assert "telegram.Bot" not in source


def test_109p_duplicate_does_not_send_twice_if_delivery_enabled():
    registry = TelegramFollowUpChoiceSurfaceRegistry()
    transport = FakeTelegramTransport()
    plan = drafted_plan()

    first = deliver_telegram_followup_choice_surface(
        draft_plan_record=plan,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )
    second = deliver_telegram_followup_choice_surface(
        draft_plan_record=plan,
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    assert first.status == "delivered"
    assert second.status == "delivered"
    assert len(transport.calls) == 1


def test_109p_owner_scoped_delivery_if_delivery_enabled():
    registry = TelegramFollowUpChoiceSurfaceRegistry()
    transport = FakeTelegramTransport()

    record = deliver_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        owner_binding=owner_binding(),
        transport=transport,
        registry=registry,
    )

    blocked = deliver_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(delivery=delivered_record()),
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
        telegram_chat_id="telegram-chat-third-party",
    )

    assert record.status == "delivered"
    assert transport.calls[0][0] == "telegram-chat-109p"
    assert blocked.status == "blocked"
    assert blocked.rejection_reason == "rejected_third_party_recipient"


def test_109p_envelope_is_telegram_compatible_and_send_disallowed():
    record = create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )

    envelope = build_telegram_followup_choice_envelope(record)

    assert isinstance(envelope, TelegramFollowUpChoiceEnvelope)
    assert envelope.channel == "telegram"
    assert envelope.send_allowed is False


def test_109p_110p_plus_remains_unauthorized():
    roadmap_text = ROADMAP_PATH.read_text()

    assert (
        "109P and later remain unauthorized" in roadmap_text
        or "110P and later remain unauthorized" in roadmap_text
        or "111P and later remain unauthorized" in roadmap_text
    )
    assert "110P+" not in SURFACE_PATH.read_text()
