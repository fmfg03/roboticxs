from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

import pytest

from app.action_draft_queue import build_action_draft_queue
from app.calendar_context_scan import build_calendar_context_scan_record
from app.fast_path_cache import build_fast_path_cache_entry
from app.google_calendar_readonly_connector import CalendarReadResult
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.runnable_telegram_robot_mvp import (
    DEFAULT_ROBOT_ID,
    TelegramBotApiClient,
    TelegramIncomingCommand,
    TelegramRobotConfig,
    TelegramRobotConfigError,
    build_menu_reply_markup,
    build_telegram_robot_startup_report,
    handle_incoming_command,
    load_telegram_robot_config_from_env,
    main,
    parse_telegram_incoming_command,
    render_brief_command_reply,
    render_help_command_reply,
    render_menu_command_reply,
    render_miss_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    render_unauthorized_reply,
    render_unknown_command_reply,
    resolve_prep_suggestion_id,
    run_polling_loop,
    run_polling_once,
    validate_telegram_robot_config,
)
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle
from app.memory_center_projection import MemoryCenterItem
from app.usage_cost_ledger import build_usage_cost_ledger_entry
from app.user_confirmation_runtime import build_user_confirmation_receipt
from app.user_approved_output_queue import build_user_approved_output_item


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/runnable_telegram_robot_mvp.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self, updates_batches: list[list[dict]] | None = None) -> None:
        self._updates_batches = list(updates_batches or [])
        self.get_updates_calls: list[dict[str, int | None]] = []
        self.sent_messages: list[dict[str, object]] = []

    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
        self.get_updates_calls.append(
            {"offset": offset, "timeout": timeout, "limit": limit}
        )
        if self._updates_batches:
            return self._updates_batches.pop(0)
        return []

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


class LegacyTelegramClient(FakeTelegramClient):
    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
        }
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


class FakeCalendarHttpClient:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {
            "items": [
                {
                    "id": "evt-client-demo",
                    "summary": "Client demo prep meeting",
                    "start": {"dateTime": "2026-06-25T10:00:00-06:00"},
                    "end": {"dateTime": "2026-06-25T10:30:00-06:00"},
                    "location": "Google Meet",
                    "description": "Review proposal context and prepare open questions.",
                    "organizer": {"email": "owner@example.com"},
                    "attendees": [{"email": "client@example.com"}],
                    "htmlLink": "https://calendar.google.com/event?eid=1",
                }
            ]
        }
        self.calls: list[dict[str, object]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.payload


class FakeGmailReadonlyHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout_seconds": timeout_seconds,
            }
        )
        if url.endswith("/messages"):
            return {"messages": [{"id": "msg-183p", "threadId": "thr-183p"}]}
        return {
            "id": "msg-183p",
            "threadId": "thr-183p",
            "labelIds": ["INBOX"],
            "snippet": "Please review the proposal before tomorrow's meeting and follow up.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Client proposal prep"},
                    {"name": "From", "value": "client@example.com"},
                    {"name": "Date", "value": "Thu, 25 Jun 2026 10:00:00 -0600"},
                ],
                "parts": [
                    {
                        "filename": "proposal.pdf",
                        "body": {"attachmentId": "att-183p"},
                    }
                ],
            },
        }


class FailingGmailReadonlyHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout_seconds": timeout_seconds,
            }
        )
        raise OSError("gmail unavailable")


class FakeGmailDraftHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: dict,
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return {"id": "draft-telegram-185p", "message": {"id": "msg-telegram-185p"}}


def build_command_update(
    *,
    update_id: int = 9001,
    chat_id: int = 4004,
    telegram_user_id: int = 111111111,
    message_id: int = 123,
    text: str = "/status",
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": telegram_user_id, "is_bot": False},
            "text": text,
        },
    }


def build_document_update(
    *,
    update_id: int = 9101,
    chat_id: int = 4004,
    telegram_user_id: int = 111111111,
    message_id: int = 124,
    file_id: str = "telegram-file-186p",
) -> dict:
    update = build_command_update(
        update_id=update_id,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        message_id=message_id,
        text="",
    )
    message = update["message"]
    message.pop("text", None)
    message["document"] = {
        "file_id": file_id,
        "file_unique_id": "unique-file-186p",
        "file_name": "vendor-agreement.pdf",
        "mime_type": "application/pdf",
        "file_size": 12055,
    }
    return update


def build_valid_config() -> TelegramRobotConfig:
    return validate_telegram_robot_config(
        load_telegram_robot_config_from_env(
            env={
                "ROBOTICXS_TELEGRAM_BOT_TOKEN": "token-123",
                "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111,222222222",
                "ROBOTICXS_TELEGRAM_DEV_MODE": "true",
            }
        )
    )


def active_memory(**overrides) -> MemoryCenterItem:
    values = {
        "item_id": "mem-today-telegram",
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "memory_kind": "preference",
        "status": "active",
        "scopes": ("telegram", "general"),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context",),
        "skill_ids": (),
        "content": "Francisco prefers compact daily briefings.",
        "bounded_summary": "Francisco prefers compact daily briefings.",
        "source": "local_fixture",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


@dataclass(frozen=True, slots=True)
class PendingProposalFixture:
    proposal_id: str = "proposal-loop-telegram"
    owner_id: str = "local-owner"
    robot_id: str = "roboticxs-dev"
    proposal_type: str = "memory_preference"
    proposed_memory_text: str = "Francisco prefers compact loop reviews."
    confidence: str = "medium"
    review_reason: str = "Explicitly stated in a local planning thread."
    source_stage: str = "142P"
    status: str = "pending_user_review"


def approved_confirmation_fixture():
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-telegram-185p",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="email_thread_no_followup",
                title="Draft Telegram Gmail export",
                summary="thread needs follow-up",
                source_refs=("gmail:thread-telegram-185p",),
            ),
        ),
    )
    inbox = build_suggestion_inbox(owner_id="local-owner", robot_id="roboticxs-dev", suggestions=suggestions)
    decision = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=inbox.items[0].suggestion_id,
        choice="create_draft",
        inbox=inbox,
    )
    queue = build_action_draft_queue(owner_id="local-owner", robot_id="roboticxs-dev", decisions=(decision,))
    return build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=queue.drafts[0].draft_id,
        choice="approve",
        queue=queue,
    )


def test_130p_config_loads_from_environment_variables():
    config = load_telegram_robot_config_from_env(
        env={
            "ROBOTICXS_TELEGRAM_BOT_TOKEN": "abc",
            "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111,222222222",
            "ROBOTICXS_ROBOT_ID": "roboticxs-francisco",
            "ROBOTICXS_OWNER_ID": "francisco",
            "ROBOTICXS_TELEGRAM_POLL_TIMEOUT_SECONDS": "45",
            "ROBOTICXS_TELEGRAM_POLL_LIMIT": "7",
            "ROBOTICXS_TELEGRAM_DRY_RUN": "false",
            "ROBOTICXS_TELEGRAM_DEV_MODE": "true",
        }
    )

    assert config.bot_token == "abc"
    assert config.owner_ids == frozenset({111111111, 222222222})
    assert config.robot_id == "roboticxs-francisco"
    assert config.owner_id == "francisco"
    assert config.poll_timeout_seconds == 45
    assert config.poll_limit == 7
    assert config.dry_run is False
    assert config.dev_mode is True


