from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = (
    REPO_ROOT
    / "docs/reference/ROBOTICXS_SKILL_MANIFEST_TO_AGENT_SKILLS_BRIDGE_v0_1.md"
)
AUDIT_PATH = (
    REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_CAPABILITY_SURFACE_AUDIT_v0_1.md"
)
RESEARCH_PATH = (
    REPO_ROOT / "docs/research/HERMES_AGENT_SKILLS_CRON_BASELINE_v0_1.md"
)
SKILL_MANIFEST_SCHEMA_PATH = REPO_ROOT / "docs/SKILL_MANIFEST_SCHEMA_v0_1.json"


def test_agent_skills_bridge_preserves_skill_manifest_authority():
    text = BRIDGE_PATH.read_text()

    assert "Status: 87P implemented pending review." in text
    assert (
        "Roboticxs SkillManifest remains canonical for package, scope, plan, "
        "confirmation, blocked actions, and upgrade path."
    ) in text
    assert "Agent Skills packages instructions and resources; it does not enforce authority." in text
    assert "Hermes is runtime capability, not Roboticxs product." in text

    for required_surface in [
        "`package`",
        "`scope_decisions`",
        "plan/decision policy",
        "`confirmation_required`",
        "`blocked_topics` and `blocked_action_classes`",
        "`upgrade_paths`",
    ]:
        assert required_surface in text


def test_agent_skills_bridge_rejects_authority_transfer_and_runtime_activation():
    text = BRIDGE_PATH.read_text()

    required_boundaries = [
        "Agent Skills do not replace Roboticxs SkillManifest.",
        "Agent Skills do not enforce authority.",
        "Agent Skills do not grant external action permission.",
        "Agent Skills do not bypass Zaubern-lite.",
        "Agent Skills do not become canonical memory.",
        "Agent Skills do not authorize 88P+.",
        "No connector, MCP, plugin, or external tool activation is authorized in 87P.",
    ]
    for boundary in required_boundaries:
        assert boundary in text

    forbidden_claims = [
        "Agent Skills replace Roboticxs SkillManifest",
        "Agent Skills enforce authority",
        "Agent Skills grant external action permission",
        "MCP activation is implemented",
        "plugin activation is implemented",
    ]
    for forbidden_claim in forbidden_claims:
        assert forbidden_claim not in text


def test_skill_manifest_schema_still_contains_canonical_authority_fields():
    schema = json.loads(SKILL_MANIFEST_SCHEMA_PATH.read_text())
    properties = schema["properties"]

    for field in [
        "package",
        "blocked_topics",
        "confirmation_required",
        "blocked_action_classes",
        "scope_decisions",
        "upgrade_paths",
    ]:
        assert field in properties


def test_agent_skills_research_and_audit_are_source_backed_and_non_runtime():
    research_text = RESEARCH_PATH.read_text()
    audit_text = AUDIT_PATH.read_text()

    assert "Commit: `6b76284c7769e0ca80012a5a4b7e22b1cea05b6b`" in research_text
    for official_source_path in [
        "`agent/skill_commands.py`",
        "`cron/jobs.py`",
        "`cron/scheduler.py`",
        "`cronjob`",
        "`skills_hub`",
    ]:
        assert official_source_path in research_text or official_source_path in audit_text

    for non_claim in [
        "Agent Skills have been exported, installed, or loaded by Roboticxs.",
        "MCP, plugins, external registries, or online skill hubs have been activated.",
        "88P or any later stage is authorized.",
    ]:
        assert non_claim in research_text
