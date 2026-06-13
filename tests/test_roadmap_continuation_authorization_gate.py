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


def test_roadmap_marks_77p_complete_and_does_not_authorize_78p():
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
    assert '"stage_id":"78P"' not in roadmap_text
    assert '"stage_id":"78P","stage_name"' not in roadmap_text
    assert '"status":"NEXT_ELIGIBLE"' not in roadmap_text
    assert '"after_commit_next_eligible":null' in roadmap_text
    assert "No next implementation stage is authorized until a maintainer explicitly chooses one." in roadmap_text


def test_no_runtime_app_files_were_modified_for_77p():
    assert changed_files_under("app") == []


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
