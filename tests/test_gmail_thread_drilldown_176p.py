from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.gmail_readonly_context_scan import GmailReadonlyConfig
from app.gmail_thread_drilldown import (
    GMAIL_THREAD_DRILLDOWN_STAGE,
    GmailThreadDrilldownRecord,
    read_gmail_thread,
    render_gmail_thread_drilldown,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/GMAIL_THREAD_DRILLDOWN_176P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeGmailThreadHttpClient:
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
        return {
            "id": "thread-176p",
            "messages": [
                {
                    "id": "msg-1",
                    "threadId": "thread-176p",
                    "labelIds": ["INBOX"],
                    "snippet": "Can you review the proposal before the meeting?",
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
                },
                {
                    "id": "msg-2",
                    "threadId": "thread-176p",
                    "labelIds": ["INBOX"],
                    "snippet": "ROI details are the key question.",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Re: Client proposal prep"},
                            {"name": "From", "value": "owner@example.com"},
                            {"name": "Date", "value": "Thu, 25 Jun 2026 10:15:00 -0600"},
                        ],
                        "parts": [],
                    },
                },
            ],
        }


def config(access_token: str = "token-176p") -> GmailReadonlyConfig:
    return GmailReadonlyConfig(
        access_token=access_token,
        query="newer_than:30d",
        max_results=5,
        timeout_seconds=30,
    )


def test_176p_reads_gmail_thread_metadata_without_writes():
    client = FakeGmailThreadHttpClient()

    record = read_gmail_thread(config=config(), thread_id="thread-176p", http_client=client)
    rendered = render_gmail_thread_drilldown(record)

    assert record.stage == GMAIL_THREAD_DRILLDOWN_STAGE
    assert record.status == "completed_with_messages"
    assert len(client.calls) == 1
    assert client.calls[0]["headers"]["Authorization"] == "Bearer token-176p"
    assert client.calls[0]["url"].endswith("/threads/thread-176p")
    assert record.subject == "Client proposal prep"
    assert len(record.messages) == 2
    assert "client@example.com" in rendered
    assert "Can you review the proposal before the meeting?" in rendered
    assert "msg-1: 1 attachment(s)" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Gmail modify/archive/label: disabled" in rendered
    assert "Gmail delete: disabled" in rendered
    assert "Draft creation: disabled" in rendered
    assert "No external action was taken." in rendered


def test_176p_missing_token_and_thread_id_fail_closed_without_http_call():
    client = FakeGmailThreadHttpClient()

    missing_token = read_gmail_thread(config=config(access_token=""), thread_id="thread-176p", http_client=client)
    missing_thread = read_gmail_thread(config=config(), thread_id="", http_client=client)

    assert missing_token.status == "blocked_gmail_thread_unavailable"
    assert missing_token.blocked_reason == "missing_access_token"
    assert missing_thread.blocked_reason == "missing_thread_id"
    assert client.calls == []


def test_176p_record_rejects_authority_expansion():
    valid = read_gmail_thread(config=config(), thread_id="thread-176p", http_client=FakeGmailThreadHttpClient())

    with pytest.raises(ValueError, match="must not expand authority"):
        replace(valid, gmail_modify_allowed=True)


def test_176p_reference_and_roadmap_close_gmail_thread_drilldown_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "176P is Gmail Thread Drilldown v0 only." in reference
    assert "/gmail_thread <thread_id>" in reference
    assert "does not authorize Gmail send" in reference
    assert '"stage_id":"176P","stage_name":"Gmail Thread Drilldown v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
