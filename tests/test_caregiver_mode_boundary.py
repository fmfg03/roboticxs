from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/CAREGIVER_MODE_BOUNDARY_SPEC_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_SOURCE_CATEGORIES = {
    "DEMENTIA_CAREGIVING",
    "MEDICATION_SAFETY",
    "MEDICINES_SUPPORT",
    "HOME_SAFETY",
    "ASSISTIVE_TECHNOLOGY",
    "CAREGIVER_SUPPORT",
}
REQUIRED_BOUNDARY_CATEGORIES = {
    "ALLOW_PREPARATION_ONLY",
    "ALLOW_ROUTINE_GUIDANCE_LATER",
    "ASK_CAREGIVER_CONFIRMATION",
    "REQUIRE_HUMAN_SUPERVISION",
    "ESCALATE_TO_CAREGIVER",
    "BLOCK_MEDICAL_DECISION",
    "BLOCK_SURVEILLANCE",
    "BLOCK_EXTERNAL_ACTION",
    "DEFER_TO_FUTURE_STAGE",
}
REQUIRED_CAPABILITIES = {
    "caregiver_approved_checklist",
    "hearing_aid_routine_prompt",
    "hydration_or_meal_routine_prompt",
    "appointment_preparation_note",
    "family_visible_routine_summary",
    "step_by_step_routine_guidance",
    "caregiver_handoff_draft",
    "medication_adjacent_routine",
    "pillbox_checklist_step",
    "routine_schedule_change",
    "store_caregiver_sensitive_context",
    "contact_family_member",
    "escalate_concern_to_caregiver",
    "mark_routine_completed",
    "medication_dosage_decision",
    "medication_substitution",
    "medical_advice",
    "diagnosis",
    "emergency_triage",
    "fall_detection_claim",
    "ingestion_verification_as_clinical_truth",
    "hidden_monitoring",
    "continuous_surveillance",
    "automatic_family_alert_without_approval",
    "external_action_without_approval_packet",
}
REQUIRED_MEMORY_CLASSES = {
    "MEDICATION_ADJACENT_ROUTINE",
    "HEARING_AID_ROUTINE",
    "FAMILY_SUPERVISION_NOTE",
    "ROUTINE_COMPLETION_STATE",
    "SENSITIVE_HEALTH_CONTEXT",
    "ESCALATION_PREFERENCE",
    "NEVER_STORE_CAREGIVER_DATA",
}
REQUIRED_FUTURE_GATES = {
    "68P_CAREGIVER_TELEGRAM_GROUP_RELAY",
    "69P_GUIDED_ROUTINE_PACKETS",
    "71P_VOICE_INTAKE_FOR_CAREGIVER_ROUTINES",
}


def load_json_block(block_name: str, path: Path = DOC_PATH):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path.name} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_source_register_contains_required_research_categories():
    sources = load_json_block("caregiver-research-source-register")
    categories = {source["category"] for source in sources}

    assert REQUIRED_SOURCE_CATEGORIES <= categories
    for source in sources:
        assert {
            "source_id",
            "category",
            "organization",
            "source_type",
            "title",
            "url_or_reference",
            "research_use",
            "boundary_implication",
        } == set(source)
        assert source["url_or_reference"].startswith("https://")
        assert source["research_use"]
        assert source["boundary_implication"]


def test_caregiver_policy_disables_runtime_and_sensitive_authority():
    policy = load_json_block("caregiver-boundary-policy")

    for field in [
        "caregiver_runtime_authorized",
        "telegram_relay_authorized",
        "guided_routine_packets_authorized",
        "medication_decision_authorized",
        "medical_advice_authorized",
        "diagnosis_authorized",
        "emergency_triage_authorized",
        "continuous_monitoring_authorized",
        "external_action_authorized",
        "sensitive_durable_memory_authorized",
    ]:
        assert policy[field] is False
    assert policy["human_supervision_required_for_sensitive_routines"] is True
    assert policy["caregiver_confirmation_required_for_medication_adjacent_steps"] is True


