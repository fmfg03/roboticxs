from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_TELEGRAM_GATEWAY_BOUNDARY_v0_1.md"


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(DOC_PATH.read_text())
    assert match is not None, f"{DOC_PATH} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_telegram_gateway_boundary_separates_channel_product_and_runtime():
    text = DOC_PATH.read_text()

    assert "Status: 94P implemented pending review." in text
    for required in [
        "Telegram is the consumer-facing channel.",
        "Roboticxs is the product command surface.",
        "Hermes Gateway is runtime capability behind the product boundary.",
        "Raw Hermes commands must not be exposed directly to consumer Telegram users.",
        "Unknown Telegram commands and unverified raw Hermes commands default to blocked consumer exposure.",
        "Hermes Gateway capability does not grant",
        "skill activation authority",
        "tool execution authority",
        "memory write authority",
        "routine wake authority",
        "external send/write/publish/payment/destructive authority",
    ]:
        assert required in text


def test_telegram_gateway_boundary_packet_blocks_group_runtime_and_credentials():
    packet = load_json_block("telegram-gateway-boundary-packet")

    assert packet == {
        "packet_type": "TelegramGatewayBoundaryPacket",
        "status": "NON_RUNTIME_GOVERNANCE_PACKET",
        "stage": "94P",
        "consumer_channel": "Telegram",
        "runtime_layer": "Hermes Gateway",
        "product_command_surface": "Roboticxs",
        "raw_hermes_commands_consumer_visible": False,
        "unknown_commands_default": "BLOCK_CONSUMER",
        "group_chat_runtime_authorized": False,
        "caregiver_escalation_boundary_required": True,
        "credentials_allowed_in_repo": False,
        "runtime_enforcement_authorized": False,
    }


def test_telegram_gateway_boundary_documents_caregiver_and_group_limits():
    text = DOC_PATH.read_text()

    for required in [
        "Caregiver Telegram flows must preserve human escalation boundaries.",
        "Medication ambiguity, dosage, missed dose, duplicate dose, side effects, contradictory caregiver context, emergency signals, or professional decisions must escalate or block",
        "Group chat support is allowed only as a documented boundary/spec in 94P.",
        "does not authorize runtime group management",
        "no Telegram webhook registration",
        "no 95P or later authorization",
    ]:
        assert required in text
