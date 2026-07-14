from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1.md"
SKILL_ROOT = REPO_ROOT / "runtime/hermes/skills"
BLUEPRINT_PACKAGES = [
    "roboticxs-daily-brief",
    "roboticxs-research-radar",
    "roboticxs-caregiver-routine",
]
REQUIRED_FIELDS = {
    "name",
    "description",
    "package",
    "inputs",
    "schedule_policy",
    "source_authorization",
    "wake_policy",
    "skill_binding",
    "model_budget_policy",
    "delivery_target",
    "authority_boundary",
    "memory_sink_policy",
    "confirmation_behavior",
}


def load_json_block(path: Path, block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_blueprint_contract_defines_required_manifest_fields_and_product_object():
    text = BLUEPRINT_DOC.read_text()
    manifest = load_json_block(BLUEPRINT_DOC, "roboticxs-blueprint-manifest-v0")

    assert "Status: 89P implemented pending review." in text
    assert "The user-facing product object is `Routine`, not `cron job`." in text
    assert "Automation Blueprints are installable routine templates, not silently scheduled jobs." in text
    assert set(manifest) == REQUIRED_FIELDS
    assert manifest["schedule_policy"]["silent_install"] is False
    assert manifest["wake_policy"] == "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE"
    assert manifest["memory_sink_policy"] == "PROPOSED_MEMORY_ONLY_NO_CANONICAL_AUTO_WRITE"


def test_initial_blueprint_skill_packages_exist_and_declare_required_manifest_fields():
    for package in BLUEPRINT_PACKAGES:
        path = SKILL_ROOT / package / "SKILL.md"
        assert path.is_file()
        manifest = load_json_block(path, "roboticxs-blueprint")

        assert set(manifest) == REQUIRED_FIELDS
        assert manifest["package"] == package
        assert manifest["skill_binding"] == package
        assert manifest["inputs"]
        assert manifest["schedule_policy"] == {
            "type": "USER_CONFIGURED",
            "silent_install": False,
        }
        assert manifest["source_authorization"] == "USER_GRANTED_SOURCES_ONLY"
        assert manifest["wake_policy"] == "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE"
        assert manifest["model_budget_policy"] == "REQUIRED_BEFORE_AGENT_WAKE"
        assert manifest["delivery_target"] == "USER_CONFIRMED_TARGET"
        assert (
            manifest["authority_boundary"]
            == "ZAUBERN_LITE_PLUS_HUMAN_CONFIRMATION_FOR_SENSITIVE_ACTIONS"
        )
        assert manifest["memory_sink_policy"] == "PROPOSED_MEMORY_ONLY_NO_CANONICAL_AUTO_WRITE"
        assert manifest["confirmation_behavior"] == "CONFIRM_BEFORE_EXTERNAL_OR_SENSITIVE_EFFECT"


def test_blueprint_docs_preserve_runtime_packaging_and_authority_roles():
    text = BLUEPRINT_DOC.read_text()

    for required in [
        "Hermes remains runtime capability.",
        "Agent Skills remains portable packaging.",
        "Roboticxs SkillManifest remains product/package/scope authority.",
        "Zaubern-lite remains action authority.",
        "Routine remains the user-facing product object.",
        "no live Hermes cron execution",
        "no production scheduler",
        "no gateway changes",
        "no actual MCP/plugin/connector activation",
        "no UI",
        "no 90P or later authorization",
    ]:
        assert required in text
