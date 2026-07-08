from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_onboarding_runbook import build_pilot_onboarding_runbook, render_pilot_onboarding_runbook
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_ONBOARDING_RUNBOOK_217P_v0_1.md"
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
        bot_token="token-217p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_217p_builds_day_0_through_day_7_runbook():
    runbook = build_pilot_onboarding_runbook(owner_id="local-owner", robot_id="roboticxs-dev")

    assert runbook.stage == "217P"
    assert runbook.status == "local_day_0_day_7_runbook_v0"
    assert tuple(day.day for day in runbook.days) == (
        "Day 0",
        "Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
        "Day 6",
        "Day 7",
    )
    assert "pilot user appears in strict local allowlist" in runbook.prerequisites
    assert runbook.local_runbook_only is True
    assert runbook.external_invite_allowed is False
    assert runbook.connector_activation_allowed is False
    assert runbook.gmail_send_allowed is False
    assert runbook.calendar_write_allowed is False


def test_217p_renders_runbook_with_expected_results_fallbacks_and_stops():
    rendered = render_pilot_onboarding_runbook(
        build_pilot_onboarding_runbook(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Pilot Onboarding Runbook" in rendered
    assert "Day 0-Day 7:" in rendered
    assert "Day 0: setup, consent, allowlist" in rendered
    assert "Day 7: weekly report and decision" in rendered
    assert "Expected:" in rendered
    assert "Fallback:" in rendered
    assert "Stop:" in rendered
    assert "Pass condition:" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered


def test_217p_rejects_authority_expansion():
    runbook = build_pilot_onboarding_runbook(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="pilot authority"):
        replace(runbook, external_invite_allowed=True)
    with pytest.raises(ValueError, match="pilot authority"):
        replace(runbook, provisioning_write_allowed=True)
    with pytest.raises(ValueError, match="pilot authority"):
        replace(runbook, connector_activation_allowed=True)
    with pytest.raises(ValueError, match="pilot authority"):
        replace(runbook, gmail_send_allowed=True)


def test_217p_telegram_runbook_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=217,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_runbook",
            command="/pilot_runbook",
        ),
        client=client,
        config=_config(),
    )

    assert "Pilot Onboarding Runbook" in receipt.reply_text
    assert "Day 0: setup, consent, allowlist" in receipt.reply_text
    assert "Day 7: weekly report and decision" in receipt.reply_text
    assert "Local runbook only: yes" in receipt.reply_text
    assert len(client.sent_messages) == 1


def test_217p_reference_and_roadmap_close_runbook_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "217P adds `/pilot_runbook`" in reference
    assert "Each day includes a command, expected result, fallback status, and stop condition" in reference
    assert '"stage_id":"217P","stage_name":"Pilot Onboarding Runbook v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
