from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.hermes_os_contract import build_hermes_os_runtime_contract
from app.memory_center_projection import (
    MemoryCenterItem,
    MemoryProjectionRequest,
    MemoryProjectionResult,
    project_memory,
)
from app.models import MemoryItem, Robot, User
from app.routine_execution_engine import RoutineDefinition, execute_routine_locally
from app.telegram_policy_chain import run_telegram_policy_chain


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/memory_center_projection.py"
SPEC_PATH = REPO_ROOT / "docs/reference/MEMORY_CENTER_PROJECTION_RUNTIME_99P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def item(item_id: str, **overrides) -> MemoryCenterItem:
    values = {
        "item_id": item_id,
        "owner_id": "owner",
        "robot_id": "robot",
        "memory_kind": "WORK_PREFERENCE",
        "status": "active",
        "scopes": ("telegram",),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context",),
        "skill_ids": (),
        "content": f"content-{item_id}",
        "bounded_summary": None,
        "source": "test",
        "authorized_actor_ids": (),
        "actor_visibility": "owner_private",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


def request(**overrides) -> MemoryProjectionRequest:
    values = {
        "request_id": "request",
        "actor_id": "owner",
        "actor_role": "owner_admin",
        "owner_id": "owner",
        "robot_id": "robot",
        "target_scope": "telegram",
        "allowed_use": "telegram_context",
        "max_items": 3,
        "max_summary_chars": 160,
    }
    values.update(overrides)
    return MemoryProjectionRequest(**values)


def build_update(text: str, user_id: int = 99001) -> dict:
    return {
        "update_id": 99001,
        "message": {
            "message_id": 990,
            "date": 1710000000,
            "chat": {"id": user_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Memory", "username": "memory"},
            "text": text,
        },
    }


def test_active_and_approved_memory_project_into_allowed_context():
    result = project_memory(items=(item("active"), item("approved", status="approved")), request=request())

    assert [summary.item_id for summary in result.summaries] == ["active", "approved"]
    assert all(summary.decisional for summary in result.summaries)


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("revoked", "excluded_status_revoked"),
        ("stale", "excluded_status_stale"),
        ("conflicted", "excluded_status_conflicted"),
        ("never-use-for-decisions", "excluded_never_use_for_decisions"),
    ],
)
def test_default_status_exclusions(status, reason):
    result = project_memory(items=(item("excluded", status=status),), request=request())

    assert result.summaries == ()
    assert result.trace[0].reason_code == reason
    assert result.trace[0].decisional is False


def test_sensitive_memory_is_redacted_or_excluded_without_leaking_trace_content():
    sensitive = item(
        "medical",
        scopes=("caregiver",),
        sensitivity="medical",
        allowed_uses=("caregiver_context",),
        content="raw-medical-secret",
        bounded_summary="Approved routine safety boundary.",
        authorized_actor_ids=("caregiver-1",),
        actor_visibility="caregiver_private",
    )
    caregiver_request = request(
        actor_id="caregiver-1",
        actor_role="caregiver",
        target_scope="caregiver",
        allowed_use="caregiver_context",
    )
    result = project_memory(items=(sensitive,), request=caregiver_request)

    assert [summary.summary for summary in result.summaries] == ["Approved routine safety boundary."]
    assert result.summaries[0].redacted is True
    assert "raw-medical-secret" not in repr(result.trace)


