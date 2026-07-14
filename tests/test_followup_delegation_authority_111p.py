from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.action_packet_approval import ActionPacketDecision, ActionPacketRequest, apply_action_packet_decision, create_action_packet, submit_action_packet_for_approval
from app.async_delegation_authority import AsyncDelegationRequest, build_async_delegation_action_packet_request, create_async_delegation_authority_state
from app.async_result_surface import build_async_result_surface
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate, evaluate_cost_preflight
from app.followup_delegation_authority import (
    FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
    FOLLOWUP_OPTION_KIND_TO_TASK_CLASS,
    FollowUpDelegationAuthorizationEvidence,
    FollowUpDelegationRegistry,
    create_followup_delegation_from_selection,
    build_followup_delegation_response_envelope,
)
from app.followup_draft_planner import FollowUpDraftPlanRegistry, create_followup_draft_plan
from app.followup_intent_review import FollowUpIntentReviewQueue, create_followup_intent_from_acknowledgement
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord, TelegramAsyncResultDeliveryRegistry, TelegramOwnerBinding, deliver_async_result_surface_to_telegram
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionPayload, TelegramFollowUpChoiceSelectionRegistry, bind_telegram_followup_choice_selection
from app.telegram_followup_choice_surface import TelegramFollowUpChoiceSurfaceRegistry, create_telegram_followup_choice_surface
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord, TelegramResultAcknowledgementRegistry, TelegramResultCallbackPayload, bind_telegram_result_acknowledgement
from app.async_delegation_authority import (
    build_completion_event,
    register_async_delegation_handle,
)
from app.async_delegation_inbox import AsyncDelegationCompletionInbox, create_async_delegation_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/followup_delegation_authority.py"
USE_DEFAULT = object()


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
        "delegation_id": "delegation-111p-seed",
        "source_stage": "98P",
        "owner_id": "owner-111p",
        "robot_id": "robot-111p",
        "actor_id": "actor-111p",
        "actor_role": "owner_admin",
        "task_class": "async_delegation",
        "requested_capability": "summarize_followup_seed",
        "requested_route_mode": "balanced",
        "request_payload": {"summary": "seed"},
        "required_policy_trace": ("command_surface_policy_90p", "skill_scope_policy_91p", "tool_authority_policy_92p"),
        "required_memory_projection_request_id": None,
        "required_routine_run_id": "routine-111p",
        "expires_at": "2026-06-21T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-111p",
        "owner_id": "owner-111p",
        "robot_id": "robot-111p",
        "task_class": "async_delegation",
        "routing_mode": "balanced",
        "sensitivity": "ordinary",
        "requires_tools": False,
        "requires_long_context": False,
        "input_chars_estimate": 1600,
        "expected_output_chars": 900,
        "context_item_count": 2,
        "active_skill_id": "basic_assistant",
        "memory_context_used": True,
        "routine_requested": True,
        "async_delegation_requested": True,
        "authority_expansion_requested": False,
    }
    values.update(overrides)
    return TaskCostRequest(**values)


