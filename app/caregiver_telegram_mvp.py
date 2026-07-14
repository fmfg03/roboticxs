from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from app.config import Settings
from app.guided_routines import (
    GuidedRoutinePacket,
    GuidedRoutineRequest,
    GuidedRoutineStep,
    build_guided_routine_packet,
)
from app.hermes_os_contract import HermesOSRuntimeContract, build_hermes_os_runtime_contract
from app.telegram_policy_chain import (
    LocalActionPacket,
    MemoryProjection,
    TelegramPolicyChainResult,
    run_telegram_policy_chain,
)


CAREGIVER_TELEGRAM_MVP_STAGE = "97P"
CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH = "/api/telegram/caregiver-mvp/webhook"

CaregiverActorRole = Literal["care_recipient", "caregiver", "owner_admin", "robot"]
CaregiverRoutineDecision = Literal[
    "GUIDE_STEP",
    "CONFIRM_STEP",
    "SAFE_REPEAT",
    "REFUSE_MEDICAL_DECISION",
    "ESCALATION_DRAFT_REQUIRED",
    "POLICY_BLOCKED",
]

MEDICAL_DECISION_TERMS = (
    "change medication",
    "change medicine",
    "alter medication",
    "alter medicine",
    "which pill",
    "which medication",
    "which medicine",
    "dosage",
    "dose",
    "missed dose",
    "double dose",
    "diagnose",
    "diagnosis",
    "treatment",
)
EMERGENCY_TERMS = ("emergency", "fell", "fall", "cannot get up", "can't get up", "chest pain", "not breathing")
CONFUSION_TERMS = ("confused", "repeat", "again", "unclear", "lost", "what step")
CONFIRMATION_TERMS = ("done", "yes", "completed", "ok", "okay", "listo")
SENSITIVE_MEMORY_TYPES = {"CREDENTIAL", "SECRET", "MEDICAL_DECISION", "OWNER_PRIVATE", "UNRELATED_OWNER_MEMORY"}


@dataclass(frozen=True, slots=True)
class CaregiverRoutineActor:
    actor_id: str
    role: CaregiverActorRole
    display_name: str
    telegram_user_id: int | None = None


@dataclass(frozen=True, slots=True)
class CaregiverRoutineActors:
    care_recipient: CaregiverRoutineActor
    caregiver: CaregiverRoutineActor
    owner_admin: CaregiverRoutineActor
    robot: CaregiverRoutineActor


@dataclass(frozen=True, slots=True)
class CaregiverRoutinePacket:
    packet_type: str
    stage: str
    packet_id: str
    routine_label: str
    actors: CaregiverRoutineActors
    routine_packet: GuidedRoutinePacket
    current_step: GuidedRoutineStep | None
    decision: CaregiverRoutineDecision
    response_text: str
    simple_confirmation_supported: bool
    missed_step_or_confusion_safe: bool
    escalation_draft: str | None
    escalation_target_actor_id: str | None
    escalation_requires_approval: bool
    automatic_caregiver_send_authorized: bool
    medical_decision_authorized: bool
    medication_change_authorized: bool
    emergency_monitoring_claim_authorized: bool
    sensitive_memory_expansion_authorized: bool
    live_delivery_authorized: bool

    def __post_init__(self) -> None:
        if self.automatic_caregiver_send_authorized:
            raise ValueError("97P cannot authorize automatic caregiver sends.")
        if self.medical_decision_authorized or self.medication_change_authorized:
            raise ValueError("97P cannot authorize medical decisions or medication changes.")
        if self.emergency_monitoring_claim_authorized:
            raise ValueError("97P cannot claim emergency monitoring.")
        if self.sensitive_memory_expansion_authorized or self.live_delivery_authorized:
            raise ValueError("97P cannot expand sensitive memory or authorize live delivery.")


@dataclass(frozen=True, slots=True)
class CaregiverTelegramMVPResult:
    ok: bool
    stage: str
    packet: CaregiverRoutinePacket
    policy_result: TelegramPolicyChainResult
    hermes_os_contract: HermesOSRuntimeContract
    action_packet: LocalActionPacket | None
    bounded_memory_projection: tuple[MemoryProjection, ...]
    policy_trace_complete: bool
    local_response: dict[str, object]
    error_code: str | None = None


