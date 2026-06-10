from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

from app.caregiver_relay import CaregiverRelayPacket
from app.guided_routines import (
    GuidedRoutineDecision,
    GuidedRoutinePacket,
    GuidedRoutineRequest,
    GuidedRoutineStep,
    GuidedRoutineType,
    RoutineStepResponseType,
    build_default_steps_for_routine,
    build_guided_routine_packet,
    classify_guided_routine_request,
    requires_caregiver_handoff,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/GUIDED_ROUTINE_PACKETS_v0_1.md"
ROADMAP_PATH = Path(__file__).resolve().parents[1] / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "routine_type",
    "routine_decision",
    "title",
    "purpose",
    "intended_user",
    "caregiver_visibility",
    "steps",
    "current_step_index",
    "max_steps",
    "requires_caregiver_confirmation",
    "requires_caregiver_supervision",
    "medication_adjacent",
    "sensitivity_level",
    "session_only_progress",
    "external_send_authorized",
    "background_reminder_authorized",
    "medical_decision_authorized",
    "dosage_decision_authorized",
    "medication_schedule_authorized",
    "ingestion_verification_authorized",
    "emergency_claim_authorized",
    "surveillance_authorized",
    "routine_completion_claim",
    "handoff_relay_packet",
    "blocked_reason",
    "future_stage_required",
    "created_at",
}

REQUIRED_STEP_FIELDS = {
    "step_id",
    "step_number",
    "instruction",
    "expected_response_type",
    "requires_user_ack",
    "requires_caregiver_confirmation",
    "can_skip",
    "safety_note",
    "blocked_if",
}


def request(**overrides) -> GuidedRoutineRequest:
    values = {
        "raw_text": "Guide her to put on her hearing aids.",
        "routine_hint": "hearing_aid",
        "intended_user": "mother-in-law",
        "caregiver_approved": True,
    }
    values.update(overrides)
    return GuidedRoutineRequest(**values)


def test_guided_routine_taxonomies_are_explicit():
    assert set(get_args(GuidedRoutineType)) == {
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
    }
    assert set(get_args(GuidedRoutineDecision)) == {
        "PREPARE_ROUTINE_PACKET",
        "PREPARE_WITH_CAREGIVER_CONFIRMATION",
        "PREPARE_MEDICATION_ADJACENT_CHECKLIST",
        "DEFER_TO_CAREGIVER_RELAY",
        "BLOCK_MEDICAL_DECISION",
        "BLOCK_SURVEILLANCE",
        "BLOCK_EMERGENCY",
        "BLOCK_EXTERNAL_ACTION",
    }
    assert set(get_args(RoutineStepResponseType)) == {
        "ACK_ONLY",
        "YES_NO",
        "CAREGIVER_CONFIRMATION",
        "FREE_TEXT_NOTE",
        "NO_RESPONSE_REQUIRED",
    }


def test_packet_contains_required_fields():
    packet = build_guided_routine_packet(request())

    assert isinstance(packet, GuidedRoutinePacket)
    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_id.startswith("guided_routine_")
    assert packet.routine_type == "HEARING_AID_ROUTINE"
    assert packet.routine_decision == "PREPARE_ROUTINE_PACKET"


def test_step_contains_required_fields():
    step = build_guided_routine_packet(request()).steps[0]

    assert isinstance(step, GuidedRoutineStep)
    assert {field.name for field in fields(step)} == REQUIRED_STEP_FIELDS
    assert step.step_number == 1
    assert step.expected_response_type == "ACK_ONLY"


def test_all_packet_authority_flags_are_disabled():
    scenarios = [
        request(),
        request(routine_hint="hydration"),
        request(medication_adjacent=True, routine_hint="pillbox"),
        request(dosage_or_schedule_requested=True, routine_hint="medication"),
        request(ingestion_verification_requested=True, routine_hint="medication"),
        request(emergency_like=True),
        request(surveillance_requested=True),
        request(external_action_requested=True),
    ]

    for scenario in scenarios:
        packet = build_guided_routine_packet(scenario)
        assert packet.external_send_authorized is False
        assert packet.background_reminder_authorized is False
        assert packet.medical_decision_authorized is False
        assert packet.dosage_decision_authorized is False
        assert packet.medication_schedule_authorized is False
        assert packet.ingestion_verification_authorized is False
        assert packet.emergency_claim_authorized is False
        assert packet.surveillance_authorized is False
        assert packet.session_only_progress is True


