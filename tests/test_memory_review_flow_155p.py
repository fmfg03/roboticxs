from __future__ import annotations

from pathlib import Path

from app.brief_memory_approval import (
    build_brief_memory_approval_decision,
    render_brief_memory_approval_decision,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
    render_memory_pending_command_reply,
)
from tests.test_telegram_memory_center_commands_136p import PendingProposalFixture


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_REVIEW_FLOW_155P_v0_1.md"


def pending_snapshot(*proposals: object):
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=proposals,
        ),
    )


def test_155p_memory_pending_renders_review_states_and_not_fact_boundary():
    rendered = render_memory_pending_command_reply(pending_snapshot(PendingProposalFixture()))

    assert rendered.startswith("Memory Review\n")
    assert "Stage: 136P" not in rendered
    assert "Status: pending owner review" in rendered
    assert "States:" in rendered
    assert "pending:" in rendered
    assert "approved pending writeback:" in rendered
    assert "rejected:" in rendered
    assert "not a fact yet:" in rendered
    assert "Pending review:" in rendered
    assert "pending | proposal-136p | business_context_candidate: ASISINT is an active client opportunity." in rendered
    assert "/memory_approve <candidate_id>" in rendered
    assert "/memory_reject <candidate_id>" in rendered
    assert "Memory writes: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Model calls: disabled" in rendered
    assert "No Memory Center mutation was performed." in rendered


def test_155p_memory_pending_empty_state_is_useful():
    rendered = render_memory_pending_command_reply(pending_snapshot())

    assert "Pending proposals: 0" in rendered
    assert "Empty: no pending memory proposals are visible right now." in rendered
    assert "not a fact yet:" in rendered
    assert "No pending proposal was approved, rejected, edited, or written." in rendered


def test_155p_approve_and_reject_decisions_are_local_receipts_only():
    approved = render_brief_memory_approval_decision(
        build_brief_memory_approval_decision(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            candidate_id="candidate-155p",
            choice="approve",
        )
    )
    rejected = render_brief_memory_approval_decision(
        build_brief_memory_approval_decision(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            candidate_id="candidate-155p",
            choice="reject",
        )
    )

    assert approved.startswith("Memory Review Decision\n")
    assert "Stage: 145P" not in approved
    assert "Status: approved pending writeback" in approved
    assert "Receipt status: approved_pending_writeback" in approved
    assert "Your robot does not remember this as a fact yet." in approved
    assert "Status: rejected" in rejected
    assert "Receipt status: rejected_no_write" in rejected
    for rendered in (approved, rejected):
        assert "Memory writes: disabled" in rendered
        assert "Memory Center mutation: disabled" in rendered
        assert "ProposedMemory writes: disabled" in rendered
        assert "Writeback executed: false" in rendered
        assert "Model calls: disabled" in rendered
        assert "No memory was written." in rendered


def test_155p_reference_and_roadmap_close_memory_review_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "155P is a customer-facing Telegram Memory Review stage." in reference
    assert "does not add new commands" in reference
    assert "mutate Memory Center" in reference
    assert "not facts yet" in reference
    assert '"stage_id":"155P","stage_name":"Memory Review Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "167P and later remain unauthorized" in roadmap
