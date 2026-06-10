from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


CaregiverRelayPacketType = Literal[
    "CAREGIVER_STATUS_NOTE",
    "CAREGIVER_CONFIRMATION_REQUEST",
    "ROUTINE_NEEDS_ATTENTION_DRAFT",
    "CAREGIVER_HANDOFF_DRAFT",
    "SENSITIVE_CONTEXT_REVIEW_REQUEST",
    "BLOCKED_MEDICAL_REQUEST_NOTICE",
    "BLOCKED_SURVEILLANCE_NOTICE",
    "BLOCKED_EXTERNAL_ACTION_NOTICE",
]

CaregiverRelayDecision = Literal[
    "PREPARE_DRAFT",
    "ASK_CAREGIVER_CONFIRMATION",
    "REDACT_AND_PREPARE",
    "ESCALATE_TO_HUMAN_CAREGIVER",
    "BLOCK_MEDICAL",
    "BLOCK_SURVEILLANCE",
    "BLOCK_EXTERNAL_ACTION",
    "DEFER_TO_GUIDED_ROUTINE_PACKETS",
]

CaregiverRelayTargetContext = Literal[
    "CAREGIVER_ROBOT",
    "FAMILY_GROUP_DRAFT",
    "HUMAN_CAREGIVER_REVIEW",
    "SESSION_ONLY",
]

CaregiverRelaySensitivity = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "SENSITIVE",
]


ALLOWED_TARGET_CONTEXTS = frozenset(
    {
        "CAREGIVER_ROBOT",
        "FAMILY_GROUP_DRAFT",
        "HUMAN_CAREGIVER_REVIEW",
        "SESSION_ONLY",
    }
)
BLOCKED_TARGET_CONTEXTS = frozenset(
    {
        "AUTO_SEND_TO_GROUP",
        "AUTO_SEND_TO_CAREGIVER",
        "AUTO_ALERT_EMERGENCY",
        "AUTO_CONTACT_THIRD_PARTY",
    }
)


@dataclass(frozen=True, slots=True)
class CaregiverRelayRequest:
    raw_text: str
    source_robot_id: str
    target_context: CaregiverRelayTargetContext
    caregiver_context_present: bool = False
    medication_adjacent: bool = False
    medical_decision_requested: bool = False
    emergency_like: bool = False
    surveillance_requested: bool = False
    external_action_requested: bool = False
    routine_execution_requested: bool = False
    sensitive_context_present: bool = False
    never_store_or_share: bool = False
    caregiver_id: str | None = None
    family_group_id: str | None = None
    routine_ref: str | None = None
    source_event_ref: str | None = None

    def __post_init__(self) -> None:
        if self.target_context in BLOCKED_TARGET_CONTEXTS:
            raise ValueError(f"{self.target_context} is not an allowed 68P relay target context.")
        if self.target_context not in ALLOWED_TARGET_CONTEXTS:
            raise ValueError(f"Unknown caregiver relay target context: {self.target_context}.")


@dataclass(frozen=True, slots=True)
class CaregiverRelayPacket:
    packet_id: str
    packet_type: CaregiverRelayPacketType
    relay_decision: CaregiverRelayDecision
    source_robot_id: str
    target_context: CaregiverRelayTargetContext
    caregiver_visibility: str
    summary: str
    requested_human_action: str
    sensitivity_level: CaregiverRelaySensitivity
    requires_confirmation: bool
    external_send_authorized: bool
    medical_decision_authorized: bool
    emergency_claim_authorized: bool
    routine_execution_authorized: bool
    redaction_required: bool
    blocked_reason: str | None
    future_stage_required: str | None
    created_at: str

    def __post_init__(self) -> None:
        if self.external_send_authorized:
            raise ValueError("68P packets cannot authorize external sending.")
        if self.medical_decision_authorized:
            raise ValueError("68P packets cannot authorize medical decisions.")
        if self.emergency_claim_authorized:
            raise ValueError("68P packets cannot authorize emergency handling claims.")
        if self.routine_execution_authorized:
            raise ValueError("68P packets cannot authorize routine execution.")


