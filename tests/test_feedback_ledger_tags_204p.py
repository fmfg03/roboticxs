from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.feedback_ledger_tags import (
    FEEDBACK_LEDGER_TAGS_STAGE,
    FEEDBACK_LEDGER_TAGS_STATUS,
    build_feedback_ledger,
    build_feedback_ledger_entry_from_capture,
    render_feedback_ledger,
)
from app.founder_feedback_capture import build_founder_feedback_capture_receipt
from app.runnable_telegram_robot_mvp import (
    TelegramIncomingCommand,
    TelegramRobotConfig,
    handle_incoming_command,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FEEDBACK_LEDGER_TAGS_204P_v0_1.md"
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
        bot_token="token-204p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _entry(tag: str = "useful", item_id: str = "founder-loop-today"):
    receipt = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag=tag,
        item_id=item_id,
        comment="good signal",
        source_trace_id="trace-204p",
    )
    return build_feedback_ledger_entry_from_capture(receipt, created_at="2026-06-29T22:00:00Z")


def test_204p_builds_feedback_ledger_entry_from_capture():
    entry = _entry()

    assert entry.stage == FEEDBACK_LEDGER_TAGS_STAGE
    assert entry.feedback_id == "fb-founder_loop-founder-loop-today-useful"
    assert entry.item_type == "founder_loop"
    assert entry.tag == "useful"
    assert entry.comment == "good signal"
    assert entry.source_trace_id == "trace-204p"
    assert entry.created_at == "2026-06-29T22:00:00Z"
    assert entry.status == "recorded"
    assert entry.storage_scope == "local_structured_ledger"
    assert entry.gmail_send_allowed is False
    assert entry.calendar_write_allowed is False
    assert entry.crm_write_allowed is False
    assert entry.whatsapp_allowed is False
    assert entry.external_write_allowed is False
    assert entry.secrets_redacted is True
    assert entry.approval_gate_preserved is True


def test_204p_ledger_filters_owner_robot_and_counts_tags():
    entries = (
        _entry("useful", "founder-loop-today"),
        _entry("missing_source", "prep-next"),
        replace(_entry("wrong", "draft-001"), owner_id="other-owner"),
    )

    ledger = build_feedback_ledger(owner_id="local-owner", robot_id="roboticxs-dev", entries=entries)

    assert ledger.stage == FEEDBACK_LEDGER_TAGS_STAGE
    assert ledger.status == FEEDBACK_LEDGER_TAGS_STATUS
    assert ledger.total_entries == 2
    assert ledger.top_tags == (("missing_source", 1), ("useful", 1))
    assert ledger.storage_scope == "local_structured_ledger"
    assert ledger.retrieval_available is True
    assert ledger.external_write_allowed is False
    assert ledger.secrets_redacted is True


def test_204p_renders_feedback_ledger_and_empty_state():
    rendered = render_feedback_ledger(
        build_feedback_ledger(owner_id="local-owner", robot_id="roboticxs-dev", entries=(_entry(),))
    )
    empty = render_feedback_ledger(build_feedback_ledger(owner_id="local-owner", robot_id="roboticxs-dev"))

    assert "Feedback Ledger" in rendered
    assert "Stage: 204P" in rendered
    assert "Entries: 1" in rendered
    assert "- useful: 1" in rendered
    assert "fb-founder_loop-founder-loop-today-useful" in rendered
    assert "Retrieval: available" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "- No local feedback entries injected yet." in empty


def test_204p_rejects_authority_expansion():
    entry = _entry()

    with pytest.raises(ValueError, match="must not expand external write"):
        replace(entry, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="local structured storage"):
        replace(entry, storage_scope="external")


def test_204p_telegram_feedback_ledger_is_customer_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=204,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/feedback_ledger",
            command="/feedback_ledger",
        ),
        client=client,
        config=_config(),
        feedback_ledger_entries=(_entry(),),
    )

    assert "Feedback Ledger" in receipt.reply_text
    assert "Stage: 204P" in receipt.reply_text
    assert "Entries: 1" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_204p_reference_and_roadmap_close_feedback_ledger_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "204P turns captured feedback into local structured ledger entries" in reference
    assert "does not authorize Gmail send" in reference
    assert '"stage_id":"204P","stage_name":"Feedback Ledger & Tags v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "207P and later remain unauthorized" in roadmap
