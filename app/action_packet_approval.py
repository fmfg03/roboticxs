from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from app.cost_governor import CostPreflightResult
from app.hermes_os_contract import HermesOSRuntimeContract
from app.routine_execution_engine import RoutineRun
from app.telegram_policy_chain import LocalCostConfirmation, TelegramPolicyChainResult


ACTION_PACKET_APPROVAL_STAGE = "101P"

ActionType = Literal[
    "cost_confirmation",
    "tool_action",
    "routine_continuation",
    "async_delegation",
    "live_delivery",
    "connector_action",
    "external_tool_execution",
]
ActionPacketApprovalStatus = Literal[
    "proposed",
    "awaiting_approval",
    "approved",
    "rejected",
    "edited",
    "cancelled",
    "expired",
    "resumed",
    "blocked",
]
DecisionType = Literal["approve", "reject", "edit", "cancel", "expire", "resume"]
ResumeScope = Literal[
    "exact_packet",
    "exact_revision",
    "exact_preflight",
    "exact_routine_run",
    "exact_memory_projection",
    "future_local_runtime_only",
]

ACTION_TYPES = frozenset(
    {
        "cost_confirmation",
        "tool_action",
        "routine_continuation",
        "async_delegation",
        "live_delivery",
        "connector_action",
        "external_tool_execution",
    }
)
APPROVAL_STATES = frozenset(
    {
        "proposed",
        "awaiting_approval",
        "approved",
        "rejected",
        "edited",
        "cancelled",
        "expired",
        "resumed",
        "blocked",
    }
)
DECISIONS = frozenset({"approve", "reject", "edit", "cancel", "expire", "resume"})
RESUME_BLOCKING_STATES = frozenset({"rejected", "cancelled", "expired", "blocked", "edited"})


@dataclass(frozen=True, slots=True)
class ActionPacketRequest:
    request_id: str
    source_stage: str
    action_type: str
    owner_id: str
    robot_id: str
    actor_id: str
    actor_role: str
    requested_by_actor_id: str
    requested_by_actor_role: str
    required_policy_trace: tuple[str, ...]
    required_cost_preflight: dict[str, object] | None
    required_memory_projection: dict[str, object] | None
    required_routine_context: dict[str, object] | None
    action_payload: dict[str, object]
    review_expires_at: str | None
    resume_scope: str


@dataclass(frozen=True, slots=True)
class ActionPacket:
    packet_id: str
    packet_version: int
    state: str
    action_type: str
    source_stage: str
    owner_id: str
    robot_id: str
    actor_id: str
    actor_role: str
    requested_by_actor_id: str
    requested_by_actor_role: str
    required_policy_trace: tuple[str, ...]
    required_cost_preflight_request_id: str | None
    required_cost_preflight_decision: str | None
    required_selected_model_id: str | None
    required_memory_projection_request_id: str | None
    required_routine_run_id: str | None
    action_payload: dict[str, object]
    review_expires_at: str | None
    resume_scope: str
    resume_token_id: str | None
    supersedes_packet_id: str | None
    audit_note: str | None
    authority_expanded: bool
    external_effect_authorized: bool
    provider_call_authorized: bool
    execution_authorized: bool


@dataclass(frozen=True, slots=True)
class ActionPacketDecision:
    packet_id: str
    packet_version: int
    decision: str
    actor_id: str
    actor_role: str
    owner_id: str
    robot_id: str
    reason_code: str
    edit_payload: dict[str, object] | None
    resume_token_id: str | None
    occurred_at: str


@dataclass(frozen=True, slots=True)
class ActionPacketReviewEvent:
    event_id: str
    packet_id: str
    packet_version: int
    previous_state: str | None
    next_state: str
    decision: str | None
    actor_id: str
    actor_role: str
    owner_id: str
    robot_id: str
    action_type: str
    source_stage: str
    reason_code: str
    occurred_at: str


