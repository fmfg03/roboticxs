from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

import pytest

from app.caregiver_relay import CaregiverRelayPacket
from app.guided_routines import GuidedRoutinePacket
from app.voice_caregiver_intake import (
    TranscriptConfidence,
    VoiceCaregiverIntakeDecision,
    VoiceCaregiverIntakePacket,
    VoiceCaregiverIntakeRequest,
    VoiceCaregiverSensitivity,
    VoiceCaregiverSourceChannel,
    build_voice_caregiver_intake_packet,
    classify_voice_caregiver_intake,
    should_prepare_caregiver_relay_review,
    should_prepare_guided_routine_review,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/VOICE_INTAKE_FOR_CAREGIVER_ROUTINES_v0_1.md"
ROADMAP_PATH = Path(__file__).resolve().parents[1] / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "source_channel",
    "transcript_text",
    "transcript_confidence",
    "language_detected",
    "code_switching_detected",
    "caregiver_context_detected",
    "routine_intent_detected",
    "medication_adjacent_detected",
    "medical_decision_requested",
    "dosage_or_schedule_requested",
    "ingestion_verification_requested",
    "emergency_like_detected",
    "surveillance_requested",
    "external_action_requested",
    "sensitive_context_detected",
    "intake_decision",
    "requires_human_review",
    "requires_caregiver_confirmation",
    "storage_lane",
    "audio_processing_authorized",
    "asr_runtime_authorized",
    "external_send_authorized",
    "tts_authorized",
    "voice_clone_authorized",
    "background_listening_authorized",
    "durable_transcript_storage_authorized",
    "voice_authentication_authorized",
    "routine_packet_review",
    "relay_packet_review",
    "blocked_reason",
    "future_stage_required",
    "created_at",
}


def request(**overrides) -> VoiceCaregiverIntakeRequest:
    values = {
        "source_channel": "VOICE_TRANSCRIPT_STUB",
        "transcript_text": "She forgot her hearing aids again.",
        "transcript_confidence": "HIGH",
        "language_detected": "en",
        "intended_user": "mother-in-law",
    }
    values.update(overrides)
    return VoiceCaregiverIntakeRequest(**values)


def test_voice_caregiver_taxonomies_are_explicit():
    assert set(get_args(VoiceCaregiverSourceChannel)) == {
        "VOICE_TRANSCRIPT_STUB",
        "USER_PROVIDED_TRANSCRIPT",
        "TEST_FIXTURE_TRANSCRIPT",
    }
    assert set(get_args(TranscriptConfidence)) == {"UNKNOWN", "LOW", "MEDIUM", "HIGH"}
    assert set(get_args(VoiceCaregiverIntakeDecision)) == {
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
    }
    assert set(get_args(VoiceCaregiverSensitivity)) == {"LOW", "MEDIUM", "HIGH", "SENSITIVE"}


def test_valid_transcript_source_channels_are_accepted():
    for source_channel in [
        "VOICE_TRANSCRIPT_STUB",
        "USER_PROVIDED_TRANSCRIPT",
        "TEST_FIXTURE_TRANSCRIPT",
    ]:
        packet = build_voice_caregiver_intake_packet(request(source_channel=source_channel))
        assert packet.source_channel == source_channel


def test_blocked_audio_source_channels_are_rejected():
    for blocked_source in [
        "TELEGRAM_VOICE_FILE",
        "AUDIO_UPLOAD",
        "LIVE_MICROPHONE",
        "BACKGROUND_AUDIO_STREAM",
        "EXTERNAL_ASR_RESULT_AUTO_ACCEPTED",
    ]:
        with pytest.raises(ValueError):
            request(source_channel=blocked_source)


def test_audio_reference_text_is_rejected():
    with pytest.raises(ValueError):
        request(transcript_text="file://voice-note.ogg")


def test_intake_packet_contains_required_fields():
    packet = build_voice_caregiver_intake_packet(request())

    assert isinstance(packet, VoiceCaregiverIntakePacket)
    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_id.startswith("voice_caregiver_intake_")


def test_all_no_runtime_no_send_invariants_are_disabled():
    scenarios = [
        request(),
        request(transcript_confidence="LOW"),
        request(transcript_text="She is confused about whether she took her pill.", medication_adjacent=True),
        request(transcript_text="Tell her which pill to take tonight.", medical_decision_requested=True),
        request(transcript_text="She fell and cannot get up.", emergency_like=True),
        request(transcript_text="Keep listening all day.", surveillance_requested=True),
        request(transcript_text="Send the family group an update.", external_action_requested=True),
    ]

    for scenario in scenarios:
        packet = build_voice_caregiver_intake_packet(scenario)
        assert packet.audio_processing_authorized is False
        assert packet.asr_runtime_authorized is False
        assert packet.external_send_authorized is False
        assert packet.tts_authorized is False
        assert packet.voice_clone_authorized is False
        assert packet.background_listening_authorized is False
        assert packet.durable_transcript_storage_authorized is False
        assert packet.voice_authentication_authorized is False


