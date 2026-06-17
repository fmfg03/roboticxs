from __future__ import annotations

from pathlib import Path
from dataclasses import replace

import pytest

from app.action_packet_approval import (
    ACTION_PACKET_APPROVAL_STAGE,
    ActionPacketApprovalState,
    ActionPacketDecision,
    ActionPacketRequest,
    action_packet_request_from_95p_result,
    action_packet_request_from_cost_confirmation,
    action_packet_request_from_routine_run,
    apply_action_packet_decision,
    bind_approval_state_to_96p_contract,
    create_action_packet,
    serialize_action_packet_approval_state,
    submit_action_packet_for_approval,
)
from app.config import Settings
from app.cost_governor import can_dispatch_async_delegation
from app.hermes_os_contract import build_hermes_os_runtime_contract
from app.memory_center_projection import MemoryCenterItem, MemoryProjectionRequest, project_memory
from app.models import Robot, User
from app.routine_execution_engine import RoutineDefinition, execute_routine_locally
from app.telegram_policy_chain import run_telegram_policy_chain


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/action_packet_approval.py"


def build_update(text: str, user_id: int = 101001, chat_id: int | None = None) -> dict:
    return {
        "update_id": 101001,
        "message": {
            "message_id": 1010,
            "date": 1710000000,
            "chat": {"id": user_id if chat_id is None else chat_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Approval", "username": "approval"},
            "text": text,
        },
    }


def request(**overrides) -> ActionPacketRequest:
    values = {
        "request_id": "request-101p",
        "source_stage": "95P",
        "action_type": "tool_action",
        "owner_id": "owner-101p",
        "robot_id": "robot-101p",
        "actor_id": "owner-101p",
        "actor_role": "owner_admin",
        "requested_by_actor_id": "owner-101p",
        "requested_by_actor_role": "owner_admin",
        "required_policy_trace": (
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        ),
        "required_cost_preflight": None,
        "required_memory_projection": None,
        "required_routine_context": None,
        "action_payload": {"requested_text": "Send the approved email draft."},
        "review_expires_at": "2026-06-18T00:00:00Z",
        "resume_scope": "future_local_runtime_only",
    }
    values.update(overrides)
    return ActionPacketRequest(**values)


def decision(approval_state: ActionPacketApprovalState, choice: str, **overrides) -> ActionPacketDecision:
    values = {
        "packet_id": approval_state.packet.packet_id,
        "packet_version": approval_state.packet.packet_version,
        "decision": choice,
        "actor_id": approval_state.packet.actor_id,
        "actor_role": approval_state.packet.actor_role,
        "owner_id": approval_state.packet.owner_id,
        "robot_id": approval_state.packet.robot_id,
        "reason_code": f"{choice}_requested",
        "edit_payload": None,
        "resume_token_id": None,
        "occurred_at": "2026-06-17T12:00:00Z",
    }
    values.update(overrides)
    return ActionPacketDecision(**values)


def create_and_submit(packet_request: ActionPacketRequest | None = None) -> ActionPacketApprovalState:
    approval_state = create_action_packet(
        request=packet_request or request(),
        occurred_at="2026-06-17T10:00:00Z",
    )
    return submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=approval_state.packet.requested_by_actor_id,
        actor_role=approval_state.packet.requested_by_actor_role,
        occurred_at="2026-06-17T10:05:00Z",
    )


@pytest.mark.anyio
async def test_creates_proposed_action_packet_from_local_request(client):
    approval_state = create_action_packet(request=request(), occurred_at="2026-06-17T10:00:00Z")

    assert approval_state.stage == ACTION_PACKET_APPROVAL_STAGE
    assert approval_state.packet.state == "proposed"
    assert approval_state.packet.resume_token_id is None
    assert approval_state.packet.execution_authorized is False
    assert approval_state.packet.external_effect_authorized is False
    assert approval_state.trace_records[0].next_state == "proposed"


@pytest.mark.anyio
async def test_transitions_proposed_to_awaiting_approval(client):
    approval_state = create_and_submit()

    assert approval_state.packet.state == "awaiting_approval"
    assert [event.next_state for event in approval_state.review_history] == ["proposed", "awaiting_approval"]


