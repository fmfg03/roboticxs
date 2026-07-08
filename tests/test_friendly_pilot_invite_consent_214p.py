from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.friendly_pilot_invite_consent import (
    build_friendly_pilot_invite_consent,
    render_pilot_consent,
    render_pilot_invite,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FRIENDLY_PILOT_INVITE_CONSENT_214P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None) -> dict:
        payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id}
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


def _config() -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="token-214p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_214p_builds_invite_consent_without_external_authority():
    consent = build_friendly_pilot_invite_consent(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_alias="Ana",
    )

    assert consent.stage == "214P"
    assert consent.status == "local_invite_consent_text_v0"
    assert consent.pilot_alias == "Ana"
    assert consent.local_text_only is True
    assert consent.external_invite_sent is False
    assert consent.connector_activation_allowed is False
    assert consent.provisioning_allowed is False
    assert consent.gmail_send_allowed is False
    assert consent.calendar_write_allowed is False
    assert consent.crm_write_allowed is False
    assert consent.whatsapp_allowed is False


def test_214p_renders_invite_and_consent_sections():
    consent = build_friendly_pilot_invite_consent(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_alias="Ana",
    )

    invite = render_pilot_invite(consent)
    consent_card = render_pilot_consent(consent)

    assert "Friendly Pilot Invite" in invite
    assert "Ana, Roboticxs is a controlled personal robot pilot" in invite
    assert "External invite sent: no" in invite
    assert "Friendly Pilot Consent" in consent_card
    assert "What the robot can read:" in consent_card
    assert "What the robot cannot do:" in consent_card
    assert "What requires approval:" in consent_card
    assert "What is logged:" in consent_card
    assert "How to stop:" in consent_card
    assert "How to remove or correct memory:" in consent_card
    assert "Gmail send: disabled" in consent_card
    assert "Calendar writes: disabled" in consent_card


def test_214p_rejects_authority_expansion():
    consent = build_friendly_pilot_invite_consent(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(consent, external_invite_sent=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(consent, connector_activation_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(consent, provisioning_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(consent, gmail_send_allowed=True)


def test_214p_telegram_invite_and_consent_commands_are_visible():
    client = FakeTelegramClient()
    config = _config()

    invite_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=214,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_invite Ana",
            command="/pilot_invite",
        ),
        client=client,
        config=config,
    )
    consent_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=215,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=334,
            raw_text="/pilot_consent Ana",
            command="/pilot_consent",
        ),
        client=client,
        config=config,
    )

    assert "Friendly Pilot Invite" in invite_receipt.reply_text
    assert "Friendly Pilot Consent" in consent_receipt.reply_text
    assert "Pilot: Ana" in consent_receipt.reply_text
    assert "Connector activation: disabled" in consent_receipt.reply_text
    assert len(client.sent_messages) == 2


def test_214p_reference_and_roadmap_close_invite_consent_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "214P adds local Telegram/admin invite and consent text" in reference
    assert "does not create a real invite" in reference
    assert '"stage_id":"214P","stage_name":"Friendly Pilot Invite & Consent Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "226P and later remain unauthorized" in roadmap