def run_caregiver_telegram_mvp(
    *,
    update: dict,
    settings: Settings,
    session: Session,
    routine_label: str = "approved morning routine",
    current_step_index: int = 0,
) -> CaregiverTelegramMVPResult:
    policy_result = run_telegram_policy_chain(
        update=update,
        settings=settings,
        session=session,
        memory_actor_role="care_recipient",
        memory_target_scope="caregiver",
        memory_allowed_use="caregiver_context",
    )
    text = _extract_text(update)
    actors = _actors_from_policy_result(policy_result)
    routine_packet = build_guided_routine_packet(
        GuidedRoutineRequest(
            raw_text=text,
            routine_hint=_routine_hint(text),
            intended_user=actors.care_recipient.display_name,
            caregiver_approved=True,
            medication_adjacent="medication" in routine_label.lower() or "pill" in routine_label.lower(),
        )
    )
    decision = _routine_decision(text=text, policy_result=policy_result)
    current_step = _current_step(routine_packet, current_step_index)
    escalation_draft = _escalation_draft(decision=decision, text=text, actors=actors, routine_label=routine_label)
    action_packet = (
        LocalActionPacket(
            packet_id=_stable_id("ap_caregiver", policy_result.user_id, text, routine_label),
            action_class="SEND_EXTERNAL_MESSAGE",
            decision="ASK_CONFIRMATION",
            requested_text=text,
            final_user_visible_content=escalation_draft,
            confirmation_command=f"/approve {_stable_id('ap_caregiver', policy_result.user_id, text, routine_label)}",
            external_effect_authorized=False,
        )
        if escalation_draft is not None
        else policy_result.action_packet
    )
    packet = CaregiverRoutinePacket(
        packet_type="CaregiverRoutinePacket",
        stage=CAREGIVER_TELEGRAM_MVP_STAGE,
        packet_id=_stable_id("caregiver_routine", policy_result.user_id, text, routine_label),
        routine_label=routine_label,
        actors=actors,
        routine_packet=routine_packet,
        current_step=current_step,
        decision=decision,
        response_text=_response_text(decision=decision, current_step=current_step, routine_label=routine_label),
        simple_confirmation_supported=True,
        missed_step_or_confusion_safe=decision in {"SAFE_REPEAT", "ESCALATION_DRAFT_REQUIRED"},
        escalation_draft=escalation_draft,
        escalation_target_actor_id=actors.caregiver.actor_id if escalation_draft is not None else None,
        escalation_requires_approval=escalation_draft is not None,
        automatic_caregiver_send_authorized=False,
        medical_decision_authorized=False,
        medication_change_authorized=False,
        emergency_monitoring_claim_authorized=False,
        sensitive_memory_expansion_authorized=False,
        live_delivery_authorized=False,
    )
    hermes_os_contract = build_hermes_os_runtime_contract(
        policy_result=policy_result,
        robot_id=actors.robot.actor_id,
        routine_requested=True,
    )
    return CaregiverTelegramMVPResult(
        ok=policy_result.ok and decision not in {"REFUSE_MEDICAL_DECISION", "POLICY_BLOCKED"},
        stage=CAREGIVER_TELEGRAM_MVP_STAGE,
        packet=packet,
        policy_result=policy_result,
        hermes_os_contract=hermes_os_contract,
        action_packet=action_packet,
        bounded_memory_projection=_redacted_projection(policy_result),
        policy_trace_complete=hermes_os_contract.policy_trace.complete,
        local_response={
            "network_call": False,
            "telegram_send": False,
            "live_hermes_gateway_started": False,
            "live_cron_scheduled": False,
            "connector_activation": False,
            "external_side_effect": False,
            "hermes_adapter_called": policy_result.hermes_adapter.called,
            "action_packet_required": action_packet is not None,
            "automatic_caregiver_send": False,
        },
        error_code=_error_code(decision, policy_result),
    )


