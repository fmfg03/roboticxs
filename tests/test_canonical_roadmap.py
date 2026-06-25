from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
ALLOWED_STAGE_STATUSES = {
    "CLOSED_COMMITTED",
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
    "no_stage_is_next_eligible_after_101P_without_explicit_maintainer_direction",
    "eligibility_permits_story_drafting_only",
    "roadmap_inclusion_never_authorizes_implementation",
    "every_stage_requires_story_approval",
    "every_stage_requires_technical_spec_approval",
    "runtime_implementation_requires_separately_approved_scoped_build_tests_and_validation",
    "stage_83P_is_closed_committed_after_metadata_reconciliation",
    "stage_84P_is_closed_committed_after_active_memory_forget_closeout",
    "stage_85P_is_closed_committed_after_hermes_soul_rebase_closeout",
    "stage_86P_is_closed_committed_after_hermes_real_settings_baseline_closeout",
    "stage_87P_is_closed_committed_after_hermes_agent_skills_cron_baseline_closeout",
    "stage_88P_is_closed_committed_after_routine_wake_gate_closeout",
    "stage_89P_is_closed_committed_after_automation_blueprints_closeout",
    "stage_90P_is_closed_committed_after_command_surface_policy_closeout",
    "stage_91P_is_closed_committed_after_skill_activation_scope_guard_closeout",
    "stage_92P_is_closed_committed_after_tool_authority_guard_closeout",
    "stage_93P_is_closed_committed_after_memory_center_bridge_closeout",
    "stage_94P_is_closed_committed_after_telegram_hermes_gateway_mvp_closeout",
    "stage_95P_is_closed_committed_after_telegram_hermes_policy_chain_runtime_skeleton",
    "stage_96P_is_closed_committed_after_hermes_os_runtime_contract_closeout",
    "stage_97P_is_closed_committed_after_caregiver_telegram_mvp_closeout",
    "stage_98P_is_closed_committed_after_routine_execution_engine_skeleton_closeout",
    "stage_99P_is_closed_committed_after_memory_center_projection_runtime_remediation_validation",
    "stage_100P_is_closed_committed_after_cost_governor_model_routing_runtime_closeout",
    "stage_101P_is_closed_committed_after_action_packet_approval_loop_remediation_review",
    "stage_102P_is_closed_committed_after_async_delegation_authority_adapter_closeout",
    "stage_103P_is_closed_committed_after_async_delegation_completion_inbox_closeout",
    "stage_104P_is_closed_committed_after_async_result_user_surface_closeout",
    "stage_105P_is_closed_committed_after_telegram_async_result_delivery_closeout",
    "stage_106P_is_closed_committed_after_telegram_result_acknowledgement_binding_closeout",
    "stage_107P_is_closed_committed_after_followup_intent_review_queue_closeout",
    "stage_108P_is_closed_committed_after_followup_draft_planner_closeout",
    "stage_109P_is_closed_committed_after_telegram_followup_choice_surface_closeout",
    "stage_110P_is_closed_committed_after_telegram_followup_choice_selection_binding_closeout",
    "stage_111P_is_closed_committed_after_user_approved_followup_delegation_closeout",
    "stage_112P_is_closed_committed_after_controlled_followup_execution_skeleton_closeout",
    "stage_113P_is_closed_committed_after_followup_completion_loop_integration_closeout",
    "stage_114P_is_closed_committed_after_followup_result_acknowledgement_closeout",
    "stage_115P_is_closed_committed_after_followup_memory_proposal_closeout",
    "stage_116P_is_closed_committed_after_telegram_memory_proposal_approval_closeout",
    "stage_117P_is_closed_committed_after_memory_center_writeback_closeout",
    "stage_118P_is_closed_committed_after_context_scan_candidate_source_closeout",
    "stage_119P_is_closed_committed_after_proactive_opportunity_detection_closeout",
    "stage_120P_is_closed_committed_after_proactive_telegram_suggestion_closeout",
    "stage_121P_is_closed_committed_after_proactive_suggestion_adapter_closeout",
    "stage_122P_is_closed_committed_after_proactive_delegation_adapter_closeout",
    "stage_123P_is_closed_committed_after_controlled_proactive_execution_skeleton_closeout",
    "stage_124P_is_closed_committed_after_what_did_i_miss_daily_brief_closeout",
    "stage_125P_is_closed_committed_after_skill_pack_activation_surface_closeout",
    "stage_126P_is_closed_committed_after_first_demo_flow_meeting_brief_from_context_closeout",
    "stage_127P_is_closed_committed_after_demo_result_delivery_surface_closeout",
    "stage_128P_is_closed_committed_after_document_review_demo_flow_closeout",
    "stage_129P_is_closed_committed_after_hermes_runtime_bootstrap_closeout",
    "stage_130P_is_closed_committed_after_runnable_telegram_robot_mvp_closeout",
    "stage_131P_is_closed_committed_after_telegram_what_did_i_miss_command_closeout",
    "stage_132P_is_closed_committed_after_telegram_meeting_brief_command_closeout",
    "stage_133P_is_closed_committed_after_read_only_google_calendar_connector_closeout",
    "stage_134P_is_closed_committed_after_calendar_backed_telegram_meeting_brief_closeout",
    "stage_135P_is_closed_committed_after_real_calendar_meeting_brief_composer_closeout",
    "stage_136P_is_closed_committed_after_memory_center_telegram_commands_closeout",
    "stage_137P_is_closed_committed_after_calendar_context_scan_closeout",
    "stage_138P_is_closed_committed_after_proactive_meeting_suggestion_closeout",
    "stage_139P_is_closed_committed_after_owner_requested_suggested_meeting_brief_closeout",
    "stage_140P_is_closed_committed_after_deerflow_pattern_review_closeout",
    "stage_141P_is_closed_committed_after_today_command_closeout",
    "stage_142P_is_closed_committed_after_open_loops_command_closeout",
    "stage_143P_is_closed_committed_after_meeting_prep_pack_closeout",
    "stage_144P_is_closed_committed_after_brief_memory_proposal_closeout",
    "stage_145P_is_closed_committed_after_brief_memory_approval_closeout",
    "stage_146P_is_closed_committed_after_personal_admin_inbox_closeout",
    "stage_147P_is_closed_committed_after_inbox_item_decision_closeout",
    "stage_148P_is_closed_committed_after_factory_loop_handoff_harness_closeout",
    "stage_149P_is_closed_committed_after_runtime_doctor_helper_manager_closeout",
    "stage_150P_is_closed_committed_after_telegram_product_shell_closeout",
    "stage_151P_is_closed_committed_after_meeting_prep_pack_product_flow_closeout",
    "do_not_invent_133P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_134P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_135P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_136P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_137P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_138P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_139P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_140P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_141P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_142P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_143P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_144P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_145P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_146P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_147P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_148P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_149P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_150P_without_explicit_maintainer_direction_in_repo_evidence",
    "do_not_invent_151P_without_explicit_maintainer_direction_in_repo_evidence",
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
    "79P": ("COMPLETED_FIXED_BASELINE", "Telegram Bot Runtime Bootstrap v0"),
    "80P": ("COMPLETED_FIXED_BASELINE", "Telegram Conversation Loop v0"),
    "81P": ("COMPLETED_FIXED_BASELINE", "Telegram Runtime Smoke / Manual Bot Wiring v0"),
    "82P": ("COMPLETED_FIXED_BASELINE", "Memory Proposal Loop over Telegram v0"),
    "83P": ("CLOSED_COMMITTED", "Active Memory Recall over Telegram v0"),
    "84P": ("CLOSED_COMMITTED", "Active Memory Forget over Telegram v0"),
    "85P": ("CLOSED_COMMITTED", "Hermes Profile / Roboticxs SOUL Rebase v0"),
    "86P": ("CLOSED_COMMITTED", "Hermes Real Settings Baseline v0"),
    "87P": ("CLOSED_COMMITTED", "Hermes + Agent Skills + Cron Integration Baseline v0"),
    "88P": ("CLOSED_COMMITTED", "Routine Wake Gate / Zero-Token Preflight v0"),
    "89P": ("CLOSED_COMMITTED", "Roboticxs Automation Blueprints v0"),
    "90P": ("CLOSED_COMMITTED", "Roboticxs Command Surface Policy v0"),
    "91P": ("CLOSED_COMMITTED", "Skill Activation Scope Guard v0"),
    "92P": ("CLOSED_COMMITTED", "Hermes Tool Authority Guard v0"),
    "93P": ("CLOSED_COMMITTED", "Roboticxs Memory Center Bridge v0"),
    "94P": ("CLOSED_COMMITTED", "Telegram MVP on Hermes Gateway v0"),
    "95P": ("CLOSED_COMMITTED", "Telegram-Hermes Policy Chain Runtime Skeleton v0"),
    "96P": ("CLOSED_COMMITTED", "Hermes OS Runtime Contract v0"),
    "97P": ("CLOSED_COMMITTED", "Caregiver Telegram MVP v0"),
    "98P": ("CLOSED_COMMITTED", "Routine Execution Engine Skeleton v0"),
    "99P": ("CLOSED_COMMITTED", "Memory Center Projection Runtime Slice v0"),
    "100P": ("CLOSED_COMMITTED", "Cost Governor / Model Routing Runtime v0"),
    "101P": ("CLOSED_COMMITTED", "Action Packet Approval Loop v0"),
    "102P": ("CLOSED_COMMITTED", "Hermes Async Delegation Authority Adapter v0"),
    "103P": ("CLOSED_COMMITTED", "Async Delegation Completion Inbox v0"),
    "104P": ("CLOSED_COMMITTED", "Async Result User Surface v0"),
    "105P": ("CLOSED_COMMITTED", "Telegram Async Result Delivery v0"),
    "106P": ("CLOSED_COMMITTED", "Telegram Result Acknowledgement Binding v0"),
    "107P": ("CLOSED_COMMITTED", "Follow-up Intent Review Queue v0"),
    "108P": ("CLOSED_COMMITTED", "Follow-up Draft Planner v0"),
    "109P": ("CLOSED_COMMITTED", "Telegram Follow-up Choice Surface v0"),
    "110P": ("CLOSED_COMMITTED", "Telegram Follow-up Choice Selection Binding v0"),
    "111P": ("CLOSED_COMMITTED", "User-Approved Follow-up Delegation v0"),
    "112P": ("CLOSED_COMMITTED", "Controlled Follow-up Execution Skeleton v0"),
    "113P": ("CLOSED_COMMITTED", "Follow-up Completion Loop Integration v0"),
    "114P": ("CLOSED_COMMITTED", "Follow-up Result Acknowledgement v0"),
    "115P": ("CLOSED_COMMITTED", "Memory Proposal from Follow-up Result v0"),
    "116P": ("CLOSED_COMMITTED", "Telegram Memory Proposal Approval v0"),
    "117P": ("CLOSED_COMMITTED", "Memory Center Writeback v0"),
    "118P": ("CLOSED_COMMITTED", "Context Scan Candidate Source v0"),
    "119P": ("CLOSED_COMMITTED", "Proactive Opportunity Detection v0"),
    "120P": ("CLOSED_COMMITTED", "Proactive Telegram Suggestion v0"),
    "121P": ("CLOSED_COMMITTED", "Proactive Suggestion Adapter to Follow-up Loop v0"),
    "122P": ("CLOSED_COMMITTED", "Proactive Delegation Adapter v0"),
    "123P": ("CLOSED_COMMITTED", "Controlled Proactive Execution Skeleton v0"),
    "124P": ("CLOSED_COMMITTED", "What Did I Miss? Daily Brief v0"),
    "125P": ("CLOSED_COMMITTED", "Skill Pack Activation Surface v0"),
    "126P": ("CLOSED_COMMITTED", "First Demo Flow: Meeting Brief from Context v0"),
    "127P": ("CLOSED_COMMITTED", "Demo Result Delivery Surface v0"),
    "128P": ("CLOSED_COMMITTED", "Document Review Demo Flow v0"),
    "129P": ("CLOSED_COMMITTED", "Hermes Runtime Bootstrap v0"),
    "130P": ("CLOSED_COMMITTED", "Runnable Telegram Robot MVP v0"),
    "131P": ("CLOSED_COMMITTED", "Telegram What Did I Miss Command v0"),
    "132P": ("CLOSED_COMMITTED", "Telegram Meeting Brief Command v0"),
    "133P": ("CLOSED_COMMITTED", "Read-Only Google Calendar Connector v0"),
    "134P": ("CLOSED_COMMITTED", "Calendar-backed Telegram Meeting Brief v0"),
    "135P": ("CLOSED_COMMITTED", "Real Calendar Meeting Brief Composer v0"),
    "136P": ("CLOSED_COMMITTED", "Memory Center Telegram Commands v0"),
    "137P": ("CLOSED_COMMITTED", "Context Scan from Calendar v0"),
    "138P": ("CLOSED_COMMITTED", "Proactive Meeting Suggestion v0"),
    "139P": ("CLOSED_COMMITTED", "Owner-Requested Suggested Meeting Brief v0"),
    "140P": ("CLOSED_COMMITTED", "DeerFlow Pattern Review / Sandbox Boundary Spike v0"),
    "141P": ("CLOSED_COMMITTED", "Today Command v0"),
    "142P": ("CLOSED_COMMITTED", "Open Loops Command v0"),
    "143P": ("CLOSED_COMMITTED", "Meeting Prep Pack v0"),
    "144P": ("CLOSED_COMMITTED", "Brief-Derived Memory Proposal v0"),
    "145P": ("CLOSED_COMMITTED", "Telegram Memory Approval for Brief Proposals v0"),
    "146P": ("CLOSED_COMMITTED", "Personal Admin Inbox v0"),
    "147P": ("CLOSED_COMMITTED", "Inbox Resolve / Dismiss v0"),
    "148P": ("CLOSED_COMMITTED", "Factory Loop Handoff Harness v0"),
    "149P": ("CLOSED_COMMITTED", "Runtime Doctor / Helper Manager v0"),
    "150P": ("CLOSED_COMMITTED", "Telegram Product Shell v0"),
    "151P": ("CLOSED_COMMITTED", "Meeting Prep Pack Product Flow v0"),
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
        "local_evidence_scope": "stages_61P_through_151P",
        "forward_sequence_source": "explicit_maintainer_direction",
        "runtime_truth_source": "local_repo",
        "roadmap_inclusion_authorizes_implementation": False,
    }


