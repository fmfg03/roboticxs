from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ONLY_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_SCRIPT_ONLY_ROUTINES_v0_1.md"
FLAG_GATE_PATH = REPO_ROOT / "runtime/hermes/scripts/examples/external_flag_gate.py"


def test_script_only_contract_forbids_model_routing_and_sensitive_effects():
    text = SCRIPT_ONLY_PATH.read_text()

    for required in [
        "No-agent/script-only routines never invoke Model Router.",
        "No-agent/script-only routines set `wakeAgent=false`.",
        "No-agent/script-only routines should have zero token usage.",
        "Scripts must not execute sensitive actions.",
        "Scripts must not write directly to canonical Roboticxs Memory Center.",
        "Hermes memory remains runtime memory, not canonical Roboticxs memory.",
    ]:
        assert required in text

    for forbidden in [
        "no direct canonical Memory Center writes",
        "no `ProposedMemory` writes",
        "no sensitive external action",
        "no model routing",
        "no LLM/provider call",
        "no connector or MCP activation",
        "no plugin activation",
        "no 89P or later authorization",
    ]:
        assert forbidden in text


def test_external_flag_script_only_alert_never_wakes_agent():
    result = subprocess.run(
        [
            sys.executable,
            str(FLAG_GATE_PATH),
            "invoice_ready",
            "true",
            "--previous-value",
            "false",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    packet = json.loads(result.stdout)

    assert packet["decision"] == "SCRIPT_ONLY_ALERT"
    assert packet["wakeAgent"] is False
    assert packet["token_expectation"] == 0
    assert packet["model_router_allowed"] is False
    assert packet["bounded_context"] is None
    assert packet["script_only_alert"] == {"flag_name": "invoice_ready", "value": "true"}
