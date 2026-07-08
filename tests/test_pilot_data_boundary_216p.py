from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_data_boundary import (
    PilotDataBoundaryItem,
    build_pilot_data_boundary_report,
    render_pilot_data_boundary,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_DATA_BOUNDARY_216P_v0_1.md"
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
        bot_token="token-216p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def boundary_item(item_type: str, **overrides) -> PilotDataBoundaryItem:
    values = {
        "item_id": f"{item_type}-1",
        "item_type": item_type,
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "scope_label": "owner_robot_scoped",
    }
    values.update(overrides)
    return PilotDataBoundaryItem(**values)


def test_216p_builds_ready_boundary_report_for_scoped_items():
    items = tuple(boundary_item(item_type) for item_type in (
        "memory",
        "approval",
        "draft",
        "feedback",
        "usage",
        "source_trace",
        "gmail_trace",
        "document_trace",
    ))

    report = build_pilot_data_boundary_report(owner_id="local-owner", robot_id="roboticxs-dev", items=items)

    assert report.stage == "216P"
    assert report.status == "local_scope_boundary_v0"
    assert report.scoped_items == 8
    assert report.cross_scope_items == ()
    assert report.memory_scoped is True
    assert report.approvals_scoped is True
    assert report.drafts_scoped is True
    assert report.feedback_scoped is True
    assert report.usage_scoped is True
    assert report.source_traces_scoped is True
    assert report.gmail_traces_scoped is True
    assert report.document_traces_scoped is True
    assert report.local_report_only is True
    assert report.data_migration_allowed is False


def test_216p_reports_cross_scope_items_without_mutation():
    report = build_pilot_data_boundary_report(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        items=(
            boundary_item("memory"),
            boundary_item("draft", owner_id="other-owner", scope_label="cross_owner"),
        ),
    )
    rendered = render_pilot_data_boundary(report)

    assert report.scoped_items == 1
    assert len(report.cross_scope_items) == 1
    assert report.drafts_scoped is False
    assert "Boundary health: blocked_cross_scope_items" in rendered
    assert "Cross-scope findings:" in rendered
    assert "draft draft-1 owner=other-owner" in rendered
    assert "Data migration: disabled" in rendered


def test_216p_rejects_boundary_write_authority():
    report = build_pilot_data_boundary_report(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="write authority"):
        replace(report, data_migration_allowed=True)
    with pytest.raises(ValueError, match="write authority"):
        replace(report, external_write_allowed=True)
    with pytest.raises(ValueError, match="write authority"):
        replace(report, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="write authority"):
        replace(report, calendar_write_allowed=True)


def test_216p_telegram_boundary_command_is_visible():
    client = FakeTelegramClient()
    config = _config()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=216,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_boundary",
            command="/pilot_boundary",
        ),
        client=client,
        config=config,
        pilot_boundary_items=(
            boundary_item("memory"),
            boundary_item("usage"),
        ),
    )

    assert "Pilot Data Boundary" in receipt.reply_text
    assert "Items checked: 2" in receipt.reply_text
    assert "Boundary health: ready_local" in receipt.reply_text
    assert "Local report only: yes" in receipt.reply_text
    assert len(client.sent_messages) == 1


def test_216p_reference_and_roadmap_close_boundary_without_migration():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "216P adds local owner/robot data-boundary visibility" in reference
    assert "does not move, delete, merge, or mutate data" in reference
    assert '"stage_id":"216P","stage_name":"Pilot Data Boundary v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "223P and later remain unauthorized" in roadmap
