from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.followup_draft_planner import FollowUpDraftPlanRegistry, create_followup_draft_plan
from app.followup_intent_review import FollowUpIntentReviewQueue, create_followup_intent_from_acknowledgement
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord, TelegramAsyncResultDeliveryRegistry, TelegramOwnerBinding, deliver_async_result_surface_to_telegram
from app.telegram_followup_choice_selection import (
    TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE,
    TelegramFollowUpChoiceSelectionPayload,
    TelegramFollowUpChoiceSelectionRegistry,
    TelegramFollowUpChoiceSelectionResponseEnvelope,
    bind_telegram_followup_choice_selection,
    build_followup_choice_selection_response_envelope,
)
from app.telegram_followup_choice_surface import TelegramFollowUpChoiceSurfaceRegistry, create_telegram_followup_choice_surface
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord, TelegramResultAcknowledgementRegistry, TelegramResultCallbackPayload, bind_telegram_result_acknowledgement
from app.async_result_surface import build_async_result_surface
from app.async_delegation_authority import (
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    build_async_delegation_action_packet_request,
    build_completion_event,
    create_async_delegation_authority_state,
    register_async_delegation_handle,
)
from app.action_packet_approval import ActionPacketDecision, apply_action_packet_decision, create_action_packet, submit_action_packet_for_approval
from app.async_delegation_inbox import AsyncDelegationCompletionInbox, AsyncDelegationInboxRecord, create_async_delegation_registry
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate, evaluate_cost_preflight


REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTION_PATH = REPO_ROOT / "app/telegram_followup_choice_selection.py"


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
        "delegation_id": "delegation-110p",
        "source_stage": "98P",
        "owner_id": "owner-110p",
        "robot_id": "robot-110p",
        "actor_id": "actor-110p",
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
        "required_routine_run_id": "routine-110p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-110p",
        "owner_id": "owner-110p",
        "robot_id": "robot-110p",
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
        budget_policy_id="policy-110p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-110p",
        "owner_id": "owner-110p",
        "robot_id": "robot-110p",
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
        "owner_id": "owner-110p",
        "robot_id": "robot-110p",
        "telegram_chat_id": "telegram-chat-110p",
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


def choice_surface(**kwargs):
    return create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(**kwargs),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )


def selection_payload(record, **overrides) -> TelegramFollowUpChoiceSelectionPayload:
    values = {
        "choice_surface_id": record.choice_surface_id,
        "draft_plan_id": record.draft_plan_id,
        "selected_option_id": record.option_refs[0],
        "owner_id": record.owner_id,
        "robot_id": record.robot_id,
        "telegram_chat_id": record.telegram_chat_id,
    }
    values.update(overrides)
    return TelegramFollowUpChoiceSelectionPayload(**values)


def test_110p_valid_followup_option_selection_records_pending_authorization():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.status == "selected_pending_authorization"
    assert record.selected_option_kind == "deeper_summary"
    assert "Todavia no ejecute nada." in record.response_text


def test_110p_cancel_option_records_cancelled_no_action():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, selected_option_id=surface.option_refs[-1]),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.status == "cancelled_no_action"
    assert record.selected_option_kind == "cancel_followup"
    assert "No ejecute ninguna accion." in record.response_text


def test_110p_selection_requires_known_choice_surface():
    payload = TelegramFollowUpChoiceSelectionPayload(
        choice_surface_id="missing-surface",
        draft_plan_id="draft-plan",
        selected_option_id="missing-option",
        owner_id="owner-110p",
        robot_id="robot-110p",
        telegram_chat_id="telegram-chat-110p",
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record={"choice_surface_id": "missing-surface"},
        payload=payload,
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_choice_surface_record"


def test_110p_selection_requires_option_present_on_choice_surface():
    source = choice_surface()
    surface = replace(
        source,
        option_refs=tuple(ref for ref in source.option_refs if ref != source.option_refs[0]),
        lineage_summary={
            **source.lineage_summary,
            "option_refs": tuple(ref for ref in source.option_refs if ref != source.option_refs[0]),
            "option_metadata_by_ref": {
                key: value
                for key, value in source.lineage_summary["option_metadata_by_ref"].items()
                if key != source.option_refs[0]
            },
        },
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(source),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_option_surface_mismatch"


def test_110p_selection_requires_option_from_source_draft_plan():
    source = choice_surface()
    surface = replace(source, lineage_summary={**source.lineage_summary, "option_metadata_by_ref": {}})

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.status == "selected_pending_authorization"


def test_110p_owner_mismatch_blocks_selection():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, owner_id="other-owner"),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_owner_mismatch"


def test_110p_robot_mismatch_blocks_selection():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, robot_id="other-robot"),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_robot_mismatch"


def test_110p_chat_mismatch_blocks_selection():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, telegram_chat_id="other-chat"),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_chat_mismatch"


def test_110p_draft_plan_mismatch_blocks_selection():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, draft_plan_id="other-draft"),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_draft_plan_mismatch"


def test_110p_unknown_option_blocks_selection():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, selected_option_id="unknown-option-id"),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_unknown_selected_option_id"


def test_110p_blocked_choice_surface_blocks_selection():
    surface = replace(choice_surface(), status="blocked", rejection_reason="blocked_upstream")

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_blocked_choice_surface_record"


def test_110p_failed_choice_surface_blocks_selection():
    surface = replace(choice_surface(), status="failed", rejection_reason="transport_delivery_failed")

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_failed_choice_surface_record"


def test_110p_duplicate_selection_is_idempotent():
    surface = choice_surface()
    registry = TelegramFollowUpChoiceSelectionRegistry()

    first = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=registry,
    )
    second = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=registry,
    )

    assert first.selection_id == second.selection_id
    assert first.status == second.status == "selected_pending_authorization"
    assert len(registry.list_selections()) == 1


