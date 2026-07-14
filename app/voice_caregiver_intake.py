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
from app.guided_routines import (
    GuidedRoutinePacket,
    GuidedRoutineRequest,
    build_guided_routine_packet,
)


VoiceCaregiverSourceChannel = Literal[
    "VOICE_TRANSCRIPT_STUB",
    "USER_PROVIDED_TRANSCRIPT",
    "TEST_FIXTURE_TRANSCRIPT",
]

TranscriptConfidence = Literal[
    "UNKNOWN",
    "LOW",
    "MEDIUM",
    "HIGH",
]

VoiceCaregiverIntakeDecision = Literal[
    "ASK_CLARIFICATION",
    "ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW",
    "PREPARE_ROUTINE_PACKET_REVIEW",
    "PREPARE_MEDICATION_ADJACENT_REVIEW",
    "PREPARE_CAREGIVER_RELAY_REVIEW",
    "ESCALATE_TO_HUMAN_CAREGIVER",
    "BLOCK_MEDICAL_DECISION",
    "BLOCK_SURVEILLANCE",
    "BLOCK_EXTERNAL_ACTION",
    "DISCARD_OR_NO_ACTION",
]

VoiceCaregiverSensitivity = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "SENSITIVE",
]


ALLOWED_SOURCE_CHANNELS = frozenset(
    {
        "VOICE_TRANSCRIPT_STUB",
        "USER_PROVIDED_TRANSCRIPT",
        "TEST_FIXTURE_TRANSCRIPT",
    }
)
BLOCKED_SOURCE_CHANNELS = frozenset(
    {
        "TELEGRAM_VOICE_FILE",
        "AUDIO_UPLOAD",
        "LIVE_MICROPHONE",
        "BACKGROUND_AUDIO_STREAM",
        "EXTERNAL_ASR_RESULT_AUTO_ACCEPTED",
    }
)
ALLOWED_CONFIDENCE_VALUES = frozenset({"UNKNOWN", "LOW", "MEDIUM", "HIGH"})


@dataclass(frozen=True, slots=True)
class VoiceCaregiverIntakeRequest:
    source_channel: VoiceCaregiverSourceChannel
    transcript_text: str
    transcript_confidence: TranscriptConfidence
    language_detected: str
    caregiver_context_present: bool = False
    caregiver_approved_context: bool = False
    routine_intent_present: bool = False
    medication_adjacent: bool = False
    medical_decision_requested: bool = False
    dosage_or_schedule_requested: bool = False
    ingestion_verification_requested: bool = False
    emergency_like: bool = False
    surveillance_requested: bool = False
    external_action_requested: bool = False
    sensitive_context_present: bool = False
    source_robot_id: str = "local_robot"
    target_context: str = "HUMAN_CAREGIVER_REVIEW"
    intended_user: str = "caregiver_review_subject"
    caregiver_id: str | None = None
    routine_hint: str | None = None
    source_event_ref: str | None = None
    code_switching_detected: bool = False

    def __post_init__(self) -> None:
        if self.source_channel in BLOCKED_SOURCE_CHANNELS:
            raise ValueError(f"{self.source_channel} is not an allowed 71P transcript source channel.")
        if self.source_channel not in ALLOWED_SOURCE_CHANNELS:
            raise ValueError(f"Unknown voice caregiver transcript source channel: {self.source_channel}.")
        if self.transcript_confidence not in ALLOWED_CONFIDENCE_VALUES:
            raise ValueError(f"Unknown transcript confidence: {self.transcript_confidence}.")
        if not isinstance(self.transcript_text, str):
            raise TypeError("71P accepts transcript text only.")
        if _looks_like_audio_reference(self.transcript_text):
            raise ValueError("71P accepts transcript stubs only; audio references are outside scope.")


