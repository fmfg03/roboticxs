from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.brief_memory_approval import (
    BRIEF_MEMORY_APPROVAL_STAGE,
    BriefMemoryApprovalDecisionRecord,
    build_brief_memory_approval_decision,
    render_brief_memory_approval_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/brief_memory_approval.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_145p_approve_creates_local_decision_without_writeback():
    record = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="approve",
    )

    assert record.stage == BRIEF_MEMORY_APPROVAL_STAGE
    assert record.source_stage == "144P"
    assert record.choice == "approve"
    assert record.decision_status == "approved_pending_writeback"
    assert record.local_audit_created is True
    assert record.owner_requested is True
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.writeback_executed is False
    assert record.external_write_allowed is False


def test_145p_reject_creates_no_write_decision():
    record = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="reject",
    )

    assert record.decision_status == "rejected_no_write"
    assert record.writeback_executed is False


def test_145p_decision_ids_are_deterministic():
    first = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="approve",
    )
    second = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="approve",
    )

    assert first.decision_id == second.decision_id


def test_145p_render_names_no_memory_write():
    record = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="approve",
    )
    rendered = render_brief_memory_approval_decision(record)

    assert "Memory Review Decision" in rendered
    assert "Stage: 145P" not in rendered
    assert "Status: approved pending writeback" in rendered
    assert "Receipt status: approved_pending_writeback" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Writeback executed: false" in rendered
    assert "No memory was written." in rendered


def test_145p_record_rejects_authority_expansion():
    valid = build_brief_memory_approval_decision(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        candidate_id="candidate-145p",
        choice="approve",
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        BriefMemoryApprovalDecisionRecord(**{**asdict(valid), "writeback_executed": True})


def test_145p_module_declares_no_writeback_authority():
    text = MODULE_PATH.read_text()

    assert "memory_center_mutated: bool" in text
    assert "proposed_memory_written: bool" in text
    assert "writeback_executed: bool" in text
    assert "worker_dispatch_allowed: bool" in text


def test_145p_roadmap_records_brief_memory_approval_and_blocks_146p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"145P","stage_name":"Telegram Memory Approval for Brief Proposals v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "204P and later remain unauthorized" in roadmap
