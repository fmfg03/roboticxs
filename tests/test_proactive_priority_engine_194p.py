from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.proactive_priority_engine import (
    PROACTIVE_PRIORITY_ENGINE_STAGE,
    ProactivePriorityDecision,
    build_proactive_priority_decision,
    render_proactive_priority_decision,
)
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.suggestion_inbox import build_suggestion_inbox, render_suggestion_inbox


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PROACTIVE_PRIORITY_ENGINE_194P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_194p_classifies_time_sensitive_meeting_as_p0():
    decision = build_proactive_priority_decision(suggestion("pdf_received_meeting_tomorrow", "PDF for meeting tomorrow"))
    rendered = "\n".join(render_proactive_priority_decision(decision))

    assert decision.stage == PROACTIVE_PRIORITY_ENGINE_STAGE
    assert decision.priority == "P0"
    assert decision.confidence == "high"
    assert "time_sensitive" in decision.reason_codes
    assert "meeting_related" in decision.reason_codes
    assert "priority: P0" in rendered
    assert "priority source trace: calendar:evt-194p, document:doc-194p" in rendered
    assert decision.no_action_taken is True
    assert decision.external_write_allowed is False


def test_194p_suggestion_inbox_displays_priority_without_execution():
    inbox = build_suggestion_inbox(
        owner_id="owner-194p",
        robot_id="robot-194p",
        suggestions=(suggestion("email_thread_no_followup", "Client email needs follow-up"),),
    )
    rendered = render_suggestion_inbox(inbox)

    assert "priority: P1" in rendered
    assert "priority confidence:" in rendered
    assert "priority reasons:" in rendered
    assert "safe next action:" in rendered
    assert "No action has been taken." in rendered
    assert "Execution: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_194p_rejects_authority_expansion():
    decision = build_proactive_priority_decision(suggestion("open_task_due_soon", "Task due soon"))

    with pytest.raises(ValueError, match="must not expand authority"):
        ProactivePriorityDecision(**{**asdict(decision), "model_call_allowed": True})


def test_194p_reference_and_roadmap_close_priority_without_drafts():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "194P classifies suggestion inbox items" in reference
    assert "no draft quality engine" in reference
    assert '"stage_id":"194P","stage_name":"Proactive Priority Engine v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "216P and later remain unauthorized" in roadmap


def suggestion(trigger_type: str, summary: str):
    return build_proactive_suggestion_loop_records(
        owner_id="owner-194p",
        robot_id="robot-194p",
        signals=(
            ProactiveSuggestionSignal(
                signal_id=f"signal-{trigger_type}",
                owner_id="owner-194p",
                robot_id="robot-194p",
                trigger_type=trigger_type,
                title=summary,
                summary=summary,
                source_refs=("calendar:evt-194p", "document:doc-194p"),
            ),
        ),
    )[0]
