from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from app.action_packet_approval import (
    ActionPacketApprovalState,
    ActionPacketRequest,
)
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    TaskCostRequest,
    serialize_budget_policy,
    serialize_cost_preflight_result,
    serialize_task_cost_request,
)


ASYNC_DELEGATION_STAGE = "102P"

AsyncDelegationState = Literal[
    "proposed",
    "preflight_blocked",
    "awaiting_approval",
    "approved_local",
    "registered",
    "cancelled",
    "expired",
    "completed",
    "failed",
    "rejected",
    "blocked",
]
AsyncDelegationDecision = Literal[
    "allow_local_register",
    "require_approval",
    "block",
    "cancel",
    "expire",
    "record_completion",
    "record_failure",
]

DELEGATION_STATES = frozenset(
    {
        "proposed",
        "preflight_blocked",
        "awaiting_approval",
        "approved_local",
        "registered",
        "cancelled",
        "expired",
        "completed",
        "failed",
        "rejected",
        "blocked",
    }
)
DELEGATION_DECISIONS = frozenset(
    {
        "allow_local_register",
        "require_approval",
        "block",
        "cancel",
        "expire",
        "record_completion",
        "record_failure",
    }
)
COMPLETION_STATUSES = frozenset({"completed", "failed", "cancelled", "expired", "rejected", "blocked"})
TERMINAL_STATES = frozenset({"cancelled", "expired", "completed", "failed", "rejected", "blocked", "preflight_blocked"})
APPROVAL_REQUIRED_COST_DECISIONS = frozenset({"require_confirmation"})
ALLOWABLE_COST_DECISIONS = frozenset({"allow", "downgrade"})


@dataclass(frozen=True, slots=True)
class AsyncDelegationRequest:
    delegation_id: str
    source_stage: str
    owner_id: str
    robot_id: str
    actor_id: str | None
    actor_role: str
    task_class: str
    requested_capability: str
    requested_route_mode: str
    request_payload: dict[str, object]
    required_policy_trace: tuple[str, ...]
    required_memory_projection_request_id: str | None
    required_routine_run_id: str | None
    expires_at: str | None
    authority_expansion_requested: bool = False
    live_dispatch_requested: bool = False


@dataclass(frozen=True, slots=True)
class AsyncDelegationPacket:
    delegation_id: str
    packet_version: int
    state: str
    decision: str
    source_stage: str
    owner_id: str
    robot_id: str
    actor_id: str | None
    actor_role: str
    task_class: str
    request_snapshot: dict[str, object]
    required_policy_trace: tuple[str, ...]
    cost_preflight_evidence: dict[str, object] | None
    approval_evidence: dict[str, object] | None
    cost_preflight_request_id: str | None
    cost_preflight_decision: str | None
    selected_provider_id: str | None
    selected_model_id: str | None
    action_packet_id: str | None
    approval_resume_token_id: str | None
    expires_at: str | None
    non_dispatching: bool = True
    authority_expanded: bool = False
    external_effect_authorized: bool = False
    provider_call_authorized: bool = False
    execution_authorized: bool = False
    live_dispatch_authorized: bool = False


@dataclass(frozen=True, slots=True)
class AsyncDelegationHandle:
    handle_id: str
    delegation_id: str
    owner_id: str
    robot_id: str
    actor_id: str | None
    actor_role: str
    task_class: str
    packet_version: int
    packet_hash: str
    original_request_evidence: dict[str, object]
    cost_preflight_evidence: dict[str, object]
    approval_evidence: dict[str, object] | None
    cost_preflight_request_id: str
    cost_preflight_decision: str
    selected_provider_id: str | None
    selected_model_id: str | None
    action_packet_id: str | None
    approval_resume_token_id: str | None
    registered_at: str
    expires_at: str | None
    status: str
    dispatch_authorized: bool = False
    authority_expanded: bool = False
    external_effect_authorized: bool = False
    provider_call_authorized: bool = False
    execution_authorized: bool = False
    live_dispatch_authorized: bool = False


@dataclass(frozen=True, slots=True)
class AsyncDelegationCompletionEvent:
    event_id: str
    handle_id: str
    delegation_id: str
    owner_id: str
    robot_id: str
    actor_id: str | None
    source_stage: str
    original_request_evidence: dict[str, object]
    cost_preflight_evidence: dict[str, object]
    approval_evidence: dict[str, object] | None
    completion_status: str
    completion_payload_summary: dict[str, object]
    reason_code: str
    authority_expanded: bool = False
    memory_access_expanded: bool = False
    tool_authority_granted: bool = False
    provider_call_authorized: bool = False
    external_effect_authorized: bool = False
    execution_authorized: bool = False
    live_dispatch_authorized: bool = False


