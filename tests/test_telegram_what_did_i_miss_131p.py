from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import (
    TelegramRobotConfig,
    handle_incoming_command,
    parse_telegram_incoming_command,
    render_help_command_reply,
    render_miss_command_reply,
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
            bot_token="token-131p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        )
    )


def test_131p_help_lists_miss_and_keeps_brief_disabled():
    reply = render_help_command_reply()

    assert "Roboticxs Menu" in reply
    assert "Setup Check: /status" in reply
    assert "/miss" in reply
    assert "/brief" in reply
    assert "/brief is not enabled yet." not in reply


def test_131p_status_marks_miss_enabled_brief_disabled_and_runtime_active():
    reply = render_status_command_reply(build_valid_config())

    assert "Today and missed-item summaries" in reply
    assert "Meeting briefs and prep packs" in reply
    assert "Roadmap: 95P-181P closed, Live Connector Readiness Check active" in reply


def test_131p_authorized_miss_produces_deterministic_local_read_only_reply():
    config = build_valid_config()

    first_reply = render_miss_command_reply(config)
    second_reply = render_miss_command_reply(config)

    assert first_reply == second_reply
    assert "What Did I Miss?" in first_reply
    assert "Status: local read-only brief" in first_reply
    assert "Source: Hermes local state snapshot" in first_reply
    assert "External connectors: disabled" in first_reply
    assert "LLM/model calls: disabled" in first_reply
    assert "Memory mutation: disabled" in first_reply
    assert "Highlights:" in first_reply
    assert "- No missed items found in the local snapshot." in first_reply
    assert "No updates were recorded in the selected window." in first_reply
    assert "Suggested next step:" in first_reply
    assert "- No action required." in first_reply
    assert "No external action was taken." in first_reply


def test_131p_authorized_miss_sends_reply_through_fake_telegram_client():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/miss"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is True
    assert receipt.reply_text == render_miss_command_reply(config)
    assert client.sent_messages == [
        {
            "chat_id": 4004,
            "text": render_miss_command_reply(config),
            "reply_to_message_id": 123,
        }
    ]


def test_131p_unauthorized_miss_returns_private_bot_response_without_brief_content():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/miss")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert "What Did I Miss?" not in receipt.reply_text
    assert "local read-only brief" not in receipt.reply_text


def test_131p_unknown_fallback_lists_brief_after_132p():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/unknown"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.reply_text == render_unknown_command_reply()
    assert "Available areas:" in receipt.reply_text
    assert "Today: /today, /miss" in receipt.reply_text
    assert "Brief: /brief, /suggest_brief" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_131p_runtime_module_does_not_add_connectors_models_tools_workers_or_memory_writes():
    text = MODULE_PATH.read_text()

    for forbidden in [
        "googleapiclient",
        "imaplib",
        "drive",
        "slack",
        "crm",
        "openai",
        "anthropic",
        "ollama",
        "worker",
        "MemoryCenterWritebackRecord",
    ]:
        assert forbidden not in text
