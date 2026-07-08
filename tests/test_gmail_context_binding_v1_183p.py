from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.gmail_context_binding_v1 import (
    GMAIL_CONTEXT_BINDING_V1_STAGE,
    GMAIL_CONTEXT_BINDING_V1_STATUS,
    GmailContextBindingV1Record,
    GmailContextSourceTrace,
    append_gmail_source_trace,
    build_gmail_context_binding_v1_record,
    build_gmail_context_source_trace,
    render_gmail_context_binding_v1_record,
    render_gmail_context_source_trace,
)
from app.gmail_readonly_context_scan import GmailReadonlyConfig, read_gmail_context
from tests.test_gmail_readonly_context_scan_163p import FakeGmailReadonlyHttpClient


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/GMAIL_CONTEXT_BINDING_V1_183P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def gmail_scan_with_signal():
    return read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="gmail-token-183p",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=FakeGmailReadonlyHttpClient(),
    )


def gmail_scan_missing_token():
    return read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=FakeGmailReadonlyHttpClient(),
    )


def test_183p_connected_gmail_scan_builds_source_trace():
    trace = build_gmail_context_source_trace(gmail_scan=gmail_scan_with_signal())
    rendered = render_gmail_context_source_trace(trace)

    assert trace.source_name == "gmail_readonly_metadata"
    assert trace.status == "connected"
    assert trace.messages_scanned == 1
    assert trace.thread_refs == ("thr-1 | msg-1 | Client proposal prep",)
    assert trace.signal_refs
    assert "- Gmail: connected" in rendered
    assert "- Threads used:" in rendered
    assert "thr-1 | msg-1 | Client proposal prep" in rendered
    assert "- Signals used:" in rendered
    assert "- Writes: disabled" in rendered


def test_183p_missing_gmail_token_fails_closed_with_checkup_guidance():
    trace = build_gmail_context_source_trace(gmail_scan=gmail_scan_missing_token())
    rendered = render_gmail_context_source_trace(trace)

    assert trace.status == "not_connected"
    assert trace.blocked_reason == "missing_access_token"
    assert "- Gmail: not_connected" in rendered
    assert "- Reason: missing_access_token" in rendered
    assert "- Next: run /checkup" in rendered
    assert "- Threads used: none" in rendered


def test_183p_binding_record_declares_read_only_boundaries():
    record = build_gmail_context_binding_v1_record(gmail_scan=gmail_scan_with_signal())
    rendered = render_gmail_context_binding_v1_record(record)

    assert record.stage == GMAIL_CONTEXT_BINDING_V1_STAGE
    assert record.status == GMAIL_CONTEXT_BINDING_V1_STATUS
    assert record.gmail_connected is True
    assert record.messages_scanned == 1
    assert record.signals_found == 3
    assert record.read_only is True
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.gmail_delete_allowed is False
    assert record.calendar_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert "Gmail Context Binding v1" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Gmail modify/archive/label: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_183p_append_source_trace_excludes_secrets_and_auth_headers():
    rendered = append_gmail_source_trace("Daily Brief\n\nStatus: completed", build_gmail_context_source_trace(gmail_scan=gmail_scan_with_signal()))

    assert rendered.startswith("Daily Brief")
    assert "Gmail source trace:" in rendered
    for forbidden in ("gmail-token-183p", "refresh-token", "client-secret", "Authorization", "Bearer"):
        assert forbidden not in rendered


def test_183p_rejects_authority_expansion():
    trace = build_gmail_context_source_trace(gmail_scan=gmail_scan_with_signal())
    record = build_gmail_context_binding_v1_record(gmail_scan=gmail_scan_with_signal())

    with pytest.raises(ValueError, match="must not allow Gmail writes"):
        GmailContextSourceTrace(**{**asdict(trace), "gmail_send_allowed": True})
    with pytest.raises(ValueError, match="must not expand authority"):
        GmailContextBindingV1Record(**{**asdict(record), "external_write_allowed": True})


def test_183p_reference_and_roadmap_close_gmail_binding_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "183P - Gmail Context Binding v1" in reference
    assert "183P is read-only Gmail context binding only." in reference
    assert "Gmail draft creation" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"183P","stage_name":"Gmail Context Binding v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "222P and later remain unauthorized" in roadmap