@dataclass(frozen=True, slots=True)
class AsyncDelegationTraceRecord:
    trace_id: str
    delegation_id: str
    handle_id: str | None
    previous_state: str | None
    next_state: str
    decision: str
    owner_id: str
    robot_id: str
    actor_id: str | None
    actor_role: str
    task_class: str
    source_stage: str
    cost_preflight_decision: str | None
    action_packet_id: str | None
    reason_code: str
    authority_expanded: bool = False
    external_effect_authorized: bool = False
    provider_call_authorized: bool = False
    execution_authorized: bool = False
    live_dispatch_authorized: bool = False


@dataclass(frozen=True, slots=True)
class AsyncDelegationAuthorityState:
    stage: str
    packet: AsyncDelegationPacket
    handle: AsyncDelegationHandle | None
    completion_events: tuple[AsyncDelegationCompletionEvent, ...]
    trace_records: tuple[AsyncDelegationTraceRecord, ...]
    data_only: bool = True
    local_only: bool = True


def create_async_delegation_authority_state(
    *,
    request: AsyncDelegationRequest,
    task_cost_request: TaskCostRequest | None,
    budget_policy: BudgetPolicy | None,
    cost_preflight: CostPreflightResult | None,
    occurred_at: str,
) -> AsyncDelegationAuthorityState:
    block_reason = _request_block_reason(request)
    if block_reason is not None:
        packet = _build_packet(
            request=request,
            state="blocked",
            decision="block",
            cost_preflight=cost_preflight,
            action_packet_id=None,
            approval_resume_token_id=None,
        )
        return _append_transition(
            AsyncDelegationAuthorityState(
                stage=ASYNC_DELEGATION_STAGE,
                packet=packet,
                handle=None,
                completion_events=(),
                trace_records=(),
            ),
            previous_state=None,
            next_state="blocked",
            decision="block",
            reason_code=block_reason,
            occurred_at=occurred_at,
        )

    preflight_state, reason_code = _preflight_transition_state(
        request=request,
        task_cost_request=task_cost_request,
        budget_policy=budget_policy,
        cost_preflight=cost_preflight,
    )
    if preflight_state is not None:
        packet = _build_packet(
            request=request,
            state=preflight_state,
            decision="block" if preflight_state != "awaiting_approval" else "require_approval",
            cost_preflight=cost_preflight,
            action_packet_id=None,
            approval_resume_token_id=None,
        )
        return _append_transition(
            AsyncDelegationAuthorityState(
                stage=ASYNC_DELEGATION_STAGE,
                packet=packet,
                handle=None,
                completion_events=(),
                trace_records=(),
            ),
            previous_state=None,
            next_state=preflight_state,
            decision=packet.decision,
            reason_code=reason_code,
            occurred_at=occurred_at,
        )

    packet = _build_packet(
        request=request,
        state="approved_local",
        decision="allow_local_register",
        cost_preflight=cost_preflight,
        action_packet_id=None,
        approval_resume_token_id=None,
    )
    return _append_transition(
        AsyncDelegationAuthorityState(
            stage=ASYNC_DELEGATION_STAGE,
            packet=packet,
            handle=None,
            completion_events=(),
            trace_records=(),
        ),
        previous_state=None,
        next_state="approved_local",
        decision="allow_local_register",
        reason_code="preflight_allowed_local_registration",
        occurred_at=occurred_at,
    )


def build_async_delegation_action_packet_request(
    *,
    request: AsyncDelegationRequest,
    cost_preflight: CostPreflightResult,
    task_cost_request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    actor_id: str,
    actor_role: str,
    review_expires_at: str | None = None,
) -> ActionPacketRequest:
    route = None if cost_preflight.route_decision is None else cost_preflight.route_decision.selected_model_id
    return ActionPacketRequest(
        request_id=request.delegation_id,
        source_stage="100P",
        action_type="async_delegation",
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        actor_id=actor_id,
        actor_role=actor_role,
        requested_by_actor_id=request.owner_id,
        requested_by_actor_role="owner_admin",
        required_policy_trace=tuple(request.required_policy_trace),
        required_cost_preflight={
            "request_id": cost_preflight.request_id,
            "owner_id": request.owner_id,
            "robot_id": request.robot_id,
            "decision": cost_preflight.decision,
            "task_cost_request": serialize_task_cost_request(task_cost_request),
            "budget_policy": serialize_budget_policy(budget_policy),
            "route_decision": None
            if cost_preflight.route_decision is None
            else {
                "selected_provider_id": cost_preflight.route_decision.selected_provider_id,
                "selected_model_id": cost_preflight.route_decision.selected_model_id,
                "selected_capability_tier": cost_preflight.route_decision.selected_capability_tier,
                "selected_trust_level": cost_preflight.route_decision.selected_trust_level,
                "candidate_models_considered": list(cost_preflight.route_decision.candidate_models_considered),
                "rejected_candidates": list(cost_preflight.route_decision.rejected_candidates),
                "downgrade_from_model_id": cost_preflight.route_decision.downgrade_from_model_id,
                "decision_reason": cost_preflight.route_decision.decision_reason,
            },
            "selected_model_id": route,
            "estimated_cost_usd": cost_preflight.estimated_cost_usd,
            "trace_reason_code": cost_preflight.trace[-1].reason_code,
            "authority_flags": {
                "authority_expanded": False,
                "external_effect_authorized": False,
                "provider_call_authorized": False,
                "execution_authorized": False,
            },
        },
        required_memory_projection=None,
        required_routine_context=None
        if request.required_routine_run_id is None
        else {
            "run_id": request.required_routine_run_id,
            "owner_id": request.owner_id,
            "robot_id": request.robot_id,
            "preflight_policy_chain_routed": True,
        },
        action_payload={
            "delegation_id": request.delegation_id,
            "task_class": request.task_class,
            "source_stage": request.source_stage,
            "requested_capability": request.requested_capability,
            "requested_route_mode": request.requested_route_mode,
            "request_payload": _dict_snapshot(request.request_payload),
            "selected_model_id": route,
            "cost_preflight_required": True,
        },
        review_expires_at=review_expires_at or request.expires_at,
        resume_scope="exact_preflight",
    )