@pytest.mark.anyio
async def test_approves_awaiting_packet_and_creates_bounded_local_resume_token(client):
    approval_state = create_and_submit()
    approved = apply_action_packet_decision(
        approval_state=approval_state,
        decision=decision(approval_state, "approve"),
    )

    assert approved.packet.state == "approved"
    assert approved.resume_token is not None
    assert approved.resume_token.used is False
    assert approved.resume_token.owner_id == approved.packet.owner_id
    assert approved.resume_token.robot_id == approved.packet.robot_id
    assert approved.resume_token.actor_id == approved.packet.actor_id
    assert approved.resume_token.resume_scope == approved.packet.resume_scope


@pytest.mark.anyio
async def test_approved_packet_still_does_not_execute_anything_in_101p(client):
    approved = apply_action_packet_decision(
        approval_state=create_and_submit(),
        decision=decision(create_and_submit(), "approve"),
    )
    serialized = serialize_action_packet_approval_state(approved)

    assert serialized["packet"]["execution_authorized"] is False
    assert serialized["packet"]["external_effect_authorized"] is False
    assert serialized["packet"]["provider_call_authorized"] is False
    assert serialized["resume_token"]["execution_authorized"] is False


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("choice", "final_state"),
    [
        ("reject", "rejected"),
        ("cancel", "cancelled"),
        ("expire", "expired"),
    ],
)
async def test_reject_cancel_and_expire_prevent_resume(client, choice, final_state):
    approval_state = create_and_submit()
    finalized = apply_action_packet_decision(approval_state=approval_state, decision=decision(approval_state, choice))
    resumed = apply_action_packet_decision(
        approval_state=finalized,
        decision=decision(finalized, "resume", resume_token_id="missing"),
    )

    assert finalized.packet.state == final_state
    assert resumed.packet.state == "blocked"
    assert resumed.trace_records[-1].reason_code == f"blocked_{final_state}_packet_cannot_resume"


@pytest.mark.anyio
async def test_blocked_packet_prevents_resume(client):
    blocked = create_action_packet(
        request=request(required_policy_trace=()),
        occurred_at="2026-06-17T10:00:00Z",
    )
    resumed = apply_action_packet_decision(
        approval_state=blocked,
        decision=decision(blocked, "resume", resume_token_id="missing"),
    )

    assert blocked.packet.state == "blocked"
    assert resumed.packet.state == "blocked"
    assert resumed.trace_records[-1].reason_code == "blocked_blocked_packet_cannot_resume"


@pytest.mark.anyio
async def test_edit_creates_revised_packet_version_and_preserves_prior_history(client):
    approval_state = create_and_submit()
    revised = apply_action_packet_decision(
        approval_state=approval_state,
        decision=decision(
            approval_state,
            "edit",
            edit_payload={"requested_text": "Send the revised local-only email draft."},
        ),
    )

    assert revised.packet.state == "proposed"
    assert revised.packet.packet_version == 2
    assert revised.packet.supersedes_packet_id == revised.packet.packet_id
    assert revised.prior_versions[-1].packet_version == 1
    assert [event.next_state for event in revised.review_history[-2:]] == ["edited", "proposed"]


