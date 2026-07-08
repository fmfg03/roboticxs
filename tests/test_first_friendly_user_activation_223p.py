from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.first_friendly_user_activation import (
    build_first_friendly_user_activation_receipt,
    parse_pilot_activation_argument,
    render_first_friendly_user_activation_receipt,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FIRST_FRIENDLY_USER_ACTIVATION_223P_v0_1.md"
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
        bot_token="token-223p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_223p_builds_local_first_friendly_user_activation_receipt():
    receipt = build_first_friendly_user_activation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        pilot_alias="Ana Pilot",
        pilot_user_id="223001",
    )

    assert receipt.stage == "223P"
    assert receipt.status == "local_first_friendly_user_activation_v0"
    assert receipt.activation_status == "ready_for_first_use"
    assert receipt.setup_status == "local_allowlist_and_consent_ready; connectors_readonly_or_explicit_fallback"
    assert receipt.first_successful_command == "/founder_loop"
    assert receipt.first_useful_output == "not_recorded_yet"
    assert receipt.first_feedback == "not_recorded_yet"
    assert receipt.first_issue == "none_recorded"
    assert receipt.local_activation_only is True
    assert receipt.account_provisioned is False
    assert receipt.external_invite_sent is False
    assert receipt.connector_activation_allowed is False
    assert receipt.live_data_claimed is False
    assert receipt.gmail_send_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.source_trace_preserved is True
    assert receipt.usage_cost_preserved is True


def test_223p_renders_activation_checklist_and_safety_boundaries():
    rendered = render_first_friendly_user_activation_receipt(
        build_first_friendly_user_activation_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            pilot_alias="Ana Pilot",
            pilot_user_id="223001",
        )
    )

    assert "First Friendly User Activation" in rendered
    assert "Stage: 223P" in rendered
    assert "Activation checklist:" in rendered
    assert "- Allowlist: ready_local" in rendered
    assert "- Consent: ready_local" in rendered
    assert "- First useful output: not_recorded" in rendered
    assert "First-use signals:" in rendered
    assert "- Account provisioned: no" in rendered
    assert "- External invite sent: no" in rendered
    assert "- Connector activation: disabled" in rendered
    assert "- External writes: disabled" in rendered


def test_223p_parses_activation_argument_without_open_signup():
    assert parse_pilot_activation_argument(None, fallback_pilot_user_id="111") == ("111", "Friendly pilot")
    assert parse_pilot_activation_argument("Ana Pilot", fallback_pilot_user_id="111") == ("111", "Ana Pilot")
    assert parse_pilot_activation_argument("223001 Ana Pilot", fallback_pilot_user_id="111") == ("223001", "Ana Pilot")


def test_223p_rejects_authority_expansion_or_missing_semantics():
    receipt = build_first_friendly_user_activation_receipt(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, account_provisioned=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, connector_activation_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(receipt, live_data_claimed=True)
    with pytest.raises(ValueError, match="trace"):
        replace(receipt, source_trace_preserved=False)


def test_223p_telegram_pilot_activate_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=223,
            chat_id=223,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_activate 223001 Ana Pilot",
            command="/pilot_activate",
        ),
        client=client,
        config=_config(),
    )

    assert "First Friendly User Activation" in receipt.reply_text
    assert "Stage: 223P" in receipt.reply_text
    assert "Pilot: Ana Pilot" in receipt.reply_text
    assert "Pilot user id: 223001" in receipt.reply_text
    assert "First-use signals:" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_223p_reference_and_roadmap_close_activation_without_external_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "223P adds `/pilot_activate`" in reference
    assert "does not" in reference
    assert "provision external accounts" in reference
    assert '"stage_id":"223P","stage_name":"First Friendly User Activation v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "225P and later remain unauthorized" in roadmap
