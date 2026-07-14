from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

import pytest

from app.caregiver_relay import (
    CaregiverRelayDecision,
    CaregiverRelayPacket,
    CaregiverRelayPacketType,
    CaregiverRelayRequest,
    build_caregiver_relay_packet,
    classify_caregiver_relay_request,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/CAREGIVER_TELEGRAM_GROUP_RELAY_v0_1.md"
ROADMAP_PATH = Path(__file__).resolve().parents[1] / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "packet_type",
    "relay_decision",
    "source_robot_id",
    "target_context",
    "caregiver_visibility",
    "summary",
    "requested_human_action",
    "sensitivity_level",
    "requires_confirmation",
    "external_send_authorized",
    "medical_decision_authorized",
    "emergency_claim_authorized",
    "routine_execution_authorized",
    "redaction_required",
    "blocked_reason",
    "future_stage_required",
    "created_at",
}


def request(**overrides) -> CaregiverRelayRequest:
    values = {
        "raw_text": "She forgot her hearing aids again.",
        "source_robot_id": "robbie_mother_in_law",
        "target_context": "FAMILY_GROUP_DRAFT",
    }
    values.update(overrides)
    return CaregiverRelayRequest(**values)


def test_relay_taxonomies_are_explicit():
    assert set(get_args(CaregiverRelayPacketType)) == {
        "CAREGIVER_STATUS_NOTE",
        "CAREGIVER_CONFIRMATION_REQUEST",
        "ROUTINE_NEEDS_ATTENTION_DRAFT",
        "CAREGIVER_HANDOFF_DRAFT",
        "SENSITIVE_CONTEXT_REVIEW_REQUEST",
        "BLOCKED_MEDICAL_REQUEST_NOTICE",
        "BLOCKED_SURVEILLANCE_NOTICE",
        "BLOCKED_EXTERNAL_ACTION_NOTICE",
    }
    assert set(get_args(CaregiverRelayDecision)) == {
        "PREPARE_DRAFT",
        "ASK_CAREGIVER_CONFIRMATION",
        "REDACT_AND_PREPARE",
        "ESCALATE_TO_HUMAN_CAREGIVER",
        "BLOCK_MEDICAL",
        "BLOCK_SURVEILLANCE",
        "BLOCK_EXTERNAL_ACTION",
        "DEFER_TO_GUIDED_ROUTINE_PACKETS",
    }


def test_packet_contains_required_fields_and_schema_values():
    packet = build_caregiver_relay_packet(request())

    assert isinstance(packet, CaregiverRelayPacket)
    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_id.startswith("caregiver_relay_")
    assert packet.packet_type == "CAREGIVER_STATUS_NOTE"
    assert packet.relay_decision == "PREPARE_DRAFT"
    assert packet.source_robot_id == "robbie_mother_in_law"


def test_all_packet_authority_flags_are_disabled():
    scenarios = [
        request(),
        request(medication_adjacent=True),
        request(medical_decision_requested=True),
        request(emergency_like=True),
        request(surveillance_requested=True),
        request(external_action_requested=True),
        request(routine_execution_requested=True),
        request(sensitive_context_present=True),
        request(never_store_or_share=True),
    ]

    for scenario in scenarios:
        packet = build_caregiver_relay_packet(scenario)
        assert packet.external_send_authorized is False
        assert packet.medical_decision_authorized is False
        assert packet.emergency_claim_authorized is False
        assert packet.routine_execution_authorized is False


def test_external_action_request_blocks():
    packet = build_caregiver_relay_packet(request(external_action_requested=True))

    assert packet.relay_decision == "BLOCK_EXTERNAL_ACTION"
    assert packet.packet_type == "BLOCKED_EXTERNAL_ACTION_NOTICE"
    assert packet.blocked_reason == "Automatic external relay or third-party contact is outside 68P."


def test_surveillance_request_blocks():
    packet = build_caregiver_relay_packet(
        request(raw_text="Monitor her all day and tell me if she leaves the room.", surveillance_requested=True)
    )

    assert packet.relay_decision == "BLOCK_SURVEILLANCE"
    assert packet.packet_type == "BLOCKED_SURVEILLANCE_NOTICE"
    assert "continuous monitoring" in packet.summary


def test_medical_decision_request_blocks():
    packet = build_caregiver_relay_packet(request(raw_text="Decide if she should take another pill.", medical_decision_requested=True))

    assert packet.relay_decision == "BLOCK_MEDICAL"
    assert packet.packet_type == "BLOCKED_MEDICAL_REQUEST_NOTICE"
    assert packet.medical_decision_authorized is False


def test_emergency_like_request_escalates_to_human_caregiver_without_emergency_claim():
    packet = build_caregiver_relay_packet(request(raw_text="She fell and cannot get up.", emergency_like=True))

    assert packet.relay_decision == "ESCALATE_TO_HUMAN_CAREGIVER"
    assert packet.packet_type == "SENSITIVE_CONTEXT_REVIEW_REQUEST"
    assert packet.emergency_claim_authorized is False
    assert packet.requested_human_action == "Contact a human caregiver or emergency services."


