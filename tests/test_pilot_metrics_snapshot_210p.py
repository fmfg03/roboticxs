from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.daily_loop_outcome_tracker import build_daily_loop_outcome_record
from app.feedback_ledger_tags import build_feedback_ledger_entry_from_capture
from app.founder_feedback_capture import build_founder_feedback_capture_receipt
from app.pilot_metrics_snapshot import build_pilot_metrics_snapshot, render_pilot_metrics_snapshot
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.usage_cost_ledger import build_usage_cost_ledger_entry


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_METRICS_SNAPSHOT_210P_v0_1.md"
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
        bot_token="token-210p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str):
    capture = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag=tag,
        item_id=item_id,
    )
    return build_feedback_ledger_entry_from_capture(capture, created_at="2026-06-30T09:00:00Z")


def _outcome(loop_id: str, outcome: str):
    return build_daily_loop_outcome_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        loop_id=loop_id,
        outcome=outcome,
        created_at="2026-06-30T10:00:00Z",
    )


def _usage(task_id: str, cost: float):
    return build_usage_cost_ledger_entry(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id=task_id,
        command="/prep",
        task_class="prep",
        provider="local",
        model="local-estimate",
        model_mode="balanced",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=cost,
        created_at="2026-06-30T11:00:00Z",
    )


def test_210p_builds_local_pilot_metrics_snapshot():
    snapshot = build_pilot_metrics_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        feedback_entries=(
            _feedback("useful", "suggestion-1"),
            _feedback("noisy", "suggestion-2"),
            _feedback("stale", "mem-1"),
        ),
        outcome_records=(
            _outcome("loop-1", "draft_created"),
            _outcome("loop-2", "draft_approved"),
            _outcome("loop-3", "document_reviewed"),
            _outcome("loop-4", "blocked_by_missing_connector"),
        ),
        usage_entries=(_usage("task-1", 0.004),),
    )

    assert snapshot.stage == "210P"
    assert snapshot.daily_loops_run == 4
    assert snapshot.suggestions_feedback_count == 2
    assert snapshot.suggestions_positive == 1
    assert snapshot.suggestions_negative == 1
    assert snapshot.drafts_created == 1
    assert snapshot.drafts_approved == 1
    assert snapshot.memory_changes == 1
    assert snapshot.document_reviews == 1
    assert snapshot.usage_tasks == 1
    assert snapshot.estimated_cost_usd == 0.004
    assert snapshot.blocked_actions == 1
    assert snapshot.fallback_status == "local_metrics_available"
    assert snapshot.live_data_claimed is False
    assert snapshot.external_write_allowed is False


def test_210p_renders_empty_fallback_without_live_claims():
    snapshot = build_pilot_metrics_snapshot(owner_id="local-owner", robot_id="roboticxs-dev")
    rendered = render_pilot_metrics_snapshot(snapshot)

    assert snapshot.fallback_status == "no_local_metrics_yet"
    assert "Pilot Metrics Snapshot" in rendered
    assert "Fallback: no_local_metrics_yet" in rendered
    assert "- Daily loops run: 0" in rendered
    assert "Live data claimed: no" in rendered
    assert "Gmail send: disabled" in rendered


def test_210p_rejects_authority_expansion():
    snapshot = build_pilot_metrics_snapshot(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external write"):
        replace(snapshot, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="live data"):
        replace(snapshot, live_data_claimed=True)


def test_210p_telegram_pilot_metrics_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=210,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_metrics",
            command="/pilot_metrics",
        ),
        client=client,
        config=_config(),
        feedback_ledger_entries=(_feedback("useful", "suggestion-1"),),
        daily_loop_outcome_records=(_outcome("loop-1", "draft_created"),),
        usage_ledger_entries=(_usage("task-1", 0.004),),
    )

    assert "Pilot Metrics Snapshot" in receipt.reply_text
    assert "Stage: 210P" in receipt.reply_text
    assert "- Daily loops run: 1" in receipt.reply_text
    assert "- Estimated cost: $0.004000" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_210p_reference_and_roadmap_close_metrics_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "210P adds `/pilot_metrics`" in reference
    assert "does not claim live analytics" in reference
    assert '"stage_id":"210P","stage_name":"Pilot Metrics Snapshot v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "220P and later remain unauthorized" in roadmap