def bind_async_delegation_approval(
    *,
    authority_state: AsyncDelegationAuthorityState,
    approval_state: ActionPacketApprovalState,
    occurred_at: str,
) -> AsyncDelegationAuthorityState:
    packet = authority_state.packet
    if packet.state not in DELEGATION_STATES:
        return _blocked_transition(authority_state=authority_state, occurred_at=occurred_at, reason_code="blocked_unknown_delegation_state")
    if packet.state != "awaiting_approval":
        return _blocked_transition(
            authority_state=authority_state,
            occurred_at=occurred_at,
            reason_code="blocked_approval_binding_requires_awaiting_approval",
        )
    approval_reason = _approval_block_reason(packet=packet, approval_state=approval_state, occurred_at=occurred_at)
    if approval_reason is not None:
        return _blocked_transition(authority_state=authority_state, occurred_at=occurred_at, reason_code=approval_reason)

    approved_packet = replace(
        packet,
        state="approved_local",
        decision="allow_local_register",
        action_packet_id=approval_state.packet.packet_id,
        approval_resume_token_id=approval_state.resume_token.token_id,
        approval_evidence={
            "action_type": approval_state.packet.action_type,
            "action_packet_id": approval_state.packet.packet_id,
            "packet_version": approval_state.packet.packet_version,
            "owner_id": approval_state.packet.owner_id,
            "robot_id": approval_state.packet.robot_id,
            "actor_id": approval_state.packet.actor_id,
            "actor_role": approval_state.packet.actor_role,
            "delegation_id": approval_state.packet.action_payload.get("delegation_id"),
            "task_class": approval_state.packet.action_payload.get("task_class"),
            "source_stage": approval_state.packet.action_payload.get("source_stage"),
            "requested_capability": approval_state.packet.action_payload.get("requested_capability"),
            "requested_route_mode": approval_state.packet.action_payload.get("requested_route_mode"),
            "request_payload": _dict_snapshot(approval_state.packet.action_payload.get("request_payload")),
            "selected_model_id": approval_state.packet.required_selected_model_id,
            "cost_preflight_request_id": approval_state.packet.required_cost_preflight_request_id,
            "cost_preflight_decision": approval_state.packet.required_cost_preflight_decision,
            "required_cost_preflight": _dict_snapshot(approval_state.packet.required_cost_preflight),
            "approval_resume_token_id": approval_state.resume_token.token_id,
        },
    )
    return _append_transition(
        replace(authority_state, packet=approved_packet),
        previous_state=packet.state,
        next_state="approved_local",
        decision="allow_local_register",
        reason_code="approval_bound_exact_preflight",
        occurred_at=occurred_at,
    )


