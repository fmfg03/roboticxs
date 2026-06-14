from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ALIASES_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_CONSUMER_COMMAND_ALIASES_v0_1.md"


def test_consumer_aliases_doc_exists_and_is_reference_only():
    text = ALIASES_DOC.read_text()

    assert ALIASES_DOC.is_file()
    assert "Status: 90P implemented pending review." in text
    for non_claim in [
        "no parser changes",
        "no runtime command registry changes",
        "no Telegram command changes",
        "no gateway changes",
        "no UI",
        "no 92P or later authorization",
    ]:
        assert non_claim in text


def test_aliases_use_roboticxs_language_for_wrapped_hermes_surfaces():
    text = ALIASES_DOC.read_text()

    for alias_row in [
        "| `routines` | `/cron` | `WRAP` |",
        "| `habilidades` | `/skills` | `WRAP` |",
        "| `skill packages` | `/skills`, `/bundles` | `WRAP` |",
        "| `economy` | `/model` | `WRAP` |",
        "| `balanced` | `/model` | `WRAP` |",
        "| `premium` | `/model` | `WRAP` |",
        "| `send approved handoff` | `/handoff` | `WRAP` |",
        "| `mode` | `/personality` | `WRAP` |",
        "| `conversation history` | `/sessions` | `WRAP` |",
        "| `continue conversation` | `/resume` | `WRAP` |",
    ]:
        assert alias_row in text


def test_aliases_define_authority_and_safe_fallback_requirements():
    text = ALIASES_DOC.read_text()

    for required in [
        "map to user intent",
        "name the relevant authority boundary",
        "name the cost policy",
        "produce an audit log",
        "provide a safe fallback",
        "Cost Governor",
        "Model Router",
        "Zaubern-lite Action Packet",
        "Memory Center",
        "SkillManifest package authority",
    ]:
        assert required in text


def test_forbidden_consumer_aliases_do_not_expose_operator_or_bypass_commands():
    text = ALIASES_DOC.read_text()

    for forbidden in [
        "`/yolo`",
        "raw `/config`",
        "raw `/reload`",
        "raw `/reload-mcp`",
        "raw `/plugins`",
        "browser connect controls",
        "raw `/toolsets`",
        "raw `/debug`",
        "raw `/profile`",
        "raw `/platforms`",
        "raw `/gateway`",
        "raw `/codex-runtime`",
        "raw `/branch`",
        "raw `/rollback`",
        "any unverified raw Hermes command",
    ]:
        assert forbidden in text
