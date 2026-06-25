from __future__ import annotations

from pathlib import Path

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.meeting_prep_pack import build_meeting_prep_pack, render_meeting_prep_pack
from app.memory_center_projection import MemoryCenterItem
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event() -> CalendarEventSnapshot:
    return CalendarEventSnapshot(
        event_id="evt-151p-client-demo",
        summary="Client demo prep meeting",
        start="2026-06-25T10:00:00-06:00",
        end="2026-06-25T10:30:00-06:00",
        all_day=False,
        location="Google Meet",
        description_preview="Review proposal context and prepare open questions.",
        organizer_email="owner@example.com",
        attendee_count=3,
        html_link="https://calendar.google.com/event?eid=151p",
        source="google_calendar_readonly",
    )


def suggestion_scan():
    result = CalendarReadResult(
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
    return build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=build_calendar_context_scan_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            calendar_result=result,
        ),
    )


def memory_item() -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id="mem-151p-prep",
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
    )


def memory_snapshot(*, include_memory: bool = True):
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(memory_item(),) if include_memory else (),
        ),
    )


def test_151p_meeting_prep_pack_renders_customer_value_sections():
    scan = suggestion_scan()
    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )

    rendered = render_meeting_prep_pack(record)

    assert "Meeting Prep Pack" in rendered
    assert "Meeting context:" in rendered
    assert "Agenda:" in rendered
    assert "Known memory:" in rendered
    assert "Open loops:" in rendered
    assert "Missing inputs:" in rendered
    assert "Suggested actions:" in rendered
    assert "Safe next step:" in rendered
    assert "Boundaries:" in rendered
    assert "Client demo prep meeting" in rendered
    assert "Francisco prefers compact meeting prep." in rendered
    assert "List open questions to resolve during the meeting." in rendered
    assert "No missing inputs detected in the local prep context." in rendered
    assert "Review this prep pack and take any external action yourself" in rendered


def test_151p_missing_memory_is_listed_as_missing_input_not_fact():
    scan = suggestion_scan()
    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(include_memory=False),
    )

    assert "No approved Memory Center context is visible for this prep pack." in record.memory_context_lines
    assert "Approved Memory Center context for this meeting." in record.missing_input_lines


def test_151p_unknown_suggestion_fails_closed_with_safe_next_step():
    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="missing-suggestion",
        suggestion_scan=suggestion_scan(),
        memory_snapshot=memory_snapshot(),
    )

    rendered = render_meeting_prep_pack(record)

    assert record.status == "blocked_suggestion_not_found"
    assert record.suggestion_validated is False
    assert "Current meeting suggestion id." in record.missing_input_lines
    assert record.safe_next_step == "Run /suggest_brief to get current meeting suggestions."
    assert "No external action was taken." in rendered


def test_151p_meeting_prep_pack_preserves_no_authority_boundaries():
    scan = suggestion_scan()
    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )

    assert record.calendar_write_allowed is False
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.followup_intent_created is False
    assert record.scheduler_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.proactive_send_allowed is False


def test_151p_roadmap_records_meeting_prep_product_flow_and_blocks_152p_plus():
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")

    assert '"stage_id":"151P","stage_name":"Meeting Prep Pack Product Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "171P and later remain unauthorized" in roadmap
