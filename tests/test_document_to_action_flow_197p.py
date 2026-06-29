from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.document_review_pack_v1 import build_document_review_pack_v1_record, render_document_review_pack_v1
from app.document_to_action_flow import (
    DOCUMENT_TO_ACTION_FLOW_STAGE,
    DocumentToActionFlowRecord,
    build_document_to_action_flow,
    render_document_to_action_flow,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DOCUMENT_TO_ACTION_FLOW_197P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_197p_builds_safe_action_candidates_from_completed_review():
    flow = build_document_to_action_flow(review())
    rendered = render_document_to_action_flow(flow)

    assert flow.stage == DOCUMENT_TO_ACTION_FLOW_STAGE
    assert flow.status == "actions_suggested"
    assert [action.action_type for action in flow.actions] == [
        "save_memory",
        "create_questions",
        "prepare_prep_pack",
        "create_draft",
        "export_review",
    ]
    assert "Document Actions" in rendered
    assert "approval:" in rendered
    assert "source:" in rendered
    assert flow.memory_center_mutated is False
    assert flow.draft_created is False
    assert flow.export_created is False
    assert flow.external_write_allowed is False


def test_197p_document_review_render_includes_actions_without_writes():
    rendered = render_document_review_pack_v1(review())

    assert "Document Actions" in rendered
    assert "save_memory" in rendered
    assert "create_draft" in rendered
    assert "Professional advice: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_197p_blocked_review_has_no_actions():
    blocked = build_document_review_pack_v1_record(
        owner_id="owner-197p",
        robot_id="robot-197p",
        document_title="blocked.txt",
        extracted_text="",
    )
    flow = build_document_to_action_flow(blocked)

    assert flow.status == "blocked_no_document_actions"
    assert flow.actions == ()


def test_197p_rejects_authority_expansion():
    flow = build_document_to_action_flow(review())

    with pytest.raises(ValueError, match="must not expand authority"):
        DocumentToActionFlowRecord(**{**asdict(flow), "draft_created": True})


def test_197p_reference_and_roadmap_close_document_actions_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "197P turns a completed draft-only document review" in reference
    assert "These are suggestions only" in reference
    assert '"stage_id":"197P","stage_name":"Document-to-Action Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "198P and later remain unauthorized" in roadmap


def review():
    return build_document_review_pack_v1_record(
        owner_id="owner-197p",
        robot_id="robot-197p",
        document_title="pilot-agreement.txt",
        extracted_text="This agreement has deadline, payment, approval, and notice terms to review before the meeting.",
    )