def synthetic_preflight(request: TaskCostRequest, *, decision: str = "allow", selected_model_id: str = "balanced_standard_v1") -> CostPreflightResult:
    token_estimate = TokenUsageEstimate(
        estimated_input_tokens=400,
        estimated_output_tokens=250,
        estimated_total_tokens=650,
        estimation_basis="test_fixture",
        long_context_applied=False,
    )
    route = ModelRouteDecision(
        selected_provider_id="local_fixture",
        selected_model_id=selected_model_id,
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=(selected_model_id,),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id=selected_model_id,
        candidate_model_ids=(selected_model_id,),
        decision=decision,
        reason_code="allow_selected_eligible_route" if decision != "require_confirmation" else "confirmation_cost_threshold",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.03,
        budget_state="within_budget" if decision != "require_confirmation" else "confirmation_required",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision=decision,
        budget_policy_id="policy-111p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=decision == "require_confirmation",
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-111p",
        "owner_id": "owner-111p",
        "robot_id": "robot-111p",
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


def approval_decision(packet_state, *, choice: str, occurred_at: str = "2026-06-20T12:05:00Z") -> ActionPacketDecision:
    return ActionPacketDecision(
        packet_id=packet_state.packet.packet_id,
        packet_version=packet_state.packet.packet_version,
        decision=choice,
        actor_id=packet_state.packet.actor_id,
        actor_role=packet_state.packet.actor_role,
        owner_id=packet_state.packet.owner_id,
        robot_id=packet_state.packet.robot_id,
        reason_code=f"{choice}_followup_delegation",
        edit_payload=None,
        resume_token_id=None,
        occurred_at=occurred_at,
    )


def accepted_record() -> object:
    task_request = task_cost_request()
    state = register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=delegation_request(),
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_preflight(task_request),
            occurred_at="2026-06-20T09:00:00Z",
        ),
        occurred_at="2026-06-20T09:05:00Z",
    )
    event = build_completion_event(
        authority_state=state,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={
            "highlights": [
                "El documento contiene obligaciones de confidencialidad amplias.",
                "La duracion principal parece ser de 3 anos.",
                "No se detecto clausula de exclusividad.",
                "Requiere revision humana antes de firma.",
            ]
        },
        reason_code="completed_local_record",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-111p",
        "robot_id": "robot-111p",
        "telegram_chat_id": "telegram-chat-111p",
        "channel": "telegram",
        "enabled": True,
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def delivered_record() -> TelegramAsyncResultDeliveryRecord:
    surface = build_async_result_surface(accepted_record())
    assert surface is not None
    return deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=TelegramAsyncResultDeliveryRegistry(),
    )


def followup_acknowledgement(delivery: TelegramAsyncResultDeliveryRecord | None = None) -> TelegramResultAcknowledgementRecord:
    if delivery is None:
        delivery = delivered_record()
    return bind_telegram_result_acknowledgement(
        delivery_registry=delivery_registry_with(delivery),
        callback_payload=TelegramResultCallbackPayload(
            delivery_id=delivery.delivery_id,
            surface_id=delivery.surface_id,
            owner_id=delivery.owner_id,
            robot_id=delivery.robot_id,
            telegram_chat_id=delivery.telegram_chat_id,
            action="request_followup_pending",
        ),
        registry=TelegramResultAcknowledgementRegistry(),
    )


def delivery_registry_with(record: TelegramAsyncResultDeliveryRecord) -> TelegramAsyncResultDeliveryRegistry:
    registry = TelegramAsyncResultDeliveryRegistry()
    registry.store(record)
    return registry


def pending_followup_intent():
    return create_followup_intent_from_acknowledgement(
        acknowledgement_record=followup_acknowledgement(),
        queue=FollowUpIntentReviewQueue(),
    )


def drafted_plan():
    return create_followup_draft_plan(
        followup_intent_record=pending_followup_intent(),
        registry=FollowUpDraftPlanRegistry(),
    )


def choice_surface():
    return create_telegram_followup_choice_surface(
        draft_plan_record=drafted_plan(),
        registry=TelegramFollowUpChoiceSurfaceRegistry(),
    )


def selection(option_index: int = 0):
    surface = choice_surface()
    return bind_telegram_followup_choice_selection(
        choice_surface_record=surface,
        payload=TelegramFollowUpChoiceSelectionPayload(
            choice_surface_id=surface.choice_surface_id,
            draft_plan_id=surface.draft_plan_id,
            selected_option_id=surface.option_refs[option_index],
            owner_id=surface.owner_id,
            robot_id=surface.robot_id,
            telegram_chat_id=surface.telegram_chat_id,
        ),
        registry=TelegramFollowUpChoiceSelectionRegistry(),
    )


def authorization(selection_record, **overrides) -> FollowUpDelegationAuthorizationEvidence:
    values = {
        "authorization_id": "followup-auth-111p",
        "authorization_kind": "followup_delegation_authorization",
        "selection_id": selection_record.selection_id,
        "owner_id": selection_record.owner_id,
        "robot_id": selection_record.robot_id,
        "selected_option_id": selection_record.selected_option_id,
        "selected_option_kind": selection_record.selected_option_kind,
        "cost_preflight_request_id": "cost-request-111p",
        "approval_evidence_id": None,
        "explicit_user_authorized": True,
    }
    values.update(overrides)
    return FollowUpDelegationAuthorizationEvidence(**values)


