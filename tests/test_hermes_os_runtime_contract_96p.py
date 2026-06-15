from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.hermes_os_contract import (
    GoalPacket,
    HERMES_OS_STAGE,
    PolicyTrace,
    build_hermes_os_runtime_contract,
)
from app.models import MemoryItem, Robot, User
from app.telegram_policy_chain import run_telegram_policy_chain


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/hermes_os_contract.py"
DOC_PATH = REPO_ROOT / "docs/reference/HERMES_OS_RUNTIME_CONTRACT_96P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_update(text: str, user_id: int = 96001, chat_id: int = 96001) -> dict:
    return {
        "update_id": 96001,
        "message": {
            "message_id": 960,
            "date": 1710000000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Hermes",
                "username": "hermes",
            },
            "text": text,
        },
    }


def run_chain_in_session(session, text: str, user_id: int = 96001):
    return run_telegram_policy_chain(
        update=build_update(text, user_id=user_id, chat_id=user_id),
        settings=Settings(),
        session=session,
    )


@pytest.mark.anyio
async def test_safe_policy_chain_result_builds_complete_os_contract(client):
    with client.app.state.db.session() as session:
        result = run_chain_in_session(session, "Draft a short local summary")
        contract = build_hermes_os_runtime_contract(policy_result=result)

    assert contract.stage == HERMES_OS_STAGE
    assert contract.robot_constitution.packet_type == "RobotConstitution"
    assert contract.robot_constitution.runtime_role == "persistent_runtime_substrate"
    assert contract.robot_constitution.hermes_is_authority is False
    assert contract.policy_trace.complete is True
    assert [decision.policy for decision in contract.policy_trace.decisions] == [
        "command_surface_policy_90p",
        "skill_scope_policy_91p",
        "tool_authority_policy_92p",
    ]
    assert contract.goal_packet.packet_type == "GoalPacket"
    assert contract.goal_packet.blocked is False
    assert contract.skill_activation_packet.packet_type == "SkillActivationPacket"
    assert contract.skill_activation_packet.manifest_authority == "Roboticxs SkillManifest"
    assert contract.skill_activation_packet.hermes_activation_grants_permission is False
    assert contract.tool_request_packet.packet_type == "ToolRequestPacket"
    assert contract.tool_request_packet.reaches_hermes_adapter is True
    assert contract.task_run_record.status == "LOCAL_HERMES_OS_STUB_COMPLETED"
    assert contract.live_hermes_start_authorized is False
    assert contract.live_cron_authorized is False
    assert contract.live_telegram_send_authorized is False
    assert contract.connector_activation_authorized is False
    assert contract.external_side_effect_authorized is False


@pytest.mark.anyio
async def test_external_tool_request_requires_action_packet_and_stops_before_hermes_adapter(client):
    with client.app.state.db.session() as session:
        result = run_chain_in_session(session, "Send email to Ana with this summary")
        contract = build_hermes_os_runtime_contract(policy_result=result)

    assert result.action_packet is not None
    assert contract.tool_request_packet.decision == "ASK_CONFIRMATION"
    assert contract.tool_request_packet.requires_action_packet is True
    assert contract.tool_request_packet.reaches_hermes_adapter is False
    assert contract.action_packet_binding.packet_type == "ActionPacket"
    assert contract.action_packet_binding.required is True
    assert contract.action_packet_binding.bound is True
    assert contract.action_packet_binding.external_effect_authorized is False
    assert contract.task_run_record.status == "WAITING_FOR_ACTION_PACKET_CONFIRMATION"


@pytest.mark.anyio
async def test_blocked_raw_hermes_command_cannot_bypass_95p_entrypoint(client):
    with client.app.state.db.session() as session:
        result = run_chain_in_session(session, "/gateway start")
        contract = build_hermes_os_runtime_contract(policy_result=result)

    assert result.command_policy.decision == "BLOCK_CONSUMER"
    assert contract.policy_trace.entrypoint == "/api/telegram/policy-chain/webhook"
    assert contract.policy_trace.complete is False
    assert contract.tool_request_packet.reaches_hermes_adapter is False
    assert contract.task_run_record.status == "STOPPED_BEFORE_HERMES"
    assert contract.task_run_record.live_hermes_started is False
    assert contract.task_run_record.network_call is False