def register_async_delegation_handle(
    *,
    authority_state: AsyncDelegationAuthorityState,
    occurred_at: str,
) -> AsyncDelegationAuthorityState:
    packet = authority_state.packet
    if packet.state not in DELEGATION_STATES:
        return _blocked_transition(authority_state=authority_state, occurred_at=occurred_at, reason_code="blocked_unknown_delegation_state")
    if packet.state != "approved_local":
        return _blocked_transition(
            authority_state=authority_state,
            occurred_at=occurred_at,
            reason_code="blocked_registration_requires_approved_local_state",
        )
    if packet.cost_preflight_request_id is None or packet.cost_preflight_decision is None:
        return _blocked_transition(authority_state=authority_state, occurred_at=occurred_at, reason_code="blocked_missing_cost_preflight")
    if packet.approval_resume_token_id is None and packet.action_packet_id is not None:
        return _blocked_transition(authority_state=authority_state, occurred_at=occurred_at, reason_code="blocked_missing_approval_resume_token")

    handle = AsyncDelegationHandle(
        handle_id=_stable_id("async_handle", packet.delegation_id, packet.packet_version, occurred_at),
        delegation_id=packet.delegation_id,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        actor_id=packet.actor_id,
        actor_role=packet.actor_role,
        task_class=packet.task_class,
        packet_version=packet.packet_version,
        packet_hash=_stable_id("async_packet_hash", packet.delegation_id, packet.packet_version, packet.selected_model_id, packet.cost_preflight_request_id),
        original_request_evidence=_dict_snapshot(packet.request_snapshot) or {},
        cost_preflight_evidence=_dict_snapshot(packet.cost_preflight_evidence) or {},
        approval_evidence=None if packet.approval_evidence is None else _dict_snapshot(packet.approval_evidence),
        cost_preflight_request_id=packet.cost_preflight_request_id,
        cost_preflight_decision=packet.cost_preflight_decision,
        selected_provider_id=packet.selected_provider_id,
        selected_model_id=packet.selected_model_id,
        action_packet_id=packet.action_packet_id,
        approval_resume_token_id=packet.approval_resume_token_id,
        registered_at=occurred_at,
        expires_at=packet.expires_at,
        status="registered",
    )
    registered_packet = replace(packet, state="registered")
    return _append_transition(
        replace(authority_state, packet=registered_packet, handle=handle),
        previous_state=packet.state,
        next_state="registered",
        decision="allow_local_register",
        reason_code="registered_local_non_dispatching_handle",
        occurred_at=occurred_at,
    )


def cancel_async_delegation(
    *,
    authority_state: AsyncDelegationAuthorityState,
    occurred_at: str,
    reason_code: str = "cancelled_local_only",
) -> AsyncDelegationAuthorityState:
    if authority_state.packet.state in TERMINAL_STATES:
        return _blocked_transition(
            authority_state=authority_state,
            occurred_at=occurred_at,
            reason_code=f"blocked_{authority_state.packet.state}_delegation_cannot_cancel",
        )
    state = _transition_packet_and_handle(authority_state=authority_state, next_state="cancelled")
    return _append_transition(
        state,
        previous_state=authority_state.packet.state,
        next_state="cancelled",
        decision="cancel",
        reason_code=reason_code,
        occurred_at=occurred_at,
    )


def expire_async_delegation(
    *,
    authority_state: AsyncDelegationAuthorityState,
    occurred_at: str,
    reason_code: str = "expired_local_only",
) -> AsyncDelegationAuthorityState:
    if authority_state.packet.state in TERMINAL_STATES:
        return _blocked_transition(
            authority_state=authority_state,
            occurred_at=occurred_at,
            reason_code=f"blocked_{authority_state.packet.state}_delegation_cannot_expire",
        )
    state = _transition_packet_and_handle(authority_state=authority_state, next_state="expired")
    return _append_transition(
        state,
        previous_state=authority_state.packet.state,
        next_state="expired",
        decision="expire",
        reason_code=reason_code,
        occurred_at=occurred_at,
    )


def record_async_delegation_completion(
    *,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
) -> AsyncDelegationAuthorityState:
    return _record_terminal_event(authority_state=authority_state, event=event, next_state="completed", decision="record_completion")


def record_async_delegation_failure(
    *,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
) -> AsyncDelegationAuthorityState:
    return _record_terminal_event(authority_state=authority_state, event=event, next_state="failed", decision="record_failure")


