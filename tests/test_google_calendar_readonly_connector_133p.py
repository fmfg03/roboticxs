from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from app.google_calendar_readonly_connector import (
    DEFAULT_CALENDAR_ID,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_DEV_MODE,
    DEFAULT_MAX_RESULTS,
    DEFAULT_TIMEZONE,
    DEFAULT_TIMEOUT_SECONDS,
    CalendarEventSnapshot,
    CalendarReadResult,
    GoogleCalendarReadOnlyConfig,
    build_google_calendar_events_url,
    load_google_calendar_readonly_config_from_env,
    main,
    normalize_google_calendar_event,
    read_google_calendar_upcoming_events,
    render_google_calendar_readonly_cli_output,
    run_google_calendar_readonly_connector,
    validate_google_calendar_readonly_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/google_calendar_readonly_connector.py"


class FakeGoogleCalendarHttpClient:
    def __init__(self, payload: dict | None = None, *, error: Exception | None = None) -> None:
        self.payload = payload if payload is not None else {"items": []}
        self.error = error
        self.calls: list[dict[str, object]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.error is not None:
            raise self.error
        return self.payload


def build_valid_config(**overrides: object) -> GoogleCalendarReadOnlyConfig:
    values = {
        "access_token": "token-133p",
        "calendar_id": "primary",
        "days_ahead": 7,
        "max_results": 10,
        "timezone": "America/Mexico_City",
        "timeout_seconds": 30,
        "dev_mode": True,
    }
    values.update(overrides)
    return GoogleCalendarReadOnlyConfig(**values)


def test_133p_config_loads_defaults_from_environment():
    config = load_google_calendar_readonly_config_from_env(
        env={"ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "token-133p"}
    )

    assert config.access_token == "token-133p"
    assert config.calendar_id == DEFAULT_CALENDAR_ID
    assert config.days_ahead == DEFAULT_DAYS_AHEAD
    assert config.max_results == DEFAULT_MAX_RESULTS
    assert config.timezone == DEFAULT_TIMEZONE
    assert config.timeout_seconds == DEFAULT_TIMEOUT_SECONDS
    assert config.dev_mode is DEFAULT_DEV_MODE


def test_133p_config_loads_explicit_overrides_from_environment():
    config = load_google_calendar_readonly_config_from_env(
        env={
            "ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "override-token",
            "ROBOTICXS_GOOGLE_CALENDAR_ID": "team@example.com",
            "ROBOTICXS_GOOGLE_CALENDAR_DAYS_AHEAD": "14",
            "ROBOTICXS_GOOGLE_CALENDAR_MAX_RESULTS": "25",
            "ROBOTICXS_GOOGLE_CALENDAR_TIMEZONE": "UTC",
            "ROBOTICXS_GOOGLE_CALENDAR_TIMEOUT_SECONDS": "45",
            "ROBOTICXS_GOOGLE_CALENDAR_DEV_MODE": "false",
        }
    )

    assert config.access_token == "override-token"
    assert config.calendar_id == "team@example.com"
    assert config.days_ahead == 14
    assert config.max_results == 25
    assert config.timezone == "UTC"
    assert config.timeout_seconds == 45
    assert config.dev_mode is False


@pytest.mark.parametrize(
    ("overrides", "error_code"),
    [
        ({"access_token": ""}, "missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN"),
        ({"days_ahead": 0}, "rejected_invalid_days_ahead"),
        ({"days_ahead": -1}, "rejected_invalid_days_ahead"),
        ({"max_results": 0}, "rejected_invalid_max_results"),
        ({"max_results": -5}, "rejected_invalid_max_results"),
    ],
)
def test_133p_invalid_configuration_fails_closed(overrides: dict[str, object], error_code: str):
    config = build_valid_config(**overrides)

    with pytest.raises(ValueError, match=error_code):
        validate_google_calendar_readonly_config(config)


def test_133p_missing_access_token_fails_closed_without_making_http_request():
    client = FakeGoogleCalendarHttpClient()

    result = read_google_calendar_upcoming_events(
        config=build_valid_config(access_token=""),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "missing_access_token"
    assert result.read_only is True
    assert result.external_writes is False
    assert result.memory_mutation is False
    assert client.calls == []


def test_133p_calendar_id_defaults_to_primary():
    config = load_google_calendar_readonly_config_from_env(
        env={"ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "token-133p"}
    )

    assert config.calendar_id == "primary"


def test_133p_connector_uses_get_endpoint_headers_and_required_query_params():
    client = FakeGoogleCalendarHttpClient(payload={"items": []})
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is True
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["url"] == "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    assert call["headers"] == {
        "Authorization": "Bearer token-133p",
        "Accept": "application/json",
    }
    assert call["params"]["singleEvents"] == "true"
    assert call["params"]["orderBy"] == "startTime"
    assert call["params"]["maxResults"] == "10"
    assert call["params"]["timeMin"] == "2026-06-21T04:00:00-06:00"
    assert call["params"]["timeMax"] == "2026-06-28T04:00:00-06:00"
    assert call["timeout_seconds"] == 30


def test_133p_connector_respects_max_results_and_custom_calendar_id():
    client = FakeGoogleCalendarHttpClient(payload={"items": []})
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(calendar_id="team@example.com", max_results=3),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is True
    assert client.calls[0]["url"] == "https://www.googleapis.com/calendar/v3/calendars/team%40example.com/events"
    assert client.calls[0]["params"]["maxResults"] == "3"


def test_133p_timed_event_is_normalized_correctly():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(
            payload={
                "items": [
                    {
                        "id": "evt-1",
                        "summary": "Meeting with Victor",
                        "start": {"dateTime": "2026-06-21T10:00:00-06:00"},
                        "end": {"dateTime": "2026-06-21T10:30:00-06:00"},
                        "location": "Google Meet",
                        "description": "Prep notes",
                        "organizer": {"email": "owner@example.com"},
                        "attendees": [{"email": "a@example.com"}, {"email": "b@example.com"}],
                        "htmlLink": "https://calendar.google.com/event?eid=1",
                    }
                ]
            }
        ),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is True
    assert result.events == (
        CalendarEventSnapshot(
            event_id="evt-1",
            summary="Meeting with Victor",
            start="2026-06-21T10:00:00-06:00",
            end="2026-06-21T10:30:00-06:00",
            all_day=False,
            location="Google Meet",
            description_preview="Prep notes",
            organizer_email="owner@example.com",
            attendee_count=2,
            html_link="https://calendar.google.com/event?eid=1",
            source="google_calendar_readonly",
        ),
    )


def test_133p_all_day_event_is_normalized_correctly():
    snapshot = normalize_google_calendar_event(
        {
            "id": "evt-2",
            "summary": "Offsite",
            "start": {"date": "2026-06-22"},
            "end": {"date": "2026-06-23"},
            "attendees": [],
        }
    )

    assert snapshot is not None
    assert snapshot.all_day is True
    assert snapshot.start == "2026-06-22"
    assert snapshot.end == "2026-06-23"
    assert snapshot.attendee_count == 0


def test_133p_missing_summary_location_and_attendees_are_safe():
    snapshot = normalize_google_calendar_event(
        {
            "id": "evt-3",
            "start": {"dateTime": "2026-06-21T12:00:00-06:00"},
            "end": {"dateTime": "2026-06-21T13:00:00-06:00"},
        }
    )

    assert snapshot is not None
    assert snapshot.summary == "(No title)"
    assert snapshot.location is None
    assert snapshot.attendee_count == 0


def test_133p_description_preview_is_truncated_deterministically():
    snapshot = normalize_google_calendar_event(
        {
            "id": "evt-4",
            "start": {"dateTime": "2026-06-21T12:00:00-06:00"},
            "end": {"dateTime": "2026-06-21T13:00:00-06:00"},
            "description": "x" * 250,
        }
    )

    assert snapshot is not None
    assert snapshot.description_preview == "x" * 200


def test_133p_cancelled_events_are_skipped():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(
            payload={
                "items": [
                    {
                        "id": "evt-cancelled",
                        "status": "cancelled",
                        "start": {"dateTime": "2026-06-21T12:00:00-06:00"},
                        "end": {"dateTime": "2026-06-21T13:00:00-06:00"},
                    }
                ]
            }
        ),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is True
    assert result.events == ()


def test_133p_empty_event_list_returns_deterministic_ok_result():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(payload={"items": []}),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result == CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-21T04:00:00-06:00",
        window_end="2026-06-28T04:00:00-06:00",
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def test_133p_http_401_returns_deterministic_unauthorized_failure():
    client = FakeGoogleCalendarHttpClient(
        error=HTTPError(
            url="https://www.googleapis.com/calendar/v3/calendars/primary/events",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
    )

    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "unauthorized"
    assert result.error_message == "Google Calendar API returned 401 unauthorized."


def test_133p_http_403_returns_deterministic_permission_failure():
    client = FakeGoogleCalendarHttpClient(
        error=HTTPError(
            url="https://www.googleapis.com/calendar/v3/calendars/primary/events",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )
    )

    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "forbidden"
    assert "calendar.readonly" in result.error_message


def test_133p_http_500_returns_deterministic_upstream_failure():
    client = FakeGoogleCalendarHttpClient(
        error=HTTPError(
            url="https://www.googleapis.com/calendar/v3/calendars/primary/events",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )
    )

    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "upstream_error"
    assert result.error_message == "Google Calendar API returned HTTP 500."


def test_133p_network_timeout_returns_deterministic_failure():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(error=TimeoutError("timeout")),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "network_timeout"
    assert result.error_message == "Google Calendar API request timed out."


def test_133p_urlerror_timeout_returns_deterministic_failure():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(error=URLError(TimeoutError("timeout"))),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "network_timeout"


def test_133p_malformed_response_does_not_crash():
    result = read_google_calendar_upcoming_events(
        config=build_valid_config(),
        http_client=FakeGoogleCalendarHttpClient(payload={"unexpected": []}),
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is False
    assert result.error_code == "malformed_response"


def test_133p_cli_renders_success_output_deterministically():
    result = CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-21T04:00:00-06:00",
        window_end="2026-06-28T04:00:00-06:00",
        events=(
            CalendarEventSnapshot(
                event_id="evt-1",
                summary="Meeting with Victor",
                start="2026-06-21T10:00:00-06:00",
                end="2026-06-21T10:30:00-06:00",
                all_day=False,
                location="Google Meet",
                description_preview=None,
                organizer_email=None,
                attendee_count=2,
                html_link=None,
                source="google_calendar_readonly",
            ),
        ),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )

    assert render_google_calendar_readonly_cli_output(result) == "\n".join(
        [
            "Google Calendar Read-Only Connector: ok",
            "Calendar: primary",
            "Window: 2026-06-21T04:00:00-06:00 -> 2026-06-28T04:00:00-06:00",
            "Events returned: 1",
            "Read-only: true",
            "External writes: disabled",
            "Memory mutation: disabled",
            "LLM/model calls: disabled",
            "Tools: disabled",
            "",
            "Upcoming events:",
            "1. 2026-06-21 10:00 - Meeting with Victor",
            "   Location: Google Meet",
            "   Attendees: 2",
        ]
    )


def test_133p_cli_renders_missing_token_blocked_output_deterministically():
    result = CalendarReadResult(
        ok=False,
        calendar_id="primary",
        window_start="2026-06-21T04:00:00-06:00",
        window_end="2026-06-28T04:00:00-06:00",
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code="missing_access_token",
        error_message="missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN",
    )

    assert render_google_calendar_readonly_cli_output(result) == "\n".join(
        [
            "Google Calendar Read-Only Connector: blocked",
            "Reason: missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN",
            "No external request was made.",
        ]
    )


def test_133p_run_connector_loads_env_and_uses_injected_client():
    client = FakeGoogleCalendarHttpClient(payload={"items": []})

    result = run_google_calendar_readonly_connector(
        env={"ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "token-133p"},
        http_client=client,
        now=datetime.fromisoformat("2026-06-21T10:00:00+00:00"),
    )

    assert result.ok is True
    assert len(client.calls) == 1


def test_133p_main_prints_blocked_output_and_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)

    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Google Calendar Read-Only Connector: blocked" in captured.out
    assert "missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN" in captured.out
    assert captured.err == ""


def test_133p_helper_builds_google_calendar_events_endpoint():
    assert (
        build_google_calendar_events_url("team@example.com")
        == "https://www.googleapis.com/calendar/v3/calendars/team%40example.com/events"
    )


def test_133p_module_keeps_connector_read_only_and_does_not_add_other_integrations():
    text = MODULE_PATH.read_text()

    for forbidden in [
        'method="POST"',
        'method="PATCH"',
        'method="PUT"',
        'method="DELETE"',
        "sendMessage",
        "gmail",
        "drive",
        "slack",
        "crm",
        "openai",
        "anthropic",
        "ollama",
        "worker",
        "MemoryCenterWritebackRecord",
        "create_event",
        "update_event",
        "delete_event",
    ]:
        assert forbidden not in text