def test_low_confidence_asks_clarification_without_review_packets():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_confidence="LOW", routine_intent_present=True, caregiver_context_present=True)
    )

    assert packet.intake_decision == "ASK_CLARIFICATION"
    assert packet.requires_human_review is True
    assert packet.routine_packet_review is None
    assert packet.relay_packet_review is None
    assert should_prepare_guided_routine_review(request(transcript_confidence="LOW")) is False


def test_unknown_confidence_asks_clarification_and_requires_human_review():
    packet = build_voice_caregiver_intake_packet(request(transcript_confidence="UNKNOWN"))

    assert packet.intake_decision == "ASK_CLARIFICATION"
    assert packet.requires_human_review is True


def test_safe_hearing_aid_transcript_prepares_review_only_routine_packet():
    packet = build_voice_caregiver_intake_packet(request())

    assert packet.intake_decision == "PREPARE_ROUTINE_PACKET_REVIEW"
    assert packet.routine_intent_detected is True
    assert isinstance(packet.routine_packet_review, GuidedRoutinePacket)
    assert packet.routine_packet_review.routine_type == "HEARING_AID_ROUTINE"
    assert packet.routine_packet_review.external_send_authorized is False
    assert packet.routine_packet_review.session_only_progress is True
    assert packet.relay_packet_review is None


def test_medication_adjacent_transcript_requires_caregiver_confirmation():
    packet = build_voice_caregiver_intake_packet(
        request(
            transcript_text="Mamá está confundida con el pastillero.",
            transcript_confidence="MEDIUM",
            language_detected="es",
        )
    )

    assert packet.intake_decision == "PREPARE_MEDICATION_ADJACENT_REVIEW"
    assert packet.medication_adjacent_detected is True
    assert packet.requires_caregiver_confirmation is True
    assert isinstance(packet.routine_packet_review, GuidedRoutinePacket)
    assert packet.routine_packet_review.routine_type == "MEDICATION_ADJACENT_CHECKLIST"
    assert isinstance(packet.relay_packet_review, CaregiverRelayPacket)
    assert packet.relay_packet_review.packet_type == "CAREGIVER_CONFIRMATION_REQUEST"


def test_medication_adjacent_uncertainty_is_review_not_ingestion_verification():
    packet = build_voice_caregiver_intake_packet(
        request(
            transcript_text="She is confused about whether she took her pill.",
            transcript_confidence="HIGH",
        )
    )

    assert packet.intake_decision == "PREPARE_MEDICATION_ADJACENT_REVIEW"
    assert packet.medication_adjacent_detected is True
    assert packet.ingestion_verification_requested is False
    assert packet.requires_caregiver_confirmation is True


def test_medication_dosage_schedule_or_selection_request_blocks():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="Tell her which pill to take tonight.")
    )

    assert classify_voice_caregiver_intake(request(transcript_text="Tell her which pill to take tonight.")) == "BLOCK_MEDICAL_DECISION"
    assert packet.intake_decision == "BLOCK_MEDICAL_DECISION"
    assert packet.routine_packet_review is None
    assert packet.relay_packet_review is None
    assert packet.blocked_reason == "Medication selection, dosage, schedule, or ingestion verification is outside Roboticxs v0."


def test_ingestion_verification_request_blocks():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="Confirmar que tomó la pastilla.", transcript_confidence="HIGH")
    )

    assert packet.intake_decision == "BLOCK_MEDICAL_DECISION"
    assert packet.ingestion_verification_requested is True
    assert packet.routine_packet_review is None


def test_emergency_like_transcript_escalates_without_guided_routine():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="She fell and cannot get up.", emergency_like=True)
    )

    assert packet.intake_decision == "ESCALATE_TO_HUMAN_CAREGIVER"
    assert packet.requires_human_review is True
    assert packet.routine_packet_review is None
    assert isinstance(packet.relay_packet_review, CaregiverRelayPacket)
    assert packet.relay_packet_review.packet_type == "SENSITIVE_CONTEXT_REVIEW_REQUEST"
    assert packet.relay_packet_review.emergency_claim_authorized is False


def test_surveillance_background_listening_request_blocks():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="Keep listening all day and tell me if she leaves the room.")
    )

    assert packet.intake_decision == "BLOCK_SURVEILLANCE"
    assert packet.blocked_reason == "Background listening or continuous monitoring is outside Roboticxs v0."
    assert packet.background_listening_authorized is False


def test_external_action_request_blocks():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="Send the family group a message now.", external_action_requested=True)
    )

    assert packet.intake_decision == "BLOCK_EXTERNAL_ACTION"
    assert packet.future_stage_required == "future_explicit_external_action_authority"
    assert packet.external_send_authorized is False