@dataclass(frozen=True, slots=True)
class ActionPacketResumeToken:
    token_id: str
    packet_id: str
    packet_version: int
    owner_id: str
    robot_id: str
    actor_id: str
    actor_role: str
    resume_scope: str
    source_stage: str
    issued_at: str
    expires_at: str | None
    used: bool = False
    used_at: str | None = None
    authority_expanded: bool = False
    external_effect_authorized: bool = False
    provider_call_authorized: bool = False
    execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class ActionPacketTraceRecord:
    trace_id: str
    packet_id: str
    packet_version: int
    previous_state: str | None
    next_state: str
    decision: str | None
    actor_id: str
    actor_role: str
    owner_id: str
    robot_id: str
    action_type: str
    source_stage: str
    reason_code: str
    authority_expanded: bool
    external_effect_authorized: bool
    provider_call_authorized: bool
    execution_authorized: bool


@dataclass(frozen=True, slots=True)
class ActionPacketApprovalState:
    stage: str
    packet: ActionPacket
    review_history: tuple[ActionPacketReviewEvent, ...]
    trace_records: tuple[ActionPacketTraceRecord, ...]
    resume_token: ActionPacketResumeToken | None
    prior_versions: tuple[ActionPacket, ...]
    data_only: bool = True
    local_only: bool = True


def create_action_packet(*, request: ActionPacketRequest, occurred_at: str, reason_code: str = "packet_created") -> ActionPacketApprovalState:
    block_reason = _request_block_reason(request)
    packet_id = _stable_id("action_packet", request.request_id, request.owner_id, request.robot_id, request.action_type)
    initial_state = "blocked" if block_reason is not None else "proposed"
    packet = ActionPacket(
        packet_id=packet_id,
        packet_version=1,
        state=initial_state,
        action_type=request.action_type,
        source_stage=request.source_stage,
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
        requested_by_actor_id=request.requested_by_actor_id,
        requested_by_actor_role=request.requested_by_actor_role,
        required_policy_trace=tuple(request.required_policy_trace),
        required_cost_preflight_request_id=_dict_str(request.required_cost_preflight, "request_id"),
        required_cost_preflight_decision=_dict_str(request.required_cost_preflight, "decision"),
        required_selected_model_id=_selected_model_id(request.required_cost_preflight),
        required_memory_projection_request_id=_dict_str(request.required_memory_projection, "request_id"),
        required_routine_run_id=_dict_str(request.required_routine_context, "run_id"),
        action_payload=dict(request.action_payload),
        review_expires_at=request.review_expires_at,
        resume_scope=request.resume_scope,
        resume_token_id=None,
        supersedes_packet_id=None,
        audit_note=None,
        authority_expanded=False,
        external_effect_authorized=False,
        provider_call_authorized=False,
        execution_authorized=False,
    )
    return _append_transition(
        ActionPacketApprovalState(
            stage=ACTION_PACKET_APPROVAL_STAGE,
            packet=packet,
            review_history=(),
            trace_records=(),
            resume_token=None,
            prior_versions=(),
        ),
        previous_state=None,
        next_state=initial_state,
        decision=None,
        actor_id=request.requested_by_actor_id,
        actor_role=request.requested_by_actor_role,
        reason_code=block_reason or reason_code,
        occurred_at=occurred_at,
    )


def submit_action_packet_for_approval(
    *,
    approval_state: ActionPacketApprovalState,
    actor_id: str,
    actor_role: str,
    occurred_at: str,
    reason_code: str = "submitted_for_approval",
) -> ActionPacketApprovalState:
    if approval_state.packet.state not in APPROVAL_STATES:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=actor_id,
            actor_role=actor_role,
            occurred_at=occurred_at,
            reason_code="blocked_unknown_packet_state",
        )
    if approval_state.packet.state != "proposed":
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=actor_id,
            actor_role=actor_role,
            occurred_at=occurred_at,
            reason_code="blocked_submit_requires_proposed_state",
        )
    packet = replace(approval_state.packet, state="awaiting_approval")
    return _append_transition(
        replace(approval_state, packet=packet),
        previous_state="proposed",
        next_state="awaiting_approval",
        decision=None,
        actor_id=actor_id,
        actor_role=actor_role,
        reason_code=reason_code,
        occurred_at=occurred_at,
    )


