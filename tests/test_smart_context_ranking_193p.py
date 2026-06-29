from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.document_review_pack import build_document_review_pack_record
from app.gmail_readonly_context_scan import GmailContextSignal, GmailReadonlyContextScanRecord
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.memory_center_projection import MemoryCenterItem
from app.smart_context_ranking import (
    SMART_CONTEXT_RANKING_STAGE,
    SmartContextRankingRecord,
    build_smart_context_ranking,
    render_smart_context_ranking,
)
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle, build_memory_center_telegram_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SMART_CONTEXT_RANKING_193P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_193p_ranks_context_with_reasons_and_source_trace():
    ranking = build_smart_context_ranking(
        owner_id="owner-193p",
        robot_id="robot-193p",
        calendar_result=calendar_result(),
        gmail_scan=gmail_scan(),
        memory_snapshot=build_memory_center_telegram_snapshot(
            owner_id="owner-193p",
            robot_id="robot-193p",
            source_bundle=TelegramMemoryCenterSourceBundle(approved_memory_items=(memory_item(),)),
        ),
        document_reviews=(document_review(),),
    )
    rendered = render_smart_context_ranking(ranking)

    assert ranking.stage == SMART_CONTEXT_RANKING_STAGE
    assert ranking.status == "ranked_context_available"
    assert ranking.ranked_items[0].source_type == "calendar"
    assert ranking.ranked_items[0].score >= ranking.ranked_items[-1].score
    assert "Prioritized context" in rendered
    assert "Why:" in rendered
    assert "Source:" in rendered
    assert "Next:" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_193p_empty_context_fails_closed_without_authority():
    ranking = build_smart_context_ranking(owner_id="owner-193p", robot_id="robot-193p")
    rendered = render_smart_context_ranking(ranking)

    assert ranking.status == "ranked_context_empty"
    assert ranking.ranked_items == ()
    assert "No rankable context" in rendered
    assert ranking.calendar_write_allowed is False
    assert ranking.gmail_write_allowed is False
    assert ranking.memory_center_mutated is False


def test_193p_rejects_authority_expansion():
    ranking = build_smart_context_ranking(owner_id="owner-193p", robot_id="robot-193p")

    with pytest.raises(ValueError, match="must not expand authority"):
        SmartContextRankingRecord(**{**asdict(ranking), "external_write_allowed": True})


def test_193p_reference_and_roadmap_close_ranking_without_priority_engine():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "193P ranks Calendar, Gmail, Memory, and Document context" in reference
    assert "no proactive priority engine" in reference
    assert '"stage_id":"193P","stage_name":"Smart Context Ranking v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "214P and later remain unauthorized" in roadmap


def calendar_result() -> CalendarReadResult:
    return CalendarReadResult(
        ok=True,
        calendar_id="primary",
        window_start="2026-06-29T00:00:00Z",
        window_end="2026-07-06T00:00:00Z",
        events=(
            CalendarEventSnapshot(
                event_id="evt-193p",
                summary="Customer demo meeting deadline review",
                start="2026-06-29T16:00:00Z",
                end="2026-06-29T16:30:00Z",
                all_day=False,
                location=None,
                description_preview="Review proposal deadline and follow-up.",
                organizer_email="client@example.com",
                attendee_count=4,
                html_link=None,
                source="google_calendar_readonly",
            ),
        ),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def gmail_scan() -> GmailReadonlyContextScanRecord:
    return GmailReadonlyContextScanRecord(
        stage="163P",
        status="completed_with_signals",
        query="newer_than:30d",
        messages=(),
        signals=(
            GmailContextSignal(
                signal_id="sig-193p",
                message_id="msg-193p",
                thread_id="thread-193p",
                signal_type="follow_up",
                summary="Client asked for proposal review before the meeting.",
                confidence="high",
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


def memory_item() -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id="mem-193p",
        owner_id="owner-193p",
        robot_id="robot-193p",
        memory_kind="preference",
        status="approved",
        scopes=("meeting_prep",),
        sensitivity="normal",
        allowed_uses=("context",),
        skill_ids=(),
        content="Prefer concise meeting prep with risks first.",
        bounded_summary="Prefer concise meeting prep with risks first.",
        source="owner_approved",
        is_preference=True,
    )


def document_review():
    return build_document_review_pack_record(
        owner_id="owner-193p",
        robot_id="robot-193p",
        document_title="Pilot proposal contract",
        extracted_text="Payment deadline and review terms must be checked before approval.",
    )