@pytest.mark.anyio
async def test_resume_token_is_single_use(client):
    submitted = create_and_submit()
    approved = apply_action_packet_decision(approval_state=submitted, decision=decision(submitted, "approve"))
    resumed = apply_action_packet_decision(
        approval_state=approved,
        decision=decision(
            approved,
            "resume",
            resume_token_id=approved.resume_token.token_id,
            reason_code="resume_once",
        ),
    )
    blocked_again = apply_action_packet_decision(
        approval_state=resumed,
        decision=decision(
            resumed,
            "resume",
            resume_token_id=resumed.resume_token.token_id,
            reason_code="resume_twice",
            occurred_at="2026-06-17T12:01:00Z",
        ),
    )

    assert resumed.packet.state == "resumed"
    assert resumed.resume_token.used is True
    assert blocked_again.packet.state == "blocked"
    assert blocked_again.trace_records[-1].reason_code == "blocked_resume_requires_approved_packet_and_token"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("owner_id", "wrong-owner", "blocked_owner_id_mismatch"),
        ("robot_id", "wrong-robot", "blocked_robot_id_mismatch"),
        ("actor_id", "wrong-actor", "blocked_actor_id_mismatch"),
    ],
)
async def test_resume_token_blocks_on_owner_robot_and_actor_mismatch(client, field, value, reason):
    submitted = create_and_submit()
    approved = apply_action_packet_decision(approval_state=submitted, decision=decision(submitted, "approve"))
    kwargs = {"resume_token_id": approved.resume_token.token_id, "reason_code": "resume_attempt"}
    kwargs[field] = value
    blocked = apply_action_packet_decision(
        approval_state=approved,
        decision=decision(approved, "resume", **kwargs),
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == reason


@pytest.mark.anyio
async def test_stale_or_expired_token_blocks(client):
    submitted = create_and_submit()
    approved = apply_action_packet_decision(approval_state=submitted, decision=decision(submitted, "approve"))
    blocked = apply_action_packet_decision(
        approval_state=approved,
        decision=decision(
            approved,
            "resume",
            resume_token_id=approved.resume_token.token_id,
            occurred_at="2026-06-19T12:00:00Z",
            reason_code="late_resume",
        ),
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_resume_token_expired"


@pytest.mark.anyio
async def test_unknown_state_blocks(client):
    approval_state = create_action_packet(request=request(), occurred_at="2026-06-17T10:00:00Z")
    broken = ActionPacketApprovalState(
        stage=approval_state.stage,
        packet=replace(approval_state.packet, state="mystery"),
        review_history=approval_state.review_history,
        trace_records=approval_state.trace_records,
        resume_token=approval_state.resume_token,
        prior_versions=approval_state.prior_versions,
    )
    blocked = apply_action_packet_decision(approval_state=broken, decision=decision(approval_state, "approve"))

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_unknown_packet_state"


@pytest.mark.anyio
async def test_unknown_decision_blocks(client):
    approval_state = create_and_submit()
    blocked = apply_action_packet_decision(
        approval_state=approval_state,
        decision=decision(approval_state, "approve", decision="mystery"),
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_unknown_decision"


@pytest.mark.anyio
async def test_missing_required_policy_trace_blocks(client):
    blocked = create_action_packet(
        request=request(required_policy_trace=()),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_missing_required_policy_trace"


@pytest.mark.anyio
async def test_missing_required_100p_cost_preflight_blocks_when_cost_is_required(client):
    blocked = create_action_packet(
        request=request(action_type="cost_confirmation", required_cost_preflight=None),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_missing_required_cost_preflight"


@pytest.mark.anyio
async def test_missing_bounded_99p_memory_projection_blocks_when_memory_is_required(client):
    blocked = create_action_packet(
        request=request(action_payload={"memory_projection_required": True}),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_missing_required_memory_projection"


@pytest.mark.anyio
async def test_100p_require_confirmation_converts_into_action_packet_compatible_approval_record(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=101077, first_name="Cost", username="cost")
        session.add(user)
        session.flush()
        owner_id = str(user.id)
        robot = Robot(user_id=user.id, name="Cost Robot")
        session.add(robot)
        session.flush()
        robot_id = str(robot.id)
        result = run_telegram_policy_chain(
            update=build_update("Premium research " + ("long context " * 700), user_id=101077),
            settings=Settings(),
            session=session,
        )

    packet_request = action_packet_request_from_cost_confirmation(
        cost_confirmation=result.cost_confirmation,
        cost_preflight=result.cost_preflight,
        actor_id=owner_id,
        actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in result.policy_trace),
        review_expires_at="2026-06-18T00:00:00Z",
    )

    assert packet_request.action_type == "cost_confirmation"
    assert packet_request.required_cost_preflight["decision"] == "require_confirmation"
    assert packet_request.action_payload["selected_model_id"] == result.cost_confirmation.selected_model_id
    assert packet_request.required_cost_preflight["task_cost_request"] == result.cost_confirmation.task_cost_request
    assert packet_request.required_cost_preflight["budget_policy"] == result.cost_confirmation.budget_policy
    assert packet_request.required_cost_preflight["owner_id"] == owner_id
    assert packet_request.required_cost_preflight["robot_id"] == robot_id
    assert packet_request.required_cost_preflight["requester_actor_id"] == owner_id


@pytest.mark.anyio
async def test_cost_confirmation_approval_preserves_selected_route_and_budget_constraints(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=101078, first_name="Budget", username="budget")
        session.add(user)
        session.flush()
        owner_id = str(user.id)
        robot = Robot(user_id=user.id, name="Budget Robot")
        session.add(robot)
        session.flush()
        result = run_telegram_policy_chain(
            update=build_update("Premium research " + ("long context " * 700), user_id=101078),
            settings=Settings(),
            session=session,
        )
    packet_request = action_packet_request_from_cost_confirmation(
        cost_confirmation=result.cost_confirmation,
        cost_preflight=result.cost_preflight,
        actor_id=owner_id,
        actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in result.policy_trace),
        review_expires_at="2026-06-18T00:00:00Z",
    )
    approval_state = create_and_submit(packet_request)
    approved = apply_action_packet_decision(approval_state=approval_state, decision=decision(approval_state, "approve"))

    assert approved.packet.required_selected_model_id == result.cost_preflight.route_decision.selected_model_id
    assert approved.packet.required_cost_preflight_decision == "require_confirmation"
    assert approved.packet.action_payload["estimated_cost_usd"] == result.cost_confirmation.estimated_cost_usd
    assert approved.packet.required_cost_preflight["route_decision"] == packet_request.required_cost_preflight["route_decision"]
    assert approved.packet.required_cost_preflight["budget_policy"] == packet_request.required_cost_preflight["budget_policy"]
    assert approved.packet.required_cost_preflight["authority_flags"]["authority_expanded"] is False
    assert approved.packet.required_cost_preflight["authority_flags"]["external_effect_authorized"] is False
    assert approved.packet.required_cost_preflight["authority_flags"]["provider_call_authorized"] is False
    assert approved.packet.required_cost_preflight["authority_flags"]["execution_authorized"] is False


@pytest.mark.anyio
async def test_cost_confirmation_approval_does_not_call_provider_model_hermes_or_external_execution(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=101079, first_name="NoExec", username="noexec")
        session.add(user)
        session.flush()
        owner_id = str(user.id)
        robot = Robot(user_id=user.id, name="NoExec Robot")
        session.add(robot)
        session.flush()
        result = run_telegram_policy_chain(
            update=build_update("Premium research " + ("long context " * 700), user_id=101079),
            settings=Settings(),
            session=session,
        )
    packet_request = action_packet_request_from_cost_confirmation(
        cost_confirmation=result.cost_confirmation,
        cost_preflight=result.cost_preflight,
        actor_id=owner_id,
        actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in result.policy_trace),
        review_expires_at="2026-06-18T00:00:00Z",
    )
    approved = apply_action_packet_decision(
        approval_state=create_and_submit(packet_request),
        decision=decision(create_and_submit(packet_request), "approve"),
    )

    assert approved.packet.provider_call_authorized is False
    assert approved.packet.execution_authorized is False
    assert approved.packet.external_effect_authorized is False
    assert can_dispatch_async_delegation(result.cost_preflight) is False


@pytest.mark.anyio
async def test_95p_can_emit_or_bind_action_packet_approval_metadata_without_bypassing_existing_policy(client):
    with client.app.state.db.session() as session:
        result = run_telegram_policy_chain(
            update=build_update("Send email to Ana with the local summary", user_id=101095),
            settings=Settings(),
            session=session,
        )

    packet_request = action_packet_request_from_95p_result(
        policy_result=result,
        actor_id=str(result.user_id),
        actor_role="owner_admin",
        review_expires_at="2026-06-18T00:00:00Z",
    )
    approval_state = create_action_packet(request=packet_request, occurred_at="2026-06-17T10:00:00Z")

    assert packet_request.required_policy_trace == (
        "command_surface_policy_90p",
        "skill_scope_policy_91p",
        "tool_authority_policy_92p",
    )
    assert packet_request.owner_id == result.owner_id
    assert packet_request.robot_id == result.robot_id
    assert packet_request.robot_id == approval_state.packet.robot_id
    assert packet_request.robot_id.startswith("robot_") is False
    assert result.hermes_adapter.called is False
    assert approval_state.packet.execution_authorized is False


@pytest.mark.anyio
async def test_96p_can_bind_action_packet_state_without_treating_approval_as_tool_or_action_authority(client):
    with client.app.state.db.session() as session:
        result = run_telegram_policy_chain(
            update=build_update("Send email to Ana with the local summary", user_id=101096),
            settings=Settings(),
            session=session,
        )
        contract = build_hermes_os_runtime_contract(policy_result=result)

    approval_state = create_action_packet(
        request=action_packet_request_from_95p_result(
            policy_result=result,
            actor_id=str(result.user_id),
            actor_role="owner_admin",
            review_expires_at="2026-06-18T00:00:00Z",
        ),
        occurred_at="2026-06-17T10:00:00Z",
    )
    binding = bind_approval_state_to_96p_contract(contract=contract, approval_state=approval_state)

    assert binding["action_packet_bound"] is True
    assert binding["approval_is_tool_authority"] is False
    assert binding["approval_is_execution_authority"] is False


@pytest.mark.anyio
async def test_98p_routine_continuation_approval_does_not_bypass_routine_preflight(client):
    with client.app.state.db.session() as session:
        good_run = execute_routine_locally(
            definition=RoutineDefinition(
                routine_id="routine_good",
                label="Good Routine",
                trigger_text="Run the good routine",
            ),
            update=build_update("Run the good routine", user_id=101098),
            settings=Settings(),
            session=session,
        )
        blocked_run = execute_routine_locally(
            definition=RoutineDefinition(
                routine_id="routine_blocked",
                label="Blocked Routine",
                trigger_text="Run the blocked routine",
                explicit_user_approved=False,
            ),
            update=build_update("Run the blocked routine", user_id=101099),
            settings=Settings(),
            session=session,
        )

    good_request = action_packet_request_from_routine_run(
        routine_run=good_run,
        actor_id=str(good_run.policy_result.user_id),
        actor_role="owner_admin",
        review_expires_at="2026-06-18T00:00:00Z",
    )
    blocked_request = action_packet_request_from_routine_run(
        routine_run=blocked_run,
        actor_id=str(blocked_run.policy_result.user_id),
        actor_role="owner_admin",
        review_expires_at="2026-06-18T00:00:00Z",
    )

    assert create_action_packet(request=good_request, occurred_at="2026-06-17T10:00:00Z").packet.state == "proposed"
    assert create_action_packet(request=blocked_request, occurred_at="2026-06-17T10:00:00Z").packet.state == "blocked"
    assert good_request.robot_id == good_run.policy_result.robot_id
    assert good_request.required_routine_context["robot_id"] == good_run.policy_result.robot_id
    assert good_request.robot_id.startswith("robot_") is False


def test_99p_excluded_memory_is_not_exposed_through_action_packet_traces_or_approval_records():
    sensitive = MemoryCenterItem(
        item_id="medical",
        owner_id="owner",
        robot_id="robot",
        memory_kind="MEDICAL_NOTE",
        status="active",
        scopes=("caregiver",),
        sensitivity="medical",
        allowed_uses=("caregiver_context",),
        skill_ids=(),
        content="raw-medical-secret",
        bounded_summary="Approved bounded summary.",
        source="test",
        authorized_actor_ids=("caregiver-1",),
        actor_visibility="caregiver_private",
    )
    result = project_memory(
        request=MemoryProjectionRequest(
            request_id="projection-101p",
            actor_id="caregiver-2",
            actor_role="caregiver",
            owner_id="owner",
            robot_id="robot",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
        items=(sensitive,),
    )
    approval_state = create_action_packet(
        request=request(
            required_memory_projection={
                "request_id": result.request_id,
                "bounded": result.bounded,
                "summary_count": len(result.summaries),
                "trace_reason_codes": [trace.reason_code for trace in result.trace],
            },
            action_payload={"memory_projection_required": True},
        ),
        occurred_at="2026-06-17T10:00:00Z",
    )
    serialized = serialize_action_packet_approval_state(approval_state)

    assert "raw-medical-secret" not in repr(result.trace)
    assert "raw-medical-secret" not in repr(serialized)
    assert "Approved bounded summary." not in repr(serialized)


@pytest.mark.anyio
@pytest.mark.parametrize("action_type", ["async_delegation", "live_delivery"])
async def test_future_async_delegation_and_live_telegram_delivery_packets_remain_local_only_and_non_executing(
    client, action_type
):
    approval_state = create_and_submit(
        request(
            action_type=action_type,
            action_payload={"requested_text": action_type, "future_only": True},
        )
    )
    approved = apply_action_packet_decision(approval_state=approval_state, decision=decision(approval_state, "approve"))

    assert approved.packet.state == "approved"
    assert approved.packet.execution_authorized is False
    assert approved.packet.external_effect_authorized is False
    assert approved.packet.provider_call_authorized is False


def test_trace_records_are_deterministic_and_inspectable():
    first = create_and_submit()
    second = create_and_submit()

    assert serialize_action_packet_approval_state(first)["trace_records"] == serialize_action_packet_approval_state(second)[
        "trace_records"
    ]
    assert all(record["packet_id"] == first.packet.packet_id for record in serialize_action_packet_approval_state(first)["trace_records"])


@pytest.mark.anyio
async def test_95p_derived_action_packet_blocks_when_upstream_robot_id_is_missing(client):
    with client.app.state.db.session() as session:
        result = run_telegram_policy_chain(
            update=build_update("Send email to Ana with the local summary", user_id=101119),
            settings=Settings(),
            session=session,
        )
    result = replace(result, robot_id=None)
    blocked = create_action_packet(
        request=action_packet_request_from_95p_result(
            policy_result=result,
            actor_id=str(result.user_id),
            actor_role="owner_admin",
        ),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_missing_robot_id"


@pytest.mark.anyio
async def test_98p_derived_action_packet_blocks_when_routine_robot_id_is_missing(client):
    with client.app.state.db.session() as session:
        run = execute_routine_locally(
            definition=RoutineDefinition(
                routine_id="routine_missing_robot",
                label="Missing Robot",
                trigger_text="Send email to Ana with the routine summary",
            ),
            update=build_update("Send email to Ana with the routine summary", user_id=101120),
            settings=Settings(),
            session=session,
        )
    run = replace(run, policy_result=replace(run.policy_result, robot_id=None))
    blocked = create_action_packet(
        request=action_packet_request_from_routine_run(
            routine_run=run,
            actor_id=str(run.policy_result.user_id),
            actor_role="owner_admin",
        ),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_missing_robot_id"


@pytest.mark.anyio
async def test_approval_resume_blocks_on_robot_mismatch_against_preserved_upstream_robot_id(client):
    with client.app.state.db.session() as session:
        result = run_telegram_policy_chain(
            update=build_update("Send email to Ana with the local summary", user_id=101121),
            settings=Settings(),
            session=session,
        )

    approval_state = create_and_submit(
        action_packet_request_from_95p_result(
            policy_result=result,
            actor_id=str(result.user_id),
            actor_role="owner_admin",
            review_expires_at="2026-06-18T00:00:00Z",
        )
    )
    approved = apply_action_packet_decision(approval_state=approval_state, decision=decision(approval_state, "approve"))
    blocked = apply_action_packet_decision(
        approval_state=approved,
        decision=decision(
            approved,
            "resume",
            robot_id="wrong-robot",
            resume_token_id=approved.resume_token.token_id,
            reason_code="robot_boundary_mismatch",
        ),
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_robot_id_mismatch"


@pytest.mark.anyio
async def test_cost_confirmation_approval_state_keeps_preserved_preflight_request_without_recomputation(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=101122, first_name="Preserve", username="preserve")
        session.add(user)
        session.flush()
        owner_id = str(user.id)
        robot = Robot(user_id=user.id, name="Preserve Robot")
        session.add(robot)
        session.flush()
        result = run_telegram_policy_chain(
            update=build_update("Premium research " + ("long context " * 700), user_id=101122),
            settings=Settings(),
            session=session,
        )
    packet_request = action_packet_request_from_cost_confirmation(
        cost_confirmation=result.cost_confirmation,
        cost_preflight=result.cost_preflight,
        actor_id=owner_id,
        actor_role="owner_admin",
        required_policy_trace=tuple(step.policy for step in result.policy_trace),
        review_expires_at="2026-06-18T00:00:00Z",
    )
    approved = apply_action_packet_decision(
        approval_state=create_and_submit(packet_request),
        decision=decision(create_and_submit(packet_request), "approve"),
    )
    serialized = serialize_action_packet_approval_state(approved)

    assert serialized["packet"]["required_cost_preflight"]["task_cost_request"] == result.cost_confirmation.task_cost_request
    assert serialized["packet"]["required_cost_preflight"]["budget_policy"] == result.cost_confirmation.budget_policy
    assert serialized["packet"]["required_cost_preflight"]["route_decision"]["selected_model_id"] == result.cost_preflight.route_decision.selected_model_id
    assert serialized["packet"]["required_cost_preflight"]["authority_flags"]["execution_authorized"] is False
    assert serialized["packet"]["execution_authorized"] is False


def test_trace_records_keep_external_provider_and_execution_flags_false():
    approved = apply_action_packet_decision(
        approval_state=create_and_submit(),
        decision=decision(create_and_submit(), "approve"),
    )

    assert all(trace.external_effect_authorized is False for trace in approved.trace_records)
    assert all(trace.provider_call_authorized is False for trace in approved.trace_records)
    assert all(trace.execution_authorized is False for trace in approved.trace_records)


def test_102p_and_later_remain_unauthorized():
    blocked = create_action_packet(
        request=request(source_stage="102P"),
        occurred_at="2026-06-17T10:00:00Z",
    )

    assert blocked.packet.state == "blocked"
    assert blocked.trace_records[-1].reason_code == "blocked_unauthorized_source_stage"


def test_action_packet_approval_module_has_no_network_or_external_execution_imports():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "api.telegram.org",
        "smtp",
        "stripe",
    ]:
        assert forbidden not in text
