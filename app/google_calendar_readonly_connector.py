from __future__ import annotations

import json
import os
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from json import JSONDecodeError
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.google_oauth_workspace import resolve_google_workspace_access_token


GOOGLE_CALENDAR_READONLY_CONNECTOR_STAGE = "133P"
GOOGLE_CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_CALENDAR_EVENTS_ENDPOINT_TEMPLATE = (
    "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
)
DEFAULT_CALENDAR_ID = "primary"
DEFAULT_DAYS_AHEAD = 7
DEFAULT_MAX_RESULTS = 10
DEFAULT_TIMEZONE = "America/Mexico_City"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_DEV_MODE = True
DEFAULT_DESCRIPTION_PREVIEW_LENGTH = 200


@dataclass(frozen=True, slots=True)
class GoogleCalendarReadOnlyConfig:
    access_token: str
    calendar_id: str
    days_ahead: int
    max_results: int
    timezone: str
    timeout_seconds: int
    dev_mode: bool


@dataclass(frozen=True, slots=True)
class CalendarEventSnapshot:
    event_id: str
    summary: str
    start: str
    end: str
    all_day: bool
    location: str | None
    description_preview: str | None
    organizer_email: str | None
    attendee_count: int
    html_link: str | None
    source: str


@dataclass(frozen=True, slots=True)
class CalendarReadResult:
    ok: bool
    calendar_id: str
    window_start: str
    window_end: str
    events: tuple[CalendarEventSnapshot, ...]
    read_only: bool
    external_writes: bool
    memory_mutation: bool
    error_code: str | None
    error_message: str | None


class GoogleCalendarHttpClientProtocol(Protocol):
    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        ...


class UrllibGoogleCalendarHttpClient:
    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        request = Request(
            f"{url}?{urlencode(params)}",
            headers=headers,
            method="GET",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)


