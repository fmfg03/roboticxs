from __future__ import annotations

import json
from pathlib import Path

from app.calendar_backed_today_prep import (
    CALENDAR_BACKED_TODAY_PREP_STAGE,
    build_calendar_backed_today_prep_record,
    main,
    render_calendar_backed_today_prep_record,
    run_calendar_backed_today_prep,
)
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from tests.test_google_calendar_readonly_connector_133p import FakeGoogleCalendarHttpClient


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CALENDAR_BACKED_TODAY_PREP_162P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def calendar_result_with_event() -> CalendarReadResult:
    return CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-25T00:00:00-06:00",
        window_end="2026-06-26T00:00:00-06:00",
        events=(
            CalendarEventSnapshot(
                event_id="evt-162p-demo",
                summary="Client demo prep meeting",
                start="2026-06-25T10:00:00-06:00",
                end="2026-06-25T10:30:00-06:00",
                all_day=False,
                location="Google Meet",
                description_preview="Review proposal and follow-up notes.",
                organizer_email="owner@example.com",
                attendee_count=2,
                html_link="https://calendar.google.com/event?eid=162",
                source="google_calendar_readonly",
            ),
        ),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def test_162p_calendar_backed_today_prep_uses_read_only_calendar_event_for_today_and_prep():
    record = build_calendar_backed_today_prep_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result_with_event(),
    )

    assert record.stage == CALENDAR_BACKED_TODAY_PREP_STAGE
    assert record.status == "calendar_connected"
    assert record.calendar_connected is True
    assert record.calendar_event_count == 1
    assert record.prep_available is True
    assert record.selected_suggestion_id is not None
    assert "Client demo prep meeting" in record.today_reply
    assert "Meeting Prep Pack" in record.prep_reply
    assert "Client demo prep meeting" in record.prep_reply
    assert "Google Calendar read-only: connected (1 event(s))." in record.source_lines
    assert "Gmail: not connected." in record.unavailable_source_lines
    assert record.read_only is True
    assert record.calendar_write_allowed is False
    assert record.gmail_read_allowed is False
    assert record.gmail_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False


def test_162p_calendar_unavailable_fails_closed_with_setup_guidance():
    record = build_calendar_backed_today_prep_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=CalendarReadResult(
            ok=False,
            calendar_id="primary",
            window_start="2026-06-25T00:00:00-06:00",
            window_end="2026-06-26T00:00:00-06:00",
            events=(),
            read_only=True,
            external_writes=False,
            memory_mutation=False,
            error_code="missing_access_token",
            error_message="missing access token",
        ),
    )
    rendered = render_calendar_backed_today_prep_record(record)

    assert record.status == "calendar_unavailable"
    assert record.calendar_connected is False
    assert record.prep_available is False
    assert "Google Calendar read-only: unavailable (missing_access_token)." in record.unavailable_source_lines
    assert "Status: partial_calendar_unavailable" in record.today_reply
    assert "Status: blocked_calendar_backed_prep_unavailable" in record.prep_reply
    assert "- Calendar: not connected; read-only setup required." in record.prep_reply
    assert "Calendar writes: disabled" in rendered
    assert "Gmail reads: disabled" in rendered
    assert "No external action was taken." in rendered


def test_162p_run_path_uses_calendar_connector_shape_without_writes(monkeypatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-162p")
    client = FakeGoogleCalendarHttpClient(
        payload={
            "items": [
                {
                    "id": "evt-162p-http",
                    "summary": "Customer proposal prep",
                    "start": {"dateTime": "2026-06-25T10:00:00-06:00"},
                    "end": {"dateTime": "2026-06-25T10:30:00-06:00"},
                    "description": "Prep proposal and demo.",
                    "attendees": [{"email": "a@example.com"}],
                }
            ]
        }
    )

    record = run_calendar_backed_today_prep(calendar_http_client=client)

    assert record.calendar_connected is True
    assert record.calendar_event_count == 1
    assert record.prep_available is True
    assert len(client.calls) == 1
    assert client.calls[0]["headers"]["Authorization"] == "Bearer token-162p"
    assert record.calendar_write_allowed is False
    assert record.external_write_allowed is False


def test_162p_cli_json_output_is_structured(monkeypatch, capsys):
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)

    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["stage"] == "162P"
    assert payload["calendar_connected"] is False
    assert payload["calendar_write_allowed"] is False


def test_162p_reference_and_roadmap_close_calendar_backed_today_prep_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "162P is read-only Calendar product integration only." in reference
    assert "does not authorize Calendar writes" in reference
    assert "Gmail reads or writes" in reference
    assert '"stage_id":"162P","stage_name":"Calendar-Backed Today / Prep v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "222P and later remain unauthorized" in roadmap
