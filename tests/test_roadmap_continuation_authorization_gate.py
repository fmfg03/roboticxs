from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ROADMAP_CONTINUATION_AUTHORIZATION_GATE_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

MANDATORY_SECTIONS = [
    "Status",
    "Decision",
    "Why this gate exists",
    "Current roadmap terminal state",
    "No authorized next stage rule",
    "Candidate stage representation",
    "Required human authorization",
    "Blocked automatic promotions",
    "Research parking-lot boundary",
    "Commit authority boundary",
    "Allowed outputs",
    "Forbidden outputs",
    "RoadmapContinuationPacket schema",
    "Candidate next-stage examples",
    "How a future stage becomes NEXT_ELIGIBLE",
    "Non-claims",
]

REQUIRED_DECISION_LINES = [
    "77P is a roadmap continuation authorization gate.",
    "It does not authorize a product feature.",
    "It does not authorize runtime changes.",
    "It does not authorize connector changes.",
    "It does not authorize retrieval changes.",
    "It does not authorize memory changes.",
    "It does not authorize model-router changes.",
    "It does not authorize user-facing commands.",
    "It does not authorize staging.",
    "It does not authorize commit.",
    "It does not create 78P as NEXT_ELIGIBLE.",
    "No next implementation stage is authorized until a maintainer explicitly chooses one.",
]

DEPENDENCY_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
]


def load_json_block(block_name: str, path: Path = ROADMAP_PATH):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path} must contain {block_name}."
    return json.loads(match.group("payload"))


