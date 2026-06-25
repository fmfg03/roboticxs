from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.inbox_item_decision import (
    INBOX_ITEM_DECISION_STAGE,
    InboxItemDecisionRecord,
    build_inbox_item_decision,
    render_inbox_item_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_147p_done_creates_local_receipt_without_deleting_evidence():
    record = build_inbox_item_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id="pending-memory:proposal-1",
        choice="done",
    )

    assert record.stage == INBOX_ITEM_DECISION_STAGE
    assert record.source_stage == "146P"
    assert record.choice == "done"
    assert record.decision_status == "marked_done_local_receipt"
    assert record.local_audit_created is True
    assert record.evidence_deleted is False
    assert record.persisted_state_written is False
    assert record.memory_center_mutated is False
    assert record.external_write_allowed is False


def test_147p_dismiss_creates_local_receipt_without_external_action():
    record = build_inbox_item_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id="meeting-suggestion:abc",
        choice="dismiss",
    )

    assert record.decision_status == "dismissed_local_receipt"
    assert record.worker_dispatch_allowed is False


def test_147p_render_names_disabled_effects():
    record = build_inbox_item_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id="pending-memory:proposal-1",
        choice="done",
    )
    rendered = render_inbox_item_decision(record)

    assert "Task Inbox Decision" in rendered
    assert "Stage: 147P" not in rendered
    assert "Status: done" in rendered
    assert "local receipt for the robot task inbox" in rendered
    assert "Evidence deleted: false" in rendered
    assert "Persisted state written: false" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "No inbox evidence was deleted." in rendered


def test_147p_record_rejects_authority_expansion():
    valid = build_inbox_item_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        item_id="pending-memory:proposal-1",
        choice="done",
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        InboxItemDecisionRecord(**{**asdict(valid), "persisted_state_written": True})


def test_147p_roadmap_records_inbox_decision_and_later_closed_stages():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"147P","stage_name":"Inbox Resolve / Dismiss v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "148P later added local non-authority loop handoff evidence only" in roadmap
    assert "149P later added local read-only runtime doctor diagnostics only" in roadmap
    assert "150P later added customer-facing Telegram product shell copy only" in roadmap
    assert "151P later added customer-facing Meeting Prep Pack product flow only" in roadmap
    assert "168P and later remain unauthorized" in roadmap
