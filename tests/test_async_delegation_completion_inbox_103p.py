from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.action_packet_approval import ActionPacketDecision, create_action_packet, submit_action_packet_for_approval, apply_action_packet_decision
from app.async_delegation_authority import (
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    build_async_delegation_action_packet_request,
    build_completion_event,
    create_async_delegation_authority_state,
    register_async_delegation_handle,
)
from app.async_delegation_inbox import (
    ASYNC_DELEGATION_INBOX_STAGE,
    AsyncDelegationCompletionInbox,
    create_async_delegation_registry,
    replay_async_delegation_inbox,
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
INBOX_PATH = REPO_ROOT / "app/async_delegation_inbox.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def delegation_request(**overrides) -> AsyncDelegationRequest:
    values = {
        "delegation_id": "delegation-103p",
        "source_stage": "98P",
        "owner_id": "owner-103p",
        "robot_id": "robot-103p",
        "actor_id": "actor-103p",
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
        "required_routine_run_id": "routine-103p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-103p",
        "owner_id": "owner-103p",
        "robot_id": "robot-103p",
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
        "policy_id": "policy-103p",
        "owner_id": "owner-103p",
        "robot_id": "robot-103p",
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
        budget_policy_id="policy-103p",
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
        _, approved_packet = create_and_approve_async_action_packet(
            request=request,
            task_request=task_request,
            policy=policy,
            preflight=preflight,
        )
        return register_async_delegation_handle(
            authority_state=bind_async_delegation_approval(
                authority_state=awaiting,
                approval_state=approved_packet,
                occurred_at="2026-06-17T14:00:00Z",
            ),
            occurred_at="2026-06-17T14:05:00Z",
        )

    return register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_cost_request(),
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_cost_request()),
            occurred_at="2026-06-17T12:00:00Z",
        ),
        occurred_at="2026-06-17T12:05:00Z",
    )


def test_103p_valid_completion_event_is_accepted():
    state = registered_state()
    registry = create_async_delegation_registry(state)
    inbox = AsyncDelegationCompletionInbox()
    event = build_completion_event(
        authority_state=state,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "done"},
        reason_code="completed_local_record",
    )

    receipt = inbox.receive_event(event=event, registry=registry)

    assert receipt.record.status == "accepted"
    assert receipt.registry.authority_states[0].packet.state == "completed"
    assert receipt.registry.authority_states[0].handle.status == "completed"
    assert receipt.record.bound_completion_event is not None


def test_103p_valid_failure_event_is_accepted():
    state = registered_state()
    registry = create_async_delegation_registry(state)
    inbox = AsyncDelegationCompletionInbox()
    event = build_completion_event(
        authority_state=state,
        completion_status="failed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "failed"},
        reason_code="failed_local_record",
    )

    receipt = inbox.receive_event(event=event, registry=registry)

    assert receipt.record.status == "accepted"
    assert receipt.registry.authority_states[0].packet.state == "failed"
    assert receipt.registry.authority_states[0].handle.status == "failed"


def test_103p_unknown_handle_event_is_quarantined():
    state = registered_state()
    registry = create_async_delegation_registry(state)
    inbox = AsyncDelegationCompletionInbox()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        handle_id="missing-handle",
    )

    receipt = inbox.receive_event(event=event, registry=registry)

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_unknown_handle"
    assert receipt.registry.authority_states[0].packet.state == "registered"
    assert receipt.registry.authority_states[0].handle.status == "registered"


def test_103p_owner_mismatch_event_is_quarantined():
    state = registered_state()
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=replace(
            build_completion_event(
                authority_state=state,
                completion_status="completed",
                source_stage="simulated_import",
                completion_payload_summary={"summary": "done"},
                reason_code="completed_local_record",
            ),
            owner_id="other-owner",
        ),
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_owner_id_mismatch"
    assert receipt.registry.authority_states[0].handle.status == "registered"


def test_103p_robot_mismatch_event_is_quarantined():
    state = registered_state()
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=replace(
            build_completion_event(
                authority_state=state,
                completion_status="completed",
                source_stage="simulated_import",
                completion_payload_summary={"summary": "done"},
                reason_code="completed_local_record",
            ),
            robot_id="other-robot",
        ),
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_robot_id_mismatch"
    assert receipt.registry.authority_states[0].handle.status == "registered"


def test_103p_authority_expanding_event_is_quarantined():
    state = registered_state()
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=replace(
            build_completion_event(
                authority_state=state,
                completion_status="completed",
                source_stage="simulated_import",
                completion_payload_summary={"summary": "done"},
                reason_code="completed_local_record",
            ),
            authority_expanded=True,
        ),
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_authority_expansion_attempt"


def test_103p_external_effect_event_is_quarantined():
    state = registered_state()
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=replace(
            build_completion_event(
                authority_state=state,
                completion_status="completed",
                source_stage="simulated_import",
                completion_payload_summary={"external_effect": "send a live message"},
                reason_code="completed_local_record",
            ),
            external_effect_authorized=True,
        ),
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_authority_expansion_attempt"


def test_103p_invalid_event_does_not_poison_valid_handle():
    state = registered_state()
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=replace(
            build_completion_event(
                authority_state=state,
                completion_status="completed",
                source_stage="simulated_import",
                completion_payload_summary={"summary": "done"},
                reason_code="completed_local_record",
            ),
            owner_id="other-owner",
        ),
        registry=create_async_delegation_registry(state),
    )
    updated = receipt.registry.authority_states[0]

    assert updated.packet.state == "registered"
    assert updated.handle.status == "registered"
    assert updated.trace_records[-1].reason_code == "rejected_owner_id_mismatch"