def test_unrelated_caregiver_actor_id_cannot_see_caregiver_private_memory():
    private = item(
        "caregiver-private",
        scopes=("caregiver",),
        sensitivity="caregiver",
        allowed_uses=("caregiver_context",),
        content="caregiver-private-raw-content",
        bounded_summary="Bounded caregiver-only summary.",
        authorized_actor_ids=("caregiver-authorized",),
        actor_visibility="caregiver_private",
    )

    result = project_memory(
        items=(private,),
        request=request(
            actor_id="caregiver-unrelated",
            actor_role="caregiver",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
    )

    assert result.summaries == ()
    assert result.trace[0].reason_code == "excluded_actor_isolation"
    assert "caregiver-private-raw-content" not in repr(result.trace)
    assert "Bounded caregiver-only summary." not in repr(result.trace)


def test_care_recipient_cannot_see_caregiver_private_memory():
    private = item(
        "caregiver-private",
        scopes=("caregiver",),
        sensitivity="caregiver",
        allowed_uses=("caregiver_context",),
        content="private-caregiver-note",
        bounded_summary="Caregiver-only bounded summary.",
        authorized_actor_ids=("recipient-1", "caregiver-1"),
        actor_visibility="caregiver_private",
    )

    result = project_memory(
        items=(private,),
        request=request(
            actor_id="recipient-1",
            actor_role="care_recipient",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
    )

    assert result.summaries == ()
    assert result.trace[0].reason_code == "excluded_actor_isolation"
    assert "private-caregiver-note" not in repr(result.trace)
    assert "Caregiver-only bounded summary." not in repr(result.trace)


def test_authorized_caregiver_receives_only_explicit_bounded_summary():
    private = item(
        "caregiver-private",
        scopes=("caregiver",),
        sensitivity="caregiver",
        allowed_uses=("caregiver_context",),
        content="raw caregiver note with sensitive detail",
        bounded_summary="Bounded caregiver summary.",
        authorized_actor_ids=("caregiver-1",),
        actor_visibility="caregiver_private",
    )

    result = project_memory(
        items=(private,),
        request=request(
            actor_id="caregiver-1",
            actor_role="caregiver",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
    )

    assert [summary.summary for summary in result.summaries] == ["Bounded caregiver summary."]
    assert result.summaries[0].redacted is True
    assert "raw caregiver note" not in repr(result)


def test_care_recipient_receives_only_care_recipient_facing_memory():
    recipient_facing = item(
        "recipient-facing",
        scopes=("caregiver",),
        sensitivity="personal",
        allowed_uses=("caregiver_context",),
        content="raw recipient-facing detail",
        bounded_summary="Care-recipient-facing bounded summary.",
        authorized_actor_ids=("recipient-1",),
        actor_visibility="care_recipient_facing",
    )
    caregiver_private = item(
        "caregiver-private",
        scopes=("caregiver",),
        sensitivity="caregiver",
        allowed_uses=("caregiver_context",),
        content="private caregiver detail",
        bounded_summary="Caregiver-private bounded summary.",
        authorized_actor_ids=("recipient-1",),
        actor_visibility="caregiver_private",
    )

    result = project_memory(
        items=(recipient_facing, caregiver_private),
        request=request(
            actor_id="recipient-1",
            actor_role="care_recipient",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
    )

    assert [summary.item_id for summary in result.summaries] == ["recipient-facing"]
    assert result.summaries[0].summary == "Care-recipient-facing bounded summary."
    assert "private caregiver detail" not in repr(result.trace)
    assert "Caregiver-private bounded summary." not in repr(result.trace)


def test_actor_role_alone_never_grants_sensitive_caregiver_access():
    private = item(
        "caregiver-private",
        scopes=("caregiver",),
        sensitivity="caregiver",
        allowed_uses=("caregiver_context",),
        content="role-only raw private note",
        bounded_summary="Role-only should not see this.",
        actor_visibility="caregiver_private",
    )

    result = project_memory(
        items=(private,),
        request=request(
            actor_id="caregiver-with-role-only",
            actor_role="caregiver",
            target_scope="caregiver",
            allowed_use="caregiver_context",
        ),
    )

    assert result.summaries == ()
    assert result.trace[0].reason_code == "excluded_actor_isolation"
    assert "role-only raw private note" not in repr(result.trace)
    assert "Role-only should not see this." not in repr(result.trace)


def test_robot_and_routine_do_not_receive_caregiver_private_memory_without_explicit_scope():
    private = item(
        "caregiver-private",
        scopes=("routine",),
        sensitivity="caregiver",
        allowed_uses=("routine_context",),
        content="caregiver private routine detail",
        bounded_summary="Caregiver-private routine summary.",
        actor_visibility="caregiver_private",
    )

    routine_result = project_memory(
        items=(private,),
        request=request(actor_id="routine-1", actor_role="routine", target_scope="routine", allowed_use="routine_context"),
    )
    robot_result = project_memory(
        items=(private,),
        request=request(actor_id="robot-1", actor_role="robot", target_scope="routine", allowed_use="routine_context"),
    )

    assert routine_result.summaries == ()
    assert robot_result.summaries == ()
    assert {trace.reason_code for trace in routine_result.trace + robot_result.trace} == {"excluded_actor_isolation"}


def test_caregiver_cannot_see_unrelated_owner_memory():
    result = project_memory(
        items=(item("foreign", owner_id="other", scopes=("caregiver",), allowed_uses=("caregiver_context",)),),
        request=request(actor_role="caregiver", target_scope="caregiver", allowed_use="caregiver_context"),
    )

    assert result.summaries == ()
    assert result.trace[0].reason_code == "excluded_owner_isolation"


def test_routine_projection_only_includes_routine_scope():
    result = project_memory(
        items=(
            item("routine", scopes=("routine",), allowed_uses=("routine_context",)),
            item("telegram"),
        ),
        request=request(actor_role="routine", target_scope="routine", allowed_use="routine_context"),
    )

    assert [summary.item_id for summary in result.summaries] == ["routine"]
    assert {trace.reason_code for trace in result.trace} >= {"included_allowed_context", "excluded_scope_mismatch"}


def test_boundary_memory_precedes_and_overrides_conflicting_preference():
    result = project_memory(
        items=(
            item("preference", conflict_group="send", is_preference=True),
            item("boundary", memory_kind="BOUNDARY_MEMORY", conflict_group="send", is_boundary=True),
        ),
        request=request(),
    )

    assert [summary.item_id for summary in result.summaries] == ["boundary"]
    assert any(trace.reason_code == "excluded_preference_conflicts_with_boundary" for trace in result.trace)


def test_foreign_or_unprojectable_boundary_does_not_override_valid_preference():
    result = project_memory(
        items=(
            item("preference", conflict_group="send", is_preference=True),
            item(
                "foreign-boundary",
                owner_id="other",
                memory_kind="BOUNDARY_MEMORY",
                conflict_group="send",
                is_boundary=True,
            ),
            item(
                "sensitive-boundary",
                memory_kind="BOUNDARY_MEMORY",
                conflict_group="send",
                is_boundary=True,
                sensitivity="personal",
            ),
        ),
        request=request(),
    )

    assert [summary.item_id for summary in result.summaries] == ["preference"]
    assert {trace.reason_code for trace in result.trace} >= {
        "excluded_owner_isolation",
        "excluded_sensitive_no_safe_summary",
    }


def test_projection_rejects_authority_expansion_and_authority_flags_stay_false():
    rejected = project_memory(items=(item("allowed"),), request=request(authority_expansion_requested=True))

    assert rejected.status == "rejected"
    assert rejected.trace[0].reason_code == "rejected_authority_expansion"
    with pytest.raises(ValueError, match="cannot expand authority"):
        MemoryProjectionResult(
            request_id="unsafe",
            status="completed",
            summaries=(),
            trace=(),
            excluded_count=0,
            redacted_count=0,
            audit_only_count=0,
            tool_action_authorization=True,
        )


@pytest.mark.parametrize(
    ("request_overrides", "expected"),
    [
        ({"actor_role": "unknown"}, "rejected_unknown_actor"),
        ({"target_scope": "unknown"}, "rejected_unknown_scope"),
        ({"allowed_use": "unknown"}, "rejected_unknown_allowed_use"),
    ],
)
def test_unknown_request_values_reject(request_overrides, expected):
    result = project_memory(items=(item("allowed"),), request=request(**request_overrides))
    assert result.status == "rejected"
    assert result.trace[0].reason_code == expected


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"status": "unknown"}, "excluded_unknown_status"),
        ({"scopes": ("telegram", "unknown")}, "excluded_unknown_scope"),
        ({"sensitivity": "unknown"}, "excluded_unknown_sensitivity"),
        ({"allowed_uses": ("unknown",)}, "excluded_unknown_allowed_use"),
    ],
)
def test_unknown_item_values_exclude_with_trace(overrides, expected):
    result = project_memory(items=(item("invalid", **overrides),), request=request())
    assert result.summaries == ()
    assert result.trace[0].reason_code == expected


