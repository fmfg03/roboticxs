from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/DEERFLOW_PATTERN_REVIEW_140P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
BOOTSTRAP_PATH = REPO_ROOT / "app/hermes_runtime_bootstrap.py"

MANDATORY_SECTIONS = [
    "Status",
    "Source Evidence",
    "Runtime Decision",
    "Classification Legend",
    "Pattern Review",
    "Copy / Adapt / Defer / Forbid Summary",
    "Forbidden Scope",
    "Future Reopen Requirements",
    "Closeout",
]
ALLOWED_CLASSIFICATIONS = {"COPY", "ADAPT", "DEFER", "FORBID", "UNKNOWN"}
REQUIRED_CATEGORIES = {
    "skills",
    "subagents",
    "sandbox",
    "im_channels",
    "memory",
}


def doc_text() -> str:
    return DOC_PATH.read_text()


def pattern_rows(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        if "DeerFlow pattern" in line or "---" in line:
            continue
        parts = [part.strip(" `") for part in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        category = parts[0]
        classification = parts[3]
        if category and classification in ALLOWED_CLASSIFICATIONS:
            rows.append((category, classification))
    return rows


def test_140p_deerflow_pattern_review_doc_exists_and_has_mandatory_sections():
    assert DOC_PATH.is_file()
    text = doc_text()

    for section in MANDATORY_SECTIONS:
        assert f"## {section}" in text


def test_140p_classification_table_uses_only_allowed_classifications_and_required_categories():
    rows = pattern_rows(doc_text())

    assert rows
    assert {category for category, _classification in rows} >= REQUIRED_CATEGORIES
    assert {classification for _category, classification in rows} <= ALLOWED_CLASSIFICATIONS
    assert any(classification == "ADAPT" for _category, classification in rows)
    assert any(classification == "DEFER" for _category, classification in rows)
    assert any(classification == "FORBID" for _category, classification in rows)


def test_140p_runtime_decision_keeps_hermes_and_blocks_deerflow_dependency():
    text = doc_text()

    assert "Hermes remains the Roboticxs runtime." in text
    assert "DeerFlow is not a production dependency in 140P." in text
    assert "no DeerFlow dependency or runtime capability is added" in text


def test_140p_forbidden_scope_blocks_runtime_sandbox_memory_model_tool_worker_and_network_expansion():
    text = doc_text()

    for forbidden in [
        "No DeerFlow clone.",
        "No DeerFlow dependency install.",
        "No production dependency change.",
        "No runtime integration.",
        "No Telegram or IM channel replacement.",
        "No owner-gate relaxation.",
        "No sandbox execution.",
        "No filesystem write authority.",
        "No connector config.",
        "No Memory Center mutation.",
        "No ProposedMemory write.",
        "No model call.",
        "No tool call.",
        "No worker dispatch.",
        "No async delegation.",
        "No external network behavior.",
        "No change to Hermes as runtime.",
    ]:
        assert forbidden in text


def test_140p_does_not_add_deerflow_to_runtime_or_dependencies():
    pyproject = PYPROJECT_PATH.read_text().lower()
    bootstrap = BOOTSTRAP_PATH.read_text().lower()

    assert "deer-flow" not in pyproject
    assert "deerflow" not in pyproject
    assert "deer-flow" not in bootstrap
    assert "deerflow" not in bootstrap


def test_140p_roadmap_records_deerflow_pattern_review_and_blocks_141p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"140P","stage_name":"DeerFlow Pattern Review / Sandbox Boundary Spike v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "143P and later remain unauthorized" in roadmap
    assert re.search(r"140P.+docs/test-only", roadmap, re.DOTALL)