def test_130p_missing_bot_token_fails_closed_in_live_mode():
    config = load_telegram_robot_config_from_env(
        env={"ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111"}
    )

    with pytest.raises(TelegramRobotConfigError, match="rejected_missing_bot_token"):
        validate_telegram_robot_config(config)


def test_130p_missing_owner_allowlist_fails_closed_in_live_mode():
    config = load_telegram_robot_config_from_env(
        env={"ROBOTICXS_TELEGRAM_BOT_TOKEN": "abc"}
    )

    with pytest.raises(
        TelegramRobotConfigError,
        match="rejected_missing_owner_allowlist",
    ):
        validate_telegram_robot_config(config)


def test_130p_owner_allowlist_parses_one_owner_id():
    config = load_telegram_robot_config_from_env(
        env={
            "ROBOTICXS_TELEGRAM_BOT_TOKEN": "abc",
            "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111",
        }
    )

    assert config.owner_ids == frozenset({111111111})


def test_130p_owner_allowlist_parses_multiple_owner_ids():
    config = load_telegram_robot_config_from_env(
        env={
            "ROBOTICXS_TELEGRAM_BOT_TOKEN": "abc",
            "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111, 222222222,333333333",
        }
    )

    assert config.owner_ids == frozenset({111111111, 222222222, 333333333})


def test_130p_parser_extracts_chat_user_message_and_command():
    incoming = parse_telegram_incoming_command(
        build_command_update(text="/status@RoboticxsBot details")
    )

    assert incoming == TelegramIncomingCommand(
        update_id=9001,
        chat_id=4004,
        telegram_user_id=111111111,
        message_id=123,
        command="/status",
        raw_text="/status@RoboticxsBot details",
    )


def test_130p_start_from_authorized_owner_produces_deterministic_online_response():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/start"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert receipt.reply_text == render_start_command_reply(config)
    assert "Premium control shell" in receipt.reply_text
    assert "Access: owner-gated" in receipt.reply_text
    assert "Command Center" in receipt.reply_text
    assert "Work Queue" in receipt.reply_text
    assert "Action: /today or /daily_brief" in receipt.reply_text
    assert "Action: /suggestions" in receipt.reply_text
    assert "I do not take external actions without approval." in receipt.reply_text


def test_130p_help_from_authorized_owner_produces_deterministic_command_list():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/help"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.reply_text == render_help_command_reply()
    assert "/status" in receipt.reply_text
    assert "/checkup" in receipt.reply_text
    assert "/setup" in receipt.reply_text
    assert "/miss" in receipt.reply_text
    assert "/today" in receipt.reply_text
    assert "/daily_brief" in receipt.reply_text
    assert "/demo" in receipt.reply_text
    assert "Roboticxs Command Center" in receipt.reply_text
    assert "Daily Flow" in receipt.reply_text
    assert "Review Flow" in receipt.reply_text
    assert "/brief" in receipt.reply_text
    assert "/suggest_brief" in receipt.reply_text
    assert "/suggestions" in receipt.reply_text
    assert "/approvals" in receipt.reply_text
    assert "/approve <id>" in receipt.reply_text
    assert "/reject <id>" in receipt.reply_text
    assert "/drafts" in receipt.reply_text
    assert "/draft_approve" in receipt.reply_text
    assert "/export_text" in receipt.reply_text
    assert "/memory" in receipt.reply_text
    assert "/memory_limits" in receipt.reply_text
    assert "/memory_pending" in receipt.reply_text
    assert "Skill gates:" in receipt.reply_text
    assert "- Gmail Drafts:" in receipt.reply_text
    assert "/brief is not enabled yet." not in receipt.reply_text




def test_rqf_019r_menu_alias_matches_help_shell_without_new_authority():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/menu"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert receipt.command == "/menu"
    assert receipt.reply_text == render_menu_command_reply()
    assert "Roboticxs Menu" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_rqf_025r_menu_sends_enriched_keyboard_without_new_authority():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/menu"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert receipt.reply_text == render_menu_command_reply()
    assert receipt.api_receipt["result"]["reply_markup"] == build_menu_reply_markup()
    assert client.sent_messages[0]["reply_markup"] == build_menu_reply_markup()
    assert "/today" in receipt.reply_text
    assert "/prep" in receipt.reply_text
    assert "/suggestions" in receipt.reply_text
    assert "/approvals" in receipt.reply_text
    assert "/drafts" in receipt.reply_text
    assert "/memory" in receipt.reply_text
    assert "/usage" in receipt.reply_text
    assert "/status" in receipt.reply_text
    assert "/memory_approve" not in receipt.reply_text
    assert "No sends." in receipt.reply_text
    assert "No Calendar writes." in receipt.reply_text
    assert "No Gmail writes." in receipt.reply_text
    assert "Drafts and memory changes require approval." in receipt.reply_text
    assert "callback_data" not in str(receipt.api_receipt)
    assert "Calendar writes: enabled" not in receipt.reply_text
    assert "Gmail writes: enabled" not in receipt.reply_text


def test_rqf_025r_menu_falls_back_for_legacy_clients_without_reply_markup():
    config = build_valid_config()
    client = LegacyTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/menu"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert receipt.reply_text == render_menu_command_reply()
    assert "reply_markup" not in receipt.api_receipt["result"]
    assert "Roboticxs Menu" in receipt.reply_text


def test_rqf_025r_bot_api_client_serializes_menu_reply_markup_without_callbacks(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple[str, dict[str, object]]] = []
    api_client = TelegramBotApiClient(bot_token="token-rqf-025r")

    def fake_post(method: str, payload: dict[str, object]) -> dict:
        calls.append((method, payload))
        return {"ok": True, "result": payload}

    monkeypatch.setattr(api_client, "_post", fake_post)

    receipt = api_client.send_message(
        4004,
        render_menu_command_reply(),
        reply_to_message_id=123,
        reply_markup=build_menu_reply_markup(),
    )

    assert calls[0][0] == "sendMessage"
    payload = calls[0][1]
    assert payload["chat_id"] == 4004
    assert payload["reply_to_message_id"] == 123
    markup = json.loads(payload["reply_markup"])
    assert markup["keyboard"][0][0]["text"] == "/today"
    assert markup["keyboard"][0][1]["text"] == "/prep"
    assert markup["keyboard"][1][1]["text"] == "/approvals"
    assert "callback_data" not in payload["reply_markup"]
    assert receipt["result"] == payload


def test_rqf_027r_approvals_command_returns_empty_state_without_external_actions():
    config = build_valid_config()
    client = FakeTelegramClient()
    gmail_draft_client = FakeGmailDraftHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/approvals"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        gmail_draft_http_client=gmail_draft_client,
    )

    assert receipt.authorized is True
    assert receipt.command == "/approvals"
    assert "Approvals" in receipt.reply_text
    assert "Status: empty" in receipt.reply_text
    assert "No pending approvals." in receipt.reply_text
    assert "Approve means record local approval; it does not execute." in receipt.reply_text
    assert "Email send: disabled" in receipt.reply_text
    assert "Gmail draft creation: disabled" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "External API writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text
    assert gmail_draft_client.calls == []


