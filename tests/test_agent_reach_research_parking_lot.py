from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/research/AGENT_REACH_RESEARCH_PARKING_LOT_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

MANDATORY_SECTIONS = [
    "Status",
    "Decision",
    "Why this exists",
    "What Agent-Reach appears to provide",
    "Potential Roboticxs value",
    "Hard boundaries",
    "Blocked for now",
    "Risk register",
    "Authority implications",
    "Privacy implications",
    "Budget implications",
    "Connector implications",
    "Memory implications",
    "Retrieval implications",
    "Future adapter requirements",
    "Open questions",
    "Recommended next stage",
    "Non-claims",
]

VALUE_AREAS = [
    "Web/source reach for research tasks.",
    "Social/media monitoring.",
    "YouTube transcript extraction.",
    "GitHub/repo discovery.",
    "External source reading for future Research Radar.",
    "Competitive intelligence.",
    "Prospect/company research.",
    "Future Agentius/Zaubern research workflows.",
]

REQUIRED_RISKS = [
    ("Terms-of-service risk", "Must be reviewed before integration"),
    ("Cookie/credential risk", "Blocked until credential boundary exists"),
    ("Privacy risk", "Requires user consent and source allowlists"),
    ("Budget risk", "Requires cost/usage governor"),
    ("Retrieval contamination", "Must not write to retrieval automatically"),
    ("Memory contamination", "Must not create memories automatically"),
    ("Source reliability", "Must label source confidence"),
    ("Scraping fragility", "Must be treated as unstable"),
    ("Platform blocking", "Must be expected"),
    ("Compliance ambiguity", "Requires review per platform/source"),
    ("Runtime blast radius", "Must be adapter-isolated"),
    ("User misunderstanding", 'UX must say "research source access," not "truth"'),
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


def test_research_note_exists_and_contains_mandatory_sections():
    text = DOC_PATH.read_text()

    assert DOC_PATH.is_file()
    for section in MANDATORY_SECTIONS:
        assert f"## {section}" in text


def test_research_only_decision_is_explicit():
    text = DOC_PATH.read_text()

    assert "Agent-Reach is parked as RESEARCH_ONLY." in text
    assert "It is not approved as a Roboticxs runtime dependency." in text
    assert "It is not approved as a connector." in text
    assert "It is not approved for live retrieval." in text
    assert "It is not approved for memory ingestion." in text
    assert "It is not approved for automatic source scanning." in text


def test_candidate_value_areas_remain_candidate_only():
    text = DOC_PATH.read_text()

    for value_area in VALUE_AREAS:
        assert value_area in text
    assert text.count("Status: CANDIDATE_ONLY") >= len(VALUE_AREAS)
    assert text.count("Requires: future adapter + authority policy + budget policy + privacy review") >= len(
        VALUE_AREAS
    )


def test_hard_boundaries_are_preserved():
    text = DOC_PATH.read_text()

    for required in [
        "No runtime integration.",
        "No network calls.",
        "No connector registration.",
        "No MCP server registration.",
        "No scraping capability.",
        "No credential/cookie handling.",
        "No memory writes.",
        "No ProposedMemory writes.",
        "No retrieval index writes.",
        "No background monitoring.",
        "No user-facing commands.",
        "No automatic roadmap promotion.",
        "No claims that Roboticxs supports Agent-Reach.",
    ]:
        assert required in text


def test_risk_register_contains_required_treatments():
    text = DOC_PATH.read_text()

    assert "## Risk register" in text
    for risk, treatment in REQUIRED_RISKS:
        assert risk in text
        assert treatment in text


def test_implications_and_future_adapter_requirements_are_present():
    text = DOC_PATH.read_text()

    for required in [
        "explicit user consent",
        "source allowlists",
        "budget limits",
        "Agent-Reach is not approved as a connector.",
        "Agent-Reach is not approved for memory ingestion.",
        "No live retrieval is enabled.",
        "explicit story and technical spec approval",
        "source traceability and audit logs",
        "no memory or retrieval writes without separate approval",
    ]:
        assert required in text


def test_authority_model_blocks_write_and_action_operations():
    text = DOC_PATH.read_text()

    for operation in [
        "READ_SOURCE",
        "SEARCH_SOURCE",
        "EXTRACT_SOURCE",
        "SUMMARIZE_SOURCE",
        "PROPOSE_MEMORY",
        "PROPOSE_ACTION",
        "WRITE_EXTERNAL",
        "PUBLISH_EXTERNAL",
    ]:
        assert operation in text
    assert "Only `READ_SOURCE`, `SEARCH_SOURCE`, `EXTRACT_SOURCE`, and `SUMMARIZE_SOURCE` are candidates" in text
    assert "`PROPOSE_MEMORY`, `PROPOSE_ACTION`, `WRITE_EXTERNAL`, and `PUBLISH_EXTERNAL` remain blocked" in text


def test_no_agent_reach_import_or_runtime_dependency_under_app():
    for path in (REPO_ROOT / "app").rglob("*.py"):
        text = path.read_text()
        normalized = text.lower().replace("_", "-")
        assert "agent-reach" not in normalized, path


def test_dependency_files_do_not_include_agent_reach():
    for relative in DEPENDENCY_FILES:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        normalized = path.read_text().lower().replace("_", "-")
        assert "agent-reach" not in normalized, path


def test_no_agent_reach_mcp_config_was_added():
    for path in REPO_ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        normalized_name = path.name.lower().replace("_", "-")
        normalized_path = path.relative_to(REPO_ROOT).as_posix().lower().replace("_", "-")
        assert not ("agent-reach" in normalized_path and "mcp" in normalized_name), path


def test_no_user_facing_agent_reach_command_was_added():
    command_surface_files = [
        REPO_ROOT / "app/command_registry.py",
        REPO_ROOT / "app/orchestrator.py",
        REPO_ROOT / "app/telegram_adapter.py",
        REPO_ROOT / "app/main.py",
    ]

    for path in command_surface_files:
        text = path.read_text().lower().replace("_", "-")
        assert "agent-reach" not in text, path


def test_roadmap_marks_75p_complete_and_76p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"75P","stage_name":"Agent-Reach Research Parking Lot","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/research/AGENT_REACH_RESEARCH_PARKING_LOT_v0_1.md"' in text
    assert '"tests/test_agent_reach_research_parking_lot.py"' in text
    assert '"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"after_commit_next_eligible":"76P"' in text
