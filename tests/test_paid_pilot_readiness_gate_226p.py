from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.daily_loop_outcome_tracker import build_daily_loop_outcome_record
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.first_friendly_user_activation import build_first_friendly_user_activation_receipt
from app.paid_pilot_readiness_gate import build_paid_pilot_readiness_gate, render_paid_pilot_readiness_gate
from app.pilot_learning_queue import build_pilot_learning_queue
from app.pilot_safety_incident_log import build_pilot_safety_incident
from app.pilot_support_issue_capture import build_pilot_support_issue_receipt
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.usage_cost_ledger import build_usage_cost_ledger_entry


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PAID_PILOT_READINESS_GATE_226P_v0_1.md"
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
        bot_token="token-226p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str, item_type: str = "suggestion", created_at: str = "2026-07-01T09:00:00Z") -> FeedbackLedgerEntry:
    return FeedbackLedgerEntry(
        stage="204P",
        feedback_id=f"fb-{tag}-{item_id}",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id=item_id,
        item_type=item_type,
        tag=tag,
        comment="local readiness signal",
        source_trace_id=f"trace-{item_id}",
        created_at=created_at,
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


def test_226p_returns_ready_for_paid_pilot_when_local_signals_pass():
    activation = build_first_friendly_user_activation_receipt(owner_id="local-owner", robot_id="roboticxs-dev")
    outcomes = tuple(
        build_daily_loop_outcome_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            loop_id=f"loop-{day}",
            outcome=outcome,
            created_at=f"2026-07-0{day}T09:00:00Z",
        )
        for day, outcome in (
            (1, "draft_created"),
            (2, "draft_approved"),
            (3, "suggestion_opened"),
            (4, "memory_approved"),
            (5, "document_reviewed"),
            (6, "draft_approved"),
            (7, "suggestion_opened"),
        )
    )
    feedback = (
        _feedback("useful", "suggestion-1", "suggestion", "2026-07-01T10:00:00Z"),
        _feedback("useful", "suggestion-2", "suggestion", "2026-07-02T10:00:00Z"),
        _feedback("useful", "draft-1", "draft", "2026-07-03T10:00:00Z"),
    )
    usage = (
        build_usage_cost_ledger_entry(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            task_id="usage-226",
            command="/founder_loop",
            task_class="daily_loop",
            provider="local",
            model="local",
            model_mode="Balanced",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.12,
            created_at="2026-06-30T09:00:00Z",
        ),
    )

    gate = build_paid_pilot_readiness_gate(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        activation_receipts=(activation,),
        feedback_entries=feedback,
        outcome_records=outcomes,
        usage_entries=usage,
    )

    assert gate.stage == "226P"
    assert gate.status == "local_paid_pilot_readiness_gate_v0"
    assert gate.decision == "READY_FOR_PAID_PILOT"
    assert gate.active_days == 7
    assert gate.activated_users == 1
    assert gate.useful_output_rate >= 0.6
    assert gate.cost_per_active_pilot_user_usd == 0.12
    assert gate.billing_enabled is False
    assert gate.payment_link_created is False
    assert gate.gmail_send_allowed is False
    assert gate.calendar_write_allowed is False
    assert gate.pilot_data_boundary_preserved is True


def test_226p_returns_ready_with_limitations_for_partial_local_signals():
    activation = build_first_friendly_user_activation_receipt(owner_id="local-owner", robot_id="roboticxs-dev")
    outcomes = tuple(
        build_daily_loop_outcome_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            loop_id=f"partial-{day}",
            outcome="suggestion_opened",
            created_at=f"2026-07-0{day}T09:00:00Z",
        )
        for day in (1, 2, 3)
    )

    gate = build_paid_pilot_readiness_gate(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        activation_receipts=(activation,),
        feedback_entries=(_feedback("useful", "suggestion-1"),),
        outcome_records=outcomes,
    )

    assert gate.decision == "READY_WITH_LIMITATIONS"
    assert "Watch checks:" in gate.reason
    assert any(check.status == "watch" for check in gate.checks)


def test_226p_returns_not_ready_for_missing_activation_or_safety_blocks():
    issue = build_pilot_support_issue_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="226001",
        command="/report_bug",
        severity="high",
        item_id="pilot-session",
        comment="high severity issue",
    )
    safety = build_pilot_safety_incident(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_user_id="226001",
        incident_type="missing_consent",
        command="/pilot_consent",
        item_id="consent-1",
        severity="high",
        reason="missing consent",
    )
    learning_queue = build_pilot_learning_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        issue_receipts=(issue,),
        safety_incidents=(safety,),
    )

    gate = build_paid_pilot_readiness_gate(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        issue_receipts=(issue,),
        safety_incidents=(safety,),
        learning_queue=learning_queue,
    )

    assert gate.decision == "NOT_READY"
    assert "Blocking checks:" in gate.reason
    assert gate.high_or_critical_issues == 1
    assert gate.safety_incidents == 1


def test_226p_renders_readiness_decision_and_safety_boundaries():
    rendered = render_paid_pilot_readiness_gate(
        build_paid_pilot_readiness_gate(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Paid Pilot Readiness Gate" in rendered
    assert "Stage: 226P" in rendered
    assert "Decision: NOT_READY" in rendered
    assert "Gate checks:" in rendered
    assert "- Billing enabled: no" in rendered
    assert "- Payment link created: no" in rendered
    assert "- External writes: disabled" in rendered
    assert "- Pilot data boundary: preserved" in rendered


def test_226p_rejects_billing_or_authority_expansion():
    gate = build_paid_pilot_readiness_gate(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="expand authority"):
        replace(gate, billing_enabled=True)
    with pytest.raises(ValueError, match="expand authority"):
        replace(gate, payment_link_created=True)
    with pytest.raises(ValueError, match="boundary"):
        replace(gate, pilot_data_boundary_preserved=False)


def test_226p_telegram_paid_pilot_gate_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=226,
            chat_id=226,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/paid_pilot_gate",
            command="/paid_pilot_gate",
        ),
        client=client,
        config=_config(),
    )

    assert "Paid Pilot Readiness Gate" in receipt.reply_text
    assert "Stage: 226P" in receipt.reply_text
    assert "Decision: NOT_READY" in receipt.reply_text
    assert "Billing enabled: no" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_226p_reference_and_roadmap_close_paid_pilot_gate_without_billing():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "226P adds `/paid_pilot_gate`" in reference
    assert "READY_FOR_PAID_PILOT" in reference
    assert "does not create payment links" in reference
    assert '"stage_id":"226P","stage_name":"Paid Pilot Readiness Gate v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
