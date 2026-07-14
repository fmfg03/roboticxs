from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.daily_loop_outcome_tracker import build_daily_loop_outcome_record
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.first_friendly_user_activation import build_first_friendly_user_activation_receipt
from app.pilot_review_session_pack import (
    build_pilot_review_session_pack,
    parse_pilot_review_argument,
    render_pilot_review_session_pack,
)
from app.pilot_safety_incident_log import build_pilot_safety_incident
from app.pilot_support_issue_capture import build_pilot_support_issue_receipt
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.usage_cost_ledger import build_usage_cost_ledger_entry


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_REVIEW_SESSION_PACK_224P_v0_1.md"
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
        bot_token="token-224p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str, item_type: str = "prep") -> FeedbackLedgerEntry:
    return FeedbackLedgerEntry(
        stage="204P",
        feedback_id=f"fb-{tag}-{item_id}",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id=item_id,
        item_type=item_type,
        tag=tag,
        comment="local comment",
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


def test_224p_builds_review_pack_from_local_signals():
    pack = build_pilot_review_session_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="224001",
        pilot_alias="Ana Pilot",
        activation_receipts=(
            build_first_friendly_user_activation_receipt(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                pilot_user_id="224001",
                pilot_alias="Ana Pilot",
            ),
        ),
        feedback_entries=(_feedback("useful", "prep-good"), _feedback("missing_source", "daily-brief", "daily_brief")),
        outcome_records=(
            build_daily_loop_outcome_record(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                loop_id="loop-224",
                outcome="draft_created",
            ),
        ),
        issue_receipts=(
            build_pilot_support_issue_receipt(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                pilot_user_id="224001",
                command="/report_missing",
                severity="medium",
                item_id="daily-brief",
                comment="missing Gmail context",
            ),
        ),
        safety_incidents=(
            build_pilot_safety_incident(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                pilot_user_id="224001",
                incident_type="connector_scope_mismatch",
                command="/prep",
                item_id="prep-good",
                reason="connector scope mismatch",
            ),
        ),
        usage_entries=(
            build_usage_cost_ledger_entry(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                task_id="usage-224",
                command="/prep",
                task_class="meeting_prep",
                provider="local",
                model="local",
                model_mode="Economy",
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.001,
                created_at="2026-06-30T09:05:00Z",
            ),
        ),
    )

    assert pack.stage == "224P"
    assert pack.status == "local_pilot_review_session_pack_v0"
    assert pack.fallback_status == "local_review_signals_available"
    assert "/pilot_activate" in pack.what_user_tried
    assert "/prep" in pack.what_user_tried
    assert any("prep-good" in item for item in pack.what_worked)
    assert any("missing Gmail context" in item for item in pack.where_stuck)
    assert pack.best_output == "prep/prep-good (trace-prep-good)"
    assert pack.worst_output == "daily_brief/daily-brief: missing_source"
    assert any("connector scope mismatch" in item for item in pack.missing_connector_or_context)
    assert any("P1: improve source/context visibility" in item for item in pack.recommended_product_fixes)
    assert pack.estimated_cost_usd == 0.001
    assert pack.gmail_send_allowed is False
    assert pack.calendar_write_allowed is False
    assert pack.source_trace_preserved is True
    assert pack.usage_cost_preserved is True


def test_224p_renders_review_sections_and_safety_boundaries():
    rendered = render_pilot_review_session_pack(
        build_pilot_review_session_pack(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Pilot Review Session Pack" in rendered
    assert "Stage: 224P" in rendered
    assert "What the user tried:" in rendered
    assert "What worked:" in rendered
    assert "Where they got stuck:" in rendered
    assert "Best output: not_recorded_yet" in rendered
    assert "Worst output: not_recorded_yet" in rendered
    assert "Recommended product fixes:" in rendered
    assert "- Local review only: yes" in rendered
    assert "- External writes: disabled" in rendered


def test_224p_parses_pilot_review_argument():
    assert parse_pilot_review_argument(None, fallback_pilot_user_id="111") == ("111", "Friendly pilot")
    assert parse_pilot_review_argument("Ana Pilot", fallback_pilot_user_id="111") == ("111", "Ana Pilot")
    assert parse_pilot_review_argument("224001 Ana Pilot", fallback_pilot_user_id="111") == ("224001", "Ana Pilot")


def test_224p_rejects_authority_expansion_or_missing_semantics():
    pack = build_pilot_review_session_pack(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(pack, crm_write_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(pack, live_data_claimed=True)
    with pytest.raises(ValueError, match="trace"):
        replace(pack, source_trace_preserved=False)
    with pytest.raises(ValueError, match="cost"):
        replace(pack, usage_cost_preserved=False)


def test_224p_telegram_pilot_review_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=224,
            chat_id=224,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_review 224001 Ana Pilot",
            command="/pilot_review",
        ),
        client=client,
        config=_config(),
    )

    assert "Pilot Review Session Pack" in receipt.reply_text
    assert "Stage: 224P" in receipt.reply_text
    assert "Pilot: Ana Pilot" in receipt.reply_text
    assert "Pilot user id: 224001" in receipt.reply_text
    assert "What the user tried:" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_224p_reference_and_roadmap_close_review_pack_without_external_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "224P adds `/pilot_review`" in reference
    assert "does not" in reference
    assert "create external tickets" in reference
    assert '"stage_id":"224P","stage_name":"Pilot Review Session Pack v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
