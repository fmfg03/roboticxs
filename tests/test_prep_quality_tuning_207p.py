from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.feedback_ledger_tags import build_feedback_ledger_entry_from_capture
from app.founder_feedback_capture import build_founder_feedback_capture_receipt
from app.prep_quality_tuning import build_prep_quality_tuning_report, render_prep_quality_tuning_report
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PREP_QUALITY_TUNING_207P_v0_1.md"
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
        bot_token="token-207p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _feedback(tag: str, item_id: str = "prep-next"):
    return build_feedback_ledger_entry_from_capture(
        build_founder_feedback_capture_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            tag=tag,
            item_id=item_id,
            source_trace_id="trace-207p",
        ),
        created_at="2026-06-30T02:00:00Z",
    )


def test_207p_builds_prep_quality_findings_from_feedback():
    report = build_prep_quality_tuning_report(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        feedback_entries=(
            _feedback("missing_context", "prep-1"),
            _feedback("bad_next_step", "prep-2"),
            _feedback("wrong_context", "prep-3"),
            _feedback("too_verbose", "prep-4"),
        ),
    )

    findings = {finding.prep_id: finding for finding in report.findings}
    assert findings["prep-1"].action == "require_source_review"
    assert findings["prep-2"].action == "rewrite_next_step"
    assert findings["prep-3"].action == "block_stale_prep"
    assert findings["prep-4"].action == "tighten"
    assert report.feedback_entries_used == 4
    assert report.local_tuning_only is True
    assert report.external_write_allowed is False


def test_207p_renders_prep_quality_report():
    rendered = render_prep_quality_tuning_report(
        build_prep_quality_tuning_report(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            feedback_entries=(_feedback("weak_agenda"),),
        )
    )

    assert "Prep Quality Tuning" in rendered
    assert "Stage: 207P" in rendered
    assert "prep-next: tighten" in rendered
    assert "weak_agenda" in rendered
    assert "Local tuning only: yes" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered


def test_207p_rejects_authority_expansion():
    report = build_prep_quality_tuning_report(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="local only"):
        replace(report, external_write_allowed=True)
    with pytest.raises(ValueError, match="connector write"):
        replace(report, calendar_write_allowed=True)


def test_207p_telegram_prep_quality_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=207,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/prep_quality",
            command="/prep_quality",
        ),
        client=client,
        config=_config(),
        feedback_ledger_entries=(_feedback("bad_risk"),),
    )

    assert "Prep Quality Tuning" in receipt.reply_text
    assert "Stage: 207P" in receipt.reply_text
    assert "require_source_review" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_207p_reference_and_roadmap_close_prep_quality_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "207P adds local quality feedback hooks" in reference
    assert "does not rewrite live prep automatically" in reference
    assert '"stage_id":"207P","stage_name":"Prep Quality Tuning v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "224P and later remain unauthorized" in roadmap
