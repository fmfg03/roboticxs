from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_TELEGRAM_HERMES_GATEWAY_MVP_v0_1.md"


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(DOC_PATH.read_text())
    assert match is not None, f"{DOC_PATH} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_telegram_hermes_gateway_mvp_contract_preserves_product_surface():
    text = DOC_PATH.read_text()

    assert "Status: 94P implemented pending review." in text
    for required in [
        "Telegram is the MVP user-facing channel",
        "Hermes Gateway is runtime capability, not the product UX.",
        "Roboticxs Command Surface Policy from 90P",
        "Skill Activation Scope Guard from 91P",
        "Hermes Tool Authority Guard from 92P",
        "Roboticxs Memory Center Bridge from 93P",
        "Routine Wake Gate from 88P",
        "Roboticxs Automation Blueprints from 89P",
        "Block raw Hermes operator, gateway, MCP/plugin, toolset, debug, config, reload, and bypass commands",
        "Require `/approve` or `/deny` equivalents to reference one specific Action Packet.",
        "Block any external send, write, publish, payment, or destructive action unless policy and confirmation both pass.",
    ]:
        assert required in text


def test_telegram_hermes_gateway_mvp_packet_blocks_runtime_and_credentials():
    packet = load_json_block("telegram-hermes-gateway-mvp-packet")

    assert packet == {
        "packet_type": "TelegramHermesGatewayMvpPacket",
        "status": "NON_RUNTIME_GOVERNANCE_PACKET",
        "stage": "94P",
        "user_channel": "Telegram",
        "runtime_capability": "Hermes Gateway",
        "product_surface": "Roboticxs Command Surface Policy",
        "raw_hermes_commands_exposed_to_consumers": False,
        "command_surface_policy_required": True,
        "skill_scope_guard_required": True,
        "tool_authority_guard_required": True,
        "memory_center_bridge_required": True,
        "routine_wake_gate_required": True,
        "action_packet_required_for_sensitive_actions": True,
        "telegram_credentials_committed": False,
        "runtime_gateway_start_authorized": False,
        "production_messaging_authorized": False,
        "future_stage_authorized": False,
    }


def test_telegram_hermes_gateway_mvp_has_no_secret_or_production_claims():
    text = DOC_PATH.read_text()

    for forbidden in [
        "no live Hermes Gateway startup",
        "no Telegram token, bot secret, credential, webhook URL, or production config",
        "no production messaging",
        "no real Telegram API sends",
        "no 95P or later authorization",
    ]:
        assert forbidden in text