def followup_async_request(selection_record, auth, task_request):
    task_class = FOLLOWUP_OPTION_KIND_TO_TASK_CLASS[selection_record.selected_option_kind]
    delegation_id = "followup_delegation_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                selection_record.selection_id,
                selection_record.selected_option_id,
                selection_record.selected_option_kind,
                selection_record.owner_id,
                selection_record.robot_id,
                selection_record.draft_plan_id,
                selection_record.choice_surface_id,
                auth.cost_preflight_request_id,
                auth.authorization_id,
            ]
        ),
    ).hex[:12]
    return AsyncDelegationRequest(
        delegation_id=delegation_id,
        source_stage=FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        actor_id=selection_record.owner_id,
        actor_role="owner_admin",
        task_class="async_delegation",
        requested_capability=f"prepare_{task_class.lower()}",
        requested_route_mode=task_request.routing_mode,
        request_payload={
            "followup_task_class": task_class,
            "selected_option_id": selection_record.selected_option_id,
            "selected_option_kind": selection_record.selected_option_kind,
            "selection_id": selection_record.selection_id,
            "draft_plan_id": selection_record.draft_plan_id,
            "choice_surface_id": selection_record.choice_surface_id,
            "acknowledgement_id": selection_record.acknowledgement_id,
            "delivery_id": selection_record.delivery_id,
            "source_surface_id": selection_record.source_surface_id,
            "inbox_record_id": selection_record.inbox_record_id,
            "authorization_id": auth.authorization_id,
            "effect_class": "ASYNC_FOLLOWUP_PREPARATION",
            "send_allowed": False,
        },
        required_policy_trace=("telegram_policy_chain_95p", "followup_delegation_authority_111p"),
        required_memory_projection_request_id=None,
        required_routine_run_id=None,
        expires_at=None,
        authority_expansion_requested=False,
        live_dispatch_requested=False,
    )


def approved_async_delegation_packet(selection_record, auth, task_request, policy, preflight):
    request = followup_async_request(selection_record, auth, task_request)
    packet_request = build_async_delegation_action_packet_request(
        request=request,
        cost_preflight=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )
    approval_state = create_action_packet(request=packet_request, occurred_at="2026-06-20T11:00:00Z")
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=request.owner_id,
        actor_role="owner_admin",
        occurred_at="2026-06-20T11:01:00Z",
    )
    return apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )


def generic_approval_packet() -> object:
    packet_request = ActionPacketRequest(
        request_id="generic-approval-111p",
        source_stage="100P",
        action_type="cost_confirmation",
        owner_id="owner-111p",
        robot_id="robot-111p",
        actor_id="owner-111p",
        actor_role="owner_admin",
        requested_by_actor_id="owner-111p",
        requested_by_actor_role="owner_admin",
        required_policy_trace=("telegram_policy_chain_95p",),
        required_cost_preflight={"request_id": "cost-request-111p", "decision": "require_confirmation", "selected_model_id": "balanced_standard_v1"},
        required_memory_projection=None,
        required_routine_context=None,
        action_payload={"confirmation_type": "budget_confirmation"},
        review_expires_at="2026-06-21T00:00:00Z",
        resume_scope="exact_preflight",
    )
    approval_state = create_action_packet(request=packet_request, occurred_at="2026-06-20T11:00:00Z")
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id="owner-111p",
        actor_role="owner_admin",
        occurred_at="2026-06-20T11:01:00Z",
    )
    return apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )


def create_record(
    *,
    selection_record=None,
    auth=USE_DEFAULT,
    preflight=USE_DEFAULT,
    task_request=USE_DEFAULT,
    policy=USE_DEFAULT,
    approval=None,
    registry=USE_DEFAULT,
    occurred_at="2026-06-20T12:00:00Z",
):
    selection_record = selection() if selection_record is None else selection_record
    task_request = task_cost_request() if task_request is USE_DEFAULT else task_request
    preflight = synthetic_preflight(task_request) if preflight is USE_DEFAULT else preflight
    policy = budget_policy() if policy is USE_DEFAULT else policy
    auth = authorization(selection_record) if auth is USE_DEFAULT else auth
    registry = FollowUpDelegationRegistry() if registry is USE_DEFAULT else registry
    return create_followup_delegation_from_selection(
        selection_record=selection_record,
        authorization_evidence=auth,
        cost_preflight_evidence=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        approval_evidence=approval,
        followup_registry=registry,
        occurred_at=occurred_at,
    )


