from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GOOGLE_OAUTH_WORKSPACE_STAGE = "google_oauth_workspace_v0"
GOOGLE_OAUTH_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_GMAIL_METADATA_SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
GOOGLE_GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE = ".secrets/google_oauth_client.json"
DEFAULT_GOOGLE_OAUTH_TOKEN_FILE = ".secrets/google_workspace_token.json"
DEFAULT_GOOGLE_OAUTH_REDIRECT_PORT = 8765
DEFAULT_GOOGLE_OAUTH_REDIRECT_PATH = "/oauth2callback"
DEFAULT_GOOGLE_OAUTH_TIMEOUT_SECONDS = 30
DEFAULT_TOKEN_EXPIRY_SKEW_SECONDS = 60
DEFAULT_WORKSPACE_SCOPES = (
    GOOGLE_CALENDAR_READONLY_SCOPE,
    GOOGLE_GMAIL_METADATA_SCOPE,
)


class GoogleOAuthHttpClientProtocol(Protocol):
    def post_form(
        self,
        url: str,
        *,
        form: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        ...


class UrllibGoogleOAuthHttpClient:
    def post_form(
        self,
        url: str,
        *,
        form: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        payload = urlencode(form).encode("utf-8")
        request = Request(
            url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True, slots=True)
class GoogleOAuthClientConfig:
    client_id: str
    client_secret: str
    auth_uri: str
    token_uri: str
    redirect_uris: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GoogleOAuthTokenRecord:
    stage: str
    client_id: str
    scopes: tuple[str, ...]
    token_type: str
    access_token: str
    refresh_token: str | None
    expires_at: int | None

    def __post_init__(self) -> None:
        if self.stage != GOOGLE_OAUTH_WORKSPACE_STAGE:
            raise ValueError("rejected_invalid_google_oauth_stage")
        if not self.client_id:
            raise ValueError("rejected_missing_google_oauth_client_id")
        if not self.access_token:
            raise ValueError("rejected_missing_google_oauth_access_token")


def load_google_oauth_client_config(path: str | os.PathLike[str]) -> GoogleOAuthClientConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    installed = payload.get("installed")
    if not isinstance(installed, dict):
        raise ValueError("rejected_google_oauth_client_must_be_installed_app")

    client_id = _required_text(installed, "client_id")
    token_uri = _text(installed.get("token_uri")) or GOOGLE_OAUTH_TOKEN_ENDPOINT
    auth_uri = _text(installed.get("auth_uri")) or GOOGLE_OAUTH_AUTHORIZATION_ENDPOINT
    client_secret = _text(installed.get("client_secret")) or ""
    redirect_uris_payload = installed.get("redirect_uris")
    redirect_uris = tuple(
        uri.strip()
        for uri in redirect_uris_payload
        if isinstance(uri, str) and uri.strip()
    ) if isinstance(redirect_uris_payload, list) else ()

    return GoogleOAuthClientConfig(
        client_id=client_id,
        client_secret=client_secret,
        auth_uri=auth_uri,
        token_uri=token_uri,
        redirect_uris=redirect_uris,
    )


def build_loopback_redirect_uri(
    *,
    port: int = DEFAULT_GOOGLE_OAUTH_REDIRECT_PORT,
    path: str = DEFAULT_GOOGLE_OAUTH_REDIRECT_PATH,
) -> str:
    if port <= 0:
        raise ValueError("rejected_invalid_google_oauth_redirect_port")
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"http://127.0.0.1:{port}{normalized_path}"


def generate_pkce_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def build_pkce_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def build_google_oauth_authorization_url(
    *,
    client: GoogleOAuthClientConfig,
    redirect_uri: str,
    scopes: tuple[str, ...] = DEFAULT_WORKSPACE_SCOPES,
    state: str,
    code_challenge: str,
) -> str:
    if not scopes:
        raise ValueError("rejected_missing_google_oauth_scopes")
    params = {
        "client_id": client.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{client.auth_uri}?{urlencode(params)}"


def exchange_google_oauth_code(
    *,
    client: GoogleOAuthClientConfig,
    code: str,
    redirect_uri: str,
    code_verifier: str,
    scopes: tuple[str, ...],
    http_client: GoogleOAuthHttpClientProtocol | None = None,
    timeout_seconds: int = DEFAULT_GOOGLE_OAUTH_TIMEOUT_SECONDS,
    now_epoch: int | None = None,
) -> GoogleOAuthTokenRecord:
    form = {
        "client_id": client.client_id,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if client.client_secret:
        form["client_secret"] = client.client_secret
    return _token_record_from_payload(
        payload=_post_token_form(
            client=client,
            form=form,
            http_client=http_client,
            timeout_seconds=timeout_seconds,
        ),
        client_id=client.client_id,
        requested_scopes=scopes,
        prior_refresh_token=None,
        now_epoch=now_epoch,
    )


def refresh_google_oauth_access_token(
    *,
    client: GoogleOAuthClientConfig,
    refresh_token: str,
    requested_scopes: tuple[str, ...],
    http_client: GoogleOAuthHttpClientProtocol | None = None,
    timeout_seconds: int = DEFAULT_GOOGLE_OAUTH_TIMEOUT_SECONDS,
    now_epoch: int | None = None,
) -> GoogleOAuthTokenRecord:
    if not refresh_token:
        raise ValueError("rejected_missing_google_oauth_refresh_token")
    form = {
        "client_id": client.client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    if client.client_secret:
        form["client_secret"] = client.client_secret
    return _token_record_from_payload(
        payload=_post_token_form(
            client=client,
            form=form,
            http_client=http_client,
            timeout_seconds=timeout_seconds,
        ),
        client_id=client.client_id,
        requested_scopes=requested_scopes,
        prior_refresh_token=refresh_token,
        now_epoch=now_epoch,
    )


def save_google_oauth_token_record(
    record: GoogleOAuthTokenRecord,
    path: str | os.PathLike[str],
) -> None:
    token_path = Path(path)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": record.stage,
        "client_id": record.client_id,
        "scopes": list(record.scopes),
        "token_type": record.token_type,
        "access_token": record.access_token,
        "refresh_token": record.refresh_token,
        "expires_at": record.expires_at,
    }
    token_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    try:
        token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def load_google_oauth_token_record(path: str | os.PathLike[str]) -> GoogleOAuthTokenRecord | None:
    token_path = Path(path)
    if not token_path.exists():
        return None
    payload = json.loads(token_path.read_text(encoding="utf-8"))
    scopes_payload = payload.get("scopes")
    scopes = tuple(
        scope.strip()
        for scope in scopes_payload
        if isinstance(scope, str) and scope.strip()
    ) if isinstance(scopes_payload, list) else ()
    return GoogleOAuthTokenRecord(
        stage=_required_text(payload, "stage"),
        client_id=_required_text(payload, "client_id"),
        scopes=scopes,
        token_type=_text(payload.get("token_type")) or "Bearer",
        access_token=_required_text(payload, "access_token"),
        refresh_token=_text(payload.get("refresh_token")),
        expires_at=_int_or_none(payload.get("expires_at")),
    )


def resolve_google_workspace_access_token(
    *,
    env: dict[str, str] | None = None,
    http_client: GoogleOAuthHttpClientProtocol | None = None,
    now_epoch: int | None = None,
) -> str:
    source = os.environ if env is None else env
    direct_token = (
        source.get("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "").strip()
        or source.get("ROBOTICXS_GOOGLE_OAUTH_ACCESS_TOKEN", "").strip()
    )
    if direct_token:
        return direct_token

    token_path = source.get("ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE", DEFAULT_GOOGLE_OAUTH_TOKEN_FILE).strip()
    if not token_path:
        token_path = DEFAULT_GOOGLE_OAUTH_TOKEN_FILE
    try:
        record = load_google_oauth_token_record(token_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return ""
    if record is None:
        return ""
    now = int(time.time()) if now_epoch is None else now_epoch
    if record.expires_at is None or record.expires_at > now + DEFAULT_TOKEN_EXPIRY_SKEW_SECONDS:
        return record.access_token
    if not record.refresh_token:
        return ""

    client_path = source.get(
        "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE",
        DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
    ).strip()
    if not client_path:
        client_path = DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE
    try:
        refreshed = refresh_google_oauth_access_token(
            client=load_google_oauth_client_config(client_path),
            refresh_token=record.refresh_token,
            requested_scopes=record.scopes,
            http_client=http_client,
            now_epoch=now,
        )
    except (HTTPError, OSError, URLError, ValueError, json.JSONDecodeError):
        return ""
    save_google_oauth_token_record(refreshed, token_path)
    return refreshed.access_token


def workspace_scopes_for_gmail_mode(gmail_mode: str) -> tuple[str, ...]:
    normalized = gmail_mode.strip().lower()
    if normalized == "metadata":
        return DEFAULT_WORKSPACE_SCOPES
    if normalized == "readonly":
        return (GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_READONLY_SCOPE)
    if normalized == "none":
        return (GOOGLE_CALENDAR_READONLY_SCOPE,)
    raise ValueError("rejected_invalid_google_oauth_gmail_mode")


def redacted_google_oauth_token_summary(record: GoogleOAuthTokenRecord) -> str:
    refresh_status = "present" if record.refresh_token else "missing"
    expiry = str(record.expires_at) if record.expires_at is not None else "unknown"
    return "\n".join(
        [
            "Google Workspace OAuth token: ready",
            f"Client: {record.client_id}",
            f"Scopes: {', '.join(record.scopes)}",
            f"Refresh token: {refresh_status}",
            f"Expires at: {expiry}",
            "Access token: redacted",
        ]
    )


def _post_token_form(
    *,
    client: GoogleOAuthClientConfig,
    form: dict[str, str],
    http_client: GoogleOAuthHttpClientProtocol | None,
    timeout_seconds: int,
) -> dict:
    transport = http_client or UrllibGoogleOAuthHttpClient()
    return transport.post_form(
        client.token_uri,
        form=form,
        timeout_seconds=timeout_seconds,
    )


def _token_record_from_payload(
    *,
    payload: dict,
    client_id: str,
    requested_scopes: tuple[str, ...],
    prior_refresh_token: str | None,
    now_epoch: int | None,
) -> GoogleOAuthTokenRecord:
    access_token = _required_text(payload, "access_token")
    token_type = _text(payload.get("token_type")) or "Bearer"
    refresh_token = _text(payload.get("refresh_token")) or prior_refresh_token
    scope_text = _text(payload.get("scope"))
    scopes = tuple(scope_text.split()) if scope_text else requested_scopes
    expires_in = _int_or_none(payload.get("expires_in"))
    now = int(time.time()) if now_epoch is None else now_epoch
    expires_at = now + expires_in if expires_in is not None else None
    return GoogleOAuthTokenRecord(
        stage=GOOGLE_OAUTH_WORKSPACE_STAGE,
        client_id=client_id,
        scopes=scopes,
        token_type=token_type,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


def _required_text(payload: dict, key: str) -> str:
    value = _text(payload.get(key))
    if value is None:
        raise ValueError(f"rejected_missing_google_oauth_{key}")
    return value


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None