def serialize_caregiver_telegram_mvp_result(result: CaregiverTelegramMVPResult) -> dict[str, object]:
    packet = result.packet
    return {
        "ok": result.ok,
        "stage": result.stage,
        "error_code": result.error_code,
        "packet": {
            "packet_type": packet.packet_type,
            "stage": packet.stage,
            "packet_id": packet.packet_id,
            "routine_label": packet.routine_label,
            "actors": {
                "care_recipient": asdict(packet.actors.care_recipient),
                "caregiver": asdict(packet.actors.caregiver),
                "owner_admin": asdict(packet.actors.owner_admin),
                "robot": asdict(packet.actors.robot),
            },
            "routine_packet_id": packet.routine_packet.packet_id,
            "current_step": None
            if packet.current_step is None
            else {
                "step_id": packet.current_step.step_id,
                "step_number": packet.current_step.step_number,
                "instruction": packet.current_step.instruction,
                "expected_response_type": packet.current_step.expected_response_type,
            },
            "decision": packet.decision,
            "response_text": packet.response_text,
            "escalation_draft": packet.escalation_draft,
            "escalation_target_actor_id": packet.escalation_target_actor_id,
            "escalation_requires_approval": packet.escalation_requires_approval,
            "automatic_caregiver_send_authorized": packet.automatic_caregiver_send_authorized,
            "medical_decision_authorized": packet.medical_decision_authorized,
            "medication_change_authorized": packet.medication_change_authorized,
            "emergency_monitoring_claim_authorized": packet.emergency_monitoring_claim_authorized,
            "sensitive_memory_expansion_authorized": packet.sensitive_memory_expansion_authorized,
            "live_delivery_authorized": packet.live_delivery_authorized,
        },
        "action_packet": None
        if result.action_packet is None
        else {
            "packet_id": result.action_packet.packet_id,
            "action_class": result.action_packet.action_class,
            "decision": result.action_packet.decision,
            "final_user_visible_content": result.action_packet.final_user_visible_content,
            "external_effect_authorized": result.action_packet.external_effect_authorized,
        },
        "bounded_memory_projection": [
            {"memory_id": item.memory_id, "memory_type": item.memory_type, "content": item.content}
            for item in result.bounded_memory_projection
        ],
        "policy_trace": [decision.policy for decision in result.policy_result.policy_trace],
        "policy_trace_complete": result.policy_trace_complete,
        "task_run_record": {
            "packet_type": result.hermes_os_contract.task_run_record.packet_type,
            "stage": result.hermes_os_contract.task_run_record.stage,
            "status": result.hermes_os_contract.task_run_record.status,
            "hermes_adapter_called": result.hermes_os_contract.task_run_record.hermes_adapter_called,
            "network_call": result.hermes_os_contract.task_run_record.network_call,
            "external_side_effect": result.hermes_os_contract.task_run_record.external_side_effect,
        },
        "local_response": result.local_response,
    }


def _routine_decision(*, text: str, policy_result: TelegramPolicyChainResult) -> CaregiverRoutineDecision:
    normalized = text.lower()
    if policy_result.command_policy.decision == "BLOCK_CONSUMER" or policy_result.skill_scope_policy.decision == "BLOCK":
        return "REFUSE_MEDICAL_DECISION" if _contains_any(normalized, MEDICAL_DECISION_TERMS) else "POLICY_BLOCKED"
    if _contains_any(normalized, EMERGENCY_TERMS):
        return "ESCALATION_DRAFT_REQUIRED"
    if _contains_any(normalized, CONFUSION_TERMS):
        return "SAFE_REPEAT"
    if normalized.strip() in CONFIRMATION_TERMS or _contains_any(normalized, ("done", "completed", "listo")):
        return "CONFIRM_STEP"
    return "GUIDE_STEP"