def test_110p_different_later_selection_is_blocked_without_replacement_authority():
    surface = choice_surface()
    registry = TelegramFollowUpChoiceSelectionRegistry()

    first = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=registry,
    )
    second = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, selected_option_id=surface.option_refs[1]),
        registry=registry,
    )

    assert first.status == "selected_pending_authorization"
    assert second.status == "blocked"
    assert second.rejection_reason == "rejected_selection_replacement_not_authorized"


def test_110p_option_that_creates_authority_blocks_selection():
    source = choice_surface()
    unsafe_metadata = {
        **source.lineage_summary["option_metadata_by_ref"][source.option_refs[0]],
        "creates_authority": True,
    }
    surface = replace(
        source,
        lineage_summary={
            **source.lineage_summary,
            "option_metadata_by_ref": {
                **source.lineage_summary["option_metadata_by_ref"],
                source.option_refs[0]: unsafe_metadata,
            },
        },
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_authority_creating_followup_option"


def test_110p_option_that_implies_execution_blocks_selection():
    source = choice_surface()
    unsafe_metadata = {
        **source.lineage_summary["option_metadata_by_ref"][source.option_refs[0]],
        "implies_execution": True,
    }
    surface = replace(
        source,
        lineage_summary={
            **source.lineage_summary,
            "option_metadata_by_ref": {
                **source.lineage_summary["option_metadata_by_ref"],
                source.option_refs[0]: unsafe_metadata,
            },
        },
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_execution_implying_followup_option"


def test_110p_review_failure_reason_option_kind_remains_blocked():
    source = choice_surface()
    unsupported_metadata = {
        **source.lineage_summary["option_metadata_by_ref"][source.option_refs[0]],
        "option_kind": "review_failure_reason",
    }
    surface = replace(
        source,
        lineage_summary={
            **source.lineage_summary,
            "option_metadata_by_ref": {
                **source.lineage_summary["option_metadata_by_ref"],
                source.option_refs[0]: unsupported_metadata,
            },
        },
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.selected_option_kind == "review_failure_reason"
    assert record.rejection_reason == "rejected_unsupported_followup_option_kind"


def test_110p_selection_preserves_100p_101p_102p_103p_104p_105p_106p_107p_108p_109p_lineage():
    surface = choice_surface(delivery_kwargs={"require_approval": True})

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    lineage = record.lineage_summary
    choice_lineage = lineage["upstream_lineage"]
    draft_lineage = choice_lineage["upstream_lineage"]
    delivery_lineage = draft_lineage["upstream_lineage"]
    surface_lineage = delivery_lineage["upstream_lineage"]

    assert lineage["selection_stage"] == TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE
    assert lineage["choice_surface_stage"] == "109P"
    assert lineage["draft_planner_stage"] == "108P"
    assert lineage["followup_stage"] == "107P"
    assert lineage["acknowledgement_stage"] == "106P"
    assert lineage["delivery_stage"] == "105P"
    assert lineage["source_surface_stage"] == "104P"
    assert lineage["inbox_stage"] == "103P"
    assert surface_lineage["cost_preflight_evidence"]["request_id"] == "cost-request-110p"
    assert surface_lineage["approval_evidence"]["action_packet_id"]


def test_110p_visible_response_does_not_dump_raw_private_evidence():
    surface = choice_surface(
        delivery_kwargs={
            "completion_payload_summary": {
                "summary": "Resumen seguro",
                "request_payload": {"secret": "value"},
                "approval_evidence": {"private": "value"},
            }
        }
    )

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert "request_payload" not in record.response_text
    assert "approval_evidence" not in record.response_text
    assert "secret" not in record.response_text


def test_110p_response_envelope_is_local_and_send_disallowed():
    surface = choice_surface()
    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    envelope = build_followup_choice_selection_response_envelope(record)

    assert isinstance(envelope, TelegramFollowUpChoiceSelectionResponseEnvelope)
    assert envelope.channel == "telegram"
    assert envelope.send_allowed is False


def test_110p_selection_does_not_create_async_delegation():
    surface = choice_surface()
    registry = TelegramFollowUpChoiceSelectionRegistry()

    bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=registry,
    )

    text = SELECTION_PATH.read_text()
    assert "register_async_delegation_handle" not in text
    assert "delegate_task" not in text


def test_110p_selection_does_not_create_action_packet_or_approval():
    surface = choice_surface()

    bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    text = SELECTION_PATH.read_text()
    assert "create_action_packet" not in text
    assert "submit_action_packet_for_approval" not in text


def test_110p_selection_does_not_call_model_or_tool():
    surface = choice_surface()

    bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    text = SELECTION_PATH.read_text()
    assert "from app.cost_governor import" not in text
    assert "from app.model_router import" not in text


def test_110p_selection_does_not_mutate_memory():
    surface = choice_surface()

    bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    text = SELECTION_PATH.read_text()
    assert "memory_center" not in text
    assert "write_memory" not in text


def test_110p_selection_does_not_send_telegram_message():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    envelope = build_followup_choice_selection_response_envelope(record)

    assert envelope.send_allowed is False


def test_110p_no_live_telegram_api_call_is_used():
    surface = choice_surface()

    bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    text = SELECTION_PATH.read_text()
    assert "requests." not in text
    assert "httpx." not in text
    assert "telegram.Bot" not in text


def test_110p_execution_request_in_payload_is_blocked():
    surface = choice_surface()

    record = bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=selection_payload(surface, requests_execution=True),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )

    assert record.rejection_reason == "rejected_execution_approval_requested"


def test_110p_111p_plus_remains_unauthorized():
    text = SELECTION_PATH.read_text()

    assert "111P" not in text
    assert "delegate_task" not in text