@dataclass(frozen=True, slots=True)
class VoiceCaregiverIntakePacket:
    packet_id: str
    source_channel: VoiceCaregiverSourceChannel
    transcript_text: str
    transcript_confidence: TranscriptConfidence
    language_detected: str
    code_switching_detected: bool
    caregiver_context_detected: bool
    routine_intent_detected: bool
    medication_adjacent_detected: bool
    medical_decision_requested: bool
    dosage_or_schedule_requested: bool
    ingestion_verification_requested: bool
    emergency_like_detected: bool
    surveillance_requested: bool
    external_action_requested: bool
    sensitive_context_detected: bool
    intake_decision: VoiceCaregiverIntakeDecision
    requires_human_review: bool
    requires_caregiver_confirmation: bool
    storage_lane: str
    audio_processing_authorized: bool
    asr_runtime_authorized: bool
    external_send_authorized: bool
    tts_authorized: bool
    voice_clone_authorized: bool
    background_listening_authorized: bool
    durable_transcript_storage_authorized: bool
    voice_authentication_authorized: bool
    routine_packet_review: GuidedRoutinePacket | None
    relay_packet_review: CaregiverRelayPacket | None
    blocked_reason: str | None
    future_stage_required: str | None
    created_at: str

    def __post_init__(self) -> None:
        if self.storage_lane != "SESSION_ONLY_OR_DO_NOT_STORE":
            raise ValueError("71P transcript intake must remain session-only or not stored.")
        if self.audio_processing_authorized:
            raise ValueError("71P cannot authorize audio processing.")
        if self.asr_runtime_authorized:
            raise ValueError("71P cannot authorize ASR runtime.")
        if self.external_send_authorized:
            raise ValueError("71P cannot authorize external sending.")
        if self.tts_authorized:
            raise ValueError("71P cannot authorize TTS.")
        if self.voice_clone_authorized:
            raise ValueError("71P cannot authorize voice cloning.")
        if self.background_listening_authorized:
            raise ValueError("71P cannot authorize background listening.")
        if self.durable_transcript_storage_authorized:
            raise ValueError("71P cannot authorize durable transcript storage.")
        if self.voice_authentication_authorized:
            raise ValueError("71P cannot authorize voice authentication.")