def _response_text(
    *,
    decision: CaregiverRoutineDecision,
    current_step: GuidedRoutineStep | None,
    routine_label: str,
) -> str:
    if decision == "REFUSE_MEDICAL_DECISION":
        return "I cannot make medical decisions or change medication. Please ask the caregiver or a medical professional."
    if decision == "ESCALATION_DRAFT_REQUIRED":
        return "This may need urgent human help. Contact local emergency services or a medical professional if there is immediate risk."
    if decision == "SAFE_REPEAT":
        instruction = current_step.instruction if current_step is not None else "Pause and ask the caregiver for help."
        return f"No problem. Let's pause and repeat one safe step: {instruction}"
    if decision == "CONFIRM_STEP":
        return "Thanks. I recorded that as a simple local confirmation only."
    if decision == "POLICY_BLOCKED":
        return "That request is blocked by the local Roboticxs policy chain."
    instruction = current_step.instruction if current_step is not None else "Please ask the caregiver for the next approved step."
    return f"{routine_label}: {instruction}"


def _escalation_draft(
    *,
    decision: CaregiverRoutineDecision,
    text: str,
    actors: CaregiverRoutineActors,
    routine_label: str,
) -> str | None:
    if decision == "ESCALATION_DRAFT_REQUIRED":
        return (
            f"Draft for {actors.caregiver.display_name}: {actors.care_recipient.display_name} may need help during "
            f"{routine_label}. Reported message: {_redact_text(text)}. If there is immediate danger, contact local "
            "emergency services or a medical professional. Roboticxs is not emergency monitoring."
        )
    if decision == "SAFE_REPEAT":
        return (
            f"Draft for {actors.caregiver.display_name}: {actors.care_recipient.display_name} seemed confused during "
            f"{routine_label}. Please review when available. No message was sent automatically."
        )
    return None


def _actors_from_policy_result(policy_result: TelegramPolicyChainResult) -> CaregiverRoutineActors:
    user_id = str(policy_result.user_id or "unknown")
    return CaregiverRoutineActors(
        care_recipient=CaregiverRoutineActor(
            actor_id=f"care_recipient_{user_id}",
            role="care_recipient",
            display_name="care recipient",
            telegram_user_id=policy_result.user_id,
        ),
        caregiver=CaregiverRoutineActor(
            actor_id=f"approved_caregiver_{user_id}",
            role="caregiver",
            display_name="approved caregiver",
        ),
        owner_admin=CaregiverRoutineActor(
            actor_id=f"owner_admin_{user_id}",
            role="owner_admin",
            display_name="owner/admin",
        ),
        robot=CaregiverRoutineActor(actor_id="local_robot", role="robot", display_name="Roboticxs"),
    )


def _current_step(packet: GuidedRoutinePacket, current_step_index: int) -> GuidedRoutineStep | None:
    if not packet.steps:
        return None
    bounded_index = max(0, min(current_step_index, len(packet.steps) - 1))
    return packet.steps[bounded_index]


def _redacted_projection(policy_result: TelegramPolicyChainResult) -> tuple[MemoryProjection, ...]:
    return tuple(
        projection
        for projection in policy_result.memory_context.projections
        if projection.memory_type not in SENSITIVE_MEMORY_TYPES and "owner private" not in projection.content.lower()
    )


def _routine_hint(text: str) -> str:
    normalized = text.lower()
    if _contains_any(normalized, ("water", "drink", "meal", "food")):
        return "hydration"
    if _contains_any(normalized, ("pill", "medication", "medicine")):
        return "pillbox"
    if _contains_any(normalized, ("wash", "brush", "hygiene")):
        return "hygiene"
    return "hearing_aid"


def _extract_text(update: dict) -> str:
    message = update.get("message", {})
    text = message.get("text")
    return text if isinstance(text, str) else ""


def _redact_text(text: str) -> str:
    if len(text) <= 120:
        return text
    return text[:117] + "..."


def _error_code(decision: CaregiverRoutineDecision, policy_result: TelegramPolicyChainResult) -> str | None:
    if decision == "REFUSE_MEDICAL_DECISION":
        return "caregiver_medical_decision_refused"
    if decision == "POLICY_BLOCKED":
        return policy_result.error_code or "caregiver_policy_blocked"
    return None


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _stable_id(prefix: str, *parts: object) -> str:
    raw = ":".join(str(part) for part in parts)
    return f"{prefix}_{uuid5(NAMESPACE_URL, raw).hex[:12]}"
