from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_scan import (
    CALENDAR_CONTEXT_SCAN_STAGE,
    CalendarContextCandidateRecord,
    build_calendar_context_scan_record,
    render_calendar_context_scan,
)
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/calendar_context_scan.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event(**overrides) -> CalendarEventSnapshot:
    values = {
        "event_id": "evt-asisint-followup",
        "summary": "ASISINT follow-up meeting",
        "start": "2026-06-25T10:00:00-06:00",
        "end": "2026-06-25T10:30:00-06:00",
        "all_day": False,
        "location": "Google Meet",
        "description_preview": "Review TrakIT context and prepare next steps.",
        "organizer_email": "owner@example.com",
        "attendee_count": 2,
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


def test_137p_calendar_events_produce_bounded_context_candidates_without_memory_writes():
    record = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(event()),
    )

    assert record.scan_stage == CALENDAR_CONTEXT_SCAN_STAGE
    assert record.status == "completed"
    assert len(record.candidates) == 3
    assert {candidate.candidate_type for candidate in record.candidates} == {
        "business_context_candidate",
        "meeting_prep_context_candidate",
        "relationship_context_candidate",
    }
    assert all(candidate.proposed_memory is False for candidate in record.candidates)
    assert all(candidate.memory_write_allowed is False for candidate in record.candidates)
    assert record.proposed_memory_count == 0
    assert record.memory_center_mutated is False
    assert record.external_write_allowed is False
    assert record.calendar_write_allowed is False
    assert record.model_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert "Context candidates are review material only, not canonical memory." in record.watchpoints


def test_137p_calendar_context_scan_fails_closed_when_calendar_is_unavailable():
    record = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(ok=False, error_code="missing_access_token"),
    )

    assert record.status == "blocked_calendar_unavailable"
    assert record.error_code == "missing_access_token"
    assert record.candidates == ()
    assert record.proposed_memory_count == 0
    assert record.memory_write_allowed is False
    assert "Calendar read failed closed: missing_access_token." in record.watchpoints


def test_137p_calendar_context_scan_has_no_candidate_empty_state():
    record = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(
            event(
                event_id="evt-focus",
                summary="Focus block",
                description_preview=None,
                attendee_count=0,
                location=None,
            )
        ),
    )

    assert record.status == "no_context_candidates"
    assert record.candidates == ()


def test_137p_rendered_scan_output_names_boundaries():
    record = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(event()),
    )

    rendered = render_calendar_context_scan(record)

    assert "Calendar Context Scan" in rendered
    assert "Stage: 137P" in rendered
    assert "Candidates: 3" in rendered
    assert "Proposed memories written: 0" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "ASISINT may be active business context" in rendered


def test_137p_candidate_record_rejects_authority_expansion():
    valid = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(event()),
    ).candidates[0]

    with pytest.raises(ValueError, match="must not become proposed memory automatically"):
        CalendarContextCandidateRecord(
            **{**asdict(valid), "proposed_memory": True}
        )


def test_137p_module_declares_no_write_or_model_authority():
    text = MODULE_PATH.read_text()

    assert "memory_write_allowed: bool" in text
    assert "memory_center_mutated: bool" in text
    assert "external_write_allowed: bool" in text
    assert "calendar_write_allowed: bool" in text
    assert "model_call_allowed: bool" in text
    assert "worker_dispatch_allowed: bool" in text
    assert "run_google_calendar_readonly_connector" in text


def test_137p_roadmap_records_calendar_context_scan_and_blocks_138p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"137P","stage_name":"Context Scan from Calendar v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "138P and later remain unauthorized" in roadmap
    assert "It does not write ProposedMemory or Memory Center records automatically." in roadmap