def test_boundary_category_registry_contains_required_categories_once():
    categories = load_json_block("caregiver-boundary-category-registry")
    category_ids = [category["category_id"] for category in categories]

    assert set(category_ids) == REQUIRED_BOUNDARY_CATEGORIES
    assert len(category_ids) == len(set(category_ids))
    for category in categories:
        assert {
            "category_id",
            "description",
            "allowed_effect",
            "forbidden_effect",
            "future_stage_requirement",
        } == set(category)


def test_capability_map_contains_required_capabilities_once_with_fields():
    capabilities = load_json_block("caregiver-capability-boundary-map")
    capability_ids = [capability["capability_id"] for capability in capabilities]
    required_fields = {
        "capability_id",
        "display_name",
        "boundary_category",
        "requires_caregiver_confirmation",
        "requires_human_supervision",
        "authorized_in_67P",
        "future_stage",
        "blocked_reason",
        "memory_boundary",
        "external_action_allowed",
    }

    assert set(capability_ids) == REQUIRED_CAPABILITIES
    assert len(capability_ids) == len(set(capability_ids))
    for capability in capabilities:
        assert set(capability) == required_fields
        assert capability["boundary_category"] in REQUIRED_BOUNDARY_CATEGORIES
        assert capability["authorized_in_67P"] is False
        assert capability["external_action_allowed"] is False
        assert capability["blocked_reason"]


def test_medication_decisions_are_blocked():
    capabilities = {
        capability["capability_id"]: capability for capability in load_json_block("caregiver-capability-boundary-map")
    }
    for capability_id in {
        "medication_dosage_decision",
        "medication_substitution",
        "medical_advice",
        "diagnosis",
        "emergency_triage",
        "ingestion_verification_as_clinical_truth",
    }:
        capability = capabilities[capability_id]
        assert capability["boundary_category"] == "BLOCK_MEDICAL_DECISION"
        assert capability["authorized_in_67P"] is False
        assert capability["external_action_allowed"] is False


def test_medication_adjacent_routines_require_caregiver_confirmation():
    capabilities = {
        capability["capability_id"]: capability for capability in load_json_block("caregiver-capability-boundary-map")
    }
    for capability_id in {"medication_adjacent_routine", "pillbox_checklist_step"}:
        capability = capabilities[capability_id]
        assert capability["boundary_category"] == "ASK_CAREGIVER_CONFIRMATION"
        assert capability["requires_caregiver_confirmation"] is True
        assert capability["requires_human_supervision"] is True
        assert capability["authorized_in_67P"] is False


def test_surveillance_and_hidden_monitoring_are_blocked():
    capabilities = {
        capability["capability_id"]: capability for capability in load_json_block("caregiver-capability-boundary-map")
    }
    for capability_id in {"hidden_monitoring", "continuous_surveillance", "fall_detection_claim"}:
        capability = capabilities[capability_id]
        assert capability["boundary_category"] == "BLOCK_SURVEILLANCE"
        assert capability["authorized_in_67P"] is False


def test_external_alerts_and_actions_are_blocked():
    capabilities = {
        capability["capability_id"]: capability for capability in load_json_block("caregiver-capability-boundary-map")
    }
    for capability_id in {
        "automatic_family_alert_without_approval",
        "external_action_without_approval_packet",
        "contact_family_member",
    }:
        capability = capabilities[capability_id]
        assert capability["boundary_category"] == "BLOCK_EXTERNAL_ACTION"
        assert capability["external_action_allowed"] is False


def test_memory_boundary_map_contains_required_classes_and_blocks_67p_use():
    entries = load_json_block("caregiver-memory-boundary-map")
    memory_classes = [entry["memory_class"] for entry in entries]

    assert set(memory_classes) == REQUIRED_MEMORY_CLASSES
    assert len(memory_classes) == len(set(memory_classes))
    for entry in entries:
        assert {
            "memory_class",
            "storage_lane",
            "confirmation_required",
            "sensitive",
            "durable_storage_authorized_in_67P",
            "allowed_use_in_67P",
            "future_stage_requirement",
            "deletion_export_requirement",
        } == set(entry)
        assert entry["storage_lane"] == "SESSION_ONLY_OR_DO_NOT_STORE"
        assert entry["durable_storage_authorized_in_67P"] is False
        assert entry["allowed_use_in_67P"] is False


