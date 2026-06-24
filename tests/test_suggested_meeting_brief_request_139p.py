from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.suggested_meeting_brief_request import (
    SUGGESTED_MEETING_BRIEF_REQUEST_STAGE,
    SuggestedMeetingBriefRequestRecord,
    build_suggested_meeting_brief_request,
    render_suggested_meeting_brief_request,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/suggested_meeting_brief_request.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event(**overrides) -> CalendarEventSnapshot:
    values = {
        "event_id": "evt-139p-client-demo",
        "summary": "Client demo prep meeting",
        "start": "2026-06-25T10:00:00-06:00",
        "end": "2026-06-25T10:30:00-06:00",
        "all_day": False,
        "location": "Google Meet",
        "description_preview": "Review proposal context and prepare open questions.",
        "organizer_email": "owner@example.com",
        "attendee_count": 3,
        "html_link": "https://calendar.google.com/event?eid=139p",
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


def suggestion_scan(*events: CalendarEventSnapshot, ok: bool = True, error_code: str | None = None):
    context_scan = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(*events, ok=ok, error_code=error_code),
    )
    return build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan,
    )


def test_139p_owner_requested_suggested_meeting_brief_renders_selected_suggestion_only():
    scan = suggestion_scan(event())
    suggestion = scan.suggestions[0]

    record = build_suggested_meeting_brief_request(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=suggestion.suggestion_id,
        suggestion_scan=scan,
    )

    assert record.stage == SUGGESTED_MEETING_BRIEF_REQUEST_STAGE
    assert record.status == "completed"
    assert record.source_stage == "138P"
    assert record.suggestion_id == suggestion.suggestion_id
    assert record.selected_suggestion == suggestion
    assert record.owner_requested is True
    assert record.suggestion_validated is True
    assert record.read_only is True
    assert record.automatic_execution is False
    assert record.callback_binding_allowed is False
    assert record.followup_intent_created is False
    assert record.async_delegation_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.external_write_allowed is False
    assert record.calendar_write_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert "Prepared an owner-requested brief for Client demo prep meeting." in record.headline
    assert "Review the objective for Client demo prep meeting." in record.preparation_checklist


def test_139p_unknown_or_stale_suggestion_id_fails_closed_without_brief():
    record = build_suggested_meeting_brief_request(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="missing-suggestion-id",
        suggestion_scan=suggestion_scan(event()),
    )

    assert record.status == "blocked_suggestion_not_found"
    assert record.error_code == "suggestion_not_found"
    assert record.selected_suggestion is None
    assert record.suggestion_validated is False
    assert record.preparation_checklist == ()
    assert "No suggested meeting brief was rendered." in record.watchpoints
    assert record.external_write_allowed is False
    assert record.calendar_write_allowed is False
    assert record.memory_center_mutated is False


def test_139p_calendar_unavailable_fails_closed():
    record = build_suggested_meeting_brief_request(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="any-suggestion-id",
        suggestion_scan=suggestion_scan(ok=False, error_code="missing_access_token"),
    )

    assert record.status == "blocked_calendar_unavailable"
    assert record.error_code == "missing_access_token"
    assert record.suggestion_validated is False
    assert "Calendar context is unavailable" in record.headline
    assert record.external_write_allowed is False


def test_139p_rendered_brief_names_owner_request_and_boundaries():
    scan = suggestion_scan(event())
    record = build_suggested_meeting_brief_request(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
    )

    rendered = render_suggested_meeting_brief_request(record)

    assert "Suggested Meeting Brief" in rendered
    assert "Stage: 139P" in rendered
    assert "Source stage: 138P" in rendered
    assert "Owner requested: true" in rendered
    assert "Suggestion validated: true" in rendered
    assert "Automatic execution: disabled" in rendered
    assert "Follow-up intent: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "LLM/model calls: disabled" in rendered
    assert "No external action was taken." in rendered


def test_139p_record_rejects_authority_expansion():
    scan = suggestion_scan(event())
    valid = build_suggested_meeting_brief_request(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        SuggestedMeetingBriefRequestRecord(
            **{**asdict(valid), "model_call_allowed": True}
        )


def test_139p_module_declares_no_callback_memory_model_tool_worker_or_calendar_write_authority():
    text = MODULE_PATH.read_text()

    assert "callback_binding_allowed: bool" in text
    assert "followup_intent_created: bool" in text
    assert "memory_write_allowed: bool" in text
    assert "memory_center_mutated: bool" in text
    assert "proposed_memory_written: bool" in text
    assert "calendar_write_allowed: bool" in text
    assert "model_call_allowed: bool" in text
    assert "tool_call_allowed: bool" in text
    assert "worker_dispatch_allowed: bool" in text


def test_139p_roadmap_records_requested_suggested_brief_and_blocks_140p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"139P","stage_name":"Owner-Requested Suggested Meeting Brief v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "140P and later remain unauthorized" in roadmap