def test_rqf_027r_approvals_command_lists_pending_items():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/approvals"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        approval_items=(
            build_user_approved_output_item(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                output_type="email_reply",
                title="Follow up with client",
                body_preview="Thanks for the meeting. Here are the next steps.",
                approval_id="approval-027r",
            ),
        ),
    )

    assert "Pending approvals: 1" in receipt.reply_text
    assert "approval-027r | email_reply | pending_user_approval" in receipt.reply_text
    assert "Follow up with client" in receipt.reply_text


def test_rqf_027r_approve_records_local_receipt_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    gmail_client = FakeGmailReadonlyHttpClient()
    gmail_draft_client = FakeGmailDraftHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/approve approval-027r"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        gmail_http_client=gmail_client,
        gmail_draft_http_client=gmail_draft_client,
        approval_items=(
            build_user_approved_output_item(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                output_type="email_reply",
                title="Follow up with client",
                body_preview="Thanks for the meeting. Here are the next steps.",
                approval_id="approval-027r",
            ),
        ),
    )

    assert receipt.command == "/approve"
    assert "Approval Receipt" in receipt.reply_text
    assert "Status: approved_local_receipt" in receipt.reply_text
    assert "Approved locally." in receipt.reply_text
    assert "No email sent." in receipt.reply_text
    assert "No Gmail draft created." in receipt.reply_text
    assert "No calendar event created." in receipt.reply_text
    assert "No external action performed." in receipt.reply_text
    assert "Receipt recorded." in receipt.reply_text
    assert calendar_client.calls == []
    assert gmail_client.calls == []
    assert gmail_draft_client.calls == []


def test_rqf_027r_reject_records_local_receipt_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/reject approval-027r"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        approval_items=(
            build_user_approved_output_item(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                output_type="email_reply",
                title="Follow up with client",
                body_preview="Thanks for the meeting. Here are the next steps.",
                approval_id="approval-027r",
            ),
        ),
    )

    assert receipt.command == "/reject"
    assert "Status: rejected_local_receipt" in receipt.reply_text
    assert "Decision recorded locally." in receipt.reply_text
    assert "No email sent." in receipt.reply_text
    assert "No external action performed." in receipt.reply_text


def test_rqf_027r_invalid_approval_id_fails_closed_in_telegram():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/approve missing-approval"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        approval_items=(
            build_user_approved_output_item(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                output_type="email_reply",
                title="Follow up with client",
                body_preview="Thanks for the meeting. Here are the next steps.",
                approval_id="approval-027r",
            ),
        ),
    )

    assert "Status: blocked_approval_not_found" in receipt.reply_text
    assert "No approval decision was applied." in receipt.reply_text
    assert "No email sent." in receipt.reply_text
    assert "No external action performed." in receipt.reply_text


def test_130p_status_from_authorized_owner_produces_deterministic_runtime_status():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/status"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.reply_text == render_status_command_reply(config)
    assert f"Robot: {DEFAULT_ROBOT_ID}" in receipt.reply_text
    assert "Access: owner-gated" in receipt.reply_text
    assert "Dev/sandbox mode: enabled" in receipt.reply_text
    assert "Telegram replies: enabled" in receipt.reply_text
    assert "Calendar reads require read-only Google setup." in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Gmail writes: disabled" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "Tool execution: disabled" in receipt.reply_text
    assert "Automatic Memory Center mutation: disabled" in receipt.reply_text
    assert "Scheduler/proactive outbound: disabled" in receipt.reply_text
    assert "Task Inbox is your robot task inbox, not your Gmail inbox yet." in receipt.reply_text
    assert "Live connector readiness:" in receipt.reply_text
    assert "- Full check: /checkup" in receipt.reply_text
    assert "Roadmap: 95P-191P closed, Premium Telegram UX Shell v0 active" in receipt.reply_text
    assert "Premium Telegram UX Shell: active" in receipt.reply_text
    assert "Skill Manifest Runtime Gates: active" in receipt.reply_text


