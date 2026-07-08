from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.pilot_safety_incident_log import (
    build_pilot_safety_incident,
    build_pilot_safety_incident_log,
    render_pilot_safety_incident_log,
)
from app.runnable_telegram_robot_mvp import TelegramIncomingCommand, TelegramRobotConfig, handle_incoming_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PILOT_SAFETY_INCIDENT_LOG_219P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None) -> dict:
        payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id}
        self.sent_messages.append(payload)
        return {"ok": True, "result": payload}


def _config() -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="token-219p",
        owner_ids=frozenset({111111111}),
        robot_id="roboticxs-dev",
        owner_id="local-owner",
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=False,
        dev_mode=True,
    )


def safety_incident(**overrides):
    values = {
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "pilot_user_id": "111111111",
        "incident_type": "attempted_gmail_send",
        "command": "/export_email",
        "item_id": "draft-1",
        "reason": "Gmail send is prohibited",
        "severity": "high",
    }
    values.update(overrides)
    return build_pilot_safety_incident(**values)


def test_219p_builds_safety_incident_log():
    incident = safety_incident()
    log = build_pilot_safety_incident_log(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        incidents=(incident,),
    )

    assert log.stage == "219P"
    assert log.status == "local_pilot_safety_log_v0"
    assert log.total_incidents == 1
    assert log.blocked_incidents == 1
    assert log.top_incident_types == (("attempted_gmail_send", 1),)
    assert log.local_log_only is True
    assert log.external_ticket_created is False
    assert log.gmail_send_allowed is False
    assert log.calendar_write_allowed is False
    assert log.approval_gate_preserved is True


def test_219p_filters_incidents_by_owner_and_robot_and_redacts_reason():
    local = safety_incident(reason="bearer token appeared")
    cross_owner = safety_incident(owner_id="other-owner", item_id="draft-2")

    log = build_pilot_safety_incident_log(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        incidents=(local, cross_owner),
    )

    assert log.total_incidents == 1
    assert log.incidents[0].item_id == "draft-1"
    assert "[redacted]" in log.incidents[0].reason
    assert "token" not in log.incidents[0].reason


def test_219p_renders_incidents_and_no_incident_fallback():
    rendered = render_pilot_safety_incident_log(
        build_pilot_safety_incident_log(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            incidents=(safety_incident(incident_type="missing_consent", command="/pilot", item_id="pilot-1"),),
        )
    )
    empty = render_pilot_safety_incident_log(
        build_pilot_safety_incident_log(owner_id="local-owner", robot_id="roboticxs-dev")
    )

    assert "Pilot Safety Incident Log" in rendered
    assert "Type: missing_consent" in rendered
    assert "Health: needs_operator_review" in rendered
    assert "External ticket: no" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Health: no_local_incidents" in empty


def test_219p_rejects_external_authority():
    log = build_pilot_safety_incident_log(owner_id="local-owner", robot_id="roboticxs-dev")

    with pytest.raises(ValueError, match="external authority"):
        replace(log, external_ticket_created=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(log, crm_write_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(log, gmail_send_allowed=True)
    with pytest.raises(ValueError, match="external authority"):
        replace(log, calendar_write_allowed=True)


def test_219p_telegram_pilot_safety_command_is_visible():
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=TelegramIncomingCommand(
            update_id=219,
            chat_id=222,
            telegram_user_id=111111111,
            message_id=333,
            raw_text="/pilot_safety",
            command="/pilot_safety",
        ),
        client=client,
        config=_config(),
        pilot_safety_incidents=(safety_incident(),),
    )

    assert "Pilot Safety Incident Log" in receipt.reply_text
    assert "Incidents: 1" in receipt.reply_text
    assert "attempted_gmail_send" in receipt.reply_text
    assert "Local log only: yes" in receipt.reply_text
    assert len(client.sent_messages) == 1


def test_219p_reference_and_roadmap_close_safety_log_without_external_tickets():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "219P adds `/pilot_safety`" in reference
    assert "attempted Gmail send" in reference
    assert '"stage_id":"219P","stage_name":"Pilot Safety Incident Log v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "222P and later remain unauthorized" in roadmap
