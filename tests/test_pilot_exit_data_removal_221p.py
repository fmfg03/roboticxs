from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_exit_data_removal import (
    build_pilot_exit_data_removal_receipt,
    parse_pilot_exit_argument,
    render_pilot_exit_data_removal_receipt,
)
from app.pilot_user_provisioning import build_pilot_user_provisioning_record
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_EXIT_DATA_REMOVAL_221P_v0_1.md"
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
        bot_token="token-221p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def _pilot_user():
    return build_pilot_user_provisioning_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        allowed_telegram_user_id=222222222,
        user_alias="Ana",
        pilot_status="active_local",
    )


def test_221p_builds_local_exit_receipts_for_all_commands():
    commands = {
        "/end_pilot": "end_pilot",
        "/export_pilot_data": "export_pilot_data",
        "/delete_pilot_memory": "delete_pilot_memory",
        "/disable_pilot_connectors": "disable_pilot_connectors",
    }

    for command, action in commands.items():
        receipt = build_pilot_exit_data_removal_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            command=command,
            pilot_user_id="222222222",
            requested_scope="all_local_pilot_data",
            pilot_users=(_pilot_user(),),
        )

        assert receipt.stage == "221P"
        assert receipt.status == "local_pilot_exit_receipt_v0"
        assert receipt.command == command
        assert receipt.action == action
        assert receipt.pilot_alias == "Ana"
        assert receipt.local_receipt_created is True
        assert receipt.external_deletion_claimed is False
        assert receipt.external_connector_disabled is False
        assert receipt.data_exported_externally is False
        assert receipt.memory_store_mutated is False
        assert receipt.gmail_send_allowed is False
        assert receipt.calendar_write_allowed is False
        assert receipt.approval_gate_preserved is True


def test_221p_renders_explicit_local_only_policy():
    receipt = build_pilot_exit_data_removal_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        command="/delete_pilot_memory",
        pilot_user_id="222222222",
        requested_scope="memory_only",
        pilot_users=(_pilot_user(),),
    )
    rendered = render_pilot_exit_data_removal_receipt(receipt)

    assert "Pilot Exit / Data Removal" in rendered
    assert "Action: delete_pilot_memory" in rendered
    assert "Requested scope: memory_only" in rendered
    assert "Memory Store mutation: disabled" in rendered
    assert "External deletion claimed: no" in rendered
    assert "External connector disabled: no" in rendered
    assert "Destructive actions: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_221p_parse_exit_argument_and_rejects_authority_expansion():
    assert parse_pilot_exit_argument("222222222 all_local_pilot_data", fallback_pilot_user_id="111111111") == (
        "222222222",
        "all_local_pilot_data",
    )
    assert parse_pilot_exit_argument("", fallback_pilot_user_id="111111111") == (
        "111111111",
        "local_pilot_scope",
    )
    receipt = build_pilot_exit_data_removal_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        command="/disable_pilot_connectors",
        pilot_user_id="222222222",
    )

    with pytest.raises(ValueError, match="external or destructive authority"):
        replace(receipt, external_connector_disabled=True)
    with pytest.raises(ValueError, match="external or destructive authority"):
        replace(receipt, external_deletion_claimed=True)
    with pytest.raises(ValueError, match="external or destructive authority"):
        replace(receipt, memory_store_mutated=True)
    with pytest.raises(ValueError, match="approval-preserving"):
        replace(receipt, approval_gate_preserved=False)


def test_221p_telegram_exit_commands_are_visible():
    client = FakeTelegramClient()
    config = _config()

    for index, command in enumerate(("/end_pilot", "/export_pilot_data", "/delete_pilot_memory", "/disable_pilot_connectors"), start=1):
        receipt = handle_incoming_command(
            incoming_command=TelegramIncomingCommand(
                update_id=221 + index,
                chat_id=222,
                telegram_user_id=111111111,
                message_id=333 + index,
                raw_text=f"{command} 222222222 all_local_pilot_data",
                command=command,
            ),
            client=client,
            config=config,
            friendly_pilot_users=(_pilot_user(),),
        )

        assert "Pilot Exit / Data Removal" in receipt.reply_text
        assert "Stage: 221P" in receipt.reply_text
        assert "Alias: Ana" in receipt.reply_text
        assert "Local receipt created: yes" in receipt.reply_text
        assert "External deletion claimed: no" in receipt.reply_text

    assert len(client.sent_messages) == 4


def test_221p_reference_and_roadmap_close_exit_flow_without_external_deletes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "221P adds local Telegram receipts" in reference
    assert "does not delete provider data" in reference
    assert '"stage_id":"221P","stage_name":"Pilot Exit / Data Removal Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "224P and later remain unauthorized" in roadmap
