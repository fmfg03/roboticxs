from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_draft_queue import (
    ACTION_DRAFT_QUEUE_STAGE,
    ActionDraftQueue,
    ActionDraftRecord,
    build_action_draft_queue,
    render_action_draft_queue,
)
from app.proactive_suggestion_loop import (
    ProactiveSuggestionSignal,
    build_proactive_suggestion_loop_records,
)
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/ACTION_DRAFT_QUEUE_177P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def draft_decision(choice: str = "create_draft"):
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-177p",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="email_thread_no_followup",
                title="Draft follow-up to Victor",
                summary="recent thread has no follow-up",
                source_refs=("gmail:thread-1",),
            ),
        ),
    )
    inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=suggestions,
    )
    return build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=inbox.items[0].suggestion_id,
        choice=choice,
        inbox=inbox,
    )


def test_177p_builds_local_action_draft_from_create_draft_decision_only():
    queue = build_action_draft_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        decisions=(draft_decision(), draft_decision("dismiss")),
    )

    assert queue.stage == ACTION_DRAFT_QUEUE_STAGE
    assert queue.status == "pending_drafts"
    assert len(queue.drafts) == 1
    assert len(queue.skipped_decision_ids) == 1
    draft = queue.drafts[0]
    assert draft.stage == ACTION_DRAFT_QUEUE_STAGE
    assert draft.draft_type == "follow_up"
    assert draft.status == "pending_user_confirmation"
    assert draft.source_suggestion_title == "Draft follow-up to Victor"
    assert draft.local_draft_record_created is True
    assert draft.requires_user_confirmation is True
    assert draft.gmail_draft_created is False
    assert draft.gmail_send_allowed is False
    assert draft.gmail_modify_allowed is False
    assert draft.calendar_write_allowed is False
    assert draft.task_persisted is False
    assert draft.memory_center_mutated is False
    assert draft.model_call_allowed is False
    assert draft.tool_call_allowed is False
    assert draft.worker_dispatch_allowed is False
    assert draft.external_write_allowed is False


def test_177p_empty_queue_is_explicit_and_non_authority_expanding():
    queue = build_action_draft_queue(owner_id="local-owner", robot_id="roboticxs-dev")

    assert queue.status == "empty"
    assert queue.drafts == ()
    assert queue.local_queue_created is True
    assert queue.no_external_action_taken is True
    assert queue.gmail_draft_creation_allowed is False
    assert queue.gmail_send_allowed is False
    assert queue.gmail_modify_allowed is False
    assert queue.calendar_write_allowed is False
    assert queue.task_persistence_allowed is False
    assert queue.memory_center_mutation_allowed is False
    assert queue.model_call_allowed is False
    assert queue.tool_call_allowed is False
    assert queue.worker_dispatch_allowed is False
    assert queue.external_write_allowed is False


def test_177p_rejects_owner_robot_mismatch_and_authority_expansion():
    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_action_draft_queue(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            decisions=(draft_decision(),),
        )

    valid_queue = build_action_draft_queue(owner_id="local-owner", robot_id="roboticxs-dev")
    with pytest.raises(ValueError, match="must not expand authority"):
        ActionDraftQueue(**{**asdict(valid_queue), "external_write_allowed": True})

    valid_draft = build_action_draft_queue(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        decisions=(draft_decision(),),
    ).drafts[0]
    with pytest.raises(ValueError, match="must not expand authority"):
        ActionDraftRecord(**{**asdict(valid_draft), "gmail_draft_created": True})


def test_177p_render_declares_local_queue_and_boundaries():
    rendered = render_action_draft_queue(
        build_action_draft_queue(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            decisions=(draft_decision(),),
        )
    )

    assert "Action Draft Queue" in rendered
    assert "Stage: 177P" in rendered
    assert "Status: pending_drafts" in rendered
    assert "Draft for: Draft follow-up to Victor" in rendered
    assert "Local draft records: enabled" in rendered
    assert "User confirmation required: true" in rendered
    assert "Gmail draft creation: disabled" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Task persistence: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_177p_reference_and_roadmap_close_action_draft_queue_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "177P is Action Draft Queue v0 only." in reference
    assert "Gmail draft creation" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"177P","stage_name":"Action Draft Queue v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "193P and later remain unauthorized" in roadmap
