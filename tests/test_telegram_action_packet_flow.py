from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_TELEGRAM_ACTION_PACKET_FLOW_v0_1.md"


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(DOC_PATH.read_text())
    assert match is not None, f"{DOC_PATH} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_telegram_action_packet_flow_requires_visible_packet_confirmation():
    text = DOC_PATH.read_text()

    assert "Status: 94P implemented pending review." in text
    for required in [
        "Sensitive actions requested from Telegram must produce visible Action Packets before confirmation.",
        "`/approve` and `/deny` equivalents must be tied to a specific Action Packet.",
        "A bare approval, ambiguous reply, emoji reaction, or command without packet identity must not execute a sensitive action.",
        "No external send, external write, publish, third-party schedule, CRM modification, visual signature, payment, refund, credential change, permission change, legal acceptance, production deploy, destructive action, or professional decision may execute from Telegram without policy and confirmation.",
        "92P Tool Authority Guard remains the classifier.",
        "`ASK_CONFIRMATION` must produce an Action Packet.",
        "`BLOCK` must not be converted into an Action Packet",
    ]:
        assert required in text


def test_telegram_action_packet_flow_packet_blocks_ambiguous_approval():
    packet = load_json_block("telegram-action-packet-flow")

    assert packet == {
        "packet_type": "TelegramActionPacketFlow",
        "status": "NON_RUNTIME_GOVERNANCE_PACKET",
        "stage": "94P",
        "channel": "Telegram",
        "action_packet_policy": "ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1",
        "tool_authority_policy": "ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1",
        "confirmation_requires_specific_packet": True,
        "bare_approve_executes_sensitive_action": False,
        "bare_deny_closes_sensitive_action": False,
        "hidden_or_truncated_content_valid": False,
        "blocked_actions_convert_to_packets": False,
        "external_effect_without_confirmation_authorized": False,
        "runtime_execution_authorized": False,
    }


def test_telegram_action_packet_flow_preserves_non_runtime_scope():
    text = DOC_PATH.read_text()

    for required in [
        "no approval command implementation",
        "no packet renderer implementation",
        "no connector activation",
        "no Telegram send/write execution",
        "no payment, credential, legal, deploy, destructive, or professional action execution",
        "no 95P or later authorization",
    ]:
        assert required in text