def classify_caregiver_relay_request(request: CaregiverRelayRequest) -> CaregiverRelayDecision:
    if request.external_action_requested:
        return "BLOCK_EXTERNAL_ACTION"
    if request.surveillance_requested:
        return "BLOCK_SURVEILLANCE"
    if request.medical_decision_requested:
        return "BLOCK_MEDICAL"
    if request.emergency_like:
        return "ESCALATE_TO_HUMAN_CAREGIVER"
    if request.routine_execution_requested:
        return "DEFER_TO_GUIDED_ROUTINE_PACKETS"
    if request.medication_adjacent:
        return "ASK_CAREGIVER_CONFIRMATION"
    if request.sensitive_context_present or request.never_store_or_share:
        return "REDACT_AND_PREPARE"
    return "PREPARE_DRAFT"


def requires_relay_redaction(request: CaregiverRelayRequest) -> bool:
    return request.sensitive_context_present or request.never_store_or_share


def build_caregiver_relay_packet(request: CaregiverRelayRequest) -> CaregiverRelayPacket:
    decision = classify_caregiver_relay_request(request)
    redaction_required = requires_relay_redaction(request) or decision == "ESCALATE_TO_HUMAN_CAREGIVER"
    target_context: CaregiverRelayTargetContext = "SESSION_ONLY" if request.never_store_or_share else request.target_context

    return CaregiverRelayPacket(
        packet_id=f"caregiver_relay_{uuid4().hex}",
        packet_type=_packet_type_for_request(request, decision),
        relay_decision=decision,
        source_robot_id=request.source_robot_id,
        target_context=target_context,
        caregiver_visibility=_caregiver_visibility(request, decision),
        summary=_summary_for_decision(request, decision),
        requested_human_action=_requested_human_action_for_decision(decision),
        sensitivity_level=_sensitivity_for_request(request, decision),
        requires_confirmation=_requires_confirmation(request, decision),
        external_send_authorized=False,
        medical_decision_authorized=False,
        emergency_claim_authorized=False,
        routine_execution_authorized=False,
        redaction_required=redaction_required,
        blocked_reason=_blocked_reason_for_decision(decision),
        future_stage_required=_future_stage_for_decision(decision),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _packet_type_for_request(
    request: CaregiverRelayRequest,
    decision: CaregiverRelayDecision,
) -> CaregiverRelayPacketType:
    if decision == "PREPARE_DRAFT" and request.routine_ref:
        return "ROUTINE_NEEDS_ATTENTION_DRAFT"
    if decision == "PREPARE_DRAFT" and request.caregiver_context_present and request.target_context == "CAREGIVER_ROBOT":
        return "CAREGIVER_HANDOFF_DRAFT"
    return _packet_type_for_decision(decision)


def _packet_type_for_decision(decision: CaregiverRelayDecision) -> CaregiverRelayPacketType:
    packet_types: dict[CaregiverRelayDecision, CaregiverRelayPacketType] = {
        "PREPARE_DRAFT": "CAREGIVER_STATUS_NOTE",
        "ASK_CAREGIVER_CONFIRMATION": "CAREGIVER_CONFIRMATION_REQUEST",
        "REDACT_AND_PREPARE": "SENSITIVE_CONTEXT_REVIEW_REQUEST",
        "ESCALATE_TO_HUMAN_CAREGIVER": "SENSITIVE_CONTEXT_REVIEW_REQUEST",
        "BLOCK_MEDICAL": "BLOCKED_MEDICAL_REQUEST_NOTICE",
        "BLOCK_SURVEILLANCE": "BLOCKED_SURVEILLANCE_NOTICE",
        "BLOCK_EXTERNAL_ACTION": "BLOCKED_EXTERNAL_ACTION_NOTICE",
        "DEFER_TO_GUIDED_ROUTINE_PACKETS": "ROUTINE_NEEDS_ATTENTION_DRAFT",
    }
    return packet_types[decision]


def _caregiver_visibility(request: CaregiverRelayRequest, decision: CaregiverRelayDecision) -> str:
    if request.never_store_or_share:
        return "session_only_human_review"
    if decision.startswith("BLOCK_"):
        return "blocked_notice_only"
    if decision in {"ASK_CAREGIVER_CONFIRMATION", "ESCALATE_TO_HUMAN_CAREGIVER"}:
        return "human_caregiver_review_required"
    return "caregiver_visible_draft"


def _summary_for_decision(request: CaregiverRelayRequest, decision: CaregiverRelayDecision) -> str:
    if decision == "BLOCK_EXTERNAL_ACTION":
        return "External sending or third-party contact is blocked in 68P."
    if decision == "BLOCK_SURVEILLANCE":
        return "This request is blocked because continuous monitoring is outside Roboticxs v0."
    if decision == "BLOCK_MEDICAL":
        return "Medical decisioning is blocked; a human caregiver or clinician must decide."
    if decision == "ESCALATE_TO_HUMAN_CAREGIVER":
        return "This looks emergency-like. Contact a human caregiver or emergency services."
    if decision == "DEFER_TO_GUIDED_ROUTINE_PACKETS":
        return "Caregiver routine execution is deferred to 69P Guided Routine Packets."
    if decision == "ASK_CAREGIVER_CONFIRMATION":
        return "Medication-adjacent uncertainty was reported. A human caregiver should verify using the approved process."
    if request.never_store_or_share:
        return "Sensitive context requires session-only human caregiver review."
    if request.sensitive_context_present:
        return "Caregiver review may be needed for sensitive context."
    if request.routine_ref:
        return "Routine attention draft may need caregiver review."
    return "Caregiver review may be needed."


def _requested_human_action_for_decision(decision: CaregiverRelayDecision) -> str:
    actions: dict[CaregiverRelayDecision, str] = {
        "PREPARE_DRAFT": "Caregiver review.",
        "ASK_CAREGIVER_CONFIRMATION": "Human caregiver should verify using the approved medication process.",
        "REDACT_AND_PREPARE": "Human caregiver should review redacted context before any sharing.",
        "ESCALATE_TO_HUMAN_CAREGIVER": "Contact a human caregiver or emergency services.",
        "BLOCK_MEDICAL": "Use a qualified human caregiver or clinician for medical decisions.",
        "BLOCK_SURVEILLANCE": "Do not use Roboticxs for hidden monitoring or continuous surveillance.",
        "BLOCK_EXTERNAL_ACTION": "Review locally; do not send externally from 68P.",
        "DEFER_TO_GUIDED_ROUTINE_PACKETS": "Wait for 69P Guided Routine Packets before routine execution.",
    }
    return actions[decision]


def _sensitivity_for_request(
    request: CaregiverRelayRequest,
    decision: CaregiverRelayDecision,
) -> CaregiverRelaySensitivity:
    if request.never_store_or_share or decision in {"ESCALATE_TO_HUMAN_CAREGIVER", "BLOCK_MEDICAL"}:
        return "SENSITIVE"
    if request.sensitive_context_present or request.medication_adjacent:
        return "HIGH"
    if request.caregiver_context_present:
        return "MEDIUM"
    return "LOW"


def _requires_confirmation(request: CaregiverRelayRequest, decision: CaregiverRelayDecision) -> bool:
    return (
        request.medication_adjacent
        or request.sensitive_context_present
        or request.never_store_or_share
        or decision in {"ASK_CAREGIVER_CONFIRMATION", "REDACT_AND_PREPARE", "ESCALATE_TO_HUMAN_CAREGIVER"}
    )


def _blocked_reason_for_decision(decision: CaregiverRelayDecision) -> str | None:
    blocked_reasons: dict[CaregiverRelayDecision, str] = {
        "BLOCK_EXTERNAL_ACTION": "Automatic external relay or third-party contact is outside 68P.",
        "BLOCK_SURVEILLANCE": "Continuous monitoring/surveillance is outside Roboticxs v0.",
        "BLOCK_MEDICAL": "Medical decisions are outside Roboticxs v0.",
    }
    return blocked_reasons.get(decision)


def _future_stage_for_decision(decision: CaregiverRelayDecision) -> str | None:
    if decision == "DEFER_TO_GUIDED_ROUTINE_PACKETS":
        return "69P_GUIDED_ROUTINE_PACKETS"
    if decision == "BLOCK_EXTERNAL_ACTION":
        return "future_explicit_external_action_authority"
    return None
