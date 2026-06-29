from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.document_review_pack import build_document_review_pack_record
from app.gmail_readonly_context_scan import GmailContextSignal, GmailReadonlyContextScanRecord
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.meeting_prep_pack import build_meeting_prep_pack
from app.meeting_prep_pack_v1 import (
    MEETING_PREP_PACK_V1_STAGE,
    MeetingPrepPackV1Record,
    build_meeting_prep_pack_v1,
    render_meeting_prep_pack_v1,
)
from app.memory_center_projection import MemoryCenterItem
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle, build_memory_center_telegram_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEETING_PREP_PACK_V1_175P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event() -> CalendarEventSnapshot:
    return CalendarEventSnapshot(
        event_id="evt-175p-client-demo",
        summary="Client demo prep meeting",
        start="2026-06-25T10:00:00-06:00",
        end="2026-06-25T10:30:00-06:00",
        all_day=False,
        location="Google Meet",
        description_preview="Review proposal context and prepare open questions.",
        organizer_email="owner@example.com",
        attendee_count=3,
        html_link="https://calendar.google.com/event?eid=175p",
        source="google_calendar_readonly",
    )


def base_pack():
    calendar_result = CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-24T10:00:00-06:00",
        window_end="2026-07-01T10:00:00-06:00",
        events=(event(),),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )
    scan = build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=build_calendar_context_scan_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            calendar_result=calendar_result,
        ),
    )
    memory_snapshot = build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                MemoryCenterItem(
                    item_id="mem-175p-prep",
                    owner_id="local-owner",
                    robot_id="roboticxs-dev",
                    memory_kind="preference",
                    status="active",
                    scopes=("telegram", "general"),
                    sensitivity="ordinary",
                    allowed_uses=("telegram_context",),
                    skill_ids=(),
                    content="Francisco prefers compact meeting prep.",
                    bounded_summary="Francisco prefers compact meeting prep.",
                    source="local_fixture",
                ),
            ),
        ),
    )
    return build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot,
    )


def gmail_scan(*, blocked: bool = False) -> GmailReadonlyContextScanRecord:
    return GmailReadonlyContextScanRecord(
        stage="163P",
        status="blocked" if blocked else "completed_with_signals",
        query="newer_than:30d",
        messages=(),
        signals=()
        if blocked
        else (
            GmailContextSignal(
                signal_id="sig-175p",
                message_id="msg-1",
                thread_id="thread-1",
                signal_type="followup_context",
                summary="Client asked for ROI details before the demo.",
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
        error_code="missing_access_token" if blocked else None,
    )


def document_review():
    return build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="Proposal.pdf",
        extracted_text=(
            "The proposal must include ROI details and a demo agenda. "
            "The customer asked for pricing risks, approval timing, and follow-up questions."
        ),
    )


def test_175p_builds_meeting_prep_pack_v1_from_read_only_context():
    record = build_meeting_prep_pack_v1(
        base_pack=base_pack(),
        gmail_scan=gmail_scan(),
        document_reviews=(document_review(),),
    )
    rendered = render_meeting_prep_pack_v1(record)

    assert record.stage == MEETING_PREP_PACK_V1_STAGE
    assert record.status == "completed_with_context"
    assert "151P" in record.source_stages
    assert "163P" in record.source_stages
    assert "166P" in record.source_stages
    assert "Client demo prep meeting" in rendered
    assert "Francisco prefers compact meeting prep." in rendered
    assert "followup_context: Client asked for ROI details before the demo." in rendered
    assert "Proposal.pdf:" in rendered
    assert "Risks and questions:" in rendered
    assert "Gmail send/modify: disabled" in rendered
    assert "Draft creation: disabled" in rendered
    assert "No external action was taken." in rendered


def test_175p_reports_blocked_sources_without_expanding_authority():
    record = build_meeting_prep_pack_v1(base_pack=base_pack(), gmail_scan=gmail_scan(blocked=True))

    assert record.status == "completed_with_blocked_sources"
    assert "Gmail: unavailable (missing_access_token)." in record.blocked_source_lines
    assert "Documents: no local document review pack supplied." in record.blocked_source_lines
    assert record.calendar_write_allowed is False
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.draft_created is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.scheduler_allowed is False
    assert record.external_write_allowed is False


def test_175p_record_rejects_authority_expansion():
    valid = build_meeting_prep_pack_v1(base_pack=base_pack())

    with pytest.raises(ValueError, match="must not expand authority"):
        replace(valid, external_write_allowed=True)


def test_175p_reference_and_roadmap_close_meeting_prep_v1_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "175P is Meeting Prep Pack v1 only." in reference
    assert "/prep" in reference
    assert "does not authorize Calendar writes" in reference
    assert '"stage_id":"175P","stage_name":"Meeting Prep Pack v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "203P and later remain unauthorized" in roadmap
