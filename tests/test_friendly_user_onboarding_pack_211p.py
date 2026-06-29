from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.friendly_user_onboarding_pack import build_friendly_user_onboarding_pack, render_friendly_user_onboarding_pack
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FRIENDLY_USER_ONBOARDING_PACK_211P_v0_1.md"
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
        bot_token="token-211p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_211p_builds_friendly_user_onboarding_pack():
    pack = build_friendly_user_onboarding_pack(owner_id="local-owner", robot_id="roboticxs-dev")

    assert pack.stage == "211P"
    assert pack.user_limit == "1-3 friendly users"
    assert "/daily_brief" in pack.allowed_commands
    assert "/pilot_metrics" in pack.allowed_commands
    assert "Gmail send/modify/archive/delete" in pack.blocked_actions
    assert any("source trace" in line for line in pack.privacy_source_explanation)
    assert any("Memory proposals are not facts" in line for line in pack.memory_approval_explanation)
    assert "/feedback useful <item_id>" in pack.feedback_commands
    assert pack.gmail_send_allowed is False
    assert pack.calendar_write_allowed is False
    assert pack.external_write_allowed is False


def test_211p_renders_pack_with_stop_conditions_and_safety():
    rendered = render_friendly_user_onboarding_pack(build_friendly_user_onboarding_pack(owner_id="local-owner", robot_id="roboticxs-dev"))

    assert "Friendly User Onboarding Pack" in rendered
    assert "- Stage: 211P" in rendered
    assert "Setup checklist" in rendered
    assert "Allowed commands" in rendered
    assert "Stop conditions" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered


def test_211p_rejects_authority_expansion():
    pack = build_friendly_user_onboarding_pack(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external write"):
        replace(pack, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="1-3 users"):
        replace(pack, user_limit="unbounded")


def test_211p_telegram_friendly_onboarding_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=211,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/friendly_onboarding",
            command="/friendly_onboarding",
        ),
        client=client,
        config=_config(),
    )

    assert "Friendly User Onboarding Pack" in receipt.reply_text
    assert "- Stage: 211P" in receipt.reply_text
    assert "1-3 friendly users" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_211p_reference_and_roadmap_close_friendly_onboarding_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "211P adds `/friendly_onboarding`" in reference
    assert "controlled 1-3 friendly-user pilot setup pack" in reference
    assert '"stage_id":"211P","stage_name":"Friendly User Onboarding Pack v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "212P and later remain unauthorized" in roadmap
