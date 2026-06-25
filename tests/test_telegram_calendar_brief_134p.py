from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError

from app.runnable_telegram_robot_mvp import (
    TelegramRobotConfig,
    handle_incoming_command,
    parse_telegram_incoming_command,
    render_brief_command_reply,
    render_status_command_reply,
    render_unauthorized_reply,
    validate_telegram_robot_config,
)
from tests.test_google_calendar_readonly_connector_133p import (
    FakeGoogleCalendarHttpClient,
)
from tests.test_runnable_telegram_robot_mvp_130p import (
    FakeTelegramClient,
    build_command_update,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/runnable_telegram_robot_mvp.py"


def build_valid_config() -> TelegramRobotConfig:
    return validate_telegram_robot_config(
        TelegramRobotConfig(
            bot_token="token-134p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        )
    )


def test_134p_status_exposes_calendar_readonly_surface_without_write_authority():
    reply = render_status_command_reply(build_valid_config())

    assert "Calendar reads require read-only Google setup." in reply
    assert "Calendar writes: disabled" in reply
    assert "Model calls: disabled" in reply
    assert "Automatic Memory Center mutation: disabled" in reply
    assert "Roadmap: 95P-168P closed, Usage Cost Meter active" in reply


def test_134p_authorized_brief_uses_readonly_calendar_snapshot(monkeypatch):
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeGoogleCalendarHttpClient(
        payload={
            "items": [
                {
                    "id": "evt-134p",
                    "summary": "Victor / ASISINT follow-up",
                    "start": {"dateTime": "2026-06-24T09:00:00-06:00"},
                    "end": {"dateTime": "2026-06-24T09:30:00-06:00"},
                    "attendees": [{"email": "victor@example.com"}],
                }
            ]
        }
    )
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-134p")
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_TIMEZONE", "America/Mexico_City")
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is True
    assert "Meeting Brief" in receipt.reply_text
    assert "Calendar:" in receipt.reply_text
    assert "- 2026-06-24T09:00:00-06:00 - Victor / ASISINT follow-up" in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "Memory mutation: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text
    assert len(calendar_client.calls) == 1
    assert calendar_client.calls[0]["headers"] == {
        "Authorization": "Bearer token-134p",
        "Accept": "application/json",
    }
    assert client.sent_messages == [
        {
            "chat_id": 4004,
            "text": receipt.reply_text,
            "reply_to_message_id": 123,
        }
    ]


def test_134p_missing_calendar_token_fails_closed_without_http_request(monkeypatch):
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeGoogleCalendarHttpClient()
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is True
    assert "Read-only Calendar connector unavailable: missing_access_token." in receipt.reply_text
    assert "Falling back to local deterministic meeting context." in receipt.reply_text
    assert "Victor / ASISINT follow-up" in receipt.reply_text
    assert calendar_client.calls == []


def test_134p_calendar_failure_falls_back_without_write_or_memory_mutation(monkeypatch):
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeGoogleCalendarHttpClient(
        error=HTTPError(
            url="https://www.googleapis.com/calendar/v3/calendars/primary/events",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )
    )
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-134p")
    incoming = parse_telegram_incoming_command(build_command_update(text="/brief"))

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert "Read-only Calendar connector unavailable: forbidden." in receipt.reply_text
    assert "Falling back to local deterministic meeting context." in receipt.reply_text
    assert "Calendar writes: disabled" in receipt.reply_text
    assert "Memory mutation: disabled" in receipt.reply_text
    assert "No external action was taken." in receipt.reply_text


def test_134p_unauthorized_brief_does_not_read_calendar(monkeypatch):
    config = build_valid_config()
    client = FakeTelegramClient()
    calendar_client = FakeGoogleCalendarHttpClient()
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-134p")
    incoming = parse_telegram_incoming_command(
        build_command_update(telegram_user_id=999999999, text="/brief")
    )

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=config,
        calendar_http_client=calendar_client,
    )

    assert receipt.authorized is False
    assert receipt.reply_text == render_unauthorized_reply()
    assert calendar_client.calls == []


def test_134p_direct_brief_render_without_calendar_result_is_local_fallback():
    reply = render_brief_command_reply(build_valid_config())

    assert "Google Calendar read-only connector was not configured for this reply." in reply
    assert "Calendar writes: disabled" in reply
    assert "No external action was taken." in reply


def test_134p_runtime_module_keeps_forbidden_surfaces_outside_calendar_readonly():
    text = MODULE_PATH.read_text()

    for forbidden in [
        "gmail",
        "drive",
        "slack",
        "crm",
        "openai",
        "anthropic",
        "ollama",
        "worker",
    ]:
        assert forbidden not in text