def test_sensitive_context_triggers_caregiver_relay_review_only():
    packet = build_voice_caregiver_intake_packet(
        request(
            transcript_text="She seemed very confused today.",
            routine_intent_present=False,
            caregiver_context_present=True,
            sensitive_context_present=True,
        )
    )

    assert packet.intake_decision == "PREPARE_CAREGIVER_RELAY_REVIEW"
    assert packet.routine_packet_review is None
    assert isinstance(packet.relay_packet_review, CaregiverRelayPacket)
    assert packet.relay_packet_review.packet_type == "SENSITIVE_CONTEXT_REVIEW_REQUEST"
    assert should_prepare_caregiver_relay_review(request(caregiver_context_present=True, sensitive_context_present=True)) is True


def test_non_caregiver_transcript_routes_to_conversation_continuity_review():
    packet = build_voice_caregiver_intake_packet(
        request(
            transcript_text="I want to plan tomorrow's work.",
            routine_intent_present=False,
            caregiver_context_present=False,
            sensitive_context_present=False,
            routine_hint="custom",
        )
    )

    assert packet.intake_decision == "ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW"
    assert packet.routine_packet_review is None
    assert packet.relay_packet_review is None


def test_empty_transcript_discards_or_no_action():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="", transcript_confidence="HIGH", routine_hint="custom")
    )

    assert packet.intake_decision == "DISCARD_OR_NO_ACTION"


def test_decision_precedence_is_deterministic():
    scenario = request(
        external_action_requested=True,
        surveillance_requested=True,
        medical_decision_requested=True,
        emergency_like=True,
        medication_adjacent=True,
        routine_intent_present=True,
        caregiver_context_present=True,
    )

    assert classify_voice_caregiver_intake(scenario) == "BLOCK_EXTERNAL_ACTION"


def test_routine_handoff_preserves_69p_invariants():
    packet = build_voice_caregiver_intake_packet(request())
    routine = packet.routine_packet_review

    assert isinstance(routine, GuidedRoutinePacket)
    assert routine.external_send_authorized is False
    assert routine.background_reminder_authorized is False
    assert routine.medical_decision_authorized is False
    assert routine.dosage_decision_authorized is False
    assert routine.medication_schedule_authorized is False
    assert routine.ingestion_verification_authorized is False
    assert routine.emergency_claim_authorized is False
    assert routine.surveillance_authorized is False
    assert routine.session_only_progress is True


def test_relay_handoff_preserves_68p_invariants():
    packet = build_voice_caregiver_intake_packet(
        request(transcript_text="Mamá está confundida con el pastillero.", transcript_confidence="MEDIUM")
    )
    relay = packet.relay_packet_review

    assert isinstance(relay, CaregiverRelayPacket)
    assert relay.external_send_authorized is False
    assert relay.medical_decision_authorized is False
    assert relay.emergency_claim_authorized is False
    assert relay.routine_execution_authorized is False


def test_storage_lane_remains_session_only():
    packet = build_voice_caregiver_intake_packet(request())

    assert packet.storage_lane == "SESSION_ONLY_OR_DO_NOT_STORE"
    assert packet.durable_transcript_storage_authorized is False


def test_docs_contain_required_non_claims_and_closeout_note():
    text = DOC_PATH.read_text()

    for required in [
        "transcript-stub caregiver intake bridge",
        "Roboticxs does not process audio in 71P.",
        "Roboticxs does not transcribe voice in 71P.",
        "Roboticxs does not handle Telegram voice files in 71P.",
        "Roboticxs does not run VibeVoice or Whisper in 71P.",
        "Roboticxs does not identify or authenticate speakers in 71P.",
        "Roboticxs does not treat a transcript as user confirmation.",
        "Roboticxs does not store transcripts durably in 71P.",
        "Roboticxs does not execute routines from voice intake.",
        "Roboticxs does not send caregiver messages automatically.",
        "Roboticxs does not make medication decisions.",
        "Roboticxs does not provide emergency response.",
        "Roboticxs does not perform surveillance or background listening.",
        "72P Research Radar / Last30Days Skill becomes the next eligible stage.",
    ]:
        assert required in text


def test_roadmap_marks_71p_completed_and_72p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"71P","stage_name":"Voice Intake for Caregiver Routines","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_71P_closeout"' in text
    assert '"app/voice_caregiver_intake.py"' in text
    assert '"docs/reference/VOICE_INTAKE_FOR_CAREGIVER_ROUTINES_v0_1.md"' in text
    assert '"tests/test_voice_caregiver_intake.py"' in text
    assert '"stage_id":"72P","stage_name":"Research Radar / Last30Days Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"NEXT_ELIGIBLE"' in text
    assert '"after_commit_next_eligible":"74P"' in text
