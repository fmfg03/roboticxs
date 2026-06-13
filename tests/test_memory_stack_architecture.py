from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_LANES = {
    "EXISTING_HERMES_MEMORY",
    "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "FUTURE_CRITERIO_STORE",
    "SESSION_ONLY_OR_DO_NOT_STORE",
}
REQUIRED_ITEM_CLASSES = {
    "FACT",
    "PREFERENCE",
    "GOAL",
    "VALUE",
    "RISK",
    "OPERATING_PATTERN",
    "COMMUNICATION_STYLE",
    "PROJECT_CONTEXT",
    "OPEN_LOOP",
    "DECISION",
    "INFERENCE",
    "STRATEGIC_OPINION",
    "SYNTHESIS",
    "PRIORITY_GATE_DECISION",
    "DAILY_START_CONTEXT",
    "BOUNDARY",
    "CAREGIVER_CONTEXT_FUTURE",
}
REQUIRED_CAREGIVER_CLASSES = {
    "MEDICATION_ADJACENT_ROUTINE",
    "HEARING_AID_ROUTINE",
    "FAMILY_SUPERVISION_NOTE",
    "ROUTINE_COMPLETION_STATE",
    "SENSITIVE_HEALTH_CONTEXT",
    "ESCALATION_PREFERENCE",
    "NEVER_STORE_CAREGIVER_DATA",
}
REQUIRED_ITEM_FIELDS = {
    "item_class",
    "default_storage_lane",
    "authority_level",
    "confirmation_required",
    "expiration_policy",
    "allowed_influence_scope",
    "export_policy",
    "deletion_policy",
    "caregiver_allowed_before_67P",
    "mirix_required_now",
    "notes",
}
FORBIDDEN_AUTHORIZATIONS = [
    "connector_authorized",
    "external_retrieval_authorized",
    "browser_email_whatsapp_authorized",
    "crm_lead_gen_handoff_authorized",
    "external_writes_authorized",
]


def load_json_block(block_name: str, path: Path = DOC_PATH):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path.name} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_memory_authority_policy_exists_and_is_non_authorizing():
    policy = load_json_block("memory-authority-policy")

    assert policy["runtime_base"] == "Hermes Agent"
    assert policy["existing_memory_is_authoritative_only_where_verified"] is True
    assert policy["memory_is_authority_surface"] is True
    assert policy["user_approval_required_for_durable_sensitive_memory"] is True
    assert policy["system_inference_is_never_confirmed_fact"] is True
    assert policy["mirix_implementation_authorized"] is False
    assert policy["new_storage_authorized"] is False
    assert policy["caregiver_behavior_authorized"] is False
    for field in FORBIDDEN_AUTHORIZATIONS:
        assert policy[field] is False


def test_storage_lane_registry_contains_required_lanes_exactly_once():
    lanes = load_json_block("storage-lane-registry")
    lane_ids = [lane["lane_id"] for lane in lanes]

    assert set(lane_ids) == REQUIRED_LANES
    assert len(lane_ids) == len(set(lane_ids))


def test_storage_lanes_have_required_fields_and_statuses():
    lanes = load_json_block("storage-lane-registry")
    required_fields = {
        "lane_id",
        "description",
        "allowed_item_classes",
        "forbidden_item_classes",
        "authority_requirements",
        "implementation_status",
        "reopen_requirements",
    }
    allowed_statuses = {
        "EXISTING_CONFIRMED",
        "EXISTING_NEEDS_VERIFICATION",
        "ARCHITECTURE_ONLY",
        "BLOCKED_FOR_DURABLE_STORAGE",
    }

    for lane in lanes:
        assert set(lane) == required_fields
        assert lane["implementation_status"] in allowed_statuses
        assert lane["authority_requirements"]
        assert lane["reopen_requirements"]


def test_every_required_continuity_item_class_is_mapped_once():
    entries = load_json_block("continuity-item-storage-map")
    item_classes = [entry["item_class"] for entry in entries]

    assert set(item_classes) == REQUIRED_ITEM_CLASSES
    assert len(item_classes) == len(set(item_classes))


def test_every_item_class_has_authority_export_delete_and_influence_policy():
    entries = load_json_block("continuity-item-storage-map")

    for entry in entries:
        assert set(entry) == REQUIRED_ITEM_FIELDS
        assert entry["default_storage_lane"] in REQUIRED_LANES
        assert entry["authority_level"]
        assert isinstance(entry["confirmation_required"], bool)
        assert entry["expiration_policy"] in {
            "NONE",
            "SESSION",
            "DATE_BASED",
            "STALE_AFTER_DAYS",
            "RECONFIRM_BEFORE_USE",
        }
        assert entry["allowed_influence_scope"]
        assert entry["export_policy"]
        assert entry["deletion_policy"]
        assert isinstance(entry["caregiver_allowed_before_67P"], bool)
        assert entry["mirix_required_now"] is False


def test_sensitive_inference_cannot_map_directly_to_durable_confirmed_memory():
    entries = {entry["item_class"]: entry for entry in load_json_block("continuity-item-storage-map")}
    inference = entries["INFERENCE"]
    operating_pattern = entries["OPERATING_PATTERN"]

    assert inference["authority_level"] == "SYSTEM_INFERENCE"
    assert inference["default_storage_lane"] == "SESSION_ONLY_OR_DO_NOT_STORE"
    assert inference["confirmation_required"] is True
    assert "DO_NOT_USE_FOR_DECISIONS" in inference["allowed_influence_scope"]
    assert operating_pattern["authority_level"] == "SYSTEM_INFERENCE"
    assert operating_pattern["confirmation_required"] is True
    assert operating_pattern["default_storage_lane"] == "FUTURE_CRITERIO_STORE"


