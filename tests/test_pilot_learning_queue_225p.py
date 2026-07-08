from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.pilot_learning_queue import build_pilot_learning_queue, render_pilot_learning_queue
from app.pilot_safety_incident_log import build_pilot_safety_incident
from app.pilot_support_issue_capture import build_pilot_support_issue_receipt
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.usage_cost_ledger import build_usage_cost_ledger_entry


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_LEARNING_QUEUE_225P_v0_1.md"
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
        bot_token="token-225p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str, item_type: str = "draft") -> FeedbackLedgerEntry:
    return FeedbackLedgerEntry(
        stage="204P",
        feedback_id=f"fb-{tag}-{item_id}",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id=item_id,
        item_type=item_type,
        tag=tag,
        comment="local learning comment",
        source_trace_id=f"trace-{item_id}",
        created_at="2026-07-08T09:00:00Z",
        status="recorded",
        storage_scope="local_structured_ledger",
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def test_225p_builds_prioritized_learning_queue_from_local_signals():
    queue = build_pilot_learning_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        feedback_entries=(_feedback("bad_draft", "draft-1"), _feedback("too_verbose", "brief-1", "daily_brief")),
        issue_receipts=(
            build_pilot_support_issue_receipt(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                pilot_user_id="225001",
                command="/report_missing",
                severity="medium",
                item_id="prep-1",
                comment="missing source trace",
            ),
        ),
        safety_incidents=(
            build_pilot_safety_incident(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                pilot_user_id="225001",
                incident_type="stale_approval_blocked",
                command="/approve",
                item_id="approval-1",
                reason="stale approval blocked",
            ),
        ),
        usage_entries=(
            build_usage_cost_ledger_entry(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                task_id="usage-225",
                command="/prep",
                task_class="meeting_prep",
                provider="local",
                model="local",
                model_mode="Premium",
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.06,
                status="blocked",
                failure_reason="local blocked fixture",
                created_at="2026-06-30T09:05:00Z",
            ),
        ),
    )

    assert queue.stage == "225P"
    assert queue.status == "local_pilot_learning_queue_v0"
    assert queue.fallback_status == "local_learning_signals_available"
    assert queue.total_items >= 5
    assert queue.priority_counts[0][0] == "P0"
    assert any(item.priority == "P0" and "safety" in item.learning_id for item in queue.items)
    assert any(item.priority == "P1" and "bad_draft" in item.learning_id for item in queue.items)
    assert any(item.priority == "P2" and item.learning_id == "usage-cost-watch" for item in queue.items)
    assert queue.local_queue_only is True
    assert queue.external_ticket_created is False
    assert queue.backlog_write_allowed is False
    assert queue.gmail_send_allowed is False
    assert queue.calendar_write_allowed is False
    assert queue.source_trace_preserved is True
    assert queue.usage_cost_preserved is True


def test_225p_renders_learning_backlog_and_safety_boundaries():
    rendered = render_pilot_learning_queue(
        build_pilot_learning_queue(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Pilot Learning Queue" in rendered
    assert "Stage: 225P" in rendered
    assert "Priority counts:" in rendered
    assert "Learning backlog:" in rendered
    assert "- no_local_learning_signals_yet" in rendered
    assert "- Local queue only: yes" in rendered
    assert "- Backlog write: disabled" in rendered
    assert "- External writes: disabled" in rendered


def test_225p_rejects_authority_expansion_or_missing_semantics():
    queue = build_pilot_learning_queue(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(queue, external_ticket_created=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(queue, backlog_write_allowed=True)
    with pytest.raises(ValueError, match="trace"):
        replace(queue, source_trace_preserved=False)
    with pytest.raises(ValueError, match="cost"):
        replace(queue, usage_cost_preserved=False)


def test_225p_telegram_pilot_learnings_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=225,
            chat_id=225,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_learnings",
            command="/pilot_learnings",
        ),
        client=client,
        config=_config(),
    )

    assert "Pilot Learning Queue" in receipt.reply_text
    assert "Stage: 225P" in receipt.reply_text
    assert "Priority counts:" in receipt.reply_text
    assert "Learning backlog:" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_225p_reference_and_roadmap_close_learning_queue_without_external_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "225P adds `/pilot_learnings`" in reference
    assert "does not" in reference
    assert "write to an external backlog" in reference
    assert '"stage_id":"225P","stage_name":"Pilot Learning Queue v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "226P and later remain unauthorized" in roadmap
