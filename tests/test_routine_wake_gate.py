from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
WAKE_GATE_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_ROUTINE_WAKE_GATE_v0_1.md"
FILE_GATE_PATH = REPO_ROOT / "runtime/hermes/scripts/examples/file_change_gate.py"


def load_json_block(block_name: str, path: Path = WAKE_GATE_PATH):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_wake_gate_document_defines_required_contract_and_vocabulary():
    text = WAKE_GATE_PATH.read_text()

    for required in [
        "Status: 88P implemented pending review.",
        "Scripts detect.",
        "Agents judge.",
        "Zaubern-lite authorizes.",
        "Humans confirm sensitive actions.",
        "`wakeAgent=false` means the LLM should not run and token usage should be zero.",
        "`wakeAgent=true` may pass bounded context to an agent run.",
        "No-agent/script-only routines never invoke Model Router.",
        "`[SILENT]` suppresses delivery only. It is not cost control",
    ]:
        assert required in text

    for decision in [
        "SKIP_NO_CHANGE",
        "SCRIPT_ONLY_ALERT",
        "WAKE_AGENT",
        "BLOCK_BUDGET",
        "ESCALATE_AUTHORITY",
        "SCRIPT_ERROR",
    ]:
        assert decision in text


def test_wake_gate_conceptual_data_model_names_are_present():
    text = WAKE_GATE_PATH.read_text()

    for model_name in [
        "Routine",
        "RoutineRun",
        "RoutinePreflight",
        "WakeDecision",
        "RoutineScript",
        "RoutineSourceFingerprint",
        "RoutineDeliveryTarget",
        "RoutineBudgetPolicy",
        "RoutineAuthorityPolicy",
        "RoutineOutput",
    ]:
        assert f"`{model_name}`" in text


def test_preflight_packet_encodes_zero_token_no_model_route_default():
    packet = load_json_block("routine-preflight-packet-v0")

    assert packet["wakeAgent"] is False
    assert packet["decision"] == "SKIP_NO_CHANGE"
    assert packet["token_expectation"] == 0
    assert packet["model_router_allowed"] is False
    assert packet["bounded_context"] is None


def test_file_change_gate_outputs_skip_no_change_without_agent_wake(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("same", encoding="utf-8")
    digest = subprocess.run(
        [sys.executable, str(FILE_GATE_PATH), str(source)],
        check=True,
        text=True,
        capture_output=True,
    )
    first_packet = json.loads(digest.stdout)

    result = subprocess.run(
        [
            sys.executable,
            str(FILE_GATE_PATH),
            str(source),
            "--previous-sha256",
            first_packet["source_fingerprints"][0]["sha256"],
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    packet = json.loads(result.stdout)

    assert packet["decision"] == "SKIP_NO_CHANGE"
    assert packet["wakeAgent"] is False
    assert packet["token_expectation"] == 0
    assert packet["model_router_allowed"] is False


def test_file_change_gate_errors_are_observable_and_do_not_wake_agent(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(FILE_GATE_PATH), str(tmp_path / "missing.txt")],
        check=True,
        text=True,
        capture_output=True,
    )
    packet = json.loads(result.stdout)

    assert packet["decision"] == "SCRIPT_ERROR"
    assert packet["wakeAgent"] is False
    assert packet["token_expectation"] == 0
    assert packet["model_router_allowed"] is False
    assert packet["observable_error"]["script"] == "file_change_gate.py"