def apply_action_packet_decision(
    *,
    approval_state: ActionPacketApprovalState,
    decision: ActionPacketDecision,
) -> ActionPacketApprovalState:
    packet = approval_state.packet
    unknown_state = packet.state not in APPROVAL_STATES
    if unknown_state:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code="blocked_unknown_packet_state",
        )
    if decision.decision not in DECISIONS:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code="blocked_unknown_decision",
        )
    mismatch = _decision_mismatch_reason(packet=packet, decision=decision)
    if mismatch is not None:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code=mismatch,
        )
    if decision.decision != "resume" and _is_expired(packet=packet, occurred_at=decision.occurred_at):
        expired_packet = replace(packet, state="expired")
        return _append_transition(
            replace(approval_state, packet=expired_packet),
            previous_state=packet.state,
            next_state="expired",
            decision=decision.decision,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            reason_code="expired_review_window_elapsed",
            occurred_at=decision.occurred_at,
        )

    if decision.decision == "approve":
        if packet.state != "awaiting_approval":
            return _blocked_transition(
                approval_state=approval_state,
                actor_id=decision.actor_id,
                actor_role=decision.actor_role,
                occurred_at=decision.occurred_at,
                reason_code="blocked_approve_requires_awaiting_approval",
            )
        token = _issue_resume_token(packet=packet, decision=decision)
        approved_packet = replace(packet, state="approved", resume_token_id=token.token_id)
        return _append_transition(
            replace(approval_state, packet=approved_packet, resume_token=token),
            previous_state=packet.state,
            next_state="approved",
            decision=decision.decision,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            reason_code=decision.reason_code,
            occurred_at=decision.occurred_at,
        )

    if decision.decision == "reject":
        return _terminal_transition(approval_state=approval_state, decision=decision, next_state="rejected")
    if decision.decision == "cancel":
        return _terminal_transition(approval_state=approval_state, decision=decision, next_state="cancelled")
    if decision.decision == "expire":
        return _terminal_transition(approval_state=approval_state, decision=decision, next_state="expired")
    if decision.decision == "edit":
        return _edit_transition(approval_state=approval_state, decision=decision)
    return _resume_transition(approval_state=approval_state, decision=decision)


def action_packet_request_from_95p_result(
    *,
    policy_result: TelegramPolicyChainResult,
    actor_id: str,
    actor_role: str,
    review_expires_at: str | None = None,
) -> ActionPacketRequest:
    if policy_result.action_packet is None:
        raise ValueError("95P result must include an Action Packet for 101P binding.")
    if not policy_result.policy_trace:
        raise ValueError("95P result must include policy trace for 101P binding.")
    owner_id = str(policy_result.user_id)
    robot_id = _local_robot_id_for_user(policy_result.user_id)
    return ActionPacketRequest(
        request_id=policy_result.action_packet.packet_id,
        source_stage=policy_result.stage,
        action_type="tool_action",
        owner_id=owner_id,
        robot_id=robot_id,
        actor_id=actor_id,
        actor_role=actor_role,
        requested_by_actor_id=owner_id,
        requested_by_actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in policy_result.policy_trace),
        required_cost_preflight=None,
        required_memory_projection=_memory_projection_snapshot(policy_result),
        required_routine_context=None,
        action_payload={
            "action_class": policy_result.action_packet.action_class,
            "requested_text": policy_result.action_packet.requested_text,
            "final_user_visible_content": policy_result.action_packet.final_user_visible_content,
            "confirmation_command": policy_result.action_packet.confirmation_command,
            "hermes_adapter_called": policy_result.hermes_adapter.called,
        },
        review_expires_at=review_expires_at,
        resume_scope="future_local_runtime_only",
    )


