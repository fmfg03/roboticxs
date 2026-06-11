from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/VOICE_NOTES_INTELLIGENCE_VIBEVOICE_SPIKE_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_SOURCE_IDS = {
    "microsoft_vibevoice_repo",
    "vibevoice_asr_technical_report",
    "vibevoice_tts_technical_report",
    "vibevoice_tts_docs",
    "roboticxs_project_brief",
    "roboticxs_66p2_memory_boundary",
    "roboticxs_67p_caregiver_boundary",
    "roboticxs_68p_relay_boundary",
    "roboticxs_69p_guided_routine_boundary",
}
REQUIRED_SOURCE_CATEGORIES = {
    "VOICE_ASR",
    "VOICE_TTS",
    "PRODUCT_BOUNDARY",
    "MEMORY_BOUNDARY",
    "CAREGIVER_BOUNDARY",
    "RELAY_BOUNDARY",
    "ROUTINE_BOUNDARY",
}
REQUIRED_CANDIDATES = {
    "VIBEVOICE_ASR",
    "OPENAI_TRANSCRIPTION",
    "LOCAL_WHISPER_OR_FASTER_WHISPER",
    "CLOUD_SPEECH_PROVIDER",
    "NO_VOICE_FOR_NOW",
    "VIBEVOICE_TTS_REJECTED_FOR_V0",
    "VOXCPM_PARKING_LOT",
}
REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "source_channel",
    "audio_ref",
    "audio_retention_policy",
    "transcript_text",
    "transcript_confidence",
    "language_detected",
    "code_switching_detected",
    "speaker_labels_available",
    "speaker_labels_confidence",
    "timestamps_available",
    "hotwords_used",
    "sensitivity_level",
    "contains_caregiver_context",
    "contains_medication_adjacent_content",
    "contains_emergency_like_content",
    "contains_external_action_request",
    "contains_memory_candidate",
    "downstream_decision",
    "requires_human_review",
    "requires_caregiver_confirmation",
    "storage_lane",
    "external_send_authorized",
    "tts_authorized",
    "voice_clone_authorized",
    "background_listening_authorized",
    "created_at",
}
REQUIRED_DECISIONS = {
    "ASK_CLARIFICATION",
    "ROUTE_TO_CONVERSATION_CONTINUITY",
    "PROPOSE_MEMORY_REVIEW",
    "PREPARE_ROUTINE_PACKET_REVIEW",
    "PREPARE_CAREGIVER_RELAY_REVIEW",
    "ESCALATE_TO_HUMAN_CAREGIVER",
    "BLOCK_MEDICAL_OR_EMERGENCY_DECISION",
    "BLOCK_EXTERNAL_ACTION",
    "DISCARD_AUDIO",
}
REQUIRED_CONFIDENCE_LEVELS = {"UNKNOWN", "LOW", "MEDIUM", "HIGH"}
REQUIRED_PRIVACY_CLASSES = {
    "RAW_AUDIO",
    "TRANSCRIPT_TEXT",
    "SENSITIVE_CAREGIVER_TRANSCRIPT",
    "SPEAKER_LABELS",
    "HOTWORDS",
    "VOICE_METADATA",
}
REQUIRED_BUDGET_CLASSES = {
    "VOICE_SHORT_NOTE",
    "VOICE_LONG_NOTE",
    "VOICE_MULTI_SPEAKER",
    "VOICE_CAREGIVER_SENSITIVE",
    "VOICE_RESEARCH_LONG_FORM",
}
REQUIRED_NON_CLAIMS = [
    "Roboticxs does not identify a person by voice in 70P.",
    "Roboticxs does not authenticate a user by voice in 70P.",
    "Roboticxs does not clone voices.",
    "Roboticxs does not generate caregiver voices.",
    "Roboticxs does not continuously listen.",
    "Roboticxs does not store raw audio durably in 70P.",
    "Roboticxs does not store transcripts durably in 70P.",
    "Roboticxs does not execute actions from voice notes.",
    "Roboticxs does not treat transcripts as confirmed memory.",
    "Roboticxs does not treat speaker labels as identity proof.",
]