def serialize_async_delegation_authority_state(authority_state: AsyncDelegationAuthorityState) -> dict[str, object]:
    return {
        "stage": authority_state.stage,
        "packet": {
            "delegation_id": authority_state.packet.delegation_id,
            "packet_version": authority_state.packet.packet_version,
            "state": authority_state.packet.state,
            "decision": authority_state.packet.decision,
            "source_stage": authority_state.packet.source_stage,
            "owner_id": authority_state.packet.owner_id,
            "robot_id": authority_state.packet.robot_id,
            "actor_id": authority_state.packet.actor_id,
            "actor_role": authority_state.packet.actor_role,
            "task_class": authority_state.packet.task_class,
            "request_snapshot": _dict_snapshot(authority_state.packet.request_snapshot),
            "required_policy_trace": list(authority_state.packet.required_policy_trace),
            "cost_preflight_evidence": _dict_snapshot(authority_state.packet.cost_preflight_evidence),
            "approval_evidence": _dict_snapshot(authority_state.packet.approval_evidence),
            "cost_preflight_request_id": authority_state.packet.cost_preflight_request_id,
            "cost_preflight_decision": authority_state.packet.cost_preflight_decision,
            "selected_provider_id": authority_state.packet.selected_provider_id,
            "selected_model_id": authority_state.packet.selected_model_id,
            "action_packet_id": authority_state.packet.action_packet_id,
            "approval_resume_token_id": authority_state.packet.approval_resume_token_id,
            "expires_at": authority_state.packet.expires_at,
            "non_dispatching": authority_state.packet.non_dispatching,
            "authority_expanded": authority_state.packet.authority_expanded,
            "external_effect_authorized": authority_state.packet.external_effect_authorized,
            "provider_call_authorized": authority_state.packet.provider_call_authorized,
            "execution_authorized": authority_state.packet.execution_authorized,
            "live_dispatch_authorized": authority_state.packet.live_dispatch_authorized,
        },
        "handle": None
        if authority_state.handle is None
        else {
            "handle_id": authority_state.handle.handle_id,
            "delegation_id": authority_state.handle.delegation_id,
            "owner_id": authority_state.handle.owner_id,
            "robot_id": authority_state.handle.robot_id,
            "actor_id": authority_state.handle.actor_id,
            "actor_role": authority_state.handle.actor_role,
            "task_class": authority_state.handle.task_class,
            "packet_version": authority_state.handle.packet_version,
            "packet_hash": authority_state.handle.packet_hash,
            "original_request_evidence": _dict_snapshot(authority_state.handle.original_request_evidence),
            "cost_preflight_evidence": _dict_snapshot(authority_state.handle.cost_preflight_evidence),
            "approval_evidence": None if authority_state.handle.approval_evidence is None else _dict_snapshot(authority_state.handle.approval_evidence),
            "cost_preflight_request_id": authority_state.handle.cost_preflight_request_id,
            "cost_preflight_decision": authority_state.handle.cost_preflight_decision,
            "selected_provider_id": authority_state.handle.selected_provider_id,
            "selected_model_id": authority_state.handle.selected_model_id,
            "action_packet_id": authority_state.handle.action_packet_id,
            "approval_resume_token_id": authority_state.handle.approval_resume_token_id,
            "registered_at": authority_state.handle.registered_at,
            "expires_at": authority_state.handle.expires_at,
            "status": authority_state.handle.status,
            "dispatch_authorized": authority_state.handle.dispatch_authorized,
            "authority_expanded": authority_state.handle.authority_expanded,
            "external_effect_authorized": authority_state.handle.external_effect_authorized,
            "provider_call_authorized": authority_state.handle.provider_call_authorized,
            "execution_authorized": authority_state.handle.execution_authorized,
            "live_dispatch_authorized": authority_state.handle.live_dispatch_authorized,
        },
        "completion_events": [
            {
                "event_id": event.event_id,
                "handle_id": event.handle_id,
                "delegation_id": event.delegation_id,
                "owner_id": event.owner_id,
                "robot_id": event.robot_id,
                "actor_id": event.actor_id,
                "source_stage": event.source_stage,
                "original_request_evidence": _dict_snapshot(event.original_request_evidence),
                "cost_preflight_evidence": _dict_snapshot(event.cost_preflight_evidence),
                "approval_evidence": None if event.approval_evidence is None else _dict_snapshot(event.approval_evidence),
                "completion_status": event.completion_status,
                "completion_payload_summary": _dict_snapshot(event.completion_payload_summary),
                "reason_code": event.reason_code,
                "authority_expanded": event.authority_expanded,
                "memory_access_expanded": event.memory_access_expanded,
                "tool_authority_granted": event.tool_authority_granted,
                "provider_call_authorized": event.provider_call_authorized,
                "external_effect_authorized": event.external_effect_authorized,
                "execution_authorized": event.execution_authorized,
                "live_dispatch_authorized": event.live_dispatch_authorized,
            }
            for event in authority_state.completion_events
        ],
        "trace_records": [
            {
                "trace_id": trace.trace_id,
                "delegation_id": trace.delegation_id,
                "handle_id": trace.handle_id,
                "previous_state": trace.previous_state,
                "next_state": trace.next_state,
                "decision": trace.decision,
                "owner_id": trace.owner_id,
                "robot_id": trace.robot_id,
                "actor_id": trace.actor_id,
                "actor_role": trace.actor_role,
                "task_class": trace.task_class,
                "source_stage": trace.source_stage,
                "cost_preflight_decision": trace.cost_preflight_decision,
                "action_packet_id": trace.action_packet_id,
                "reason_code": trace.reason_code,
                "authority_expanded": trace.authority_expanded,
                "external_effect_authorized": trace.external_effect_authorized,
                "provider_call_authorized": trace.provider_call_authorized,
                "execution_authorized": trace.execution_authorized,
                "live_dispatch_authorized": trace.live_dispatch_authorized,
            }
            for trace in authority_state.trace_records
        ],
    }


def _record_terminal_event(
    *,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
    next_state: str,
    decision: str,
) -> AsyncDelegationAuthorityState:
    packet = authority_state.packet
    handle = authority_state.handle
    if packet.state not in DELEGATION_STATES:
        return _blocked_transition(authority_state=authority_state, occurred_at=event.source_stage, reason_code="blocked_unknown_delegation_state")
    event_reason = _completion_event_block_reason(authority_state=authority_state, event=event, expected_status=next_state)
    if event_reason is not None:
        rejected_state = replace(authority_state, completion_events=authority_state.completion_events + (event,))
        return _append_transition(
            rejected_state,
            previous_state=packet.state,
            next_state=packet.state,
            decision="block",
            reason_code=event_reason,
            occurred_at=event.source_stage,
        )
    updated_state = _transition_packet_and_handle(authority_state=authority_state, next_state=next_state)
    updated_state = replace(updated_state, completion_events=updated_state.completion_events + (event,))
    return _append_transition(
        updated_state,
        previous_state=packet.state,
        next_state=next_state,
        decision=decision,
        reason_code=event.reason_code,
        occurred_at=event.source_stage,
    )