def action_packet_request_from_cost_confirmation(
    *,
    cost_confirmation: LocalCostConfirmation,
    cost_preflight: CostPreflightResult,
    actor_id: str,
    actor_role: str,
    required_policy_trace: tuple[str, ...],
    review_expires_at: str | None = None,
) -> ActionPacketRequest:
    if cost_confirmation.decision != "require_confirmation" or cost_preflight.decision != "require_confirmation":
        raise ValueError("Only 100P require_confirmation results can convert into 101P cost-confirmation packets.")
    return ActionPacketRequest(
        request_id=cost_confirmation.request_id,
        source_stage="100P",
        action_type="cost_confirmation",
        owner_id=cost_confirmation.owner_id,
        robot_id=cost_confirmation.robot_id,
        actor_id=actor_id,
        actor_role=actor_role,
        requested_by_actor_id=cost_confirmation.owner_id,
        requested_by_actor_role="owner_admin",
        required_policy_trace=required_policy_trace,
        required_cost_preflight=_cost_preflight_snapshot(cost_preflight),
        required_memory_projection=None,
        required_routine_context=None,
        action_payload={
            "confirmation_type": cost_confirmation.confirmation_type,
            "task_class": cost_confirmation.task_class,
            "routing_mode": cost_confirmation.routing_mode,
            "estimated_tokens": cost_confirmation.estimated_tokens,
            "estimated_cost_usd": cost_confirmation.estimated_cost_usd,
            "selected_model_id": cost_confirmation.selected_model_id,
            "decision": cost_confirmation.decision,
            "reason_code": cost_confirmation.reason_code,
        },
        review_expires_at=review_expires_at,
        resume_scope="exact_preflight",
    )


def action_packet_request_from_routine_run(
    *,
    routine_run: RoutineRun,
    actor_id: str,
    actor_role: str,
    review_expires_at: str | None = None,
) -> ActionPacketRequest:
    return ActionPacketRequest(
        request_id=routine_run.run_id,
        source_stage=routine_run.stage,
        action_type="routine_continuation",
        owner_id=str(routine_run.policy_result.user_id),
        robot_id=_local_robot_id_for_user(routine_run.policy_result.user_id),
        actor_id=actor_id,
        actor_role=actor_role,
        requested_by_actor_id=str(routine_run.policy_result.user_id),
        requested_by_actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in routine_run.policy_result.policy_trace),
        required_cost_preflight=None
        if routine_run.task_run_record.cost_preflight_decision is None
        else {
            "request_id": routine_run.task_run_record.task_run_id,
            "decision": routine_run.task_run_record.cost_preflight_decision,
            "selected_model_id": routine_run.task_run_record.selected_model_id,
        },
        required_memory_projection=_routine_memory_snapshot(routine_run),
        required_routine_context={
            "run_id": routine_run.run_id,
            "preflight_policy_chain_routed": routine_run.preflight.policy_chain_routed,
            "wake_allowed": routine_run.preflight.wake_allowed,
            "budget_allowed": routine_run.preflight.budget_allowed,
        },
        action_payload={
            "routine_id": routine_run.definition.routine_id,
            "routine_state": routine_run.state,
            "policy_chain_routed": routine_run.preflight.policy_chain_routed,
        },
        review_expires_at=review_expires_at,
        resume_scope="exact_routine_run",
    )


def bind_approval_state_to_96p_contract(
    *,
    contract: HermesOSRuntimeContract,
    approval_state: ActionPacketApprovalState,
) -> dict[str, object]:
    return {
        "binding_stage": contract.stage,
        "approval_stage": approval_state.stage,
        "packet_id": approval_state.packet.packet_id,
        "packet_version": approval_state.packet.packet_version,
        "approval_state": approval_state.packet.state,
        "tool_request_requires_action_packet": contract.tool_request_packet.requires_action_packet,
        "action_packet_bound": contract.action_packet_binding.bound,
        "approval_is_tool_authority": False,
        "approval_is_execution_authority": False,
        "external_effect_authorized": False,
        "provider_call_authorized": False,
        "execution_authorized": False,
    }


