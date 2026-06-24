from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.memory_center_projection import MemoryCenterItem
from app.runnable_telegram_robot_mvp import (
    TelegramIncomingCommand,
    handle_incoming_command,
    load_telegram_robot_config_from_env,
    validate_telegram_robot_config,
)
from app.telegram_memory_center_commands import (
    TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE,
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
    render_memory_center_command_reply,
    render_memory_limits_command_reply,
    render_memory_pending_command_reply,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/telegram_memory_center_commands.py"
ROBOT_PATH = REPO_ROOT / "app/runnable_telegram_robot_mvp.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


@dataclass(frozen=True, slots=True)
class PendingProposalFixture:
    proposal_id: str = "proposal-136p"
    owner_id: str = "local-owner"
    robot_id: str = "roboticxs-dev"
    proposal_type: str = "business_context_candidate"
    proposed_memory_text: str = "ASISINT is an active client opportunity."
    confidence: str = "high"
    review_reason: str = "Calendar context may help future meeting prep."
    status: str = "pending_user_review"
    source_stage: str = "115P"


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
                "ROBOTICXS_TELEGRAM_BOT_TOKEN": "token-136p",
                "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111",
                "ROBOTICXS_OWNER_ID": "local-owner",
                "ROBOTICXS_ROBOT_ID": "roboticxs-dev",
            }
        )
    )


def incoming(command: str, *, user_id: int = 111111111) -> TelegramIncomingCommand:
    return TelegramIncomingCommand(
        update_id=13601,
        chat_id=4004,
        telegram_user_id=user_id,
        message_id=501,
        command=command,
        raw_text=command,
    )


def active_memory(**overrides) -> MemoryCenterItem:
    values = {
        "item_id": "mem-136p-1",
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "memory_kind": "BUSINESS_CONTEXT_MEMORY",
        "status": "active",
        "scopes": ("general", "telegram"),
        "sensitivity": "ordinary",
        "allowed_uses": ("answer_personalization", "telegram_context"),
        "skill_ids": (),
        "content": "ASISINT is an active client opportunity.",
        "bounded_summary": "ASISINT is active client context.",
        "source": "approved_memory_fixture",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


def test_136p_snapshot_separates_approved_memory_from_pending_proposals():
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                active_memory(),
                active_memory(item_id="mem-other-owner", owner_id="other-owner"),
                active_memory(item_id="mem-proposed", status="proposed"),
            ),
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert snapshot.stage == TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE
    assert snapshot.approved_total_count == 1
    assert snapshot.pending_total_count == 1
    assert snapshot.memory_write_allowed is False
    assert snapshot.memory_center_mutated is False
    assert snapshot.external_write_allowed is False
    assert snapshot.model_call_allowed is False
    assert snapshot.approved_memories[0].summary == "ASISINT is active client context."
    assert snapshot.pending_proposals[0].proposed_memory_text == "ASISINT is an active client opportunity."


def test_136p_memory_reply_lists_only_approved_visible_memory():
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    reply = render_memory_center_command_reply(snapshot)

    assert "Memory Center" in reply
    assert "Status: local read-only visibility" in reply
    assert "Approved visible memories: 1" in reply
    assert "BUSINESS_CONTEXT_MEMORY: ASISINT is active client context." in reply
    assert "ASISINT is an active client opportunity." not in reply
    assert "No Memory Center mutation was performed." in reply


def test_136p_memory_pending_reply_lists_only_pending_proposals():
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    reply = render_memory_pending_command_reply(snapshot)

    assert "Memory Pending" in reply
    assert "Pending proposals: 1" in reply
    assert "business_context_candidate: ASISINT is an active client opportunity." in reply
    assert "ASISINT is active client context." not in reply
    assert "No pending proposal was approved, rejected, edited, or written." in reply


def test_136p_memory_limits_reply_declares_non_mutating_bounds():
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
    )

    reply = render_memory_limits_command_reply(snapshot)

    assert "Memory Center Limits" in reply
    assert "Read-only: enabled" in reply
    assert "Memory writes: disabled" in reply
    assert "Approvals/rejections: disabled in 136P commands" in reply
    assert "Credential-like memory is always redacted from Telegram replies." in reply
    assert "External writes: disabled" in reply


def test_136p_telegram_memory_command_is_owner_gated_and_read_only():
    config = valid_config()
    client = FakeTelegramClient()
    source_bundle = TelegramMemoryCenterSourceBundle(
        approved_memory_items=(active_memory(),),
    )

    receipt = handle_incoming_command(
        incoming_command=incoming("/memory"),
        client=client,
        config=config,
        memory_source_bundle=source_bundle,
    )

    assert receipt.authorized is True
    assert receipt.command == "/memory"
    assert "Approved visible memories: 1" in receipt.reply_text
    assert "Memory writes: disabled" in receipt.reply_text
    assert "No Memory Center mutation was performed." in receipt.reply_text


def test_136p_telegram_memory_pending_command_does_not_write_memory():
    config = valid_config()
    client = FakeTelegramClient()
    source_bundle = TelegramMemoryCenterSourceBundle(
        pending_memory_proposals=(PendingProposalFixture(),),
    )

    receipt = handle_incoming_command(
        incoming_command=incoming("/memory_pending"),
        client=client,
        config=config,
        memory_source_bundle=source_bundle,
    )

    assert receipt.authorized is True
    assert "Pending proposals: 1" in receipt.reply_text
    assert "No pending proposal was approved, rejected, edited, or written." in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_136p_unauthorized_memory_command_does_not_leak_memory():
    config = valid_config()
    client = FakeTelegramClient()
    source_bundle = TelegramMemoryCenterSourceBundle(
        approved_memory_items=(active_memory(),),
    )

    receipt = handle_incoming_command(
        incoming_command=incoming("/memory", user_id=999999999),
        client=client,
        config=config,
        memory_source_bundle=source_bundle,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == "This Roboticxs bot is private. No action was taken."
    assert "ASISINT" not in receipt.reply_text


def test_136p_sensitive_memory_is_bounded_or_redacted_for_telegram():
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                active_memory(
                    item_id="mem-credential",
                    memory_kind="BOUNDARY_MEMORY",
                    sensitivity="credential_like",
                    content="password is never displayed",
                    bounded_summary=None,
                    is_boundary=True,
                    conflict_group="credentials",
                ),
            )
        ),
    )

    reply = render_memory_center_command_reply(snapshot)

    assert "[redacted credential-like memory]" in reply
    assert "password is never displayed" not in reply


def test_136p_files_declare_no_memory_mutation_or_external_write_authority():
    module_text = MODULE_PATH.read_text()
    robot_text = ROBOT_PATH.read_text()

    assert "memory_center_mutated: bool = False" in module_text
    assert "external_write_allowed: bool = False" in module_text
    assert "connector_read_allowed: bool = False" in module_text
    assert "model_call_allowed: bool = False" in module_text
    assert "worker_dispatch_allowed: bool = False" in module_text
    assert "Memory Center mutation: disabled" in robot_text


def test_136p_roadmap_records_memory_center_telegram_commands_and_blocks_137p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"136P","stage_name":"Memory Center Telegram Commands v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "138P and later remain unauthorized" in roadmap
    assert "No Telegram memory command writes, approves, rejects, edits, deletes, or mutates Memory Center state." in roadmap
