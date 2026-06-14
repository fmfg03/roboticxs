from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / "docs/research/HERMES_REAL_SETTINGS_BASELINE_v0_1.md"
CONTRACT_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_CONFIG_CONTRACT_v0_1.md"
SOUL_PATH = REPO_ROOT / "runtime/hermes/SOUL.md"
AGENTS_PATH = REPO_ROOT / "runtime/hermes/AGENTS.md"

REJECTED_FAKE_SETTINGS = {
    "MEMORY_BACKEND",
    "SKILLS_WATCH",
    "CONTEXT_PRELOAD",
    "NOTIFICATION_GATEWAY",
    "MEMORY_RETRIEVAL_DEPTH",
    "OUTPUT_PATH",
    "HERMES_MAKE_ME_SMARTER",
}


def read_86p_docs() -> str:
    return "\n".join([BASELINE_PATH.read_text(), CONTRACT_PATH.read_text()])


def test_86p_reference_docs_exist_and_record_verified_upstream_source():
    text = read_86p_docs()

    for path in [BASELINE_PATH, CONTRACT_PATH]:
        assert path.is_file()

    for required in [
        "Stage 86P is closed committed.",
        "https://github.com/NousResearch/hermes-agent",
        "6b76284c7769e0ca80012a5a4b7e22b1cea05b6b",
        "official upstream source",
        "Community posts, planning chat, and screenshots may be used only as discovery inputs.",
        "Every Hermes key, environment variable, command, and profile behavior referenced by a Roboticxs implementation must cite official Hermes docs or source.",
    ]:
        assert required in text


def test_86p_contract_records_real_hermes_config_surfaces_only_as_baseline():
    text = read_86p_docs()

    for required in [
        "`config.yaml` is the primary non-secret user configuration file under `HERMES_HOME`.",
        "`.env` is for secrets such as API keys, tokens, and passwords",
        "`HERMES_HOME` is the profile/home location mechanism used by Hermes source.",
        "`SOUL.md` is profile identity/personality content",
        "`AGENTS.md` is developer/runtime instruction content",
        "`hermes config set` is the documented command for setting individual config values.",
        "`hermes profile` is a documented profile-management command family.",
        "Hermes profiles isolate Hermes state by separate `HERMES_HOME` directories.",
    ]:
        assert required in text


def test_86p_rejects_fake_hermes_settings_by_name():
    text = read_86p_docs()

    assert "## Rejected Fake Settings" in text
    assert "## Rejected Settings" in text

    for fake_setting in REJECTED_FAKE_SETTINGS:
        assert f"- `{fake_setting}`" in text

    for required in [
        "not accepted Roboticxs Hermes configuration keys or environment variables",
        "Do not add them to Roboticxs `.env`, config docs, runtime config models, tests, or product specs as accepted settings.",
        "Do not treat them as aliases for verified Hermes settings.",
        "Do not infer support from community examples, screenshots, or generated packets.",
        "`OUTPUT_PATH` appears in upstream repository maintenance scripts",
        "not a Hermes user/runtime config key",
    ]:
        assert required in text


def test_86p_preserves_roboticxs_authority_and_memory_boundaries():
    text = read_86p_docs()

    for required in [
        "`SOUL.md` remains identity/style only.",
        "`AGENTS.md` and context files remain project/runtime instructions.",
        "`.env` is for secrets.",
        "Config files are for non-secret runtime configuration.",
        "Hermes profiles are state isolation, not business authorization.",
        "Hermes memory is runtime memory, not Roboticxs canonical memory.",
        "Hermes command approval is not Roboticxs business-action authority.",
        "Zaubern-lite remains the authority layer.",
        "Memory Center remains canonical memory.",
        "Cost Governor remains spend and wake authority.",
    ]:
        assert required in text


def test_86p_does_not_pollute_soul_or_agents_with_fake_runtime_settings():
    combined_profile_text = "\n".join([SOUL_PATH.read_text(), AGENTS_PATH.read_text()])

    for fake_setting in REJECTED_FAKE_SETTINGS:
        assert fake_setting not in combined_profile_text


def test_86p_does_not_authorize_runtime_or_87p_behavior():
    text = read_86p_docs()

    for forbidden_claim in [
        "Roboticxs has installed Hermes Agent",
        "full Hermes compatibility",
        "authorize model-router changes",
        "authorize Telegram gateway changes",
        "authorize connectors",
        "authorize 87P",
    ]:
        assert forbidden_claim in text

    assert "87P is authorized" not in text
    assert "NEXT_ELIGIBLE" not in text
