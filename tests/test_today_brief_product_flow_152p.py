from __future__ import annotations

from pathlib import Path

from app.google_calendar_readonly_connector import CalendarReadResult
from app.runnable_telegram_robot_mvp import render_brief_command_reply
from app.today_command import build_today_command_record, render_today_command
from tests.test_runnable_telegram_robot_mvp_130p import build_valid_config
from tests.test_today_command_141p import (
    PendingProposalFixture,
    active_memory,
    event,
    memory_snapshot,
    suggestion_scan,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/TODAY_BRIEF_PRODUCT_FLOW_152P_v0_1.md"


def test_152p_today_renders_customer_daily_view_with_boundaries():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(active_memory(), pending=(PendingProposalFixture(),)),
    )

    rendered = render_today_command(record)

    assert rendered.startswith("Today\n")
    assert "Stage: 141P" not in rendered
    assert "Meetings:" in rendered
    assert "Open loops:" in rendered
    assert "Things waiting for you:" in rendered
    assert "Brief options:" in rendered
    assert "Known memory:" in rendered
    assert "Suggested next action:" in rendered
    assert "Blocked / unavailable sources:" in rendered
    assert "Boundaries:" in rendered
    assert "Client demo prep meeting" in rendered
    assert "Pending memory proposals need owner review before they become facts." in rendered
    assert "1 pending memory proposal(s) need review." in rendered
    assert "No blocked sources detected in this local Today view." in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Memory writes: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Model calls: disabled" in rendered
    assert "Tools: disabled" in rendered
    assert "Worker dispatch: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_152p_today_lists_calendar_unavailable_as_blocked_source():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(ok=False, error_code="missing_access_token"),
        memory_snapshot=memory_snapshot(),
    )

    rendered = render_today_command(record)

    assert "Status: partial_calendar_unavailable" in rendered
    assert "Blocked / unavailable sources:" in rendered
    assert "Calendar read-only source unavailable: missing_access_token." in rendered
    assert "Today continued with local Memory Center visibility only." in rendered
    assert "No external action was taken." in rendered


def test_152p_brief_renders_customer_meeting_view_and_fails_closed():
    reply = render_brief_command_reply(
        build_valid_config(),
        calendar_result=CalendarReadResult(
            ok=False,
            calendar_id="primary",
            window_start="2026-06-24T10:00:00-06:00",
            window_end="2026-07-01T10:00:00-06:00",
            events=(),
            read_only=True,
            external_writes=False,
            memory_mutation=False,
            error_code="missing_access_token",
            error_message="missing_access_token",
        ),
    )

    assert reply.startswith("Meeting Brief\n")
    assert "Source: local meeting context + optional read-only Calendar snapshot" in reply
    assert "Blocked / unavailable sources:" in reply
    assert "Read-only Calendar connector unavailable: missing_access_token." in reply
    assert "Meeting context:" in reply
    assert "Agenda:" in reply
    assert "Watchpoints:" in reply
    assert "Suggested prep:" in reply
    assert "Safe next step:" in reply
    assert "Boundaries:" in reply
    assert "Calendar writes: disabled" in reply
    assert "Memory mutation: disabled" in reply
    assert "Model calls: disabled" in reply
    assert "Tools: disabled" in reply
    assert "Worker dispatch: disabled" in reply
    assert "External writes: disabled" in reply
    assert "LLM/model calls: disabled" not in reply
    assert "No external action was taken." in reply


def test_152p_reference_and_roadmap_close_product_flow_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "152P is a customer-facing Telegram product flow stage." in reference
    assert "does not add new commands" in reference
    assert "mutate Memory Center" in reference
    assert '"stage_id":"152P","stage_name":"Today / Brief Product Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "204P and later remain unauthorized" in roadmap