def test_hearing_aid_routine_builds_valid_short_step_packet():
    packet = build_guided_routine_packet(request())

    assert packet.routine_type == "HEARING_AID_ROUTINE"
    assert packet.max_steps == 5
    assert [step.instruction for step in packet.steps] == [
        "Please find your hearing aids.",
        "Check that they are facing the right direction.",
        "Put on the left hearing aid.",
        "Put on the right hearing aid.",
        "Tell me when you are done.",
    ]
    assert all(len(step.instruction.split()) <= 10 for step in packet.steps)
    assert all(step.requires_user_ack is True for step in packet.steps)


def test_hydration_or_meal_routine_builds_valid_step_packet_without_reminders():
    packet = build_guided_routine_packet(
        request(raw_text="Remind her to drink water.", routine_hint="hydration")
    )

    assert packet.routine_type == "HYDRATION_OR_MEAL_ROUTINE"
    assert packet.routine_decision == "PREPARE_ROUTINE_PACKET"
    assert packet.background_reminder_authorized is False
    assert [step.instruction for step in packet.steps[:3]] == [
        "Please take your glass or meal.",
        "Take one small sip or bite.",
        "Put it somewhere safe.",
    ]


def test_hygiene_routine_builds_local_packet():
    packet = build_guided_routine_packet(request(routine_hint="hygiene"))

    assert packet.routine_type == "HYGIENE_ROUTINE"
    assert packet.routine_decision == "PREPARE_ROUTINE_PACKET"
    assert packet.external_send_authorized is False


def test_appointment_preparation_routine_builds_local_packet():
    packet = build_guided_routine_packet(request(routine_hint="appointment"))

    assert packet.routine_type == "APPOINTMENT_PREPARATION_ROUTINE"
    assert "Ask your caregiver if anything is missing." in [step.instruction for step in packet.steps]
    assert packet.background_reminder_authorized is False


def test_household_simple_routine_builds_local_packet():
    packet = build_guided_routine_packet(request(routine_hint="household"))

    assert packet.routine_type == "HOUSEHOLD_SIMPLE_ROUTINE"
    assert packet.steps[0].instruction == "Let's do one small step."
    assert packet.session_only_progress is True


def test_pillbox_hint_becomes_medication_adjacent_checklist_without_flag():
    packet = build_guided_routine_packet(request(routine_hint="pillbox"))

    assert packet.routine_type == "MEDICATION_ADJACENT_CHECKLIST"
    assert packet.routine_decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST"
    assert packet.requires_caregiver_confirmation is True
    assert packet.sensitivity_level == "HIGH"
    assert packet.handoff_relay_packet.packet_type == "CAREGIVER_CONFIRMATION_REQUEST"
    assert packet.handoff_relay_packet.requires_confirmation is True


def test_medication_adjacent_checklist_requires_confirmation_and_supervision():
    packet = build_guided_routine_packet(
        request(raw_text="Help her fill her weekly pillbox.", routine_hint="pillbox", medication_adjacent=True)
    )

    assert packet.routine_type == "MEDICATION_ADJACENT_CHECKLIST"
    assert packet.routine_decision == "PREPARE_MEDICATION_ADJACENT_CHECKLIST"
    assert packet.requires_caregiver_confirmation is True
    assert packet.requires_caregiver_supervision is True
    assert packet.medication_adjacent is True
    assert packet.routine_completion_claim == "CAREGIVER_REPORTED_OR_USER_REPORTED_ONLY"
    assert all(step.requires_caregiver_confirmation is True for step in packet.steps)
    assert all(step.expected_response_type == "CAREGIVER_CONFIRMATION" for step in packet.steps)


def test_medication_dosage_or_schedule_request_blocks():
    packet = build_guided_routine_packet(
        request(raw_text="Tell her which pill to take tonight.", routine_hint="medication", dosage_or_schedule_requested=True)
    )

    assert packet.routine_type == "BLOCKED_MEDICAL_ROUTINE"
    assert packet.routine_decision == "BLOCK_MEDICAL_DECISION"
    assert "Medication selection, dosage, schedule" in packet.blocked_reason


def test_ingestion_verification_request_blocks():
    packet = build_guided_routine_packet(
        request(raw_text="Verify that she swallowed the pill.", routine_hint="medication", ingestion_verification_requested=True)
    )

    assert packet.routine_type == "BLOCKED_MEDICAL_ROUTINE"
    assert packet.routine_decision == "BLOCK_MEDICAL_DECISION"
    assert packet.ingestion_verification_authorized is False


