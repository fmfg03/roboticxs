from __future__ import annotations

from pathlib import Path

from app.open_loops_command import OpenLoopsCommandRecord
from app.personal_admin_inbox import build_personal_admin_inbox_record
from app.personal_admin_inbox import render_personal_admin_inbox
from app.runnable_telegram_robot_mvp import (
    render_start_command_reply,
    render_status_command_reply,
)
from app.setup_capability_status_component import (
    PRODUCT_APPROVAL_BOUNDARY_LINES,
    SETUP_COMPACT_LINES,
    SETUP_NEEDS_SETUP_LINES,
    SETUP_UNAVAILABLE_LINES,
    render_compact_setup_capability_block,
    render_setup_capability_status_sections,
)
from app.telegram_demo_loop import build_telegram_demo_loop_transcript
from tests.test_telegram_product_shell_150p import valid_config


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SETUP_CAPABILITY_STATUS_COMPONENT_161P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_161p_full_status_block_is_shared_by_status_reply():
    reply = render_status_command_reply(valid_config())
    full_block = "\n".join(render_setup_capability_status_sections())

    assert full_block in reply
    for line in SETUP_NEEDS_SETUP_LINES:
        assert line in reply
    for line in SETUP_UNAVAILABLE_LINES:
        assert line in reply
    for line in PRODUCT_APPROVAL_BOUNDARY_LINES:
        assert line in reply


def test_161p_compact_setup_block_is_shared_by_primary_product_surfaces():
    transcript = build_telegram_demo_loop_transcript()
    start_reply = render_start_command_reply(valid_config())
    today_reply = next(step.reply_text for step in transcript.steps if step.command == "/today")
    prep_reply = next(step.reply_text for step in transcript.steps if step.command.startswith("/prep"))

    compact_block = "\n".join(render_compact_setup_capability_block())
    assert compact_block in start_reply
    assert compact_block in today_reply
    assert compact_block in prep_reply
    for line in SETUP_COMPACT_LINES:
        assert line in start_reply
        assert line in today_reply
        assert line in prep_reply


def test_161p_inbox_list_surface_uses_compact_setup_block():
    open_loops = OpenLoopsCommandRecord(
        stage="142P",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        status="completed",
        calendar_status="blocked_calendar_unavailable",
        memory_status="empty",
        suggestion_status="blocked_calendar_unavailable",
        pending_memory_lines=("No pending memory proposals are visible right now.",),
        meeting_suggestion_lines=("No owner-requestable meeting suggestions are available right now.",),
        calendar_lines=("Read-only Calendar context unavailable.",),
        next_steps=("No urgent local prep action was found.",),
        read_only=True,
        calendar_write_allowed=False,
        memory_write_allowed=False,
        proposed_memory_written=False,
        followup_intent_created=False,
        reminder_scheduled=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        proactive_send_allowed=False,
    )
    rendered = render_personal_admin_inbox(
        build_personal_admin_inbox_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            open_loops_record=open_loops,
        )
    )

    assert "\n".join(render_compact_setup_capability_block()) in rendered


def test_161p_reference_and_roadmap_close_component_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "161P is a local shared-copy component only." in reference
    assert "does not add commands" in reference
    assert "Memory Center mutation" in reference
    assert '"stage_id":"161P","stage_name":"Setup Capability Status Component v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "200P and later remain unauthorized" in roadmap
