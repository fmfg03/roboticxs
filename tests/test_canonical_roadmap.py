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
    "no_stage_is_next_eligible_after_78P_without_explicit_maintainer_direction",
    "eligibility_permits_story_drafting_only",
    "roadmap_inclusion_never_authorizes_implementation",
    "every_stage_requires_story_approval",
    "every_stage_requires_technical_spec_approval",
    "runtime_implementation_requires_separately_approved_scoped_build_tests_and_validation",
    "stage_78P_is_completed_after_approved_docs_tests_closeout",
    "do_not_invent_79P_without_explicit_maintainer_direction_in_repo_evidence",
    "sequence_changes_require_explicit_maintainer_approval_and_canonical_roadmap_update",
    "external_repositories_and_recent_planning_threads_cannot_independently_change_sequence",
}
EXPECTED_FINAL_SEQUENCE = {
    "66P": ("COMPLETED_FIXED_BASELINE", "Conversación Horizontal / Continuity Spine v0"),
    "66P2": ("COMPLETED_FIXED_BASELINE", "Memory Stack Architecture / Criterio Store Spec"),
    "67P": ("COMPLETED_FIXED_BASELINE", "Caregiver Mode Boundary Spec"),
    "68P": ("COMPLETED_FIXED_BASELINE", "Caregiver Telegram Group Relay v0"),
    "69P": ("COMPLETED_FIXED_BASELINE", "Guided Routine Packets v0"),
    "70P": ("COMPLETED_FIXED_BASELINE", "Voice Notes Intelligence / VibeVoice Spike"),
    "71P": ("COMPLETED_FIXED_BASELINE", "Voice Intake for Caregiver Routines"),
    "72P": ("COMPLETED_FIXED_BASELINE", "Research Radar / Last30Days Skill"),
    "73P": ("COMPLETED_FIXED_BASELINE", "Understand-Anything + codegraph Factory Skill"),
    "74P": ("COMPLETED_FIXED_BASELINE", "ECC Knowledge Compiler Factory Skill"),
    "75P": ("COMPLETED_FIXED_BASELINE", "Agent-Reach Research Parking Lot"),
    "76P": ("COMPLETED_FIXED_BASELINE", "VoxCPM Research Parking Lot"),
    "77P": ("COMPLETED_FIXED_BASELINE", "Roadmap Continuation Authorization Gate v0"),
    "78P": ("COMPLETED_FIXED_BASELINE", "Hermes Runtime Foundation Bootstrap v0"),
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
        "local_evidence_scope": "stages_61P_through_78P",
        "forward_sequence_source": "explicit_maintainer_direction",
        "runtime_truth_source": "local_repo",
        "roadmap_inclusion_authorizes_implementation": False,
    }


