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
from app.async_result_surface import build_async_result_surface
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate, evaluate_cost_preflight
from app.followup_intent_review import (
    FOLLOWUP_INTENT_REVIEW_STAGE,
    FollowUpIntentReviewQueue,
    build_followup_intent_response_envelope,
    create_followup_intent_from_acknowledgement,
)
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord, TelegramAsyncResultDeliveryRegistry, TelegramOwnerBinding, deliver_async_result_surface_to_telegram
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord, TelegramResultAcknowledgementRegistry, TelegramResultCallbackPayload, bind_telegram_result_acknowledgement


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLLOWUP_PATH = REPO_ROOT / "app/followup_intent_review.py"
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
        "delegation_id": "delegation-107p",
        "source_stage": "98P",
        "owner_id": "owner-107p",
        "robot_id": "robot-107p",
        "actor_id": "actor-107p",
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
        "required_routine_run_id": "routine-107p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-107p",
        "owner_id": "owner-107p",
        "robot_id": "robot-107p",
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
        budget_policy_id="policy-107p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-107p",
        "owner_id": "owner-107p",
        "robot_id": "robot-107p",
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
        "owner_id": "owner-107p",
        "robot_id": "robot-107p",
        "telegram_chat_id": "telegram-chat-107p",
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
    record = bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=callback_payload(delivery, **callback_overrides),
        registry=TelegramResultAcknowledgementRegistry(),
    )
    return record


def test_107p_request_followup_ack_creates_pending_review_intent():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "pending_review"
    assert record.source_action == "request_followup_pending"


def test_107p_acknowledge_ack_does_not_create_followup_intent():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(action="acknowledge"),
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_non_followup_acknowledgement_action"


def test_107p_dismiss_ack_does_not_create_followup_intent():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(action="dismiss"),
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"


def test_107p_lineage_summary_ack_does_not_create_followup_intent():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(action="view_lineage_summary"),
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"


def test_107p_unknown_acknowledgement_blocks_intent_creation():
    blocked_ack = TelegramResultAcknowledgementRecord(
        acknowledgement_id="ack-unknown-107p",
        delivery_id="delivery-missing",
        surface_id="surface-missing",
        inbox_record_id="",
        owner_id="owner-107p",
        robot_id="robot-107p",
        telegram_chat_id="telegram-chat-107p",
        callback_action="request_followup_pending",
        status="blocked",
        response_text="No pude registrar esa interaccion en esta version.",
        lineage_summary={"acknowledgement_stage": "106P", "callback_action": "request_followup_pending", "upstream_lineage": None},
        rejection_reason="rejected_unknown_delivery_id",
    )

    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=blocked_ack,
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_delivery_id"


def test_107p_blocked_acknowledgement_blocks_intent_creation():
    acknowledgement = followup_acknowledgement()
    blocked_ack = replace(acknowledgement, status="blocked", rejection_reason="rejected_owner_mismatch")

    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=blocked_ack,
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_owner_mismatch"


def test_107p_duplicate_followup_intent_is_idempotent():
    queue = FollowUpIntentReviewQueue()
    acknowledgement = followup_acknowledgement()

    first = create_followup_intent_from_acknowledgement(acknowledgement_record=acknowledgement, queue=queue)
    duplicate = create_followup_intent_from_acknowledgement(acknowledgement_record=acknowledgement, queue=queue)

    assert first.status == "pending_review"
    assert duplicate.status == "duplicate"
    assert duplicate.followup_intent_id == first.followup_intent_id


def test_107p_duplicate_does_not_create_multiple_active_intents():
    queue = FollowUpIntentReviewQueue()
    acknowledgement = followup_acknowledgement()

    create_followup_intent_from_acknowledgement(acknowledgement_record=acknowledgement, queue=queue)
    create_followup_intent_from_acknowledgement(acknowledgement_record=acknowledgement, queue=queue)

    assert len(queue.list_pending()) == 1
    assert len(queue.records_by_id) == 1


def test_107p_missing_owner_blocks_intent_creation():
    source = followup_acknowledgement()
    acknowledgement = replace(source, owner_id="", lineage_summary={**source.lineage_summary, "owner_id": ""})

    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=acknowledgement,
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_missing_owner_id"


def test_107p_missing_robot_blocks_intent_creation():
    source = followup_acknowledgement()
    acknowledgement = replace(source, robot_id="", lineage_summary={**source.lineage_summary, "robot_id": ""})

    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=acknowledgement,
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.rejection_reason == "rejected_missing_robot_id"


def test_107p_missing_chat_blocks_intent_creation():
    source = followup_acknowledgement()
    acknowledgement = replace(source, telegram_chat_id="", lineage_summary={**source.lineage_summary, "telegram_chat_id": ""})

    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=acknowledgement,
        queue=FollowUpIntentReviewQueue(),
    )

    assert record.rejection_reason == "rejected_missing_telegram_chat_id"