def _env_bool(name: str, default: bool = False, env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_google_calendar_readonly_config_from_env(
    env: dict[str, str] | None = None,
) -> GoogleCalendarReadOnlyConfig:
    source = os.environ if env is None else env
    return GoogleCalendarReadOnlyConfig(
        access_token=resolve_google_workspace_access_token(env=source),
        calendar_id=source.get("ROBOTICXS_GOOGLE_CALENDAR_ID", DEFAULT_CALENDAR_ID).strip()
        or DEFAULT_CALENDAR_ID,
        days_ahead=int(source.get("ROBOTICXS_GOOGLE_CALENDAR_DAYS_AHEAD", str(DEFAULT_DAYS_AHEAD))),
        max_results=int(source.get("ROBOTICXS_GOOGLE_CALENDAR_MAX_RESULTS", str(DEFAULT_MAX_RESULTS))),
        timezone=source.get("ROBOTICXS_GOOGLE_CALENDAR_TIMEZONE", DEFAULT_TIMEZONE).strip()
        or DEFAULT_TIMEZONE,
        timeout_seconds=int(
            source.get(
                "ROBOTICXS_GOOGLE_CALENDAR_TIMEOUT_SECONDS",
                str(DEFAULT_TIMEOUT_SECONDS),
            )
        ),
        dev_mode=_env_bool(
            "ROBOTICXS_GOOGLE_CALENDAR_DEV_MODE",
            DEFAULT_DEV_MODE,
            env=source,
        ),
    )


def validate_google_calendar_readonly_config(
    config: GoogleCalendarReadOnlyConfig,
) -> GoogleCalendarReadOnlyConfig:
    if not config.access_token:
        raise ValueError("missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN")
    if not config.calendar_id:
        raise ValueError("rejected_missing_calendar_id")
    if config.days_ahead <= 0:
        raise ValueError("rejected_invalid_days_ahead")
    if config.max_results <= 0:
        raise ValueError("rejected_invalid_max_results")
    if config.timeout_seconds <= 0:
        raise ValueError("rejected_invalid_timeout_seconds")
    try:
        ZoneInfo(config.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("rejected_invalid_timezone") from exc
    return config


def build_google_calendar_events_url(calendar_id: str) -> str:
    return GOOGLE_CALENDAR_EVENTS_ENDPOINT_TEMPLATE.format(calendar_id=quote(calendar_id, safe=""))


def build_google_calendar_time_window(
    *,
    now: datetime | None,
    timezone_name: str,
    days_ahead: int,
) -> tuple[str, str]:
    tz = ZoneInfo(timezone_name)
    current = datetime.now(tz) if now is None else now.astimezone(tz)
    window_end = current + timedelta(days=days_ahead)
    return (
        current.isoformat(timespec="seconds"),
        window_end.isoformat(timespec="seconds"),
    )


def _safe_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _truncate_preview(text: str | None, limit: int = DEFAULT_DESCRIPTION_PREVIEW_LENGTH) -> str | None:
    if text is None:
        return None
    return text[:limit]


def normalize_google_calendar_event(event: dict) -> CalendarEventSnapshot | None:
    if event.get("status") == "cancelled":
        return None
    start_payload = event.get("start")
    end_payload = event.get("end")
    if not isinstance(start_payload, dict) or not isinstance(end_payload, dict):
        return None

    start_datetime = _safe_text(start_payload.get("dateTime"))
    end_datetime = _safe_text(end_payload.get("dateTime"))
    start_date = _safe_text(start_payload.get("date"))
    end_date = _safe_text(end_payload.get("date"))

    if start_datetime and end_datetime:
        start = start_datetime
        end = end_datetime
        all_day = False
    elif start_date and end_date:
        start = start_date
        end = end_date
        all_day = True
    else:
        return None

    attendees = event.get("attendees")
    attendee_count = len(attendees) if isinstance(attendees, list) else 0
    organizer = event.get("organizer")
    organizer_email = _safe_text(organizer.get("email")) if isinstance(organizer, dict) else None
    summary = _safe_text(event.get("summary")) or "(No title)"
    description_preview = _truncate_preview(_safe_text(event.get("description")))

    return CalendarEventSnapshot(
        event_id=_safe_text(event.get("id")) or "(missing-event-id)",
        summary=summary,
        start=start,
        end=end,
        all_day=all_day,
        location=_safe_text(event.get("location")),
        description_preview=description_preview,
        organizer_email=organizer_email,
        attendee_count=attendee_count,
        html_link=_safe_text(event.get("htmlLink")),
        source="google_calendar_readonly",
    )


def read_google_calendar_upcoming_events(
    *,
    config: GoogleCalendarReadOnlyConfig,
    http_client: GoogleCalendarHttpClientProtocol | None = None,
    now: datetime | None = None,
) -> CalendarReadResult:
    window_start, window_end = build_google_calendar_time_window(
        now=now,
        timezone_name=config.timezone,
        days_ahead=config.days_ahead,
    )

    if not config.access_token:
        return CalendarReadResult(
            ok=False,
            calendar_id=config.calendar_id,
            window_start=window_start,
            window_end=window_end,
            events=(),
            read_only=True,
            external_writes=False,
            memory_mutation=False,
            error_code="missing_access_token",
            error_message=(
                "missing ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN or "
                "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE"
            ),
        )

    try:
        validate_google_calendar_readonly_config(config)
    except ValueError as exc:
        return CalendarReadResult(
            ok=False,
            calendar_id=config.calendar_id,
            window_start=window_start,
            window_end=window_end,
            events=(),
            read_only=True,
            external_writes=False,
            memory_mutation=False,
            error_code="invalid_configuration",
            error_message=str(exc),
        )

    client = http_client or UrllibGoogleCalendarHttpClient()
    url = build_google_calendar_events_url(config.calendar_id)
    params = {
        "singleEvents": "true",
        "orderBy": "startTime",
        "timeMin": window_start,
        "timeMax": window_end,
        "maxResults": str(config.max_results),
    }
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Accept": "application/json",
    }

    try:
        payload = client.get_json(
            url,
            headers=headers,
            params=params,
            timeout_seconds=config.timeout_seconds,
        )
    except HTTPError as exc:
        if exc.code == 401:
            return _failed_result(
                config=config,
                window_start=window_start,
                window_end=window_end,
                error_code="unauthorized",
                error_message="Google Calendar API returned 401 unauthorized.",
            )
        if exc.code == 403:
            return _failed_result(
                config=config,
                window_start=window_start,
                window_end=window_end,
                error_code="forbidden",
                error_message=(
                    "Google Calendar API returned 403 forbidden. "
                    f"Token must include {GOOGLE_CALENDAR_READONLY_SCOPE}."
                ),
            )
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="upstream_error",
            error_message=f"Google Calendar API returned HTTP {exc.code}.",
        )
    except TimeoutError:
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="network_timeout",
            error_message="Google Calendar API request timed out.",
        )
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError | socket.timeout):
            return _failed_result(
                config=config,
                window_start=window_start,
                window_end=window_end,
                error_code="network_timeout",
                error_message="Google Calendar API request timed out.",
            )
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="network_error",
            error_message="Google Calendar API request failed before a response was received.",
        )
    except JSONDecodeError:
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="malformed_response",
            error_message="Google Calendar API returned malformed JSON.",
        )

    if not isinstance(payload, dict):
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="malformed_response",
            error_message="Google Calendar API returned a non-object payload.",
        )

    items = payload.get("items")
    if not isinstance(items, list):
        return _failed_result(
            config=config,
            window_start=window_start,
            window_end=window_end,
            error_code="malformed_response",
            error_message="Google Calendar API payload did not include a valid items list.",
        )

    events: list[CalendarEventSnapshot] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        snapshot = normalize_google_calendar_event(item)
        if snapshot is not None:
            events.append(snapshot)

    return CalendarReadResult(
        ok=True,
        calendar_id=config.calendar_id,
        window_start=window_start,
        window_end=window_end,
        events=tuple(events),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def _failed_result(
    *,
    config: GoogleCalendarReadOnlyConfig,
    window_start: str,
    window_end: str,
    error_code: str,
    error_message: str,
) -> CalendarReadResult:
    return CalendarReadResult(
        ok=False,
        calendar_id=config.calendar_id,
        window_start=window_start,
        window_end=window_end,
        events=(),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=error_code,
        error_message=error_message,
    )


def _format_event_start(snapshot: CalendarEventSnapshot) -> str:
    if snapshot.all_day:
        return f"{snapshot.start} (all day)"
    try:
        parsed = datetime.fromisoformat(snapshot.start)
    except ValueError:
        return snapshot.start
    return parsed.strftime("%Y-%m-%d %H:%M")


def render_google_calendar_readonly_cli_output(result: CalendarReadResult) -> str:
    if result.ok:
        lines = [
            "Google Calendar Read-Only Connector: ok",
            f"Calendar: {result.calendar_id}",
            f"Window: {result.window_start} -> {result.window_end}",
            f"Events returned: {len(result.events)}",
            f"Read-only: {str(result.read_only).lower()}",
            "External writes: disabled",
            "Memory mutation: disabled",
            "LLM/model calls: disabled",
            "Tools: disabled",
            "",
        ]
        if not result.events:
            lines.append("No upcoming events found in the configured window.")
            return "\n".join(lines)

        lines.append("Upcoming events:")
        for index, event in enumerate(result.events, start=1):
            lines.extend(
                [
                    f"{index}. {_format_event_start(event)} - {event.summary}",
                    f"   Location: {event.location or 'Not provided'}",
                    f"   Attendees: {event.attendee_count}",
                    "",
                ]
            )
        return "\n".join(lines[:-1])

    if result.error_code in {"missing_access_token", "invalid_configuration"}:
        return "\n".join(
            [
                "Google Calendar Read-Only Connector: blocked",
                f"Reason: {result.error_message}",
                "No external request was made.",
            ]
        )

    return "\n".join(
        [
            "Google Calendar Read-Only Connector: failed",
            f"Reason: {result.error_message}",
            "No external write was attempted.",
        ]
    )


def run_google_calendar_readonly_connector(
    *,
    env: dict[str, str] | None = None,
    http_client: GoogleCalendarHttpClientProtocol | None = None,
    now: datetime | None = None,
) -> CalendarReadResult:
    config = load_google_calendar_readonly_config_from_env(env=env)
    return read_google_calendar_upcoming_events(
        config=config,
        http_client=http_client,
        now=now,
    )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = []
    if argv:
        print("Google Calendar Read-Only Connector: failed", file=sys.stderr)
        print("Reason: this command does not accept arguments in 133P.", file=sys.stderr)
        return 2

    result = run_google_calendar_readonly_connector()
    print(render_google_calendar_readonly_cli_output(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
