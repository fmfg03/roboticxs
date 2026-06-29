from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.friendly_pilot_operator_console import (
    FriendlyPilotUserStatus,
    build_friendly_pilot_operator_console,
    render_pilot_health,
    render_pilot_user,
    render_pilot_users,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FRIENDLY_PILOT_OPERATOR_CONSOLE_213P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None) -> dict:
        payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id}
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


def pilot_user(**overrides) -> FriendlyPilotUserStatus:
    values = {
        "user_id": "pilot-1",
        "user_alias": "Friendly One",
        "role": "friendly_user",
        "robot_status": "ready_local",
        "connector_readiness": "calendar_readonly_ready",
        "last_activity": "2026-06-30T12:00:00Z",
        "feedback_count": 3,
        "blocked_actions": 1,
        "unresolved_setup_issues": 0,
        "usage_cost_snapshot": "$0.004000 estimated",
    }
    values.update(overrides)
    return FriendlyPilotUserStatus(**values)


def _config() -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="token-213p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_213p_builds_operator_console_for_pilot_users():
    console = build_friendly_pilot_operator_console(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        users=(pilot_user(),),
    )

    assert console.stage == "213P"
    assert console.status == "local_friendly_pilot_operator_console_v0"
    assert console.users[0].user_alias == "Friendly One"
    assert console.users[0].feedback_count == 3
    assert console.local_console_only is True
    assert console.web_console_created is False
    assert console.provisioning_allowed is False
    assert console.external_write_allowed is False


def test_213p_renders_users_user_detail_and_health():
    console = build_friendly_pilot_operator_console(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        users=(pilot_user(),),
        selected_user_id="pilot-1",
    )

    roster = render_pilot_users(console)
    detail = render_pilot_user(console)
    health = render_pilot_health(console)

    assert "Friendly Pilot Users" in roster
    assert "Friendly One" in roster
    assert "Friendly Pilot User" in detail
    assert "Usage/cost snapshot: $0.004000 estimated" in detail
    assert "Friendly Pilot Health" in health
    assert "Health: needs_attention" in health
    assert "Web console: not created" in health


def test_213p_rejects_authority_expansion():
    console = build_friendly_pilot_operator_console(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external write"):
        replace(console, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="non-provisioning"):
        replace(console, provisioning_allowed=True)


def test_213p_telegram_operator_console_commands_are_visible():
    client = FakeTelegramClient()
    config = _config()
    users = (pilot_user(),)

    users_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=213,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_users",
            command="/pilot_users",
        ),
        client=client,
        config=config,
        friendly_pilot_users=users,
    )
    detail_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=214,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=334,
            raw_text="/pilot_user pilot-1",
            command="/pilot_user",
        ),
        client=client,
        config=config,
        friendly_pilot_users=users,
    )
    health_receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=215,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=335,
            raw_text="/pilot_health",
            command="/pilot_health",
        ),
        client=client,
        config=config,
        friendly_pilot_users=users,
    )

    assert "Friendly Pilot Users" in users_receipt.reply_text
    assert "Friendly Pilot User" in detail_receipt.reply_text
    assert "Friendly Pilot Health" in health_receipt.reply_text
    assert len(client.sent_messages) == 3


def test_213p_reference_and_roadmap_close_operator_console_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "213P adds local Telegram/admin pilot visibility commands" in reference
    assert "This is not a web console" in reference
    assert '"stage_id":"213P","stage_name":"Friendly Pilot Operator Console v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "216P and later remain unauthorized" in roadmap
