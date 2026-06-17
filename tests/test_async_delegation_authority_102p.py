from __future__ import annotations

from pathlib import Path

from app.action_packet_approval import (
    ActionPacketDecision,
    create_action_packet,
    submit_action_packet_for_approval,
    apply_action_packet_decision,
)
from app.async_delegation_authority import (
    ASYNC_DELEGATION_STAGE,
    AsyncDelegationCompletionEvent,
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    build_async_delegation_action_packet_request,
    build_completion_event,
    cancel_async_delegation,
    create_async_delegation_authority_state,
    expire_async_delegation,
    record_async_delegation_completion,
    record_async_delegation_failure,
    register_async_delegation_handle,
    serialize_async_delegation_authority_state,
)
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    CostTraceRecord,
    ModelRouteDecision,
    TaskCostRequest,
    TokenUsageEstimate,
    evaluate_cost_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/async_delegation_authority.py"


def delegation_request(**overrides) -> AsyncDelegationRequest:
    values = {
        "delegation_id": "delegation-102p",
        "source_stage": "98P",
        "owner_id": "owner-102p",
        "robot_id": "robot-102p",
        "actor_id": "actor-102p",
        "actor_role": "owner_admin",
        "task_class": "async_delegation",
        "requested_capability": "summarize_long_running_task",
        "requested_route_mode": "balanced",
        "request_payload": {"summary": "Run the local-only async delegation packet flow."},
        "required_policy_trace": (
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        ),
        "required_memory_projection_request_id": None,
        "required_routine_run_id": "routine-102p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-102p",
        "owner_id": "owner-102p",
        "robot_id": "robot-102p",
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
        "policy_id": "policy-102p",
        "owner_id": "owner-102p",
        "robot_id": "robot-102p",
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
        selected_model_id="balanced_standard_v1",
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=("balanced_standard_v1",),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id="balanced_standard_v1",
        candidate_model_ids=("balanced_standard_v1",),
        decision="allow",
        reason_code="allow_selected_eligible_route",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.01,
        budget_state="within_budget",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision="allow",
        budget_policy_id="policy-102p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.01,
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
    approval_state = create_action_packet(
        request=packet_request,
        occurred_at="2026-06-17T12:00:00Z",
    )
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=request.owner_id,
        actor_role="owner_admin",
        occurred_at="2026-06-17T12:05:00Z",
    )
    approved = apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )
    return packet_request, approved


def test_creates_docs_only_local_authority_state_for_allow_path():
    request = delegation_request()
    task_request = task_cost_request()
    state = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        cost_preflight=synthetic_allow_preflight(task_request),
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert state.stage == ASYNC_DELEGATION_STAGE
    assert state.packet.state == "approved_local"
    assert state.packet.decision == "allow_local_register"
    assert state.packet.execution_authorized is False
    assert state.packet.live_dispatch_authorized is False
    assert state.trace_records[-1].reason_code == "preflight_allowed_local_registration"


def test_missing_owner_blocks_with_trace():
    state = create_async_delegation_authority_state(
        request=delegation_request(owner_id=""),
        task_cost_request=None,
        budget_policy=None,
        cost_preflight=None,
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert state.packet.state == "blocked"
    assert state.trace_records[-1].reason_code == "blocked_missing_owner_id"


def test_missing_cost_preflight_blocks_before_registration():
    state = create_async_delegation_authority_state(
        request=delegation_request(),
        task_cost_request=None,
        budget_policy=budget_policy(),
        cost_preflight=None,
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert state.packet.state == "preflight_blocked"
    assert state.packet.decision == "block"
    assert state.trace_records[-1].reason_code == "blocked_missing_cost_preflight"


def test_async_delegation_policy_disabled_blocks():
    request = delegation_request()
    task_request = task_cost_request()
    preflight = evaluate_cost_preflight(
        request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=False),
    )
    state = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=False),
        cost_preflight=preflight,
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert state.packet.state == "preflight_blocked"
    assert state.trace_records[-1].reason_code == "blocked_async_delegation_disabled_by_policy"


