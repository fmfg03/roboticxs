from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.action_packet_approval import (
    ActionPacketDecision,
    ActionPacketRequest,
    apply_action_packet_decision,
    create_action_packet,
    submit_action_packet_for_approval,
)
from app.async_delegation_authority import (
    AsyncDelegationRequest,
    build_async_delegation_action_packet_request,
    create_async_delegation_authority_state,
    serialize_async_delegation_authority_state,
)
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    CostTraceRecord,
    ModelRouteDecision,
    TaskCostRequest,
    TokenUsageEstimate,
)
from app.followup_delegation_authority import (
    FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
    FOLLOWUP_OPTION_KIND_TO_TASK_CLASS,
    FollowUpDelegationAuthorizationEvidence,
    FollowUpDelegationRegistry,
    create_followup_delegation_from_selection,
)
from app.followup_execution_skeleton import (
    FOLLOWUP_EXECUTION_SKELETON_STAGE,
    FollowUpExecutionAttemptRegistry,
    FollowUpExecutionFixture,
    build_followup_execution_skeleton_response_envelope,
    execute_followup_delegation_skeleton,
)
from app.followup_draft_planner import FollowUpDraftPlanRegistry, create_followup_draft_plan
from app.followup_intent_review import FollowUpIntentReviewQueue, create_followup_intent_from_acknowledgement
from app.telegram_async_result_delivery import (
    TelegramAsyncResultDeliveryRecord,
    TelegramAsyncResultDeliveryRegistry,
    TelegramOwnerBinding,
    deliver_async_result_surface_to_telegram,
)
from app.telegram_followup_choice_selection import (
    TelegramFollowUpChoiceSelectionPayload,
    TelegramFollowUpChoiceSelectionRegistry,
    bind_telegram_followup_choice_selection,
)
from app.telegram_followup_choice_surface import (
    TelegramFollowUpChoiceSurfaceRegistry,
    create_telegram_followup_choice_surface,
)
from app.telegram_result_acknowledgement import (
    TelegramResultAcknowledgementRecord,
    TelegramResultAcknowledgementRegistry,
    TelegramResultCallbackPayload,
    bind_telegram_result_acknowledgement,
)
from app.async_delegation_authority import build_completion_event, register_async_delegation_handle
from app.async_delegation_inbox import AsyncDelegationCompletionInbox, create_async_delegation_registry
from app.async_result_surface import build_async_result_surface


REPO_ROOT = Path(__file__).resolve().parents[1]
SKELETON_PATH = REPO_ROOT / "app/followup_execution_skeleton.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
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
        "delegation_id": "delegation-112p-seed",
        "source_stage": "98P",
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
        "actor_id": "actor-112p",
        "actor_role": "owner_admin",
        "task_class": "async_delegation",
        "requested_capability": "summarize_followup_seed",
        "requested_route_mode": "balanced",
        "request_payload": {"summary": "seed"},
        "required_policy_trace": (
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        ),
        "required_memory_projection_request_id": None,
        "required_routine_run_id": "routine-112p",
        "expires_at": "2026-06-21T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-112p",
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
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


def synthetic_preflight(
    request: TaskCostRequest,
    *,
    decision: str = "allow",
    selected_model_id: str = "balanced_standard_v1",
    estimated_cost_usd: float = 0.03,
) -> CostPreflightResult:
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
        reason_code=(
            "allow_selected_eligible_route"
            if decision != "require_confirmation"
            else "confirmation_cost_threshold"
        ),
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        budget_state=(
            "within_budget" if decision != "require_confirmation" else "confirmation_required"
        ),
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision=decision,
        budget_policy_id="policy-112p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=estimated_cost_usd,
        confirmation_required=decision == "require_confirmation",
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-112p",
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
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


def approval_decision(
    packet_state,
    *,
    choice: str,
    occurred_at: str = "2026-06-20T12:05:00Z",
) -> ActionPacketDecision:
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
        completion_payload_summary={"highlights": ["fixture"]},
        reason_code="completed_local_record",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
        "telegram_chat_id": "telegram-chat-112p",
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


def followup_acknowledgement(
    delivery: TelegramAsyncResultDeliveryRecord | None = None,
) -> TelegramResultAcknowledgementRecord:
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