def test_181p_checkup_command_returns_live_connector_readiness_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/checkup"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Live Connector Readiness" in receipt.reply_text
    assert "Stage: 181P" in receipt.reply_text
    assert "Calendar read-only:" in receipt.reply_text
    assert "Gmail context:" in receipt.reply_text
    assert "Secrets: redacted" in receipt.reply_text
    assert "Connector activation: disabled" in receipt.reply_text
    assert "Gmail draft creation: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "No connector was activated." in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_181p_setup_alias_returns_live_connector_readiness_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/setup"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Live Connector Readiness" in receipt.reply_text
    assert "Stage: 181P" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_171p_suggestions_command_returns_owner_requested_local_inbox():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/suggestions"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Suggestion Inbox" in receipt.reply_text
    assert "Stage: 171P" in receipt.reply_text
    assert "Status: 0 pending suggestion(s)" in receipt.reply_text
    assert "No pending suggestions in the local inbox." in receipt.reply_text
    assert "No action has been taken." in receipt.reply_text
    assert "Decision flow: disabled" in receipt.reply_text
    assert "Draft creation: disabled" in receipt.reply_text
    assert "Memory writes: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_172p_suggestion_decision_command_returns_local_receipt_without_execution():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/suggestion_draft suggestion-1"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Suggestion Decision" in receipt.reply_text
    assert "Stage: 172P" in receipt.reply_text
    assert "Suggestion id: suggestion-1" in receipt.reply_text
    assert "Choice: create_draft" in receipt.reply_text
    assert "Status: blocked_suggestion_not_found" in receipt.reply_text
    assert "No action has been taken." in receipt.reply_text
    assert "Draft created: false" in receipt.reply_text
    assert "Memory written: false" in receipt.reply_text
    assert "Snooze scheduled: false" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_177p_drafts_command_returns_local_action_draft_queue_without_execution():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/drafts"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Action Draft Queue" in receipt.reply_text
    assert "Stage: 177P" in receipt.reply_text
    assert "Status: empty" in receipt.reply_text
    assert "No pending local drafts." in receipt.reply_text
    assert "Local draft records: enabled" in receipt.reply_text
    assert "User confirmation required: true" in receipt.reply_text
    assert "Gmail draft creation: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Task persistence: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_178p_draft_confirmation_command_returns_local_receipt_without_execution():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/draft_approve draft-1"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "User Confirmation Receipt" in receipt.reply_text
    assert "Stage: 178P" in receipt.reply_text
    assert "Draft id: draft-1" in receipt.reply_text
    assert "Choice: approve" in receipt.reply_text
    assert "Status: blocked_draft_not_found" in receipt.reply_text
    assert "Action executed: false" in receipt.reply_text
    assert "Approved output export: disabled" in receipt.reply_text
    assert "Gmail draft creation: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_179p_export_command_returns_local_payload_receipt_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/export_text confirmation-1"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Approved Output Export" in receipt.reply_text
    assert "Stage: 179P" in receipt.reply_text
    assert "Confirmation id: confirmation-1" in receipt.reply_text
    assert "Format: text" in receipt.reply_text
    assert "Status: blocked_confirmation_not_found" in receipt.reply_text
    assert "Local export payload created: false" in receipt.reply_text
    assert "Gmail draft creation: disabled" in receipt.reply_text
    assert "Local file write: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_185p_export_email_creates_approved_gmail_draft_without_sending(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", "gmail-token-telegram-185p")
    config = build_valid_config()
    client = FakeTelegramClient()
    gmail_draft_client = FakeGmailDraftHttpClient()
    confirmation = approved_confirmation_fixture()
    incoming = parse_telegram_incoming_command(build_command_update(text=f"/export_email {confirmation.confirmation_id}"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        gmail_draft_http_client=gmail_draft_client,
        confirmation_receipts=(confirmation,),
    )

    assert receipt.authorized is True
    assert len(gmail_draft_client.calls) == 1
    assert "Approved Gmail Draft Creation" in receipt.reply_text
    assert "Stage: 185P" in receipt.reply_text
    assert "Status: gmail_draft_created" in receipt.reply_text
    assert "Gmail draft id: draft-telegram-185p" in receipt.reply_text
    assert "Gmail draft created: true" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Gmail modify/archive/label: disabled" in receipt.reply_text
    assert "Gmail delete: disabled" in receipt.reply_text
    assert "No email was sent." in receipt.reply_text
    for forbidden in ("gmail-token-telegram-185p", "Authorization", "Bearer"):
        assert forbidden not in receipt.reply_text


def test_186p_document_command_renders_v1_when_local_text_is_injected():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_document_update(file_id="telegram-file-186p"))
    assert incoming is not None

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        document_extracted_text_by_file_id={
            "telegram-file-186p": (
                "This vendor agreement requires written approval before subcontractor sharing. "
                "Payment fees must be reviewed before renewal. Confidential information must remain private."
            )
        },
    )

    assert receipt.command == "/document"
    assert receipt.authorized is True
    assert "Document Review Pack v1" in receipt.reply_text
    assert "Stage: 186P" in receipt.reply_text
    assert "Executive summary:" in receipt.reply_text
    assert "Risks / unclear points:" in receipt.reply_text
    assert "Questions to ask:" in receipt.reply_text
    assert "Draft-only review. Not legal, tax, financial, medical, or professional advice." in receipt.reply_text
    assert "File downloaded: false" in receipt.reply_text
    assert "OCR used: false" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "Signature or acceptance: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_180p_demo_command_returns_customer_mvp_demo_pack_without_external_writes():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/demo"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Customer MVP Demo Pack v1" in receipt.reply_text
    assert "Stage: 180P" in receipt.reply_text
    assert "/today" in receipt.reply_text
    assert "/prep" in receipt.reply_text
    assert "/suggestion_draft" in receipt.reply_text
    assert "/draft_approve" in receipt.reply_text
    assert "/export_text" in receipt.reply_text
    assert "Telegram API called: false" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_190p_pilot_command_returns_controlled_live_pilot_receipt_without_send_authority():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/pilot"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Controlled Live Pilot Baseline" in receipt.reply_text
    assert "Stage: 190P" in receipt.reply_text
    assert "/daily_brief" in receipt.reply_text
    assert "/prep" in receipt.reply_text
    assert "/suggestion_draft" in receipt.reply_text
    assert "/draft_approve" in receipt.reply_text
    assert "/export_email" in receipt.reply_text
    assert "Source Trace Receipt" in receipt.reply_text
    assert "Usage & Cost Ledger" in receipt.reply_text
    assert "No email was sent." in receipt.reply_text
    assert "No external irreversible action was taken." in receipt.reply_text


def test_130p_unknown_command_from_authorized_owner_produces_safe_fallback():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/unknown"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert "I do not know that command yet." in receipt.reply_text
    assert "Skill Runtime Gate" in receipt.reply_text
    assert "Decision: REFUSE_SCOPE" in receipt.reply_text
    assert "Execution authorized: false" in receipt.reply_text
    assert "Use /help to see the Roboticxs menu." in receipt.reply_text
    assert "Setup Check: /status, /checkup, /setup" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_130p_unauthorized_user_receives_safe_private_bot_response():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/status")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert "Access: owner-gated" not in receipt.reply_text
    assert "Roadmap:" not in receipt.reply_text


def test_130p_command_routing_is_owner_gated():
    config = build_valid_config()
    client = FakeTelegramClient(
        updates_batches=[
            [
                build_command_update(telegram_user_id=111111111, text="/status"),
                build_command_update(update_id=9002, telegram_user_id=999999999, text="/status"),
            ]
        ]
    )

    result = run_polling_once(client=client, config=config)

    assert result.processed_update_ids == (9001, 9002)
    assert len(result.receipts) == 2
    assert result.receipts[0].authorized is True
    assert result.receipts[1].authorized is False
    assert result.receipts[1].reply_text == render_unauthorized_reply()


def test_130p_bot_sends_replies_through_injected_fake_client():
    config = build_valid_config()
    client = FakeTelegramClient(
        updates_batches=[[build_command_update(text="/help")]]
    )

    run_polling_once(client=client, config=config)

    assert client.sent_messages == [
        {
            "chat_id": 4004,
            "text": render_help_command_reply(),
            "reply_to_message_id": 123,
        }
    ]


def test_130p_polling_loop_handles_empty_updates_without_crashing():
    config = build_valid_config()
    client = FakeTelegramClient(updates_batches=[[]])

    result = run_polling_once(client=client, config=config)

    assert result.receipts == ()
    assert result.processed_update_ids == ()
    assert result.ignored_update_ids == ()
    assert result.next_offset is None


def test_130p_polling_loop_advances_update_offset_deterministically():
    config = build_valid_config()
    client = FakeTelegramClient(
        updates_batches=[
            [build_command_update(update_id=9001, text="/start")],
            [build_command_update(update_id=9002, text="/help")],
        ]
    )

    result = run_polling_loop(client=client, config=config, max_cycles=2)

    assert client.get_updates_calls == [
        {"offset": None, "timeout": 30, "limit": 10},
        {"offset": 9002, "timeout": 30, "limit": 10},
    ]
    assert result.next_offset == 9003
    assert result.processed_update_ids == (9001, 9002)


def test_130p_polling_loop_handles_malformed_updates_safely():
    config = build_valid_config()
    client = FakeTelegramClient(
        updates_batches=[
            [
                {"update_id": 9001},
                build_command_update(update_id=9002, text="/status"),
            ]
        ]
    )

    result = run_polling_once(client=client, config=config)

    assert result.ignored_update_ids == (9001,)
    assert result.processed_update_ids == (9002,)
    assert len(result.receipts) == 1


def test_130p_send_message_payload_uses_correct_chat_id_and_text():
    config = build_valid_config()
    client = FakeTelegramClient(
        updates_batches=[[build_command_update(chat_id=7777, text="/start")]]
    )

    result = run_polling_once(client=client, config=config)

    assert result.receipts[0].chat_id == 7777
    assert client.sent_messages[0]["chat_id"] == 7777
    assert client.sent_messages[0]["text"] == render_start_command_reply(config)


