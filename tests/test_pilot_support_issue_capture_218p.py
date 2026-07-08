from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_support_issue_capture import (
    build_pilot_support_issue_receipt,
    parse_pilot_issue_argument,
    render_pilot_support_issue_receipt,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_SUPPORT_ISSUE_CAPTURE_218P_v0_1.md"
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
        bot_token="token-218p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_218p_builds_local_issue_receipt():
    receipt = build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        command="/report_bug",
        severity="high",
        item_id="prep-next",
        comment="source trace missing",
    )

    assert receipt.stage == "218P"
    assert receipt.status == "local_pilot_issue_captured_v0"
    assert receipt.issue_id == "issue-bug-prep-next-high"
    assert receipt.pilot_user_id == "111111111"
    assert receipt.category == "bug"
    assert receipt.severity == "high"
    assert receipt.local_capture_only is True
    assert receipt.external_ticket_created is False
    assert receipt.crm_write_allowed is False
    assert receipt.gmail_send_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.approval_gate_preserved is True


def test_218p_parses_issue_arguments_and_redacts_comments():
    assert parse_pilot_issue_argument("critical draft-1 token leaked") == (
        "critical",
        "draft-1",
        "token leaked",
    )
    assert parse_pilot_issue_argument("prep-next missing calendar") == (
        "medium",
        "prep-next",
        "missing calendar",
    )
    receipt = build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        command="/report_issue",
        severity="medium",
        item_id="pilot-1",
        comment="bearer token visible",
    )

    assert "[redacted]" in receipt.comment
    assert "token" not in receipt.comment


def test_218p_renders_issue_receipt():
    receipt = build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        command="/report_confusing",
        severity="low",
        item_id="daily-brief",
        comment="too much setup copy",
    )
    rendered = render_pilot_support_issue_receipt(receipt)

    assert "Pilot Support Issue" in rendered
    assert "Category: confusing" in rendered
    assert "Item: daily-brief" in rendered
    assert "External ticket: no" in rendered
    assert "CRM write: disabled" in rendered
    assert "Gmail send: disabled" in rendered


def test_218p_rejects_external_authority():
    receipt = build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        command="/report_bug",
        severity="high",
        item_id="prep-next",
    )

    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, crm_write_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, calendar_write_allowed=True)
    with pytest.raises(ValueError, match="local"):
        replace(receipt, external_ticket_created=True)


def test_218p_telegram_issue_commands_are_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=218,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/report_missing high prep-next no calendar context",
            command="/report_missing",
        ),
        client=client,
        config=_config(),
    )

    assert "Pilot Support Issue" in receipt.reply_text
    assert "Pilot user: 111111111" in receipt.reply_text
    assert "Severity: high" in receipt.reply_text
    assert "Category: missing_context" in receipt.reply_text
    assert "Item: prep-next" in receipt.reply_text
    assert len(client.sent_messages) == 1


def test_218p_reference_and_roadmap_close_issue_capture_without_external_tickets():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "218P adds local Telegram issue capture" in reference
    assert "does not create external tickets" in reference
    assert '"stage_id":"218P","stage_name":"Pilot Support & Issue Capture v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "226P and later remain unauthorized" in roadmap