def load_json_block(block_name: str, path: Path = DOC_PATH):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path.name} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_voice_spike_policy_exists_and_blocks_runtime_behavior():
    policy = load_json_block("voice-spike-policy")

    assert policy["stage_id"] == "70P"
    for field in [
        "voice_runtime_authorized",
        "audio_upload_handling_authorized",
        "asr_inference_authorized",
        "external_audio_api_authorized",
        "model_download_authorized",
        "model_weights_authorized",
        "tts_authorized",
        "voice_clone_authorized",
        "speaker_identification_authorized",
        "voice_authentication_authorized",
        "background_listening_authorized",
        "raw_audio_durable_storage_authorized",
        "durable_transcript_storage_authorized",
        "caregiver_voice_runtime_authorized",
        "external_send_authorized",
    ]:
        assert policy[field] is False


def test_research_source_register_includes_required_sources():
    sources = load_json_block("voice-research-source-register")
    source_ids = [source["source_id"] for source in sources]
    required_fields = {
        "source_id",
        "category",
        "title",
        "organization_or_origin",
        "source_type",
        "research_use",
        "boundary_implication",
    }

    assert set(source_ids) == REQUIRED_SOURCE_IDS
    assert len(source_ids) == len(set(source_ids))
    for source in sources:
        assert set(source) == required_fields
        assert source["category"] in REQUIRED_SOURCE_CATEGORIES


def test_vibevoice_asr_and_tts_are_distinguished():
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in load_json_block("voice-technology-candidate-registry")
    }

    assert candidates["VIBEVOICE_ASR"]["candidate_type"] == "ASR"
    assert candidates["VIBEVOICE_ASR"]["implementation_status"] == "EVALUATION_ONLY"
    assert candidates["VIBEVOICE_ASR"]["authorized_in_70P"] is False
    assert candidates["VIBEVOICE_TTS_REJECTED_FOR_V0"]["candidate_type"] == "TTS"
    assert candidates["VIBEVOICE_TTS_REJECTED_FOR_V0"]["implementation_status"] == "REJECTED_FOR_V0"
    assert candidates["VIBEVOICE_TTS_REJECTED_FOR_V0"]["authorized_in_70P"] is False


def test_technology_candidate_registry_contains_required_candidates():
    candidates = load_json_block("voice-technology-candidate-registry")
    candidate_ids = [candidate["candidate_id"] for candidate in candidates]
    allowed_statuses = {"EVALUATION_ONLY", "REJECTED_FOR_V0", "PARKING_LOT", "NOT_SELECTED"}

    assert set(candidate_ids) == REQUIRED_CANDIDATES
    assert len(candidate_ids) == len(set(candidate_ids))
    for candidate in candidates:
        assert candidate["implementation_status"] in allowed_statuses
        assert candidate["authorized_in_70P"] is False
    assert {
        candidate["candidate_id"]: candidate["implementation_status"]
        for candidate in candidates
    }["VOXCPM_PARKING_LOT"] == "PARKING_LOT"


def test_voice_note_packet_contract_contains_required_fields_and_invariants():
    contract = load_json_block("voice-note-packet-contract")

    assert contract["packet_name"] == "VoiceNoteIntelligencePacket"
    assert set(contract["required_fields"]) == REQUIRED_PACKET_FIELDS
    assert len(contract["required_fields"]) == len(set(contract["required_fields"]))
    assert contract["required_invariants"] == {
        "external_send_authorized": False,
        "tts_authorized": False,
        "voice_clone_authorized": False,
        "background_listening_authorized": False,
    }


def test_downstream_decision_registry_contains_required_decisions_and_no_external_send():
    decisions = load_json_block("voice-downstream-decision-registry")
    decision_ids = [decision["decision_id"] for decision in decisions]
    required_fields = {
        "decision_id",
        "description",
        "allowed_effect",
        "forbidden_effect",
        "requires_human_review",
        "requires_caregiver_confirmation",
        "storage_lane",
        "downstream_stage",
    }

    assert set(decision_ids) == REQUIRED_DECISIONS
    assert len(decision_ids) == len(set(decision_ids))
    for decision in decisions:
        assert set(decision) == required_fields
        assert "external_send" in decision["forbidden_effect"]
    assert {
        decision["decision_id"]: decision
        for decision in decisions
    }["PREPARE_CAREGIVER_RELAY_REVIEW"]["requires_caregiver_confirmation"] is True
    assert {
        decision["decision_id"]: decision
        for decision in decisions
    }["BLOCK_MEDICAL_OR_EMERGENCY_DECISION"]["requires_caregiver_confirmation"] is True