def test_goal_packet_rejects_blocked_tool_requests_without_policy_block():
    trace = PolicyTrace(
        packet_type="PolicyTrace",
        stage=HERMES_OS_STAGE,
        complete=False,
        decisions=(),
        entrypoint="/api/telegram/policy-chain/webhook",
        downstream_authority_required=("tool_authority_policy",),
    )

    with pytest.raises(ValueError, match="blocked tools"):
        GoalPacket(
            packet_type="GoalPacket",
            stage=HERMES_OS_STAGE,
            goal_id="goal_test",
            robot_id="robot_test",
            user_intent="pay invoice",
            requested_tool_classes=("PAY",),
            policy_trace=trace,
            blocked=False,
            blocked_reason=None,
        )


@pytest.mark.anyio
async def test_routine_packet_has_wake_and_budget_placeholders_without_live_cron(client):
    with client.app.state.db.session() as session:
        result = run_chain_in_session(session, "/cron daily brief")
        contract = build_hermes_os_runtime_contract(policy_result=result, routine_requested=True)

    assert contract.routine_packet.packet_type == "RoutinePacket"
    assert contract.routine_packet.wake_preflight_required is True
    assert contract.routine_packet.budget_preflight_required is True
    assert contract.routine_packet.live_cron_authorized is False
    assert contract.routine_packet.model_router_allowed_before_budget is False
    assert contract.routine_packet.delivery_authorized is False


@pytest.mark.anyio
async def test_memory_projection_packet_is_bounded_scoped_and_non_authority(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=96111, first_name="Memory", username="memory")
        session.add(user)
        session.flush()
        robot = Robot(user_id=user.id, name="Memory Robot")
        session.add(robot)
        session.flush()
        session.add(
            MemoryItem(
                user_id=user.id,
                robot_id=robot.id,
                memory_type="BOUNDARY_MEMORY",
                content="Requires confirmation before external sends.",
                display_label="Boundary",
                source="telegram_text",
                status="ACTIVE",
            )
        )
        session.flush()
        result = run_chain_in_session(session, "Draft a local note", user_id=96111)
        contract = build_hermes_os_runtime_contract(policy_result=result)

    assert contract.memory_projection_packet.packet_type == "MemoryProjectionPacket"
    assert contract.memory_projection_packet.source_of_truth == "Roboticxs Memory Center"
    assert contract.memory_projection_packet.runtime_target == "Hermes OS context"
    assert contract.memory_projection_packet.projection_count == 1
    assert contract.memory_projection_packet.bounded is True
    assert contract.memory_projection_packet.scoped is True
    assert contract.memory_projection_packet.tool_action_authorization is False
    assert contract.memory_projection_packet.permission_expansion_authorized is False


def test_hermes_os_contract_module_has_no_network_or_external_execution_imports():
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


def test_96p_reference_doc_and_roadmap_register_contract_stage():
    doc = DOC_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "Status: 96P implemented pending review." in doc
    for packet_name in [
        "RobotConstitution",
        "GoalPacket",
        "RoutinePacket",
        "SkillActivationPacket",
        "MemoryProjectionPacket",
        "ToolRequestPacket",
        "ActionPacket",
        "PolicyTrace",
        "TaskRunRecord",
    ]:
        assert packet_name in doc
    assert "Hermes is runtime substrate, not authority layer." in doc
    assert "no live Hermes startup" in doc
    assert "no caregiver workflows" in doc
    assert '"stage_id":"96P","stage_name":"Hermes OS Runtime Contract v0","status":"IMPLEMENTED_PENDING_REVIEW"' in roadmap