def test_require_confirmation_transitions_to_awaiting_approval():
    request = delegation_request()
    task_request = task_cost_request()
    preflight = evaluate_cost_preflight(
        request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=True),
    )
    state = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=True),
        cost_preflight=preflight,
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert preflight.decision == "require_confirmation"
    assert state.packet.state == "awaiting_approval"
    assert state.packet.decision == "require_approval"


def test_builds_101p_async_delegation_approval_request_with_exact_cost_evidence():
    request = delegation_request()
    task_request = task_cost_request()
    preflight = evaluate_cost_preflight(
        request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=True),
    )

    packet_request = build_async_delegation_action_packet_request(
        request=request,
        cost_preflight=preflight,
        task_cost_request=task_request,
        budget_policy=budget_policy(async_delegation_allowed=True),
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )

    assert packet_request.action_type == "async_delegation"
    assert packet_request.source_stage == "100P"
    assert packet_request.required_cost_preflight["request_id"] == task_request.request_id
    assert packet_request.required_cost_preflight["task_cost_request"]["task_class"] == "async_delegation"
    assert packet_request.action_payload["delegation_id"] == request.delegation_id
    assert packet_request.action_payload["selected_model_id"] == preflight.route_decision.selected_model_id


def test_valid_approval_binds_exact_preflight_and_allows_registration():
    request = delegation_request()
    task_request = task_cost_request()
    policy = budget_policy(async_delegation_allowed=True)
    preflight = evaluate_cost_preflight(request=task_request, budget_policy=policy)
    awaiting = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=policy,
        cost_preflight=preflight,
        occurred_at="2026-06-17T12:00:00Z",
    )
    _, approved_packet = create_and_approve_async_action_packet(
        request=request,
        task_request=task_request,
        policy=policy,
        preflight=preflight,
    )

    approved = bind_async_delegation_approval(
        authority_state=awaiting,
        approval_state=approved_packet,
        occurred_at="2026-06-17T14:00:00Z",
    )
    registered = register_async_delegation_handle(
        authority_state=approved,
        occurred_at="2026-06-17T14:05:00Z",
    )

    assert approved.packet.state == "approved_local"
    assert approved.packet.action_packet_id == approved_packet.packet.packet_id
    assert registered.packet.state == "registered"
    assert registered.handle is not None
    assert registered.handle.action_packet_id == approved_packet.packet.packet_id
    assert registered.handle.live_dispatch_authorized is False


def test_used_or_mismatched_approval_token_blocks_registration():
    request = delegation_request()
    task_request = task_cost_request()
    policy = budget_policy(async_delegation_allowed=True)
    preflight = evaluate_cost_preflight(request=task_request, budget_policy=policy)
    awaiting = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=policy,
        cost_preflight=preflight,
        occurred_at="2026-06-17T12:00:00Z",
    )
    _, approved_packet = create_and_approve_async_action_packet(
        request=request,
        task_request=task_request,
        policy=policy,
        preflight=preflight,
    )
    used_token = approved_packet.resume_token
    used_packet = apply_action_packet_decision(
        approval_state=approved_packet,
        decision=ActionPacketDecision(
            packet_id=approved_packet.packet.packet_id,
            packet_version=approved_packet.packet.packet_version,
            decision="resume",
            actor_id=approved_packet.packet.actor_id,
            actor_role=approved_packet.packet.actor_role,
            owner_id=approved_packet.packet.owner_id,
            robot_id=approved_packet.packet.robot_id,
            reason_code="resume_once",
            edit_payload=None,
            resume_token_id=used_token.token_id,
            occurred_at="2026-06-17T14:01:00Z",
        ),
    )

    blocked = bind_async_delegation_approval(
        authority_state=awaiting,
        approval_state=used_packet,
        occurred_at="2026-06-17T14:02:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code in {"blocked_approval_not_approved", "blocked_resume_token_already_used"}


def test_cancellation_and_expiry_are_local_only():
    request = delegation_request()
    task_request = task_cost_request()
    state = register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_request),
            occurred_at="2026-06-17T12:00:00Z",
        ),
        occurred_at="2026-06-17T12:05:00Z",
    )
    cancelled = cancel_async_delegation(authority_state=state, occurred_at="2026-06-17T12:06:00Z")
    expired = expire_async_delegation(authority_state=state, occurred_at="2026-06-17T12:07:00Z")

    assert cancelled.packet.state == "cancelled"
    assert cancelled.handle.status == "cancelled"
    assert expired.packet.state == "expired"
    assert expired.handle.status == "expired"
    assert cancelled.handle.execution_authorized is False