def test_111p_valid_selected_option_creates_followup_delegation():
    registry = FollowUpDelegationRegistry()
    record = create_record(registry=registry)
    state = registry.get_authority_state(record.followup_delegation_id)

    assert record.status == "registered"
    assert record.followup_task_class == "FOLLOWUP_DEEPER_SUMMARY"
    assert record.async_handle_id is not None
    assert state is not None
    assert state.packet.state == "registered"
    assert state.handle is not None
    assert state.handle.status == "registered"


def test_111p_selection_alone_does_not_create_delegation():
    record = create_record(auth=None)
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_missing_followup_delegation_authorization"


def test_111p_requires_explicit_followup_delegation_authorization():
    selected = selection()
    record = create_record(auth=authorization(selected, explicit_user_authorized=False), selection_record=selected)
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_explicit_followup_authorization_required"


def test_111p_generic_cost_confirmation_does_not_authorize_delegation():
    selected = selection()
    record = create_record(
        selection_record=selected,
        auth=authorization(selected, authorization_kind="cost_confirmation"),
    )
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_invalid_followup_delegation_authorization"


def test_111p_missing_100p_cost_lineage_blocks_delegation():
    record = create_record(preflight=None)
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_missing_cost_preflight_lineage"


def test_111p_cost_preflight_request_mismatch_blocks_delegation():
    selected = selection()
    record = create_record(
        selection_record=selected,
        auth=authorization(selected, cost_preflight_request_id="other-cost"),
    )
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_cost_preflight_request_id_mismatch"


def test_111p_route_model_mismatch_blocks_delegation():
    task_request = task_cost_request(routing_mode="economy")
    preflight = synthetic_preflight(task_request, selected_model_id="economy_basic_v1")
    record = create_record(task_request=task_request, preflight=preflight)
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_selected_route_mismatch"


def test_111p_missing_required_101p_approval_blocks_delegation():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection()
    record = create_record(selection_record=selected, task_request=task_request, preflight=preflight, auth=authorization(selected, approval_evidence_id="required-packet"))
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_missing_required_approval_evidence"


def test_111p_generic_approval_evidence_does_not_bind():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection()
    record = create_record(
        selection_record=selected,
        task_request=task_request,
        preflight=preflight,
        auth=authorization(selected, approval_evidence_id="generic-approval-111p"),
        approval=generic_approval_packet(),
    )
    assert record.status == "blocked"
    assert record.rejection_reason == "blocked_generic_approval_evidence_does_not_bind"


def test_111p_require_confirmation_path_registers_after_exact_approval_binding():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection()
    policy = budget_policy()
    approved = approved_async_delegation_packet(selected, authorization(selected, approval_evidence_id=None), task_request, policy, preflight)
    record = create_record(
        selection_record=selected,
        task_request=task_request,
        preflight=preflight,
        policy=policy,
        auth=authorization(selected, approval_evidence_id=approved.packet.packet_id),
        approval=approved,
    )
    assert record.status == "registered"
    assert record.lineage_summary["approval_stage"] == "101P"


def test_111p_owner_robot_and_chat_mismatch_block_delegation():
    selected = selection()
    owner_block = create_record(selection_record=replace(selected, owner_id="other-owner"), auth=authorization(selected))
    robot_block = create_record(selection_record=replace(selected, robot_id="other-robot"), auth=authorization(selected))
    chat_block = create_record(selection_record=replace(selected, telegram_chat_id="other-chat"), auth=authorization(selected))

    assert owner_block.rejection_reason == "blocked_owner_mismatch"
    assert robot_block.rejection_reason == "blocked_robot_mismatch"
    assert chat_block.rejection_reason == "blocked_selection_chat_mismatch"


def test_111p_selected_option_mismatch_and_unknown_option_block_delegation():
    selected = selection()
    mismatched_auth = create_record(selection_record=selected, auth=authorization(selected, selected_option_id="other-option"))
    unknown_metadata = replace(
        selected,
        lineage_summary={**selected.lineage_summary, "upstream_lineage": {**selected.lineage_summary["upstream_lineage"], "option_metadata_by_ref": {}}},
    )
    unknown_option = create_record(selection_record=unknown_metadata, auth=authorization(unknown_metadata))

    assert mismatched_auth.rejection_reason == "blocked_selected_option_mismatch"
    assert unknown_option.rejection_reason == "blocked_unknown_selected_option_id"


