from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import (
    TelegramIncomingCommand,
    handle_incoming_command,
    load_telegram_robot_config_from_env,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    render_unknown_command_reply,
    validate_telegram_robot_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, int | str | None]] = []

    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
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


def valid_config():
    return validate_telegram_robot_config(
        load_telegram_robot_config_from_env(
            env={
                "ROBOTICXS_TELEGRAM_BOT_TOKEN": "secret-bot-token-150p",
                "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111",
                "ROBOTICXS_OWNER_ID": "local-owner",
                "ROBOTICXS_ROBOT_ID": "roboticxs-dev",
            }
        )
    )


def incoming(command: str, *, user_id: int = 111111111) -> TelegramIncomingCommand:
    return TelegramIncomingCommand(
        update_id=15001,
        chat_id=4004,
        telegram_user_id=user_id,
        message_id=150,
        command=command,
        raw_text=command,
    )


def test_150p_start_shell_explains_product_in_30_seconds_without_secret_leaks():
    reply = render_start_command_reply(valid_config())

    assert "Welcome. Your private robot is online." in reply
    assert "What I can do now:" in reply
    assert "What needs setup:" in reply
    assert "Approval boundaries:" in reply
    assert "Choose first useful action:" in reply
    assert "Today: /today, /miss" in reply
    assert "Brief: /brief, /suggest_brief" in reply
    assert "Prep: /prep <suggestion_id>" in reply
    assert "Tasks: /inbox, /inbox_done <item_id>, /inbox_dismiss <item_id>" in reply
    assert "Memory: /memory, /memory_review, /memory_pending, /memory_limits" in reply
    assert "Setup Check: /status" in reply
    assert "secret-bot-token-150p" not in reply
    assert "Doctor" not in reply


def test_150p_help_groups_commands_by_customer_job():
    reply = render_help_command_reply()

    assert "Roboticxs Menu" in reply
    assert "Today:" in reply
    assert "Brief:" in reply
    assert "Prep:" in reply
    assert "Tasks:" in reply
    assert "Memory:" in reply
    assert "Setup Check:" in reply
    assert "Tasks is your robot task inbox, not your Gmail inbox yet." in reply
    assert "Doctor" not in reply


def test_150p_status_reports_setup_capabilities_and_boundaries():
    reply = render_status_command_reply(valid_config())

    assert "Setup Check" in reply
    assert "Active now:" in reply
    assert "Needs setup:" in reply
    assert "Unavailable:" in reply
    assert "Intentionally disabled:" in reply
    assert "Approval boundaries:" in reply
    assert "Calendar reads require read-only Google setup." in reply
    assert "Gmail is not an inbox yet." in reply
    assert "Task Inbox is your robot task inbox, not your Gmail inbox yet." in reply
    assert "Calendar writes: disabled" in reply
    assert "Gmail writes: disabled" in reply
    assert "Model calls: disabled" in reply
    assert "Tool execution: disabled" in reply
    assert "Workers: disabled" in reply
    assert "Scheduler/proactive outbound: disabled" in reply
    assert "Automatic Memory Center mutation: disabled" in reply
    assert "I do not remember new facts without approval." in reply
    assert "I do not take external actions without approval." in reply
    assert "Doctor" not in reply


def test_150p_unknown_command_points_back_to_product_menu_without_action():
    reply = render_unknown_command_reply()

    assert "I do not know that command yet." in reply
    assert "Use /help to see the Roboticxs menu." in reply
    assert "Today: /today, /miss" in reply
    assert "Setup Check: /status" in reply
    assert "No external action was taken." in reply
    assert "Doctor" not in reply


def test_150p_product_shell_remains_owner_gated():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=incoming("/help", user_id=999999999),
        client=client,
        config=valid_config(),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == "This Roboticxs bot is private. No action was taken."
    assert "Roboticxs Menu" not in receipt.reply_text
    assert "secret-bot-token-150p" not in receipt.reply_text


def test_150p_roadmap_records_product_shell_and_blocks_151p_plus():
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")

    assert '"stage_id":"150P","stage_name":"Telegram Product Shell v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "151P behavior beyond customer-facing Meeting Prep Pack product flow" in roadmap
    assert "186P and later remain unauthorized" in roadmap
