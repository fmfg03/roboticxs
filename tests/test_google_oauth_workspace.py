from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.google_oauth_workspace import (
    GOOGLE_CALENDAR_READONLY_SCOPE,
    GOOGLE_GMAIL_METADATA_SCOPE,
    GOOGLE_GMAIL_READONLY_SCOPE,
    GoogleOAuthClientConfig,
    build_google_oauth_authorization_url,
    build_loopback_redirect_uri,
    build_pkce_code_challenge,
    exchange_google_oauth_code,
    load_google_oauth_client_config,
    resolve_google_workspace_access_token,
    save_google_oauth_token_record,
    workspace_scopes_for_gmail_mode,
)


class FakeOAuthHttpClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def post_form(self, url: str, *, form: dict[str, str], timeout_seconds: int) -> dict:
        self.calls.append({"url": url, "form": form, "timeout_seconds": timeout_seconds})
        return self.payload


def test_google_oauth_loads_installed_desktop_client(tmp_path: Path):
    client_file = tmp_path / "client.json"
    client_file.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "client-123.apps.googleusercontent.com",
                    "client_secret": "secret-123",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://127.0.0.1:8765/oauth2callback"],
                }
            }
        ),
        encoding="utf-8",
    )

    client = load_google_oauth_client_config(client_file)

    assert client.client_id == "client-123.apps.googleusercontent.com"
    assert client.client_secret == "secret-123"
    assert client.redirect_uris == ("http://127.0.0.1:8765/oauth2callback",)


def test_google_oauth_authorization_url_uses_pkce_offline_and_readonly_scopes():
    client = GoogleOAuthClientConfig(
        client_id="client-123",
        client_secret="secret-123",
        auth_uri="https://accounts.google.com/o/oauth2/v2/auth",
        token_uri="https://oauth2.googleapis.com/token",
        redirect_uris=(),
    )

    url = build_google_oauth_authorization_url(
        client=client,
        redirect_uri=build_loopback_redirect_uri(port=8765),
        scopes=workspace_scopes_for_gmail_mode("metadata"),
        state="state-123",
        code_challenge=build_pkce_code_challenge("verifier-123"),
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert query["client_id"] == ["client-123"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8765/oauth2callback"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["code_challenge_method"] == ["S256"]
    assert GOOGLE_CALENDAR_READONLY_SCOPE in query["scope"][0].split()
    assert GOOGLE_GMAIL_METADATA_SCOPE in query["scope"][0].split()


def test_google_oauth_gmail_mode_can_request_readonly_or_calendar_only():
    assert workspace_scopes_for_gmail_mode("readonly") == (
        GOOGLE_CALENDAR_READONLY_SCOPE,
        GOOGLE_GMAIL_READONLY_SCOPE,
    )
    assert workspace_scopes_for_gmail_mode("none") == (GOOGLE_CALENDAR_READONLY_SCOPE,)


def test_google_oauth_exchange_saves_refresh_token_and_expiry():
    client = GoogleOAuthClientConfig(
        client_id="client-123",
        client_secret="secret-123",
        auth_uri="https://accounts.google.com/o/oauth2/v2/auth",
        token_uri="https://oauth2.googleapis.com/token",
        redirect_uris=(),
    )
    fake_http = FakeOAuthHttpClient(
        {
            "access_token": "access-123",
            "refresh_token": "refresh-123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    )

    record = exchange_google_oauth_code(
        client=client,
        code="code-123",
        redirect_uri="http://127.0.0.1:8765/oauth2callback",
        code_verifier="verifier-123",
        scopes=workspace_scopes_for_gmail_mode("metadata"),
        http_client=fake_http,
        now_epoch=1000,
    )

    assert record.access_token == "access-123"
    assert record.refresh_token == "refresh-123"
    assert record.expires_at == 4600
    assert fake_http.calls[0]["form"]["grant_type"] == "authorization_code"
    assert fake_http.calls[0]["form"]["code_verifier"] == "verifier-123"


def test_google_oauth_resolver_prefers_existing_calendar_access_token(tmp_path: Path):
    token_file = tmp_path / "token.json"

    token = resolve_google_workspace_access_token(
        env={
            "ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "calendar-token",
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )

    assert token == "calendar-token"


def test_google_oauth_resolver_reads_unexpired_token_file(tmp_path: Path):
    token_file = tmp_path / "token.json"
    client = GoogleOAuthClientConfig(
        client_id="client-123",
        client_secret="secret-123",
        auth_uri="https://accounts.google.com/o/oauth2/v2/auth",
        token_uri="https://oauth2.googleapis.com/token",
        redirect_uris=(),
    )
    record = exchange_google_oauth_code(
        client=client,
        code="code-123",
        redirect_uri="http://127.0.0.1:8765/oauth2callback",
        code_verifier="verifier-123",
        scopes=workspace_scopes_for_gmail_mode("metadata"),
        http_client=FakeOAuthHttpClient(
            {
                "access_token": "fresh-token",
                "refresh_token": "refresh-123",
                "expires_in": 3600,
            }
        ),
        now_epoch=1000,
    )
    save_google_oauth_token_record(record, token_file)

    token = resolve_google_workspace_access_token(
        env={"ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file)},
        now_epoch=1200,
    )

    assert token == "fresh-token"


def test_google_oauth_resolver_fails_closed_for_malformed_token_file(tmp_path: Path):
    token_file = tmp_path / "token.json"
    token_file.write_text("{not-json", encoding="utf-8")

    token = resolve_google_workspace_access_token(
        env={"ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file)},
        now_epoch=1200,
    )

    assert token == ""