def test_stage_registry_contains_ordered_61p_through_66p2_and_78p_once():
    stages = load_stage_registry()
    stage_ids = [stage["stage_id"] for stage in stages]

    assert stage_ids == [f"{number}P" for number in range(61, 67)] + ["66P2"] + [
        f"{number}P" for number in range(67, 79)
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
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    transition = load_json_block("stage-66p2-completion-transition")

    assert stages_by_id["66P2"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert stages_by_id["67P"]["stage_name"] == "Caregiver Mode Boundary Spec"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "67P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }


def test_67p_transition_and_68p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-67p-completion-transition")

    assert stages_by_id["67P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "68P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert next_eligible == []
    assert next_eligible == []


def test_68p_transition_and_69p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-68p-completion-transition")

    assert stages_by_id["68P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "69P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert next_eligible == []
    assert next_eligible == []


def test_69p_transition_and_70p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-69p-completion-transition")

    assert stages_by_id["69P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "70P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert next_eligible == []
    assert next_eligible == []


def test_required_final_sequence_after_66p_is_encoded_exactly():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    for stage_id, (status, stage_name) in EXPECTED_FINAL_SEQUENCE.items():
        stage = stages_by_id[stage_id]
        assert stage["status"] == status
        assert stage["stage_name"] == stage_name


def test_no_future_sequence_entries_claim_local_evidence_or_authorization():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert "79P" not in stages_by_id
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


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


def test_67p_is_caregiver_boundary_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["67P"] == {
        "stage_id": "67P",
        "stage_name": "Caregiver Mode Boundary Spec",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_67P_closeout",
            "paths": [
                "docs/reference/CAREGIVER_MODE_BOUNDARY_SPEC_v0_1.md",
                "tests/test_caregiver_mode_boundary.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the caregiver boundary baseline; no caregiver runtime, relay, routine packet, medication, monitoring, or external action is authorized.",
    }


def test_68p_is_caregiver_relay_packet_preparation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["68P"] == {
        "stage_id": "68P",
        "stage_name": "Caregiver Telegram Group Relay v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_68P_closeout",
            "paths": [
                "app/caregiver_relay.py",
                "docs/reference/CAREGIVER_TELEGRAM_GROUP_RELAY_v0_1.md",
                "tests/test_caregiver_relay.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local caregiver relay packet baseline; no Telegram sending, group management, routine execution, medication, monitoring, emergency handling, sensitive caregiver memory, or external action is authorized.",
    }


def test_69p_is_guided_routine_packet_preparation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["69P"] == {
        "stage_id": "69P",
        "stage_name": "Guided Routine Packets v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_69P_closeout",
            "paths": [
                "app/guided_routines.py",
                "docs/reference/GUIDED_ROUTINE_PACKETS_v0_1.md",
                "tests/test_guided_routines.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local guided routine packet baseline; no scheduler, reminders, Telegram sending, routine execution, medication decision, ingestion verification, monitoring, emergency handling, durable routine memory, voice behavior, or external action is authorized.",
    }


def test_71p_is_voice_intake_transcript_stub_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["71P"] == {
        "stage_id": "71P",
        "stage_name": "Voice Intake for Caregiver Routines",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_71P_closeout",
            "paths": [
                "app/voice_caregiver_intake.py",
                "docs/reference/VOICE_INTAKE_FOR_CAREGIVER_ROUTINES_v0_1.md",
                "tests/test_voice_caregiver_intake.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local transcript-stub caregiver voice intake baseline; no audio processing, ASR, Telegram voice handling, TTS, voice clone, speaker authentication, durable transcript storage, routine execution, medication decision, emergency triage, surveillance, or external send is authorized.",
    }


def test_71p_transition_and_72p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-71p-completion-transition")

    assert stages_by_id["71P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "72P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert next_eligible == []


def test_72p_is_research_radar_packet_preparation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["72P"] == {
        "stage_id": "72P",
        "stage_name": "Research Radar / Last30Days Skill",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_72P_closeout",
            "paths": [
                "app/research_radar.py",
                "docs/reference/RESEARCH_RADAR_LAST30DAYS_SKILL_v0_1.md",
                "tests/test_research_radar.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local request-scoped research packet baseline; no live search, scraping, connector activation, browser automation, external API calls, background monitoring, scheduled alerts, memory writes, raw content storage, external actions, CRM, lead-gen, handoff, or 73P behavior is authorized.",
    }


def test_72p_transition_and_73p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-72p-completion-transition")

    assert stages_by_id["72P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "73P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]


def test_73p_is_repo_understanding_packet_preparation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["73P"] == {
        "stage_id": "73P",
        "stage_name": "Understand-Anything + codegraph Factory Skill",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_73P_closeout",
            "paths": [
                "app/repo_understanding.py",
                "docs/reference/REPO_UNDERSTANDING_FACTORY_SKILL_v0_1.md",
                "tests/test_repo_understanding.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local repo-understanding packet baseline; no code execution, dependency install, repo clone, MCP server, external tool activation, network access, persistent index, raw source archive, security certification, correctness claim, or 74P behavior is authorized.",
    }


def test_73p_transition_and_74p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-73p-completion-transition")

    assert stages_by_id["73P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "74P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]


def test_74p_is_ecc_knowledge_compilation_packet_preparation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["74P"] == {
        "stage_id": "74P",
        "stage_name": "ECC Knowledge Compiler Factory Skill",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_74P_closeout",
            "paths": [
                "app/ecc_knowledge_compiler.py",
                "docs/reference/ECC_KNOWLEDGE_COMPILER_FACTORY_SKILL_v0_1.md",
                "tests/test_ecc_knowledge_compiler.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local ECC knowledge compilation packet baseline; no memory writes, proposed-memory writes, retrieval, connectors, network access, user-facing commands, canon auto-apply, or truth conversion is authorized.",
    }


def test_74p_transition_and_75p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-74p-completion-transition")

    assert stages_by_id["74P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "75P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]


def test_75p_is_agent_reach_research_parking_lot_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["75P"] == {
        "stage_id": "75P",
        "stage_name": "Agent-Reach Research Parking Lot",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_75P_closeout",
            "paths": [
                "docs/research/AGENT_REACH_RESEARCH_PARKING_LOT_v0_1.md",
                "tests/test_agent_reach_research_parking_lot.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Agent-Reach research parking-lot baseline; no runtime dependency, connector, live retrieval, memory ingestion, automatic source scanning, scraping, cookies, credentials, MCP config, user-facing command, or product support claim is authorized.",
    }


def test_75p_transition_and_76p_are_the_only_current_sequence_gate():
    stages = load_stage_registry()
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    transition = load_json_block("stage-75p-completion-transition")

    assert stages_by_id["75P"]["status"] == "COMPLETED_FIXED_BASELINE"
    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": "76P",
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]
    assert next_eligible == []


def test_76p_is_voxcpm_research_parking_lot_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["76P"] == {
        "stage_id": "76P",
        "stage_name": "VoxCPM Research Parking Lot",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_76P_closeout",
            "paths": [
                "docs/research/VOXCPM_RESEARCH_PARKING_LOT_v0_1.md",
                "tests/test_voxcpm_research_parking_lot.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local VoxCPM research parking-lot baseline; no dependency, model download, inference, audio generation, voice cloning, audio storage, Telegram voice handling, connector, MCP config, user-facing command, or product support claim is authorized.",
    }


def test_76p_transition_points_to_77p_governance_gate():
    stages = load_stage_registry()
    transition = load_json_block("stage-76p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_77p_is_roadmap_continuation_authorization_gate_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["77P"] == {
        "stage_id": "77P",
        "stage_name": "Roadmap Continuation Authorization Gate v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_77P_closeout",
            "paths": [
                "docs/reference/ROADMAP_CONTINUATION_AUTHORIZATION_GATE_v0_1.md",
                "tests/test_roadmap_continuation_authorization_gate.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local roadmap continuation authorization gate; no next implementation stage, 78P, runtime change, product feature, staging, or commit is authorized without explicit maintainer approval.",
    }


def test_77p_transition_did_not_auto_invent_78p():
    stages = load_stage_registry()
    transition = load_json_block("stage-77p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_78p_is_hermes_runtime_foundation_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["78P"] == {
        "stage_id": "78P",
        "stage_name": "Hermes Runtime Foundation Bootstrap v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_78P_closeout",
            "paths": [
                "app/hermes_runtime.py",
                "docs/reference/HERMES_RUNTIME_FOUNDATION_BOOTSTRAP_v0_1.md",
                "docs/reference/HERMES_UPSTREAM_TRACKING_v0_1.md",
                "tests/test_hermes_runtime_foundation.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Hermes-compatible runtime foundation baseline; no Telegram, caregiver routines, document intake, connectors, retrieval, memory writes, ProposedMemory writes, scheduler, background jobs, shell execution, Hermes dependency install, upstream install script execution, auto-update, staging, commit, or 79P behavior is authorized.",
    }


def test_78p_transition_does_not_invent_79p():
    stages = load_stage_registry()
    transition = load_json_block("stage-78p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert "79P" not in {stage["stage_id"] for stage in stages}


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
