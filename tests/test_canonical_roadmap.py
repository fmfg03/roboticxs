from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
ALLOWED_STAGE_STATUSES = {
    "COMPLETED_FIXED_BASELINE",
    "CURRENT_STAGE",
    "NEXT_ELIGIBLE",
    "SEQUENCE_ENTRY_ONLY",
}
ALLOWED_DEFERRED_CLASSIFICATIONS = {"DEFERRED", "RADAR_ONLY", "PARKING_LOT"}
LOCAL_BASELINE_EVIDENCE = {
    "61P": {
        "commit": "c079a96",
        "path": "docs/reference/COMMAND_ROUTING_CONSOLIDATION_v0_1.md",
    },
    "62P": {
        "commit": "93bcbff",
        "path": "docs/reference/RUNTIME_SURFACE_AUDIT_v0_1.md",
    },
    "63P": {
        "commit": "86afd53",
        "path": "docs/reference/RETRIEVAL_CONTROL_FREEZE_v0_1.md",
    },
}
REQUIRED_BLOCKED_IDS = {
    "total_autonomy",
    "continuous_screen_tracking",
    "authenticated_scraping",
    "automatic_publishing_or_direct_messages",
    "cloned_voice",
    "external_action_without_approval_packet",
    "connector_activation",
    "live_retrieval_execution",
    "browser_email_whatsapp_execution",
    "crm_lead_pipeline_handoff",
    "external_writes",
}
REQUIRED_DEFERRED_IDS = {
    "connector_architecture",
    "live_retrieval",
    "browser_email_whatsapp_execution",
    "external_skills",
    "agent_reach",
    "voxcpm",
}
REQUIRED_SEQUENCE_RULES = {
    "exactly_one_stage_may_be_next_eligible",
    "sole_next_eligible_stage_is_67P",
    "eligibility_permits_story_drafting_only",
    "roadmap_inclusion_never_authorizes_implementation",
    "every_stage_requires_story_approval",
    "every_stage_requires_technical_spec_approval",
    "runtime_implementation_requires_separately_approved_scoped_build_tests_and_validation",
    "stages_68P_through_76P_remain_unopened_until_67P_closes_or_explicit_maintainer_direction_changes_the_canon",
    "sequence_changes_require_explicit_maintainer_approval_and_canonical_roadmap_update",
    "external_repositories_and_recent_planning_threads_cannot_independently_change_sequence",
}
EXPECTED_FINAL_SEQUENCE = {
    "66P": ("COMPLETED_FIXED_BASELINE", "Conversación Horizontal / Continuity Spine v0"),
    "66P2": ("COMPLETED_FIXED_BASELINE", "Memory Stack Architecture / Criterio Store Spec"),
    "67P": ("NEXT_ELIGIBLE", "Caregiver Mode Boundary Spec"),
    "68P": ("SEQUENCE_ENTRY_ONLY", "Caregiver Telegram Group Relay v0"),
    "69P": ("SEQUENCE_ENTRY_ONLY", "Guided Routine Packets v0"),
    "70P": ("SEQUENCE_ENTRY_ONLY", "Voice Notes Intelligence / VibeVoice Spike"),
    "71P": ("SEQUENCE_ENTRY_ONLY", "Voice Intake for Caregiver Routines"),
    "72P": ("SEQUENCE_ENTRY_ONLY", "Research Radar / Last30Days Skill"),
    "73P": ("SEQUENCE_ENTRY_ONLY", "Understand-Anything + codegraph Factory Skill"),
    "74P": ("SEQUENCE_ENTRY_ONLY", "ECC Knowledge Compiler Factory Skill"),
    "75P": ("SEQUENCE_ENTRY_ONLY", "Agent-Reach Research Parking Lot"),
    "76P": ("SEQUENCE_ENTRY_ONLY", "VoxCPM Research Parking Lot"),
}


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(ROADMAP_PATH.read_text())
    assert match is not None, f"Canonical roadmap must contain {block_name}."
    return json.loads(match.group("payload"))


