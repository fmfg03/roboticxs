from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.daily_loop_outcome_tracker import (
    DAILY_LOOP_OUTCOME_TRACKER_STAGE,
    DAILY_LOOP_OUTCOME_TRACKER_STATUS,
    build_daily_loop_outcome_record,
    parse_daily_loop_outcome_argument,
    render_daily_loop_outcome_record,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DAILY_LOOP_OUTCOME_TRACKER_205P_v0_1.md"
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
        bot_token="token-205p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_205p_parses_and_builds_daily_loop_outcome():
    assert parse_daily_loop_outcome_argument("loop-1 draft_approved useful draft") == (
        "loop-1",
        "draft_approved",
        "useful draft",
    )

    record = build_daily_loop_outcome_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        loop_id="loop-1",
        outcome="draft_approved",
        note="sent to export",
        source_trace_id="trace-205p",
    )

    assert record.stage == DAILY_LOOP_OUTCOME_TRACKER_STAGE
    assert record.status == DAILY_LOOP_OUTCOME_TRACKER_STATUS
    assert record.outcome == "draft_approved"
    assert record.note == "sent to export"
    assert record.source_trace_id == "trace-205p"
    assert record.local_tracker_only is True
    assert record.external_write_allowed is False
    assert record.gmail_send_allowed is False
    assert record.calendar_write_allowed is False
    assert record.secrets_redacted is True
    assert record.approval_gate_preserved is True


def test_205p_renders_customer_visible_outcome_receipt():
    rendered = render_daily_loop_outcome_record(
        build_daily_loop_outcome_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            loop_id="loop-1",
            outcome="memory_approved",
        )
    )

    assert "Daily Loop Outcome" in rendered
    assert "Stage: 205P" in rendered
    assert "Loop: loop-1" in rendered
    assert "Outcome: memory_approved" in rendered
    assert "Local tracker only: yes" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_205p_rejects_invalid_outcomes_and_authority_expansion():
    record = build_daily_loop_outcome_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        loop_id="loop-1",
        outcome="viewed",
    )

    with pytest.raises(ValueError, match="unsupported"):
        build_daily_loop_outcome_record(owner_id="local-owner", robot_id="roboticxs-dev", loop_id="loop-1", outcome="send")
    with pytest.raises(ValueError, match="connector write"):
        replace(record, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="local only"):
        replace(record, external_write_allowed=True)


def test_205p_telegram_founder_outcome_command_is_owner_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=205,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/founder_outcome loop-1 blocked_by_missing_connector calendar missing",
            command="/founder_outcome",
        ),
        client=client,
        config=_config(),
    )

    assert "Daily Loop Outcome" in receipt.reply_text
    assert "Stage: 205P" in receipt.reply_text
    assert "Outcome: blocked_by_missing_connector" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_205p_reference_and_roadmap_close_outcome_tracker_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "205P records whether a founder loop produced a useful outcome" in reference
    assert "does not add pilot metrics" in reference
    assert '"stage_id":"205P","stage_name":"Daily Loop Outcome Tracker v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "223P and later remain unauthorized" in roadmap