def serialize_action_packet_approval_state(approval_state: ActionPacketApprovalState) -> dict[str, object]:
    return {
        "stage": approval_state.stage,
        "packet": {
            "packet_id": approval_state.packet.packet_id,
            "packet_version": approval_state.packet.packet_version,
            "state": approval_state.packet.state,
            "action_type": approval_state.packet.action_type,
            "source_stage": approval_state.packet.source_stage,
            "owner_id": approval_state.packet.owner_id,
            "robot_id": approval_state.packet.robot_id,
            "actor_id": approval_state.packet.actor_id,
            "actor_role": approval_state.packet.actor_role,
            "required_policy_trace": list(approval_state.packet.required_policy_trace),
            "required_cost_preflight_request_id": approval_state.packet.required_cost_preflight_request_id,
            "required_cost_preflight_decision": approval_state.packet.required_cost_preflight_decision,
            "required_selected_model_id": approval_state.packet.required_selected_model_id,
            "required_memory_projection_request_id": approval_state.packet.required_memory_projection_request_id,
            "required_routine_run_id": approval_state.packet.required_routine_run_id,
            "action_payload": dict(approval_state.packet.action_payload),
            "review_expires_at": approval_state.packet.review_expires_at,
            "resume_scope": approval_state.packet.resume_scope,
            "resume_token_id": approval_state.packet.resume_token_id,
            "supersedes_packet_id": approval_state.packet.supersedes_packet_id,
            "authority_expanded": approval_state.packet.authority_expanded,
            "external_effect_authorized": approval_state.packet.external_effect_authorized,
            "provider_call_authorized": approval_state.packet.provider_call_authorized,
            "execution_authorized": approval_state.packet.execution_authorized,
        },
        "resume_token": None
        if approval_state.resume_token is None
        else {
            "token_id": approval_state.resume_token.token_id,
            "packet_id": approval_state.resume_token.packet_id,
            "packet_version": approval_state.resume_token.packet_version,
            "owner_id": approval_state.resume_token.owner_id,
            "robot_id": approval_state.resume_token.robot_id,
            "actor_id": approval_state.resume_token.actor_id,
            "actor_role": approval_state.resume_token.actor_role,
            "resume_scope": approval_state.resume_token.resume_scope,
            "source_stage": approval_state.resume_token.source_stage,
            "issued_at": approval_state.resume_token.issued_at,
            "expires_at": approval_state.resume_token.expires_at,
            "used": approval_state.resume_token.used,
            "used_at": approval_state.resume_token.used_at,
            "authority_expanded": approval_state.resume_token.authority_expanded,
            "external_effect_authorized": approval_state.resume_token.external_effect_authorized,
            "provider_call_authorized": approval_state.resume_token.provider_call_authorized,
            "execution_authorized": approval_state.resume_token.execution_authorized,
        },
        "review_history": [
            {
                "event_id": event.event_id,
                "packet_id": event.packet_id,
                "packet_version": event.packet_version,
                "previous_state": event.previous_state,
                "next_state": event.next_state,
                "decision": event.decision,
                "actor_id": event.actor_id,
                "actor_role": event.actor_role,
                "owner_id": event.owner_id,
                "robot_id": event.robot_id,
                "action_type": event.action_type,
                "source_stage": event.source_stage,
                "reason_code": event.reason_code,
                "occurred_at": event.occurred_at,
            }
            for event in approval_state.review_history
        ],
        "trace_records": [
            {
                "trace_id": trace.trace_id,
                "packet_id": trace.packet_id,
                "packet_version": trace.packet_version,
                "previous_state": trace.previous_state,
                "next_state": trace.next_state,
                "decision": trace.decision,
                "actor_id": trace.actor_id,
                "actor_role": trace.actor_role,
                "owner_id": trace.owner_id,
                "robot_id": trace.robot_id,
                "action_type": trace.action_type,
                "source_stage": trace.source_stage,
                "reason_code": trace.reason_code,
                "authority_expanded": trace.authority_expanded,
                "external_effect_authorized": trace.external_effect_authorized,
                "provider_call_authorized": trace.provider_call_authorized,
                "execution_authorized": trace.execution_authorized,
            }
            for trace in approval_state.trace_records
        ],
        "prior_versions": [
            {
                "packet_id": packet.packet_id,
                "packet_version": packet.packet_version,
                "state": packet.state,
            }
            for packet in approval_state.prior_versions
        ],
    }


def _terminal_transition(
    *,
    approval_state: ActionPacketApprovalState,
    decision: ActionPacketDecision,
    next_state: str,
) -> ActionPacketApprovalState:
    current = approval_state.packet
    if current.state in RESUME_BLOCKING_STATES or current.state == "resumed":
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code=f"blocked_{current.state}_packet_cannot_transition",
        )
    packet = replace(current, state=next_state)
    return _append_transition(
        replace(approval_state, packet=packet),
        previous_state=current.state,
        next_state=next_state,
        decision=decision.decision,
        actor_id=decision.actor_id,
        actor_role=decision.actor_role,
        reason_code=decision.reason_code,
        occurred_at=decision.occurred_at,
    )