def test_stage_registry_contains_ordered_61p_through_66p2_and_83p_once():
    stages = load_stage_registry()
    stage_ids = [stage["stage_id"] for stage in stages]

    assert stage_ids == [f"{number}P" for number in range(61, 67)] + ["66P2"] + [
        f"{number}P" for number in range(67, 152)
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

    assert stages_by_id["83P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["83P"]["authority_source"] == "local_repo_evidence"
    assert stages_by_id["83P"]["local_evidence"]["commit"] == "ef9faeb5ed427e2fe4cc04720a50a0a5eadf4d22"
    assert stages_by_id["84P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["84P"]["local_evidence"]["commit"] == "1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6"
    assert stages_by_id["85P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["85P"]["local_evidence"]["commit"] == "95e23e5438812328f804ba026095237d17f1bf72"
    assert stages_by_id["86P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["87P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["88P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["89P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["90P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["91P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["92P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["93P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["94P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["95P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["96P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["97P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["98P"]["status"] == "CLOSED_COMMITTED"
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


def test_78p_transition_did_not_auto_invent_79p():
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


def test_79p_is_telegram_bot_runtime_bootstrap_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["79P"] == {
        "stage_id": "79P",
        "stage_name": "Telegram Bot Runtime Bootstrap v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_79P_closeout",
            "paths": [
                "app/telegram_runtime.py",
                "app/config.py",
                "app/main.py",
                "docs/reference/TELEGRAM_BOT_RUNTIME_BOOTSTRAP_v0_1.md",
                "tests/test_telegram_runtime_bootstrap.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Telegram text-channel runtime bootstrap baseline; no caregiver routines, guided routines, document/PDF intake, file downloads, voice, payments, Telegram group relay, proactive/background messages, memory writes, ProposedMemory writes, retrieval, connectors, scheduler, WhatsApp, production deployment, staging, commit, or 80P behavior is authorized.",
    }


def test_79p_transition_did_not_auto_invent_80p():
    stages = load_stage_registry()
    transition = load_json_block("stage-79p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_80p_is_telegram_conversation_loop_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["80P"] == {
        "stage_id": "80P",
        "stage_name": "Telegram Conversation Loop v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_80P_closeout",
            "paths": [
                "app/telegram_runtime.py",
                "app/main.py",
                "docs/reference/TELEGRAM_CONVERSATION_LOOP_v0_1.md",
                "tests/test_telegram_conversation_loop.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram text conversation loop baseline; no real Telegram API delivery, long-term memory, user profile memory, ProposedMemory creation, caregiver behavior, document/file handling, voice, retrieval, connectors, proactive/background messaging, scheduler, deployment, staging, commit, or 81P behavior is authorized.",
    }


def test_80p_transition_did_not_auto_authorize_81p():
    stages = load_stage_registry()
    transition = load_json_block("stage-80p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_81p_is_telegram_runtime_smoke_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["81P"] == {
        "stage_id": "81P",
        "stage_name": "Telegram Runtime Smoke / Manual Bot Wiring v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_81P_closeout",
            "paths": [
                "app/config.py",
                "app/telegram_runtime.py",
                "docs/reference/TELEGRAM_RUNTIME_SMOKE_MANUAL_WIRING_v0_1.md",
                "tests/test_telegram_runtime_smoke.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local manual Telegram runtime smoke baseline; no production deployment, automatic webhook registration, real Telegram API calls in tests, committed secrets, caregiver routines, document/file handling, voice, memory writes, ProposedMemory writes, retrieval, connectors, proactive/background messaging, scheduler, staging, commit, or 82P behavior is authorized.",
    }


def test_81p_transition_did_not_auto_authorize_82p():
    stages = load_stage_registry()
    transition = load_json_block("stage-81p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_82p_is_telegram_memory_proposal_loop_only_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["82P"] == {
        "stage_id": "82P",
        "stage_name": "Memory Proposal Loop over Telegram v0",
        "status": "COMPLETED_FIXED_BASELINE",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "same_commit_as_82P_closeout",
            "paths": [
                "app/telegram_runtime.py",
                "app/main.py",
                "app/memory_service.py",
                "docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md",
                "tests/test_telegram_memory_proposal_loop.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Telegram memory proposal loop baseline; no automatic memory activation, normal-conversation memory extraction, Context Scan, external source scanning, retrieval, connectors, caregiver routines, document/file handling, voice, proactive/background behavior, scheduler, staging, commit, or 83P behavior is authorized.",
    }


def test_82p_transition_keeps_no_next_eligible_after_82p_closeout():
    stages = load_stage_registry()
    transition = load_json_block("stage-82p-completion-transition")

    assert transition == {
        "closeout_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_status": "COMPLETED_FIXED_BASELINE",
        "after_commit_next_eligible": None,
        "transition_requires_commit": True,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_83p_is_active_memory_recall_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["83P"] == {
        "stage_id": "83P",
        "stage_name": "Active Memory Recall over Telegram v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "ef9faeb5ed427e2fe4cc04720a50a0a5eadf4d22",
            "commit_message": "feat: add active memory recall over telegram",
            "paths": [
                "app/telegram_runtime.py",
                "app/memory_control.py",
                "docs/reference/TELEGRAM_ACTIVE_MEMORY_RECALL_v0_1.md",
                "tests/test_telegram_memory_proposal_loop.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local active memory recall over Telegram baseline.",
    }
    for path in stages_by_id["83P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_83p_transition_does_not_authorize_next_eligible():
    stages = load_stage_registry()
    transition = load_json_block("stage-83p-closeout-transition")

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "ef9faeb5ed427e2fe4cc04720a50a0a5eadf4d22",
        "commit_message": "feat: add active memory recall over telegram",
        "after_commit_next_eligible": None,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_84p_is_active_memory_forget_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["84P"] == {
        "stage_id": "84P",
        "stage_name": "Active Memory Forget over Telegram v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6",
            "commit_message": "feat: add telegram active memory forget",
            "paths": [
                "app/telegram_runtime.py",
                "docs/reference/TELEGRAM_ACTIVE_MEMORY_FORGET_v0_1.md",
                "tests/test_telegram_memory_proposal_loop.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local active memory forget over Telegram baseline.",
    }
    for path in stages_by_id["84P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()
    result = subprocess.run(
        ["git", "cat-file", "-e", "1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6^{commit}"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_84p_transition_selects_85p_without_runtime_authorization():
    transition = load_json_block("stage-84p-closeout-transition")

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6",
        "commit_message": "feat: add telegram active memory forget",
        "after_commit_next_eligible": "85P",
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }


def test_85p_is_hermes_profile_rebase_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["85P"] == {
        "stage_id": "85P",
        "stage_name": "Hermes Profile / Roboticxs SOUL Rebase v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "95e23e5438812328f804ba026095237d17f1bf72",
            "commit_message": "docs: add hermes roboticxs soul rebase",
            "paths": [
                "runtime/hermes/SOUL.md",
                "runtime/hermes/AGENTS.md",
                "docs/reference/85P_HERMES_PROFILE_ROBOTICXS_SOUL_REBASE_SPEC_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_SOUL_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_PROFILE_REBASE_v0_1.md",
                "tests/test_hermes_soul_contract.py",
                "tests/test_hermes_profile_boundary.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Hermes profile and Roboticxs SOUL rebase baseline. 86P is closed committed; do not infer 87P implementation, 88P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["85P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()
    result = subprocess.run(
        ["git", "cat-file", "-e", "95e23e5438812328f804ba026095237d17f1bf72^{commit}"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_85p_transition_selects_86p_without_runtime_authorization():
    transition = load_json_block("stage-85p-closeout-transition")

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "95e23e5438812328f804ba026095237d17f1bf72",
        "commit_message": "docs: add hermes roboticxs soul rebase",
        "after_commit_next_eligible": "86P",
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["86P"]["status"] == "CLOSED_COMMITTED"


def test_86p_is_hermes_real_settings_baseline_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["86P"] == {
        "stage_id": "86P",
        "stage_name": "Hermes Real Settings Baseline v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "efb4f5f",
            "commit_message": "docs: add hermes real settings baseline",
            "paths": [
                "docs/research/HERMES_REAL_SETTINGS_BASELINE_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_CONFIG_CONTRACT_v0_1.md",
                "tests/test_hermes_real_settings_baseline.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the verified Hermes real-settings baseline and config contract. 87P is closed committed; do not infer 88P implementation, 89P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["86P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_86p_transition_selects_87p_without_runtime_authorization():
    transition = load_json_block("stage-86p-implementation-transition")

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "efb4f5f",
        "commit_message": "docs: add hermes real settings baseline",
        "after_commit_next_eligible": "87P",
        "next_eligible_stage_name": "Hermes + Agent Skills + Cron Integration Baseline v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_88p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["87P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["88P"]["status"] == "CLOSED_COMMITTED"


def test_87p_is_hermes_agent_skills_cron_baseline_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["87P"] == {
        "stage_id": "87P",
        "stage_name": "Hermes + Agent Skills + Cron Integration Baseline v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "213a7772aef3a55e03f2284044aba458c752c54e",
            "commit_message": "docs: add hermes agent skills cron baseline",
            "paths": [
                "docs/reference/ROBOTICXS_SKILL_MANIFEST_TO_AGENT_SKILLS_BRIDGE_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_CRON_ROUTINE_MAPPING_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_CAPABILITY_SURFACE_AUDIT_v0_1.md",
                "docs/research/HERMES_AGENT_SKILLS_CRON_BASELINE_v0_1.md",
                "tests/test_agent_skills_export_contract.py",
                "tests/test_hermes_cron_routine_mapping.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Hermes Agent Skills and cron integration baseline. 88P - Routine Wake Gate / Zero-Token Preflight v0 - is closed committed; do not infer 89P implementation, 90P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["87P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_87p_transition_selects_88p_without_runtime_authorization():
    transition = load_json_block("stage-87p-implementation-transition")

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "213a7772aef3a55e03f2284044aba458c752c54e",
        "commit_message": "docs: add hermes agent skills cron baseline",
        "after_commit_next_eligible": "88P",
        "next_eligible_stage_name": "Routine Wake Gate / Zero-Token Preflight v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_91p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["88P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["89P"]["status"] == "CLOSED_COMMITTED"


def test_88p_is_routine_wake_gate_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["88P"] == {
        "stage_id": "88P",
        "stage_name": "Routine Wake Gate / Zero-Token Preflight v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "590305394f57ccfbc729b895b446b052adbc4e6e",
            "commit_message": "docs: add routine wake gate baseline",
            "paths": [
                "docs/reference/ROBOTICXS_ROUTINE_WAKE_GATE_v0_1.md",
                "docs/reference/ROBOTICXS_ROUTINE_COST_POLICY_v0_1.md",
                "docs/reference/ROBOTICXS_SCRIPT_ONLY_ROUTINES_v0_1.md",
                "runtime/hermes/scripts/examples/file_change_gate.py",
                "runtime/hermes/scripts/examples/http_diff_gate.py",
                "runtime/hermes/scripts/examples/external_flag_gate.py",
                "tests/test_routine_wake_gate.py",
                "tests/test_routine_no_agent_mode.py",
                "tests/test_routine_budget_skip.py",
                "tests/test_routine_context_payload.py",
                "tests/test_routine_silent_is_not_cost_control.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Routine Wake Gate and Zero-Token Preflight baseline. 89P - Roboticxs Automation Blueprints v0 - is closed committed; do not infer 90P implementation, 91P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["88P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_88p_transition_selects_89p_without_implementation_authorization():
    transition = load_json_block("stage-88p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "590305394f57ccfbc729b895b446b052adbc4e6e",
        "commit_message": "docs: add routine wake gate baseline",
        "after_commit_next_eligible": "89P",
        "next_eligible_stage_name": "Roboticxs Automation Blueprints v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_91p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["89P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["90P"]["status"] == "CLOSED_COMMITTED"


def test_89p_is_automation_blueprints_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["89P"] == {
        "stage_id": "89P",
        "stage_name": "Roboticxs Automation Blueprints v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "dc53ef24f2d15ba1d35ce93ec82555e8290dc565",
            "commit_message": "docs: add roboticxs automation blueprints",
            "paths": [
                "docs/reference/ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1.md",
                "docs/reference/ROBOTICXS_BLUEPRINT_AUTHORITY_BOUNDARIES_v0_1.md",
                "docs/reference/ROBOTICXS_BLUEPRINT_INSTALLATION_CONTRACT_v0_1.md",
                "runtime/hermes/skills/roboticxs-daily-brief/SKILL.md",
                "runtime/hermes/skills/roboticxs-research-radar/SKILL.md",
                "runtime/hermes/skills/roboticxs-caregiver-routine/SKILL.md",
                "tests/test_roboticxs_blueprint_manifest.py",
                "tests/test_roboticxs_blueprint_authority.py",
                "tests/test_roboticxs_blueprint_no_silent_schedule.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Automation Blueprints baseline. 90P - Roboticxs Command Surface Policy v0 - is closed committed; do not infer 91P implementation, 92P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["89P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_89p_transition_selects_90p_without_implementation_authorization():
    transition = load_json_block("stage-89p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "dc53ef24f2d15ba1d35ce93ec82555e8290dc565",
        "commit_message": "docs: add roboticxs automation blueprints",
        "after_commit_next_eligible": "90P",
        "next_eligible_stage_name": "Roboticxs Command Surface Policy v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_91p_next_eligible_after_90p_closeout": True,
        "stage_91p_implemented": False,
        "stage_92p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["90P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["91P"]["status"] == "CLOSED_COMMITTED"


def test_90p_is_command_surface_policy_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["90P"] == {
        "stage_id": "90P",
        "stage_name": "Roboticxs Command Surface Policy v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "970e6e9014ec6e7b3031a7d3d412004fdebea815",
            "commit_message": "docs: add roboticxs command surface policy",
            "paths": [
                "docs/reference/ROBOTICXS_COMMAND_SURFACE_POLICY_v0_1.md",
                "docs/reference/ROBOTICXS_CONSUMER_COMMAND_ALIASES_v0_1.md",
                "docs/reference/ROBOTICXS_HERMES_RAW_COMMAND_BLOCKLIST_v0_1.md",
                "tests/test_command_surface_policy.py",
                "tests/test_forbidden_hermes_commands.py",
                "tests/test_consumer_command_aliases.py",
                "tests/test_approval_command_packets.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Command Surface Policy baseline. 91P - Skill Activation Scope Guard v0 - is closed committed; do not infer 92P implementation, 93P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["90P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_90p_closeout_selects_91p_without_implementation_authorization():
    transition = load_json_block("stage-90p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "970e6e9014ec6e7b3031a7d3d412004fdebea815",
        "commit_message": "docs: add roboticxs command surface policy",
        "after_commit_next_eligible": "91P",
        "next_eligible_stage_name": "Skill Activation Scope Guard v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_92p_next_eligible_after_91p_closeout": True,
        "stage_92p_implemented": False,
        "stage_93p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["91P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["92P"]["status"] == "CLOSED_COMMITTED"


def test_91p_is_skill_activation_scope_guard_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["91P"] == {
        "stage_id": "91P",
        "stage_name": "Skill Activation Scope Guard v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "0f786def035d0c6380f6f511c03313b4d9db3756",
            "commit_message": "docs: add skill activation scope guard",
            "paths": [
                "docs/reference/ROBOTICXS_SKILL_ACTIVATION_SCOPE_GUARD_v0_1.md",
                "docs/reference/ROBOTICXS_SKILL_SCOPE_DECISIONS_v0_1.md",
                "docs/reference/ROBOTICXS_SKILL_UPGRADE_AND_REDIRECT_POLICY_v0_1.md",
                "tests/test_skill_activation_scope_guard.py",
                "tests/test_skill_scope_decisions.py",
                "tests/test_skill_redirect_upgrade_policy.py",
                "tests/test_skill_scope_guard_blocks_prohibited_actions.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Skill Activation Scope Guard baseline. 92P - Hermes Tool Authority Guard v0 - is closed committed; do not infer 93P implementation, 94P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["91P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_91p_closeout_selects_92p_closed_committed_without_implementation_authorization():
    transition = load_json_block("stage-91p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "0f786def035d0c6380f6f511c03313b4d9db3756",
        "commit_message": "docs: add skill activation scope guard",
        "after_commit_next_eligible": "92P",
        "next_eligible_stage_name": "Hermes Tool Authority Guard v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_93p_next_eligible_after_92p_closeout": True,
        "stage_93p_implemented": False,
        "stage_94p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["92P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["93P"]["status"] == "CLOSED_COMMITTED"


def test_92p_is_hermes_tool_authority_guard_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["92P"] == {
        "stage_id": "92P",
        "stage_name": "Hermes Tool Authority Guard v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "ac6d5c4d775367ea9b1774cfe985fedeee7a49cf",
            "commit_message": "docs: add hermes tool authority guard",
            "paths": [
                "docs/reference/ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1.md",
                "docs/reference/ROBOTICXS_TOOL_ACTION_CLASSIFICATION_v0_1.md",
                "docs/reference/ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1.md",
                "docs/reference/ROBOTICXS_TOOL_AUTHORITY_DECISIONS_v0_1.md",
                "tests/test_hermes_tool_authority_guard.py",
                "tests/test_tool_action_classification.py",
                "tests/test_action_packet_contract.py",
                "tests/test_tool_authority_blocks_sensitive_actions.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Hermes Tool Authority Guard baseline. 93P - Roboticxs Memory Center Bridge v0 - is closed committed; do not infer 94P implementation, 95P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["92P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_92p_closeout_records_93p_closed_committed_without_94p_implementation():
    transition = load_json_block("stage-92p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "ac6d5c4d775367ea9b1774cfe985fedeee7a49cf",
        "commit_message": "docs: add hermes tool authority guard",
        "after_commit_next_eligible": "93P",
        "next_eligible_stage_name": "Roboticxs Memory Center Bridge v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_94p_closed_committed": True,
        "stage_95p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []
    assert stages_by_id["93P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["94P"]["status"] == "CLOSED_COMMITTED"


def test_93p_is_memory_center_bridge_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["93P"] == {
        "stage_id": "93P",
        "stage_name": "Roboticxs Memory Center Bridge v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "65ac8c03fc3305548627ca3162fb71191fcdcbb7",
            "commit_message": "docs: add memory center bridge",
            "paths": [
                "docs/reference/ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1.md",
                "docs/reference/ROBOTICXS_MEMORY_PROJECTION_POLICY_v0_1.md",
                "docs/reference/ROBOTICXS_MEMORY_WRITEBACK_BOUNDARY_v0_1.md",
                "docs/reference/ROBOTICXS_MEMORY_CONTEXT_INJECTION_CONTRACT_v0_1.md",
                "tests/test_memory_center_bridge.py",
                "tests/test_memory_projection_policy.py",
                "tests/test_memory_writeback_boundary.py",
                "tests/test_memory_context_injection_contract.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Memory Center Bridge baseline. 94P - Telegram MVP on Hermes Gateway v0 - is closed committed as story/spec/test work only; do not infer 95P or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["93P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_93p_closeout_selects_94p_as_closed_committed_without_future_authorization():
    transition = load_json_block("stage-93p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "65ac8c03fc3305548627ca3162fb71191fcdcbb7",
        "commit_message": "docs: add memory center bridge",
        "after_commit_next_eligible": "94P",
        "next_eligible_stage_name": "Telegram MVP on Hermes Gateway v0",
        "next_eligible_implementation_status": "CLOSED_COMMITTED",
        "stage_94p_closed_committed": True,
        "stage_95p_and_later_authorized": False,
        "transition_requires_commit": False,
        "implementation_authorized": False,
    }
    assert stages_by_id["93P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["94P"]["status"] == "CLOSED_COMMITTED"


def test_94p_is_telegram_hermes_gateway_mvp_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["94P"] == {
        "stage_id": "94P",
        "stage_name": "Telegram MVP on Hermes Gateway v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "local_repo_evidence",
        "local_evidence": {
            "commit": "97777ca68e0443e17236e9858ce350f68ed77864",
            "commit_message": "docs: add telegram hermes gateway mvp",
            "paths": [
                "docs/reference/ROBOTICXS_TELEGRAM_HERMES_GATEWAY_MVP_v0_1.md",
                "docs/reference/ROBOTICXS_TELEGRAM_GATEWAY_BOUNDARY_v0_1.md",
                "docs/reference/ROBOTICXS_TELEGRAM_ACTION_PACKET_FLOW_v0_1.md",
                "docs/reference/ROBOTICXS_TELEGRAM_MEMORY_ROUTINE_FLOW_v0_1.md",
                "tests/test_telegram_hermes_gateway_mvp.py",
                "tests/test_telegram_gateway_boundary.py",
                "tests/test_telegram_action_packet_flow.py",
                "tests/test_telegram_memory_routine_flow.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the Telegram MVP on Hermes Gateway story/spec/test contract. 95P and 96P are closed committed; do not infer runtime gateway startup, production Telegram messaging, credentials, UI, 97P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["94P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_94p_closeout_transition_records_later_95p_authorization_without_live_runtime_or_credentials():
    transition = load_json_block("stage-94p-closeout-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "closeout_status": "CLOSED_COMMITTED",
        "commit": "97777ca68e0443e17236e9858ce350f68ed77864",
        "commit_message": "docs: add telegram hermes gateway mvp",
        "closed_stage": "94P",
        "closed_stage_name": "Telegram MVP on Hermes Gateway v0",
        "stage_95p_authorized_later": True,
        "stage_96p_and_later_authorized": False,
        "next_eligible_stage": "95P",
        "runtime_gateway_start_authorized": False,
        "production_messaging_authorized": False,
        "telegram_credentials_authorized": False,
        "implementation_authorized": False,
    }
    assert stages_by_id["94P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["95P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_95p_is_telegram_hermes_policy_chain_runtime_skeleton_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["95P"] == {
        "stage_id": "95P",
        "stage_name": "Telegram-Hermes Policy Chain Runtime Skeleton v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "699f5e8953227bb16164b5ee7c8749f662b6d731",
            "commit_message": "feat: add telegram hermes policy chain runtime skeleton",
            "paths": [
                "app/telegram_policy_chain.py",
                "app/main.py",
                "docs/reference/TELEGRAM_HERMES_POLICY_CHAIN_RUNTIME_SKELETON_95P_v0_1.md",
                "tests/test_telegram_policy_chain_95p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Telegram-Hermes policy-chain runtime skeleton baseline. 96P is closed committed; do not infer caregiver behavior, live Telegram sends, live Hermes Gateway startup, live cron scheduling, connector activation, external writes, payments, publishing, browser/email/WhatsApp execution, production credentials, 97P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["95P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_95p_transition_records_later_96p_authorization_and_blocks_external_runtime_surfaces():
    transition = load_json_block("stage-95p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "95P",
        "stage_name": "Telegram-Hermes Policy Chain Runtime Skeleton v0",
        "implementation_commit": "699f5e8953227bb16164b5ee7c8749f662b6d731",
        "stage_96p_authorized_later": True,
        "stage_97p_and_later_authorized": False,
        "next_eligible_stage": "96P",
        "caregiver_behavior_authorized": False,
        "live_telegram_sends_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_scheduling_authorized": False,
        "connector_activation_authorized": False,
        "external_writes_authorized": False,
        "payments_authorized": False,
        "publishing_authorized": False,
        "browser_email_whatsapp_execution_authorized": False,
        "production_credentials_authorized": False,
    }
    assert stages_by_id["95P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["96P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_96p_is_hermes_os_runtime_contract_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["96P"] == {
        "stage_id": "96P",
        "stage_name": "Hermes OS Runtime Contract v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "d2aa97d",
            "commit_message": "feat: add hermes os runtime contract",
            "paths": [
                "app/hermes_os_contract.py",
                "docs/reference/HERMES_OS_RUNTIME_CONTRACT_96P_v0_1.md",
                "tests/test_hermes_os_runtime_contract_96p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local Hermes OS runtime contract baseline. 97P is closed committed; do not infer live Hermes startup, live cron execution, live Telegram sends, connector activation, model provider calls, auto skill install, production credentials, external writes, payments, publishing, browser/email/WhatsApp execution, destructive actions, 98P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["96P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_96p_transition_records_later_97p_authorization_and_blocks_external_runtime_surfaces():
    transition = load_json_block("stage-96p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "96P",
        "stage_name": "Hermes OS Runtime Contract v0",
        "implementation_commit": "d2aa97d",
        "stage_97p_authorized_later": True,
        "stage_98p_and_later_authorized": False,
        "next_eligible_stage": "97P",
        "caregiver_workflows_authorized": "local_deterministic_97p_slice_only",
        "live_hermes_start_authorized": False,
        "live_cron_execution_authorized": False,
        "live_telegram_sends_authorized": False,
        "connector_activation_authorized": False,
        "model_provider_calls_authorized": False,
        "auto_skill_install_authorized": False,
        "production_credentials_authorized": False,
        "external_writes_authorized": False,
        "payments_authorized": False,
        "publishing_authorized": False,
        "browser_email_whatsapp_execution_authorized": False,
        "destructive_actions_authorized": False,
    }
    assert stages_by_id["96P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["97P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_97p_is_caregiver_telegram_mvp_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["97P"] == {
        "stage_id": "97P",
        "stage_name": "Caregiver Telegram MVP v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_97P_closeout",
            "commit_message": "feat: add caregiver telegram mvp slice",
            "paths": [
                "app/caregiver_telegram_mvp.py",
                "app/telegram_policy_chain.py",
                "app/main.py",
                "docs/reference/CAREGIVER_TELEGRAM_MVP_97P_v0_1.md",
                "tests/test_caregiver_telegram_mvp_97p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic caregiver Telegram MVP slice. 98P is closed committed; do not infer live Telegram sends, automatic caregiver alerts, live Hermes startup, live cron execution, connector activation, model provider calls, production credentials, external writes, payments, publishing, browser/email/WhatsApp execution, medical decisions, medication changes, emergency monitoring, destructive actions, 99P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["97P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_97p_transition_records_later_98p_authorization_and_blocks_external_runtime_surfaces():
    transition = load_json_block("stage-97p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "97P",
        "stage_name": "Caregiver Telegram MVP v0",
        "implementation_commit": "same_commit_as_97P_closeout",
        "stage_98p_authorized_later": True,
        "stage_99p_and_later_authorized": False,
        "next_eligible_stage": "98P",
        "live_telegram_sends_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
        "live_hermes_start_authorized": False,
        "live_cron_execution_authorized": False,
        "connector_activation_authorized": False,
        "model_provider_calls_authorized": False,
        "production_credentials_authorized": False,
        "external_writes_authorized": False,
        "payments_authorized": False,
        "publishing_authorized": False,
        "browser_email_whatsapp_execution_authorized": False,
        "medical_decisions_authorized": False,
        "medication_changes_authorized": False,
        "emergency_monitoring_authorized": False,
        "destructive_actions_authorized": False,
    }
    assert stages_by_id["97P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["98P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_98p_is_routine_execution_engine_closed_committed_and_self_referenced():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["98P"] == {
        "stage_id": "98P",
        "stage_name": "Routine Execution Engine Skeleton v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_98P_closeout",
            "commit_message": "feat: add routine execution engine skeleton",
            "paths": [
                "app/routine_execution_engine.py",
                "app/main.py",
                "docs/reference/ROUTINE_EXECUTION_ENGINE_98P_v0_1.md",
                "tests/test_routine_execution_engine_98p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic routine execution engine skeleton. 99P and 100P are closed committed; do not infer live scheduler, live cron, live Telegram sends, automatic delivery, automatic caregiver alerts, live Hermes startup, connector activation, model provider calls, production credentials, external writes, payments, publishing, browser/email/WhatsApp execution, medical decisions, medication changes, emergency monitoring, destructive actions, 101P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["98P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_98p_transition_blocks_99p_and_external_runtime_surfaces():
    transition = load_json_block("stage-98p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "98P",
        "stage_name": "Routine Execution Engine Skeleton v0",
        "implementation_commit": "same_commit_as_98P_closeout",
        "stage_99p_and_later_authorized": False,
        "next_eligible_stage": None,
        "live_scheduler_authorized": False,
        "live_cron_authorized": False,
        "live_telegram_sends_authorized": False,
        "automatic_delivery_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
        "live_hermes_start_authorized": False,
        "connector_activation_authorized": False,
        "model_provider_calls_authorized": False,
        "production_credentials_authorized": False,
        "external_writes_authorized": False,
        "payments_authorized": False,
        "publishing_authorized": False,
        "browser_email_whatsapp_execution_authorized": False,
        "medical_decisions_authorized": False,
        "medication_changes_authorized": False,
        "emergency_monitoring_authorized": False,
        "destructive_actions_authorized": False,
    }
    assert stages_by_id["98P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_99p_transition_records_later_100p_authorization_and_keeps_101p_blocked():
    transition = load_json_block("stage-99p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "99P",
        "stage_name": "Memory Center Projection Runtime Slice v0",
        "implementation_commit": "same_commit_as_99P_closeout",
        "stage_100p_authorized_later": True,
        "stage_101p_and_later_authorized": False,
        "next_eligible_stage": "100P",
        "database_migrations_authorized": False,
        "canonical_memory_writes_authorized": False,
        "ui_or_endpoints_authorized": False,
        "live_telegram_or_hermes_authorized": False,
        "live_cron_authorized": False,
        "connector_or_provider_calls_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["99P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["100P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_100p_is_cost_governor_model_routing_runtime_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["100P"] == {
        "stage_id": "100P",
        "stage_name": "Cost Governor / Model Routing Runtime v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_100P_closeout",
            "commit_message": "feat: add cost governor model routing runtime",
            "paths": [
                "app/cost_governor.py",
                "app/telegram_policy_chain.py",
                "app/hermes_os_contract.py",
                "app/routine_execution_engine.py",
                "docs/reference/COST_GOVERNOR_MODEL_ROUTING_RUNTIME_100P_v0_1.md",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_cost_governor_model_routing_100p.py",
                "tests/test_telegram_policy_chain_95p.py",
                "tests/test_routine_execution_engine_98p.py",
                "tests/test_canonical_roadmap.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic cost governor and model-routing runtime baseline. 101P and 102P are closed committed; 103P, 104P, 105P, 106P, 107P, 108P, 109P, 110P, and 111P are closed committed; 112P and later remain unauthorized. Do not infer async delegation dispatch, live Telegram sends, live Hermes startup, live cron scheduling, connectors, provider calls, billing, credential checks, migrations, UI, endpoints, external writes, payments, publishing, browser/email/WhatsApp execution, destructive actions, medical decisions, emergency monitoring, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["100P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_101p_is_action_packet_approval_loop_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["101P"] == {
        "stage_id": "101P",
        "stage_name": "Action Packet Approval Loop v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_101P_closeout",
            "commit_message": "docs: close action packet approval loop",
            "paths": [
                "app/action_packet_approval.py",
                "app/cost_governor.py",
                "app/routine_execution_engine.py",
                "app/telegram_policy_chain.py",
                "docs/reference/ROBOTICXS_ACTION_PACKET_APPROVAL_LOOP_101P_v0_1.md",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_action_packet_approval_101p.py",
                "tests/test_telegram_policy_chain_95p.py",
                "tests/test_routine_execution_engine_98p.py",
                "tests/test_cost_governor_model_routing_100p.py",
                "tests/test_memory_center_projection_99p.py",
                "tests/test_hermes_os_runtime_contract_96p.py",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Action Packet approval loop baseline. 102P is closed committed; 103P, 104P, 105P, 106P, 107P, 108P, 109P, 110P, and 111P are closed committed; 112P and later remain unauthorized. Do not infer live execution, async delegation dispatch, live Telegram sends, live Hermes startup, live cron scheduling, connectors, provider calls, billing, credential checks, migrations, UI, endpoints, external writes, payments, publishing, browser/email/WhatsApp execution, destructive actions, medical decisions, emergency monitoring, automatic caregiver alerts, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["101P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_102p_is_async_delegation_authority_adapter_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["102P"] == {
        "stage_id": "102P",
        "stage_name": "Hermes Async Delegation Authority Adapter v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_102P_closeout",
            "commit_message": "docs: close async delegation authority adapter",
            "paths": [
                "app/async_delegation_authority.py",
                "tests/test_async_delegation_authority_102p.py",
                "docs/reference/HERMES_ASYNC_DELEGATION_AUTHORITY_ADAPTER_102P_v0_1.md",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic async delegation authority adapter baseline. 102P is closed committed after remediation review and validation. 103P, 104P, 105P, 106P, and 107P are closed committed. Do not infer live Hermes delegate_task, background dispatch, live subagents, provider calls, connector activation, live Telegram sends, external effects, 108P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["102P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_103p_is_async_delegation_completion_inbox_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["103P"] == {
        "stage_id": "103P",
        "stage_name": "Async Delegation Completion Inbox v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_103P_closeout",
            "commit_message": "docs: close async delegation completion inbox",
            "paths": [
                "app/async_delegation_inbox.py",
                "tests/test_async_delegation_completion_inbox_103p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic async delegation completion inbox baseline. 103P is closed committed after implementation, validation, and closeout review. 104P, 105P, 106P, and 107P are closed committed. Do not infer async workers, live Hermes delegate_task, background dispatch, callbacks, live subagents, provider calls, connector activation, live Telegram sends, Memory Center mutation, external effects, 108P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["103P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_104p_is_async_result_user_surface_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["104P"] == {
        "stage_id": "104P",
        "stage_name": "Async Result User Surface v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_104P_closeout",
            "commit_message": "docs: close async result user surface",
            "paths": [
                "app/async_result_surface.py",
                "tests/test_async_result_user_surface_104p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic async result user surface baseline. 104P is closed committed after implementation, validation, and closeout review. 105P, 106P, and 107P are closed committed. Do not infer model calls, new delegations, approvals, Memory Center mutation, external effects, 108P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["104P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_105p_is_telegram_async_result_delivery_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["105P"] == {
        "stage_id": "105P",
        "stage_name": "Telegram Async Result Delivery v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_105P_closeout",
            "commit_message": "feat: add telegram async result delivery",
            "paths": [
                "app/telegram_async_result_delivery.py",
                "tests/test_telegram_async_result_delivery_105p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram async result delivery baseline. 105P is closed committed after implementation, validation, and closeout review. 106P and 107P are closed committed. Do not infer Telegram callback execution, new delegations, new approvals, Memory Center mutation, external effects, 108P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["105P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_106p_is_telegram_result_acknowledgement_binding_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["106P"] == {
        "stage_id": "106P",
        "stage_name": "Telegram Result Acknowledgement Binding v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_106P_closeout",
            "commit_message": "feat: add telegram result acknowledgement binding",
            "paths": [
                "app/telegram_result_acknowledgement.py",
                "tests/test_telegram_result_acknowledgement_106p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram result acknowledgement baseline. 106P is closed committed after implementation, validation, and closeout review. 107P is closed committed. Do not infer Telegram callback execution authority, new delegations, new approvals, Memory Center mutation, external effects, 108P, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["106P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_107p_is_followup_intent_review_queue_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["107P"] == {
        "stage_id": "107P",
        "stage_name": "Follow-up Intent Review Queue v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_107P_closeout",
            "commit_message": "feat: add follow-up intent review queue",
            "paths": [
                "app/followup_intent_review.py",
                "tests/test_followup_intent_review_107p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up intent review queue baseline. 107P is closed committed after implementation, validation, and closeout review. 108P, 109P, 110P, and 111P are closed committed after follow-up planning, Telegram choice-surface validation, local selection binding validation, and governed delegation registration validation. Do not infer follow-up execution, worker dispatch, completion events, model/tool calls, Memory Center mutation, Telegram sends beyond approved owner-scoped local transport, external effects, 112P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["107P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_108p_is_followup_draft_planner_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["108P"] == {
        "stage_id": "108P",
        "stage_name": "Follow-up Draft Planner v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_108P_closeout",
            "commit_message": "feat: add follow-up draft planner",
            "paths": [
                "app/followup_draft_planner.py",
                "tests/test_followup_draft_planner_108p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up draft planner baseline. 108P is closed committed after implementation, validation, and closeout review. 109P later added Telegram-facing choice surfaces only, 110P later added local option selection binding only, and 111P later added local governed delegation registration only. Do not infer follow-up execution, worker dispatch, completion events, model/tool calls, Memory Center mutation, live Telegram APIs, external effects, 112P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["108P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_109p_is_telegram_followup_choice_surface_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["109P"] == {
        "stage_id": "109P",
        "stage_name": "Telegram Follow-up Choice Surface v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_109P_closeout",
            "commit_message": "feat: add telegram follow-up choice surface",
            "paths": [
                "app/telegram_followup_choice_surface.py",
                "tests/test_telegram_followup_choice_surface_109p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram follow-up choice surface baseline. 109P is closed committed after implementation, validation, and closeout review. 110P later added local selection binding only, and 111P later added local governed delegation registration only. Do not infer follow-up execution, worker dispatch, completion events, new approvals, action packets, model/tool calls, Memory Center mutation, live Telegram APIs, external effects, 112P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["109P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_110p_is_telegram_followup_choice_selection_binding_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["110P"] == {
        "stage_id": "110P",
        "stage_name": "Telegram Follow-up Choice Selection Binding v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_110P_closeout",
            "commit_message": "feat: add telegram follow-up choice selection binding",
            "paths": [
                "app/telegram_followup_choice_selection.py",
                "app/telegram_followup_choice_surface.py",
                "tests/test_telegram_followup_choice_selection_110p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram follow-up choice selection binding baseline. 110P is closed committed after implementation, validation, and closeout review. 111P later added local governed follow-up delegation creation only. Do not infer follow-up execution, workers, completion events, model/tool calls, Memory Center mutation, live Telegram APIs, external effects, 112P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["110P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_111p_is_user_approved_followup_delegation_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["111P"] == {
        "stage_id": "111P",
        "stage_name": "User-Approved Follow-up Delegation v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_111P_closeout",
            "commit_message": "feat: add follow-up delegation authority",
            "paths": [
                "app/followup_delegation_authority.py",
                "app/async_delegation_authority.py",
                "tests/test_followup_delegation_authority_111p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up delegation authority baseline. 111P is closed committed after implementation, validation, and closeout review. Do not infer follow-up execution, worker dispatch, completion or failure events, model/tool calls, Memory Center mutation, live Telegram APIs, external effects, 112P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["111P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_112p_is_controlled_followup_execution_skeleton_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["112P"] == {
        "stage_id": "112P",
        "stage_name": "Controlled Follow-up Execution Skeleton v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_112P_closeout",
            "commit_message": "feat: add controlled follow-up execution skeleton",
            "paths": [
                "app/followup_execution_skeleton.py",
                "tests/test_followup_execution_skeleton_112p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic controlled follow-up execution skeleton baseline. 112P is closed committed after implementation, validation, and closeout review. Do not infer 103P inbox insertion, 104P result surfaces, 105P Telegram delivery, model/tool calls, worker dispatch, Memory Center mutation, live Telegram APIs, external effects, 113P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["112P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_113p_is_followup_completion_loop_integration_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["113P"] == {
        "stage_id": "113P",
        "stage_name": "Follow-up Completion Loop Integration v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_113P_closeout",
            "commit_message": "feat: add follow-up completion loop integration",
            "paths": [
                "app/followup_completion_loop.py",
                "tests/test_followup_completion_loop_113p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up completion loop integration baseline. 113P is closed committed after implementation, validation, and closeout review. 114P later added local acknowledgement binding only. Do not infer new follow-up execution, live Telegram APIs, memory proposal/writeback behavior, model/tool calls, worker dispatch, external effects, 115P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["113P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_114p_is_followup_result_acknowledgement_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["114P"] == {
        "stage_id": "114P",
        "stage_name": "Follow-up Result Acknowledgement v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_114P_closeout",
            "commit_message": "feat: add follow-up result acknowledgement",
            "paths": [
                "app/followup_result_acknowledgement.py",
                "tests/test_followup_result_acknowledgement_114p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up result acknowledgement baseline. 114P is closed committed after implementation, validation, and closeout review. 115P later added local memory proposal candidates only, 116P later added local Telegram-facing approval surfaces and approval binding only, 117P later added local Memory Center writeback only, 118P later added local context scan candidate source records only, 119P later added local proactive opportunity candidate detection only, 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer new follow-up execution, new draft options, selections, delegations, executions, routes, live connector reads, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["114P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_115p_is_followup_memory_proposal_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["115P"] == {
        "stage_id": "115P",
        "stage_name": "Memory Proposal from Follow-up Result v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_115P_closeout",
            "commit_message": "feat: add follow-up memory proposal candidates",
            "paths": [
                "app/followup_memory_proposal.py",
                "tests/test_followup_memory_proposal_115p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic follow-up memory proposal candidate baseline. 115P is closed committed after implementation, validation, and closeout review. 116P later added Telegram-facing approval surfaces and local approval binding only, 117P later added local Memory Center writeback only, 118P later added local context scan candidate source records only, 119P later added local proactive opportunity candidate detection only, 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer new action packets, new delegations, new follow-up execution, live connector reads, model/tool calls, live Telegram APIs, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["115P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_116p_is_telegram_memory_proposal_approval_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["116P"] == {
        "stage_id": "116P",
        "stage_name": "Telegram Memory Proposal Approval v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_116P_closeout",
            "commit_message": "feat: add telegram memory proposal approval",
            "paths": [
                "app/telegram_memory_proposal_approval.py",
                "tests/test_telegram_memory_proposal_approval_116p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Telegram memory proposal approval baseline. 116P is closed committed after implementation, validation, and closeout review. 117P later added local Memory Center writeback only, 118P later added local context scan candidate source records only, 119P later added local proactive opportunity candidate detection only, 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer automatic later-stage execution, new action packets, new delegations, new follow-up execution, live connector reads, model/tool calls, live Telegram APIs, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["116P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_117p_is_memory_center_writeback_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["117P"] == {
        "stage_id": "117P",
        "stage_name": "Memory Center Writeback v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_117P_closeout",
            "commit_message": "feat: add memory center writeback",
            "paths": [
                "app/memory_center_writeback.py",
                "tests/test_memory_center_writeback_117p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Memory Center writeback baseline. 117P is closed committed after implementation, validation, and closeout review. 118P later added local context scan candidate source records only, 119P later added local proactive opportunity candidate detection only, 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer live connector reads, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["117P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_118p_is_context_scan_candidate_source_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["118P"] == {
        "stage_id": "118P",
        "stage_name": "Context Scan Candidate Source v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_118P_closeout",
            "commit_message": "feat: add context scan candidate sources",
            "paths": [
                "app/context_scan_candidate_source.py",
                "tests/test_context_scan_candidate_source_118p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic Context Scan candidate source baseline. 118P is closed committed after implementation, validation, and closeout review. 119P later added local proactive opportunity candidate detection only, 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer live connector reads, scan extraction, memory proposals, memory writes, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["118P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_119p_is_proactive_opportunity_detection_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["119P"] == {
        "stage_id": "119P",
        "stage_name": "Proactive Opportunity Detection v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_119P_closeout",
            "commit_message": "feat: add proactive opportunity detection",
            "paths": [
                "app/proactive_opportunity_detection.py",
                "tests/test_proactive_opportunity_detection_119p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic proactive opportunity detection baseline. 119P is closed committed after implementation, validation, and closeout review. 120P later added local proactive Telegram suggestion surfaces and local delivery only, 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer planning, choice surfaces, selections, delegations, execution, Memory Center mutation, live connector reads, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["119P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_120p_is_proactive_telegram_suggestion_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["120P"] == {
        "stage_id": "120P",
        "stage_name": "Proactive Telegram Suggestion v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_120P_closeout",
            "commit_message": "feat: add proactive telegram suggestions",
            "paths": [
                "app/proactive_telegram_suggestion.py",
                "tests/test_proactive_telegram_suggestion_120p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic proactive Telegram suggestion baseline. 120P is closed committed after implementation, validation, and closeout review. 121P later added local adaptation into a 107P-compatible follow-up intent-review record only, 122P later added local governed proactive delegation registration only, and 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer callback binding, acknowledgement, planner execution, choice surfaces, selections, delegations, execution, Memory Center mutation, live Telegram APIs, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["120P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_121p_is_proactive_suggestion_adapter_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["121P"] == {
        "stage_id": "121P",
        "stage_name": "Proactive Suggestion Adapter to Follow-up Loop v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_121P_closeout",
            "commit_message": "feat: add proactive suggestion adapter",
            "paths": [
                "app/proactive_suggestion_adapter.py",
                "tests/test_proactive_suggestion_adapter_121p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic proactive suggestion adapter baseline. 121P is closed committed after implementation, validation, and closeout review. 122P later added local governed delegation registration for explicitly authorized proactive-sourced selections only. 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer planner execution, Telegram choice surfaces, selection binding outside the existing follow-up path, inbox routing, result surfaces, Telegram delivery, Memory Center mutation, live Telegram APIs, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["121P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_122p_is_proactive_delegation_adapter_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["122P"] == {
        "stage_id": "122P",
        "stage_name": "Proactive Delegation Adapter v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_122P_closeout",
            "commit_message": "feat: add proactive delegation adapter",
            "paths": [
                "app/proactive_delegation_adapter.py",
                "tests/test_proactive_delegation_adapter_122p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic proactive delegation adapter baseline. 122P is closed committed after implementation, validation, and closeout review. It reuses the existing 111P-style governed delegation authority path for explicitly authorized proactive-sourced work and stops at packet and handle registration only. 123P later added local deterministic proactive execution attempts and local completion or failure event candidates only. Do not infer inbox routing, result surfaces, Telegram delivery, Memory Center mutation, live connector reads, model/tool calls, external effects, 124P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["122P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_123p_is_controlled_proactive_execution_skeleton_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["123P"] == {
        "stage_id": "123P",
        "stage_name": "Controlled Proactive Execution Skeleton v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_123P_closeout",
            "commit_message": "feat: add controlled proactive execution skeleton",
            "paths": [
                "app/proactive_execution_skeleton.py",
                "tests/test_proactive_execution_skeleton_123p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic proactive execution skeleton baseline. 123P is closed committed after implementation, validation, and closeout review. It executes governed proactive-origin delegations through deterministic local skeleton behavior only and produces local completion or failure event candidates only. 124P later added deterministic read-only daily brief snapshots only, 125P later added deterministic read-only skill pack activation surfaces only, 126P later added a deterministic local first-demo composition flow only, 127P later added a deterministic local owner-facing demo result surface only, 128P later added a deterministic local document-review demo flow only, 129P later added a runnable local Hermes runtime bootstrap shell only, and 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer inbox routing, result surfaces beyond the closed local demo surfaces, Telegram delivery beyond the closed command replies, Memory Center mutation, live connector reads, model/tool calls, worker dispatch, external effects, 131P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["123P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_124p_is_what_did_i_miss_daily_brief_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["124P"] == {
        "stage_id": "124P",
        "stage_name": "What Did I Miss? Daily Brief v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_124P_closeout",
            "commit_message": "feat: add what did i miss daily brief",
            "paths": [
                "app/daily_brief_what_did_i_miss.py",
                "tests/test_daily_brief_what_did_i_miss_124p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic read-only daily brief baseline. 124P is closed committed after implementation, validation, and closeout review. It aggregates existing 103P through 123P local records into read-only daily brief snapshots and renderable local text only. 125P later added deterministic read-only skill pack classification surfaces only, 126P later added a deterministic local first-demo composition flow only, 127P later added a deterministic local owner-facing demo result surface only, 128P later added a deterministic local document-review demo flow only, 129P later added a runnable local Hermes runtime bootstrap shell only, and 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer Telegram delivery beyond the closed command replies, callback binding, follow-up intent creation, async delegations, execution, Memory Center mutation, model/tool calls, live connector reads, external writes, worker dispatch, 131P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["124P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_125p_is_skill_pack_activation_surface_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["125P"] == {
        "stage_id": "125P",
        "stage_name": "Skill Pack Activation Surface v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_125P_closeout",
            "commit_message": "feat: add skill pack activation surface",
            "paths": [
                "app/skill_pack_activation_surface.py",
                "tests/test_skill_pack_activation_surface_125p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic read-only skill pack activation baseline. 125P is closed committed after implementation, validation, and closeout review. It classifies existing 103P through 124P local records into skill pack surfaces and renderable local text only. 126P later added a deterministic local first-demo composition flow only, 127P later added a deterministic local owner-facing demo result surface only, 128P later added a deterministic local document-review demo flow only, 129P later added a runnable local Hermes runtime bootstrap shell only, and 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer billing, entitlement enforcement, package activation, upgrade prompts, Telegram delivery beyond the closed command replies, callback binding, follow-up intent creation, async delegations, execution, Memory Center mutation, model/tool calls, live connector reads, external writes, worker dispatch, 131P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["125P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_126p_is_first_demo_flow_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["126P"] == {
        "stage_id": "126P",
        "stage_name": "First Demo Flow: Meeting Brief from Context v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_126P_closeout",
            "commit_message": "feat: add meeting brief demo flow",
            "paths": [
                "app/meeting_brief_demo_flow.py",
                "tests/test_meeting_brief_demo_flow_126p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic first product-demo baseline. 126P is closed committed after implementation, validation, and closeout review. It composes existing 118P through 125P local primitives into a deterministic local meeting-brief demo flow, preserves normalized_intent_kind=prepare_meeting_brief as product lineage, reuses the existing governed human_review_checklist / FOLLOWUP_HUMAN_REVIEW_CHECKLIST task class for deterministic local execution, and stops at local demo artifacts, daily brief inclusion, and skill pack inclusion only. 127P later added a deterministic local owner-facing demo result surface only. 128P later added a deterministic local document-review demo flow only. 129P later added a runnable local Hermes runtime bootstrap shell only. 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer new task classes, new authority paths, live connector reads, Telegram delivery beyond the closed command replies, model/tool calls, worker dispatch, Memory Center mutation, billing, entitlement enforcement, external writes, 131P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["126P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_127p_is_demo_result_delivery_surface_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["127P"] == {
        "stage_id": "127P",
        "stage_name": "Demo Result Delivery Surface v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_127P_closeout",
            "commit_message": "feat: add demo result delivery surface",
            "paths": [
                "app/demo_result_delivery_surface.py",
                "tests/test_demo_result_delivery_surface_127p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the deterministic local owner-facing demo result surface baseline. 127P is closed committed after implementation, validation, and closeout review. It consumes valid 126P meeting-brief demo flow and artifact records, preserves 118P through 126P lineage, renders only a deterministic local owner-facing result surface, and does not deliver through live Telegram, bind callbacks, create approvals or follow-up intents, delegate, execute, mutate Memory Center, call models/tools, read live connectors, dispatch workers, enforce billing or entitlements, or write external systems. 128P later added a deterministic local document-review demo flow only. 129P later added a runnable local Hermes runtime bootstrap shell only. 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer 131P+, NEXT_ELIGIBLE, or any new authority path from this status.",
    }
    for path in stages_by_id["127P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_128p_is_document_review_demo_flow_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["128P"] == {
        "stage_id": "128P",
        "stage_name": "Document Review Demo Flow v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_128P_closeout",
            "commit_message": "feat: add document review demo flow",
            "paths": [
                "app/document_review_demo_flow.py",
                "tests/test_document_review_demo_flow_128p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local deterministic document-review product-demo baseline. 128P is closed committed after implementation, validation, and closeout review. It composes existing 118P through 127P local primitives into a deterministic local document-review demo flow, preserves normalized_intent_kind=review_document as product lineage, reuses the existing governed human_review_checklist / FOLLOWUP_HUMAN_REVIEW_CHECKLIST task class for deterministic local execution, classifies the work under documents_pack, and stops at local demo artifacts and local owner-facing presentation only. 129P later added a runnable local Hermes runtime bootstrap shell only. 130P later added a runnable owner-gated Telegram robot with deterministic replies only. Do not infer live document reads, OCR, legal advice, signature creation, new task classes, new authority paths, Telegram delivery beyond the closed command replies, model/tool calls, worker dispatch, Memory Center mutation, billing, entitlement enforcement, external writes, 131P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["128P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_129p_is_hermes_runtime_bootstrap_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["129P"] == {
        "stage_id": "129P",
        "stage_name": "Hermes Runtime Bootstrap v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_129P_closeout",
            "commit_message": "feat: add hermes runtime bootstrap",
            "paths": [
                "app/hermes_runtime_bootstrap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the runnable local Hermes runtime bootstrap baseline. 129P is closed committed after implementation, validation, and closeout review. It loads deterministic local config, validates robot and owner identity, reports runtime health, local feature availability, and disabled live integrations, and stops before Telegram startup, connector reads, model/tool calls, worker dispatch, Memory Center mutation, billing, entitlement enforcement, or external writes. 130P later added a runnable owner-gated Telegram robot with deterministic /start, /help, and /status replies only. Do not infer 131P+, NEXT_ELIGIBLE, live runtime integrations beyond the closed Telegram command surface, or any new execution authority from this status.",
    }
    for path in stages_by_id["129P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_130p_is_runnable_telegram_robot_mvp_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["130P"] == {
        "stage_id": "130P",
        "stage_name": "Runnable Telegram Robot MVP v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_130P_closeout",
            "commit_message": "feat: add runnable telegram robot mvp",
            "paths": [
                "app/runnable_telegram_robot_mvp.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the runnable owner-gated Telegram robot baseline. 130P is closed committed after implementation, validation, and closeout review. It runs a live/dev Telegram bot with deterministic /start, /help, and /status replies, owner gating by Telegram user id, bounded polling helpers, and Telegram sendMessage replies only. 131P later added deterministic owner-gated /miss replies backed by the existing 124P local daily brief path only. 132P later added deterministic owner-gated /brief replies backed by the existing 126P local meeting brief path only. 133P later added a local manual Google Calendar read-only connector only. Do not infer live connector-backed Telegram behavior, model/tool calls, workers, Memory Center mutation, async delegation, billing, entitlement enforcement, external writes beyond Telegram replies, 138P+, or NEXT_ELIGIBLE from this status.",
    }
    for path in stages_by_id["130P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_131p_is_telegram_what_did_i_miss_command_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["131P"] == {
        "stage_id": "131P",
        "stage_name": "Telegram What Did I Miss Command v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_131P_closeout",
            "commit_message": "feat: add telegram what did i miss command",
            "paths": [
                "app/runnable_telegram_robot_mvp.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_telegram_what_did_i_miss_131p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the runnable owner-gated Telegram what did i miss baseline. 131P is closed committed after implementation, validation, and closeout review. It adds deterministic owner-gated /miss replies backed by the existing 124P local daily brief path and preserves Telegram sendMessage replies as the only external write. 132P later added deterministic owner-gated /brief replies backed by the existing 126P local meeting brief path only. 133P later added a local manual Google Calendar read-only connector only. Do not infer 138P+, NEXT_ELIGIBLE, live connector-backed Telegram behavior, model/tool calls, worker dispatch, Memory Center mutation, async delegation, billing, entitlement enforcement, or external writes beyond Telegram replies from this status.",
    }
    for path in stages_by_id["131P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_132p_is_telegram_meeting_brief_command_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["132P"] == {
        "stage_id": "132P",
        "stage_name": "Telegram Meeting Brief Command v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_132P_closeout",
            "commit_message": "feat: add telegram meeting brief command",
            "paths": [
                "app/runnable_telegram_robot_mvp.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_telegram_what_did_i_miss_131p.py",
                "tests/test_telegram_meeting_brief_132p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the runnable owner-gated Telegram meeting brief baseline. 132P is closed committed after implementation, validation, and closeout review. It adds deterministic owner-gated /brief replies backed by the existing 126P local meeting brief path, keeps /miss enabled, and preserves Telegram sendMessage replies as the only external write. 133P later added a local manual Google Calendar read-only connector only and did not change Telegram /brief behavior. Do not infer 138P+, NEXT_ELIGIBLE, live connector-backed Telegram behavior, model/tool calls, worker dispatch, Memory Center mutation, async delegation, billing, entitlement enforcement, or external writes beyond Telegram replies from this status.",
    }
    for path in stages_by_id["132P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_133p_is_read_only_google_calendar_connector_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["133P"] == {
        "stage_id": "133P",
        "stage_name": "Read-Only Google Calendar Connector v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_133P_closeout",
            "commit_message": "feat: add read-only google calendar connector",
            "paths": [
                "app/google_calendar_readonly_connector.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_google_calendar_readonly_connector_133p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local manual Google Calendar read-only connector baseline. 133P is closed committed after implementation, validation, and closeout review. It reads upcoming events from Google Calendar through a read-only bearer token, normalizes them into a deterministic local snapshot, renders a local CLI smoke output, and keeps read_only=true, external_writes=false, and memory_mutation=false. 134P later added bounded owner-gated Telegram /brief read-only Calendar backing only. It does not authorize Calendar writes, Memory Center mutation, model/tool calls, worker dispatch, billing, entitlement enforcement, or 143P+ behavior.",
    }
    for path in stages_by_id["133P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_134p_is_calendar_backed_telegram_meeting_brief_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["134P"] == {
        "stage_id": "134P",
        "stage_name": "Calendar-backed Telegram Meeting Brief v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_134P_closeout",
            "commit_message": "feat: add calendar-backed telegram meeting brief",
            "paths": [
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_telegram_calendar_brief_134p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_telegram_what_did_i_miss_131p.py",
                "tests/test_telegram_meeting_brief_132p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the bounded owner-gated Telegram /brief Calendar backing baseline. 134P is closed committed after implementation, validation, and closeout review. It lets authorized /brief replies include a read-only Google Calendar snapshot through the existing 133P connector, fails closed to deterministic local meeting context when Calendar config or upstream access is unavailable, keeps Telegram sendMessage replies as the only external write, and preserves Calendar writes=false, Memory Center mutation=false, LLM/model calls=false, tools=false, workers=false, billing=false, and entitlement enforcement=false. 135P later added a reusable local real Calendar meeting brief composer/CLI only. It does not authorize Calendar create/update/delete, Memory Center mutation, model/tool calls, worker dispatch, async delegation, billing, entitlement enforcement, or 143P+ behavior.",
    }
    for path in stages_by_id["134P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_135p_is_real_calendar_meeting_brief_composer_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["135P"] == {
        "stage_id": "135P",
        "stage_name": "Real Calendar Meeting Brief Composer v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_135P_closeout",
            "commit_message": "feat: add real calendar meeting brief composer",
            "paths": [
                "app/real_calendar_meeting_brief.py",
                "tests/test_real_calendar_meeting_brief_135p.py",
                "app/hermes_runtime_bootstrap.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the reusable local real Calendar meeting brief composer baseline. 135P is closed committed after implementation, validation, and closeout review. It composes deterministic local meeting brief records and CLI output from the existing 133P Google Calendar read-only snapshot, fails closed when Calendar is unavailable, and preserves read_only=true, Calendar writes=false, external_writes=false, Memory Center mutation=false, LLM/model calls=false, tools=false, workers=false, billing=false, and entitlement enforcement=false. It does not change Telegram behavior beyond the existing 134P surface, and it does not authorize Calendar create/update/delete, Memory Center mutation, model/tool calls, worker dispatch, async delegation, billing, entitlement enforcement, or 143P+ behavior.",
    }
    for path in stages_by_id["135P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_138p_is_proactive_meeting_suggestion_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["138P"] == {
        "stage_id": "138P",
        "stage_name": "Proactive Meeting Suggestion v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_138P_closeout",
            "commit_message": "feat: add proactive meeting suggestion",
            "paths": [
                "docs/reference/PROACTIVE_MEETING_SUGGESTION_v0_1.md",
                "app/proactive_meeting_suggestion.py",
                "tests/test_proactive_meeting_suggestion_138p.py",
                "app/runnable_telegram_robot_mvp.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
                "tests/test_calendar_context_scan_137p.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-gated proactive meeting suggestion baseline. 138P detects upcoming Calendar meetings that deserve a brief from the existing 137P read-only Calendar context scan and suggests an action only. It does not execute /brief automatically, does not bind callbacks, does not create follow-up intents, does not delegate or dispatch workers, does not mutate Memory Center or ProposedMemory, does not call models or tools, does not write Calendar, and does not write externally beyond approved Telegram replies. 139P later added owner-requested suggested meeting brief rendering only. It does not authorize automatic /brief execution, callbacks, follow-up intents, async delegation, worker dispatch, Memory Center mutation, ProposedMemory writes, Calendar writes, model/tool calls, billing, entitlement enforcement, or 143P+ behavior.",
    }
    for path in stages_by_id["138P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_139p_is_owner_requested_suggested_meeting_brief_closed_committed():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["139P"] == {
        "stage_id": "139P",
        "stage_name": "Owner-Requested Suggested Meeting Brief v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_139P_closeout",
            "commit_message": "feat: add owner requested suggested meeting brief",
            "paths": [
                "docs/reference/SUGGESTED_MEETING_BRIEF_REQUEST_139P_v0_1.md",
                "app/suggested_meeting_brief_request.py",
                "tests/test_suggested_meeting_brief_request_139p.py",
                "app/proactive_meeting_suggestion.py",
                "tests/test_proactive_meeting_suggestion_138p.py",
                "app/runnable_telegram_robot_mvp.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-requested suggested meeting brief baseline. 139P lets the owner request /brief <suggestion_id> from a current 138P proactive meeting suggestion, revalidates the suggestion against the current Calendar context scan, and renders a deterministic read-only selected meeting brief only. It preserves /suggest_brief as action-only, keeps bare /brief behavior unchanged, and does not authorize automatic /brief execution, callbacks, follow-up intents, async delegation, worker dispatch, Memory Center mutation, ProposedMemory writes, Calendar writes, model/tool calls, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 140P later added a DeerFlow docs/test-only pattern review only. It does not authorize DeerFlow runtime integration, dependency installation, sandbox execution, Telegram replacement, memory mutation, model/tool calls, worker dispatch, or 143P+ behavior.",
    }
    for path in stages_by_id["139P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_140p_is_deerflow_pattern_review_closed_committed_docs_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["140P"] == {
        "stage_id": "140P",
        "stage_name": "DeerFlow Pattern Review / Sandbox Boundary Spike v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_140P_closeout",
            "commit_message": "docs: add deerflow pattern review",
            "paths": [
                "docs/reference/DEERFLOW_PATTERN_REVIEW_140P_v0_1.md",
                "tests/test_deerflow_pattern_review_140p.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the docs/test-only DeerFlow pattern review baseline. 140P evaluates DeerFlow as a reference for skills, sub-agents, sandbox execution, IM channels, memory, embedded-client experiments, and model-provider ergonomics. Hermes remains the Roboticxs runtime. DeerFlow is not a production dependency, is not installed, is not cloned, and is not integrated into runtime. 140P does not authorize sandbox execution, filesystem write authority, Telegram or IM channel replacement, owner-gate relaxation, connector config, Memory Center mutation, ProposedMemory writes, model/tool calls, worker dispatch, async delegation, external network behavior, billing, entitlement enforcement, or 143P+ behavior. 141P later added an owner-requested read-only Today command only. 142P later added an owner-requested read-only Open Loops command only. 143P and later remain unauthorized.",
    }
    for path in stages_by_id["140P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_141p_is_today_command_closed_committed_owner_gated_read_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["141P"] == {
        "stage_id": "141P",
        "stage_name": "Today Command v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_141P_closeout",
            "commit_message": "feat: add today command",
            "paths": [
                "docs/reference/TODAY_COMMAND_141P_v0_1.md",
                "app/today_command.py",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_today_command_141p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-requested read-only Today command baseline. 141P adds /today to the owner-gated Telegram command surface and composes existing 138P proactive meeting suggestions with existing 136P Memory Center visibility only. It fails closed for unavailable Calendar context, keeps Memory Center read-only, and preserves Telegram sendMessage replies as the only external write. It does not authorize proactive outbound daily pushes, scheduler, reminders, callbacks, buttons, follow-up intents, Memory Center mutation, ProposedMemory writes, Calendar writes, model/tool calls, worker dispatch, DeerFlow runtime integration, dependencies, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 142P later added an owner-requested read-only Open Loops command only. 143P and later remain unauthorized.",
    }
    for path in stages_by_id["141P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_142p_is_open_loops_command_closed_committed_owner_gated_read_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["142P"] == {
        "stage_id": "142P",
        "stage_name": "Open Loops Command v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_142P_closeout",
            "commit_message": "feat: add open loops command",
            "paths": [
                "docs/reference/OPEN_LOOPS_COMMAND_142P_v0_1.md",
                "app/open_loops_command.py",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_open_loops_command_142p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-requested read-only Open Loops command baseline. 142P adds /loops to the owner-gated Telegram command surface and composes existing 136P pending Memory Center proposal visibility with existing 138P proactive meeting suggestions only. It fails closed for unavailable Calendar context, keeps pending memory proposals marked as not facts, and preserves Telegram sendMessage replies as the only external write. It does not authorize task persistence, follow-up intents, reminders, scheduler, callbacks, buttons, Memory Center mutation, ProposedMemory writes, Calendar writes, model/tool calls, worker dispatch, DeerFlow runtime integration, dependencies, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 143P later added an owner-requested read-only Meeting Prep Pack command only. 144P and later remain unauthorized.",
    }
    for path in stages_by_id["142P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_143p_is_meeting_prep_pack_closed_committed_owner_gated_read_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["143P"] == {
        "stage_id": "143P",
        "stage_name": "Meeting Prep Pack v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_143P_closeout",
            "commit_message": "feat: add meeting prep pack",
            "paths": [
                "docs/reference/MEETING_PREP_PACK_143P_v0_1.md",
                "app/meeting_prep_pack.py",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_meeting_prep_pack_143p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-requested read-only Meeting Prep Pack baseline. 143P adds /prep <suggestion_id> to the owner-gated Telegram command surface and composes existing 138P meeting suggestions, existing 139P selected suggested brief validation, and existing 136P Memory Center visibility only. It fails closed for unavailable Calendar context or stale suggestion ids, keeps pending memory proposals out of facts, and preserves Telegram sendMessage replies as the only external write. It does not authorize task persistence, follow-up intents, reminders, scheduler, callbacks, buttons, Memory Center mutation, ProposedMemory writes, Calendar writes, model/tool calls, worker dispatch, DeerFlow runtime integration, dependencies, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 144P later added brief-derived pending memory candidates only. 151P later added customer-facing Meeting Prep Pack product flow only. 152P and later remain unauthorized.",
    }
    for path in stages_by_id["143P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_144p_is_brief_memory_proposal_closed_committed_pending_owner_review_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["144P"] == {
        "stage_id": "144P",
        "stage_name": "Brief-Derived Memory Proposal v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_144P_closeout",
            "commit_message": "feat: add brief memory proposals",
            "paths": [
                "docs/reference/BRIEF_MEMORY_PROPOSAL_144P_v0_1.md",
                "app/brief_memory_proposal.py",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_brief_memory_proposal_144p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the brief-derived pending memory proposal baseline. 144P adds deterministic memory candidates to owner-requested /prep replies from the existing 143P Meeting Prep Pack only. Candidates are marked pending owner review and are not treated as facts. It does not authorize approval decisions, Memory Center mutation, ProposedMemory writes, task persistence, follow-up intents, reminders, scheduler, callbacks, buttons, Calendar writes, model/tool calls, worker dispatch, DeerFlow runtime integration, dependencies, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 145P later added explicit owner decision receipts only. 146P and later remain unauthorized.",
    }
    for path in stages_by_id["144P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_145p_is_brief_memory_approval_closed_committed_local_decision_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["145P"] == {
        "stage_id": "145P",
        "stage_name": "Telegram Memory Approval for Brief Proposals v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_145P_closeout",
            "commit_message": "feat: add brief memory approval commands",
            "paths": [
                "docs/reference/BRIEF_MEMORY_APPROVAL_145P_v0_1.md",
                "app/brief_memory_approval.py",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_brief_memory_approval_145p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the owner-requested brief memory decision baseline. 145P adds /memory_approve <candidate_id> and /memory_reject <candidate_id> to create deterministic local decision receipts for 144P candidates only. Approval status remains approved_pending_writeback and does not execute writeback. It does not authorize Memory Center mutation, ProposedMemory writes, task persistence, follow-up intents, reminders, scheduler, callbacks, buttons, Calendar writes, model/tool calls, worker dispatch, DeerFlow runtime integration, dependencies, billing, entitlement enforcement, or external writes beyond approved Telegram replies. 146P later added read-only personal inbox visibility only. 147P and later remain unauthorized.",
    }
    for path in stages_by_id["145P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_148p_is_factory_loop_handoff_harness_closed_committed_non_authority_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["148P"] == {
        "stage_id": "148P",
        "stage_name": "Factory Loop Handoff Harness v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_148P_closeout",
            "commit_message": "feat: add factory loop handoff harness",
            "paths": [
                "docs/reference/ROBOTICXS_LOOP_HANDOFF_TARGET_v0_1.md",
                "app/roboticxs_loop_handoff.py",
                "app/roboticxs_loop_cli.py",
                "tests/test_roboticxs_loop_handoff_target.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local factory loop handoff harness baseline. 148P adds a non-authority local loop target that creates isolated worktrees, runs pytest and Open Loops checks, emits evidence.json, handoff.md, and risk_diff.md, labels output non_authority_candidate, and requires human review for promotion. It does not authorize merge, commit, deploy, live retrieval, external writes, Telegram live sends, Memory Center mutation, provider execution, billing, or secret access. 149P later added local read-only runtime doctor diagnostics only. 150P later added customer-facing Telegram product shell copy only. 151P later added customer-facing Meeting Prep Pack product flow only. 152P and later remain unauthorized.",
    }
    for path in stages_by_id["148P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_149p_runtime_doctor_helper_manager_is_closed_committed_read_only_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["149P"] == {
        "stage_id": "149P",
        "stage_name": "Runtime Doctor / Helper Manager v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_149P_closeout",
            "commit_message": "feat: add runtime doctor helper manager",
            "paths": [
                "docs/reference/RUNTIME_DOCTOR_HELPER_MANAGER_149P_v0_1.md",
                "app/runtime_doctor.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_runtime_doctor_149p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the local read-only Runtime Doctor / Helper Manager baseline. 149P checks runtime config, env presence, .secrets path presence, OAuth JSON shape, Calendar readiness, Gmail readiness, and explicit authority boundaries without printing secrets or activating connectors. It does not authorize OAuth URL generation, token exchange, token refresh, Calendar reads or writes, Gmail reads or writes, Telegram live sends, Memory Center mutation, model/tool calls, worker dispatch, persistence, scheduler, billing, deployment, push, merge, PR creation, or 150P behavior beyond customer-facing Telegram product shell copy.",
    }
    for path in stages_by_id["149P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_150p_telegram_product_shell_is_closed_committed_customer_facing_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["150P"] == {
        "stage_id": "150P",
        "stage_name": "Telegram Product Shell v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_150P_closeout",
            "commit_message": "feat: add telegram product shell",
            "paths": [
                "docs/reference/TELEGRAM_PRODUCT_SHELL_150P_v0_1.md",
                "app/runnable_telegram_robot_mvp.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_telegram_product_shell_150p.py",
                "tests/test_runnable_telegram_robot_mvp_130p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the customer-facing Telegram Product Shell baseline. 150P unifies /start, /help, /status, and unknown-command replies into a product menu with Today, Brief, Prep, Tasks, Memory, and Setup Check areas. It clarifies that /inbox is a robot task inbox, not Gmail, and keeps Checkup/Setup language customer-facing. It does not authorize new commands, connector activation, OAuth generation, OAuth token exchange, Calendar writes, Gmail reads or writes, Memory Center mutation, model/tool calls, worker dispatch, persistence, scheduler, billing, deployment, push, merge, PR creation, or 151P behavior beyond customer-facing Meeting Prep Pack product flow.",
    }
    for path in stages_by_id["150P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_151p_meeting_prep_pack_product_flow_is_closed_committed_customer_facing_only():
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert stages_by_id["151P"] == {
        "stage_id": "151P",
        "stage_name": "Meeting Prep Pack Product Flow v0",
        "status": "CLOSED_COMMITTED",
        "authority_source": "explicit_maintainer_authorization",
        "local_evidence": {
            "commit": "same_commit_as_151P_closeout",
            "commit_message": "feat: improve meeting prep product flow",
            "paths": [
                "docs/reference/MEETING_PREP_PACK_PRODUCT_FLOW_151P_v0_1.md",
                "app/meeting_prep_pack.py",
                "app/hermes_runtime_bootstrap.py",
                "tests/test_meeting_prep_pack_product_flow_151p.py",
                "tests/test_meeting_prep_pack_143p.py",
                "tests/test_hermes_runtime_bootstrap_129p.py",
                "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
                "tests/test_canonical_roadmap.py",
                "tests/test_roadmap_continuation_authorization_gate.py",
            ],
        },
        "implementation_authorized": False,
        "next_action": "Use as the customer-facing Meeting Prep Pack Product Flow baseline. 151P improves /prep output with meeting context, agenda, known memory, open loops, missing inputs, suggested actions, safe next step, and boundaries. It does not authorize new commands, Calendar writes, Gmail reads or writes, Memory Center mutation, ProposedMemory writes, follow-up intents, scheduler, model/tool calls, worker dispatch, persistence, proactive outbound sends, billing, deployment, push, merge, PR creation, or 152P+ behavior.",
    }
    for path in stages_by_id["151P"]["local_evidence"]["paths"]:
        assert (REPO_ROOT / path).is_file()


def test_100p_transition_records_later_101p_102p_103p_104p_105p_106p_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-100p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "100P",
        "stage_name": "Cost Governor / Model Routing Runtime v0",
        "implementation_commit": "same_commit_as_100P_closeout",
        "stage_101p_authorized_later": True,
        "stage_102p_authorized_later": True,
        "stage_102p_current_status": "CLOSED_COMMITTED",
        "stage_103p_authorized_later": True,
        "stage_103p_current_status": "CLOSED_COMMITTED",
        "stage_104p_authorized_later": True,
        "stage_104p_current_status": "CLOSED_COMMITTED",
        "stage_105p_authorized_later": True,
        "stage_105p_current_status": "CLOSED_COMMITTED",
        "stage_106p_authorized_later": True,
        "stage_106p_current_status": "CLOSED_COMMITTED",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": "101P",
        "action_packet_approval_loop_authorized": True,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_sends_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["100P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["101P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["103P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["104P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["105P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_101p_transition_records_later_102p_103p_104p_105p_106p_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-101p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "101P",
        "stage_name": "Action Packet Approval Loop v0",
        "implementation_commit": "f031777e12a7e53b4849f8eb7068b952551e2625",
        "remediation_review_commit": "f031777e12a7e53b4849f8eb7068b952551e2625",
        "stage_102p_authorized_later": True,
        "stage_102p_current_status": "CLOSED_COMMITTED",
        "stage_103p_authorized_later": True,
        "stage_103p_current_status": "CLOSED_COMMITTED",
        "stage_104p_authorized_later": True,
        "stage_104p_current_status": "CLOSED_COMMITTED",
        "stage_105p_authorized_later": True,
        "stage_105p_current_status": "CLOSED_COMMITTED",
        "stage_106p_authorized_later": True,
        "stage_106p_current_status": "CLOSED_COMMITTED",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_sends_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["101P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["102P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["103P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["104P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["105P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_103p_transition_records_later_104p_105p_106p_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-103p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "103P",
        "stage_name": "Async Delegation Completion Inbox v0",
        "implementation_commit": "same_commit_as_103P_closeout",
        "stage_104p_authorized_later": True,
        "stage_104p_current_status": "CLOSED_COMMITTED",
        "stage_105p_authorized_later": True,
        "stage_105p_current_status": "CLOSED_COMMITTED",
        "stage_106p_authorized_later": True,
        "stage_106p_current_status": "CLOSED_COMMITTED",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "async_workers_authorized": False,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_sends_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["103P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["104P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["105P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_104p_transition_records_later_105p_106p_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-104p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "104P",
        "stage_name": "Async Result User Surface v0",
        "implementation_commit": "same_commit_as_104P_closeout",
        "stage_105p_authorized_later": True,
        "stage_105p_current_status": "CLOSED_COMMITTED",
        "stage_106p_authorized_later": True,
        "stage_106p_current_status": "CLOSED_COMMITTED",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "telegram_delivery_authorized": False,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_sends_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["104P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["105P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_105p_transition_records_later_106p_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-105p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "105P",
        "stage_name": "Telegram Async Result Delivery v0",
        "implementation_commit": "same_commit_as_105P_closeout",
        "stage_106p_authorized_later": True,
        "stage_106p_current_status": "CLOSED_COMMITTED",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "telegram_callback_execution_authorized": False,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["105P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_106p_transition_records_later_107p_108p_authorization_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-106p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "106P",
        "stage_name": "Telegram Result Acknowledgement Binding v0",
        "implementation_commit": "same_commit_as_106P_closeout",
        "stage_107p_authorized_later": True,
        "stage_107p_current_status": "CLOSED_COMMITTED",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "telegram_callback_execution_authorized": False,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["106P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_107p_transition_records_108p_closeout_and_keeps_109p_plus_blocked():
    transition = load_json_block("stage-107p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "107P",
        "stage_name": "Follow-up Intent Review Queue v0",
        "implementation_commit": "same_commit_as_107P_closeout",
        "stage_108p_authorized_later": True,
        "stage_108p_current_status": "CLOSED_COMMITTED",
        "stage_109p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_planning_authorized": False,
        "live_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["107P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_108p_transition_keeps_109p_plus_blocked():
    transition = load_json_block("stage-108p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "108P",
        "stage_name": "Follow-up Draft Planner v0",
        "implementation_commit": "same_commit_as_108P_closeout",
        "stage_109p_authorized_later": True,
        "stage_109p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "telegram_display_authorized_later": True,
        "followup_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["108P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_109p_transition_records_later_110p_authorization_and_keeps_111p_plus_blocked():
    transition = load_json_block("stage-109p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "109P",
        "stage_name": "Telegram Follow-up Choice Surface v0",
        "implementation_commit": "same_commit_as_109P_closeout",
        "stage_110p_authorized_later": True,
        "stage_110p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "telegram_choice_surface_authorized": True,
        "injected_local_transport_authorized": True,
        "option_selection_binding_authorized": False,
        "followup_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["109P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_110p_transition_records_later_111p_authorization_and_keeps_112p_plus_blocked():
    transition = load_json_block("stage-110p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "110P",
        "stage_name": "Telegram Follow-up Choice Selection Binding v0",
        "implementation_commit": "same_commit_as_110P_closeout",
        "stage_111p_authorized_later": True,
        "stage_111p_current_status": "CLOSED_COMMITTED",
        "stage_112p_and_later_authorized": False,
        "next_eligible_stage": None,
        "telegram_choice_surface_authorized": True,
        "option_selection_binding_authorized": True,
        "selection_record_authorized": True,
        "selection_response_envelope_authorized": True,
        "followup_execution_authorized": False,
        "async_delegation_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": True,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["110P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["111P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_111p_transition_keeps_112p_plus_blocked():
    transition = load_json_block("stage-111p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "111P",
        "stage_name": "User-Approved Follow-up Delegation v0",
        "implementation_commit": "same_commit_as_111P_closeout",
        "stage_112p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_delegation_registration_authorized": True,
        "async_handle_registration_authorized": True,
        "followup_execution_authorized": False,
        "worker_dispatch_authorized": False,
        "completion_events_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["111P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_112p_transition_keeps_113p_plus_blocked():
    transition = load_json_block("stage-112p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "112P",
        "stage_name": "Controlled Follow-up Execution Skeleton v0",
        "implementation_commit": "same_commit_as_112P_closeout",
        "stage_113p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": True,
        "local_event_candidate_creation_authorized": True,
        "inbox_insertion_authorized": False,
        "async_handle_transition_authorized": False,
        "user_surface_authorized": False,
        "telegram_delivery_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "memory_center_mutation_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["112P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_113p_transition_records_later_114p_authorization_and_keeps_115p_plus_blocked():
    transition = load_json_block("stage-113p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "113P",
        "stage_name": "Follow-up Completion Loop Integration v0",
        "implementation_commit": "same_commit_as_113P_closeout",
        "stage_114p_authorized_later": True,
        "stage_114p_current_status": "CLOSED_COMMITTED",
        "stage_115p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "local_event_candidate_routing_authorized": True,
        "inbox_insertion_authorized": True,
        "user_surface_authorized": True,
        "telegram_delivery_authorized": True,
        "acknowledgement_binding_authorized": False,
        "memory_proposal_authorized": False,
        "memory_center_mutation_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["113P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_114p_transition_records_later_115p_authorization_and_keeps_116p_plus_blocked():
    transition = load_json_block("stage-114p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "114P",
        "stage_name": "Follow-up Result Acknowledgement v0",
        "implementation_commit": "same_commit_as_114P_closeout",
        "stage_115p_authorized_later": True,
        "stage_115p_current_status": "CLOSED_COMMITTED",
        "stage_116p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "acknowledgement_binding_authorized": True,
        "local_acknowledgement_record_authorized": True,
        "lineage_summary_authorized": True,
        "memory_proposal_authorized": False,
        "memory_center_mutation_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["114P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_115p_transition_records_later_116p_authorization_and_keeps_117p_plus_blocked():
    transition = load_json_block("stage-115p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "115P",
        "stage_name": "Memory Proposal from Follow-up Result v0",
        "implementation_commit": "same_commit_as_115P_closeout",
        "stage_116p_authorized_later": True,
        "stage_116p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "pending_user_review_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": False,
        "memory_center_mutation_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["115P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["116P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_116p_transition_records_later_117p_authorization_and_keeps_118p_plus_blocked():
    transition = load_json_block("stage-116p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "116P",
        "stage_name": "Telegram Memory Proposal Approval v0",
        "implementation_commit": "same_commit_as_116P_closeout",
        "stage_117p_authorized_later": True,
        "stage_117p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": True,
        "memory_center_mutation_authorized": True,
        "memory_item_creation_authorized": True,
        "memory_item_update_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["116P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["117P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_117p_transition_records_118p_and_119p_authorization_and_keeps_120p_plus_blocked():
    transition = load_json_block("stage-117p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "117P",
        "stage_name": "Memory Center Writeback v0",
        "implementation_commit": "same_commit_as_117P_closeout",
        "stage_118p_authorized_later": True,
        "stage_118p_current_status": "CLOSED_COMMITTED",
        "stage_119p_authorized_later": True,
        "stage_119p_current_status": "CLOSED_COMMITTED",
        "stage_120p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": True,
        "memory_center_mutation_authorized": True,
        "memory_item_creation_authorized": True,
        "memory_item_update_authorized": False,
        "context_scan_authorized": False,
        "proactive_detection_authorized": False,
        "proactive_suggestion_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["117P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["118P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["119P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_118p_transition_records_119p_authorization_and_keeps_120p_plus_blocked():
    transition = load_json_block("stage-118p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "118P",
        "stage_name": "Context Scan Candidate Source v0",
        "implementation_commit": "same_commit_as_118P_closeout",
        "stage_119p_authorized_later": True,
        "stage_119p_current_status": "CLOSED_COMMITTED",
        "stage_120p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": True,
        "memory_center_mutation_authorized": True,
        "memory_item_creation_authorized": True,
        "memory_item_update_authorized": False,
        "context_scan_candidate_source_authorized": True,
        "context_scan_metadata_registration_authorized": True,
        "live_connector_read_authorized": False,
        "scan_extraction_authorized": False,
        "proactive_detection_authorized": True,
        "proactive_opportunity_candidate_authorized": True,
        "proactive_suggestion_authorized": False,
        "memory_proposal_creation_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["118P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["119P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_119p_transition_records_120p_authorization_and_keeps_121p_plus_blocked():
    transition = load_json_block("stage-119p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "119P",
        "stage_name": "Proactive Opportunity Detection v0",
        "implementation_commit": "same_commit_as_119P_closeout",
        "stage_120p_authorized_later": True,
        "stage_120p_current_status": "CLOSED_COMMITTED",
        "stage_121p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": True,
        "memory_center_mutation_authorized": True,
        "memory_item_creation_authorized": True,
        "memory_item_update_authorized": False,
        "context_scan_candidate_source_authorized": True,
        "context_scan_metadata_registration_authorized": True,
        "proactive_detection_authorized": True,
        "proactive_opportunity_candidate_authorized": True,
        "proactive_detection_run_authorized": True,
        "proactive_suggestion_authorized": True,
        "proactive_telegram_surface_authorized": True,
        "proactive_telegram_delivery_authorized": True,
        "callback_binding_authorized": False,
        "telegram_suggestion_surface_authorized": False,
        "followup_intent_authorized": False,
        "async_delegation_authorized": False,
        "worker_dispatch_authorized": False,
        "execution_authorized": False,
        "live_connector_read_authorized": False,
        "memory_proposal_creation_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["119P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["120P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_120p_transition_records_later_121p_authorization_and_keeps_122p_plus_blocked():
    transition = load_json_block("stage-120p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "120P",
        "stage_name": "Proactive Telegram Suggestion v0",
        "implementation_commit": "same_commit_as_120P_closeout",
        "stage_121p_authorized_later": True,
        "stage_121p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": "121P",
        "followup_execution_authorized": False,
        "memory_proposal_candidate_authorized": True,
        "telegram_approval_surface_authorized": True,
        "memory_approval_binding_authorized": True,
        "memory_center_writeback_authorized": True,
        "memory_center_mutation_authorized": True,
        "memory_item_creation_authorized": True,
        "memory_item_update_authorized": False,
        "context_scan_candidate_source_authorized": True,
        "context_scan_metadata_registration_authorized": True,
        "proactive_detection_authorized": True,
        "proactive_opportunity_candidate_authorized": True,
        "proactive_detection_run_authorized": True,
        "proactive_suggestion_authorized": True,
        "proactive_telegram_surface_authorized": True,
        "proactive_telegram_delivery_authorized": True,
        "callback_binding_authorized": False,
        "telegram_suggestion_surface_authorized": False,
        "followup_intent_authorized": False,
        "async_delegation_authorized": False,
        "worker_dispatch_authorized": False,
        "execution_authorized": False,
        "live_connector_read_authorized": False,
        "memory_proposal_creation_authorized": False,
        "new_followup_intent_authorized": False,
        "new_draft_options_authorized": False,
        "new_delegations_authorized": False,
        "new_executions_authorized": False,
        "new_routes_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "live_hermes_gateway_start_authorized": False,
        "live_cron_authorized": False,
        "connector_activation_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "new_approvals_authorized": False,
        "new_action_packets_authorized": False,
        "billing_or_token_reconciliation_authorized": False,
        "credential_checks_authorized": False,
        "database_migrations_authorized": False,
        "ui_or_endpoints_authorized": False,
        "external_effects_authorized": False,
        "medical_behavior_authorized": False,
        "automatic_caregiver_alerts_authorized": False,
    }
    assert stages_by_id["120P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["121P"]["status"] == "CLOSED_COMMITTED"


def test_121p_transition_records_122p_closeout_and_keeps_124p_plus_blocked():
    transition = load_json_block("stage-121p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "121P",
        "stage_name": "Proactive Suggestion Adapter to Follow-up Loop v0",
        "implementation_commit": "same_commit_as_121P_closeout",
        "stage_122p_authorized_later": True,
        "stage_122p_current_status": "CLOSED_COMMITTED",
        "stage_123p_and_later_authorized": False,
        "next_eligible_stage": None,
        "followup_intent_authorized": True,
        "followup_intent_review_record_authorized": True,
        "proactive_suggestion_adapter_authorized": True,
        "explicit_owner_adapter_authorization_required": True,
        "planner_execution_authorized": False,
        "telegram_choice_surface_authorized": False,
        "selection_binding_authorized": False,
        "async_delegation_authorized": False,
        "worker_dispatch_authorized": False,
        "execution_authorized": False,
        "memory_center_mutation_authorized": False,
        "memory_proposal_creation_authorized": False,
        "telegram_delivery_authorized": False,
        "live_connector_read_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["121P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["122P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_122p_transition_records_123p_closeout_and_keeps_124p_plus_blocked():
    transition = load_json_block("stage-122p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "122P",
        "stage_name": "Proactive Delegation Adapter v0",
        "implementation_commit": "same_commit_as_122P_closeout",
        "stage_123p_authorized_later": True,
        "stage_123p_current_status": "CLOSED_COMMITTED",
        "stage_124p_and_later_authorized": False,
        "next_eligible_stage": None,
        "proactive_delegation_adapter_authorized": True,
        "explicit_owner_delegation_authorization_required": True,
        "existing_111p_authority_reused": True,
        "governed_async_delegation_registration_authorized": True,
        "delegation_packet_registration_authorized": True,
        "delegation_handle_registration_authorized": True,
        "planner_execution_authorized": False,
        "telegram_choice_surface_authorized": False,
        "selection_binding_authorized": False,
        "execution_authorized": False,
        "worker_dispatch_authorized": False,
        "memory_center_mutation_authorized": False,
        "memory_proposal_creation_authorized": False,
        "telegram_delivery_authorized": False,
        "live_connector_read_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_telegram_api_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["122P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["123P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_123p_transition_records_later_124p_through_129p_closeout_and_keeps_130p_plus_blocked():
    transition = load_json_block("stage-123p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "123P",
        "stage_name": "Controlled Proactive Execution Skeleton v0",
        "implementation_commit": "same_commit_as_123P_closeout",
        "stage_124p_authorized_later": True,
        "stage_124p_current_status": "CLOSED_COMMITTED",
        "stage_125p_authorized_later": True,
        "stage_125p_current_status": "CLOSED_COMMITTED",
        "stage_126p_authorized_later": True,
        "stage_126p_current_status": "CLOSED_COMMITTED",
        "stage_127p_authorized_later": True,
        "stage_127p_current_status": "CLOSED_COMMITTED",
        "stage_128p_authorized_later": True,
        "stage_128p_current_status": "CLOSED_COMMITTED",
        "stage_129p_authorized_later": True,
        "stage_129p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "proactive_execution_authorized": True,
        "local_completion_failure_candidate_creation_authorized": True,
        "existing_122p_delegation_lineage_required": True,
        "daily_brief_snapshot_authorized": True,
        "read_only_daily_brief_rendering_authorized": True,
        "inbox_insertion_authorized": False,
        "result_surface_authorized": False,
        "telegram_delivery_authorized": False,
        "worker_dispatch_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_connector_read_authorized": False,
        "memory_center_mutation_authorized": False,
        "memory_proposal_creation_authorized": False,
        "new_action_packets_authorized": False,
        "new_delegations_authorized": False,
        "live_telegram_api_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["123P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["124P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["125P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["126P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["127P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["128P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["129P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_124p_transition_records_later_125p_through_129p_closeout_and_keeps_130p_plus_blocked():
    transition = load_json_block("stage-124p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "124P",
        "stage_name": "What Did I Miss? Daily Brief v0",
        "implementation_commit": "same_commit_as_124P_closeout",
        "stage_125p_authorized_later": True,
        "stage_125p_current_status": "CLOSED_COMMITTED",
        "stage_126p_authorized_later": True,
        "stage_126p_current_status": "CLOSED_COMMITTED",
        "stage_127p_authorized_later": True,
        "stage_127p_current_status": "CLOSED_COMMITTED",
        "stage_128p_authorized_later": True,
        "stage_128p_current_status": "CLOSED_COMMITTED",
        "stage_129p_authorized_later": True,
        "stage_129p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "daily_brief_snapshot_authorized": True,
        "renderable_local_brief_text_authorized": True,
        "read_only_local_aggregation_authorized": True,
        "existing_103p_through_123p_local_records_required": True,
        "skill_pack_activation_surface_authorized": True,
        "telegram_delivery_authorized": False,
        "callback_binding_authorized": False,
        "followup_intent_creation_authorized": False,
        "async_delegation_authorized": False,
        "execution_authorized": False,
        "memory_center_mutation_authorized": False,
        "memory_proposal_creation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_connector_read_authorized": False,
        "external_write_authorized": False,
        "worker_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["124P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["125P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["126P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["127P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["128P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["129P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_125p_transition_records_later_126p_through_129p_closeout_and_keeps_130p_plus_blocked():
    transition = load_json_block("stage-125p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "125P",
        "stage_name": "Skill Pack Activation Surface v0",
        "implementation_commit": "same_commit_as_125P_closeout",
        "stage_126p_authorized_later": True,
        "stage_126p_current_status": "CLOSED_COMMITTED",
        "stage_127p_authorized_later": True,
        "stage_127p_current_status": "CLOSED_COMMITTED",
        "stage_128p_authorized_later": True,
        "stage_128p_current_status": "CLOSED_COMMITTED",
        "stage_129p_authorized_later": True,
        "stage_129p_current_status": "CLOSED_COMMITTED",
        "next_eligible_stage": None,
        "skill_pack_activation_surface_authorized": True,
        "read_only_skill_pack_classification_authorized": True,
        "renderable_local_skill_pack_surface_authorized": True,
        "existing_103p_through_124p_local_records_required": True,
        "billing_authorized": False,
        "entitlement_enforcement_authorized": False,
        "package_activation_authorized": False,
        "upgrade_prompt_authorized": False,
        "telegram_delivery_authorized": False,
        "callback_binding_authorized": False,
        "followup_intent_creation_authorized": False,
        "async_delegation_authorized": False,
        "execution_authorized": False,
        "memory_center_mutation_authorized": False,
        "memory_proposal_creation_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "live_connector_read_authorized": False,
        "external_write_authorized": False,
        "worker_dispatch_authorized": False,
        "live_telegram_api_authorized": False,
        "callbacks_or_webhooks_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["125P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["126P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["127P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["128P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["129P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


def test_129p_transition_records_130p_closeout_and_keeps_131p_plus_blocked():
    transition = load_json_block("stage-129p-implementation-transition")
    stages_by_id = {stage["stage_id"]: stage for stage in load_stage_registry()}

    assert transition == {
        "implementation_status": "CLOSED_COMMITTED",
        "stage": "129P",
        "stage_name": "Hermes Runtime Bootstrap v0",
        "implementation_commit": "same_commit_as_129P_closeout",
        "stage_130p_authorized_later": True,
        "stage_130p_current_status": "CLOSED_COMMITTED",
        "stage_131p_and_later_authorized": False,
        "next_eligible_stage": None,
        "runtime_bootstrap_authorized": True,
        "manual_local_run_authorized": True,
        "deterministic_local_config_required": True,
        "robot_identity_validation_required": True,
        "owner_identity_validation_required": True,
        "module_availability_check_authorized": True,
        "runtime_health_report_authorized": True,
        "telegram_startup_authorized": False,
        "live_connector_read_authorized": False,
        "provider_calls_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "worker_dispatch_authorized": False,
        "memory_center_mutation_authorized": False,
        "billing_authorized": False,
        "entitlement_enforcement_authorized": False,
        "external_write_authorized": False,
        "external_effects_authorized": False,
    }
    assert stages_by_id["129P"]["status"] == "CLOSED_COMMITTED"
    assert stages_by_id["130P"]["status"] == "CLOSED_COMMITTED"
    assert [stage for stage in stages_by_id.values() if stage["status"] == "NEXT_ELIGIBLE"] == []


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
