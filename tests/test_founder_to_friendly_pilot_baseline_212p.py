from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.founder_to_friendly_pilot_baseline import (
    build_founder_to_friendly_pilot_baseline,
    render_founder_to_friendly_pilot_baseline,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FOUNDER_TO_FRIENDLY_PILOT_BASELINE_212P_v0_1.md"
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
        bot_token="token-212p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_212p_builds_founder_to_friendly_pilot_baseline():
    baseline = build_founder_to_friendly_pilot_baseline(owner_id="local-owner", robot_id="roboticxs-dev")

    assert baseline.stage == "212P"
    assert baseline.status == "founder_to_friendly_pilot_baseline_v0"
    commands = {command for _, command, _ in baseline.flow_steps}
    assert "/founder_loop" in commands
    assert "/pilot_metrics" in commands
    assert "/friendly_onboarding" in commands
    assert any("source trace" in receipt for receipt in baseline.required_receipts)
    assert any("/setup" in check for check in baseline.readiness_checks)
    assert baseline.gmail_send_allowed is False
    assert baseline.calendar_write_allowed is False
    assert baseline.external_write_allowed is False


def test_212p_renders_baseline_with_receipts_and_stop_conditions():
    rendered = render_founder_to_friendly_pilot_baseline(
        build_founder_to_friendly_pilot_baseline(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Founder-to-Friendly Pilot Baseline" in rendered
    assert "Stage: 212P" in rendered
    assert "Pilot flow:" in rendered
    assert "Required receipts:" in rendered
    assert "Stop conditions:" in rendered
    assert "- Gmail send: disabled" in rendered
    assert "- Calendar writes: disabled" in rendered


def test_212p_rejects_authority_expansion():
    baseline = build_founder_to_friendly_pilot_baseline(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external write"):
        replace(baseline, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="dangerous writes"):
        replace(baseline, dangerous_writes_allowed=True)


def test_212p_telegram_friendly_pilot_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=212,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/friendly_pilot",
            command="/friendly_pilot",
        ),
        client=client,
        config=_config(),
    )

    assert "Founder-to-Friendly Pilot Baseline" in receipt.reply_text
    assert "Stage: 212P" in receipt.reply_text
    assert "/friendly_onboarding" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_212p_reference_and_roadmap_close_baseline_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "212P adds `/friendly_pilot`" in reference
    assert "controlled baseline from founder dogfooding" in reference
    assert '"stage_id":"212P","stage_name":"Founder-to-Friendly Pilot Baseline v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "215P and later remain unauthorized" in roadmap