def _edit_transition(
    *,
    approval_state: ActionPacketApprovalState,
    decision: ActionPacketDecision,
) -> ActionPacketApprovalState:
    if decision.edit_payload is None:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code="blocked_edit_missing_payload",
        )
    current = approval_state.packet
    edited_packet = replace(current, state="edited")
    edited_state = _append_transition(
        replace(
            approval_state,
            packet=edited_packet,
            prior_versions=approval_state.prior_versions + (current,),
        ),
        previous_state=current.state,
        next_state="edited",
        decision=decision.decision,
        actor_id=decision.actor_id,
        actor_role=decision.actor_role,
        reason_code=decision.reason_code,
        occurred_at=decision.occurred_at,
    )
    revised_packet = ActionPacket(
        packet_id=current.packet_id,
        packet_version=current.packet_version + 1,
        state="proposed",
        action_type=current.action_type,
        source_stage=current.source_stage,
        owner_id=current.owner_id,
        robot_id=current.robot_id,
        actor_id=current.actor_id,
        actor_role=current.actor_role,
        requested_by_actor_id=current.requested_by_actor_id,
        requested_by_actor_role=current.requested_by_actor_role,
        required_policy_trace=current.required_policy_trace,
        required_cost_preflight_request_id=current.required_cost_preflight_request_id,
        required_cost_preflight_decision=current.required_cost_preflight_decision,
        required_selected_model_id=current.required_selected_model_id,
        required_memory_projection_request_id=current.required_memory_projection_request_id,
        required_routine_run_id=current.required_routine_run_id,
        action_payload=dict(decision.edit_payload),
        review_expires_at=current.review_expires_at,
        resume_scope=current.resume_scope,
        resume_token_id=None,
        supersedes_packet_id=current.packet_id,
        audit_note=f"edited_from_v{current.packet_version}",
        authority_expanded=False,
        external_effect_authorized=False,
        provider_call_authorized=False,
        execution_authorized=False,
    )
    return _append_transition(
        replace(edited_state, packet=revised_packet, resume_token=None),
        previous_state=None,
        next_state="proposed",
        decision="edit",
        actor_id=decision.actor_id,
        actor_role=decision.actor_role,
        reason_code="edited_revision_created",
        occurred_at=decision.occurred_at,
    )


def _resume_transition(
    *,
    approval_state: ActionPacketApprovalState,
    decision: ActionPacketDecision,
) -> ActionPacketApprovalState:
    current = approval_state.packet
    token = approval_state.resume_token
    if current.state in RESUME_BLOCKING_STATES:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code=f"blocked_{current.state}_packet_cannot_resume",
        )
    if current.state != "approved" or token is None or decision.resume_token_id is None:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code="blocked_resume_requires_approved_packet_and_token",
        )
    token_reason = _resume_token_block_reason(token=token, packet=current, decision=decision)
    if token_reason is not None:
        return _blocked_transition(
            approval_state=approval_state,
            actor_id=decision.actor_id,
            actor_role=decision.actor_role,
            occurred_at=decision.occurred_at,
            reason_code=token_reason,
        )
    used_token = replace(token, used=True, used_at=decision.occurred_at)
    resumed_packet = replace(current, state="resumed")
    return _append_transition(
        replace(approval_state, packet=resumed_packet, resume_token=used_token),
        previous_state=current.state,
        next_state="resumed",
        decision=decision.decision,
        actor_id=decision.actor_id,
        actor_role=decision.actor_role,
        reason_code=decision.reason_code,
        occurred_at=decision.occurred_at,
    )


def _blocked_transition(
    *,
    approval_state: ActionPacketApprovalState,
    actor_id: str,
    actor_role: str,
    occurred_at: str,
    reason_code: str,
) -> ActionPacketApprovalState:
    current = approval_state.packet
    blocked_packet = replace(current, state="blocked")
    return _append_transition(
        replace(approval_state, packet=blocked_packet, resume_token=None if current.state == "blocked" else approval_state.resume_token),
        previous_state=current.state,
        next_state="blocked",
        decision=None,
        actor_id=actor_id,
        actor_role=actor_role,
        reason_code=reason_code,
        occurred_at=occurred_at,
    )


