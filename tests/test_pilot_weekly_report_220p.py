from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.daily_loop_outcome_tracker import build_daily_loop_outcome_record
from app.draft_revision_loop import build_draft_revision_receipt
from app.feedback_ledger_tags import build_feedback_ledger_entry_from_capture
from app.founder_feedback_capture import build_founder_feedback_capture_receipt
from app.memory_center_projection import MemoryCenterItem
from app.memory_correction_loop import build_memory_correction_receipt
from app.pilot_safety_incident_log import build_pilot_safety_incident
from app.pilot_support_issue_capture import build_pilot_support_issue_receipt
from app.pilot_weekly_report import build_pilot_weekly_report, render_pilot_weekly_report
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle
from app.usage_cost_ledger import build_usage_cost_ledger_entry


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_WEEKLY_REPORT_220P_v0_1.md"
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
        bot_token="token-220p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str, created_at: str = "2026-07-01T09:00:00Z"):
    capture = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag=tag,
        item_id=item_id,
    )
    return build_feedback_ledger_entry_from_capture(capture, created_at=created_at)


def _outcome(loop_id: str, outcome: str, created_at: str = "2026-07-02T09:00:00Z"):
    return build_daily_loop_outcome_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        loop_id=loop_id,
        outcome=outcome,
        created_at=created_at,
    )


def _usage(task_id: str, command: str, task_class: str, cost: float):
    return build_usage_cost_ledger_entry(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id=task_id,
        command=command,
        task_class=task_class,
        provider="local",
        model="local-estimate",
        model_mode="balanced",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=cost,
        created_at="2026-06-30T11:00:00Z",
    )


def _issue():
    return build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        command="/report_bug",
        severity="high",
        item_id="prep-1",
        comment="missing source",
        created_at="2026-07-03T09:00:00Z",
    )


def _safety():
    return build_pilot_safety_incident(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="111111111",
        incident_type="attempted_gmail_send",
        command="/export_email",
        item_id="draft-1",
        reason="Gmail send is prohibited",
        created_at="2026-07-04T09:00:00Z",
    )


def _memory_item(item_id: str = "mem-220p") -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id=item_id,
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_kind="owner_preference",
        status="active",
        scopes=("telegram", "general"),
        sensitivity="ordinary",
        allowed_uses=("telegram_context",),
        skill_ids=(),
        content="Francisco prefers direct pilot reports.",
        bounded_summary="Francisco prefers direct pilot reports.",
        source="owner_approved_memory",
        actor_visibility="owner_private",
    )


def _memory_correction():
    return build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="stale",
        memory_id="mem-220p",
        source_bundle=TelegramMemoryCenterSourceBundle(approved_memory_items=(_memory_item(),)),
    )


def test_220p_builds_local_pilot_weekly_report():
    report = build_pilot_weekly_report(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        feedback_entries=(
            _feedback("useful", "suggestion-1"),
            _feedback("noisy", "suggestion-2"),
            _feedback("stale", "memory-1"),
        ),
        outcome_records=(
            _outcome("loop-1", "draft_created"),
            _outcome("loop-2", "draft_approved"),
            _outcome("loop-3", "memory_approved"),
            _outcome("loop-4", "document_reviewed"),
        ),
        usage_entries=(_usage("task-prep", "/prep", "prep", 0.004),),
        issue_receipts=(_issue(),),
        safety_incidents=(_safety(),),
        draft_revisions=(build_draft_revision_receipt(owner_id="local-owner", robot_id="roboticxs-dev", draft_id="draft-1", revision_request="shorter"),),
        memory_corrections=(_memory_correction(),),
    )

    assert report.stage == "220P"
    assert report.status == "local_pilot_weekly_report_v0"
    assert report.active_days == 4
    assert report.loops_run == 4
    assert report.prep_packs_generated == 1
    assert report.suggestions_accepted == 1
    assert report.suggestions_dismissed == 1
    assert report.drafts_created == 1
    assert report.drafts_revised == 1
    assert report.drafts_approved == 1
    assert report.memories_approved == 1
    assert report.memories_corrected == 1
    assert report.memories_forgotten == 1
    assert report.documents_reviewed == 1
    assert report.issues_opened == 1
    assert report.safety_incidents == 1
    assert report.estimated_cost_usd == 0.004
    assert report.top_product_learnings == (
        "Feedback trend: noisy appeared 1 time(s).",
        "Support trend: bug issue(s) appeared 1 time(s).",
        "Safety trend: attempted_gmail_send blocked 1 time(s).",
    )
    assert report.local_report_only is True
    assert report.live_data_claimed is False
    assert report.gmail_send_allowed is False
    assert report.calendar_write_allowed is False
    assert report.approval_gate_preserved is True


def test_220p_renders_empty_fallback_without_live_claims():
    report = build_pilot_weekly_report(owner_id="local-owner", robot_id="roboticxs-dev")
    rendered = render_pilot_weekly_report(report)

    assert report.fallback_status == "no_local_weekly_data_yet"
    assert "Pilot Weekly Report" in rendered
    assert "Fallback: no_local_weekly_data_yet" in rendered
    assert "- Active days: 0" in rendered
    assert "- Estimated cost: $0.000000" in rendered
    assert "- no_local_weekly_data_yet" in rendered
    assert "Live data claimed: no" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered


def test_220p_rejects_authority_expansion():
    report = build_pilot_weekly_report(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="live data"):
        replace(report, live_data_claimed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(report, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(report, calendar_write_allowed=True)
    with pytest.raises(ValueError, match="approval-preserving"):
        replace(report, approval_gate_preserved=False)


def test_220p_telegram_pilot_weekly_report_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=220,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_weekly_report",
            command="/pilot_weekly_report",
        ),
        client=client,
        config=_config(),
        feedback_ledger_entries=(_feedback("useful", "suggestion-1"),),
        daily_loop_outcome_records=(_outcome("loop-1", "draft_created"),),
        usage_ledger_entries=(_usage("task-prep", "/prep", "prep", 0.004),),
        pilot_support_issues=(_issue(),),
        pilot_safety_incidents=(_safety(),),
    )

    assert "Pilot Weekly Report" in receipt.reply_text
    assert "Stage: 220P" in receipt.reply_text
    assert "- Loops run: 1" in receipt.reply_text
    assert "- Prep packs generated: 1" in receipt.reply_text
    assert "- Estimated cost: $0.004000" in receipt.reply_text
    assert "Local report only: yes" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_220p_reference_and_roadmap_close_weekly_report_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "220P adds `/pilot_weekly_report`" in reference
    assert "does not claim live analytics" in reference
    assert '"stage_id":"220P","stage_name":"Pilot Weekly Report v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "225P and later remain unauthorized" in roadmap
