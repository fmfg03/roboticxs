from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.meeting_prep_pack import (
    MEETING_PREP_PACK_STAGE,
    MeetingPrepPackRecord,
    build_meeting_prep_pack,
    render_meeting_prep_pack,
)
from app.memory_center_projection import MemoryCenterItem
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/meeting_prep_pack.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def event() -> CalendarEventSnapshot:
    return CalendarEventSnapshot(
        event_id="evt-143p-client-demo",
        summary="Client demo prep meeting",
        start="2026-06-25T10:00:00-06:00",
        end="2026-06-25T10:30:00-06:00",
        all_day=False,
        location="Google Meet",
        description_preview="Review proposal context and prepare open questions.",
        organizer_email="owner@example.com",
        attendee_count=3,
        html_link="https://calendar.google.com/event?eid=143p",
        source="google_calendar_readonly",
    )


def suggestion_scan(*, ok: bool = True, error_code: str | None = None):
    result = CalendarReadResult(
        ok=ok,
        calendar_id="primary",
        window_start="2026-06-24T10:00:00-06:00",
        window_end="2026-07-01T10:00:00-06:00",
        events=(event(),) if ok else (),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=error_code,
        error_message=error_code,
    )
    context_scan = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=result,
    )
    return build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan,
    )


def memory_item() -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id="mem-143p-prep",
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


def memory_snapshot():
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(memory_item(),),
        ),
    )


def test_143p_builds_owner_requested_read_only_meeting_prep_pack():
    scan = suggestion_scan()
    suggestion = scan.suggestions[0]

    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=suggestion.suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )

    assert record.stage == MEETING_PREP_PACK_STAGE
    assert record.status == "completed"
    assert record.source_stages == ("138P", "139P", "136P")
    assert record.owner_requested is True
    assert record.suggestion_validated is True
    assert record.read_only is True
    assert "Client demo prep meeting" in record.meeting_lines[0]
    assert "Review the objective for Client demo prep meeting." in record.agenda_lines
    assert "Francisco prefers compact meeting prep." in record.memory_context_lines[0]
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


def test_143p_unknown_suggestion_fails_closed_without_actions():
    record = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="missing-suggestion",
        suggestion_scan=suggestion_scan(),
        memory_snapshot=memory_snapshot(),
    )

    assert record.status == "blocked_suggestion_not_found"
    assert record.suggestion_validated is False
    assert record.error_code == "suggestion_not_found"
    assert "could not be converted" in record.watchpoints[0]
    assert record.external_write_allowed is False


def test_143p_render_names_disabled_boundaries():
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
    assert "Owner requested: true" in rendered
    assert "Meeting context:" in rendered
    assert "Known memory:" in rendered
    assert "Suggested actions:" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Scheduler/reminders: disabled" in rendered
    assert "Model calls: disabled" in rendered
    assert "Tools/workers: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_143p_record_rejects_authority_expansion():
    scan = suggestion_scan()
    valid = build_meeting_prep_pack(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=scan.suggestions[0].suggestion_id,
        suggestion_scan=scan,
        memory_snapshot=memory_snapshot(),
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        MeetingPrepPackRecord(**{**asdict(valid), "tool_call_allowed": True})


def test_143p_module_declares_no_write_model_tool_worker_or_scheduler_authority():
    text = MODULE_PATH.read_text()

    assert "calendar_write_allowed: bool" in text
    assert "memory_write_allowed: bool" in text
    assert "memory_center_mutated: bool" in text
    assert "proposed_memory_written: bool" in text
    assert "scheduler_allowed: bool" in text
    assert "model_call_allowed: bool" in text
    assert "tool_call_allowed: bool" in text
    assert "worker_dispatch_allowed: bool" in text


def test_143p_roadmap_records_meeting_prep_pack_and_blocks_144p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"143P","stage_name":"Meeting Prep Pack v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "151P later added customer-facing Meeting Prep Pack product flow only" in roadmap