def test_103p_duplicate_valid_event_is_idempotent():
    state = registered_state()
    inbox = AsyncDelegationCompletionInbox()
    registry = create_async_delegation_registry(state)
    event = build_completion_event(
        authority_state=state,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "done"},
        reason_code="completed_local_record",
    )

    first = inbox.receive_event(event=event, registry=registry)
    second = first.inbox.receive_event(event=event, registry=first.registry)
    third = second.inbox.receive_event(event=event, registry=second.registry)

    assert first.record.status == "accepted"
    assert second.record.status == "duplicate"
    assert third.record.status == "duplicate"
    assert second.registry.authority_states[0].packet.state == "completed"
    assert len(second.inbox.list_records()) == 2
    assert len(third.inbox.list_records()) == 2


def test_103p_duplicate_invalid_event_is_idempotent():
    state = registered_state()
    inbox = AsyncDelegationCompletionInbox()
    registry = create_async_delegation_registry(state)
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        owner_id="other-owner",
    )

    first = inbox.receive_event(event=event, registry=registry)
    second = first.inbox.receive_event(event=event, registry=first.registry)
    third = second.inbox.receive_event(event=event, registry=second.registry)

    assert first.record.status == "quarantined"
    assert second.record.status == "duplicate"
    assert third.record.status == "duplicate"
    assert first.registry.authority_states[0].packet.state == "registered"
    assert len(second.inbox.list_records()) == 2
    assert len(third.inbox.list_records()) == 2


def test_103p_missing_100p_lineage_blocks_acceptance():
    state = registered_state()
    corrupted = replace(
        state,
        packet=replace(state.packet, cost_preflight_evidence=None),
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        registry=create_async_delegation_registry(corrupted),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_missing_cost_preflight_evidence"


def test_103p_completion_event_creation_rejects_missing_100p_lineage():
    state = registered_state()
    corrupted = replace(
        state,
        handle=replace(state.handle, cost_preflight_evidence=None),
    )

    try:
        build_completion_event(
            authority_state=corrupted,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        )
    except ValueError as exc:
        assert "100P cost preflight evidence" in str(exc)
    else:
        raise AssertionError("Expected build_completion_event to reject missing lineage.")


def test_103p_generic_cost_confirmation_does_not_bind_async_authority():
    state = registered_state(require_approval=True)
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        approval_evidence={"action_type": "cost_confirmation"},
    )

    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_approval_evidence_mismatch"


def test_103p_route_model_mismatch_blocks_acceptance():
    state = registered_state()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        cost_preflight_evidence={
            **state.handle.cost_preflight_evidence,
            "route_decision": {
                **state.handle.cost_preflight_evidence["route_decision"],
                "selected_model_id": "other-model",
            },
        },
    )

    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_cost_preflight_evidence_mismatch"


def test_103p_cost_preflight_request_id_mismatch_blocks_acceptance():
    state = registered_state()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        cost_preflight_evidence={
            **state.handle.cost_preflight_evidence,
            "request_id": "other-request",
        },
    )

    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_cost_preflight_evidence_mismatch"


def test_103p_request_evidence_mismatch_blocks_acceptance():
    state = registered_state()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        original_request_evidence={
            **state.handle.original_request_evidence,
            "request_payload": {"summary": "tampered"},
        },
    )

    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )

    assert receipt.record.status == "quarantined"
    assert receipt.record.reason == "rejected_request_evidence_mismatch"


def test_103p_replay_is_deterministic():
    state = registered_state()
    valid = build_completion_event(
        authority_state=state,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "done"},
        reason_code="completed_local_record",
    )
    invalid = replace(valid, event_id="owner-mismatch-event", owner_id="other-owner")
    events = (invalid, invalid, valid, valid)

    first = replay_async_delegation_inbox(events=events, clean_registry=create_async_delegation_registry(registered_state()))
    second = replay_async_delegation_inbox(events=events, clean_registry=create_async_delegation_registry(registered_state()))

    assert first.registry.authority_states[0].packet.state == second.registry.authority_states[0].packet.state
    assert first.inbox.list_records() == second.inbox.list_records()


def test_103p_preserves_100p_101p_102p_evidence():
    state = registered_state(require_approval=True)
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "done"},
            reason_code="completed_local_record",
        ),
        registry=create_async_delegation_registry(state),
    )

    event = receipt.record.bound_completion_event
    assert event is not None
    assert event["original_request_evidence"] == state.handle.original_request_evidence
    assert event["cost_preflight_evidence"] == state.handle.cost_preflight_evidence
    assert event["approval_evidence"] == state.handle.approval_evidence
    assert event["cost_preflight_evidence"]["estimated_cost_usd"] == state.handle.cost_preflight_evidence["estimated_cost_usd"]
    assert event["cost_preflight_evidence"]["estimated_cost_usd"] > 0


def test_103p_remains_local_only_non_dispatching_non_executing():
    inbox = AsyncDelegationCompletionInbox()
    text = INBOX_PATH.read_text()

    assert ASYNC_DELEGATION_INBOX_STAGE == "103P"
    assert inbox.local_only is True
    assert inbox.non_dispatching is True
    assert inbox.execution_authorized is False
    for forbidden in [
        "delegate_task",
        "asyncio.create_task",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "send_message",
        "subprocess",
    ]:
        assert forbidden not in text


def test_103p_104p_plus_remains_unauthorized():
    roadmap = ROADMAP_PATH.read_text()

    assert (
        "108P and later remain unauthorized" in roadmap
        or "108P+ remains unauthorized" in roadmap
    )
