from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.friendly_pilot_launch_baseline import (
    build_friendly_pilot_launch_baseline,
    render_friendly_pilot_launch_baseline,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FRIENDLY_PILOT_LAUNCH_BASELINE_222P_v0_1.md"
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
        bot_token="token-222p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_222p_builds_full_friendly_pilot_launch_baseline():
    baseline = build_friendly_pilot_launch_baseline(owner_id="local-owner", robot_id="roboticxs-dev")

    assert baseline.stage == "222P"
    assert baseline.status == "local_friendly_pilot_launch_baseline_v0"
    commands = {step.command for step in baseline.launch_steps}
    assert "/pilot_allowlist" in commands
    assert "/pilot_consent <alias>" in commands
    assert "/pilot_runbook" in commands
    assert "/pilot_boundary" in commands
    assert "/founder_loop" in commands
    assert "/feedback useful <item_id>" in commands
    assert "/report_issue medium <item_id>" in commands
    assert "/pilot_safety" in commands
    assert "/pilot_weekly_report" in commands
    assert "/end_pilot" in commands
    assert baseline.local_baseline_only is True
    assert baseline.live_data_claimed is False
    assert baseline.gmail_send_allowed is False
    assert baseline.calendar_write_allowed is False
    assert baseline.source_trace_preserved is True
    assert baseline.usage_cost_preserved is True


def test_222p_renders_launch_flow_and_stop_conditions():
    rendered = render_friendly_pilot_launch_baseline(
        build_friendly_pilot_launch_baseline(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Friendly Pilot Launch Baseline" in rendered
    assert "Stage: 222P" in rendered
    assert "Launch flow:" in rendered
    assert "/pilot_allowlist" in rendered
    assert "/pilot_weekly_report" in rendered
    assert "/end_pilot" in rendered
    assert "Stop conditions:" in rendered
    assert "- Gmail send: disabled" in rendered
    assert "- Source trace: preserved" in rendered


def test_222p_rejects_authority_expansion_or_missing_semantics():
    baseline = build_friendly_pilot_launch_baseline(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(baseline, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="live-data claims"):
        replace(baseline, live_data_claimed=True)
    with pytest.raises(ValueError, match="trace"):
        replace(baseline, source_trace_preserved=False)
    with pytest.raises(ValueError, match="cost"):
        replace(baseline, usage_cost_preserved=False)


def test_222p_telegram_pilot_launch_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=222,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_launch",
            command="/pilot_launch",
        ),
        client=client,
        config=_config(),
    )

    assert "Friendly Pilot Launch Baseline" in receipt.reply_text
    assert "Stage: 222P" in receipt.reply_text
    assert "/pilot_allowlist" in receipt.reply_text
    assert "/pilot_weekly_report" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_222p_reference_and_roadmap_close_launch_baseline_without_external_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "222P adds `/pilot_launch`" in reference
    assert "does not activate connectors" in reference
    assert '"stage_id":"222P","stage_name":"Friendly Pilot Launch Baseline v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
