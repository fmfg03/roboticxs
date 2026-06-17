from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from app.caregiver_telegram_mvp import CaregiverTelegramMVPResult, run_caregiver_telegram_mvp
from app.config import Settings
from app.hermes_os_contract import HermesOSRuntimeContract, TaskRunRecord, build_hermes_os_runtime_contract
from app.telegram_policy_chain import (
    HermesGatewayAdapterStubResult,
    LocalActionPacket,
    MemoryContextBlock,
    MemoryProjection,
    PolicyDecision,
    TelegramPolicyChainResult,
    run_telegram_policy_chain,
)


ROUTINE_EXECUTION_STAGE = "98P"

RoutineState = Literal[
    "pending",
    "running",
    "completed",
    "skipped",
    "needs_confirmation",
    "blocked",
    "failed",
]
RoutineKind = Literal["general", "caregiver"]

SENSITIVE_MEMORY_TYPES = {"CREDENTIAL", "SECRET", "MEDICAL_DECISION", "OWNER_PRIVATE", "UNRELATED_OWNER_MEMORY"}


@dataclass(frozen=True, slots=True)
class RoutineDefinition:
    routine_id: str
    label: str
    trigger_text: str
    kind: RoutineKind = "general"
    explicit_user_approved: bool = True
    manual_start_required: bool = True
    wake_signal_present: bool = True
    budget_preflight_allowed: bool = True
    live_schedule_authorized: bool = False
    live_delivery_authorized: bool = False
    automatic_caregiver_alerts_authorized: bool = False
    allow_sensitive_memory_expansion: bool = False

    def __post_init__(self) -> None:
        if self.live_schedule_authorized or self.live_delivery_authorized:
            raise ValueError("98P routines cannot authorize live scheduling or delivery.")
        if self.automatic_caregiver_alerts_authorized:
            raise ValueError("98P routines cannot authorize automatic caregiver alerts.")
        if self.allow_sensitive_memory_expansion:
            raise ValueError("98P routines cannot authorize sensitive memory expansion.")


@dataclass(frozen=True, slots=True)
class RoutinePreflight:
    wake_allowed: bool
    budget_allowed: bool
    explicit_user_approved: bool
    manual_start_required: bool
    policy_chain_routed: bool


@dataclass(frozen=True, slots=True)
class LocalRoutineDelivery:
    delivery_id: str
    channel: str
    content: str
    automatic_delivery_authorized: bool
    live_telegram_send_authorized: bool
    external_side_effect_authorized: bool
    caregiver_send_authorized: bool

    def __post_init__(self) -> None:
        if any(
            (
                self.automatic_delivery_authorized,
                self.live_telegram_send_authorized,
                self.external_side_effect_authorized,
                self.caregiver_send_authorized,
            )
        ):
            raise ValueError("98P local delivery objects cannot authorize live or automatic delivery.")


@dataclass(frozen=True, slots=True)
class RoutineAuditEvent:
    event: str
    detail: str


@dataclass(frozen=True, slots=True)
class RoutineRun:
    run_id: str
    stage: str
    definition: RoutineDefinition
    state: RoutineState
    preflight: RoutinePreflight
    policy_result: TelegramPolicyChainResult
    hermes_os_contract: HermesOSRuntimeContract
    task_run_record: TaskRunRecord
    bounded_memory_projection: tuple[MemoryProjection, ...]
    delivery: LocalRoutineDelivery
    action_packet: LocalActionPacket | None
    caregiver_result: CaregiverTelegramMVPResult | None
    audit_trail: tuple[RoutineAuditEvent, ...]
    error_code: str | None
    live_scheduler_authorized: bool
    live_cron_authorized: bool
    live_telegram_send_authorized: bool
    external_side_effect_authorized: bool
    automatic_caregiver_alert_authorized: bool
    medical_decision_authorized: bool
    hidden_escalation_authorized: bool

    def __post_init__(self) -> None:
        if any(
            (
                self.live_scheduler_authorized,
                self.live_cron_authorized,
                self.live_telegram_send_authorized,
                self.external_side_effect_authorized,
                self.automatic_caregiver_alert_authorized,
                self.medical_decision_authorized,
                self.hidden_escalation_authorized,
            )
        ):
            raise ValueError("98P RoutineRun cannot authorize external effects, medical decisions, or hidden escalation.")


