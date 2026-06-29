from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.context_scan_proposed_memory import build_context_scan_proposed_memory_record
from app.memory_store import (
    MEMORY_STORE_STAGE,
    MemoryStoreReceipt,
    MemoryStoreRegistry,
    add_memory_to_store,
    approve_context_candidate_to_memory_store,
    build_memory_center_source_bundle_from_store,
    edit_memory_in_store,
    forget_memory_in_store,
    pin_memory_in_store,
    render_memory_store_receipt,
)
from app.telegram_memory_center_commands import build_memory_center_telegram_snapshot, render_memory_center_command_reply
from tests.test_context_scan_proposed_memory_164p import calendar_scan, gmail_scan


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_STORE_165P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def context_candidate():
    record = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
        gmail_scan=gmail_scan(),
    )
    return record.candidates[0]


def test_165p_approves_context_candidate_into_local_memory_store_without_external_writes():
    registry = MemoryStoreRegistry()
    candidate = context_candidate()

    receipt = approve_context_candidate_to_memory_store(
        candidate=candidate,
        registry=registry,
        approved_at="2026-06-25T12:00:00Z",
    )

    assert receipt.stage == MEMORY_STORE_STAGE
    assert receipt.action == "approve_context_candidate"
    assert receipt.status == "stored"
    assert receipt.local_memory_store_mutated is True
    assert receipt.memory_center_mutated is False
    assert receipt.proposed_memory_written is False
    assert receipt.calendar_write_allowed is False
    assert receipt.gmail_write_allowed is False
    assert receipt.model_call_allowed is False
    assert receipt.tool_call_allowed is False
    assert receipt.worker_dispatch_allowed is False
    assert receipt.external_write_allowed is False
    item = registry.get_item(receipt.memory_id)
    assert item is not None
    assert item.memory_id == receipt.memory_id
    assert item.robot_id == "roboticxs-dev"
    assert item.user_id == "local-owner"
    assert item.content == candidate.proposed_memory_text
    assert item.source == "context_scan_owner_approved"
    assert item.confidence == candidate.confidence
    assert item.approved_at == "2026-06-25T12:00:00Z"
    assert item.status == "active"
    assert item.visibility == "owner_private"
    assert item.pinned is False


def test_165p_duplicate_context_candidate_does_not_create_second_store_mutation():
    registry = MemoryStoreRegistry()
    candidate = context_candidate()

    first = approve_context_candidate_to_memory_store(
        candidate=candidate,
        registry=registry,
        approved_at="2026-06-25T12:00:00Z",
    )
    second = approve_context_candidate_to_memory_store(
        candidate=candidate,
        registry=registry,
        approved_at="2026-06-25T12:00:00Z",
    )

    assert first.memory_id == second.memory_id
    assert second.status == "duplicate_existing"
    assert second.local_memory_store_mutated is False
    assert len(registry.items_by_id) == 1


def test_165p_owner_can_add_edit_pin_and_forget_local_memory():
    registry = MemoryStoreRegistry()

    add_receipt = add_memory_to_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
        content="I prefer short meeting prep packs.",
        memory_type="owner_preference",
        approved_at="2026-06-25T12:00:00Z",
    )
    edit_receipt = edit_memory_in_store(
        registry=registry,
        memory_id=add_receipt.memory_id,
        content="I prefer short, action-first meeting prep packs.",
    )
    pin_receipt = pin_memory_in_store(registry=registry, memory_id=add_receipt.memory_id)
    pinned_item = registry.get_item(add_receipt.memory_id)
    forget_receipt = forget_memory_in_store(registry=registry, memory_id=add_receipt.memory_id)
    forgotten_item = registry.get_item(add_receipt.memory_id)

    assert add_receipt.status == "stored"
    assert edit_receipt.status == "edited"
    assert pin_receipt.status == "pinned"
    assert pinned_item is not None
    assert pinned_item.pinned is True
    assert pinned_item.content == "I prefer short, action-first meeting prep packs."
    assert forget_receipt.status == "forgotten"
    assert forgotten_item is not None
    assert forgotten_item.status == "forgotten"
    assert forgotten_item.pinned is False


def test_165p_active_store_items_export_to_existing_memory_center_visibility_surface():
    registry = MemoryStoreRegistry()
    add_receipt = add_memory_to_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
        content="Victor prefers ROI-first proposals.",
        memory_type="business_context_memory",
        approved_at="2026-06-25T12:00:00Z",
    )

    bundle = build_memory_center_source_bundle_from_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
    )
    snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=bundle,
    )
    rendered = render_memory_center_command_reply(snapshot)

    assert add_receipt.status == "stored"
    assert len(bundle.approved_memory_items) == 1
    assert bundle.approved_memory_items[0].item_id == add_receipt.memory_id
    assert snapshot.approved_total_count == 1
    assert "Victor prefers ROI-first proposals." in rendered
    assert "No Memory Center mutation was performed." in rendered


def test_165p_rendered_receipt_names_local_only_boundaries():
    registry = MemoryStoreRegistry()
    receipt = add_memory_to_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
        content="Use compact daily briefs.",
        approved_at="2026-06-25T12:00:00Z",
    )

    rendered = render_memory_store_receipt(receipt)

    assert "Memory Store" in rendered
    assert "Stage: 165P" in rendered
    assert "Local memory store mutation: true" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Gmail writes: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_165p_receipt_rejects_external_authority_expansion():
    registry = MemoryStoreRegistry()
    receipt = add_memory_to_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
        content="Use compact daily briefs.",
        approved_at="2026-06-25T12:00:00Z",
    )

    with pytest.raises(ValueError, match="must not expand external authority"):
        MemoryStoreReceipt(**{**asdict(receipt), "external_write_allowed": True})


def test_165p_reference_and_roadmap_close_memory_store_without_external_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "165P is local Memory Store v0 only." in reference
    assert "does not authorize Memory Center mutation" in reference
    assert "Calendar writes" in reference
    assert '"stage_id":"165P","stage_name":"Memory Store v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "197P and later remain unauthorized" in roadmap