def _append_transition(
    approval_state: ActionPacketApprovalState,
    *,
    previous_state: str | None,
    next_state: str,
    decision: str | None,
    actor_id: str,
    actor_role: str,
    reason_code: str,
    occurred_at: str,
) -> ActionPacketApprovalState:
    packet = approval_state.packet
    event = ActionPacketReviewEvent(
        event_id=_stable_id(
            "review_event",
            packet.packet_id,
            packet.packet_version,
            previous_state,
            next_state,
            decision,
            actor_id,
            occurred_at,
            reason_code,
        ),
        packet_id=packet.packet_id,
        packet_version=packet.packet_version,
        previous_state=previous_state,
        next_state=next_state,
        decision=decision,
        actor_id=actor_id,
        actor_role=actor_role,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        action_type=packet.action_type,
        source_stage=packet.source_stage,
        reason_code=reason_code,
        occurred_at=occurred_at,
    )
    trace = ActionPacketTraceRecord(
        trace_id=_stable_id(
            "trace_record",
            packet.packet_id,
            packet.packet_version,
            previous_state,
            next_state,
            decision,
            actor_id,
            occurred_at,
            reason_code,
        ),
        packet_id=packet.packet_id,
        packet_version=packet.packet_version,
        previous_state=previous_state,
        next_state=next_state,
        decision=decision,
        actor_id=actor_id,
        actor_role=actor_role,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        action_type=packet.action_type,
        source_stage=packet.source_stage,
        reason_code=reason_code,
        authority_expanded=False,
        external_effect_authorized=False,
        provider_call_authorized=False,
        execution_authorized=False,
    )
    return replace(
        approval_state,
        review_history=approval_state.review_history + (event,),
        trace_records=approval_state.trace_records + (trace,),
    )


def _issue_resume_token(*, packet: ActionPacket, decision: ActionPacketDecision) -> ActionPacketResumeToken:
    return ActionPacketResumeToken(
        token_id=_stable_id("resume_token", packet.packet_id, packet.packet_version, decision.actor_id, decision.occurred_at),
        packet_id=packet.packet_id,
        packet_version=packet.packet_version,
        owner_id=packet.owner_id,
        robot_id=packet.robot_id,
        actor_id=packet.actor_id,
        actor_role=packet.actor_role,
        resume_scope=packet.resume_scope,
        source_stage=packet.source_stage,
        issued_at=decision.occurred_at,
        expires_at=packet.review_expires_at,
    )


def _resume_token_block_reason(*, token: ActionPacketResumeToken, packet: ActionPacket, decision: ActionPacketDecision) -> str | None:
    if token.token_id != decision.resume_token_id:
        return "blocked_resume_token_mismatch"
    if token.used:
        return "blocked_resume_token_already_used"
    if token.owner_id != decision.owner_id:
        return "blocked_owner_id_mismatch"
    if token.robot_id != decision.robot_id:
        return "blocked_robot_id_mismatch"
    if token.actor_id != decision.actor_id:
        return "blocked_actor_id_mismatch"
    if token.actor_role != decision.actor_role:
        return "blocked_actor_role_mismatch"
    if token.packet_id != packet.packet_id or token.packet_version != packet.packet_version:
        return "blocked_packet_revision_mismatch"
    if token.expires_at is not None and decision.occurred_at > token.expires_at:
        return "blocked_resume_token_expired"
    return None


def _decision_mismatch_reason(*, packet: ActionPacket, decision: ActionPacketDecision) -> str | None:
    if packet.packet_id != decision.packet_id or packet.packet_version != decision.packet_version:
        return "blocked_packet_revision_mismatch"
    if packet.owner_id != decision.owner_id:
        return "blocked_owner_id_mismatch"
    if packet.robot_id != decision.robot_id:
        return "blocked_robot_id_mismatch"
    if decision.decision in {"approve", "resume"} and packet.actor_id != decision.actor_id:
        return "blocked_actor_id_mismatch"
    if packet.actor_role and packet.actor_role != decision.actor_role:
        return "blocked_actor_role_mismatch"
    return None


