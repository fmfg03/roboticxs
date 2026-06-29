from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.founder_feedback_capture import (
    FOUNDER_FEEDBACK_CAPTURE_STAGE,
    FOUNDER_FEEDBACK_CAPTURE_STATUS,
    SUPPORTED_FEEDBACK_TAGS,
    build_founder_feedback_capture_receipt,
    infer_feedback_item_type,
    parse_feedback_argument,
    render_feedback_usage,
    render_founder_feedback_capture_receipt,
)
from app.runnable_telegram_robot_mvp import (
    TelegramIncomingCommand,
    TelegramRobotConfig,
    handle_incoming_command,
    render_command_reply,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FOUNDER_FEEDBACK_CAPTURE_203P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, object] | None = None,
    ) -> dict:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


def _config() -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="token-203p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_203p_feedback_argument_parser_and_item_type_binding():
    assert parse_feedback_argument("missing_source prep-next source trace was absent") == (
        "missing_source",
        "prep-next",
        "source trace was absent",
    )
    assert parse_feedback_argument("useful founder-loop-today") == ("useful", "founder-loop-today", "")
    assert parse_feedback_argument(None) == ("", "", "")

    assert infer_feedback_item_type("founder-loop-today") == "founder_loop"
    assert infer_feedback_item_type("daily-brief-20260629") == "daily_brief"
    assert infer_feedback_item_type("prep-next") == "prep"
    assert infer_feedback_item_type("suggestion-001") == "suggestion"
    assert infer_feedback_item_type("draft-001") == "draft"
    assert infer_feedback_item_type("memory-001") == "memory"
    assert infer_feedback_item_type("document-review-001") == "document"


def test_203p_builds_local_non_persistent_feedback_receipt():
    receipt = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag="useful",
        item_id="founder-loop-today",
        comment="Good morning path.",
        source_trace_id="source-trace-001",
    )

    assert receipt.stage == FOUNDER_FEEDBACK_CAPTURE_STAGE
    assert receipt.status == FOUNDER_FEEDBACK_CAPTURE_STATUS
    assert receipt.tag == "useful"
    assert receipt.item_type == "founder_loop"
    assert receipt.comment == "Good morning path."
    assert receipt.source_trace_id == "source-trace-001"
    assert receipt.important_output_bound is True
    assert receipt.local_capture_only is True
    assert receipt.persisted is False
    assert receipt.gmail_send_allowed is False
    assert receipt.gmail_modify_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.crm_write_allowed is False
    assert receipt.whatsapp_allowed is False
    assert receipt.external_write_allowed is False
    assert receipt.secrets_redacted is True
    assert receipt.approval_gate_preserved is True


def test_203p_renders_customer_visible_feedback_receipt():
    rendered = render_founder_feedback_capture_receipt(
        build_founder_feedback_capture_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            tag="bad_draft",
            item_id="draft-001",
            comment="too generic",
        )
    )

    assert "Founder Feedback Capture" in rendered
    assert "Stage: 203P" in rendered
    assert "- Item: draft-001" in rendered
    assert "- Type: draft" in rendered
    assert "- Tag: bad_draft" in rendered
    assert "- Comment: too generic" in rendered
    assert "- Source trace: source_trace_not_provided" in rendered
    assert "- Local capture only: yes" in rendered
    assert "- Persisted ledger: no, 204P required" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_203p_rejects_unsupported_tags_unknown_items_and_authority_expansion():
    receipt = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag="wrong",
        item_id="prep-next",
    )

    with pytest.raises(ValueError, match="unsupported"):
        build_founder_feedback_capture_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            tag="delete",
            item_id="prep-next",
        )
    with pytest.raises(ValueError, match="important output"):
        build_founder_feedback_capture_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            tag="wrong",
            item_id="random-output",
        )
    with pytest.raises(ValueError, match="must not expand external write"):
        replace(receipt, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="non-persistent"):
        replace(receipt, persisted=True)


def test_203p_redacts_sensitive_feedback_comments():
    receipt = build_founder_feedback_capture_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        tag="wrong",
        item_id="prep-next",
        comment="password-like material",
    )

    assert receipt.comment == "[redacted-sensitive-comment]"


def test_203p_telegram_feedback_command_is_owner_gated_and_usage_safe():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=203,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/feedback missing_source prep-next missing Gmail source",
            command="/feedback",
        ),
        client=client,
        config=_config(),
    )

    assert "Founder Feedback Capture" in receipt.reply_text
    assert "Stage: 203P" in receipt.reply_text
    assert "- Tag: missing_source" in receipt.reply_text
    assert "- Item: prep-next" in receipt.reply_text
    assert "Local capture only: yes" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text

    usage = render_command_reply(command="/feedback", config=_config())
    assert usage == render_feedback_usage()
    assert "/feedback useful <item_id>" in usage
    assert ", ".join(SUPPORTED_FEEDBACK_TAGS) not in usage


def test_203p_reference_and_roadmap_close_feedback_capture_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "203P adds quick owner feedback capture" in reference
    assert "does not persist feedback" in reference
    assert "does not authorize Gmail send" in reference
    assert '"stage_id":"203P","stage_name":"Founder Feedback Capture v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "204P and later remain unauthorized" in roadmap
