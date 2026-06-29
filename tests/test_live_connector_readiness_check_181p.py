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
from app.live_connector_readiness_check import (
    ALLOWED_READINESS_STATUSES,
    LIVE_CONNECTOR_READINESS_CHECK_STAGE,
    LIVE_CONNECTOR_READINESS_CHECK_STATUS,
    LiveConnectorReadinessItem,
    LiveConnectorReadinessReport,
    build_live_connector_readiness_report,
    render_compact_live_connector_readiness_block,
    render_live_connector_readiness_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/LIVE_CONNECTOR_READINESS_CHECK_181P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def write_client_file(path: Path, *, client_secret: str = "client-secret-181p") -> None:
    path.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "client-181p.apps.googleusercontent.com",
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
    access_token: str = "access-token-181p",
    refresh_token: str = "refresh-token-181p",
    scopes: list[str] | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "stage": GOOGLE_OAUTH_WORKSPACE_STAGE,
                "client_id": "client-181p.apps.googleusercontent.com",
                "scopes": scopes
                if scopes is not None
                else [GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_METADATA_SCOPE],
                "token_type": "Bearer",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": 4_000_000_000,
            }
        ),
        encoding="utf-8",
    )


def test_181p_missing_connector_files_report_not_connected_without_crashing(tmp_path: Path):
    report = build_live_connector_readiness_report(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(tmp_path / "missing-client.json"),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(tmp_path / "missing-token.json"),
        }
    )
    items = {item.name: item for item in report.items}

    assert report.stage == LIVE_CONNECTOR_READINESS_CHECK_STAGE
    assert report.status == LIVE_CONNECTOR_READINESS_CHECK_STATUS
    assert report.overall_status == "not_connected"
    assert items["Calendar read-only"].status == "not_connected"
    assert items["Gmail context"].status == "not_connected"
    assert items["External writes"].status == "disabled"


def test_181p_valid_oauth_shape_reports_calendar_and_gmail_connected_without_printing_secrets(tmp_path: Path):
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    write_client_file(client_file, client_secret="very-secret-client-181p")
    write_token_file(
        token_file,
        access_token="very-secret-access-181p",
        refresh_token="very-secret-refresh-181p",
        scopes=[GOOGLE_CALENDAR_READONLY_SCOPE, GOOGLE_GMAIL_METADATA_SCOPE, GOOGLE_GMAIL_READONLY_SCOPE],
    )

    report = build_live_connector_readiness_report(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(token_file),
        }
    )
    rendered = render_live_connector_readiness_report(report)
    items = {item.name: item for item in report.items}

    assert report.overall_status == "partially_connected"
    assert items["Calendar read-only"].status == "connected"
    assert items["Gmail context"].status == "connected"
    assert "very-secret-client-181p" not in rendered
    assert "very-secret-access-181p" not in rendered
    assert "very-secret-refresh-181p" not in rendered
    assert str(client_file) not in rendered
    assert str(token_file) not in rendered


def test_181p_direct_token_env_is_redacted_and_not_rendered(tmp_path: Path):
    client_file = tmp_path / "client.json"
    write_client_file(client_file)
    report = build_live_connector_readiness_report(
        env={
            "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE": str(client_file),
            "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE": str(tmp_path / "missing-token.json"),
            "ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN": "direct-secret-token-181p",
        }
    )
    rendered = render_live_connector_readiness_report(report)

    assert "Calendar read-only: connected" in rendered
    assert "direct-secret-token-181p" not in rendered
    assert "Secrets: redacted" in rendered


def test_181p_render_declares_disabled_write_boundaries():
    rendered = render_live_connector_readiness_report(build_live_connector_readiness_report(env={}))

    assert "Live Connector Readiness" in rendered
    assert "Stage: 181P" in rendered
    assert "Connector activation: disabled" in rendered
    assert "OAuth generation: disabled" in rendered
    assert "OAuth refresh: disabled" in rendered
    assert "Gmail draft creation: disabled" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No connector was activated." in rendered
    assert "No external action was taken." in rendered


def test_181p_compact_block_is_status_safe():
    block = render_compact_live_connector_readiness_block(build_live_connector_readiness_report(env={}))

    assert block[0] == "Live connector readiness:"
    assert "- Full check: /checkup" in block
    assert all("secret" not in line.lower() for line in block)


def test_181p_rejects_unsupported_status_and_authority_expansion():
    item = build_live_connector_readiness_report(env={}).items[0]
    report = build_live_connector_readiness_report(env={})

    with pytest.raises(ValueError, match="unsupported status"):
        LiveConnectorReadinessItem(**{**asdict(item), "status": "maybe"})
    with pytest.raises(ValueError, match="must not expand authority"):
        LiveConnectorReadinessReport(**{**asdict(report), "external_write_allowed": True})


def test_181p_all_items_use_allowed_statuses_and_no_authority_flags_are_enabled():
    report = build_live_connector_readiness_report(env={})

    assert {item.status for item in report.items} <= ALLOWED_READINESS_STATUSES
    assert report.secrets_redacted is True
    assert report.connector_activation_allowed is False
    assert report.oauth_generation_allowed is False
    assert report.oauth_refresh_allowed is False
    assert report.gmail_draft_creation_allowed is False
    assert report.gmail_send_allowed is False
    assert report.calendar_write_allowed is False
    assert report.external_write_allowed is False
    assert report.memory_mutation_allowed is False
    assert report.model_call_allowed is False
    assert report.tool_call_allowed is False


def test_181p_reference_and_roadmap_close_readiness_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "181P - Live Connector Readiness Check v0" in reference
    assert "181P is a customer-facing readiness check only." in reference
    assert "OAuth token refresh" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"181P","stage_name":"Live Connector Readiness Check v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "205P and later remain unauthorized" in roadmap
