from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1.md"
INSTALL_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_BLUEPRINT_INSTALLATION_CONTRACT_v0_1.md"
SKILL_ROOT = REPO_ROOT / "runtime/hermes/skills"
BLUEPRINT_PACKAGES = [
    "roboticxs-daily-brief",
    "roboticxs-research-radar",
    "roboticxs-caregiver-routine",
]


def test_installation_contract_requires_user_review_and_no_silent_schedule():
    text = INSTALL_DOC.read_text()

    for required in [
        "Installing a blueprint means preparing a draft `Routine` template for user review.",
        "Installing a blueprint does not schedule the routine.",
        "Installing a blueprint does not activate Agent Skills, MCP servers, plugins, connectors, gateways, cron jobs, or external delivery.",
        "Installing a blueprint does not grant source authorization, model budget authorization, delivery authorization, memory-write authorization, or external-action authorization.",
        "`AVAILABLE_TEMPLATE`",
        "`DRAFT_ROUTINE`",
        "`PENDING_USER_CONFIGURATION`",
        "`READY_FOR_REVIEW`",
        "`INSTALLED_NOT_SCHEDULED`",
    ]:
        assert required in text


def test_no_89p_blueprint_claims_live_scheduler_gateway_mcp_plugin_or_ui():
    combined = "\n".join(
        [BLUEPRINT_DOC.read_text(), INSTALL_DOC.read_text()]
        + [(SKILL_ROOT / package / "SKILL.md").read_text() for package in BLUEPRINT_PACKAGES]
    )

    for forbidden_claim in [
        "no live Hermes cron execution",
        "no production scheduler",
        "no gateway changes",
        "no actual MCP/plugin/connector activation",
        "no UI",
        "no silent schedule",
        "Not installed, not scheduled, not activated.",
    ]:
        assert forbidden_claim in combined


def test_blueprint_skill_templates_do_not_use_cron_as_product_object():
    for package in BLUEPRINT_PACKAGES:
        text = (SKILL_ROOT / package / "SKILL.md").read_text()

        assert "The user-facing product object is `Routine`, not `cron job`." in text
        assert "This blueprint is an installable routine template, not a silently scheduled job." in text
        assert '"silent_install": false' in text
        assert "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE" in text