def delivery_registry_with(
    record: TelegramAsyncResultDeliveryRecord,
) -> TelegramAsyncResultDeliveryRegistry:
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
        "authorization_id": "followup-auth-112p",
        "authorization_kind": "followup_delegation_authorization",
        "selection_id": selection_record.selection_id,
        "owner_id": selection_record.owner_id,
        "robot_id": selection_record.robot_id,
        "selected_option_id": selection_record.selected_option_id,
        "selected_option_kind": selection_record.selected_option_kind,
        "cost_preflight_request_id": "cost-request-112p",
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
    approval_state = create_action_packet(
        request=packet_request,
        occurred_at="2026-06-20T11:00:00Z",
    )
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
        request_id="generic-approval-112p",
        source_stage="100P",
        action_type="cost_confirmation",
        owner_id="owner-112p",
        robot_id="robot-112p",
        actor_id="owner-112p",
        actor_role="owner_admin",
        requested_by_actor_id="owner-112p",
        requested_by_actor_role="owner_admin",
        required_policy_trace=("telegram_policy_chain_95p",),
        required_cost_preflight={
            "request_id": "cost-request-112p",
            "decision": "require_confirmation",
            "selected_model_id": "balanced_standard_v1",
        },
        required_memory_projection=None,
        required_routine_context=None,
        action_payload={"confirmation_type": "budget_confirmation"},
        review_expires_at="2026-06-21T00:00:00Z",
        resume_scope="exact_preflight",
    )
    approval_state = create_action_packet(
        request=packet_request,
        occurred_at="2026-06-20T11:00:00Z",
    )
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id="owner-112p",
        actor_role="owner_admin",
        occurred_at="2026-06-20T11:01:00Z",
    )
    return apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )


def create_followup_record(
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
    record = create_followup_delegation_from_selection(
        selection_record=selection_record,
        authorization_evidence=auth,
        cost_preflight_evidence=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        approval_evidence=approval,
        followup_registry=registry,
        occurred_at=occurred_at,
    )
    return record, registry


def fixture(**overrides) -> FollowUpExecutionFixture:
    values = {
        "fixture_id": "fixture-112p",
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
        "allowed_task_classes": (
            "FOLLOWUP_DEEPER_SUMMARY",
            "FOLLOWUP_EXTRACT_QUESTIONS",
            "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
            "FOLLOWUP_COMPARE_PRIOR_VERSION",
        ),
        "deterministic_payloads": {
            "FOLLOWUP_DEEPER_SUMMARY": "Fixture deeper summary.",
            "FOLLOWUP_EXTRACT_QUESTIONS": "Fixture review questions.",
            "FOLLOWUP_HUMAN_REVIEW_CHECKLIST": "Fixture review checklist.",
        },
        "force_failure_task_classes": (),
    }
    values.update(overrides)
    return FollowUpExecutionFixture(**values)


def compare_prior_version_record():
    record, registry = create_followup_record()
    state = registry.get_authority_state(record.followup_delegation_id)
    assert state is not None and state.handle is not None
    updated_request_snapshot = {
        **state.packet.request_snapshot,
        "request_payload": {
            **state.packet.request_snapshot["request_payload"],
            "followup_task_class": "FOLLOWUP_COMPARE_PRIOR_VERSION",
        },
    }
    registry.authority_states_by_id[record.followup_delegation_id] = replace(
        state,
        packet=replace(
            state.packet,
            request_snapshot=updated_request_snapshot,
        ),
        handle=replace(
            state.handle,
            original_request_evidence={
                **state.handle.original_request_evidence,
                "request_payload": {
                    **state.handle.original_request_evidence["request_payload"],
                    "followup_task_class": "FOLLOWUP_COMPARE_PRIOR_VERSION",
                },
            },
        ),
    )
    return (
        replace(
            record,
            followup_task_class="FOLLOWUP_COMPARE_PRIOR_VERSION",
            selected_option_kind="compare_prior_version",
            lineage_summary={
                **record.lineage_summary,
                "followup_task_class": "FOLLOWUP_COMPARE_PRIOR_VERSION",
                "selected_option_kind": "compare_prior_version",
            },
        ),
        registry,
    )


def execute_record(
    *,
    record=USE_DEFAULT,
    registry=USE_DEFAULT,
    attempt_registry=USE_DEFAULT,
    execution_fixture=USE_DEFAULT,
):
    if record is USE_DEFAULT or registry is USE_DEFAULT:
        created, created_registry = create_followup_record()
        if record is USE_DEFAULT:
            record = created
        if registry is USE_DEFAULT:
            registry = created_registry
    attempt_registry = (
        FollowUpExecutionAttemptRegistry()
        if attempt_registry is USE_DEFAULT
        else attempt_registry
    )
    execution_fixture = fixture() if execution_fixture is USE_DEFAULT else execution_fixture
    return execute_followup_delegation_skeleton(
        followup_delegation_record=record,
        followup_registry=registry,
        fixture=execution_fixture,
        attempt_registry=attempt_registry,
    )


def test_112p_registered_followup_delegation_creates_completed_candidate():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "completed_candidate"
    assert attempt.result_summary == "Fixture deeper summary."
    assert attempt.completion_event_candidate is not None
    assert attempt.completion_event_candidate.completion_status == "completed"
    assert attempt.completion_event_candidate.source_stage == FOLLOWUP_EXECUTION_SKELETON_STAGE


def test_112p_registered_followup_delegation_can_create_failed_candidate():
    record, registry = compare_prior_version_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "failed_candidate"
    assert attempt.failure_reason == "Prior version unavailable in local execution fixture."
    assert attempt.failure_event_candidate is not None
    assert attempt.failure_event_candidate.completion_status == "failed"


def test_112p_cancelled_delegation_blocks_execution():
    record, registry = create_followup_record(selection_record=selection(option_index=3))
    attempt = execute_record(record=record, registry=registry)

    assert record.status == "cancelled_no_action"
    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_followup_delegation_status_cancelled_no_action"


def test_112p_blocked_delegation_blocks_execution():
    record, registry = create_followup_record(auth=None)
    attempt = execute_record(record=record, registry=registry)

    assert record.status == "blocked"
    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_followup_delegation_status_blocked"


def test_112p_unknown_delegation_blocks_execution():
    attempt = execute_followup_delegation_skeleton(
        followup_delegation_record=object(),
        followup_registry=FollowUpDelegationRegistry(),
        fixture=fixture(),
        attempt_registry=FollowUpExecutionAttemptRegistry(),
    )

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_unknown_followup_delegation_record"


def test_112p_missing_async_packet_or_handle_blocks_execution():
    record, registry = create_followup_record()
    corrupted = replace(record, async_packet_id=None, async_handle_id=None)
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_missing_async_packet_or_handle"


def test_112p_owner_mismatch_blocks_execution():
    record, registry = create_followup_record()
    attempt = execute_record(
        record=record,
        registry=registry,
        execution_fixture=fixture(owner_id="other-owner"),
    )

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_owner_mismatch"


def test_112p_robot_mismatch_blocks_execution():
    record, registry = create_followup_record()
    attempt = execute_record(
        record=record,
        registry=registry,
        execution_fixture=fixture(robot_id="other-robot"),
    )

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_robot_mismatch"


def test_112p_task_class_mismatch_blocks_execution():
    record, registry = create_followup_record()
    corrupted = replace(record, followup_task_class="FOLLOWUP_UNKNOWN")
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_unsupported_followup_task_class"


def test_112p_missing_100p_cost_lineage_blocks_execution():
    record, registry = create_followup_record()
    corrupted = replace(record, lineage_summary={**record.lineage_summary, "cost_preflight_summary": None})
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_missing_100p_cost_lineage"


def test_112p_cost_preflight_request_mismatch_blocks_execution():
    record, registry = create_followup_record()
    corrupted = replace(
        record,
        lineage_summary={**record.lineage_summary, "cost_preflight_request_id": "other-request"},
    )
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_cost_preflight_request_mismatch"


def test_112p_route_model_mismatch_blocks_execution():
    record, registry = create_followup_record()
    cost = dict(record.lineage_summary["cost_preflight_summary"])
    route = dict(cost["route_decision"])
    route["selected_model_id"] = "other-model"
    cost["route_decision"] = route
    corrupted = replace(record, lineage_summary={**record.lineage_summary, "cost_preflight_summary": cost})
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_route_model_mismatch"


def test_112p_missing_required_101p_approval_blocks_execution():
    task_request = task_cost_request()
    record, registry = create_followup_record(
        task_request=task_request,
        preflight=synthetic_preflight(task_request, decision="require_confirmation"),
        approval=None,
    )
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_followup_delegation_status_blocked"


def test_112p_missing_102p_async_lineage_blocks_execution():
    record, _registry = create_followup_record()
    attempt = execute_record(record=record, registry=FollowUpDelegationRegistry())

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_missing_102p_async_lineage"


def test_112p_unsupported_task_class_blocks_execution():
    record, registry = create_followup_record()
    corrupted = replace(record, followup_task_class="FOLLOWUP_SIDE_EFFECT")
    attempt = execute_record(record=corrupted, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_unsupported_followup_task_class"


def test_112p_fixture_disallowed_task_class_blocks_execution():
    record, registry = create_followup_record()
    attempt = execute_record(
        record=record,
        registry=registry,
        execution_fixture=fixture(allowed_task_classes=("FOLLOWUP_EXTRACT_QUESTIONS",)),
    )

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_fixture_disallowed_task_class"


def test_112p_external_effect_request_blocks_execution():
    record, registry = create_followup_record()
    state = registry.get_authority_state(record.followup_delegation_id)
    assert state is not None and state.handle is not None
    registry.authority_states_by_id[record.followup_delegation_id] = replace(
        state,
        handle=replace(
            state.handle,
            original_request_evidence={
                **state.handle.original_request_evidence,
                "request_payload": {
                    **state.handle.original_request_evidence["request_payload"],
                    "send_allowed": True,
                },
            },
        ),
    )
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_external_effect_request"


def test_112p_live_model_or_tool_request_blocks_execution():
    record, registry = create_followup_record()
    state = registry.get_authority_state(record.followup_delegation_id)
    assert state is not None and state.handle is not None
    registry.authority_states_by_id[record.followup_delegation_id] = replace(
        state,
        handle=replace(
            state.handle,
            original_request_evidence={
                **state.handle.original_request_evidence,
                "request_payload": {
                    **state.handle.original_request_evidence["request_payload"],
                    "model_call_requested": True,
                },
            },
        ),
    )
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "blocked"
    assert attempt.rejection_reason == "blocked_live_model_or_tool_request"


def test_112p_completion_candidate_preserves_100p_101p_102p_103p_104p_105p_106p_107p_108p_109p_110p_111p_lineage():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection(option_index=1)
    approval = approved_async_delegation_packet(
        selected,
        authorization(selected, approval_evidence_id=None),
        task_request,
        budget_policy(),
        preflight,
    )
    auth = authorization(
        selected,
        approval_evidence_id=approval.packet.packet_id,
    )
    record, registry = create_followup_record(
        selection_record=selected,
        auth=auth,
        task_request=task_request,
        preflight=preflight,
        approval=approval,
    )
    attempt = execute_record(record=record, registry=registry)
    event = attempt.completion_event_candidate

    assert attempt.status == "completed_candidate"
    assert event is not None
    assert event.original_request_evidence["request_payload"]["selection_id"] == record.selection_id
    assert event.cost_preflight_evidence["request_id"] == record.lineage_summary["cost_preflight_request_id"]
    assert (
        event.approval_evidence.get("packet_id", event.approval_evidence.get("action_packet_id"))
        == record.lineage_summary["approval_packet_id"]
    )
    assert event.completion_payload_summary["followup_lineage"]["inbox_record_id"] == record.inbox_record_id
    assert event.completion_payload_summary["followup_lineage"]["source_surface_id"] == record.source_surface_id
    assert event.completion_payload_summary["followup_lineage"]["delivery_id"] == record.delivery_id
    assert event.completion_payload_summary["followup_lineage"]["acknowledgement_id"] == record.acknowledgement_id
    assert event.completion_payload_summary["followup_lineage"]["followup_intent_id"] == record.lineage_summary["followup_intent_id"]
    assert event.completion_payload_summary["followup_lineage"]["draft_plan_id"] == record.draft_plan_id
    assert event.completion_payload_summary["followup_lineage"]["choice_surface_id"] == record.choice_surface_id
    assert event.completion_payload_summary["followup_lineage"]["selection_id"] == record.selection_id
    assert event.completion_payload_summary["followup_lineage"]["followup_delegation_id"] == record.followup_delegation_id


def test_112p_failure_candidate_preserves_lineage():
    record, registry = compare_prior_version_record()
    attempt = execute_record(record=record, registry=registry)
    event = attempt.failure_event_candidate

    assert attempt.status == "failed_candidate"
    assert event is not None
    assert event.cost_preflight_evidence["request_id"] == record.lineage_summary["cost_preflight_request_id"]
    assert event.completion_payload_summary["followup_lineage"]["selection_id"] == record.selection_id
    assert event.completion_payload_summary["followup_lineage"]["followup_delegation_id"] == record.followup_delegation_id


def test_112p_no_synthetic_zero_cost_evidence_is_fabricated():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.completion_event_candidate is not None
    assert attempt.completion_event_candidate.cost_preflight_evidence["estimated_cost_usd"] > 0
    assert (
        attempt.completion_event_candidate.cost_preflight_evidence["trace"][-1]["estimated_cost_usd"]
        > 0
    )


def test_112p_generic_cost_confirmation_does_not_authorize_execution():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection(option_index=1)
    generic = generic_approval_packet()
    auth = authorization(
        selected,
        approval_evidence_id=generic.packet.packet_id,
    )
    record, registry = create_followup_record(
        selection_record=selected,
        auth=auth,
        task_request=task_request,
        preflight=preflight,
        approval=generic,
    )
    attempt = execute_record(record=record, registry=registry)

    assert attempt.status == "blocked"
    assert (
        attempt.rejection_reason
        == "blocked_followup_delegation_status_blocked"
    )


def test_112p_duplicate_execution_is_idempotent():
    record, registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    first = execute_record(
        record=record,
        registry=registry,
        attempt_registry=attempt_registry,
    )
    second = execute_record(
        record=record,
        registry=registry,
        attempt_registry=attempt_registry,
    )

    assert first == second
    assert attempt_registry.list_records() == (first,)


def test_112p_duplicate_does_not_create_second_event_candidate():
    record, registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    first = execute_record(
        record=record,
        registry=registry,
        attempt_registry=attempt_registry,
    )
    second = execute_record(
        record=record,
        registry=registry,
        attempt_registry=attempt_registry,
    )

    assert first.completion_event_candidate == second.completion_event_candidate
    assert len(attempt_registry.list_records()) == 1


def test_112p_does_not_insert_event_into_103p_inbox():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.completion_event_candidate is not None
    assert attempt.lineage_summary["async_handle_summary"]["status"] == "registered"


def test_112p_does_not_create_104p_surface():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.lineage_summary["upstream_lineage"]["source_surface_id"] == record.source_surface_id
    assert "surface_id" not in attempt.lineage_summary


def test_112p_does_not_create_105p_delivery():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)

    assert attempt.lineage_summary["upstream_lineage"]["delivery_id"] == record.delivery_id
    assert attempt.lineage_summary["followup_execution_stage"] == "112P"


def test_112p_does_not_dispatch_worker():
    text = SKELETON_PATH.read_text()

    for forbidden in ["delegate_task", "asyncio.create_task", "ThreadPoolExecutor", "multiprocessing"]:
        assert forbidden not in text


def test_112p_does_not_call_model_or_tool():
    text = SKELETON_PATH.read_text()

    for forbidden in ["openai.", "anthropic.", "requests.", "httpx.", "subprocess.", "Popen("]:
        assert forbidden not in text


def test_112p_does_not_mutate_memory():
    text = SKELETON_PATH.read_text()

    for forbidden in ["memory_center", "memory_service", "write_memory", "upsert_memory"]:
        assert forbidden not in text


def test_112p_does_not_send_telegram_message():
    text = SKELETON_PATH.read_text()

    for forbidden in ["send_message", "deliver_async_result_surface_to_telegram", "telegram.Bot"]:
        assert forbidden not in text


def test_112p_response_envelope_is_local_and_send_disallowed():
    record, registry = create_followup_record()
    attempt = execute_record(record=record, registry=registry)
    envelope = build_followup_execution_skeleton_response_envelope(attempt)

    assert envelope.channel == "telegram"
    assert envelope.telegram_chat_id == record.telegram_chat_id
    assert envelope.send_allowed is False
    assert envelope.text == "Fixture deeper summary."


def test_112p_113p_plus_remains_unauthorized():
    roadmap = ROADMAP_PATH.read_text()

    assert "113P and later remain unauthorized" in roadmap or "113P+ remains unauthorized" in roadmap
