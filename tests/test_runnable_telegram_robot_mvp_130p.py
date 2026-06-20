from __future__ import annotations

from pathlib import Path

import pytest

from app.runnable_telegram_robot_mvp import (
    DEFAULT_ROBOT_ID,
    TelegramIncomingCommand,
    TelegramRobotConfig,
    TelegramRobotConfigError,
    build_telegram_robot_startup_report,
    handle_incoming_command,
    load_telegram_robot_config_from_env,
    main,
    parse_telegram_incoming_command,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    render_unauthorized_reply,
    render_unknown_command_reply,
    run_polling_loop,
    run_polling_once,
    validate_telegram_robot_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/runnable_telegram_robot_mvp.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self, updates_batches: list[list[dict]] | None = None) -> None:
        self._updates_batches = list(updates_batches or [])
        self.get_updates_calls: list[dict[str, int | None]] = []
        self.sent_messages: list[dict[str, int | str | None]] = []

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
    ) -> dict:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
        }
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


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
    assert "Roboticxs is online." in receipt.reply_text
    assert "This dev bot is owner-gated." in receipt.reply_text
    assert "Available commands: /help, /status." in receipt.reply_text
    assert "No external actions are enabled." in receipt.reply_text


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
    assert "/start" in receipt.reply_text
    assert "/help" in receipt.reply_text
    assert "/status" in receipt.reply_text
    assert "/miss and /brief are not enabled yet." in receipt.reply_text


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
    assert f"robot_id: {DEFAULT_ROBOT_ID}" in receipt.reply_text
    assert "owner_gated: enabled" in receipt.reply_text
    assert "Hermes runtime bootstrap: available" in receipt.reply_text
    assert "Telegram dev/sandbox mode: enabled" in receipt.reply_text
    assert "live Telegram: enabled" in receipt.reply_text
    assert "external connectors: disabled" in receipt.reply_text
    assert "LLM/model calls: disabled" in receipt.reply_text
    assert "tools: disabled" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert "proactive outbound: disabled" in receipt.reply_text
    assert "roadmap state: 95P-129P closed, 130P runtime active" in receipt.reply_text


def test_130p_unknown_command_from_authorized_owner_produces_safe_fallback():
    config = build_valid_config()
    client = FakeTelegramClient()
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
    )

    assert receipt.reply_text == render_unknown_command_reply()
    assert "Command not enabled." in receipt.reply_text
    assert "No action was taken." in receipt.reply_text


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
    assert "owner_gated: enabled" not in receipt.reply_text
    assert "roadmap state" not in receipt.reply_text


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
        "gmail",
        "calendar",
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
    assert "Available commands: /start, /help, /status" in captured.out
    assert fake_client.sent_messages[0]["text"] == render_status_command_reply(build_valid_config())


def test_130p_startup_report_is_deterministic():
    report = build_telegram_robot_startup_report(build_valid_config())

    assert "Stage: 130P" in report
    assert "Owner gate: enabled" in report
    assert "External connectors: disabled" in report
    assert "LLM/model calls: disabled" in report
    assert "Tools: disabled" in report
    assert "Memory Center mutation: disabled" in report
    assert "Proactive outbound: disabled" in report


def test_130p_roadmap_registers_stage_and_131p_plus_block():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"130P","stage_name":"Runnable Telegram Robot MVP v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "131P and later remain unauthorized" in roadmap
