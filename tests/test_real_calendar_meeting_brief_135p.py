from __future__ import annotations

from pathlib import Path

import pytest

from app.google_calendar_readonly_connector import (
    CalendarReadResult,
    normalize_google_calendar_event,
    run_google_calendar_readonly_connector,
)
from app.real_calendar_meeting_brief import (
    DEFAULT_CREATED_AT,
    REAL_CALENDAR_MEETING_BRIEF_STAGE,
    compose_real_calendar_meeting_brief,
    main,
    run_real_calendar_meeting_brief,
)
from tests.test_google_calendar_readonly_connector_133p import (
    FakeGoogleCalendarHttpClient,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/real_calendar_meeting_brief.py"


def test_135p_composes_real_calendar_meeting_brief_from_readonly_events(monkeypatch):
    calendar_client = FakeGoogleCalendarHttpClient(
        payload={
            "items": [
                {
                    "id": "evt-135p-1",
                    "summary": "ASISINT follow-up",
                    "start": {"dateTime": "2026-06-24T09:00:00-06:00"},
                    "end": {"dateTime": "2026-06-24T09:30:00-06:00"},
                    "location": "Google Meet",
                    "description": "Review pending TrakIT questions.",
                    "attendees": [{"email": "victor@example.com"}],
                },
                {
                    "id": "evt-135p-2",
                    "summary": "Caregiver logistics",
                    "start": {"dateTime": "2026-06-24T15:00:00-06:00"},
                    "end": {"dateTime": "2026-06-24T15:30:00-06:00"},
                    "attendees": [],
                },
            ]
        }
    )
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-135p")
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_TIMEZONE", "America/Mexico_City")

    record = run_real_calendar_meeting_brief(
        owner_id="francisco",
        robot_id="roboticxs-dev",
        http_client=calendar_client,
        created_at=DEFAULT_CREATED_AT,
    )

    assert record.stage == REAL_CALENDAR_MEETING_BRIEF_STAGE
    assert record.status == "completed"
    assert record.owner_id == "francisco"
    assert record.robot_id == "roboticxs-dev"
    assert len(record.selected_events) == 2
    assert record.headline == "Prepared a deterministic brief for 2 upcoming Calendar event(s)."
    assert "2026-06-24 09:00 - ASISINT follow-up | Google Meet | 1 attendee(s)" in record.meeting_summaries
    assert "Review the objective for ASISINT follow-up." in record.preparation_checklist
    assert "Review the Calendar description preview for owner-provided context." in record.preparation_checklist
    assert "At least one selected event has no attendee list in Calendar." in record.watchpoints
    assert "At least one selected event has no location or meeting link." in record.watchpoints
    assert record.read_only is True
    assert record.calendar_writes is False
    assert record.external_writes is False
    assert record.memory_mutation is False
    assert record.model_calls is False
    assert record.tool_calls is False
    assert record.worker_dispatch is False
    assert "Real Calendar Meeting Brief" in record.local_render_text
    assert "Calendar writes: disabled" in record.local_render_text
    assert "No external action was taken." in record.local_render_text
    assert len(calendar_client.calls) == 1


def test_135p_limits_selected_meetings_and_reports_remaining_events():
    events = tuple(
        {
            "id": f"evt-{index}",
            "summary": f"Meeting {index}",
            "start": {"dateTime": f"2026-06-24T0{index}:00:00-06:00"},
            "end": {"dateTime": f"2026-06-24T0{index}:30:00-06:00"},
        }
        for index in range(1, 5)
    )
    snapshots = tuple(
        snapshot
        for event in events
        for snapshot in [normalize_google_calendar_event(event)]
        if snapshot is not None
    )
    calendar_result = CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-24T00:00:00-06:00",
        window_end="2026-06-25T00:00:00-06:00",
        events=snapshots,
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )

    record = compose_real_calendar_meeting_brief(
        owner_id="owner",
        robot_id="robot",
        calendar_result=calendar_result,
        max_meetings=2,
    )

    assert len(record.selected_events) == 2
    assert record.headline == "Prepared a deterministic brief for 2 upcoming Calendar event(s)."
    assert "Meeting 3" not in "\n".join(record.meeting_summaries)


def test_135p_missing_calendar_token_fails_closed_without_http_request(monkeypatch):
    calendar_client = FakeGoogleCalendarHttpClient()
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)

    record = run_real_calendar_meeting_brief(
        owner_id="owner",
        robot_id="robot",
        http_client=calendar_client,
    )

    assert record.status == "blocked_calendar_unavailable"
    assert record.error_code == "missing_access_token"
    assert record.selected_events == ()
    assert "Calendar read was unavailable" in record.headline
    assert "Calendar read failed closed: missing_access_token." in record.watchpoints
    assert calendar_client.calls == []
    assert record.external_writes is False
    assert record.memory_mutation is False


def test_135p_no_events_composes_empty_readonly_brief():
    result = CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-24T00:00:00-06:00",
        window_end="2026-06-25T00:00:00-06:00",
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )

    record = compose_real_calendar_meeting_brief(
        owner_id="owner",
        robot_id="robot",
        calendar_result=result,
    )

    assert record.status == "completed_no_events"
    assert record.meeting_summaries == ()
    assert record.preparation_checklist == (
        "No Calendar-backed meeting preparation is needed for this window.",
    )
    assert "No upcoming Calendar events were available in the configured window." in record.watchpoints


def test_135p_rejects_unsafe_record_authority():
    result = CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-24T00:00:00-06:00",
        window_end="2026-06-25T00:00:00-06:00",
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )
    record = compose_real_calendar_meeting_brief(
        owner_id="owner",
        robot_id="robot",
        calendar_result=result,
    )
    values = {field_name: getattr(record, field_name) for field_name in record.__dataclass_fields__}
    values["calendar_writes"] = True

    with pytest.raises(ValueError, match="rejected_unsafe_authority"):
        type(record)(**values)


def test_135p_cli_renders_local_brief_and_rejects_arguments(monkeypatch, capsys):
    calendar_client = FakeGoogleCalendarHttpClient(payload={"items": []})
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-135p")
    monkeypatch.setattr(
        "app.real_calendar_meeting_brief.run_google_calendar_readonly_connector",
        lambda http_client=None: run_google_calendar_readonly_connector(http_client=calendar_client),
    )

    assert main([]) == 0
    output = capsys.readouterr().out
    assert "Real Calendar Meeting Brief" in output
    assert "Status: completed_no_events" in output
    assert "Calendar writes: disabled" in output

    assert main(["unexpected"]) == 2
    error = capsys.readouterr().err
    assert "does not accept arguments in 135P" in error


def test_135p_module_keeps_runtime_boundary_terms_out():
    text = MODULE_PATH.read_text()

    for forbidden in [
        "send_message",
        "TelegramBotApiClient",
        "MemoryCenterWritebackRecord",
        "openai",
        "anthropic",
        "worker.dispatch",
        "events.insert",
        "events.update",
        "events.delete",
    ]:
        assert forbidden not in text
