from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.cross_source_daily_brief import (
    CROSS_SOURCE_DAILY_BRIEF_STAGE,
    CrossSourceDailyBriefRecord,
    build_cross_source_daily_brief,
    render_cross_source_daily_brief,
)
from app.document_review_pack import build_document_review_pack_record
from app.gmail_readonly_context_scan import (
    GmailContextSignal,
    GmailReadonlyContextScanRecord,
)
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.memory_center_projection import MemoryCenterItem
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CROSS_SOURCE_DAILY_BRIEF_174P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def calendar_result(ok: bool = True) -> CalendarReadResult:
    return CalendarReadResult(
        ok=ok,
        calendar_id="primary",
        window_start="2026-06-26T00:00:00Z",
        window_end="2026-06-26T23:59:59Z",
        events=(
            CalendarEventSnapshot(
                event_id="evt-174p",
                summary="Client demo",
                start="2026-06-26T10:00:00Z",
                end="2026-06-26T10:30:00Z",
                all_day=False,
                location="Google Meet",
                description_preview="Demo prep",
                organizer_email="owner@example.com",
                attendee_count=2,
                html_link=None,
                source="google_calendar_readonly",
            ),
        )
        if ok
        else (),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None if ok else "missing_access_token",
        error_message=None if ok else "Calendar token missing",
    )


def gmail_scan() -> GmailReadonlyContextScanRecord:
    return GmailReadonlyContextScanRecord(
        stage="163P",
        status="completed_with_signals",
        query="newer_than:30d",
        messages=(),
        signals=(
            GmailContextSignal(
                signal_id="sig-174p",
                message_id="msg-1",
                thread_id="thread-1",
                signal_type="follow_up",
                summary="Client asked for ROI details.",
                confidence="medium",
            ),
        ),
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def memory_snapshot():
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                MemoryCenterItem(
                    item_id="mem-174p",
                    owner_id="local-owner",
                    robot_id="roboticxs-dev",
                    memory_kind="preference",
                    status="active",
                    scopes=("telegram",),
                    sensitivity="ordinary",
                    allowed_uses=("telegram_context",),
                    skill_ids=(),
                    content="Francisco prefers compact daily briefs.",
                    bounded_summary="Francisco prefers compact daily briefs.",
                    source="local_memory_store",
                ),
            )
        ),
    )


def document_review():
    return build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="Proposal.pdf",
        extracted_text="The proposal must include ROI details and a demo agenda.",
    )


def test_174p_builds_empty_brief_with_blocked_sources_and_boundaries():
    record = build_cross_source_daily_brief(owner_id="local-owner", robot_id="roboticxs-dev")
    rendered = render_cross_source_daily_brief(record)

    assert record.stage == CROSS_SOURCE_DAILY_BRIEF_STAGE
    assert record.status == "completed_empty_sources"
    assert record.read_only is True
    assert record.calendar_write_allowed is False
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.memory_store_written is False
    assert record.memory_center_mutated is False
    assert record.draft_created is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.scheduler_allowed is False
    assert record.external_write_allowed is False
    assert "Calendar: no read-only Calendar result supplied." in rendered
    assert "No external action was taken." in rendered


def test_174p_combines_calendar_gmail_memory_and_documents():
    record = build_cross_source_daily_brief(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(),
        gmail_scan=gmail_scan(),
        memory_snapshot=memory_snapshot(),
        document_reviews=(document_review(),),
    )
    rendered = render_cross_source_daily_brief(record)

    assert record.status == "completed_with_context"
    assert "2026-06-26T10:00:00Z - Client demo (Google Meet)" in rendered
    assert "follow_up: Client asked for ROI details." in rendered
    assert "preference: Francisco prefers compact daily briefs." in rendered
    assert "Proposal.pdf:" in rendered
    assert "Review email context signals before deciding whether a follow-up draft is needed." in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Gmail send/modify: disabled" in rendered
    assert "Memory Store writes: disabled" in rendered
    assert "Draft creation: disabled" in rendered


def test_174p_uses_only_visible_approved_memory_context():
    record = build_cross_source_daily_brief(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        memory_snapshot=memory_snapshot(),
    )

    assert record.memory_context_lines == ("preference: Francisco prefers compact daily briefs.",)


def test_174p_reports_blocked_calendar_and_gmail_sources():
    blocked_gmail = GmailReadonlyContextScanRecord(
        stage="163P",
        status="blocked",
        query="newer_than:30d",
        messages=(),
        signals=(),
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        error_code="missing_access_token",
    )

    record = build_cross_source_daily_brief(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(ok=False),
        gmail_scan=blocked_gmail,
    )

    assert "Calendar: unavailable (missing_access_token)." in record.blocked_source_lines
    assert "Gmail: unavailable (missing_access_token)." in record.blocked_source_lines
    assert record.status == "completed_empty_sources"


def test_174p_rejects_authority_expansion():
    valid = build_cross_source_daily_brief(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="must not expand authority"):
        CrossSourceDailyBriefRecord(**{**asdict(valid), "external_write_allowed": True})


def test_174p_reference_and_roadmap_close_cross_source_daily_brief_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "174P is Cross-Source Daily Brief v1 only." in reference
    assert "/daily_brief" in reference
    assert "does not authorize Calendar writes" in reference
    assert '"stage_id":"174P","stage_name":"Cross-Source Daily Brief v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "202P and later remain unauthorized" in roadmap
