from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.customer_pilot_readiness_pack import (
    CUSTOMER_PILOT_READINESS_PACK_STAGE,
    CUSTOMER_PILOT_READINESS_PACK_STATUS,
    build_customer_pilot_readiness_pack,
    render_customer_pilot_readiness_pack,
)
from app.runnable_telegram_robot_mvp import (
    TelegramRobotConfig,
    render_command_reply,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CUSTOMER_PILOT_READINESS_PACK_199P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_199p_builds_complete_local_customer_pilot_pack():
    pack = build_customer_pilot_readiness_pack(owner_id="owner-199p", robot_id="robot-199p")

    assert pack.stage == CUSTOMER_PILOT_READINESS_PACK_STAGE
    assert pack.status == CUSTOMER_PILOT_READINESS_PACK_STATUS
    assert pack.target_pilot_users == "1-3"
    assert "/pilot" in pack.supported_commands
    assert "/pilot_pack" in pack.supported_commands
    assert any("Gmail send" in item for item in pack.blocked_actions)
    assert any("Calendar create" in item for item in pack.blocked_actions)
    assert pack.local_pack_only is True
    assert pack.external_write_allowed is False
    assert pack.gmail_send_allowed is False
    assert pack.gmail_modify_allowed is False
    assert pack.calendar_write_allowed is False
    assert pack.crm_write_allowed is False
    assert pack.whatsapp_allowed is False
    assert pack.secrets_redacted is True
    assert pack.approval_gate_preserved is True


def test_199p_rendered_pack_contains_operator_ready_sections_and_safety_receipts():
    rendered = render_customer_pilot_readiness_pack(
        build_customer_pilot_readiness_pack(owner_id="owner-199p", robot_id="robot-199p")
    )

    assert "Customer Pilot Readiness Pack" in rendered
    assert "Stage: 199P" in rendered
    assert "Setup checklist:" in rendered
    assert "Supported commands:" in rendered
    assert "Blocked actions:" in rendered
    assert "Demo script:" in rendered
    assert "Failure modes:" in rendered
    assert "Source trace examples:" in rendered
    assert "Usage report:" in rendered
    assert "Safety receipts:" in rendered
    assert "Onboarding copy:" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "CRM writes: disabled" in rendered
    assert "WhatsApp: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_199p_telegram_pilot_pack_command_is_customer_visible_without_external_writes():
    pack = build_customer_pilot_readiness_pack(owner_id="local-owner", robot_id="roboticxs-dev")

    rendered = render_command_reply(
        command="/pilot_pack",
        config=TelegramRobotConfig(
            bot_token="token-199p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        ),
        customer_pilot_readiness_pack=pack,
    )

    assert "Customer Pilot Readiness Pack" in rendered
    assert "/pilot_pack" in rendered
    assert "External writes: disabled" in rendered
    assert "Secrets: redacted" in rendered


def test_199p_rejects_authority_expansion_and_incomplete_pack():
    pack = build_customer_pilot_readiness_pack(owner_id="owner-199p", robot_id="robot-199p")

    with pytest.raises(ValueError, match="must not expand external action authority"):
        replace(pack, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="must stay controlled"):
        replace(pack, target_pilot_users="10")
    with pytest.raises(ValueError, match="require every pilot section"):
        replace(pack, safety_receipts=())


def test_199p_reference_and_roadmap_close_customer_pilot_pack_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "199P adds a local customer-pilot pack" in reference
    assert "does not authorize Gmail send" in reference
    assert "Secrets must remain redacted" in reference
    assert '"stage_id":"199P","stage_name":"Customer Pilot Readiness Pack v0","status":"CLOSED_COMMITTED"' in roadmap