def test_111p_cancel_selection_and_blocked_selection_create_no_delegation():
    cancelled = selection(option_index=-1)
    blocked = replace(selection(), status="blocked", rejection_reason="manual_block")

    cancelled_record = create_record(selection_record=cancelled, auth=authorization(cancelled))
    blocked_record = create_record(selection_record=blocked, auth=authorization(blocked))

    assert cancelled_record.status == "cancelled_no_action"
    assert cancelled_record.async_handle_id is None
    assert blocked_record.status == "blocked"
    assert blocked_record.async_handle_id is None


def test_111p_authority_expanding_and_external_effect_options_block_delegation():
    selected = selection()
    metadata = dict(selected.lineage_summary["upstream_lineage"]["option_metadata_by_ref"][selected.selected_option_id])
    authority_surface = replace(
        selected,
        lineage_summary={
            **selected.lineage_summary,
            "upstream_lineage": {
                **selected.lineage_summary["upstream_lineage"],
                "option_metadata_by_ref": {
                    **selected.lineage_summary["upstream_lineage"]["option_metadata_by_ref"],
                    selected.selected_option_id: {**metadata, "creates_authority": True},
                },
            },
        },
    )
    external_surface = replace(
        selected,
        lineage_summary={
            **selected.lineage_summary,
            "upstream_lineage": {
                **selected.lineage_summary["upstream_lineage"],
                "option_metadata_by_ref": {
                    **selected.lineage_summary["upstream_lineage"]["option_metadata_by_ref"],
                    selected.selected_option_id: {**metadata, "implies_external_send": True},
                },
            },
        },
    )

    authority_record = create_record(selection_record=authority_surface, auth=authorization(authority_surface))
    external_record = create_record(selection_record=external_surface, auth=authorization(external_surface))

    assert authority_record.rejection_reason == "blocked_authority_expanding_option"
    assert external_record.rejection_reason == "blocked_external_effect_option"


def test_111p_duplicate_delegation_creation_is_idempotent_and_does_not_create_second_handle():
    registry = FollowUpDelegationRegistry()
    first = create_record(registry=registry)
    second = create_record(registry=registry)

    assert second.followup_delegation_id == first.followup_delegation_id
    assert second.async_handle_id == first.async_handle_id
    assert len(registry.list_records()) == 1


def test_111p_delegation_preserves_full_lineage_and_registered_non_executing_handle():
    registry = FollowUpDelegationRegistry()
    record = create_record(registry=registry)
    state = registry.get_authority_state(record.followup_delegation_id)

    assert record.lineage_summary["cost_preflight_stage"] == "100P"
    assert record.lineage_summary["async_delegation_stage"] == "102P"
    assert record.lineage_summary["selection_stage"] == "110P"
    assert record.lineage_summary["choice_surface_stage"] == "109P"
    assert record.lineage_summary["draft_planner_stage"] == "108P"
    assert record.lineage_summary["followup_stage"] == "107P"
    assert record.lineage_summary["acknowledgement_stage"] == "106P"
    assert record.lineage_summary["delivery_stage"] == "105P"
    assert record.lineage_summary["source_surface_stage"] == "104P"
    assert record.lineage_summary["inbox_stage"] == "103P"
    assert state is not None
    assert state.handle is not None
    assert state.handle.dispatch_authorized is False
    assert state.packet.execution_authorized is False
    assert state.packet.external_effect_authorized is False
    assert state.packet.provider_call_authorized is False
    assert state.packet.live_dispatch_authorized is False
    assert state.completion_events == ()


def test_111p_response_envelope_is_local_and_send_disallowed():
    record = create_record()
    envelope = build_followup_delegation_response_envelope(record)

    assert envelope.channel == "telegram"
    assert envelope.telegram_chat_id == record.telegram_chat_id
    assert envelope.send_allowed is False


def test_111p_112p_plus_remains_unauthorized():
    task_request = task_cost_request()
    state = create_async_delegation_authority_state(
        request=delegation_request(source_stage="112P"),
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        cost_preflight=synthetic_preflight(task_request),
        occurred_at="2026-06-20T10:00:00Z",
    )

    assert state.packet.state == "blocked"
    assert state.trace_records[-1].reason_code == "blocked_unauthorized_source_stage"
