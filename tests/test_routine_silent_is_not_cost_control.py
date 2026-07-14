from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WAKE_GATE_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_ROUTINE_WAKE_GATE_v0_1.md"
COST_POLICY_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_ROUTINE_COST_POLICY_v0_1.md"
SCRIPT_ONLY_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_SCRIPT_ONLY_ROUTINES_v0_1.md"


def test_silent_is_delivery_only_not_cost_control_across_88p_contracts():
    texts = [path.read_text() for path in [WAKE_GATE_PATH, COST_POLICY_PATH, SCRIPT_ONLY_PATH]]

    assert "`[SILENT]` suppresses delivery only. It is not cost control" in texts[0]
    assert "`[SILENT]` suppresses delivery only. It does not prevent agent wake" in texts[1]
    assert "Silent delivery and token usage are separate fields." in texts[1]
    assert "Script errors must not silently fall back to agent wake" in texts[2]


def test_88p_contracts_do_not_authorize_later_runtime_or_89p_scope():
    combined = "\n".join(
        path.read_text() for path in [WAKE_GATE_PATH, COST_POLICY_PATH, SCRIPT_ONLY_PATH]
    )

    for forbidden in [
        "no live Hermes cron execution",
        "no production scheduler",
        "no runtime gateway change",
        "no automation blueprint",
        "no MCP/plugin/connector activation",
        "no Model Router changes",
        "no 89P or later authorization",
    ]:
        assert forbidden in combined