def _request_block_reason(request: AsyncDelegationRequest) -> str | None:
    if not request.owner_id:
        return "blocked_missing_owner_id"
    if not request.robot_id:
        return "blocked_missing_robot_id"
    if request.task_class != "async_delegation":
        return "blocked_task_class_not_async_delegation"
    if request.authority_expansion_requested:
        return "blocked_authority_expansion_attempt"
    if request.live_dispatch_requested:
        return "blocked_live_dispatch_request"
    if not request.required_policy_trace:
        return "blocked_missing_required_policy_trace"
    if _source_stage_unauthorized(request.source_stage):
        return "blocked_unauthorized_source_stage"
    return None


def _preflight_transition_state(
    *,
    request: AsyncDelegationRequest,
    task_cost_request: TaskCostRequest | None,
    budget_policy: BudgetPolicy | None,
    cost_preflight: CostPreflightResult | None,
) -> tuple[str | None, str]:
    if cost_preflight is None or task_cost_request is None:
        return ("preflight_blocked", "blocked_missing_cost_preflight")
    if task_cost_request.request_id != cost_preflight.request_id:
        return ("preflight_blocked", "blocked_cost_preflight_request_id_mismatch")
    if task_cost_request.owner_id != request.owner_id:
        return ("preflight_blocked", "blocked_owner_id_mismatch")
    if task_cost_request.robot_id != request.robot_id:
        return ("preflight_blocked", "blocked_robot_id_mismatch")
    if task_cost_request.task_class != "async_delegation":
        return ("preflight_blocked", "blocked_cost_preflight_task_class_mismatch")
    if budget_policy is not None:
        if budget_policy.owner_id != request.owner_id:
            return ("preflight_blocked", "blocked_budget_policy_owner_id_mismatch")
        if budget_policy.robot_id != request.robot_id:
            return ("preflight_blocked", "blocked_budget_policy_robot_id_mismatch")
        if not budget_policy.async_delegation_allowed:
            return ("preflight_blocked", "blocked_async_delegation_disabled_by_policy")
    if cost_preflight.decision == "block":
        return ("preflight_blocked", cost_preflight.trace[-1].reason_code)
    if cost_preflight.decision in APPROVAL_REQUIRED_COST_DECISIONS:
        return ("awaiting_approval", "approval_required_for_async_delegation")
    if cost_preflight.decision in ALLOWABLE_COST_DECISIONS:
        return (None, "preflight_allowed_local_registration")
    return ("preflight_blocked", "blocked_unknown_cost_preflight_decision")


def _approval_block_reason(
    *,
    packet: AsyncDelegationPacket,
    approval_state: ActionPacketApprovalState,
    occurred_at: str,
) -> str | None:
    if approval_state.packet.state != "approved":
        return "blocked_approval_not_approved"
    if approval_state.resume_token is None:
        return "blocked_missing_approval_resume_token"
    token = approval_state.resume_token
    if token.used:
        return "blocked_resume_token_already_used"
    if token.expires_at is not None and occurred_at > token.expires_at:
        return "blocked_resume_token_expired"
    if approval_state.packet.owner_id != packet.owner_id:
        return "blocked_owner_id_mismatch"
    if approval_state.packet.robot_id != packet.robot_id:
        return "blocked_robot_id_mismatch"
    if packet.actor_id is not None and approval_state.packet.actor_id != packet.actor_id:
        return "blocked_actor_id_mismatch"
    if approval_state.packet.action_type != "async_delegation":
        return "blocked_approval_action_type_mismatch"
    if packet.cost_preflight_evidence is None:
        return "blocked_missing_cost_preflight_evidence"
    if approval_state.packet.required_cost_preflight_request_id != packet.cost_preflight_request_id:
        return "blocked_cost_preflight_request_id_mismatch"
    if approval_state.packet.required_cost_preflight_decision != packet.cost_preflight_decision:
        return "blocked_101p_approval_mismatch"
    if approval_state.packet.required_selected_model_id != packet.selected_model_id:
        return "blocked_selected_route_mismatch"
    snapshot = approval_state.packet.required_cost_preflight or {}
    if not snapshot:
        return "blocked_missing_cost_preflight_evidence"
    task_snapshot = snapshot.get("task_cost_request")
    if not isinstance(task_snapshot, dict):
        return "blocked_missing_async_delegation_task_cost_request"
    if str(task_snapshot.get("task_class")) != packet.task_class:
        return "blocked_task_class_mismatch"
    if str(task_snapshot.get("owner_id")) != packet.owner_id:
        return "blocked_owner_id_mismatch"
    if str(task_snapshot.get("robot_id")) != packet.robot_id:
        return "blocked_robot_id_mismatch"
    budget_snapshot = snapshot.get("budget_policy")
    if not isinstance(budget_snapshot, dict):
        return "blocked_missing_async_delegation_budget_policy"
    if str(budget_snapshot.get("owner_id")) != packet.owner_id:
        return "blocked_owner_id_mismatch"
    if str(budget_snapshot.get("robot_id")) != packet.robot_id:
        return "blocked_robot_id_mismatch"
    if budget_snapshot.get("async_delegation_allowed") is not True:
        return "blocked_async_delegation_disabled_by_policy"
    route_snapshot = snapshot.get("route_decision")
    if packet.selected_model_id is not None:
        if not isinstance(route_snapshot, dict):
            return "blocked_selected_route_mismatch"
        if str(route_snapshot.get("selected_model_id")) != packet.selected_model_id:
            return "blocked_selected_route_mismatch"
    payload = approval_state.packet.action_payload
    if str(payload.get("delegation_id")) != packet.delegation_id:
        return "blocked_delegation_id_mismatch"
    if str(payload.get("task_class")) != packet.task_class:
        return "blocked_task_class_mismatch"
    if str(payload.get("source_stage")) != packet.source_stage:
        return "blocked_source_stage_mismatch"
    if str(payload.get("requested_capability")) != str(packet.request_snapshot.get("requested_capability")):
        return "blocked_request_payload_mismatch"
    if str(payload.get("requested_route_mode")) != str(packet.request_snapshot.get("requested_route_mode")):
        return "blocked_request_payload_mismatch"
    if _dict_snapshot(payload.get("request_payload")) != _dict_snapshot(packet.request_snapshot.get("request_payload")):
        return "blocked_request_payload_mismatch"
    return None


