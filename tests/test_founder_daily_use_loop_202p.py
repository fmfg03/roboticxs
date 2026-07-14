from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.founder_daily_use_loop import (
    FOUNDER_DAILY_USE_LOOP_STAGE,
    FOUNDER_DAILY_USE_LOOP_STATUS,
    build_founder_daily_use_loop,
    render_founder_daily_use_loop,
)
from app.runnable_telegram_robot_mvp import TelegramRobotConfig, render_command_reply


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FOUNDER_DAILY_USE_LOOP_202P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_202p_empty_founder_loop_uses_explicit_fallbacks():
    loop = build_founder_daily_use_loop(owner_id="owner-202p", robot_id="robot-202p")

    assert loop.stage == FOUNDER_DAILY_USE_LOOP_STAGE
    assert loop.status == FOUNDER_DAILY_USE_LOOP_STATUS
    assert "No live daily brief injected" in loop.today_overview
    assert "No meeting prep injected" in loop.next_prep
    assert loop.pending_suggestions == 0
    assert loop.pending_approvals == 0
    assert loop.pending_drafts == 0
    assert loop.pending_memory_reviews == 0
    assert "local estimated ledger boundary" in loop.usage_cost_snapshot
    assert "Source trace not injected" in loop.source_trace_summary
    assert loop.recommended_next_action == "Run /daily_brief, then /prep, then /usage to start the founder daily routine."


def test_202p_partial_founder_loop_prioritizes_approval_and_preserves_boundaries():
    loop = build_founder_daily_use_loop(
        owner_id="owner-202p",
        robot_id="robot-202p",
        today_overview="Two meetings today; one needs prep.",
        next_prep="Prep 10:00 investor check-in.",
        pending_suggestions=2,
        pending_approvals=1,
        pending_drafts=3,
        pending_memory_reviews=1,
        usage_cost_snapshot="$0.004 estimated local usage this month.",
        setup_warnings=("Gmail read-only connected; Calendar write disabled.",),
        source_trace_summary="Calendar, Gmail, Memory used; Documents unavailable.",
    )

    assert loop.recommended_next_action == "Review /approvals before materializing any output."
    assert loop.gmail_send_allowed is False
    assert loop.gmail_modify_allowed is False
    assert loop.calendar_write_allowed is False
    assert loop.crm_write_allowed is False
    assert loop.whatsapp_allowed is False
    assert loop.external_write_allowed is False
    assert loop.autonomous_background_actions_allowed is False
    assert loop.billing_allowed is False
    assert loop.secrets_redacted is True
    assert loop.approval_gate_preserved is True


def test_202p_rich_founder_loop_renders_daily_operating_card():
    rendered = render_founder_daily_use_loop(
        build_founder_daily_use_loop(
            owner_id="owner-202p",
            robot_id="robot-202p",
            today_overview="Daily brief has Calendar, Gmail, and approved Memory context.",
            next_prep="Prepare 11:30 customer pilot review.",
            pending_suggestions=1,
            pending_approvals=0,
            pending_drafts=1,
            pending_memory_reviews=2,
            usage_cost_snapshot="Balanced mode estimate: $0.006 local only.",
            setup_warnings=("Calendar read-only connected.", "Gmail send disabled."),
            source_trace_summary="Source trace available for daily brief, prep, and pilot.",
        )
    )

    assert "Founder Daily Loop" in rendered
    assert "Stage: 202P" in rendered
    assert "Today overview:" in rendered
    assert "Next useful prep:" in rendered
    assert "- Pending suggestions: 1" in rendered
    assert "- Pending approvals: 0" in rendered
    assert "- Pending drafts: 1" in rendered
    assert "- Pending memory reviews: 2" in rendered
    assert "Usage/cost:" in rendered
    assert "Setup warnings:" in rendered
    assert "Source trace:" in rendered
    assert "Recommended next action:" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "CRM writes: disabled" in rendered
    assert "WhatsApp: disabled" in rendered
    assert "Autonomous background actions: disabled" in rendered


def test_202p_telegram_founder_loop_command_is_customer_visible_without_external_writes():
    loop = build_founder_daily_use_loop(owner_id="local-owner", robot_id="roboticxs-dev")

    rendered = render_command_reply(
        command="/founder_loop",
        config=TelegramRobotConfig(
            bot_token="token-202p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        ),
        founder_daily_use_loop=loop,
    )

    assert "Founder Daily Loop" in rendered
    assert "Stage: 202P" in rendered
    assert "External writes: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_202p_rejects_authority_expansion_or_invalid_counts():
    loop = build_founder_daily_use_loop(owner_id="owner-202p", robot_id="robot-202p")

    with pytest.raises(ValueError, match="must not expand external action"):
        replace(loop, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="counts must be non-negative"):
        replace(loop, pending_suggestions=-1)
    with pytest.raises(ValueError, match="must remain local"):
        replace(loop, local_loop_only=False)


def test_202p_reference_and_roadmap_close_founder_loop_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "202P adds a repeatable founder morning routine" in reference
    assert "does not authorize Gmail send" in reference
    assert "autonomous background actions" in reference
    assert '"stage_id":"202P","stage_name":"Founder Daily Use Loop v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