def test_skill_specific_projection_requires_supported_active_skill():
    skill_item = item(
        "skill",
        scopes=("skill_specific",),
        allowed_uses=("skill_context",),
        skill_ids=("basic_assistant", "unknown_skill"),
    )

    rejected = project_memory(
        items=(skill_item,),
        request=request(
            target_scope="skill_specific",
            allowed_use="skill_context",
            active_skill_id="unknown_skill",
        ),
    )
    supported = project_memory(
        items=(skill_item,),
        request=request(
            target_scope="skill_specific",
            allowed_use="skill_context",
            active_skill_id="basic_assistant",
        ),
    )

    assert rejected.status == "rejected"
    assert rejected.trace[0].reason_code == "rejected_unsupported_active_skill"
    assert [summary.item_id for summary in supported.summaries] == ["skill"]


def test_credential_like_data_never_projects():
    result = project_memory(
        items=(item("credential", sensitivity="credential_like", bounded_summary="still forbidden"),),
        request=request(),
    )
    assert result.summaries == ()
    assert result.trace[0].reason_code == "excluded_sensitive_unauthorized"


def test_bounds_and_ordering_are_deterministic():
    items = (
        item("z"),
        item("a"),
        item("boundary", memory_kind="BOUNDARY_MEMORY", is_boundary=True),
    )
    first = project_memory(items=items, request=request(max_items=2, max_summary_chars=8))
    second = project_memory(items=tuple(reversed(items)), request=request(max_items=2, max_summary_chars=8))

    assert first == second
    assert [summary.item_id for summary in first.summaries] == ["boundary", "a"]
    assert all(len(summary.summary) <= 8 for summary in first.summaries)
    assert any(trace.reason_code == "excluded_result_bound" for trace in first.trace)


