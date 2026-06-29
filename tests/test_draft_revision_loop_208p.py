from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.draft_revision_loop import build_draft_revision_receipt, parse_draft_revision_argument, render_draft_revision_receipt
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DRAFT_REVISION_LOOP_208P_v0_1.md"
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
        bot_token="token-208p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_208p_builds_revision_receipt():
    assert parse_draft_revision_argument("draft-1 shorter") == ("draft-1", "shorter")
    receipt = build_draft_revision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id="draft-1",
        revision_request="remove_claims",
        source_trace_id="trace-208p",
    )

    assert receipt.stage == "208P"
    assert receipt.draft_id == "draft-1"
    assert receipt.revision_request == "remove_claims"
    assert receipt.approval_state == "pending_revision"
    assert receipt.source_trace_id == "trace-208p"
    assert receipt.revised_body_created is True
    assert receipt.gmail_send_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.external_write_allowed is False
    assert receipt.approval_gate_preserved is True


def test_208p_renders_revision_receipt():
    rendered = render_draft_revision_receipt(
        build_draft_revision_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            draft_id="draft-1",
            revision_request="spanish",
        )
    )

    assert "Draft Revision Loop" in rendered
    assert "Stage: 208P" in rendered
    assert "Revision: spanish" in rendered
    assert "Approval state: pending_revision" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_208p_rejects_unsupported_revision_or_authority_expansion():
    receipt = build_draft_revision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id="draft-1",
        revision_request="shorter",
    )

    with pytest.raises(ValueError, match="unsupported"):
        build_draft_revision_receipt(owner_id="local-owner", robot_id="roboticxs-dev", draft_id="draft-1", revision_request="send")
    with pytest.raises(ValueError, match="external write"):
        replace(receipt, gmail_send_allowed=True)


def test_208p_telegram_draft_revise_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=208,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/draft_revise draft-1 warmer",
            command="/draft_revise",
        ),
        client=client,
        config=_config(),
    )

    assert "Draft Revision Loop" in receipt.reply_text
    assert "Stage: 208P" in receipt.reply_text
    assert "Revision: warmer" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_208p_reference_and_roadmap_close_draft_revision_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "208P adds safe local draft revision requests" in reference
    assert "does not send Gmail" in reference
    assert '"stage_id":"208P","stage_name":"Draft Revision Loop v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "216P and later remain unauthorized" in roadmap
