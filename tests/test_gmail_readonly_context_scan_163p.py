from __future__ import annotations

import json
from pathlib import Path

from app.gmail_readonly_context_scan import (
    GMAIL_READONLY_CONTEXT_SCAN_STAGE,
    GmailReadonlyConfig,
    main,
    read_gmail_context,
    render_gmail_readonly_context_scan,
    run_gmail_readonly_context_scan,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/GMAIL_READONLY_CONTEXT_SCAN_163P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeGmailReadonlyHttpClient:
    def __init__(self) -> None:
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
        if url.endswith("/messages"):
            return {"messages": [{"id": "msg-1", "threadId": "thr-1"}]}
        return {
            "id": "msg-1",
            "threadId": "thr-1",
            "labelIds": ["INBOX"],
            "snippet": "Please review the proposal before tomorrow's meeting and follow up.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Client proposal prep"},
                    {"name": "From", "value": "client@example.com"},
                    {"name": "Date", "value": "Thu, 25 Jun 2026 10:00:00 -0600"},
                ],
                "parts": [
                    {
                        "filename": "proposal.pdf",
                        "body": {"attachmentId": "att-1"},
                    }
                ],
            },
        }


def test_163p_gmail_readonly_context_scan_detects_context_signals_without_writes():
    client = FakeGmailReadonlyHttpClient()

    record = read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="token-163p",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=client,
    )

    assert record.stage == GMAIL_READONLY_CONTEXT_SCAN_STAGE
    assert record.status == "completed_with_signals"
    assert len(client.calls) == 2
    assert client.calls[0]["headers"]["Authorization"] == "Bearer token-163p"
    assert client.calls[0]["params"] == {"q": "newer_than:30d", "maxResults": "5"}
    assert client.calls[1]["params"]["format"] == "metadata"
    assert record.messages[0].subject == "Client proposal prep"
    assert record.messages[0].attachment_count == 1
    assert {signal.signal_type for signal in record.signals} == {
        "related_context",
        "attachment_context",
        "followup_context",
    }
    assert record.read_only is True
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.gmail_delete_allowed is False
    assert record.calendar_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False


def test_163p_missing_gmail_token_fails_closed_without_http_call():
    client = FakeGmailReadonlyHttpClient()

    record = read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=client,
    )

    assert record.status == "blocked_gmail_unavailable"
    assert record.error_code == "missing_access_token"
    assert record.messages == ()
    assert record.signals == ()
    assert client.calls == []


def test_163p_run_path_uses_direct_gmail_token_and_renders_boundaries(monkeypatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", "gmail-token-163p")
    record = run_gmail_readonly_context_scan(http_client=FakeGmailReadonlyHttpClient())
    rendered = render_gmail_readonly_context_scan(record)

    assert record.status == "completed_with_signals"
    assert "Gmail Read-Only Context Scan" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Gmail modify/archive/label: disabled" in rendered
    assert "Gmail delete: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "No external action was taken." in rendered
    assert "gmail-token-163p" not in rendered


def test_163p_cli_json_output_is_structured_and_fail_closed(monkeypatch, capsys):
    monkeypatch.delenv("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ROBOTICXS_GOOGLE_OAUTH_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", raising=False)

    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["stage"] == "163P"
    assert payload["status"] == "blocked_gmail_unavailable"
    assert payload["gmail_send_allowed"] is False
    assert payload["external_write_allowed"] is False


def test_163p_reference_and_roadmap_close_gmail_context_scan_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "163P is Gmail read-only context scanning only." in reference
    assert "does not authorize Gmail send" in reference
    assert "Memory Center mutation" in reference
    assert '"stage_id":"163P","stage_name":"Gmail Read-Only Context Scan v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "209P and later remain unauthorized" in roadmap
