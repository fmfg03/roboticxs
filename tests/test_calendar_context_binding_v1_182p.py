from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_binding_v1 import (
    CALENDAR_CONTEXT_BINDING_V1_STAGE,
    CALENDAR_CONTEXT_BINDING_V1_STATUS,
    CalendarContextBindingV1Record,
    CalendarContextSourceTrace,
    append_calendar_source_trace,
    build_calendar_context_binding_v1_record,
    build_calendar_context_source_trace,
    render_calendar_context_binding_v1_record,
    render_calendar_context_source_trace,
)
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CALENDAR_CONTEXT_BINDING_V1_182P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def calendar_result_with_event() -> CalendarReadResult:
    return CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-26T09:00:00-06:00",
        window_end="2026-06-27T09:00:00-06:00",
        events=(
            CalendarEventSnapshot(
                event_id="evt-182p-demo",
                summary="Victor kickoff prep",
                start="2026-06-26T11:00:00-06:00",
                end="2026-06-26T11:30:00-06:00",
                all_day=False,
                location="Google Meet",
                description_preview="Review kickoff notes.",
                organizer_email="owner@example.com",
                attendee_count=2,
                html_link="https://calendar.google.com/event?eid=182",
                source="google_calendar_readonly",
            ),
        ),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def unavailable_calendar_result() -> CalendarReadResult:
    return CalendarReadResult(
        ok=False,
        calendar_id="primary",
        window_start="2026-06-26T09:00:00-06:00",
        window_end="2026-06-27T09:00:00-06:00",
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code="missing_access_token",
        error_message="missing access token",
    )


def test_182p_connected_calendar_result_builds_source_trace():
    trace = build_calendar_context_source_trace(calendar_result=calendar_result_with_event())
    rendered = render_calendar_context_source_trace(trace)

    assert trace.source_name == "google_calendar_readonly"
    assert trace.status == "connected"
    assert trace.calendar_id == "primary"
    assert trace.blocked_reason is None
    assert trace.event_refs == ("evt-182p-demo | Victor kickoff prep | 2026-06-26T11:00:00-06:00",)
    assert "- Calendar: connected" in rendered
    assert "- Events used:" in rendered
    assert "Victor kickoff prep" in rendered
    assert "- Writes: disabled" in rendered


def test_182p_unavailable_calendar_result_fails_closed_with_checkup_guidance():
    trace = build_calendar_context_source_trace(calendar_result=unavailable_calendar_result())
    rendered = render_calendar_context_source_trace(trace)

    assert trace.status == "not_connected"
    assert trace.blocked_reason == "missing_access_token"
    assert "- Calendar: not_connected" in rendered
    assert "- Reason: missing_access_token" in rendered
    assert "- Next: run /checkup" in rendered
    assert "- Events used: none" in rendered


def test_182p_binding_record_declares_read_only_boundaries():
    record = build_calendar_context_binding_v1_record(calendar_result=calendar_result_with_event())
    rendered = render_calendar_context_binding_v1_record(record)

    assert record.stage == CALENDAR_CONTEXT_BINDING_V1_STAGE
    assert record.status == CALENDAR_CONTEXT_BINDING_V1_STATUS
    assert record.calendar_connected is True
    assert record.calendar_event_count == 1
    assert record.read_only is True
    assert record.calendar_write_allowed is False
    assert record.gmail_read_allowed is False
    assert record.gmail_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert "Calendar Context Binding v1" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_182p_append_source_trace_does_not_include_secrets():
    trace = build_calendar_context_source_trace(calendar_result=calendar_result_with_event())
    rendered = append_calendar_source_trace("Today\n\nStatus: completed", trace)

    assert rendered.startswith("Today")
    assert "Source trace:" in rendered
    for forbidden in ("access-token", "refresh-token", "client-secret", "Authorization", "Bearer"):
        assert forbidden not in rendered


def test_182p_rejects_authority_expansion():
    trace = build_calendar_context_source_trace(calendar_result=calendar_result_with_event())
    record = build_calendar_context_binding_v1_record(calendar_result=calendar_result_with_event())

    with pytest.raises(ValueError, match="must not allow Calendar writes"):
        CalendarContextSourceTrace(**{**asdict(trace), "calendar_write_allowed": True})
    with pytest.raises(ValueError, match="must not expand authority"):
        CalendarContextBindingV1Record(**{**asdict(record), "external_write_allowed": True})


def test_182p_reference_and_roadmap_close_calendar_binding_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "182P - Calendar Context Binding v1" in reference
    assert "182P is read-only Calendar binding only." in reference
    assert "OAuth token refresh" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"182P","stage_name":"Calendar Context Binding v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "214P and later remain unauthorized" in roadmap
