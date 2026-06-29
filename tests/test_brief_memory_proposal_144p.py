from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.brief_memory_proposal import (
    BRIEF_MEMORY_PROPOSAL_STAGE,
    BriefMemoryProposalRecord,
    build_brief_memory_proposal_record,
    render_brief_memory_proposal_record,
)
from app.meeting_prep_pack import MEETING_PREP_PACK_STAGE, build_meeting_prep_pack
from tests.test_meeting_prep_pack_143p import memory_snapshot, suggestion_scan


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/brief_memory_proposal.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def prep_pack():
    scan = suggestion_scan()
    return build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )


def test_144p_builds_pending_owner_review_candidates_without_writes():
    record = build_brief_memory_proposal_record(prep_pack=prep_pack())

    assert record.stage == BRIEF_MEMORY_PROPOSAL_STAGE
    assert record.source_stage == MEETING_PREP_PACK_STAGE
    assert record.status == "completed_with_candidates"
    assert len(record.candidates) == 1
    candidate = record.candidates[0]
    assert candidate.stage == "144P"
    assert candidate.source_stage == MEETING_PREP_PACK_STAGE
    assert candidate.status == "pending_owner_review"
    assert candidate.treated_as_fact is False
    assert candidate.approval_command == f"/memory_approve {candidate.candidate_id}"
    assert candidate.rejection_command == f"/memory_reject {candidate.candidate_id}"
    assert record.read_only is True
    assert record.owner_review_required is True
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.approval_decision_created is False
    assert record.external_write_allowed is False


def test_144p_candidate_ids_are_deterministic_for_same_prep_pack():
    first = build_brief_memory_proposal_record(prep_pack=prep_pack())
    second = build_brief_memory_proposal_record(prep_pack=prep_pack())

    assert first.candidates[0].candidate_id == second.candidates[0].candidate_id


def test_144p_non_completed_prep_pack_produces_no_candidates():
    scan = suggestion_scan()
    blocked = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="missing-suggestion",
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )

    record = build_brief_memory_proposal_record(prep_pack=blocked)

    assert record.status == "empty"
    assert record.candidates == ()
    assert record.proposed_memory_written is False


def test_144p_render_marks_candidates_as_pending_not_facts():
    record = build_brief_memory_proposal_record(prep_pack=prep_pack())
    rendered = render_brief_memory_proposal_record(record)

    assert "Brief Memory Proposals" in rendered
    assert "Stage: 144P" in rendered
    assert "Owner review required: true" in rendered
    assert "Treated as facts: false" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Approval decisions: disabled in 144P" in rendered
    assert "pending owner review" in rendered
    assert "No memory was written." in rendered


def test_144p_record_rejects_authority_expansion():
    valid = build_brief_memory_proposal_record(prep_pack=prep_pack())

    with pytest.raises(ValueError, match="must not expand authority"):
        BriefMemoryProposalRecord(**{**asdict(valid), "proposed_memory_written": True})


def test_144p_module_declares_no_write_or_approval_decision_authority():
    text = MODULE_PATH.read_text()

    assert "memory_write_allowed: bool" in text
    assert "memory_center_mutated: bool" in text
    assert "proposed_memory_written: bool" in text
    assert "approval_decision_created: bool" in text
    assert "model_call_allowed: bool" in text
    assert "tool_call_allowed: bool" in text


def test_144p_roadmap_records_brief_memory_proposal_and_blocks_145p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"144P","stage_name":"Brief-Derived Memory Proposal v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "215P and later remain unauthorized" in roadmap
