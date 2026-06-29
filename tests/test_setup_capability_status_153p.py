from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import (
    handle_incoming_command,
    load_telegram_robot_config_from_env,
    render_status_command_reply,
    validate_telegram_robot_config,
)
from tests.test_telegram_product_shell_150p import FakeTelegramClient, incoming


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/SETUP_CAPABILITY_STATUS_153P_v0_1.md"


def valid_config():
    return validate_telegram_robot_config(
        load_telegram_robot_config_from_env(
            env={
                "ROBOTICXS_TELEGRAM_BOT_TOKEN": "secret-bot-token-153p",
                "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111",
                "ROBOTICXS_OWNER_ID": "local-owner",
                "ROBOTICXS_ROBOT_ID": "roboticxs-dev",
            }
        )
    )


def test_153p_status_renders_setup_capability_surface_without_secret_leaks():
    reply = render_status_command_reply(valid_config())

    assert reply.startswith("Setup Check\n")
    assert "Active now:" in reply
    assert "Needs setup:" in reply
    assert "Unavailable:" in reply
    assert "Intentionally disabled:" in reply
    assert "Approval boundaries:" in reply
    assert "Suggested next action:" in reply
    assert "Calendar reads require read-only Google setup." in reply
    assert "Calendar meeting suggestions need read-only Calendar setup." in reply
    assert "Gmail is not an inbox yet." in reply
    assert "Document review remains draft-only; file contents are not downloaded or parsed." in reply
    assert "Task Inbox is your robot task inbox, not your Gmail inbox yet." in reply
    assert "Calendar writes: disabled" in reply
    assert "Gmail writes: disabled" in reply
    assert "Model calls: disabled" in reply
    assert "Tool execution: disabled" in reply
    assert "Automatic Memory Center mutation: disabled" in reply
    assert "/today" in reply
    assert "/brief" in reply
    assert "/prep <suggestion_id>" in reply
    assert "Roadmap: 95P-191P closed, Premium Telegram UX Shell v0 active" in reply
    assert "Doctor" not in reply
    assert "secret-bot-token-153p" not in reply


def test_153p_status_remains_owner_gated_and_does_not_activate_connectors():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=incoming("/status", user_id=999999999),
        client=client,
        config=valid_config(),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == "This Roboticxs bot is private. No action was taken."
    assert client.sent_messages == [
        {
            "chat_id": 4004,
            "text": "This Roboticxs bot is private. No action was taken.",
            "reply_to_message_id": 150,
        }
    ]


def test_153p_reference_and_roadmap_close_status_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "153P is a customer-facing Telegram status stage." in reference
    assert "does not add new commands" in reference
    assert "read secrets" in reference
    assert "activate connectors" in reference
    assert "Task Inbox must be described as the robot task inbox, not Gmail." in reference
    assert '"stage_id":"153P","stage_name":"Setup & Capability Status v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "204P and later remain unauthorized" in roadmap