def build_voice_caregiver_intake_packet(
    request: VoiceCaregiverIntakeRequest,
) -> VoiceCaregiverIntakePacket:
    decision = classify_voice_caregiver_intake(request)
    detected = _detected_context(request)
    routine_packet = _routine_packet_review_for_request(request, decision, detected)
    relay_packet = _relay_packet_review_for_request(request, decision, detected)

    return VoiceCaregiverIntakePacket(
        packet_id=f"voice_caregiver_intake_{uuid4().hex}",
        source_channel=request.source_channel,
        transcript_text=request.transcript_text,
        transcript_confidence=request.transcript_confidence,
        language_detected=request.language_detected,
        code_switching_detected=request.code_switching_detected,
        caregiver_context_detected=detected.caregiver_context_detected,
        routine_intent_detected=detected.routine_intent_detected,
        medication_adjacent_detected=detected.medication_adjacent_detected,
        medical_decision_requested=detected.medical_decision_requested,
        dosage_or_schedule_requested=detected.dosage_or_schedule_requested,
        ingestion_verification_requested=detected.ingestion_verification_requested,
        emergency_like_detected=detected.emergency_like_detected,
        surveillance_requested=detected.surveillance_requested,
        external_action_requested=detected.external_action_requested,
        sensitive_context_detected=detected.sensitive_context_detected,
        intake_decision=decision,
        requires_human_review=_requires_human_review(decision, request),
        requires_caregiver_confirmation=_requires_caregiver_confirmation(decision, detected),
        storage_lane="SESSION_ONLY_OR_DO_NOT_STORE",
        audio_processing_authorized=False,
        asr_runtime_authorized=False,
        external_send_authorized=False,
        tts_authorized=False,
        voice_clone_authorized=False,
        background_listening_authorized=False,
        durable_transcript_storage_authorized=False,
        voice_authentication_authorized=False,
        routine_packet_review=routine_packet,
        relay_packet_review=relay_packet,
        blocked_reason=_blocked_reason_for_decision(decision),
        future_stage_required=_future_stage_for_decision(decision),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def classify_voice_caregiver_intake(
    request: VoiceCaregiverIntakeRequest,
) -> VoiceCaregiverIntakeDecision:
    detected = _detected_context(request)
    if detected.external_action_requested:
        return "BLOCK_EXTERNAL_ACTION"
    if detected.surveillance_requested:
        return "BLOCK_SURVEILLANCE"
    if (
        detected.medical_decision_requested
        or detected.dosage_or_schedule_requested
        or detected.ingestion_verification_requested
    ):
        return "BLOCK_MEDICAL_DECISION"
    if detected.emergency_like_detected:
        return "ESCALATE_TO_HUMAN_CAREGIVER"
    if request.transcript_confidence in {"UNKNOWN", "LOW"}:
        return "ASK_CLARIFICATION"
    if detected.medication_adjacent_detected:
        return "PREPARE_MEDICATION_ADJACENT_REVIEW"
    if detected.routine_intent_detected:
        return "PREPARE_ROUTINE_PACKET_REVIEW"
    if detected.caregiver_context_detected or detected.sensitive_context_detected:
        return "PREPARE_CAREGIVER_RELAY_REVIEW"
    if request.transcript_text.strip():
        return "ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW"
    return "DISCARD_OR_NO_ACTION"


def should_prepare_guided_routine_review(request: VoiceCaregiverIntakeRequest) -> bool:
    decision = classify_voice_caregiver_intake(request)
    return decision in {"PREPARE_ROUTINE_PACKET_REVIEW", "PREPARE_MEDICATION_ADJACENT_REVIEW"}


def should_prepare_caregiver_relay_review(request: VoiceCaregiverIntakeRequest) -> bool:
    decision = classify_voice_caregiver_intake(request)
    detected = _detected_context(request)
    return (
        decision in {
            "PREPARE_MEDICATION_ADJACENT_REVIEW",
            "PREPARE_CAREGIVER_RELAY_REVIEW",
            "ESCALATE_TO_HUMAN_CAREGIVER",
        }
        or detected.sensitive_context_detected
    )


@dataclass(frozen=True, slots=True)
class _DetectedContext:
    caregiver_context_detected: bool
    routine_intent_detected: bool
    medication_adjacent_detected: bool
    medical_decision_requested: bool
    dosage_or_schedule_requested: bool
    ingestion_verification_requested: bool
    emergency_like_detected: bool
    surveillance_requested: bool
    external_action_requested: bool
    sensitive_context_detected: bool
    routine_hint: str


def _detected_context(request: VoiceCaregiverIntakeRequest) -> _DetectedContext:
    text = _normalized_text(request.transcript_text)
    medication_adjacent = request.medication_adjacent or _contains_any(
        text,
        {
            "pastillero",
            "medicina",
            "medicamento",
            "pillbox",
            "pill",
            "pills",
            "medicine",
            "medication",
        },
    )
    dosage_or_schedule = request.dosage_or_schedule_requested or _contains_any(
        text,
        {
            "dosis",
            "dosage",
            "schedule",
            "horario",
            "cambiar medicamento",
            "which pill",
            "que pastilla",
            "que medicina",
            "cual medicina",
            "tomar esta noche",
            "take tonight",
        },
    )
    ingestion_verification = request.ingestion_verification_requested or _contains_any(
        text,
        {
            "tomo la pastilla",
            "tomó la pastilla",
            "confirmar que tomo",
            "confirmar que tomó",
            "verify that she swallowed",
            "si se tomo",
            "si se tomó",
        },
    )
    routine_hint = request.routine_hint or _routine_hint_from_text(text)

    return _DetectedContext(
        caregiver_context_detected=request.caregiver_context_present
        or _contains_any(
            text,
            {
                "mama",
                "mamá",
                "mother",
                "mother-in-law",
                "caregiver",
                "cuidador",
                "cuidadora",
                "abuela",
                "grandma",
                "she ",
                "her ",
                "ella ",
            },
        ),
        routine_intent_detected=request.routine_intent_present or routine_hint != "custom",
        medication_adjacent_detected=medication_adjacent,
        medical_decision_requested=request.medical_decision_requested
        or _contains_any(
            text,
            {
                "tell her which pill",
                "which pill to take",
                "que pastilla tomar",
                "qué pastilla tomar",
                "cual medicina",
                "cuál medicina",
                "decide if she should take",
                "should take another pill",
            },
        ),
        dosage_or_schedule_requested=dosage_or_schedule,
        ingestion_verification_requested=ingestion_verification,
        emergency_like_detected=request.emergency_like
        or _contains_any(
            text,
            {
                "se cayo",
                "se cayó",
                "cannot get up",
                "can't get up",
                "no responde",
                "dolor fuerte",
                "emergencia",
                "ambulancia",
                "fell and cannot",
            },
        ),
        surveillance_requested=request.surveillance_requested
        or _contains_any(
            text,
            {
                "vigila todo el dia",
                "vigila todo el día",
                "keep listening",
                "monitor all day",
                "track her",
                "si sale del cuarto",
                "leaves the room",
                "background listening",
                "continuous monitoring",
            },
        ),
        external_action_requested=request.external_action_requested
        or _contains_any(
            text,
            {
                "send ",
                "manda ",
                "mandale ",
                "mándale ",
                "contact ",
                "call ",
                "publish ",
                "email ",
                "whatsapp ",
                "text the",
                "message the",
            },
        ),
        sensitive_context_detected=request.sensitive_context_present
        or _contains_any(
            text,
            {
                "confused",
                "confundio",
                "confundió",
                "private",
                "sensitive",
                "family conflict",
                "crisis",
            },
        ),
        routine_hint=routine_hint,
    )


def _routine_packet_review_for_request(
    request: VoiceCaregiverIntakeRequest,
    decision: VoiceCaregiverIntakeDecision,
    detected: _DetectedContext,
) -> GuidedRoutinePacket | None:
    if decision not in {"PREPARE_ROUTINE_PACKET_REVIEW", "PREPARE_MEDICATION_ADJACENT_REVIEW"}:
        return None
    if request.transcript_confidence not in {"MEDIUM", "HIGH"}:
        return None

    return build_guided_routine_packet(
        GuidedRoutineRequest(
            raw_text=request.transcript_text,
            routine_hint=detected.routine_hint,
            intended_user=request.intended_user,
            caregiver_context_present=detected.caregiver_context_detected,
            caregiver_approved=request.caregiver_approved_context,
            medication_adjacent=decision == "PREPARE_MEDICATION_ADJACENT_REVIEW",
            medical_decision_requested=False,
            dosage_or_schedule_requested=False,
            ingestion_verification_requested=False,
            emergency_like=False,
            surveillance_requested=False,
            external_action_requested=False,
            routine_execution_requested=False,
            sensitive_context_present=detected.sensitive_context_detected,
            source_robot_id=request.source_robot_id,
            target_context="HUMAN_CAREGIVER_REVIEW",
            caregiver_id=request.caregiver_id,
            routine_ref=detected.routine_hint,
            source_event_ref=request.source_event_ref,
        )
    )


def _relay_packet_review_for_request(
    request: VoiceCaregiverIntakeRequest,
    decision: VoiceCaregiverIntakeDecision,
    detected: _DetectedContext,
) -> CaregiverRelayPacket | None:
    if decision in {"ASK_CLARIFICATION", "DISCARD_OR_NO_ACTION", "ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW"}:
        return None
    if decision == "PREPARE_ROUTINE_PACKET_REVIEW" and not detected.sensitive_context_detected:
        return None
    if decision in {"BLOCK_SURVEILLANCE", "BLOCK_EXTERNAL_ACTION", "BLOCK_MEDICAL_DECISION"}:
        return None

    return build_caregiver_relay_packet(
        CaregiverRelayRequest(
            raw_text=request.transcript_text,
            source_robot_id=request.source_robot_id,
            target_context="HUMAN_CAREGIVER_REVIEW",
            caregiver_context_present=detected.caregiver_context_detected,
            medication_adjacent=decision == "PREPARE_MEDICATION_ADJACENT_REVIEW",
            medical_decision_requested=False,
            emergency_like=decision == "ESCALATE_TO_HUMAN_CAREGIVER",
            surveillance_requested=False,
            external_action_requested=False,
            routine_execution_requested=False,
            sensitive_context_present=detected.sensitive_context_detected,
            caregiver_id=request.caregiver_id,
            routine_ref=detected.routine_hint if decision == "PREPARE_CAREGIVER_RELAY_REVIEW" else None,
            source_event_ref=request.source_event_ref,
        )
    )


def _requires_human_review(
    decision: VoiceCaregiverIntakeDecision,
    request: VoiceCaregiverIntakeRequest,
) -> bool:
    return decision not in {"DISCARD_OR_NO_ACTION", "ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW"} or request.transcript_confidence == "UNKNOWN"


def _requires_caregiver_confirmation(
    decision: VoiceCaregiverIntakeDecision,
    detected: _DetectedContext,
) -> bool:
    return (
        detected.medication_adjacent_detected
        or detected.sensitive_context_detected
        or decision in {
            "PREPARE_MEDICATION_ADJACENT_REVIEW",
            "PREPARE_CAREGIVER_RELAY_REVIEW",
            "ESCALATE_TO_HUMAN_CAREGIVER",
            "BLOCK_MEDICAL_DECISION",
        }
    )


def _blocked_reason_for_decision(decision: VoiceCaregiverIntakeDecision) -> str | None:
    reasons: dict[VoiceCaregiverIntakeDecision, str] = {
        "BLOCK_EXTERNAL_ACTION": "External sending, alerts, browser/email/WhatsApp, or third-party contact are outside Roboticxs v0.",
        "BLOCK_SURVEILLANCE": "Background listening or continuous monitoring is outside Roboticxs v0.",
        "BLOCK_MEDICAL_DECISION": "Medication selection, dosage, schedule, or ingestion verification is outside Roboticxs v0.",
    }
    return reasons.get(decision)


def _future_stage_for_decision(decision: VoiceCaregiverIntakeDecision) -> str | None:
    if decision == "BLOCK_EXTERNAL_ACTION":
        return "future_explicit_external_action_authority"
    if decision == "BLOCK_SURVEILLANCE":
        return "future_explicit_monitoring_authority"
    return None


def _routine_hint_from_text(text: str) -> str:
    if _contains_any(text, {"hearing aid", "hearing aids", "auxiliar auditivo", "aparato auditivo"}):
        return "hearing_aid"
    if _contains_any(text, {"agua", "hidratacion", "hidratación", "comer", "comida", "water", "meal", "food"}):
        return "hydration"
    if _contains_any(text, {"baño", "bano", "lavarse", "higiene", "hygiene"}):
        return "hygiene"
    if _contains_any(text, {"cita", "appointment", "doctor appointment"}):
        return "appointment"
    if _contains_any(text, {"pastillero", "pillbox", "pill", "medicina", "medicamento", "medication"}):
        return "pillbox"
    return "custom"


def _looks_like_audio_reference(value: str) -> bool:
    text = value.strip().lower()
    return text.startswith(("file://", "audio://")) or text.endswith(
        (".ogg", ".oga", ".opus", ".mp3", ".wav", ".m4a", ".aac", ".flac")
    )


def _normalized_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _contains_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)