def test_130p_module_has_no_models_tools_workers_or_nontelegram_external_paths():
    text = MODULE_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import socket",
        "import subprocess",
        "openai",
        "anthropic",
        "ollama",
        "googleapiclient",
        "imaplib",
        "drive",
        "slack",
        "worker",
    ]:
        assert forbidden not in text


def test_130p_main_returns_nonzero_for_missing_live_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.delenv("ROBOTICXS_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("ROBOTICXS_TELEGRAM_OWNER_IDS", raising=False)

    exit_code = main(["--once"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Roboticxs Telegram Robot: offline" in captured.out
    assert "Reason: rejected_missing_owner_allowlist" in captured.out


def test_130p_main_uses_injected_client_for_bounded_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    fake_client = FakeTelegramClient(updates_batches=[[build_command_update(text="/status")]])
    monkeypatch.setenv("ROBOTICXS_TELEGRAM_BOT_TOKEN", "token-123")
    monkeypatch.setenv("ROBOTICXS_TELEGRAM_OWNER_IDS", "111111111")
    monkeypatch.setattr(
        "app.runnable_telegram_robot_mvp.create_telegram_client",
        lambda config: fake_client,
    )

    exit_code = main(["--once"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Roboticxs Telegram Robot: online" in captured.out
    assert "Available commands: /start, /help, /menu, /status" in captured.out
    assert "/checkup" in captured.out
    assert "/miss" in captured.out
    assert "/demo" in captured.out
    assert "/brief" in captured.out
    assert "/suggest_brief" in captured.out
    assert "/suggestions" in captured.out
    assert "/suggestion_draft" in captured.out
    assert "/drafts" in captured.out
    assert "/draft_approve" in captured.out
    assert "/export_text" in captured.out
    assert fake_client.sent_messages[0]["text"] == render_status_command_reply(build_valid_config())


def test_130p_startup_report_is_deterministic():
    report = build_telegram_robot_startup_report(build_valid_config())

    assert "Stage: 150P" in report
    assert "Owner gate: enabled" in report
    assert "Product menu: Today, Prep, Pilot, Suggestions, Approvals, Drafts, Memory, Documents, Usage, Status" in report
    assert "Available commands: /start, /help, /menu, /status, /checkup, /setup, /miss, /today, /daily_brief, /demo, /pilot, /pilot_pack, /pilot_audit, /live_smoke, /gmail_thread, /loops, /inbox, /inbox_done, /inbox_dismiss, /prep, /brief, /suggest_brief, /suggestions, /suggestion_dismiss, /suggestion_snooze, /suggestion_memory, /suggestion_draft, /suggestion_followup, /approvals, /approve, /reject, /drafts, /draft_approve, /draft_reject, /draft_edit, /draft_expire, /export_text, /export_email, /export_file, /usage, /memory_review, /memory_approve, /memory_reject, /memory_edit, /memory_forget, /memory, /memory_limits, /memory_pending, document upload" in report
    assert "External connectors: Google Calendar read-only optional" in report
    assert "Calendar writes: disabled" in report
    assert "LLM/model calls: disabled" in report
    assert "Tools: disabled" in report
    assert "Memory Center commands: /memory, /memory_review, /memory_limits, /memory_pending, /memory_forget" in report
    assert "Memory Center mutation: disabled" in report
    assert "Today command: /today owner-requested read-only summary only" in report
    assert "Cross-Source Daily Brief: /daily_brief owner-requested read-only brief only" in report
    assert "Customer MVP Demo Pack v1: /demo owner-requested local demo only" in report
    assert "Live Connector Readiness Check: /checkup owner-requested read-only readiness only" in report
    assert "Gmail Thread Drilldown: /gmail_thread <thread_id> owner-requested read-only metadata only" in report
    assert "Meeting Prep Pack: /prep or /prep <suggestion_id> owner-requested read-only prep only" in report
    assert "Meeting Prep Pack v1: /prep includes read-only email/document context when locally available" in report
    assert "Open Loops command: /loops owner-requested read-only unresolved loops only" in report
    assert "Memory Review Decisions: /memory_approve, /memory_reject, and /memory_edit create local decision receipts only" in report
    assert "Memory Source & Forget Receipts: /memory shows provenance and /memory_forget creates local receipts only" in report
    assert "Document Intake: Telegram document metadata receives draft-only local replies only" in report
    assert "Proactive meeting suggestions: /suggest_brief owner-requested replies only" in report
    assert "Suggestion Inbox: /suggestions owner-requested local pending suggestions only" in report
    assert "User-Approved Output Queue: /approvals, /approve, and /reject create local receipts only" in report
    assert "Suggestion Decisions: /suggestion_* owner-requested local receipts only" in report
    assert "Action Draft Queue: /drafts owner-requested local approval candidates only" in report
    assert "User Confirmation Runtime: /draft_* creates local confirmation receipts only" in report
    assert "Approved Output Export: /export_* creates local export payloads only" in report
    assert "Usage & Cost Ledger: /usage shows local estimated usage only" in report
    assert "Skill Manifest Runtime Gates: available for local command skill boundaries only" in report
    assert "Controlled Live Pilot Baseline: /pilot owner-requested controlled pilot receipt only" in report
    assert "Customer Pilot Readiness Pack: /pilot_pack owner-requested pilot setup pack only" in report
    assert "Customer Pilot Audit Gate: /pilot_audit owner-requested pilot audit report only" in report
    assert "Live Smoke Script: /live_smoke owner-requested manual smoke guide only" in report
    assert "Suggested meeting brief requests: /brief <suggestion_id> owner-requested replies only" in report
    assert "Proactive outbound: disabled" in report


def test_130p_miss_command_is_routed_through_existing_runtime():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/miss"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.reply_text == render_miss_command_reply(config)
    assert "What Did I Miss?" in receipt.reply_text


def test_130p_brief_command_is_routed_through_existing_runtime():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert "Meeting Brief" in receipt.reply_text
    assert "Read-only Calendar connector unavailable: missing_access_token." in receipt.reply_text
    assert "Falling back to local deterministic meeting context." in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_138p_suggest_brief_command_returns_action_only_calendar_suggestions(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-123")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/suggest_brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.command == "/suggest_brief"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert "Proactive Meeting Suggestions" in receipt.reply_text
    assert "Stage: 138P" in receipt.reply_text
    assert "Action-only: true" in receipt.reply_text
    assert "Briefs executed: 0" in receipt.reply_text
    assert "Suggested action:" in receipt.reply_text
    assert re.search(r"/brief [0-9a-f-]{36}", receipt.reply_text)
    assert "Telegram delivery: owner-requested reply only." in receipt.reply_text
    assert "Automatic proactive send: disabled." in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "LLM/model calls: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_141p_today_command_returns_owner_requested_read_only_summary(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-141p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/today"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/today"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert "Today" in receipt.reply_text
    assert "Stage: 141P" not in receipt.reply_text
    assert "Meetings:" in receipt.reply_text
    assert "Open loops:" in receipt.reply_text
    assert "Things waiting for you:" in receipt.reply_text
    assert "Suggested next action:" in receipt.reply_text
    assert "Blocked / unavailable sources:" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "Source trace:" in receipt.reply_text
    assert "- Calendar: connected" in receipt.reply_text
    assert "- Calendar id: primary" in receipt.reply_text
    assert "evt-client-demo | Client demo prep meeting" in receipt.reply_text
    assert "- Writes: disabled" in receipt.reply_text
    assert "/brief" in receipt.reply_text
    assert "Approved visible memories: 1" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Memory writes: disabled" in receipt.reply_text
    assert "ProposedMemory writes: disabled" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "Tools: disabled" in receipt.reply_text
    assert "Worker dispatch: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "Proactive outbound: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_192p_today_command_can_use_fast_path_cache_without_connector_read(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-192p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/today"))
    cache_entry = build_fast_path_cache_entry(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        command="/today",
        cached_reply="Today cached customer summary",
        source_trace="calendar:evt-client-demo memory:mem-today-telegram",
        cached_at_epoch_seconds=1_000,
        ttl_seconds=120,
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        fast_path_cache_entries=(cache_entry,),
        fast_path_now_epoch_seconds=1_030,
    )

    assert receipt.command == "/today"
    assert receipt.authorized is True
    assert calendar_client.calls == []
    assert "Fast Path Cache" in receipt.reply_text
    assert "Stage: 192P" in receipt.reply_text
    assert "Status: hit" in receipt.reply_text
    assert "Freshness: fresh (30s old, ttl 120s)" in receipt.reply_text
    assert "Source trace: calendar:evt-client-demo memory:mem-today-telegram" in receipt.reply_text
    assert "Today cached customer summary" in receipt.reply_text
    assert "Connector reads: not performed for this reply" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_182p_today_calendar_unavailable_source_trace_points_to_checkup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/today"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is True
    assert calendar_client.calls == []
    assert "Source trace:" in receipt.reply_text
    assert "- Calendar: not_connected" in receipt.reply_text
    assert "- Reason: missing_access_token" in receipt.reply_text
    assert "- Next: run /checkup" in receipt.reply_text
    assert "- Writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_174p_daily_brief_command_returns_cross_source_read_only_summary(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-174p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    gmail_client = FakeGmailReadonlyHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/daily_brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        gmail_http_client=gmail_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/daily_brief"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert len(gmail_client.calls) == 2
    assert "Daily Brief" in receipt.reply_text
    assert "Stage: 174P" in receipt.reply_text
    assert "Prioritized context" in receipt.reply_text
    assert "Stage: 193P" in receipt.reply_text
    assert "Ranking: deterministic local score" in receipt.reply_text
    assert "Why:" in receipt.reply_text
    assert "Source:" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "Source Trace Receipt" in receipt.reply_text
    assert "Stage: 184P" in receipt.reply_text
    assert "- Calendar: used" in receipt.reply_text
    assert "evt-client-demo | Client demo prep meeting" in receipt.reply_text
    assert "be relevant for prep" in receipt.reply_text
    assert "- Gmail: used" in receipt.reply_text
    assert "- Memory: used" in receipt.reply_text
    assert "- Documents: not_used" in receipt.reply_text
    assert "- Usage/Cost: not_used" in receipt.reply_text
    assert "Francisco prefers compact daily briefings." in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Gmail modify/delete: disabled" in receipt.reply_text
    assert "Memory mutation: approval_required" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "Tools/workers: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_183p_daily_brief_keeps_calendar_context_when_gmail_fails_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-183p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    gmail_client = FailingGmailReadonlyHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/daily_brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        gmail_http_client=gmail_client,
    )

    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert len(gmail_client.calls) == 1
    assert "Client demo prep meeting" in receipt.reply_text
    assert "Gmail: unavailable (gmail_read_failed_closed)." in receipt.reply_text
    assert "Source Trace Receipt" in receipt.reply_text
    assert "- Gmail: blocked" in receipt.reply_text
    assert "Reason: gmail_read_failed_closed" in receipt.reply_text
    assert "Next: run /checkup" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text


def test_174p_unauthorized_daily_brief_does_not_read_calendar_or_memory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-174p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/daily_brief")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []
    assert "Daily Brief" not in receipt.reply_text


def test_176p_gmail_thread_command_fails_closed_without_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ROBOTICXS_GOOGLE_OAUTH_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/gmail_thread thread-176p"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.command == "/gmail_thread"
    assert receipt.authorized is True
    assert "Gmail Thread Drilldown" in receipt.reply_text
    assert "Stage: 176P" in receipt.reply_text
    assert "Status: blocked_gmail_thread_unavailable" in receipt.reply_text
    assert "Thread: thread-176p" in receipt.reply_text
    assert "Blocked reason: missing_access_token" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Gmail modify/archive/label: disabled" in receipt.reply_text
    assert "Gmail delete: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_176p_unauthorized_gmail_thread_does_not_render_thread():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/gmail_thread thread-176p")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert "Gmail Thread Drilldown" not in receipt.reply_text


def test_141p_unauthorized_today_does_not_read_calendar_or_memory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-141p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/today")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []
    assert "Today" not in receipt.reply_text


def test_142p_loops_command_returns_owner_requested_read_only_open_loops(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-142p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/loops"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.command == "/loops"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert "Open Loops" in receipt.reply_text
    assert "Stage: 142P" in receipt.reply_text
    assert "pending review; not treated as fact" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "/brief" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Memory writes: disabled" in receipt.reply_text
    assert "ProposedMemory writes: disabled" in receipt.reply_text
    assert "Follow-up intents: disabled" in receipt.reply_text
    assert "Reminders/scheduler: disabled" in receipt.reply_text
    assert "LLM/model calls: disabled" in receipt.reply_text
    assert "Tools/workers: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "Proactive outbound: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_142p_unauthorized_loops_does_not_read_calendar_or_memory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-142p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/loops")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []
    assert "Open Loops" not in receipt.reply_text


def test_143p_prep_command_returns_owner_requested_read_only_meeting_prep_pack(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-143p")
    config = build_valid_config()
    suggest_client = FakeTelegramClient()
    suggest_calendar_client = FakeCalendarHttpClient()
    suggest_incoming = parse_telegram_incoming_command(build_command_update(text="/suggest_brief"))

    suggest_receipt = handle_incoming_command(
        incoming_command=suggest_incoming,
        client=suggest_client,
        config=config,
        calendar_http_client=suggest_calendar_client,
    )
    suggestion_match = re.search(r"/brief ([0-9a-f-]{36})", suggest_receipt.reply_text)
    assert suggestion_match is not None

    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    gmail_client = FakeGmailReadonlyHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text=f"/prep {suggestion_match.group(1)}")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        gmail_http_client=gmail_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/prep"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert len(gmail_client.calls) == 2
    assert "Meeting Prep Pack" in receipt.reply_text
    assert "Stage: 175P" in receipt.reply_text
    assert "Meeting context:" in receipt.reply_text
    assert "Recent email context:" in receipt.reply_text
    assert "Documents / risks:" in receipt.reply_text
    assert "be relevant for prep" in receipt.reply_text
    assert "Source Trace Receipt" in receipt.reply_text
    assert "Stage: 184P" in receipt.reply_text
    assert "- Gmail: used" in receipt.reply_text
    assert "Next steps:" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "- Calendar: used" in receipt.reply_text
    assert "evt-client-demo | Client demo prep meeting" in receipt.reply_text
    assert "Francisco prefers compact daily briefings." in receipt.reply_text
    assert "Memory candidates:" in receipt.reply_text
    assert "pending owner review" in receipt.reply_text
    assert "/memory_approve" in receipt.reply_text
    assert "/memory_reject" in receipt.reply_text
    assert "Memory candidates are pending owner review and are not treated as facts." in receipt.reply_text
    assert "No memory was written." in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Gmail modify/delete: disabled" in receipt.reply_text
    assert "Memory mutation: approval_required" in receipt.reply_text
    assert "Draft creation: disabled" in receipt.reply_text
    assert "Scheduler/proactive sends: disabled" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "Tools/workers: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_rqf_023r_prep_without_suggestion_id_uses_next_read_only_meeting(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-rqf-023r")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    gmail_client = FakeGmailReadonlyHttpClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/prep"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        gmail_http_client=gmail_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/prep"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert len(gmail_client.calls) == 2
    assert "Meeting Prep Pack" in receipt.reply_text
    assert "Stage: 175P" in receipt.reply_text
    assert "Status: completed_with_context" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "Review the objective for Client demo prep meeting." in receipt.reply_text
    assert "Source Trace Receipt" in receipt.reply_text
    assert "- Calendar: used" in receipt.reply_text
    assert "- Gmail: used" in receipt.reply_text
    assert "Next steps:" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Gmail send: disabled" in receipt.reply_text
    assert "Draft creation: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_rqf_023r_prep_resolver_fails_closed_when_calendar_is_unavailable():
    scan = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=build_calendar_context_scan_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            calendar_result=CalendarReadResult(
                ok=False,
                calendar_id="primary",
                window_start="2026-06-24T10:00:00-06:00",
                window_end="2026-07-01T10:00:00-06:00",
                events=(),
                read_only=True,
                external_writes=False,
                memory_mutation=False,
                error_code="missing_access_token",
                error_message="missing_access_token",
            ),
        ),
    )

    assert (
        resolve_prep_suggestion_id(
            requested_suggestion_id=None,
            suggestion_scan=scan,
        )
        == "calendar-unavailable"
    )


def test_143p_unauthorized_prep_does_not_read_calendar_or_memory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-143p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/prep any-suggestion")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []
    assert "Meeting Prep Pack" not in receipt.reply_text


def test_173p_memory_review_returns_visible_pending_candidates_without_writeback():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/memory_review"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.command == "/memory_review"
    assert receipt.authorized is True
    assert "Memory Approval Review" in receipt.reply_text
    assert "Stage: 173P" in receipt.reply_text
    assert "Pending candidates: 1" in receipt.reply_text
    assert "proposal-loop-telegram | memory_preference: Francisco prefers compact loop reviews." in receipt.reply_text
    assert "/memory_approve proposal-loop-telegram" in receipt.reply_text
    assert "/memory_reject proposal-loop-telegram" in receipt.reply_text
    assert "/memory_edit proposal-loop-telegram <text>" in receipt.reply_text
    assert "No memory was written." in receipt.reply_text


def test_173p_memory_approve_returns_local_decision_without_writeback():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/memory_approve proposal-loop-telegram"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.command == "/memory_approve"
    assert receipt.authorized is True
    assert "Memory Approval Decision" in receipt.reply_text
    assert "Stage: 173P" in receipt.reply_text
    assert "Choice: approve" in receipt.reply_text
    assert "Status: approved_pending_writeback_local_receipt" in receipt.reply_text
    assert "Writeback executed: false" in receipt.reply_text
    assert "No memory was written." in receipt.reply_text


def test_173p_memory_edit_without_text_fails_closed_without_writeback():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/memory_edit proposal-loop-telegram"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.command == "/memory_edit"
    assert receipt.authorized is True
    assert "Memory Approval Decision" in receipt.reply_text
    assert "Stage: 173P" in receipt.reply_text
    assert "Choice: edit" in receipt.reply_text
    assert "Status: blocked_missing_edit_text" in receipt.reply_text
    assert "No memory was written." in receipt.reply_text


def test_187p_memory_command_appends_source_receipts_without_leaking_sensitive_values():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/memory"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                active_memory(
                    item_id="mem-secret-187p",
                    sensitivity="credential_like",
                    content="api key secret-187p-token",
                    bounded_summary="api key secret-187p-token",
                ),
            ),
        ),
    )

    assert receipt.command == "/memory"
    assert receipt.authorized is True
    assert "Memory Center" in receipt.reply_text
    assert "Memory Source Receipts" in receipt.reply_text
    assert "Stage: 187P" in receipt.reply_text
    assert "Memory Intelligence" in receipt.reply_text
    assert "Stage: 196P" in receipt.reply_text
    assert "used_memory:" in receipt.reply_text
    assert "mem-secret-187p | preference: [redacted credential-like memory]" in receipt.reply_text
    assert "Source: local_fixture" in receipt.reply_text
    assert "Source stage: unknown" in receipt.reply_text
    assert "Scopes: telegram, general" in receipt.reply_text
    assert "Allowed uses: telegram_context" in receipt.reply_text
    assert "secret-187p-token" not in receipt.reply_text
    assert "Source evidence deletion: disabled" in receipt.reply_text
    assert "No source evidence was deleted." in receipt.reply_text


