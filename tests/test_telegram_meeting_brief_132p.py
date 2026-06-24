from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import (
    TelegramRobotConfig,
    handle_incoming_command,
    parse_telegram_incoming_command,
    render_brief_command_reply,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    render_unauthorized_reply,
    render_unknown_command_reply,
    validate_telegram_robot_config,
)
from tests.test_runnable_telegram_robot_mvp_130p import (
    FakeTelegramClient,
    build_command_update,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/runnable_telegram_robot_mvp.py"


def build_valid_config() -> TelegramRobotConfig:
    return validate_telegram_robot_config(
        TelegramRobotConfig(
            bot_token="token-132p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        )
    )


def test_132p_help_start_and_status_expose_brief_command():
    config = build_valid_config()

    help_reply = render_help_command_reply()
    start_reply = render_start_command_reply(config)
    status_reply = render_status_command_reply(config)

    assert "/brief" in help_reply
    assert "/brief is not enabled yet." not in help_reply
    assert "Available commands: /help, /status, /miss, /brief, /suggest_brief, /memory, /memory_limits, /memory_pending." in start_reply
    assert "/brief command: enabled" in status_reply
    assert "roadmap state: 95P-139P closed, 139P runtime active" in status_reply


def test_132p_authorized_brief_reply_is_deterministic_and_local_only():
    config = build_valid_config()

    first_reply = render_brief_command_reply(config)
    second_reply = render_brief_command_reply(config)

    assert first_reply == second_reply
    assert "Meeting Brief" in first_reply
    assert "Status: local read-only meeting brief" in first_reply
    assert "Source: Hermes local context demo flow + optional Google Calendar read-only snapshot" in first_reply
    assert "External connectors: Google Calendar read-only optional" in first_reply
    assert "Calendar writes: disabled" in first_reply
    assert "LLM/model calls: disabled" in first_reply
    assert "Memory mutation: disabled" in first_reply
    assert "Google Calendar read-only connector was not configured for this reply." in first_reply
    assert "Meeting:" in first_reply
    assert "- Victor / ASISINT follow-up" in first_reply
    assert "Context:" in first_reply
    assert "Agenda:" in first_reply
    assert "Risks / Watchpoints:" in first_reply
    assert "Suggested prep:" in first_reply
    assert "No external action was taken." in first_reply


def test_132p_authorized_brief_uses_injected_fake_telegram_client():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert "Meeting Brief" in receipt.reply_text
    assert "Read-only Calendar connector unavailable: missing_access_token." in receipt.reply_text
    assert "Falling back to local deterministic meeting context." in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text
    assert client.sent_messages == [
        {
            "chat_id": 4004,
            "text": receipt.reply_text,
            "reply_to_message_id": 123,
        }
    ]


def test_132p_empty_meeting_context_reply_is_deterministic():
    config = build_valid_config()

    reply = render_brief_command_reply(config, meeting_context_available=False)

    assert reply == "\n".join(
        [
            "Meeting Brief",
            "",
            "No local meeting context is available in the deterministic snapshot.",
            "Google Calendar read-only connector was not used.",
            "No external action was taken.",
        ]
    )


def test_132p_unauthorized_brief_returns_private_bot_response_without_brief_content():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/brief")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert "Meeting Brief" not in receipt.reply_text
    assert "Victor / ASISINT follow-up" not in receipt.reply_text


def test_132p_unknown_fallback_lists_brief_command():
    reply = render_unknown_command_reply()

    assert "Available commands: /start, /help, /status, /miss, /brief, /suggest_brief, /memory, /memory_limits, /memory_pending." in reply
    assert "No action was taken." in reply


def test_132p_runtime_module_keeps_non_telegram_surfaces_disabled():
    text = MODULE_PATH.read_text()

    for forbidden in [
        "gmail",
        "drive",
        "slack",
        "crm",
        "openai",
        "anthropic",
        "ollama",
        "worker",
    ]:
        assert forbidden not in text
