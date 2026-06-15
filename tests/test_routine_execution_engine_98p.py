from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.models import MemoryItem, Robot, User
from app.routine_execution_engine import (
    ROUTINE_EXECUTION_STAGE,
    RoutineDefinition,
    execute_routine_locally,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/routine_execution_engine.py"
DOC_PATH = REPO_ROOT / "docs/reference/ROUTINE_EXECUTION_ENGINE_98P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_update(text: str, user_id: int = 98001, chat_id: int = 98001) -> dict:
    return {
        "update_id": 98001,
        "message": {
            "message_id": 980,
            "date": 1710000000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Routine",
                "username": "routine",
            },
            "text": text,
        },
    }


def definition(**overrides) -> RoutineDefinition:
    values = {
        "routine_id": "routine_morning",
        "label": "Approved morning routine",
        "trigger_text": "Run the local morning routine",
    }
    values.update(overrides)
    return RoutineDefinition(**values)


def run_routine(session, text: str, routine: RoutineDefinition | None = None, user_id: int = 98001, **kwargs):
    return execute_routine_locally(
        definition=routine or definition(trigger_text=text),
        update=build_update(text, user_id=user_id, chat_id=user_id),
        settings=Settings(),
        session=session,
        **kwargs,
    )


@pytest.mark.anyio
async def test_routine_happy_path_local_execution(client):
    with client.app.state.db.session() as session:
        run = run_routine(session, "Run the local morning routine")

    assert run.stage == ROUTINE_EXECUTION_STAGE
    assert run.state == "completed"
    assert run.preflight.policy_chain_routed is True
    assert run.preflight.wake_allowed is True
    assert run.preflight.budget_allowed is True
    assert run.task_run_record.packet_type == "TaskRunRecord"
    assert run.task_run_record.stage == "96P"
    assert run.delivery.channel == "local_only"
    assert run.delivery.automatic_delivery_authorized is False
    assert run.live_cron_authorized is False
    assert [event.event for event in run.audit_trail] == [
        "routine_defined",
        "policy_chain_routed",
        "wake_preflight",
        "budget_preflight",
        "state_selected",
    ]


@pytest.mark.anyio
async def test_wake_gate_skip(client):
    with client.app.state.db.session() as session:
        run = run_routine(
            session,
            "Run the local morning routine",
            definition(wake_signal_present=False),
        )

    assert run.state == "skipped"
    assert run.error_code == "routine_wake_gate_skipped"
    assert run.delivery.external_side_effect_authorized is False


@pytest.mark.anyio
async def test_budget_block_placeholder(client):
    with client.app.state.db.session() as session:
        run = run_routine(
            session,
            "Run the local morning routine",
            definition(budget_preflight_allowed=False),
        )

    assert run.state == "blocked"
    assert run.error_code == "routine_budget_preflight_blocked"
    assert ("budget_preflight", "block_placeholder") in [(event.event, event.detail) for event in run.audit_trail]


@pytest.mark.anyio
async def test_memory_projection_bounded_by_routine_scope(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=98111, first_name="Scoped", username="scoped")
        session.add(user)
        session.flush()
        robot = Robot(user_id=user.id, name="Scoped Robot")
        session.add(robot)
        session.flush()
        session.add_all(
            [
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Use routines only after explicit approval.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="WORK_PREFERENCE",
                    content="Prefers concise routine summaries.",
                    display_label="Preference",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="SECRET",
                    content="Sensitive value must not project.",
                    display_label="Secret",
                    source="telegram_text",
                    status="ACTIVE",
                ),
            ]
        )
        session.flush()
        run = run_routine(session, "Run the local morning routine", user_id=98111)

    assert [projection.memory_type for projection in run.bounded_memory_projection] == [
        "BOUNDARY_MEMORY",
        "WORK_PREFERENCE",
    ]
    assert all("Sensitive value" not in projection.content for projection in run.bounded_memory_projection)


@pytest.mark.anyio
async def test_caregiver_routine_compatibility_uses_97p_without_auto_send(client):
    with client.app.state.db.session() as session:
        run = run_routine(
            session,
            "Start the hearing aid routine",
            definition(kind="caregiver", label="Approved caregiver routine"),
        )

    assert run.state == "completed"
    assert run.caregiver_result is not None
    assert run.caregiver_result.stage == "97P"
    assert run.automatic_caregiver_alert_authorized is False
    assert run.caregiver_result.local_response["automatic_caregiver_send"] is False


@pytest.mark.anyio
async def test_approval_required_action_produces_action_packet_local_output(client):
    with client.app.state.db.session() as session:
        run = run_routine(session, "Send email to Ana with the routine summary")

    assert run.state == "needs_confirmation"
    assert run.action_packet is not None
    assert run.action_packet.action_class == "SEND_EXTERNAL_MESSAGE"
    assert run.action_packet.external_effect_authorized is False
    assert run.task_run_record.hermes_adapter_called is False
    assert run.delivery.automatic_delivery_authorized is False


@pytest.mark.anyio
async def test_blocked_action_does_not_reach_hermes_adapter(client):
    with client.app.state.db.session() as session:
        run = run_routine(session, "Change her medication dose tonight")

    assert run.state == "blocked"
    assert run.policy_result.ok is False
    assert run.task_run_record.hermes_adapter_called is False
    assert run.policy_result.hermes_adapter.called is False


@pytest.mark.anyio
async def test_no_silent_scheduling_or_execution(client):
    with client.app.state.db.session() as session:
        run = run_routine(
            session,
            "Run the local morning routine",
            definition(explicit_user_approved=False),
        )

    assert run.state == "blocked"
    assert run.error_code == "routine_silent_execution_blocked"
    assert run.live_scheduler_authorized is False
    assert run.live_cron_authorized is False


def test_definition_rejects_live_schedule_authority():
    with pytest.raises(ValueError, match="live scheduling"):
        definition(live_schedule_authorized=True)


@pytest.mark.anyio
async def test_failed_routine_produces_auditable_failed_state(client):
    with client.app.state.db.session() as session:
        run = run_routine(session, "Run the local morning routine", force_failure=True)

    assert run.state == "failed"
    assert run.error_code == "routine_local_failure"
    assert ("state_selected", "failed") in [(event.event, event.detail) for event in run.audit_trail]
    assert run.delivery.external_side_effect_authorized is False


@pytest.mark.anyio
async def test_policy_trace_completeness(client):
    with client.app.state.db.session() as session:
        run = run_routine(session, "Run the local morning routine")

    assert [decision.policy for decision in run.policy_result.policy_trace] == [
        "command_surface_policy_90p",
        "skill_scope_policy_91p",
        "tool_authority_policy_92p",
    ]
    assert run.hermes_os_contract.policy_trace.complete is True


def test_routine_execution_module_has_no_network_or_external_execution_imports():
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


def test_98p_reference_doc_and_roadmap_close_stage_without_99p_authorization():
    doc = DOC_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "Status: 98P closed committed." in doc
    assert "RoutineDefinition" in doc
    assert "RoutineRun" in doc
    assert "no live cron" in doc
    assert "no automatic delivery" in doc
    assert '"stage_id":"98P","stage_name":"Routine Execution Engine Skeleton v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_99p_and_later_authorized":false' in roadmap
    assert '"status":"NEXT_ELIGIBLE"' not in roadmap