def test_107p_missing_delivery_surface_or_inbox_lineage_blocks_intent_creation():
    source = followup_acknowledgement()
    missing_delivery = replace(source, delivery_id="", lineage_summary={**source.lineage_summary, "delivery_id": ""})
    missing_surface = replace(source, surface_id="", lineage_summary={**source.lineage_summary, "surface_id": ""})
    missing_inbox = replace(source, inbox_record_id="", lineage_summary={**source.lineage_summary, "inbox_record_id": ""})
    missing_lineage = replace(source, lineage_summary={})

    assert create_followup_intent_from_acknowledgement(
        acknowledgement_record=missing_delivery,
        queue=FollowUpIntentReviewQueue(),
    ).rejection_reason == "rejected_missing_delivery_id"
    assert create_followup_intent_from_acknowledgement(
        acknowledgement_record=missing_surface,
        queue=FollowUpIntentReviewQueue(),
    ).rejection_reason == "rejected_missing_surface_id"
    assert create_followup_intent_from_acknowledgement(
        acknowledgement_record=missing_inbox,
        queue=FollowUpIntentReviewQueue(),
    ).rejection_reason == "rejected_missing_inbox_record_id"
    assert create_followup_intent_from_acknowledgement(
        acknowledgement_record=missing_lineage,
        queue=FollowUpIntentReviewQueue(),
    ).rejection_reason == "rejected_missing_lineage_summary"


def test_107p_followup_intent_preserves_100p_101p_102p_103p_104p_105p_106p_lineage():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(delivery_kwargs={"require_approval": True}),
        queue=FollowUpIntentReviewQueue(),
    )

    lineage = record.lineage_summary
    upstream = lineage["upstream_lineage"]

    assert lineage["followup_stage"] == FOLLOWUP_INTENT_REVIEW_STAGE
    assert lineage["acknowledgement_stage"] == "106P"
    assert lineage["delivery_stage"] == "105P"
    assert upstream["surface_stage"] == "104P"
    assert upstream["upstream_lineage"]["inbox_stage"] == "103P"
    assert upstream["upstream_lineage"]["cost_preflight_evidence"]["request_id"] == "cost-request-107p"
    assert upstream["upstream_lineage"]["approval_evidence"]["action_packet_id"]


def test_107p_review_summary_does_not_dump_raw_private_evidence():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(
            delivery_kwargs={
                "completion_payload_summary": {
                    "summary": "Resumen seguro",
                    "original_request_evidence": {"secret": "value"},
                }
            }
        ),
        queue=FollowUpIntentReviewQueue(),
    )

    assert "original_request_evidence" not in record.review_summary
    assert "request_payload" not in record.review_summary
    assert "approval_evidence" not in record.review_summary


def test_107p_list_pending_is_deterministic():
    queue = FollowUpIntentReviewQueue()
    a = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=queue,
    )
    b = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(delivery=delivered_record(completion_payload_summary={"summary": "Otro resultado"})),
        queue=queue,
    )

    pending = queue.list_pending()

    assert tuple(record.followup_intent_id for record in pending) == tuple(sorted([a.followup_intent_id, b.followup_intent_id]))


def test_107p_allowed_status_transition_to_dismissed():
    queue = FollowUpIntentReviewQueue()
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=queue,
    )

    updated = queue.update_status(followup_intent_id=record.followup_intent_id, status="dismissed")

    assert updated.status == "dismissed"


def test_107p_allowed_status_transition_to_resolved_no_action():
    queue = FollowUpIntentReviewQueue()
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=queue,
    )

    updated = queue.update_status(followup_intent_id=record.followup_intent_id, status="resolved_no_action")

    assert updated.status == "resolved_no_action"


def test_107p_blocks_execution_expanding_status_transition():
    queue = FollowUpIntentReviewQueue()
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=queue,
    )

    with pytest.raises(ValueError):
        queue.update_status(followup_intent_id=record.followup_intent_id, status="delegated")


def test_107p_response_envelope_is_local_and_send_disallowed():
    record = create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=FollowUpIntentReviewQueue(),
    )

    envelope = build_followup_intent_response_envelope(record)

    assert envelope.channel == "telegram"
    assert envelope.send_allowed is False
    assert "Todavía no ejecuté nada" in envelope.text


def test_107p_does_not_create_async_delegation():
    text = FOLLOWUP_PATH.read_text()

    assert "register_async_delegation_handle" not in text
    assert "delegate_task" not in text


def test_107p_does_not_create_action_packet_or_approval():
    text = FOLLOWUP_PATH.read_text()

    assert "create_action_packet" not in text
    assert "submit_action_packet_for_approval" not in text
    assert "approval" not in text


def test_107p_does_not_call_model_or_tool():
    text = FOLLOWUP_PATH.read_text()

    for forbidden in ["openai", "anthropic", "tool_call", "run_tool", "httpx", "requests"]:
        assert forbidden not in text


def test_107p_does_not_mutate_memory():
    text = FOLLOWUP_PATH.read_text()

    assert "memory_center" not in text
    assert "writeback" not in text
    assert "memory_write" not in text


def test_107p_no_live_telegram_api_call_is_used():
    text = FOLLOWUP_PATH.read_text()

    assert "telegram.Bot" not in text
    assert ".send_message" not in text
    assert "send_allowed=True" not in text


def test_107p_108p_plus_remains_unauthorized():
    text = ROADMAP_PATH.read_text()

    assert (
        "108P and later remain unauthorized" in text
        or "108P+ remains unauthorized" in text
        or "109P and later remain unauthorized" in text
        or "110P and later remain unauthorized" in text
        or "111P and later remain unauthorized" in text
        or "109P+ remains unauthorized" in text
        or "110P+ remains unauthorized" in text
        or "111P+ remains unauthorized" in text
    )
    assert "108P+" not in FOLLOWUP_PATH.read_text()