def test_187p_memory_forget_returns_local_receipt_without_mutation():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/memory_forget mem-today-telegram"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/memory_forget"
    assert receipt.authorized is True
    assert "Memory Forget Receipt" in receipt.reply_text
    assert "Stage: 187P" in receipt.reply_text
    assert "Status: local_forget_receipt_created" in receipt.reply_text
    assert "Matched visible memory: true" in receipt.reply_text
    assert "Local forget receipt created: true" in receipt.reply_text
    assert "Memory Store mutation: disabled" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert "Source evidence deletion: disabled" in receipt.reply_text


def test_187p_memory_forget_missing_or_wrong_id_fails_closed():
    config = build_valid_config()
    client = FakeTelegramClient()
    missing = parse_telegram_incoming_command(build_command_update(text="/memory_forget"))
    wrong = parse_telegram_incoming_command(build_command_update(text="/memory_forget missing-memory"))

    missing_receipt = handle_incoming_command(
        incoming_command=missing,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )
    wrong_receipt = handle_incoming_command(
        incoming_command=wrong,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert "Status: blocked_missing_memory_id" in missing_receipt.reply_text
    assert "Local forget receipt created: false" in missing_receipt.reply_text
    assert "Status: blocked_memory_not_found" in wrong_receipt.reply_text
    assert "Local forget receipt created: false" in wrong_receipt.reply_text


def test_187p_memory_edit_for_visible_approved_memory_returns_local_edit_receipt():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text="/memory_edit mem-today-telegram Use concise daily briefings.")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/memory_edit"
    assert receipt.authorized is True
    assert "Memory Edit Receipt" in receipt.reply_text
    assert "Stage: 187P" in receipt.reply_text
    assert "Status: local_edit_receipt_created" in receipt.reply_text
    assert "Matched visible memory: true" in receipt.reply_text
    assert "Local edit receipt created: true" in receipt.reply_text
    assert "Proposed replacement: Use concise daily briefings." in receipt.reply_text
    assert "Memory Store mutation: disabled" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text


