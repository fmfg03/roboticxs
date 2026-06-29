from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.memory_center_projection import MemoryCenterItem
from app.memory_source_forget_receipts import (
    MEMORY_SOURCE_FORGET_RECEIPTS_STAGE,
    MemorySourceReceipt,
    build_memory_edit_receipt,
    build_memory_forget_receipt,
    build_memory_source_receipts,
    render_memory_edit_receipt,
    render_memory_forget_receipt,
    render_memory_source_receipts,
)
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_SOURCE_FORGET_RECEIPTS_187P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def memory_item(**overrides) -> MemoryCenterItem:
    values = {
        "item_id": "mem-187p",
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "memory_kind": "owner_preference",
        "status": "active",
        "scopes": ("telegram", "general"),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context", "answer_personalization"),
        "skill_ids": (),
        "content": "Francisco prefers short, action-first meeting prep packs.",
        "bounded_summary": "Francisco prefers short, action-first meeting prep packs.",
        "source": "context_scan_owner_approved",
        "actor_visibility": "owner_private",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


def source_bundle(*items: MemoryCenterItem) -> TelegramMemoryCenterSourceBundle:
    return TelegramMemoryCenterSourceBundle(approved_memory_items=items)


def test_187p_builds_source_receipts_without_expanding_authority():
    receipts = build_memory_source_receipts(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=source_bundle(memory_item()),
    )

    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.stage == MEMORY_SOURCE_FORGET_RECEIPTS_STAGE
    assert receipt.owner_id == "local-owner"
    assert receipt.robot_id == "roboticxs-dev"
    assert receipt.memory_id == "mem-187p"
    assert receipt.source == "context_scan_owner_approved"
    assert receipt.source_stage == "unknown"
    assert receipt.approved_at == "unknown"
    assert receipt.visibility == "owner_private"
    assert receipt.scopes == ("telegram", "general")
    assert receipt.allowed_uses == ("telegram_context", "answer_personalization")
    assert receipt.read_only is True
    assert receipt.memory_center_mutated is False
    assert receipt.source_evidence_deleted is False
    assert receipt.connector_read_allowed is False
    assert receipt.model_call_allowed is False
    assert receipt.external_write_allowed is False


def test_187p_source_receipts_filter_owner_robot_and_redact_credential_like_memory():
    receipts = build_memory_source_receipts(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=source_bundle(
            memory_item(
                item_id="mem-secret",
                sensitivity="credential_like",
                content="api token is secret-token-187p",
                bounded_summary="api token is secret-token-187p",
            ),
            memory_item(item_id="mem-other-owner", owner_id="other-owner"),
            memory_item(item_id="mem-other-robot", robot_id="other-robot"),
        ),
    )
    rendered = render_memory_source_receipts(receipts)

    assert len(receipts) == 1
    assert "[redacted credential-like memory]" in rendered
    assert "secret-token-187p" not in rendered
    assert "mem-other-owner" not in rendered
    assert "mem-other-robot" not in rendered


def test_187p_forget_receipt_is_local_only_and_does_not_delete_source_evidence():
    receipt = build_memory_forget_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="mem-187p",
        source_bundle=source_bundle(memory_item()),
    )
    rendered = render_memory_forget_receipt(receipt)

    assert receipt.stage == MEMORY_SOURCE_FORGET_RECEIPTS_STAGE
    assert receipt.status == "local_forget_receipt_created"
    assert receipt.matched_memory is True
    assert receipt.local_forget_receipt_created is True
    assert receipt.memory_store_mutated is False
    assert receipt.memory_center_mutated is False
    assert receipt.source_evidence_deleted is False
    assert "Memory Store mutation: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "Source evidence deletion: disabled" in rendered


def test_187p_forget_receipt_fails_closed_for_missing_or_wrong_memory_id():
    missing = build_memory_forget_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="",
        source_bundle=source_bundle(memory_item()),
    )
    wrong = build_memory_forget_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="mem-missing",
        source_bundle=source_bundle(memory_item()),
    )

    assert missing.status == "blocked_missing_memory_id"
    assert missing.local_forget_receipt_created is False
    assert wrong.status == "blocked_memory_not_found"
    assert wrong.local_forget_receipt_created is False


def test_187p_edit_receipt_is_local_only_and_requires_visible_memory_and_text():
    receipt = build_memory_edit_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="mem-187p",
        proposed_text="Use short action-first prep packs.",
        source_bundle=source_bundle(memory_item()),
    )
    missing_text = build_memory_edit_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="mem-187p",
        proposed_text="",
        source_bundle=source_bundle(memory_item()),
    )
    rendered = render_memory_edit_receipt(receipt)

    assert receipt.status == "local_edit_receipt_created"
    assert receipt.local_edit_receipt_created is True
    assert receipt.memory_store_mutated is False
    assert receipt.memory_center_mutated is False
    assert receipt.source_evidence_deleted is False
    assert "Proposed replacement: Use short action-first prep packs." in rendered
    assert "Memory Store mutation: disabled" in rendered
    assert missing_text.status == "blocked_missing_edit_text"
    assert missing_text.local_edit_receipt_created is False


def test_187p_edit_receipt_redacts_credential_like_replacement_text():
    receipt = build_memory_edit_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_id="mem-187p",
        proposed_text="Use api key secret-token-187p for this account.",
        source_bundle=source_bundle(memory_item()),
    )
    rendered = render_memory_edit_receipt(receipt)

    assert receipt.status == "local_edit_receipt_created"
    assert receipt.proposed_text == "[redacted credential-like edit]"
    assert "[redacted credential-like edit]" in rendered
    assert "secret-token-187p" not in rendered
    assert "api key" not in rendered


def test_187p_receipts_reject_external_authority_expansion():
    receipt = build_memory_source_receipts(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=source_bundle(memory_item()),
    )[0]

    with pytest.raises(ValueError, match="must not expand authority"):
        MemorySourceReceipt(**{**asdict(receipt), "external_write_allowed": True})


def test_187p_reference_and_roadmap_close_memory_source_forget_receipts():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "187P is Memory Source & Forget Receipts v0 only." in reference
    assert "does not authorize Memory Center mutation" in reference
    assert "Source evidence deletion: disabled" in reference
    assert '"stage_id":"187P","stage_name":"Memory Source & Forget Receipts v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "197P and later remain unauthorized" in roadmap
