from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.caregiver_relay import (
    CaregiverRelayPacket,
    CaregiverRelayRequest,
    build_caregiver_relay_packet,
)


GuidedRoutineType = Literal[
    "HEARING_AID_ROUTINE",
    "HYGIENE_ROUTINE",
    "HYDRATION_OR_MEAL_ROUTINE",
    "APPOINTMENT_PREPARATION_ROUTINE",
    "HOUSEHOLD_SIMPLE_ROUTINE",
    "CAREGIVER_APPROVED_CUSTOM_ROUTINE",
    "MEDICATION_ADJACENT_CHECKLIST",
    "BLOCKED_MEDICAL_ROUTINE",
    "BLOCKED_SURVEILLANCE_ROUTINE",
    "BLOCKED_EMERGENCY_ROUTINE",
]

GuidedRoutineDecision = Literal[
    "PREPARE_ROUTINE_PACKET",
    "PREPARE_WITH_CAREGIVER_CONFIRMATION",
    "PREPARE_MEDICATION_ADJACENT_CHECKLIST",
    "DEFER_TO_CAREGIVER_RELAY",
    "BLOCK_MEDICAL_DECISION",
    "BLOCK_SURVEILLANCE",
    "BLOCK_EMERGENCY",
    "BLOCK_EXTERNAL_ACTION",
]

RoutineStepResponseType = Literal[
    "ACK_ONLY",
    "YES_NO",
    "CAREGIVER_CONFIRMATION",
    "FREE_TEXT_NOTE",
    "NO_RESPONSE_REQUIRED",
]

RoutineCompletionClaim = Literal[
    "NOT_COMPLETED",
    "USER_REPORTED_ONLY",
    "CAREGIVER_REPORTED_ONLY",
    "CAREGIVER_REPORTED_OR_USER_REPORTED_ONLY",
    "NOT_CLINICAL_FACT",
]

RoutineSensitivity = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "SENSITIVE",
]


@dataclass(frozen=True, slots=True)
class GuidedRoutineRequest:
    raw_text: str
    routine_hint: str
    intended_user: str
    caregiver_context_present: bool = False
    caregiver_approved: bool = False
    medication_adjacent: bool = False
    medical_decision_requested: bool = False
    dosage_or_schedule_requested: bool = False
    ingestion_verification_requested: bool = False
    emergency_like: bool = False
    surveillance_requested: bool = False
    external_action_requested: bool = False
    routine_execution_requested: bool = False
    sensitive_context_present: bool = False
    source_robot_id: str = "local_robot"
    target_context: str = "HUMAN_CAREGIVER_REVIEW"
    caregiver_id: str | None = None
    routine_ref: str | None = None
    source_event_ref: str | None = None
    custom_steps: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GuidedRoutineStep:
    step_id: str
    step_number: int
    instruction: str
    expected_response_type: RoutineStepResponseType
    requires_user_ack: bool
    requires_caregiver_confirmation: bool
    can_skip: bool
    safety_note: str | None
    blocked_if: str | None


@dataclass(frozen=True, slots=True)
class GuidedRoutinePacket:
    packet_id: str
    routine_type: GuidedRoutineType
    routine_decision: GuidedRoutineDecision
    title: str
    purpose: str
    intended_user: str
    caregiver_visibility: str
    steps: tuple[GuidedRoutineStep, ...]
    current_step_index: int
    max_steps: int
    requires_caregiver_confirmation: bool
    requires_caregiver_supervision: bool
    medication_adjacent: bool
    sensitivity_level: RoutineSensitivity
    session_only_progress: bool
    external_send_authorized: bool
    background_reminder_authorized: bool
    medical_decision_authorized: bool
    dosage_decision_authorized: bool
    medication_schedule_authorized: bool
    ingestion_verification_authorized: bool
    emergency_claim_authorized: bool
    surveillance_authorized: bool
    routine_completion_claim: RoutineCompletionClaim
    handoff_relay_packet: CaregiverRelayPacket | None
    blocked_reason: str | None
    future_stage_required: str | None
    created_at: str

    def __post_init__(self) -> None:
        if not self.session_only_progress:
            raise ValueError("69P routine progress must remain session-only.")
        if self.external_send_authorized:
            raise ValueError("69P packets cannot authorize external sending.")
        if self.background_reminder_authorized:
            raise ValueError("69P packets cannot authorize background reminders.")
        if self.medical_decision_authorized:
            raise ValueError("69P packets cannot authorize medical decisions.")
        if self.dosage_decision_authorized:
            raise ValueError("69P packets cannot authorize dosage decisions.")
        if self.medication_schedule_authorized:
            raise ValueError("69P packets cannot authorize medication schedule decisions.")
        if self.ingestion_verification_authorized:
            raise ValueError("69P packets cannot authorize ingestion verification.")
        if self.emergency_claim_authorized:
            raise ValueError("69P packets cannot authorize emergency handling claims.")
        if self.surveillance_authorized:
            raise ValueError("69P packets cannot authorize surveillance.")