def execute_routine_locally(
    *,
    definition: RoutineDefinition,
    update: dict,
    settings: Settings,
    session: Session,
    force_failure: bool = False,
) -> RoutineRun:
    preflight_stop = _preflight_stop(definition=definition, force_failure=force_failure)
    if preflight_stop is not None:
        state, error_code = preflight_stop
        policy_result = _preflight_stopped_policy_result(update=update, state=state, error_code=error_code)
        hermes_os_contract = build_hermes_os_runtime_contract(policy_result=policy_result, routine_requested=True)
        return _build_routine_run(
            definition=definition,
            state=state,
            error_code=error_code,
            policy_result=policy_result,
            hermes_os_contract=hermes_os_contract,
            caregiver_result=None,
            policy_chain_routed=False,
        )

    policy_result = run_telegram_policy_chain(
        update=update,
        settings=settings,
        session=session,
        memory_actor_role="routine",
        memory_target_scope="routine",
        memory_allowed_use="routine_context",
    )
    hermes_os_contract = build_hermes_os_runtime_contract(policy_result=policy_result, routine_requested=True)
    caregiver_result = (
        run_caregiver_telegram_mvp(
            update=update,
            settings=settings,
            session=session,
            routine_label=definition.label,
        )
        if definition.kind == "caregiver"
        else None
    )
    state, error_code = _state_for_policy_result(
        policy_result=policy_result,
        caregiver_result=caregiver_result,
    )
    return _build_routine_run(
        definition=definition,
        state=state,
        error_code=error_code,
        policy_result=policy_result,
        hermes_os_contract=hermes_os_contract,
        caregiver_result=caregiver_result,
        policy_chain_routed=True,
    )


def _build_routine_run(
    *,
    definition: RoutineDefinition,
    state: RoutineState,
    error_code: str | None,
    policy_result: TelegramPolicyChainResult,
    hermes_os_contract: HermesOSRuntimeContract,
    caregiver_result: CaregiverTelegramMVPResult | None,
    policy_chain_routed: bool,
) -> RoutineRun:
    action_packet = caregiver_result.action_packet if caregiver_result and caregiver_result.action_packet else policy_result.action_packet
    delivery = LocalRoutineDelivery(
        delivery_id=_stable_id("routine_delivery", definition.routine_id, policy_result.user_id, state),
        channel="local_only",
        content=_delivery_content(definition=definition, state=state, policy_result=policy_result),
        automatic_delivery_authorized=False,
        live_telegram_send_authorized=False,
        external_side_effect_authorized=False,
        caregiver_send_authorized=False,
    )
    return RoutineRun(
        run_id=_stable_id("routine_run", definition.routine_id, policy_result.user_id, state),
        stage=ROUTINE_EXECUTION_STAGE,
        definition=definition,
        state=state,
        preflight=RoutinePreflight(
            wake_allowed=definition.wake_signal_present,
            budget_allowed=definition.budget_preflight_allowed,
            explicit_user_approved=definition.explicit_user_approved,
            manual_start_required=definition.manual_start_required,
            policy_chain_routed=policy_chain_routed,
        ),
        policy_result=policy_result,
        hermes_os_contract=hermes_os_contract,
        task_run_record=hermes_os_contract.task_run_record,
        bounded_memory_projection=_bounded_routine_memory_projection(policy_result),
        delivery=delivery,
        action_packet=action_packet,
        caregiver_result=caregiver_result,
        audit_trail=_audit_trail(
            definition=definition,
            state=state,
            policy_result=policy_result,
            action_packet=action_packet,
            error_code=error_code,
            policy_chain_routed=policy_chain_routed,
        ),
        error_code=error_code,
        live_scheduler_authorized=False,
        live_cron_authorized=False,
        live_telegram_send_authorized=False,
        external_side_effect_authorized=False,
        automatic_caregiver_alert_authorized=False,
        medical_decision_authorized=False,
        hidden_escalation_authorized=False,
    )


