from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.feedback_ledger_tags import build_feedback_ledger_entry_from_capture
from app.founder_feedback_capture import build_founder_feedback_capture_receipt
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.suggestion_quality_tuning import build_suggestion_quality_tuning_report, render_suggestion_quality_tuning_report


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SUGGESTION_QUALITY_TUNING_206P_v0_1.md"
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
        bot_token="token-206p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str):
    return build_feedback_ledger_entry_from_capture(
        build_founder_feedback_capture_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            tag=tag,
            item_id=item_id,
            source_trace_id="trace-206p",
        ),
        created_at="2026-06-30T01:00:00Z",
    )


def test_206p_builds_suggestion_quality_decisions_from_feedback():
    report = build_suggestion_quality_tuning_report(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        feedback_entries=(
            _feedback("wrong", "suggestion-1"),
            _feedback("useful", "suggestion-2"),
            _feedback("missing_source", "suggestion-3"),
        ),
    )

    decisions = {decision.suggestion_id: decision for decision in report.decisions}
    assert decisions["suggestion-1"].action == "suppress"
    assert decisions["suggestion-1"].adjusted_priority == "SUPPRESSED"
    assert decisions["suggestion-2"].action == "promote"
    assert decisions["suggestion-2"].adjusted_priority == "P1"
    assert decisions["suggestion-3"].action == "downgrade"
    assert decisions["suggestion-3"].adjusted_priority == "P3"
    assert report.feedback_entries_used == 3
    assert report.local_tuning_only is True
    assert report.external_write_allowed is False


def test_206p_renders_customer_visible_tuning_report():
    rendered = render_suggestion_quality_tuning_report(
        build_suggestion_quality_tuning_report(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            feedback_entries=(_feedback("stale", "suggestion-1"),),
        )
    )

    assert "Suggestion Quality Tuning" in rendered
    assert "Stage: 206P" in rendered
    assert "suggestion-1: suppress -> SUPPRESSED" in rendered
    assert "stale_or_wrong_signal" in rendered
    assert "Local tuning only: yes" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered


def test_206p_rejects_authority_expansion():
    report = build_suggestion_quality_tuning_report(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="local only"):
        replace(report, external_write_allowed=True)
    with pytest.raises(ValueError, match="connector write"):
        replace(report, gmail_send_allowed=True)


def test_206p_telegram_suggestion_quality_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=206,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/suggestion_quality",
            command="/suggestion_quality",
        ),
        client=client,
        config=_config(),
        feedback_ledger_entries=(_feedback("wrong", "suggestion-1"),),
    )

    assert "Suggestion Quality Tuning" in receipt.reply_text
    assert "Stage: 206P" in receipt.reply_text
    assert "suggestion-1: suppress" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_206p_reference_and_roadmap_close_suggestion_quality_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "206P uses local feedback ledger entries" in reference
    assert "does not add proactive sends" in reference
    assert '"stage_id":"206P","stage_name":"Suggestion Quality Tuning v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "207P and later remain unauthorized" in roadmap