def test_completion_event_rejects_unknown_or_authority_expanding_payloads():
    request = delegation_request()
    task_request = task_cost_request()
    state = create_async_delegation_authority_state(
        request=request,
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        cost_preflight=synthetic_allow_preflight(task_request),
        occurred_at="2026-06-17T12:00:00Z",
    )
    unknown = record_async_delegation_completion(
        authority_state=state,
        event=AsyncDelegationCompletionEvent(
            event_id="unknown-event",
            handle_id="missing-handle",
            delegation_id=request.delegation_id,
            owner_id=request.owner_id,
            robot_id=request.robot_id,
            actor_id=request.actor_id,
            source_stage="simulated_import",
            original_request_evidence={},
            cost_preflight_evidence={},
            approval_evidence=None,
            completion_status="completed",
            completion_payload_summary={"result": "done"},
            reason_code="imported_record",
        ),
    )

    assert unknown.packet.state == "rejected"
    assert unknown.trace_records[-1].reason_code == "rejected_unknown_handle"

    registered = register_async_delegation_handle(authority_state=state, occurred_at="2026-06-17T12:05:00Z")
    expanding = record_async_delegation_completion(
        authority_state=registered,
        event=AsyncDelegationCompletionEvent(
            event_id="expanding-event",
            handle_id=registered.handle.handle_id,
            delegation_id=request.delegation_id,
            owner_id=request.owner_id,
            robot_id=request.robot_id,
            actor_id=request.actor_id,
            source_stage="simulated_import",
            original_request_evidence={},
            cost_preflight_evidence={},
            approval_evidence=None,
            completion_status="completed",
            completion_payload_summary={"external_effect": "send a live message"},
            reason_code="imported_record",
            external_effect_authorized=True,
        ),
    )

    assert expanding.packet.state == "rejected"
    assert expanding.trace_records[-1].reason_code == "rejected_authority_expansion_attempt"


def test_matching_completion_and_failure_events_are_local_data_only_records():
    request = delegation_request()
    task_request = task_cost_request()
    registered = register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_request),
            occurred_at="2026-06-17T12:00:00Z",
        ),
        occurred_at="2026-06-17T12:05:00Z",
    )
    completion = build_completion_event(
        authority_state=registered,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "work completed locally"},
        reason_code="completed_local_record",
    )
    completed = record_async_delegation_completion(authority_state=registered, event=completion)

    assert completed.packet.state == "completed"
    assert completed.completion_events[-1].completion_status == "completed"
    assert completed.completion_events[-1].execution_authorized is False

    registered_again = register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_request),
            occurred_at="2026-06-17T13:00:00Z",
        ),
        occurred_at="2026-06-17T13:05:00Z",
    )
    failure = build_completion_event(
        authority_state=registered_again,
        completion_status="failed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "work failed locally"},
        reason_code="failed_local_record",
    )
    failed = record_async_delegation_failure(authority_state=registered_again, event=failure)
    serialized = serialize_async_delegation_authority_state(failed)

    assert failed.packet.state == "failed"
    assert serialized["packet"]["live_dispatch_authorized"] is False
    assert serialized["completion_events"][-1]["provider_call_authorized"] is False


def test_103p_and_later_source_stage_remains_blocked():
    state = create_async_delegation_authority_state(
        request=delegation_request(source_stage="103P"),
        task_cost_request=task_cost_request(),
        budget_policy=budget_policy(),
        cost_preflight=synthetic_allow_preflight(task_cost_request()),
        occurred_at="2026-06-17T12:00:00Z",
    )

    assert state.packet.state == "blocked"
    assert state.trace_records[-1].reason_code == "blocked_unauthorized_source_stage"
