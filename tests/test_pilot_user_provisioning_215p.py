from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_user_provisioning import (
    build_pilot_user_provisioning_record,
    parse_pilot_provision_argument,
    render_pilot_allowlist,
    render_pilot_user_provisioning,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_USER_PROVISIONING_215P_v0_1.md"
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
        bot_token="token-215p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_215p_builds_strict_allowlist_provisioning_record():
    record = build_pilot_user_provisioning_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        allowed_telegram_user_id=222222222,
        user_alias="Ana",
    )

    assert record.stage == "215P"
    assert record.status == "local_allowlist_provisioning_v0"
    assert record.role == "friendly_user"
    assert record.user_alias == "Ana"
    assert record.allowed_telegram_user_id == 222222222
    assert "basic" in record.enabled_skill_packages
    assert "memory: local_scoped" in record.connector_status
    assert record.pilot_status == "pending_consent"
    assert record.strict_allowlist is True
    assert record.open_signup_allowed is False
    assert record.connector_activation_allowed is False


def test_215p_renders_provisioning_and_allowlist():
    record = build_pilot_user_provisioning_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        allowed_telegram_user_id=222222222,
        user_alias="Ana",
    )

    provisioning = render_pilot_user_provisioning(record)
    allowlist = render_pilot_allowlist((record,))

    assert "Pilot User Provisioning" in provisioning
    assert "Allowed Telegram user id: 222222222" in provisioning
    assert "Enabled skill packages:" in provisioning
    assert "Connector status:" in provisioning
    assert "Strict allowlist: yes" in provisioning
    assert "Connector activation: disabled" in provisioning
    assert "Pilot User Allowlist" in allowlist
    assert "222222222 | Ana | friendly_user | pending_consent" in allowlist


def test_215p_parse_provisioning_argument():
    assert parse_pilot_provision_argument("222222222 Ana Pilot", fallback_telegram_user_id=111111111) == (
        222222222,
        "Ana Pilot",
    )
    assert parse_pilot_provision_argument("Ana Pilot", fallback_telegram_user_id=111111111) == (
        111111111,
        "Ana Pilot",
    )


def test_215p_rejects_authority_expansion():
    record = build_pilot_user_provisioning_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        allowed_telegram_user_id=222222222,
        user_alias="Ana",
    )

    with pytest.raises(ValueError, match="strict local allowlist authority"):
        replace(record, strict_allowlist=False)
    with pytest.raises(ValueError, match="strict local allowlist authority"):
        replace(record, open_signup_allowed=True)
    with pytest.raises(ValueError, match="strict local allowlist authority"):
        replace(record, connector_activation_allowed=True)
    with pytest.raises(ValueError, match="strict local allowlist authority"):
        replace(record, gmail_send_allowed=True)


def test_215p_telegram_provisioning_commands_are_visible():
    client = FakeTelegramClient()
    config = _config()

    provision_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=215,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_provision 222222222 Ana",
            command="/pilot_provision",
        ),
        client=client,
        config=config,
    )
    allowlist_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=216,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=334,
            raw_text="/pilot_allowlist",
            command="/pilot_allowlist",
        ),
        client=client,
        config=config,
    )

    assert "Pilot User Provisioning" in provision_receipt.reply_text
    assert "Alias: Ana" in provision_receipt.reply_text
    assert "Allowed Telegram user id: 222222222" in provision_receipt.reply_text
    assert "Pilot User Allowlist" in allowlist_receipt.reply_text
    assert "Strict allowlist: yes" in allowlist_receipt.reply_text
    assert len(client.sent_messages) == 2


def test_215p_reference_and_roadmap_close_provisioning_without_open_access():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "215P adds local Telegram/admin pilot provisioning visibility" in reference
    assert "does not modify Telegram owner ids" in reference
    assert '"stage_id":"215P","stage_name":"Pilot User Provisioning v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "225P and later remain unauthorized" in roadmap
