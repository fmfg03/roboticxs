from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.proactive_suggestion_loop import (
    PROACTIVE_SUGGESTION_LOOP_STAGE,
    ProactiveSuggestionLoopRecord,
    ProactiveSuggestionSignal,
    build_proactive_suggestion_loop_records,
    render_proactive_suggestion,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PROACTIVE_SUGGESTION_LOOP_170P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def signal(trigger_type: str, signal_id: str = "signal-1") -> ProactiveSuggestionSignal:
    return ProactiveSuggestionSignal(
        signal_id=signal_id,
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        trigger_type=trigger_type,
        title="Useful next step",
        summary="related context is available",
        source_refs=("calendar:evt-1", "gmail:thread-1"),
    )


@pytest.mark.parametrize(
    ("trigger_type", "next_step"),
    [
        ("upcoming_meeting_no_prep", "offer_prep_pack"),
        ("meeting_related_document", "offer_prep_pack"),
        ("email_thread_no_followup", "offer_followup_draft"),
        ("pdf_received_meeting_tomorrow", "offer_document_review_pack"),
        ("open_task_due_soon", "offer_task_summary"),
    ],
)
def test_170p_builds_local_suggestions_for_authorized_triggers(trigger_type: str, next_step: str):
    records = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(signal(trigger_type),),
    )

    assert len(records) == 1
    record = records[0]
    assert record.stage == PROACTIVE_SUGGESTION_LOOP_STAGE
    assert record.trigger_type == trigger_type
    assert record.suggested_next_step == next_step
    assert "Do you want" in record.suggestion_text
    assert record.local_deterministic is True
    assert record.live_send_allowed is False
    assert record.callback_binding_allowed is False
    assert record.execution_allowed is False
    assert record.connector_activation_allowed is False
    assert record.memory_write_allowed is False
    assert record.external_write_allowed is False
    assert record.worker_dispatch_allowed is False


def test_170p_filters_other_owner_signals_and_dedupes():
    records = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            signal("upcoming_meeting_no_prep", "same"),
            signal("upcoming_meeting_no_prep", "same"),
            ProactiveSuggestionSignal(
                signal_id="other",
                owner_id="other-owner",
                robot_id="roboticxs-dev",
                trigger_type="open_task_due_soon",
                title="Other",
                summary="not in scope",
                source_refs=(),
            ),
        ),
    )

    assert len(records) == 1


def test_170p_render_declares_no_action_taken_and_boundaries():
    rendered = render_proactive_suggestion(
        build_proactive_suggestion_loop_records(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            signals=(signal("pdf_received_meeting_tomorrow"),),
        )[0]
    )

    assert "Proactive Suggestion" in rendered
    assert "Stage: 170P" in rendered
    assert "No action has been taken." in rendered
    assert "Live send: disabled" in rendered
    assert "Callbacks: disabled" in rendered
    assert "Execution: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_170p_rejects_unauthorized_signals_and_authority_expansion():
    with pytest.raises(ValueError, match="authorized read-only"):
        ProactiveSuggestionSignal(
            signal_id="bad",
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            trigger_type="open_task_due_soon",
            title="Bad",
            summary="bad",
            source_refs=(),
            authorized_read_only=False,
        )

    valid = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(signal("open_task_due_soon"),),
    )[0]
    with pytest.raises(ValueError, match="must not expand authority"):
        ProactiveSuggestionLoopRecord(**{**asdict(valid), "execution_allowed": True})


def test_170p_reference_and_roadmap_close_proactive_loop_without_execution():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "170P is Proactive Suggestion Loop v0 only." in reference
    assert "No action has been taken" in reference
    assert "does not authorize live Telegram sends" in reference
    assert '"stage_id":"170P","stage_name":"Proactive Suggestion Loop v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "215P and later remain unauthorized" in roadmap
