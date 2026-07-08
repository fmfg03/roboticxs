from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.live_smoke_script import (
    LIVE_SMOKE_SCRIPT_STAGE,
    LIVE_SMOKE_SCRIPT_STATUS,
    LiveSmokeScript,
    build_live_smoke_script,
    render_live_smoke_script,
)
from app.runnable_telegram_robot_mvp import TelegramRobotConfig, render_command_reply


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/LIVE_SMOKE_SCRIPT_201P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_201p_builds_manual_live_smoke_script_for_full_pilot_loop():
    script = build_live_smoke_script(owner_id="owner-201p", robot_id="robot-201p")

    assert script.stage == LIVE_SMOKE_SCRIPT_STAGE
    assert script.status == LIVE_SMOKE_SCRIPT_STATUS
    assert [step.command for step in script.smoke_steps] == [
        "/start",
        "/pilot_pack",
        "/pilot_audit",
        "/daily_brief",
        "/prep",
        "/suggestions",
        "/drafts",
        "/usage",
        "/pilot",
        "/pilot_pack",
    ]
    assert any("real Calendar/Gmail/Memory sources" in item for item in script.operator_prerequisites)
    assert any("Missing source trace" in item for item in script.stop_conditions)
    assert "real source context or explicit fallback" in script.pass_condition
    assert script.local_script_only is True
    assert script.telegram_owner_gate_required is True
    assert script.real_sources_or_fallback_required is True
    assert script.gmail_send_allowed is False
    assert script.gmail_modify_allowed is False
    assert script.calendar_write_allowed is False
    assert script.crm_write_allowed is False
    assert script.whatsapp_allowed is False
    assert script.external_write_allowed is False
    assert script.secrets_redacted is True
    assert script.approval_gate_preserved is True


def test_201p_rendered_script_is_operator_usable_and_boundary_clear():
    rendered = render_live_smoke_script(build_live_smoke_script(owner_id="owner-201p", robot_id="robot-201p"))

    assert "Live Smoke Script" in rendered
    assert "Stage: 201P" in rendered
    assert "Operator prerequisites:" in rendered
    assert "Smoke steps:" in rendered
    assert "/pilot_pack [pilot_pack]" in rendered
    assert "/pilot_audit [pilot_audit]" in rendered
    assert "Expected:" in rendered
    assert "Fallback:" in rendered
    assert "Stop conditions:" in rendered
    assert "Pass condition:" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "CRM writes: disabled" in rendered
    assert "WhatsApp: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_201p_telegram_live_smoke_command_is_customer_visible_without_external_writes():
    script = build_live_smoke_script(owner_id="local-owner", robot_id="roboticxs-dev")

    rendered = render_command_reply(
        command="/live_smoke",
        config=TelegramRobotConfig(
            bot_token="token-201p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        ),
        live_smoke_script=script,
    )

    assert "Live Smoke Script" in rendered
    assert "Stage: 201P" in rendered
    assert "External writes: disabled" in rendered
    assert "Secrets: redacted" in rendered


def test_201p_rejects_incomplete_script_or_authority_expansion():
    script = build_live_smoke_script(owner_id="owner-201p", robot_id="robot-201p")

    with pytest.raises(ValueError, match="complete pilot loop"):
        replace(script, smoke_steps=script.smoke_steps[:3])
    with pytest.raises(ValueError, match="must not expand external action authority"):
        replace(script, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="preserve owner"):
        replace(script, telegram_owner_gate_required=False)


def test_201p_reference_and_roadmap_close_live_smoke_script_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "201P adds a manual live smoke script" in reference
    assert "does not authorize automated live smoke execution" in reference
    assert "Gmail send/archive/delete/label/modify" in reference
    assert '"stage_id":"201P","stage_name":"Live Smoke Script v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "221P and later remain unauthorized" in roadmap