def test_routine_execution_request_defers_to_69p():
    packet = build_caregiver_relay_packet(request(raw_text="Start her morning checklist now.", routine_execution_requested=True))

    assert packet.relay_decision == "DEFER_TO_GUIDED_ROUTINE_PACKETS"
    assert packet.packet_type == "ROUTINE_NEEDS_ATTENTION_DRAFT"
    assert packet.future_stage_required == "69P_GUIDED_ROUTINE_PACKETS"
    assert packet.routine_execution_authorized is False


def test_medication_adjacent_request_requires_caregiver_confirmation():
    packet = build_caregiver_relay_packet(
        request(raw_text="She is confused about whether she took her pill.", medication_adjacent=True)
    )

    assert packet.relay_decision == "ASK_CAREGIVER_CONFIRMATION"
    assert packet.packet_type == "CAREGIVER_CONFIRMATION_REQUEST"
    assert packet.requires_confirmation is True
    assert packet.medical_decision_authorized is False


def test_sensitive_context_requires_redaction_or_confirmation():
    packet = build_caregiver_relay_packet(request(raw_text="She seemed very confused today.", sensitive_context_present=True))

    assert packet.relay_decision == "REDACT_AND_PREPARE"
    assert packet.packet_type == "SENSITIVE_CONTEXT_REVIEW_REQUEST"
    assert packet.redaction_required is True
    assert packet.requires_confirmation is True
    assert packet.sensitivity_level == "HIGH"


def test_never_store_or_share_input_is_session_only_and_redacted():
    packet = build_caregiver_relay_packet(
        request(raw_text="Private family conflict details.", sensitive_context_present=True, never_store_or_share=True)
    )

    assert packet.target_context == "SESSION_ONLY"
    assert packet.redaction_required is True
    assert packet.requires_confirmation is True
    assert "Private family conflict details" not in packet.summary
    assert packet.sensitivity_level == "SENSITIVE"


def test_allowed_routine_attention_draft_does_not_send_externally():
    packet = build_caregiver_relay_packet(request(routine_ref="hearing_aids"))

    assert packet.relay_decision == "PREPARE_DRAFT"
    assert packet.packet_type == "ROUTINE_NEEDS_ATTENTION_DRAFT"
    assert packet.external_send_authorized is False


def test_caregiver_handoff_draft_is_local_preparation_only():
    packet = build_caregiver_relay_packet(
        request(target_context="CAREGIVER_ROBOT", caregiver_context_present=True)
    )

    assert packet.relay_decision == "PREPARE_DRAFT"
    assert packet.packet_type == "CAREGIVER_HANDOFF_DRAFT"
    assert packet.external_send_authorized is False


def test_target_context_cannot_be_automatic_send():
    for blocked_target in [
        "AUTO_SEND_TO_GROUP",
        "AUTO_SEND_TO_CAREGIVER",
        "AUTO_ALERT_EMERGENCY",
        "AUTO_CONTACT_THIRD_PARTY",
    ]:
        with pytest.raises(ValueError):
            request(target_context=blocked_target)


def test_decision_precedence_is_deterministic():
    scenario = request(
        external_action_requested=True,
        surveillance_requested=True,
        medical_decision_requested=True,
        emergency_like=True,
        routine_execution_requested=True,
        medication_adjacent=True,
        sensitive_context_present=True,
    )

    assert classify_caregiver_relay_request(scenario) == "BLOCK_EXTERNAL_ACTION"


def test_docs_contain_no_automatic_send_and_non_claims():
    text = DOC_PATH.read_text()

    for required in [
        "This stage prepares relay packets only.",
        "Roboticxs does not send Telegram messages automatically in 68P.",
        "Roboticxs does not manage Telegram groups in 68P.",
        "Roboticxs does not execute caregiver routines in 68P.",
        "Roboticxs does not decide medication dosage, schedule, ingestion, or treatment.",
        "Roboticxs does not provide emergency response or triage.",
        "Roboticxs does not continuously monitor the person.",
        "Roboticxs does not contact family members automatically.",
        "Guided Routine Packets are deferred to 69P.",
    ]:
        assert required in text


def test_roadmap_marks_68p_and_69p_completed_and_70p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"68P","stage_name":"Caregiver Telegram Group Relay v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_68P_closeout"' in text
    assert '"app/caregiver_relay.py"' in text
    assert '"docs/reference/CAREGIVER_TELEGRAM_GROUP_RELAY_v0_1.md"' in text
    assert '"tests/test_caregiver_relay.py"' in text
    assert '"stage_id":"69P","stage_name":"Guided Routine Packets v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"70P","stage_name":"Voice Notes Intelligence / VibeVoice Spike","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_70P_closeout"' in text
    assert '"stage_id":"71P","stage_name":"Voice Intake for Caregiver Routines","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"72P","stage_name":"Research Radar / Last30Days Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"after_commit_next_eligible":"76P"' in text