def _completion_event_block_reason(
    *,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
    expected_status: str,
) -> str | None:
    handle = authority_state.handle
    packet = authority_state.packet
    if handle is None:
        return "rejected_unknown_handle"
    if event.completion_status != expected_status:
        return "rejected_completion_status_mismatch"
    if event.handle_id != handle.handle_id:
        return "rejected_unknown_handle"
    if event.delegation_id != packet.delegation_id:
        return "rejected_delegation_id_mismatch"
    if event.owner_id != packet.owner_id:
        return "rejected_owner_id_mismatch"
    if event.robot_id != packet.robot_id:
        return "rejected_robot_id_mismatch"
    if packet.actor_id is not None and event.actor_id != packet.actor_id:
        return "rejected_actor_id_mismatch"
    if _dict_snapshot(event.original_request_evidence) != _dict_snapshot(packet.request_snapshot):
        return "rejected_request_evidence_mismatch"
    if packet.cost_preflight_evidence is None:
        return "rejected_missing_cost_preflight_evidence"
    if _dict_snapshot(event.cost_preflight_evidence) != _dict_snapshot(packet.cost_preflight_evidence):
        return "rejected_cost_preflight_evidence_mismatch"
    if packet.action_packet_id is None:
        if event.approval_evidence is not None:
            return "rejected_unexpected_approval_evidence"
    elif _dict_snapshot(event.approval_evidence) != _dict_snapshot(packet.approval_evidence):
        return "rejected_approval_evidence_mismatch"
    if authority_state.packet.state in {"cancelled", "expired", "completed", "failed"}:
        return f"rejected_{authority_state.packet.state}_handle"
    if any(
        (
            event.authority_expanded,
            event.memory_access_expanded,
            event.tool_authority_granted,
            event.provider_call_authorized,
            event.external_effect_authorized,
            event.execution_authorized,
            event.live_dispatch_authorized,
        )
    ):
        return "rejected_authority_expansion_attempt"
    payload_text = repr(sorted(event.completion_payload_summary.items()))
    if "external_effect" in payload_text or "dispatch" in payload_text or "connector" in payload_text:
        return "rejected_external_effect_payload"
    return None


def _transition_packet_and_handle(
    *,
    authority_state: AsyncDelegationAuthorityState,
    next_state: str,
) -> AsyncDelegationAuthorityState:
    packet = replace(authority_state.packet, state=next_state)
    handle = authority_state.handle
    if handle is not None:
        handle = replace(handle, status=next_state)
    return replace(authority_state, packet=packet, handle=handle)


def _blocked_transition(
    *,
    authority_state: AsyncDelegationAuthorityState,
    occurred_at: str,
    reason_code: str,
) -> AsyncDelegationAuthorityState:
    updated = _transition_packet_and_handle(authority_state=authority_state, next_state="blocked")
    return _append_transition(
        updated,
        previous_state=authority_state.packet.state,
        next_state="blocked",
        decision="block",
        reason_code=reason_code,
        occurred_at=occurred_at,
    )


