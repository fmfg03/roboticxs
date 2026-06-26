from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_binding_v1 import build_calendar_context_source_trace
from app.gmail_context_binding_v1 import build_gmail_context_source_trace
from app.gmail_readonly_context_scan import GmailReadonlyConfig, read_gmail_context
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.memory_center_projection import MemoryCenterItem
from app.source_trace_receipts import (
    SOURCE_TRACE_RECEIPTS_STAGE,
    SOURCE_TRACE_RECEIPTS_STATUS,
    SourceTraceReceipt,
    SourceTraceReceiptItem,
    build_source_trace_receipt,
    render_source_trace_receipt,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)
from tests.test_gmail_readonly_context_scan_163p import FakeGmailReadonlyHttpClient
from tests.test_runnable_telegram_robot_mvp_130p import PendingProposalFixture


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SOURCE_TRACE_RECEIPTS_184P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def calendar_result_ok() -> CalendarReadResult:
    return CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-26T00:00:00-06:00",
        window_end="2026-06-26T23:59:59-06:00",
        events=(
            CalendarEventSnapshot(
                event_id="evt-184p-demo",
                summary="Victor kickoff prep",
                start="2026-06-26T11:00:00-06:00",
                end="2026-06-26T11:30:00-06:00",
                all_day=False,
                location="Meet",
                description_preview="Prep customer source trace receipt.",
                organizer_email="owner@example.com",
                attendee_count=2,
                html_link="https://calendar.google.com/event?eid=184p",
                source="google_calendar_readonly",
            ),
        ),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def gmail_scan_with_signal():
    return read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="gmail-token-184p",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=FakeGmailReadonlyHttpClient(),
    )


def approved_memory() -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id="mem-184p",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_kind="preference",
        status="active",
        scopes=("telegram",),
        sensitivity="ordinary",
        allowed_uses=("telegram_context",),
        skill_ids=(),
        content="Francisco prefers compact source receipts.",
        bounded_summary="Francisco prefers compact source receipts.",
        source="local_fixture",
    )


def test_184p_builds_unified_receipt_for_calendar_gmail_memory_and_documents():
    receipt = build_source_trace_receipt(
        calendar_trace=build_calendar_context_source_trace(calendar_result=calendar_result_ok()),
        gmail_trace=build_gmail_context_source_trace(gmail_scan=gmail_scan_with_signal()),
        memory_snapshot=build_memory_center_telegram_snapshot(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            source_bundle=TelegramMemoryCenterSourceBundle(approved_memory_items=(approved_memory(),)),
        ),
        document_reviews=(),
    )
    rendered = render_source_trace_receipt(receipt)

    assert receipt.stage == SOURCE_TRACE_RECEIPTS_STAGE
    assert receipt.status == SOURCE_TRACE_RECEIPTS_STATUS
    assert "- Calendar: used" in rendered
    assert "evt-184p-demo | Victor kickoff prep" in rendered
    assert "- Gmail: used" in rendered
    assert "be relevant for prep" in rendered
    assert "- Memory: used" in rendered
    assert "- Documents: not_used" in rendered
    assert "- Usage/Cost: not_used" in rendered


def test_184p_gmail_not_connected_and_memory_approval_required_are_explicit():
    gmail_trace = build_gmail_context_source_trace(
        gmail_scan=read_gmail_context(
            config=GmailReadonlyConfig(
                access_token="",
                query="newer_than:30d",
                max_results=5,
                timeout_seconds=30,
            ),
            http_client=FakeGmailReadonlyHttpClient(),
        )
    )
    receipt = build_source_trace_receipt(
        calendar_trace=build_calendar_context_source_trace(calendar_result=calendar_result_ok()),
        gmail_trace=gmail_trace,
        memory_snapshot=build_memory_center_telegram_snapshot(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            source_bundle=TelegramMemoryCenterSourceBundle(
                pending_memory_proposals=(PendingProposalFixture(),),
            ),
        ),
    )
    rendered = render_source_trace_receipt(receipt)

    assert "- Gmail: not_connected" in rendered
    assert "Reason: missing_access_token" in rendered
    assert "- Memory: approval_required" in rendered
    assert "proposal-loop-telegram" in rendered
    assert "Next: use /memory_review" in rendered


def test_184p_receipt_declares_action_boundaries_and_no_authority_expansion():
    receipt = build_source_trace_receipt()
    rendered = render_source_trace_receipt(receipt)

    assert receipt.read_only is True
    assert receipt.connector_activation_allowed is False
    assert receipt.oauth_flow_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.gmail_send_allowed is False
    assert receipt.gmail_modify_allowed is False
    assert receipt.gmail_delete_allowed is False
    assert receipt.memory_center_mutated is False
    assert receipt.model_call_allowed is False
    assert receipt.tool_call_allowed is False
    assert receipt.worker_dispatch_allowed is False
    assert receipt.external_write_allowed is False
    assert "- Gmail send: disabled" in rendered
    assert "- Gmail modify/delete: disabled" in rendered
    assert "- Calendar writes: disabled" in rendered
    assert "- Memory mutation: approval_required" in rendered
    assert "- External writes: disabled" in rendered


def test_184p_receipt_rejects_unsupported_status_and_authority_expansion():
    receipt = build_source_trace_receipt()

    with pytest.raises(ValueError, match="unsupported status"):
        SourceTraceReceiptItem(source_name="Gmail", status="sent", summary="bad")
    with pytest.raises(ValueError, match="must not expand authority"):
        SourceTraceReceipt(**{**asdict(receipt), "external_write_allowed": True})


def test_184p_receipt_redacts_secret_like_values():
    receipt = build_source_trace_receipt(
        calendar_trace=build_calendar_context_source_trace(calendar_result=calendar_result_ok()),
        gmail_trace=build_gmail_context_source_trace(gmail_scan=gmail_scan_with_signal()),
    )
    rendered = render_source_trace_receipt(receipt)

    for forbidden in ("gmail-token-184p", "Authorization", "Bearer", "client_secret", "refresh_token"):
        assert forbidden not in rendered


def test_184p_reference_and_roadmap_close_source_trace_receipts_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "184P - Source Trace Receipts v0" in reference
    assert "184P is source trace receipt rendering only." in reference
    assert "188P and later remain unauthorized" in reference
    assert '"stage_id":"184P","stage_name":"Source Trace Receipts v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "188P and later remain unauthorized" in roadmap