def load_stage_registry() -> list[dict]:
    return load_json_block("canonical-stage-registry")


def test_authority_policy_separates_local_evidence_from_maintainer_direction():
    authority = load_json_block("canonical-roadmap-authority")

    assert authority == {
        "authority_source": "maintainer_approved_chatgpt_web_planning_thread",
        "local_evidence_scope": "stages_61P_through_66P",
        "forward_sequence_source": "explicit_maintainer_direction",
        "runtime_truth_source": "local_repo",
        "roadmap_inclusion_authorizes_implementation": False,
    }


def test_stage_registry_contains_ordered_61p_through_66p2_and_76p_once():
    stages = load_stage_registry()
    stage_ids = [stage["stage_id"] for stage in stages]

    assert stage_ids == [f"{number}P" for number in range(61, 67)] + ["66P2"] + [
        f"{number}P" for number in range(67, 77)
    ]
    assert len(stage_ids) == len(set(stage_ids))
    assert all(stage["status"] in ALLOWED_STAGE_STATUSES for stage in stages)
    assert all(stage["implementation_authorized"] is False for stage in stages)


def test_local_fixed_baselines_have_existing_repo_evidence():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    for stage_id, expected in LOCAL_BASELINE_EVIDENCE.items():
        stage = stages_by_id[stage_id]
        assert stage["status"] == "COMPLETED_FIXED_BASELINE"
        assert stage["authority_source"] == "local_repo_evidence"
        assert stage["local_evidence"] == {
            "commit": expected["commit"],
            "paths": [expected["path"]],
        }
        assert (REPO_ROOT / expected["path"]).is_file()
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{expected['commit']}^{{commit}}"],
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 0


