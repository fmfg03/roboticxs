from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_RAW_COMMAND_BLOCKLIST_v0_1.md"


def test_blocklist_doc_exists_and_defaults_unknown_raw_commands_to_blocked():
    text = BLOCKLIST_DOC.read_text()

    assert BLOCKLIST_DOC.is_file()
    assert "Status: 90P implemented pending review." in text
    assert "Any raw Hermes command not explicitly mapped by the 90P command surface policy defaults to `UNKNOWN_UNVERIFIED`" in text
    assert "Unknown is blocked" in text


def test_yolo_and_dangerous_bypasses_are_never_consumer_visible():
    text = BLOCKLIST_DOC.read_text()

    for blocked in [
        "| `/yolo` | `BLOCK_CONSUMER` |",
        "| Dangerous command approvals without Action Packet | `BLOCK_CONSUMER` |",
        "| Arbitrary tool enable/disable | `BLOCK_CONSUMER` |",
        "| Arbitrary MCP reload | `BLOCK_CONSUMER` |",
        "| Unrestricted model/provider switching | `BLOCK_CONSUMER` |",
        "| Direct external platform handoff | `BLOCK_CONSUMER` |",
        "| Any unverified raw Hermes command | `BLOCK_CONSUMER` |",
    ]:
        assert blocked in text


def test_operator_only_commands_are_not_consumer_visible():
    text = BLOCKLIST_DOC.read_text()

    for command in [
        "`/config`",
        "`/reload`",
        "`/reload-mcp`",
        "`/plugins`",
        "browser connect controls",
        "`/toolsets`",
        "`/debug`",
        "`/profile`",
        "`/platforms`",
        "`/gateway`",
        "`/codex-runtime`",
        "`/branch`",
        "`/rollback`",
    ]:
        assert command in text

    assert "These raw commands and controls are not consumer-visible." in text


def test_blocklist_is_reference_only_not_runtime_enforcement():
    text = BLOCKLIST_DOC.read_text()

    for non_claim in [
        "no gateway interception",
        "no command parser changes",
        "no live enforcement",
        "no plugin or MCP activation",
        "no model-provider switching implementation",
        "no UI",
        "no 91P or later authorization",
    ]:
        assert non_claim in text
