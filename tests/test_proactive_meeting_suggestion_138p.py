from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.proactive_meeting_suggestion import (
    PROACTIVE_MEETING_SUGGESTION_STAGE,
    ProactiveMeetingBriefSuggestionRecord,
    build_proactive_meeting_suggestion_scan,
    render_proactive_meeting_suggestion_scan,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_meeting_suggestion.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event(**overrides) -> CalendarEventSnapshot:
    values = {
        "event_id": "evt-client-demo",
        "summary": "Client demo prep meeting",
        "start": "2026-06-25T10:00:00-06:00",
        "end": "2026-06-25T10:30:00-06:00",
        "all_day": False,
        "location": "Google Meet",
        "description_preview": "Review proposal context and prepare open questions.",
        "organizer_email": "owner@example.com",
        "attendee_count": 3,
        "html_link": "https://calendar.google.com/event?eid=1",
        "source": "google_calendar_readonly",
    }
    values.update(overrides)
    return CalendarEventSnapshot(**values)


def calendar_result(*events: CalendarEventSnapshot, ok: bool = True, error_code: str | None = None) -> CalendarReadResult:
    return CalendarReadResult(
        ok=ok,
        calendar_id="primary",
        window_start="2026-06-24T10:00:00-06:00",
        window_end="2026-07-01T10:00:00-06:00",
        events=events,
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=error_code,
        error_message=error_code,
    )


def context_scan(*events: CalendarEventSnapshot, ok: bool = True, error_code: str | None = None):
    return build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(*events, ok=ok, error_code=error_code),
    )


def test_138p_detects_meetings_that_deserve_brief_suggestions_without_execution():
    record = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan(event()),
    )

    assert record.suggestion_stage == PROACTIVE_MEETING_SUGGESTION_STAGE
    assert record.source_stage == "137P"
    assert record.status == "completed"
    assert len(record.suggestions) == 1
    suggestion = record.suggestions[0]
    assert suggestion.event_id == "evt-client-demo"
    assert suggestion.action_only is True
    assert suggestion.brief_executed is False
    assert "/brief" in suggestion.suggested_action
    assert record.brief_executions == 0
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.external_write_allowed is False
    assert record.calendar_write_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert "Suggestions are action-only and do not execute /brief automatically." in record.watchpoints


def test_138p_fails_closed_when_calendar_context_scan_is_unavailable():
    record = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan(ok=False, error_code="missing_access_token"),
    )

    assert record.status == "blocked_calendar_unavailable"
    assert record.error_code == "missing_access_token"
    assert record.suggestions == ()
    assert record.brief_executions == 0
    assert "No proactive meeting suggestion was sent automatically." in record.watchpoints


def test_138p_has_no_suggestion_empty_state_for_non_meeting_context():
    record = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan(
            event(
                event_id="evt-focus",
                summary="Focus block",
                description_preview=None,
                attendee_count=0,
                location=None,
            )
        ),
    )

    assert record.status == "no_meeting_suggestions"
    assert record.suggestions == ()


def test_138p_rendered_suggestions_name_action_only_boundaries():
    record = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan(event()),
    )

    rendered = render_proactive_meeting_suggestion_scan(record)

    assert "Proactive Meeting Suggestions" in rendered
    assert "Stage: 138P" in rendered
    assert "Action-only: true" in rendered
    assert "Briefs executed: 0" in rendered
    assert "Suggested action:" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "LLM/model calls: disabled" in rendered
    assert "No external action was taken." in rendered


def test_138p_suggestion_record_rejects_authority_expansion():
    valid = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan(event()),
    ).suggestions[0]

    with pytest.raises(ValueError, match="must not execute a brief automatically"):
        ProactiveMeetingBriefSuggestionRecord(
            **{**asdict(valid), "brief_executed": True}
        )


def test_138p_module_declares_no_write_model_tool_or_worker_authority():
    text = MODULE_PATH.read_text()

    assert "memory_write_allowed: bool" in text
    assert "memory_center_mutated: bool" in text
    assert "external_write_allowed: bool" in text
    assert "calendar_write_allowed: bool" in text
    assert "model_call_allowed: bool" in text
    assert "tool_call_allowed: bool" in text
    assert "worker_dispatch_allowed: bool" in text
    assert "run_calendar_context_scan" in text


def test_138p_roadmap_records_proactive_meeting_suggestion_and_blocks_139p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"138P","stage_name":"Proactive Meeting Suggestion v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "140P later added a DeerFlow docs/test-only pattern review only. 141P and later remain unauthorized" in roadmap
    assert "It suggests an action only and does not execute a meeting brief automatically." in roadmap