def changed_files_under(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_continuation_gate_document_exists_and_contains_mandatory_sections():
    assert DOC_PATH.is_file()
    text = DOC_PATH.read_text()

    for section in MANDATORY_SECTIONS:
        assert f"## {section}" in text


def test_required_decision_text_is_present_verbatim():
    text = DOC_PATH.read_text()

    for line in REQUIRED_DECISION_LINES:
        assert line in text


def test_roadmap_continuation_packet_schema_is_docs_only_and_blocks_promotions():
    text = DOC_PATH.read_text()

    assert "RoadmapContinuationPacket" in text
    assert '"packet_type": "RoadmapContinuationPacket"' in text
    assert '"status": "NON_RUNTIME_GOVERNANCE_PACKET"' in text
    assert '"current_terminal_stage": "76P"' in text
    assert '"current_terminal_commit": "3a03d6c"' in text
    assert '"next_stage_authorized": false' in text
    assert '"authorized_next_stage": null' in text
    assert '"candidate_status": "CANDIDATE_ONLY"' in text
    assert '"research_parking_lot_to_runtime"' in text
    assert '"candidate_to_next_eligible"' in text
    assert '"conversation_context_to_canon"' in text
    assert '"validation_pass_to_commit_authority"' in text
    assert '"commit_authority": false' in text
    assert "This schema is documentation-only in 77P. It does not add runtime models." in text


def test_candidate_examples_are_candidate_only_and_not_authorization():
    text = DOC_PATH.read_text()

    for candidate in [
        "78P - Next Roadmap Block Selected by Maintainer",
        "Voice Provider Boundary Spec",
        "External Reach Adapter Boundary Spec",
        "Research Parking Lot Index",
        "Factory Methodology Guard Hardening",
        "Artifacts Hygiene Policy",
        "Caregiver Safety Runtime Expansion",
        "Roboticxs Launch MVP Consolidation",
    ]:
        assert candidate in text
    assert text.count("CANDIDATE_ONLY") >= 8
    assert "Listing candidates does not authorize them." in text
    assert "Candidate listing does not authorize implementation." in text


def test_hard_boundaries_block_runtime_dependency_connector_and_command_changes():
    text = DOC_PATH.read_text()

    for boundary in [
        "No runtime code changes.",
        "No app behavior changes.",
        "No new product capability.",
        "No dependency changes.",
        "No connector config.",
        "No retrieval config.",
        "No memory writes.",
        "No `ProposedMemory` writes.",
        "No model-router changes.",
        "No Telegram changes.",
        "No API changes.",
        "No background jobs.",
        "No MCP/tool config.",
        "No external network behavior.",
        "No automatic 78P.",
        "No staging authority.",
        "No commit authority.",
    ]:
        assert boundary in text


def test_roadmap_preserves_77p_gate_and_records_later_authorized_stages():
    roadmap_text = ROADMAP_PATH.read_text()
    stages = load_json_block("canonical-stage-registry")
    stages_by_id = {stage["stage_id"]: stage for stage in stages}
    next_eligible = [stage for stage in stages if stage["status"] == "NEXT_ELIGIBLE"]

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
    assert next_eligible == []
    assert (
        '"stage_id":"78P","stage_name":"Hermes Runtime Foundation Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"'
        in roadmap_text
    )
    assert (
        '"stage_id":"79P","stage_name":"Telegram Bot Runtime Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"'
        in roadmap_text
    )
    assert (
        '"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE"'
        in roadmap_text
    )
    assert (
        '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"'
        in roadmap_text
    )
    assert (
        '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"'
        in roadmap_text
    )
    assert (
        '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"87P","stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"88P","stage_name":"Routine Wake Gate / Zero-Token Preflight v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert '"after_commit_next_eligible":"87P"' in roadmap_text
    assert '"after_commit_next_eligible":"88P"' in roadmap_text
    assert '"after_commit_next_eligible":"89P"' in roadmap_text
    assert '"stage_id":"89P","stage_name":"Roboticxs Automation Blueprints v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"after_commit_next_eligible":"90P"' in roadmap_text
    assert '"stage_id":"90P","stage_name":"Roboticxs Command Surface Policy v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"after_commit_next_eligible":"91P"' in roadmap_text
    assert '"stage_id":"91P","stage_name":"Skill Activation Scope Guard v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"after_commit_next_eligible":"92P"' in roadmap_text
    assert (
        '"stage_id":"92P","stage_name":"Hermes Tool Authority Guard v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert "stage-92p-closeout-transition" in roadmap_text
    assert '"after_commit_next_eligible":"94P"' in roadmap_text
    assert '"next_eligible_stage_name":"Telegram MVP on Hermes Gateway v0"' in roadmap_text
    assert '"stage_95p_and_later_authorized":false' in roadmap_text
    assert '"stage_id":"93P","stage_name":"Roboticxs Memory Center Bridge v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"94P","stage_name":"Telegram MVP on Hermes Gateway v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert (
        '"stage_id":"100P","stage_name":"Cost Governor / Model Routing Runtime v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert '"stage_id":"101P","stage_name":"Action Packet Approval Loop v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"102P","stage_name":"Hermes Async Delegation Authority Adapter v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"103P","stage_name":"Async Delegation Completion Inbox v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"104P","stage_name":"Async Result User Surface v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"105P","stage_name":"Telegram Async Result Delivery v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"106P","stage_name":"Telegram Result Acknowledgement Binding v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"107P","stage_name":"Follow-up Intent Review Queue v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"108P","stage_name":"Follow-up Draft Planner v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"109P","stage_name":"Telegram Follow-up Choice Surface v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"110P","stage_name":"Telegram Follow-up Choice Selection Binding v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"111P","stage_name":"User-Approved Follow-up Delegation v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"112P","stage_name":"Controlled Follow-up Execution Skeleton v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"113P","stage_name":"Follow-up Completion Loop Integration v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"114P","stage_name":"Follow-up Result Acknowledgement v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"115P","stage_name":"Memory Proposal from Follow-up Result v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"124P","stage_name":"What Did I Miss? Daily Brief v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"125P","stage_name":"Skill Pack Activation Surface v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"126P","stage_name":"First Demo Flow: Meeting Brief from Context v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"127P","stage_name":"Demo Result Delivery Surface v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"128P","stage_name":"Document Review Demo Flow v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"129P","stage_name":"Hermes Runtime Bootstrap v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"130P","stage_name":"Runnable Telegram Robot MVP v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"131P","stage_name":"Telegram What Did I Miss Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"132P","stage_name":"Telegram Meeting Brief Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"133P","stage_name":"Read-Only Google Calendar Connector v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"134P","stage_name":"Calendar-backed Telegram Meeting Brief v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"135P","stage_name":"Real Calendar Meeting Brief Composer v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"136P","stage_name":"Memory Center Telegram Commands v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"137P","stage_name":"Context Scan from Calendar v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"138P","stage_name":"Proactive Meeting Suggestion v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert (
        '"stage_id":"139P","stage_name":"Owner-Requested Suggested Meeting Brief v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert (
        '"stage_id":"140P","stage_name":"DeerFlow Pattern Review / Sandbox Boundary Spike v0","status":"CLOSED_COMMITTED"'
        in roadmap_text
    )
    assert '"stage_id":"141P","stage_name":"Today Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"142P","stage_name":"Open Loops Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"143P","stage_name":"Meeting Prep Pack v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"144P","stage_name":"Brief-Derived Memory Proposal v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"145P","stage_name":"Telegram Memory Approval for Brief Proposals v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"146P","stage_name":"Personal Admin Inbox v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"147P","stage_name":"Inbox Resolve / Dismiss v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"148P","stage_name":"Factory Loop Handoff Harness v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"149P","stage_name":"Runtime Doctor / Helper Manager v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"150P","stage_name":"Telegram Product Shell v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"151P","stage_name":"Meeting Prep Pack Product Flow v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"152P","stage_name":"Today / Brief Product Flow v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"153P","stage_name":"Setup & Capability Status v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"154P","stage_name":"Task Inbox Flow v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"155P","stage_name":"Memory Review Flow v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"156P","stage_name":"First-Run Onboarding v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"157P","stage_name":"Telegram Demo Loop v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"158P","stage_name":"Telegram Document Intake Stub v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"159P","stage_name":"Telegram Product Copy Consolidation v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"160P","stage_name":"Customer MVP Baseline v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"161P","stage_name":"Setup Capability Status Component v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"162P","stage_name":"Calendar-Backed Today / Prep v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert '"stage_id":"163P","stage_name":"Gmail Read-Only Context Scan v0","status":"CLOSED_COMMITTED"' in roadmap_text
    assert "207P and later remain unauthorized" in roadmap_text
    assert '"status":"NEXT_ELIGIBLE"' not in roadmap_text


def test_no_runtime_app_files_were_modified_for_77p():
    stages = load_json_block("canonical-stage-registry")
    stage_77p = {stage["stage_id"]: stage for stage in stages}["77P"]

    assert all(not path.startswith("app/") for path in stage_77p["local_evidence"]["paths"])


def test_no_dependency_files_were_modified_or_new_packages_added():
    changed = changed_files_under(*DEPENDENCY_FILES)

    assert changed == []


def test_no_connector_or_mcp_config_was_added_for_new_capability():
    changed = changed_files_under(".codex", ".codex-plugin", ".github", "docs", "tests")
    connector_or_mcp_changes = [
        path
        for path in changed
        if ("mcp" in path.lower() or "connector" in path.lower())
        and "ROADMAP_CONTINUATION_AUTHORIZATION_GATE" not in path
        and "test_roadmap_continuation_authorization_gate" not in path
        and "LIVE_CONNECTOR_READINESS_CHECK_181P" not in path
        and "test_live_connector_readiness_check_181p" not in path
        and "CALENDAR_CONTEXT_BINDING_V1_182P" not in path
        and "test_calendar_context_binding_v1_182p" not in path
    ]

    assert connector_or_mcp_changes == []


def test_no_user_facing_command_strings_were_added():
    command_surface_files = [
        REPO_ROOT / "app/command_registry.py",
        REPO_ROOT / "app/orchestrator.py",
        REPO_ROOT / "app/telegram_adapter.py",
        REPO_ROOT / "app/main.py",
    ]

    for path in command_surface_files:
        text = path.read_text().lower()
        assert "roadmap continuation" not in text, path
        assert "roadmapcontinuationpacket" not in text, path
        assert "77p" not in text, path