@pytest.mark.anyio
async def test_95p_consumes_bounded_99p_projection_and_96p_binding_is_non_authority(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=99111, first_name="Bounded", username="bounded")
        session.add(user)
        session.flush()
        robot = Robot(user_id=user.id, name="Bounded Robot")
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
        policy_result = run_telegram_policy_chain(
            update=build_update("Draft a note", 99111),
            settings=Settings(),
            session=session,
        )
        contract = build_hermes_os_runtime_contract(policy_result=policy_result)

    projection = policy_result.memory_context.projection_result
    assert projection is not None
    assert projection.bounded is True
    assert projection.data_only is True
    assert len(projection.summaries) == len(policy_result.memory_context.projections) == 1
    assert contract.memory_projection_packet.bounded is True
    assert contract.memory_projection_packet.tool_action_authorization is False
    assert contract.memory_projection_packet.permission_expansion_authorized is False


@pytest.mark.anyio
async def test_legacy_adapter_does_not_invent_caregiver_or_routine_scope(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=99112, first_name="Scoped", username="scoped")
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
                    content="Require approval before routine actions.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="WORK_PREFERENCE",
                    content="Use concise routine summaries.",
                    display_label="Preference",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="TASK_MEMORY",
                    content="Owner-only ordinary task context.",
                    display_label="Task",
                    source="telegram_text",
                    status="ACTIVE",
                ),
            ]
        )
        session.flush()
        caregiver = run_telegram_policy_chain(
            update=build_update("Start the routine", 99112),
            settings=Settings(),
            session=session,
            memory_actor_role="care_recipient",
            memory_target_scope="caregiver",
            memory_allowed_use="caregiver_context",
        )
        routine = run_telegram_policy_chain(
            update=build_update("Run the routine", 99112),
            settings=Settings(),
            session=session,
            memory_actor_role="routine",
            memory_target_scope="routine",
            memory_allowed_use="routine_context",
        )

    assert [item.memory_type for item in caregiver.memory_context.projections] == ["BOUNDARY_MEMORY"]
    assert [item.memory_type for item in routine.memory_context.projections] == [
        "BOUNDARY_MEMORY",
        "WORK_PREFERENCE",
    ]
    assert all(item.memory_type != "TASK_MEMORY" for item in caregiver.memory_context.projections)
    assert all(item.memory_type != "TASK_MEMORY" for item in routine.memory_context.projections)


@pytest.mark.anyio
async def test_preflight_stopped_routine_does_not_invoke_99p_or_hermes_adapter(client, monkeypatch):
    def fail_if_called(**kwargs):
        raise AssertionError("99P projection runtime must not run before successful preflight.")

    monkeypatch.setattr("app.telegram_policy_chain.project_memory", fail_if_called)
    with client.app.state.db.session() as session:
        run = execute_routine_locally(
            definition=RoutineDefinition(
                routine_id="stopped",
                label="Stopped",
                trigger_text="Stop",
                wake_signal_present=False,
            ),
            update=build_update("Stop"),
            settings=Settings(),
            session=session,
        )

    assert run.preflight.policy_chain_routed is False
    assert run.policy_result.memory_context.projections == ()
    assert run.task_run_record.hermes_adapter_called is False


def test_runtime_has_no_network_or_external_execution_imports_and_100p_is_unauthorized():
    runtime = RUNTIME_PATH.read_text()
    spec = SPEC_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    for forbidden in ["import requests", "import httpx", "import urllib", "import socket", "import subprocess"]:
        assert forbidden not in runtime
    assert "100P and later: unauthorized" in spec
    assert '"stage_100p_and_later_authorized":false' in roadmap
