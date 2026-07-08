from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_draft_queue import build_action_draft_queue, render_action_draft_queue
from app.draft_quality_engine import (
    DRAFT_QUALITY_ENGINE_STAGE,
    DraftQualityReview,
    build_draft_quality_review,
    render_draft_quality_review,
)
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DRAFT_QUALITY_ENGINE_195P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_195p_review_exposes_intent_audience_tone_sources_and_risk():
    draft = draft_queue().drafts[0]
    review = build_draft_quality_review(draft)
    rendered = "\n".join(render_draft_quality_review(review))

    assert review.stage == DRAFT_QUALITY_ENGINE_STAGE
    assert review.intent == "follow_up_reply"
    assert review.tone == "concise_professional"
    assert review.approval_state == "pending_user_confirmation"
    assert "stage:172P" in review.source_basis
    assert "intent: follow_up_reply" in rendered
    assert "sources:" in rendered
    assert "editable body:" in rendered
    assert review.gmail_send_allowed is False
    assert review.external_write_allowed is False


def test_195p_action_draft_queue_renders_quality_block():
    rendered = render_action_draft_queue(draft_queue())

    assert "Quality:" in rendered
    assert "intent:" in rendered
    assert "audience:" in rendered
    assert "tone:" in rendered
    assert "risk:" in rendered
    assert "approval: pending_user_confirmation" in rendered
    assert "Gmail send: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_195p_rejects_authority_expansion():
    review = build_draft_quality_review(draft_queue().drafts[0])

    with pytest.raises(ValueError, match="must not expand authority"):
        DraftQualityReview(**{**asdict(review), "gmail_send_allowed": True})


def test_195p_reference_and_roadmap_close_quality_without_memory_intelligence():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "195P improves local draft review quality" in reference
    assert "no memory intelligence" in reference
    assert '"stage_id":"195P","stage_name":"Draft Quality Engine v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "217P and later remain unauthorized" in roadmap


def draft_queue():
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="owner-195p",
        robot_id="robot-195p",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-195p",
                owner_id="owner-195p",
                robot_id="robot-195p",
                trigger_type="email_thread_no_followup",
                title="Draft client follow-up",
                summary="client thread has no follow-up",
                source_refs=("gmail:thread-195p",),
            ),
        ),
    )
    inbox = build_suggestion_inbox(owner_id="owner-195p", robot_id="robot-195p", suggestions=suggestions)
    decision = build_suggestion_decision_receipt(
        owner_id="owner-195p",
        robot_id="robot-195p",
        suggestion_id=inbox.items[0].suggestion_id,
        choice="create_draft",
        inbox=inbox,
    )
    return build_action_draft_queue(owner_id="owner-195p", robot_id="robot-195p", decisions=(decision,))