def test_187p_memory_edit_redacts_credential_like_replacement_text_in_telegram():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text="/memory_edit mem-today-telegram Use api key secret-token-187p.")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
        ),
    )

    assert receipt.command == "/memory_edit"
    assert "Memory Edit Receipt" in receipt.reply_text
    assert "Proposed replacement: [redacted credential-like edit]" in receipt.reply_text
    assert "secret-token-187p" not in receipt.reply_text
    assert "api key" not in receipt.reply_text


def test_187p_memory_edit_preserves_pending_proposal_edit_when_id_is_not_approved_memory():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text="/memory_edit proposal-loop-telegram Use shorter loop reviews.")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert receipt.command == "/memory_edit"
    assert receipt.authorized is True
    assert "Memory Approval Decision" in receipt.reply_text
    assert "Stage: 173P" in receipt.reply_text
    assert "Memory Edit Receipt" not in receipt.reply_text
    assert "Status: edit_pending_local_receipt" in receipt.reply_text
    assert "No memory was written." in receipt.reply_text


def test_188p_usage_command_renders_injected_local_usage_ledger_without_external_calls():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/usage"))
    usage_entries = (
        build_usage_cost_ledger_entry(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            task_id="prep-telegram-188p",
            command="/prep",
            task_class="meeting_prep",
            provider="local_fixture",
            model="balanced_standard_v1",
            model_mode="balanced",
            input_tokens=1200,
            output_tokens=360,
            estimated_cost_usd=0.001896,
            latency_ms=125,
            status="completed",
            created_at="2026-06-26T12:00:00+00:00",
        ),
        build_usage_cost_ledger_entry(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            task_id="doc-telegram-188p",
            command="/document",
            task_class="document_review",
            provider="local_fixture",
            model="advanced_reasoning_v1",
            model_mode="premium",
            input_tokens=2000,
            output_tokens=700,
            estimated_cost_usd=0.00621,
            latency_ms=220,
            status="completed",
            created_at="2026-06-26T13:00:00+00:00",
        ),
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        usage_ledger_entries=usage_entries,
    )

    assert receipt.command == "/usage"
    assert receipt.authorized is True
    assert "Usage & Cost Ledger" in receipt.reply_text
    assert "Stage: 188P" in receipt.reply_text
    assert "Tasks run: 2" in receipt.reply_text
    assert "Estimated cost: $0.008106" in receipt.reply_text
    assert "Documents reviewed: 1" in receipt.reply_text
    assert "Most expensive task: doc-telegram-188p ($0.006210)" in receipt.reply_text
    assert "- /prep: 1" in receipt.reply_text
    assert "- /document: 1" in receipt.reply_text
    assert "Live billing: disabled" in receipt.reply_text
    assert "Provider calls: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_188p_usage_command_empty_state_is_local_only():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/usage"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.command == "/usage"
    assert receipt.authorized is True
    assert "Usage & Cost Ledger" in receipt.reply_text
    assert "Stage: 188P" in receipt.reply_text
    assert "Tasks run: 0" in receipt.reply_text
    assert "No local usage records yet." in receipt.reply_text
    assert "Live billing: disabled" in receipt.reply_text
    assert "Provider calls: disabled" in receipt.reply_text
    assert "Persistence: disabled" in receipt.reply_text


