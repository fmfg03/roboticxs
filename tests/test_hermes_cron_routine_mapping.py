from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CRON_MAPPING_PATH = (
    REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_CRON_ROUTINE_MAPPING_v0_1.md"
)
AUDIT_PATH = (
    REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_CAPABILITY_SURFACE_AUDIT_v0_1.md"
)
RESEARCH_PATH = (
    REPO_ROOT / "docs/research/HERMES_AGENT_SKILLS_CRON_BASELINE_v0_1.md"
)


def test_hermes_cron_maps_to_routine_without_becoming_product_authority():
    text = CRON_MAPPING_PATH.read_text()

    assert "Status: 87P implemented pending review." in text
    assert "Hermes cron schedules work; Roboticxs Routine is the consumer product object." in text
    assert "Hermes cron is a runtime capability." in text
    assert "Instruction text is not authority." in text
    assert "Scheduling is not execution authorization." in text
    assert "Skill references require SkillManifest authority." in text


def test_cron_silent_and_no_agent_boundaries_are_deferred_to_future_stage():
    text = CRON_MAPPING_PATH.read_text()
    audit_text = AUDIT_PATH.read_text()
    research_text = RESEARCH_PATH.read_text()

    for source_text in [text, audit_text, research_text]:
        assert "Cron `[SILENT]` is not cost control." in source_text
        assert "`wakeAgent=false` and no-agent mode belong to 88P, not 87P implementation." in source_text

    assert "`[SILENT]` output prefix" in text
    assert "Suppresses delivery only; it does not prevent model spend or wake activity." in text
    assert "Hermes `no_agent=True`" in audit_text
    assert "Deferred to 88P+. Not implemented in 87P." in audit_text


def test_cron_mapping_requires_zaubern_confirmation_and_cost_governor():
    text = CRON_MAPPING_PATH.read_text()
    audit_text = AUDIT_PATH.read_text()

    assert "Zaubern-lite authority." in text
    assert "User confirmation for send/update/publish/payment/destructive actions." in text
    assert "Cost Governor spend/wake authorization." in text
    assert "Memory Center policy before any canonical memory write." in text
    assert (
        "No external send/update/publish/payment/destructive action may be implied "
        "without Zaubern-lite authority and user confirmation."
    ) in audit_text


def test_87p_forbids_runtime_cron_gateway_plugin_and_88p_scope():
    text = CRON_MAPPING_PATH.read_text()
    audit_text = AUDIT_PATH.read_text()
    research_text = RESEARCH_PATH.read_text()

    for forbidden_scope in [
        "running Hermes cron",
        "creating Hermes cron jobs",
        "changing gateways or delivery paths",
        "activating MCP servers, plugins, connectors, or online skill hubs",
        "implementing blueprints",
        "implementing wake gates",
        "implementing `wakeAgent=false`",
        "implementing Hermes `no_agent=True`",
        "authorizing 88P+",
    ]:
        assert forbidden_scope in text

    for non_implementation in [
        "Hermes cron execution",
        "runtime gateway changes",
        "MCP/plugin activation",
        "wake-gate execution",
        "88P+",
    ]:
        assert non_implementation in audit_text

    assert "Hermes cron has been executed by Roboticxs." in research_text
    assert "88P or any later stage is authorized." in research_text