def test_emergency_like_request_blocks_routine_and_creates_local_handoff():
    packet = build_guided_routine_packet(
        request(raw_text="She fell and cannot get up. Walk her through what to do.", emergency_like=True)
    )

    assert packet.routine_type == "BLOCKED_EMERGENCY_ROUTINE"
    assert packet.routine_decision == "BLOCK_EMERGENCY"
    assert packet.blocked_reason == "Emergency-like situations require human caregiver or emergency services."
    assert isinstance(packet.handoff_relay_packet, CaregiverRelayPacket)
    assert packet.handoff_relay_packet.external_send_authorized is False
    assert packet.handoff_relay_packet.emergency_claim_authorized is False


def test_surveillance_request_blocks():
    packet = build_guided_routine_packet(
        request(raw_text="Watch her all day and guide her if she wanders.", surveillance_requested=True)
    )

    assert packet.routine_type == "BLOCKED_SURVEILLANCE_ROUTINE"
    assert packet.routine_decision == "BLOCK_SURVEILLANCE"
    assert packet.surveillance_authorized is False


def test_external_action_request_blocks_without_send_authority():
    packet = build_guided_routine_packet(
        request(raw_text="Send the group a reminder when she starts.", external_action_requested=True)
    )

    assert packet.routine_type == "BLOCKED_SURVEILLANCE_ROUTINE"
    assert packet.routine_decision == "BLOCK_EXTERNAL_ACTION"
    assert packet.external_send_authorized is False
    assert packet.future_stage_required == "future_explicit_external_action_authority"


def test_routine_progress_is_session_only_not_durable_memory():
    packet = build_guided_routine_packet(request())

    assert packet.session_only_progress is True
    assert packet.current_step_index == 0
    assert packet.routine_completion_claim == "USER_REPORTED_ONLY"


def test_caregiver_confirmation_creates_local_68p_relay_handoff_only():
    packet = build_guided_routine_packet(
        request(caregiver_context_present=True, caregiver_approved=False, sensitive_context_present=True)
    )

    assert packet.routine_decision == "PREPARE_WITH_CAREGIVER_CONFIRMATION"
    assert packet.requires_caregiver_confirmation is True
    assert requires_caregiver_handoff(request(caregiver_context_present=True, caregiver_approved=False)) is True
    assert isinstance(packet.handoff_relay_packet, CaregiverRelayPacket)
    assert packet.handoff_relay_packet.external_send_authorized is False
    assert packet.handoff_relay_packet.routine_execution_authorized is False


def test_decision_precedence_is_deterministic():
    scenario = request(
        external_action_requested=True,
        surveillance_requested=True,
        emergency_like=True,
        medical_decision_requested=True,
        medication_adjacent=True,
        caregiver_context_present=True,
        caregiver_approved=False,
    )

    assert classify_guided_routine_request(scenario) == "BLOCK_EXTERNAL_ACTION"


def test_default_custom_steps_remain_local_and_respectful():
    packet = build_guided_routine_packet(
        request(
            routine_hint="custom",
            custom_steps=("Please check the blue folder.", "Put it by the door."),
        )
    )

    assert packet.routine_type == "CAREGIVER_APPROVED_CUSTOM_ROUTINE"
    assert [step.instruction for step in packet.steps] == [
        "Please check the blue folder.",
        "Put it by the door.",
    ]


def test_docs_contain_required_non_claims_and_source_register():
    text = DOC_PATH.read_text()

    for required in [
        "local packet builder",
        "Roboticxs does not schedule reminders in 69P.",
        "Roboticxs does not send Telegram messages automatically in 69P.",
        "Roboticxs does not store caregiver routine progress durably in 69P.",
        "Roboticxs does not decide medication selection, dosage, schedule, substitution, or ingestion.",
        "Roboticxs does not verify medication ingestion as fact.",
        "Roboticxs does not provide emergency response or triage.",
        "Roboticxs does not continuously monitor the person.",
        "Voice behavior is deferred to 70P or later approved stages.",
        "Alzheimer's Association - Daily Care Plan",
        "NHS - Medicines: tips for carers",
        "MedlinePlus - Keeping your medicines organized",
        "WHO - Assistive technology",
    ]:
        assert required in text


def test_roadmap_marks_69p_completed_and_70p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"69P","stage_name":"Guided Routine Packets v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_69P_closeout"' in text
    assert '"app/guided_routines.py"' in text
    assert '"docs/reference/GUIDED_ROUTINE_PACKETS_v0_1.md"' in text
    assert '"tests/test_guided_routines.py"' in text
    assert '"stage_id":"70P","stage_name":"Voice Notes Intelligence / VibeVoice Spike","status":"NEXT_ELIGIBLE"' in text
    assert '"after_commit_next_eligible":"70P"' in text