def test_confidence_policy_blocks_low_confidence_packet_creation():
    policy = {
        entry["confidence_level"]: entry
        for entry in load_json_block("voice-confidence-policy")
    }

    assert set(policy) == REQUIRED_CONFIDENCE_LEVELS
    assert policy["LOW"]["can_create_memory_proposal"] is False
    assert policy["LOW"]["can_prepare_routine_packet"] is False
    assert policy["LOW"]["can_prepare_caregiver_relay"] is False
    assert policy["UNKNOWN"]["requires_human_review"] is True


def test_privacy_retention_policy_blocks_durable_raw_audio_and_transcripts():
    policies = {
        policy["data_class"]: policy
        for policy in load_json_block("voice-privacy-retention-policy")
    }

    assert set(policies) == REQUIRED_PRIVACY_CLASSES
    for data_class in [
        "RAW_AUDIO",
        "TRANSCRIPT_TEXT",
        "SENSITIVE_CAREGIVER_TRANSCRIPT",
    ]:
        assert policies[data_class]["durable_storage_authorized_in_70P"] is False
        assert policies[data_class]["delete_after_processing_default"] is True


def test_budget_registry_contains_classes_and_requires_checks_for_costly_audio():
    budgets = {
        budget["budget_class"]: budget
        for budget in load_json_block("voice-budget-class-registry")
    }

    assert set(budgets) == REQUIRED_BUDGET_CLASSES
    assert budgets["VOICE_LONG_NOTE"]["requires_budget_check"] is True
    assert budgets["VOICE_MULTI_SPEAKER"]["requires_budget_check"] is True
    assert budgets["VOICE_CAREGIVER_SENSITIVE"]["requires_privacy_review"] is True
    assert all(budget["background_processing_authorized"] is False for budget in budgets.values())


def test_docs_contain_required_research_findings_and_non_claims():
    text = DOC_PATH.read_text()

    for required in [
        "long-form speech-to-text",
        "speaker, timestamp, and content",
        "multilingual and code-switching support",
        "prompt-based context injection",
        "VibeVoice-TTS is not the Roboticxs v0 target.",
        "Speaker labels are not identity verification.",
        "Transcription confidence does not equal action authority.",
        "Voice-derived memory candidates require the same approval path as text-derived memory.",
        "Voice caregiver content remains sensitive and session-only unless a future approved stage changes that.",
        "Voice cost must be governed before long or multi-speaker audio processing.",
        "71P Voice Intake for Caregiver Routines may open only after 70P closes.",
    ]:
        assert required in text
    for non_claim in REQUIRED_NON_CLAIMS:
        assert non_claim in text


def test_roadmap_marks_70p_completed_and_71p_next_after_closeout():
    stages = load_json_block("canonical-stage-registry", path=ROADMAP_PATH)
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    transition = load_json_block("stage-70p-completion-transition", path=ROADMAP_PATH)

    assert stages_by_id["70P"] == {
        "stage_id": "70P",
        "stage_name": "Voice Notes Intelligence / VibeVoice Spike",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_70P_closeout",
            "paths": [
                "docs/reference/VOICE_NOTES_INTELLIGENCE_VIBEVOICE_SPIKE_v0_1.md",
                "tests/test_voice_notes_intelligence_spike.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the voice-note intelligence boundary; no voice runtime, ASR inference, TTS, cloned voice, audio storage, durable transcript storage, background listening, caregiver voice runtime, or external send is authorized.",
    }
    assert stages_by_id["71P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert [stage["stage_id"] for stage in next_eligible] == ["72P"]
    assert next_eligible[0]["stage_name"] == "Research Radar / Last30Days Skill"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "71P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