def _append_transition(
    authority_state: AsyncDelegationAuthorityState,
    *,
    previous_state: str | None,
    next_state: str,
    decision: str,
    reason_code: str,
    occurred_at: str,
) -> AsyncDelegationAuthorityState:
    packet = authority_state.packet
    trace = AsyncDelegationTraceRecord(
        trace_id=_stable_id(
            "async_trace",
            packet.delegation_id,
            previous_state,
            next_state,
            decision,
            reason_code,
            occurred_at,
            authority_state.handle.handle_id if authority_state.handle is not None else None,
        ),
        delegation_id=packet.delegation_id,
        handle_id=None if authority_state.handle is None else authority_state.handle.handle_id,
        previous_state=previous_state,
        next_state=next_state,
        decision=decision,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        actor_id=packet.actor_id,
        actor_role=packet.actor_role,
        task_class=packet.task_class,
        source_stage=packet.source_stage,
        cost_preflight_decision=packet.cost_preflight_decision,
        action_packet_id=packet.action_packet_id,
        reason_code=reason_code,
    )
    return replace(authority_state, trace_records=authority_state.trace_records + (trace,))


def _build_packet(
    *,
    request: AsyncDelegationRequest,
    state: str,
    decision: str,
    cost_preflight: CostPreflightResult | None,
    action_packet_id: str | None,
    approval_resume_token_id: str | None,
) -> AsyncDelegationPacket:
    route = None if cost_preflight is None else cost_preflight.route_decision
    return AsyncDelegationPacket(
        delegation_id=request.delegation_id,
        packet_version=1,
        state=state,
        decision=decision,
        source_stage=request.source_stage,
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
        task_class=request.task_class,
        request_snapshot={
            "delegation_id": request.delegation_id,
            "source_stage": request.source_stage,
            "owner_id": request.owner_id,
            "robot_id": request.robot_id,
            "actor_id": request.actor_id,
            "actor_role": request.actor_role,
            "task_class": request.task_class,
            "requested_capability": request.requested_capability,
            "requested_route_mode": request.requested_route_mode,
            "request_payload": _dict_snapshot(request.request_payload),
            "required_memory_projection_request_id": request.required_memory_projection_request_id,
            "required_routine_run_id": request.required_routine_run_id,
            "expires_at": request.expires_at,
        },
        required_policy_trace=tuple(request.required_policy_trace),
        cost_preflight_evidence=serialize_cost_preflight_result(cost_preflight),
        approval_evidence=None,
        cost_preflight_request_id=None if cost_preflight is None else cost_preflight.request_id,
        cost_preflight_decision=None if cost_preflight is None else cost_preflight.decision,
        selected_provider_id=None if route is None else route.selected_provider_id,
        selected_model_id=None if route is None else route.selected_model_id,
        action_packet_id=action_packet_id,
        approval_resume_token_id=approval_resume_token_id,
        expires_at=request.expires_at,
    )


def _source_stage_unauthorized(stage: str) -> bool:
    if stage == "111P":
        return False
    if stage.endswith("P"):
        numeric = stage[:-1]
        if numeric.isdigit():
            return int(numeric) >= 103
    return False


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(NAMESPACE_URL, "|".join("" if part is None else str(part) for part in parts)).hex[:12]


def _dict_snapshot(value: dict[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    snapshot: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, dict):
            snapshot[key] = _dict_snapshot(item)
        elif isinstance(item, list):
            snapshot[key] = list(item)
        elif isinstance(item, tuple):
            snapshot[key] = list(item)
        else:
            snapshot[key] = item
    return snapshot


def build_completion_event(
    *,
    authority_state: AsyncDelegationAuthorityState,
    completion_status: str,
    source_stage: str,
    completion_payload_summary: dict[str, object],
    reason_code: str,
) -> AsyncDelegationCompletionEvent:
    packet = authority_state.packet
    handle = authority_state.handle
    if handle is None:
        raise ValueError("Completion events require a registered local handle.")
    if completion_status not in COMPLETION_STATUSES:
        raise ValueError("Completion status must be known.")
    if not handle.original_request_evidence:
        raise ValueError("Completion events require preserved original request evidence.")
    if not handle.cost_preflight_evidence:
        raise ValueError("Completion events require preserved 100P cost preflight evidence.")
    return AsyncDelegationCompletionEvent(
        event_id=_stable_id("async_event", packet.delegation_id, handle.handle_id, completion_status, source_stage, reason_code),
        handle_id=handle.handle_id,
        delegation_id=packet.delegation_id,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        actor_id=packet.actor_id,
        source_stage=source_stage,
        original_request_evidence=_dict_snapshot(handle.original_request_evidence) or {},
        cost_preflight_evidence=_dict_snapshot(handle.cost_preflight_evidence) or {},
        approval_evidence=None if handle.approval_evidence is None else _dict_snapshot(handle.approval_evidence),
        completion_status=completion_status,
        completion_payload_summary=_dict_snapshot(completion_payload_summary) or {},
        reason_code=reason_code,
    )