def test_173p_unauthorized_memory_reject_does_not_create_decision():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/memory_reject proposal-loop-telegram")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert "Memory Approval Decision" not in receipt.reply_text


def test_147p_inbox_done_returns_local_decision_without_deleting_evidence():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/inbox_done pending-memory:proposal-1"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.command == "/inbox_done"
    assert receipt.authorized is True
    assert "Task Inbox Decision" in receipt.reply_text
    assert "Stage: 147P" not in receipt.reply_text
    assert "Status: done" in receipt.reply_text
    assert "Choice: done" in receipt.reply_text
    assert "Evidence deleted: false" in receipt.reply_text
    assert "Persisted state written: false" in receipt.reply_text
    assert "No inbox evidence was deleted." in receipt.reply_text


def test_139p_owner_can_request_suggested_meeting_brief_by_suggestion_id(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-139p")
    config = build_valid_config()
    suggest_client = FakeTelegramClient()
    suggest_calendar_client = FakeCalendarHttpClient()
    suggest_incoming = parse_telegram_incoming_command(build_command_update(text="/suggest_brief"))

    suggest_receipt = handle_incoming_command(
        incoming_command=suggest_incoming,
        client=suggest_client,
        config=config,
        calendar_http_client=suggest_calendar_client,
    )
    suggestion_match = re.search(r"/brief ([0-9a-f-]{36})", suggest_receipt.reply_text)
    assert suggestion_match is not None

    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text=f"/brief {suggestion_match.group(1)}")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.command == "/brief"
    assert receipt.authorized is True
    assert len(calendar_client.calls) == 1
    assert "Suggested Meeting Brief" in receipt.reply_text
    assert "Stage: 139P" in receipt.reply_text
    assert "Source stage: 138P" in receipt.reply_text
    assert "Owner requested: true" in receipt.reply_text
    assert "Suggestion validated: true" in receipt.reply_text
    assert "Client demo prep meeting" in receipt.reply_text
    assert "Automatic execution: disabled" in receipt.reply_text
    assert "Callback binding: disabled" in receipt.reply_text
    assert "Follow-up intent: disabled" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "LLM/model calls: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_139p_unknown_suggestion_id_fails_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-139p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(text="/brief 00000000-0000-0000-0000-000000000000")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is True
    assert "Suggested Meeting Brief" in receipt.reply_text
    assert "Status: blocked_suggestion_not_found" in receipt.reply_text
    assert "Suggestion validated: false" in receipt.reply_text
    assert "No suggested meeting brief was rendered." in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_139p_unauthorized_suggested_brief_request_does_not_read_calendar(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-139p")
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeCalendarHttpClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(
            telegram_user_id=999999999,
            text="/brief 00000000-0000-0000-0000-000000000000",
        )
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []


def test_130p_roadmap_registers_stage_and_133p_plus_block():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"130P","stage_name":"Runnable Telegram Robot MVP v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"131P","stage_name":"Telegram What Did I Miss Command v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"132P","stage_name":"Telegram Meeting Brief Command v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"134P","stage_name":"Calendar-backed Telegram Meeting Brief v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"135P","stage_name":"Real Calendar Meeting Brief Composer v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"138P","stage_name":"Proactive Meeting Suggestion v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"139P","stage_name":"Owner-Requested Suggested Meeting Brief v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "151P later added customer-facing Meeting Prep Pack product flow only" in roadmap
    assert "202P and later remain unauthorized" in roadmap
