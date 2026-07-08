from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.memory_center_projection import MemoryCenterItem
from app.memory_correction_loop import (
    MEMORY_CORRECTION_LOOP_STAGE,
    build_memory_correction_receipt,
    correction_type_from_command,
    parse_memory_correction_argument,
    render_memory_correction_receipt,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_CORRECTION_LOOP_209P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None) -> dict:
        payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id}
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


def memory_item(item_id: str = "mem-209p", **overrides) -> MemoryCenterItem:
    values = {
        "item_id": item_id,
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "memory_kind": "owner_preference",
        "status": "active",
        "scopes": ("telegram", "general"),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context", "answer_personalization"),
        "skill_ids": (),
        "content": "Francisco prefers short daily loops.",
        "bounded_summary": "Francisco prefers short daily loops.",
        "source": "owner_approved_memory",
        "actor_visibility": "owner_private",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


def source_bundle(*items: MemoryCenterItem) -> TelegramMemoryCenterSourceBundle:
    return TelegramMemoryCenterSourceBundle(approved_memory_items=items)


def _config() -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="token-209p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def test_209p_builds_memory_correction_receipt_without_mutation():
    receipt = build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="stale",
        memory_id="mem-209p",
        source_bundle=source_bundle(memory_item()),
    )

    assert receipt.stage == MEMORY_CORRECTION_LOOP_STAGE
    assert receipt.status == "local_memory_correction_receipt_created"
    assert receipt.correction_type == "stale"
    assert receipt.matched_memory is True
    assert receipt.local_receipt_created is True
    assert receipt.memory_store_mutated is False
    assert receipt.memory_center_mutated is False
    assert receipt.source_evidence_deleted is False
    assert receipt.external_write_allowed is False
    assert receipt.approval_gate_preserved is True


def test_209p_parses_and_builds_merge_receipt_for_two_visible_memories():
    assert correction_type_from_command("/memory_merge") == "merge"
    assert parse_memory_correction_argument("merge", "mem-a mem-b") == ("mem-a", "mem-b")
    receipt = build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="merge",
        memory_id="mem-a",
        merge_target_memory_id="mem-b",
        source_bundle=source_bundle(memory_item("mem-a"), memory_item("mem-b")),
    )
    rendered = render_memory_correction_receipt(receipt)

    assert receipt.status == "local_memory_correction_receipt_created"
    assert receipt.matched_memory is True
    assert receipt.matched_merge_target is True
    assert "Merge target: mem-b" in rendered
    assert "Memory Store mutation: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_209p_blocks_missing_or_non_visible_memory_and_authority_expansion():
    missing = build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="wrong",
        memory_id="",
        source_bundle=source_bundle(memory_item()),
    )
    not_found = build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="wrong",
        memory_id="mem-missing",
        source_bundle=source_bundle(memory_item()),
    )
    receipt = build_memory_correction_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        correction_type="wrong",
        memory_id="mem-209p",
        source_bundle=source_bundle(memory_item()),
    )

    assert missing.status == "blocked_missing_memory_id"
    assert missing.local_receipt_created is False
    assert not_found.status == "blocked_memory_not_found"
    assert not_found.local_receipt_created is False
    with pytest.raises(ValueError, match="expand authority"):
        replace(receipt, memory_center_mutated=True)


def test_209p_telegram_memory_correction_command_is_visible():
    client = FakeTelegramClient()
    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=209,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/memory_wrong mem-209p",
            command="/memory_wrong",
        ),
        client=client,
        config=_config(),
        memory_source_bundle=source_bundle(memory_item()),
    )

    assert "Memory Correction Receipt" in receipt.reply_text
    assert "Stage: 209P" in receipt.reply_text
    assert "Correction: wrong" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert client.sent_messages[0]["text"] == receipt.reply_text


def test_209p_reference_and_roadmap_close_memory_correction_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "209P adds local memory correction receipts" in reference
    assert "does not mutate Memory Store" in reference
    assert '"stage_id":"209P","stage_name":"Memory Correction Loop v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "221P and later remain unauthorized" in roadmap