def test_current_memory_flow_preserves_approval_reject_and_forget_semantics():
    text = DOC_PATH.read_text()
    lanes = {lane["lane_id"]: lane for lane in load_json_block("storage-lane-registry")}
    current = lanes["CURRENT_ROBOTICXS_MEMORY_FLOW"]

    assert current["implementation_status"] == "EXISTING_CONFIRMED"
    assert "user_approval_preserved" in current["authority_requirements"]
    assert "reject_preserved" in current["authority_requirements"]
    assert "forget_preserved" in current["authority_requirements"]
    assert "ProposedMemory" in text
    assert "MemoryItem" in text
    assert "forget behavior" in text


def test_future_criterio_store_is_architecture_only_and_not_implementation_authority():
    lanes = {lane["lane_id"]: lane for lane in load_json_block("storage-lane-registry")}
    future = lanes["FUTURE_CRITERIO_STORE"]

    assert future["implementation_status"] == "ARCHITECTURE_ONLY"
    assert "approved_story" in future["reopen_requirements"]
    assert "approved_technical_spec" in future["reopen_requirements"]
    assert "migration_plan" in future["reopen_requirements"]


def test_synthesis_priority_and_daily_start_do_not_require_mirix_now():
    entries = {entry["item_class"]: entry for entry in load_json_block("continuity-item-storage-map")}

    for item_class in {"SYNTHESIS", "PRIORITY_GATE_DECISION", "DAILY_START_CONTEXT"}:
        entry = entries[item_class]
        assert entry["mirix_required_now"] is False
        assert entry["default_storage_lane"] in {"FUTURE_CRITERIO_STORE", "SESSION_ONLY_OR_DO_NOT_STORE"}


def test_mirix_evaluation_frame_is_present_and_non_authorizing():
    frame = load_json_block("mirix-evaluation-frame")

    assert frame["decision_status"] == "DESIGN_CRITERIO_STORE"
    assert frame["not_authorized_in_66P2"] is True
    assert "typed_memory" in frame["evaluation_criteria"]
    assert "deletion_forget_semantics" in frame["evaluation_criteria"]
    assert "current_stack_gap_analysis" in frame["minimum_evidence_required"]
    assert frame["blocked_until"] == "future_approved_memory_architecture_stage"


def test_caregiver_prerequisite_registry_blocks_use_before_67p():
    entries = load_json_block("caregiver-memory-prerequisite")
    caregiver_classes = [entry["caregiver_memory_class"] for entry in entries]

    assert set(caregiver_classes) == REQUIRED_CAREGIVER_CLASSES
    assert len(caregiver_classes) == len(set(caregiver_classes))
    for entry in entries:
        assert entry["storage_lane_before_67P"] == "SESSION_ONLY_OR_DO_NOT_STORE"
        assert entry["allowed_use_before_67P"] is False
        assert entry["blocked_behavior"]
        assert entry["notes"]


def test_sensitive_caregiver_context_is_not_confirmed_durable_memory():
    entries = {
        entry["caregiver_memory_class"]: entry for entry in load_json_block("caregiver-memory-prerequisite")
    }
    sensitive = entries["SENSITIVE_HEALTH_CONTEXT"]
    never_store = entries["NEVER_STORE_CAREGIVER_DATA"]

    assert sensitive["storage_lane_before_67P"] == "SESSION_ONLY_OR_DO_NOT_STORE"
    assert sensitive["confirmation_required"] is True
    assert sensitive["allowed_use_before_67P"] is False
    assert never_store["blocked_behavior"] == "never_store_and_never_use_for_decisions"


def test_no_registry_authorizes_external_or_runtime_expansion():
    text = DOC_PATH.read_text()
    policy = load_json_block("memory-authority-policy")

    assert policy["caregiver_behavior_authorized"] is False
    for field in FORBIDDEN_AUTHORIZATIONS:
        assert policy[field] is False
    for forbidden in [
        "storage migration",
        "new backend",
        "Mirix implementation",
        "vector store",
        "graph store",
        "connector retrieval",
        "cross-thread retrieval",
        "browser, email, or WhatsApp execution",
        "caregiver behavior",
        "voice behavior",
        "Research Radar",
        "CRM, lead-gen, pipeline, or handoff",
        "external writes",
    ]:
        assert forbidden in text


def test_roadmap_keeps_66p2_completed_after_67p_closeout():
    stages = load_json_block("canonical-stage-registry", path=ROADMAP_PATH)
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]

    assert stages_by_id["66P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["66P2"]["stage_name"] == "Memory Stack Architecture / Criterio Store Spec"
    assert stages_by_id["66P2"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["66P2"]["local_evidence"] == {
        "commit": "same_commit_as_66P2_closeout",
        "paths": [
            "docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md",
            "tests/test_memory_stack_architecture.py",
            "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
            "tests/test_canonical_roadmap.py",
        ],
    }
    assert stages_by_id["68P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["69P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["70P"]["stage_name"] == "Voice Notes Intelligence / VibeVoice Spike"
    assert stages_by_id["70P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert [stage["stage_id"] for stage in next_eligible] == ["75P"]
    assert next_eligible[0]["stage_name"] == "Agent-Reach Research Parking Lot"
