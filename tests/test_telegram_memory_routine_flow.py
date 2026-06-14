from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_TELEGRAM_MEMORY_ROUTINE_FLOW_v0_1.md"


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(DOC_PATH.read_text())
    assert match is not None, f"{DOC_PATH} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_telegram_memory_routine_flow_preserves_memory_projection_boundary():
    text = DOC_PATH.read_text()

    assert "Status: 94P implemented pending review." in text
    for required in [
        "Memory context may personalize, constrain, or enforce boundaries, but it must not authorize tools, external actions, spend, wake decisions, or permission expansion.",
        "Read candidate memory only from Roboticxs Memory Center.",
        "Apply 93P MemoryProjectionPolicy",
        "Build a bounded MemoryContextBlock with non-authority metadata.",
        "Do not write canonical memory from Hermes runtime output.",
        "Treat runtime memory suggestions as ProposedMemory candidates for later explicit review only when an approved future path exists.",
    ]:
        assert required in text


def test_telegram_memory_routine_flow_preserves_routine_wake_gate():
    text = DOC_PATH.read_text()

    for required in [
        "Treat Telegram routine messages as Roboticxs Routine intents, not raw Hermes cron commands.",
        "Apply 90P Command Surface Policy to block raw `/cron` exposure as consumer UX.",
        "Apply 89P Automation Blueprint boundaries for installable templates.",
        "Apply 88P Routine Wake Gate before agent wake.",
        "Keep script-only/no-agent routines from invoking Model Router.",
        "Keep `wakeAgent=false` at zero token expectation.",
        "Require budget authority before any agent wake.",
        "Require Tool Authority Guard and Action Packet confirmation before any external routine delivery or sensitive effect.",
    ]:
        assert required in text


def test_telegram_memory_routine_flow_packet_blocks_runtime_sync_and_delivery():
    packet = load_json_block("telegram-memory-routine-flow")

    assert packet == {
        "packet_type": "TelegramMemoryRoutineFlow",
        "status": "NON_RUNTIME_GOVERNANCE_PACKET",
        "stage": "94P",
        "channel": "Telegram",
        "memory_policy": "ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1",
        "routine_wake_policy": "ROBOTICXS_ROUTINE_WAKE_GATE_v0_1",
        "blueprint_policy": "ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1",
        "canonical_memory_source": "Roboticxs Memory Center",
        "hermes_memory_is_canonical": False,
        "memory_projection_authorizes_tools": False,
        "raw_cron_exposed_to_consumers": False,
        "wake_agent_false_token_expectation": 0,
        "external_routine_delivery_without_confirmation": False,
        "caregiver_human_escalation_required": True,
        "runtime_scheduler_authorized": False,
        "production_messaging_authorized": False,
    }


def test_telegram_memory_routine_flow_preserves_caregiver_human_escalation():
    text = DOC_PATH.read_text()

    for required in [
        "Caregiver Telegram routine flows must preserve human escalation boundaries.",
        "must not decide medication changes, diagnose symptoms, monitor continuously, dispatch emergency services, or replace a caregiver, clinician, or responsible human.",
        "no live Hermes memory provider integration",
        "no scheduler execution",
        "no Telegram routine delivery",
        "no 95P or later authorization",
    ]:
        assert required in text