def classify_guided_routine_request(request: GuidedRoutineRequest) -> GuidedRoutineDecision:
    if request.external_action_requested:
        return "BLOCK_EXTERNAL_ACTION"
    if request.surveillance_requested:
        return "BLOCK_SURVEILLANCE"
    if request.emergency_like:
        return "BLOCK_EMERGENCY"
    if (
        request.medical_decision_requested
        or request.dosage_or_schedule_requested
        or request.ingestion_verification_requested
    ):
        return "BLOCK_MEDICAL_DECISION"
    if request.medication_adjacent or request.routine_hint.lower().strip() in {"pillbox", "medication"}:
        return "PREPARE_MEDICATION_ADJACENT_CHECKLIST"
    if request.caregiver_context_present and not request.caregiver_approved:
        return "PREPARE_WITH_CAREGIVER_CONFIRMATION"
    return "PREPARE_ROUTINE_PACKET"


def build_guided_routine_packet(request: GuidedRoutineRequest) -> GuidedRoutinePacket:
    decision = classify_guided_routine_request(request)
    routine_type = _routine_type_for_request(request, decision)
    steps = tuple(build_default_steps_for_routine(routine_type, request))
    requires_confirmation = _requires_caregiver_confirmation(request, decision)
    requires_supervision = decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST"

    return GuidedRoutinePacket(
        packet_id=f"guided_routine_{uuid4().hex}",
        routine_type=routine_type,
        routine_decision=decision,
        title=_title_for_routine(routine_type),
        purpose=_purpose_for_routine(routine_type, decision),
        intended_user=request.intended_user,
        caregiver_visibility=_caregiver_visibility(request, decision),
        steps=steps,
        current_step_index=0,
        max_steps=len(steps),
        requires_caregiver_confirmation=requires_confirmation,
        requires_caregiver_supervision=requires_supervision,
        medication_adjacent=decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST",
        sensitivity_level=_sensitivity_for_request(request, decision),
        session_only_progress=True,
        external_send_authorized=False,
        background_reminder_authorized=False,
        medical_decision_authorized=False,
        dosage_decision_authorized=False,
        medication_schedule_authorized=False,
        ingestion_verification_authorized=False,
        emergency_claim_authorized=False,
        surveillance_authorized=False,
        routine_completion_claim=_completion_claim_for_decision(decision),
        handoff_relay_packet=_handoff_packet_for_request(request, decision),
        blocked_reason=_blocked_reason_for_decision(decision),
        future_stage_required=_future_stage_for_decision(decision),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def build_default_steps_for_routine(
    routine_type: GuidedRoutineType,
    request: GuidedRoutineRequest | None = None,
) -> list[GuidedRoutineStep]:
    if routine_type == "HEARING_AID_ROUTINE":
        return _steps(
            [
                "Please find your hearing aids.",
                "Check that they are facing the right direction.",
                "Put on the left hearing aid.",
                "Put on the right hearing aid.",
                "Tell me when you are done.",
            ]
        )
    if routine_type == "HYGIENE_ROUTINE":
        return _steps(
            [
                "Please gather what you need.",
                "Do one small hygiene step now.",
                "Put the item back in its usual place.",
                "Tell me when you are done.",
            ]
        )
    if routine_type == "HYDRATION_OR_MEAL_ROUTINE":
        return _steps(
            [
                "Please take your glass or meal.",
                "Take one small sip or bite.",
                "Put it somewhere safe.",
                "Tell me when you are done.",
            ]
        )
    if routine_type == "APPOINTMENT_PREPARATION_ROUTINE":
        return _steps(
            [
                "Please check the appointment note.",
                "Put the needed item in one place.",
                "Ask your caregiver if anything is missing.",
                "Tell me when you are ready.",
            ]
        )
    if routine_type == "HOUSEHOLD_SIMPLE_ROUTINE":
        return _steps(
            [
                "Let's do one small step.",
                "Pick up the item in front of you.",
                "Put it in its usual place.",
                "Tell me when you are done.",
            ]
        )
    if routine_type == "CAREGIVER_APPROVED_CUSTOM_ROUTINE":
        custom_steps = request.custom_steps if request is not None else ()
        instructions = custom_steps or (
            "Please do the first caregiver-approved step.",
            "Pause and check that it feels clear.",
            "Tell me when you are done.",
        )
        return _steps(instructions)
    if routine_type == "MEDICATION_ADJACENT_CHECKLIST":
        return _steps(
            [
                "A caregiver must confirm the approved medication list is present.",
                "A caregiver must confirm the pillbox or container labels.",
                "Follow the caregiver-approved list only.",
                "Stop and ask the caregiver if anything is unclear.",
            ],
            expected_response_type="CAREGIVER_CONFIRMATION",
            requires_caregiver_confirmation=True,
            can_skip=False,
        )
    return []


def requires_caregiver_handoff(request: GuidedRoutineRequest) -> bool:
    decision = classify_guided_routine_request(request)
    return (
        request.medication_adjacent
        or (request.caregiver_context_present and not request.caregiver_approved)
        or request.sensitive_context_present
        or request.emergency_like
        or decision in {"PREPARE_WITH_CAREGIVER_CONFIRMATION", "PREPARE_MEDICATION_ADJACENT_CHECKLIST", "BLOCK_EMERGENCY"}
    )


def _steps(
    instructions: tuple[str, ...] | list[str],
    expected_response_type: RoutineStepResponseType = "ACK_ONLY",
    requires_caregiver_confirmation: bool = False,
    can_skip: bool = True,
) -> list[GuidedRoutineStep]:
    return [
        GuidedRoutineStep(
            step_id=f"step_{index}",
            step_number=index,
            instruction=instruction,
            expected_response_type=expected_response_type,
            requires_user_ack=expected_response_type != "NO_RESPONSE_REQUIRED",
            requires_caregiver_confirmation=requires_caregiver_confirmation,
            can_skip=can_skip,
            safety_note=None,
            blocked_if="unclear_or_distressing" if requires_caregiver_confirmation else None,
        )
        for index, instruction in enumerate(instructions, start=1)
    ]


def _routine_type_for_request(
    request: GuidedRoutineRequest,
    decision: GuidedRoutineDecision,
) -> GuidedRoutineType:
    if decision == "BLOCK_MEDICAL_DECISION":
        return "BLOCKED_MEDICAL_ROUTINE"
    if decision in {"BLOCK_SURVEILLANCE", "BLOCK_EXTERNAL_ACTION"}:
        return "BLOCKED_SURVEILLANCE_ROUTINE"
    if decision == "BLOCK_EMERGENCY":
        return "BLOCKED_EMERGENCY_ROUTINE"
    if decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST":
        return "MEDICATION_ADJACENT_CHECKLIST"

    hint = request.routine_hint.lower().strip()
    if hint in {"hearing_aid", "hearing_aids", "hearing"}:
        return "HEARING_AID_ROUTINE"
    if hint == "hygiene":
        return "HYGIENE_ROUTINE"
    if hint in {"hydration", "meal", "water", "food"}:
        return "HYDRATION_OR_MEAL_ROUTINE"
    if hint == "appointment":
        return "APPOINTMENT_PREPARATION_ROUTINE"
    if hint == "household":
        return "HOUSEHOLD_SIMPLE_ROUTINE"
    if hint in {"pillbox", "medication"}:
        return "MEDICATION_ADJACENT_CHECKLIST"
    return "CAREGIVER_APPROVED_CUSTOM_ROUTINE"


def _title_for_routine(routine_type: GuidedRoutineType) -> str:
    titles: dict[GuidedRoutineType, str] = {
        "HEARING_AID_ROUTINE": "Hearing Aid Routine",
        "HYGIENE_ROUTINE": "Hygiene Routine",
        "HYDRATION_OR_MEAL_ROUTINE": "Hydration or Meal Routine",
        "APPOINTMENT_PREPARATION_ROUTINE": "Appointment Preparation Routine",
        "HOUSEHOLD_SIMPLE_ROUTINE": "Simple Household Routine",
        "CAREGIVER_APPROVED_CUSTOM_ROUTINE": "Caregiver-Approved Routine",
        "MEDICATION_ADJACENT_CHECKLIST": "Medication-Adjacent Checklist",
        "BLOCKED_MEDICAL_ROUTINE": "Blocked Medical Routine",
        "BLOCKED_SURVEILLANCE_ROUTINE": "Blocked Surveillance Routine",
        "BLOCKED_EMERGENCY_ROUTINE": "Blocked Emergency Routine",
    }
    return titles[routine_type]


def _purpose_for_routine(routine_type: GuidedRoutineType, decision: GuidedRoutineDecision) -> str:
    if decision.startswith("BLOCK_"):
        return "Explain why this routine cannot be prepared in 69P."
    if routine_type == "MEDICATION_ADJACENT_CHECKLIST":
        return "Prepare a supervision-only checklist without medication authority."
    return "Prepare a short, respectful routine packet for one-step-at-a-time guidance."


def _caregiver_visibility(request: GuidedRoutineRequest, decision: GuidedRoutineDecision) -> str:
    if decision.startswith("BLOCK_"):
        return "blocked_notice_only"
    if requires_caregiver_handoff(request):
        return "human_caregiver_review_required"
    return "session_local_guidance"


def _sensitivity_for_request(
    request: GuidedRoutineRequest,
    decision: GuidedRoutineDecision,
) -> RoutineSensitivity:
    if decision in {"BLOCK_EMERGENCY", "BLOCK_MEDICAL_DECISION"}:
        return "SENSITIVE"
    if decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST" or request.sensitive_context_present:
        return "HIGH"
    if request.caregiver_context_present:
        return "MEDIUM"
    return "LOW"


def _requires_caregiver_confirmation(
    request: GuidedRoutineRequest,
    decision: GuidedRoutineDecision,
) -> bool:
    return (
        decision in {"PREPARE_MEDICATION_ADJACENT_CHECKLIST", "PREPARE_WITH_CAREGIVER_CONFIRMATION"}
        or request.sensitive_context_present
    )


def _completion_claim_for_decision(decision: GuidedRoutineDecision) -> RoutineCompletionClaim:
    if decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST":
        return "CAREGIVER_REPORTED_OR_USER_REPORTED_ONLY"
    if decision.startswith("BLOCK_"):
        return "NOT_CLINICAL_FACT"
    return "USER_REPORTED_ONLY"


def _handoff_packet_for_request(
    request: GuidedRoutineRequest,
    decision: GuidedRoutineDecision,
) -> CaregiverRelayPacket | None:
    if not requires_caregiver_handoff(request):
        return None

    return build_caregiver_relay_packet(
        CaregiverRelayRequest(
            raw_text=request.raw_text,
            source_robot_id=request.source_robot_id,
            target_context="HUMAN_CAREGIVER_REVIEW",
            caregiver_context_present=request.caregiver_context_present,
            medication_adjacent=decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST",
            medical_decision_requested=decision == "BLOCK_MEDICAL_DECISION",
            emergency_like=decision == "BLOCK_EMERGENCY",
            surveillance_requested=decision == "BLOCK_SURVEILLANCE",
            external_action_requested=decision == "BLOCK_EXTERNAL_ACTION",
            routine_execution_requested=False,
            sensitive_context_present=request.sensitive_context_present,
            caregiver_id=request.caregiver_id,
            routine_ref=request.routine_ref,
            source_event_ref=request.source_event_ref,
        )
    )


def _blocked_reason_for_decision(decision: GuidedRoutineDecision) -> str | None:
    reasons: dict[GuidedRoutineDecision, str] = {
        "BLOCK_EXTERNAL_ACTION": "External sending, alerts, or third-party contact are outside 69P.",
        "BLOCK_SURVEILLANCE": "Continuous monitoring or hidden supervision is outside Roboticxs v0.",
        "BLOCK_EMERGENCY": "Emergency-like situations require human caregiver or emergency services.",
        "BLOCK_MEDICAL_DECISION": "Medication selection, dosage, schedule, or ingestion verification decisions are outside Roboticxs v0.",
    }
    return reasons.get(decision)


def _future_stage_for_decision(decision: GuidedRoutineDecision) -> str | None:
    if decision == "BLOCK_EXTERNAL_ACTION":
        return "future_explicit_external_action_authority"
    return None