def serialize_routine_run(run: RoutineRun) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "stage": run.stage,
        "state": run.state,
        "routine_definition": {
            "routine_id": run.definition.routine_id,
            "label": run.definition.label,
            "kind": run.definition.kind,
            "explicit_user_approved": run.definition.explicit_user_approved,
            "manual_start_required": run.definition.manual_start_required,
            "live_schedule_authorized": run.definition.live_schedule_authorized,
            "live_delivery_authorized": run.definition.live_delivery_authorized,
        },
        "preflight": {
            "wake_allowed": run.preflight.wake_allowed,
            "budget_allowed": run.preflight.budget_allowed,
            "policy_chain_routed": run.preflight.policy_chain_routed,
        },
        "policy_trace": [decision.policy for decision in run.policy_result.policy_trace],
        "policy_trace_complete": run.hermes_os_contract.policy_trace.complete,
        "task_run_record": {
            "packet_type": run.task_run_record.packet_type,
            "stage": run.task_run_record.stage,
            "status": run.task_run_record.status,
            "hermes_adapter_called": run.task_run_record.hermes_adapter_called,
            "cost_preflight_decision": run.task_run_record.cost_preflight_decision,
            "selected_model_id": run.task_run_record.selected_model_id,
            "network_call": run.task_run_record.network_call,
            "external_side_effect": run.task_run_record.external_side_effect,
        },
        "bounded_memory_projection": [
            {"memory_id": item.memory_id, "memory_type": item.memory_type, "content": item.content}
            for item in run.bounded_memory_projection
        ],
        "delivery": {
            "delivery_id": run.delivery.delivery_id,
            "channel": run.delivery.channel,
            "content": run.delivery.content,
            "automatic_delivery_authorized": run.delivery.automatic_delivery_authorized,
            "live_telegram_send_authorized": run.delivery.live_telegram_send_authorized,
            "external_side_effect_authorized": run.delivery.external_side_effect_authorized,
            "caregiver_send_authorized": run.delivery.caregiver_send_authorized,
        },
        "action_packet": None
        if run.action_packet is None
        else {
            "packet_id": run.action_packet.packet_id,
            "action_class": run.action_packet.action_class,
            "decision": run.action_packet.decision,
            "external_effect_authorized": run.action_packet.external_effect_authorized,
        },
        "caregiver_compatible": run.caregiver_result is not None,
        "audit_trail": [{"event": event.event, "detail": event.detail} for event in run.audit_trail],
        "error_code": run.error_code,
        "local_response": {
            "live_scheduler": False,
            "live_cron": False,
            "telegram_send": False,
            "external_side_effect": False,
            "automatic_caregiver_alert": False,
        },
    }


def _preflight_stop(
    *,
    definition: RoutineDefinition,
    force_failure: bool,
) -> tuple[RoutineState, str] | None:
    if force_failure:
        return "failed", "routine_local_failure"
    if not definition.explicit_user_approved or not definition.manual_start_required:
        return "blocked", "routine_silent_execution_blocked"
    if not definition.wake_signal_present:
        return "skipped", "routine_wake_gate_skipped"
    if not definition.budget_preflight_allowed:
        return "blocked", "routine_budget_preflight_blocked"
    return None


def _state_for_policy_result(
    *,
    policy_result: TelegramPolicyChainResult,
    caregiver_result: CaregiverTelegramMVPResult | None,
) -> tuple[RoutineState, str | None]:
    if policy_result.cost_preflight is not None and policy_result.cost_preflight.confirmation_required:
        return "needs_confirmation", "routine_cost_confirmation_required"
    if policy_result.action_packet is not None or (caregiver_result is not None and caregiver_result.action_packet is not None):
        return "needs_confirmation", "routine_action_packet_required"
    if not policy_result.ok or not (caregiver_result.ok if caregiver_result is not None else True):
        return "blocked", policy_result.error_code or (caregiver_result.error_code if caregiver_result else None)
    return "completed", None


