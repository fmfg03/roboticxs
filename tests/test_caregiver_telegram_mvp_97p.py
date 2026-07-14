from __future__ import annotations

from pathlib import Path

import pytest

from app.caregiver_telegram_mvp import (
    CAREGIVER_TELEGRAM_MVP_STAGE,
    CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH,
    run_caregiver_telegram_mvp,
)
from app.config import Settings
from app.models import MemoryItem, Robot, User


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/caregiver_telegram_mvp.py"
DOC_PATH = REPO_ROOT / "docs/reference/CAREGIVER_TELEGRAM_MVP_97P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_update(text: str, user_id: int = 97001, chat_id: int = 97001) -> dict:
    return {
        "update_id": 97001,
        "message": {
            "message_id": 970,
            "date": 1710000000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Care",
                "username": "care",
            },
            "text": text,
        },
    }


def run_slice(session, text: str, user_id: int = 97001):
    return run_caregiver_telegram_mvp(
        update=build_update(text, user_id=user_id, chat_id=user_id),
        settings=Settings(),
        session=session,
    )


@pytest.mark.anyio
async def test_guided_routine_happy_path_uses_policy_chain_and_96p_contract(client):
    response = await client.post(CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH, json=build_update("Start the hearing aid routine"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["stage"] == CAREGIVER_TELEGRAM_MVP_STAGE
    assert body["packet"]["packet_type"] == "CaregiverRoutinePacket"
    assert body["packet"]["decision"] == "GUIDE_STEP"
    assert body["packet"]["current_step"]["instruction"] == "Please find your hearing aids."
    assert set(body["packet"]["actors"]) == {"care_recipient", "caregiver", "owner_admin", "robot"}
    assert body["policy_trace"] == [
        "command_surface_policy_90p",
        "skill_scope_policy_91p",
        "tool_authority_policy_92p",
    ]
    assert body["policy_trace_complete"] is True
    assert body["task_run_record"]["packet_type"] == "TaskRunRecord"
    assert body["task_run_record"]["stage"] == "96P"
    assert body["local_response"]["telegram_send"] is False
    assert body["local_response"]["live_hermes_gateway_started"] is False
    assert body["local_response"]["live_cron_scheduled"] is False
    assert body["local_response"]["connector_activation"] is False


@pytest.mark.anyio
async def test_confused_repeated_step_returns_safe_repeat_and_local_escalation_draft(client):
    response = await client.post(CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH, json=build_update("I am confused, repeat the step"))
    body = response.json()

    assert body["packet"]["decision"] == "SAFE_REPEAT"
    assert "repeat one safe step" in body["packet"]["response_text"]
    assert body["packet"]["escalation_requires_approval"] is True
    assert body["packet"]["escalation_draft"].startswith("Draft for approved caregiver:")
    assert body["action_packet"]["action_class"] == "SEND_EXTERNAL_MESSAGE"
    assert body["action_packet"]["external_effect_authorized"] is False
    assert body["local_response"]["automatic_caregiver_send"] is False


@pytest.mark.anyio
async def test_medication_change_refusal_does_not_reach_hermes_adapter(client):
    response = await client.post(
        CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH,
        json=build_update("Change her medication dose tonight"),
    )
    body = response.json()

    assert body["ok"] is False
    assert body["error_code"] == "caregiver_medical_decision_refused"
    assert body["packet"]["decision"] == "REFUSE_MEDICAL_DECISION"
    assert body["packet"]["medical_decision_authorized"] is False
    assert body["packet"]["medication_change_authorized"] is False
    assert body["local_response"]["hermes_adapter_called"] is False


@pytest.mark.anyio
async def test_medical_decision_refusal_blocks_before_adapter(client):
    response = await client.post(
        CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH,
        json=build_update("Which pill should she take for treatment?"),
    )
    body = response.json()

    assert body["error_code"] == "caregiver_medical_decision_refused"
    assert "cannot make medical decisions" in body["packet"]["response_text"]
    assert body["task_run_record"]["hermes_adapter_called"] is False


@pytest.mark.anyio
async def test_emergency_escalation_safe_copy_is_approval_required_and_not_monitoring(client):
    response = await client.post(
        CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH,
        json=build_update("She fell and cannot get up"),
    )
    body = response.json()

    assert body["packet"]["decision"] == "ESCALATION_DRAFT_REQUIRED"
    assert "local emergency services or a medical professional" in body["packet"]["response_text"]
    assert "Roboticxs is not emergency monitoring" in body["packet"]["escalation_draft"]
    assert body["packet"]["emergency_monitoring_claim_authorized"] is False
    assert body["packet"]["automatic_caregiver_send_authorized"] is False
    assert body["action_packet"]["decision"] == "ASK_CONFIRMATION"
    assert body["local_response"]["telegram_send"] is False


@pytest.mark.anyio
async def test_consent_actor_isolation_and_sensitive_memory_redaction(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=97111, first_name="Recipient", username="recipient")
        owner = User(telegram_user_id=97112, first_name="Owner", username="owner")
        session.add_all([user, owner])
        session.flush()
        robot = Robot(user_id=user.id, name="Recipient Robot")
        owner_robot = Robot(user_id=owner.id, name="Owner Robot")
        session.add_all([robot, owner_robot])
        session.flush()
        session.add_all(
            [
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Use only approved caregiver routine labels.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="MEDICAL_DECISION",
                    content="Sensitive medical decision must not project.",
                    display_label="Medical",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=owner.id,
                    robot_id=owner_robot.id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Owner private unrelated memory.",
                    display_label="Owner",
                    source="telegram_text",
                    status="ACTIVE",
                ),
            ]
        )
        session.flush()
        result = run_slice(session, "Start the routine", user_id=97111)

    assert result.packet.actors.care_recipient.telegram_user_id == 97111
    assert result.packet.actors.caregiver.telegram_user_id is None
    assert [projection.memory_type for projection in result.bounded_memory_projection] == ["BOUNDARY_MEMORY"]
    assert all("Owner private" not in projection.content for projection in result.bounded_memory_projection)
    assert result.packet.sensitive_memory_expansion_authorized is False


@pytest.mark.anyio
async def test_simple_confirmation_stays_local(client):
    response = await client.post(CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH, json=build_update("done"))
    body = response.json()

    assert body["packet"]["decision"] == "CONFIRM_STEP"
    assert "local confirmation only" in body["packet"]["response_text"]
    assert body["local_response"]["external_side_effect"] is False


def test_caregiver_mvp_module_has_no_network_or_external_execution_imports():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "api.telegram.org",
        "setWebhook",
        "uvicorn.run",
        "smtp",
        "stripe",
    ]:
        assert forbidden not in text


def test_97p_reference_doc_and_roadmap_close_stage_without_98p_authorization():
    doc = DOC_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "Status: 97P closed committed." in doc
    assert "CaregiverRoutinePacket" in doc
    assert "no live Telegram sends" in doc
    assert "no automatic caregiver sends" in doc
    assert "no medical decisions" in doc
    assert '"stage_id":"97P","stage_name":"Caregiver Telegram MVP v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_98p_and_later_authorized":false' in roadmap
    assert '"status":"NEXT_ELIGIBLE"' not in roadmap