def test_sensitive_health_context_and_never_store_data_are_constrained():
    entries = {entry["memory_class"]: entry for entry in load_json_block("caregiver-memory-boundary-map")}
    sensitive = entries["SENSITIVE_HEALTH_CONTEXT"]
    never_store = entries["NEVER_STORE_CAREGIVER_DATA"]

    assert sensitive["sensitive"] is True
    assert sensitive["confirmation_required"] is True
    assert sensitive["durable_storage_authorized_in_67P"] is False
    assert never_store["durable_storage_authorized_in_67P"] is False
    assert never_store["allowed_use_in_67P"] is False
    assert never_store["deletion_export_requirement"] == "discard_and_do_not_use_for_decisions"


def test_future_stage_gates_exist_and_are_not_authorized_by_67p():
    gates = load_json_block("future-stage-gates")
    gate_ids = [gate["stage_id"] for gate in gates]

    assert set(gate_ids) == REQUIRED_FUTURE_GATES
    assert len(gate_ids) == len(set(gate_ids))
    for gate in gates:
        assert {
            "stage_id",
            "stage_name",
            "prerequisites_from_67P",
            "authorized_by_67P",
            "required_future_approval",
            "forbidden_until_stage_approval",
        } == set(gate)
        assert gate["authorized_by_67P"] is False
        assert gate["prerequisites_from_67P"]
        assert gate["forbidden_until_stage_approval"]


def test_required_non_claims_are_present():
    text = DOC_PATH.read_text()

    for non_claim in [
        "Roboticxs does not provide medical advice.",
        "Roboticxs does not decide medication dosage or schedule.",
        "Roboticxs does not verify medication ingestion as clinical fact.",
        "Roboticxs does not replace family supervision or professional caregiving.",
        "Roboticxs does not provide emergency response or triage.",
        "Roboticxs does not continuously monitor the person.",
        "Roboticxs does not contact family members automatically.",
        "Roboticxs does not store sensitive caregiver context durably in 67P.",
    ]:
        assert non_claim in text


def test_no_registry_authorizes_caregiver_runtime_or_external_surfaces():
    policy = load_json_block("caregiver-boundary-policy")
    capabilities = load_json_block("caregiver-capability-boundary-map")
    gates = load_json_block("future-stage-gates")

    assert policy["caregiver_runtime_authorized"] is False
    assert policy["telegram_relay_authorized"] is False
    assert policy["guided_routine_packets_authorized"] is False
    assert policy["external_action_authorized"] is False
    assert all(capability["authorized_in_67P"] is False for capability in capabilities)
    assert all(capability["external_action_allowed"] is False for capability in capabilities)
    assert all(gate["authorized_by_67P"] is False for gate in gates)


def test_roadmap_marks_67p_through_69p_completed_and_70p_next_after_closeout():
    stages = load_json_block("canonical-stage-registry", path=ROADMAP_PATH)
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]

    assert stages_by_id["67P"]["stage_name"] == "Caregiver Mode Boundary Spec"
    assert stages_by_id["67P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["67P"]["local_evidence"] == {
        "commit": "same_commit_as_67P_closeout",
        "paths": [
            "docs/reference/CAREGIVER_MODE_BOUNDARY_SPEC_v0_1.md",
            "tests/test_caregiver_mode_boundary.py",
            "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
            "tests/test_canonical_roadmap.py",
        ],
    }
    assert stages_by_id["68P"]["stage_name"] == "Caregiver Telegram Group Relay v0"
    assert stages_by_id["68P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["69P"]["stage_name"] == "Guided Routine Packets v0"
    assert stages_by_id["69P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["70P"]["stage_name"] == "Voice Notes Intelligence / VibeVoice Spike"
    assert stages_by_id["70P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert [stage["stage_id"] for stage in next_eligible] == ["72P"]
    assert next_eligible[0]["stage_name"] == "Research Radar / Last30Days Skill"