def _preflight_stopped_policy_result(
    *,
    update: dict,
    state: RoutineState,
    error_code: str,
) -> TelegramPolicyChainResult:
    message = update.get("message", {}) if isinstance(update, dict) else {}
    chat = message.get("chat", {}) if isinstance(message, dict) else {}
    sender = message.get("from", {}) if isinstance(message, dict) else {}
    chat_id = chat.get("id") if isinstance(chat.get("id"), int) else None
    user_id = sender.get("id") if isinstance(sender.get("id"), int) else None
    decision = PolicyDecision(
        policy="routine_preflight_98p",
        decision="STOPPED",
        reason=error_code,
        metadata={"routine_state": state},
    )
    skipped_tool_authority = PolicyDecision(
        policy="routine_preflight_98p",
        decision="SKIPPED",
        reason="Routine preflight stopped execution before the 95P tool-authority policy.",
        metadata={"routine_state": state, "action_class": "ROUTE"},
    )
    memory_context = MemoryContextBlock(
        packet_type="MemoryContextBlock",
        status="PREFLIGHT_STOPPED_LOCAL_AUDIT",
        stage=ROUTINE_EXECUTION_STAGE,
        source_of_truth="Roboticxs Memory Center",
        runtime_target="none_preflight_stopped",
        projection_policy_id="routine_preflight_no_projection_v0_1",
        request_scope="preflight_stopped",
        active_skill_id="none",
        projections=(),
        tool_action_authorization=False,
        permission_expansion_authorized=False,
    )
    hermes_adapter = HermesGatewayAdapterStubResult(
        called=False,
        status="preflight_stopped",
        response_text="Routine stopped by local preflight before policy-chain or Hermes adapter execution.",
        request_text=None,
        memory_projection_count=0,
    )
    return TelegramPolicyChainResult(
        ok=False,
        stage=ROUTINE_EXECUTION_STAGE,
        chat_id=chat_id,
        user_id=user_id,
        response_text=hermes_adapter.response_text,
        command_policy=decision,
        skill_scope_policy=decision,
        tool_authority_policy=skipped_tool_authority,
        memory_context=memory_context,
        cost_preflight=None,
        cost_confirmation=None,
        action_packet=None,
        hermes_adapter=hermes_adapter,
        policy_trace=(decision,),
        local_response={
            "network_call": False,
            "policy_chain_routed": False,
            "hermes_adapter_called": False,
            "external_side_effect": False,
        },
        error_code=error_code,
    )


def _bounded_routine_memory_projection(policy_result: TelegramPolicyChainResult) -> tuple[MemoryProjection, ...]:
    return tuple(
        projection
        for projection in policy_result.memory_context.projections[:2]
        if projection.memory_type not in SENSITIVE_MEMORY_TYPES and "owner private" not in projection.content.lower()
    )


def _delivery_content(
    *,
    definition: RoutineDefinition,
    state: RoutineState,
    policy_result: TelegramPolicyChainResult,
) -> str:
    if state == "completed":
        return f"Local routine completed: {definition.label}."
    if state == "skipped":
        return f"Local routine skipped by wake gate: {definition.label}."
    if state == "needs_confirmation":
        return f"Local routine needs approval before any external action: {definition.label}."
    if state == "failed":
        return f"Local routine failed and was recorded for audit: {definition.label}."
    if state == "blocked":
        return f"Local routine blocked: {policy_result.error_code or definition.label}."
    return f"Local routine state {state}: {definition.label}."


def _audit_trail(
    *,
    definition: RoutineDefinition,
    state: RoutineState,
    policy_result: TelegramPolicyChainResult,
    action_packet: LocalActionPacket | None,
    error_code: str | None,
    policy_chain_routed: bool,
) -> tuple[RoutineAuditEvent, ...]:
    events = [
        RoutineAuditEvent("routine_defined", definition.routine_id),
        RoutineAuditEvent(
            "policy_chain_routed" if policy_chain_routed else "policy_chain_skipped",
            ",".join(decision.policy for decision in policy_result.policy_trace),
        ),
        RoutineAuditEvent("wake_preflight", "allow" if definition.wake_signal_present else "skip"),
        RoutineAuditEvent("budget_preflight", "allow" if definition.budget_preflight_allowed else "block_placeholder"),
        RoutineAuditEvent(
            "cost_preflight",
            "not_run" if policy_result.cost_preflight is None else policy_result.cost_preflight.decision,
        ),
        RoutineAuditEvent("state_selected", state),
    ]
    if action_packet is not None:
        events.append(RoutineAuditEvent("action_packet_required", action_packet.packet_id))
    if error_code is not None:
        events.append(RoutineAuditEvent("error_code", error_code))
    return tuple(events)


def _stable_id(prefix: str, *parts: object) -> str:
    raw = ":".join(str(part) for part in parts)
    return f"{prefix}_{uuid5(NAMESPACE_URL, raw).hex[:12]}"