def test_65p_is_committed_before_66p_closure():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    stage = stages_by_id["65P"]

    assert stage["status"] == "COMPLETED_FIXED_BASELINE"
    assert stage["stage_name"] == "Budget Awareness / Cost Authority Guard v0"
    assert stage["local_evidence"] == {
        "commit": "d346939",
        "paths": [
            "app/budget_authority.py",
            "docs/reference/BUDGET_AUTHORITY_GUARD_v0_1.md",
            "tests/test_budget_authority_guard.py",
        ],
    }
    result = subprocess.run(
        ["git", "cat-file", "-e", "d346939^{commit}"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_66p_local_evidence_is_additive_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    stage = stages_by_id["66P"]

    assert stage["status"] == "COMPLETED_FIXED_BASELINE"
    assert stage["stage_name"] == "Conversación Horizontal / Continuity Spine v0"
    assert stage["local_evidence"] == {
        "commit": "same_commit_as_66P_closeout",
        "paths": [
            "app/conversation_continuity.py",
            "docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md",
            "tests/test_conversation_continuity_spine.py",
        ],
    }
    for path in stage["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_66p_transition_points_to_66p2_continuation():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    transition = load_json_block("stage-66p-completion-transition")

    assert stages_by_id["66P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["66P2"]["stage_name"] == "Memory Stack Architecture / Criterio Store Spec"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "66P2",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }


def test_66p2_transition_and_67p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-66p2-completion-transition")

    assert stages_by_id["66P2"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "67P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert [stage["stage_id"] for stage in next_eligible] == ["67P"]
    assert next_eligible[0]["stage_name"] == "Caregiver Mode Boundary Spec"
    assert next_eligible[0]["next_action"] == "Eligible for story drafting only after 66P2 closes."


def test_required_final_sequence_after_66p_is_encoded_exactly():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    for stage_id, (status, stage_name) in EXPECTED_FINAL_SEQUENCE.items():
        stage = stages_by_id[stage_id]
        assert stage["status"] == status
        assert stage["stage_name"] == stage_name


def test_future_sequence_entries_do_not_claim_local_evidence_or_authorization():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    for stage_id in [f"{number}P" for number in range(67, 77)]:
        stage = stages_by_id[stage_id]
        assert stage["status"] in {"NEXT_ELIGIBLE", "SEQUENCE_ENTRY_ONLY"}
        assert stage["authority_source"] == "explicit_maintainer_direction"
        assert stage["local_evidence"] is None
        assert stage["implementation_authorized"] is False


def test_ch01_is_the_non_authorizing_66p_canonical_product_spine():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    spine = load_json_block("canonical-product-spine-stage")

    assert stages_by_id["66P"]["stage_name"] == "Conversación Horizontal / Continuity Spine v0"
    assert spine == {
        "spine_id": "CH-01",
        "stage_id": "66P",
        "stage_name": "Conversación Horizontal / Continuity Spine v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "rationale": "Defines continuity across conversations before later caregiver, voice, research, and advanced-skill stages.",
        "scope_signals": [
            "conversation_classification",
            "selective_notes",
            "user_criterio",
            "priority_gate",
            "que_hago_hoy_mode",
            "proactive_intervention_rules",
            "cross_topic_synthesis",
            "next_step_resolver",
            "zaubern_authority_checks",
        ],
        "implementation_authorized": False,
        "baseline_paths": [
            "app/conversation_continuity.py",
            "docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md",
            "tests/test_conversation_continuity_spine.py",
        ],
        "next_stage": "66P2",
    }


def test_66p2_is_memory_architecture_continuation_not_feature_expansion():
    text = ROADMAP_PATH.read_text()
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["65P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["66P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["66P2"] == {
        "stage_id": "66P2",
        "stage_name": "Memory Stack Architecture / Criterio Store Spec",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_66P2_closeout",
            "paths": [
                "docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md",
                "tests/test_memory_stack_architecture.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the memory architecture boundary for continuity and criterio; no storage implementation is authorized.",
    }
    assert "66P2 is a continuation of 66P, not a feature expansion." in text
    for allowed in [
        "story/spec for memory architecture",
        "docs/tests only by default",
        "inventory existing memory surfaces",
        "map `ContinuityMemoryCandidate` from 66P to current and future storage targets",
        "define authority, sensitivity, confirmation, expiration, export, deletion, and influence rules",
    ]:
        assert allowed in text
    for forbidden in [
        "no storage migration",
        "no new backend",
        "no Mirix implementation",
        "no vector store",
        "no graph store",
        "no external retrieval",
        "no connector",
        "no caregiver behavior",
    ]:
        assert forbidden in text


def test_sequencing_rules_preserve_story_spec_build_and_validation_gates():
    rules = load_json_block("roadmap-sequencing-rules")

    assert set(rules) == REQUIRED_SEQUENCE_RULES


def test_deferred_candidates_are_unimplemented_and_use_approved_classifications():
    candidates = load_json_block("deferred-candidate-registry")
    candidate_ids = [candidate["candidate_id"] for candidate in candidates]

    assert set(candidate_ids) == REQUIRED_DEFERRED_IDS
    assert len(candidate_ids) == len(set(candidate_ids))
    assert all(
        candidate["classification"] in ALLOWED_DEFERRED_CLASSIFICATIONS
        for candidate in candidates
    )
    assert all(candidate["authority_source"] == "explicit_maintainer_direction" for candidate in candidates)
    assert all(candidate["reopen_requirements"] for candidate in candidates)
    assert all(candidate["implementation_authorized"] is False for candidate in candidates)


def test_blocked_v0_registry_is_complete_and_never_authorized():
    blocked = load_json_block("canonical-blocked-v0-registry")
    blocked_ids = [item["blocked_id"] for item in blocked]

    assert set(blocked_ids) == REQUIRED_BLOCKED_IDS
    assert len(blocked_ids) == len(set(blocked_ids))
    assert all(item["behavior"] for item in blocked)
    assert all(item["reason"] for item in blocked)
    assert all(item["reopen_requirements"] for item in blocked)
    assert all(item["implementation_authorized"] is False for item in blocked)
