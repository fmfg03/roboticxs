from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from app.google_oauth_workspace import (
    GOOGLE_CALENDAR_READONLY_SCOPE,
    GOOGLE_GMAIL_METADATA_SCOPE,
    GOOGLE_GMAIL_READONLY_SCOPE,
    GOOGLE_OAUTH_WORKSPACE_STAGE,
)
from app.runtime_doctor import (
    RUNTIME_DOCTOR_STAGE,
    build_runtime_doctor_status,
    main,
    render_runtime_doctor_report,
    run_runtime_doctor,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR_PATH = REPO_ROOT / "app/runtime_doctor.py"


def write_client_file(path: Path, *, client_secret: str = "client-secret-149p") -> None:
    path.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "client-149p.apps.googleusercontent.com",
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://127.0.0.1:8765/oauth2callback"],
                }
            }
        ),
        encoding="utf-8",
    )


def write_token_file(
    path: Path,
    *,
    access_token: str = "access-token-149p",
    refresh_token: str | None = "refresh-token-149p",
    scopes: list[str] | None = None,
    expires_at: int = 4_000_000_000,
) -> None:
    path.write_text(
        json.dumps(
            {
                "stage": GOOGLE_OAUTH_WORKSPACE_STAGE,
                "client_id": "client-149p.apps.googleusercontent.com",
                "scopes": scopes if scopes is not None else [GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_METADATA_SCOPE],
                "token_type": "Bearer",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
            }
        ),
        encoding="utf-8",
    )


def test_149p_missing_secret_files_fail_closed_without_crashing(tmp_path: Path):
    client_file = tmp_path / "missing-client.json"
    token_file = tmp_path / "missing-token.json"

    status = build_runtime_doctor_status(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )

    assert status.stage == RUNTIME_DOCTOR_STAGE
    assert status.overall_status == "warning"
    assert status.path_checks[0].shape_status == "missing"
    assert status.path_checks[0].reason == "client_secrets_file_missing"
    assert status.path_checks[1].shape_status == "missing"
    assert status.path_checks[1].reason == "workspace_token_file_missing"


def test_149p_valid_oauth_shapes_report_ready_without_printing_secrets(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    write_client_file(client_file, client_secret="super-secret-client-value")
    write_token_file(token_file, access_token="super-secret-access-token", refresh_token="super-secret-refresh-token")

    report = run_runtime_doctor(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        },
        generated_at="2026-06-25T12:00:00Z",
    )

    assert report.status.overall_status == "ready"
    assert report.status.path_checks[0].reason == "installed_app_client_shape_valid_secret_redacted"
    assert report.status.path_checks[1].reason == "workspace_token_shape_valid_tokens_redacted"
    assert "super-secret-client-value" not in report.rendered_text
    assert "super-secret-access-token" not in report.rendered_text
    assert "super-secret-refresh-token" not in report.rendered_text
    assert "Runtime Doctor: local read-only" in report.rendered_text
    assert "Stage: 149P" in report.rendered_text


def test_149p_malformed_client_json_reports_blocked_reason(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    client_file.write_text("{not-json", encoding="utf-8")
    write_token_file(token_file)

    status = build_runtime_doctor_status(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )

    assert status.overall_status == "blocked"
    assert status.path_checks[0].shape_status == "blocked"
    assert status.path_checks[0].reason == "invalid_json"


def test_149p_token_scopes_drive_calendar_and_gmail_readiness(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    write_client_file(client_file)
    write_token_file(
        token_file,
        scopes=[GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_METADATA_SCOPE, GOOGLE_GMAIL_READONLY_SCOPE],
    )

    status = build_runtime_doctor_status(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )
    readiness = {item.service: item for item in status.service_readiness}

    assert readiness["calendar_readonly"].ready is True
    assert readiness["gmail_metadata"].ready is True
    assert readiness["gmail_readonly"].ready is True
    assert GOOGLE_CALENDAR_READONLY_SCOPE in readiness["calendar_readonly"].available_scopes


def test_149p_gmail_metadata_and_readonly_are_reported_separately(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    write_client_file(client_file)
    write_token_file(token_file, scopes=[GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_METADATA_SCOPE])

    status = build_runtime_doctor_status(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )
    readiness = {item.service: item for item in status.service_readiness}

    assert readiness["gmail_metadata"].ready is True
    assert readiness["gmail_readonly"].ready is False
    assert readiness["gmail_readonly"].reason == "gmail_readonly_scope_missing"


def test_149p_direct_token_env_is_redacted_and_does_not_require_token_file(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "missing-token.json"
    write_client_file(client_file)

    report = run_runtime_doctor(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
            "ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "direct-secret-token-149p",
        }
    )
    readiness = {item.service: item for item in report.status.service_readiness}
    env_checks = {item.name: item for item in report.status.env_checks}

    assert readiness["calendar_readonly"].ready is True
    assert readiness["calendar_readonly"].reason == "direct_token_configured_redacted"
    assert env_checks["ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN"].status == "configured_redacted"
    assert "direct-secret-token-149p" not in report.rendered_text


def test_149p_json_output_is_structured_and_secret_free(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    write_client_file(client_file, client_secret="json-client-secret")
    write_token_file(token_file, access_token="json-access-secret", refresh_token="json-refresh-secret")

    report = run_runtime_doctor(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        },
        output_format="json",
    )
    payload = json.loads(report.rendered_text)

    assert payload["stage"] == "149P"
    assert payload["roadmap_closed_through"] == "172P"
    assert payload["next_stage_authorized"] is False
    assert payload["next_stage"] == "173P"
    assert "json-client-secret" not in report.rendered_text
    assert "json-access-secret" not in report.rendered_text
    assert "json-refresh-secret" not in report.rendered_text


def test_149p_boundary_status_declares_no_authority():
    status = build_runtime_doctor_status(env={})

    assert all(value is False for value in asdict(status.boundary_status).values())


def test_149p_main_prints_text_report_and_returns_zero(capsys: pytest.CaptureFixture[str]):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Runtime Doctor: local read-only" in captured.out
    assert "Stage: 149P" in captured.out
    assert captured.err == ""


def test_149p_render_rejects_invalid_output_format():
    status = build_runtime_doctor_status(env={})

    with pytest.raises(ValueError, match="rejected_invalid_output_format"):
        render_runtime_doctor_report(status=status, output_format="yaml")


def test_149p_runtime_doctor_has_no_network_subprocess_or_oauth_activation_imports():
    text = DOCTOR_PATH.read_text(encoding="utf-8")

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "resolve_google_workspace_access_token",
        "build_google_oauth_authorization_url",
        "exchange_google_oauth_code",
        "refresh_google_oauth_access_token",
        "save_google_oauth_token_record",
        "api.telegram.org",
        "gmail.googleapis.com",
        "calendar/v3",
    ]:
        assert forbidden not in text