def _request_block_reason(request: ActionPacketRequest) -> str | None:
    if request.action_type not in ACTION_TYPES:
        return "blocked_unknown_action_type"
    if request.resume_scope not in {
        "exact_packet",
        "exact_revision",
        "exact_preflight",
        "exact_routine_run",
        "exact_memory_projection",
        "future_local_runtime_only",
    }:
        return "blocked_unknown_resume_scope"
    if not request.required_policy_trace:
        return "blocked_missing_required_policy_trace"
    if _source_stage_unauthorized(request.source_stage):
        return "blocked_unauthorized_source_stage"
    if request.action_type == "cost_confirmation" and request.required_cost_preflight is None:
        return "blocked_missing_required_cost_preflight"
    if request.action_payload.get("cost_preflight_required") and request.required_cost_preflight is None:
        return "blocked_missing_required_cost_preflight"
    if request.action_payload.get("memory_projection_required") and request.required_memory_projection is None:
        return "blocked_missing_required_memory_projection"
    if request.required_memory_projection is not None and request.required_memory_projection.get("bounded") is False:
        return "blocked_unbounded_memory_projection"
    if request.action_type == "routine_continuation":
        if request.required_routine_context is None:
            return "blocked_missing_required_routine_context"
        if request.required_routine_context.get("preflight_policy_chain_routed") is False:
            return "blocked_routine_preflight_not_satisfied"
    return None


def _source_stage_unauthorized(stage: str) -> bool:
    if stage.endswith("P"):
        numeric = stage[:-1]
        if numeric.isdigit():
            return int(numeric) >= 102
    return False


def _selected_model_id(snapshot: dict[str, object] | None) -> str | None:
    if snapshot is None:
        return None
    route = snapshot.get("route_decision")
    if isinstance(route, dict):
        value = route.get("selected_model_id")
        return None if value is None else str(value)
    value = snapshot.get("selected_model_id")
    return None if value is None else str(value)


def _dict_str(source: dict[str, object] | None, key: str) -> str | None:
    if source is None:
        return None
    value = source.get(key)
    return None if value is None else str(value)


def _is_expired(*, packet: ActionPacket, occurred_at: str) -> bool:
    return packet.review_expires_at is not None and occurred_at > packet.review_expires_at


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(NAMESPACE_URL, "|".join("" if part is None else str(part) for part in parts)).hex[:12]


def _cost_preflight_snapshot(result: CostPreflightResult) -> dict[str, object]:
    return {
        "request_id": result.request_id,
        "decision": result.decision,
        "budget_policy_id": result.budget_policy_id,
        "estimated_cost_usd": result.estimated_cost_usd,
        "selected_model_id": None if result.route_decision is None else result.route_decision.selected_model_id,
        "route_decision": None
        if result.route_decision is None
        else {
            "selected_model_id": result.route_decision.selected_model_id,
            "selected_provider_id": result.route_decision.selected_provider_id,
            "decision_reason": result.route_decision.decision_reason,
        },
        "trace_reason_code": result.trace[-1].reason_code,
        "confirmation_required": result.confirmation_required,
        "execution_authorized": result.execution_authorized,
    }


def _memory_projection_snapshot(policy_result: TelegramPolicyChainResult) -> dict[str, object] | None:
    projection_result = policy_result.memory_context.projection_result
    if projection_result is None:
        return None
    return {
        "request_id": projection_result.request_id,
        "bounded": projection_result.bounded,
        "summary_count": len(projection_result.summaries),
        "allowed_use": policy_result.memory_context.projections[0].allowed_use if policy_result.memory_context.projections else None,
        "trace_reason_codes": [trace.reason_code for trace in projection_result.trace],
    }


def _routine_memory_snapshot(routine_run: RoutineRun) -> dict[str, object]:
    return {
        "request_id": f"routine_memory:{routine_run.run_id}",
        "bounded": True,
        "summary_count": len(routine_run.bounded_memory_projection),
        "trace_reason_codes": [],
    }


def _local_robot_id_for_user(user_id: int | None) -> str:
    return _stable_id("robot", user_id)
