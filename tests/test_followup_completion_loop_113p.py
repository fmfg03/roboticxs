from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.async_delegation_authority import serialize_async_delegation_authority_state
from app.followup_completion_loop import (
    FOLLOWUP_COMPLETION_LOOP_STAGE,
    DELIVERED_TRANSPORT_KIND,
    FollowUpCompletionLoopRegistry,
    get_followup_completion_route,
    list_followup_completion_routes,
    route_followup_execution_candidate,
)
from app.followup_execution_skeleton import FollowUpExecutionAttemptRegistry
from app.telegram_async_result_delivery import OWNER_ASYNC_RESULT_NOTIFICATION, TelegramOwnerBinding
from tests.test_followup_execution_skeleton_112p import (
    FakeTelegramTransport,
    authorization,
    approved_async_delegation_packet,
    budget_policy,
    compare_prior_version_record,
    create_followup_record,
    execute_record,
    fixture,
    selection,
    synthetic_preflight,
    task_cost_request,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
LOOP_PATH = REPO_ROOT / "app/followup_completion_loop.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-112p",
        "robot_id": "robot-112p",
        "telegram_chat_id": "telegram-chat-112p",
        "channel": "telegram",
        "enabled": True,
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def routed_completion(
    *,
    attempt=None,
    attempt_registry=None,
    followup_registry=None,
    binding=None,
    transport=None,
    route_registry=None,
):
    if attempt is None or attempt_registry is None or followup_registry is None:
        record, followup_registry = create_followup_record()
        attempt_registry = FollowUpExecutionAttemptRegistry()
        attempt = execute_record(
            record=record,
            registry=followup_registry,
            attempt_registry=attempt_registry,
            execution_fixture=fixture(),
        )
    binding = owner_binding() if binding is None else binding
    transport = FakeTelegramTransport() if transport is None else transport
    route_registry = FollowUpCompletionLoopRegistry() if route_registry is None else route_registry
    return route_followup_execution_candidate(
        attempt_record=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        route_registry=route_registry,
        owner_binding=binding,
        transport=transport,
    )


def test_113p_valid_112p_completion_candidate_routes_into_103p_104p_105p():
    route = routed_completion()

    assert route.status == "routed"
    assert route.event_status == "completed"
    assert route.inbox_record_id is not None
    assert route.surface_id is not None
    assert route.delivery_record_id is not None
    assert route.send_transport == DELIVERED_TRANSPORT_KIND


def test_113p_valid_112p_failure_candidate_routes_into_103p_104p_105p():
    record, followup_registry = compare_prior_version_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    route = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    )

    assert route.status == "routed"
    assert route.event_status == "failed"
    assert route.inbox_record_id is not None
    assert route.surface_id is not None
    assert route.delivery_record_id is not None


def test_113p_routed_records_preserve_100p_cost_model_lineage():
    route = routed_completion()

    lineage = route.lineage_summary["upstream_lineage"]["upstream_lineage"]
    assert lineage["cost_preflight_request_id"] == "cost-request-112p"
    assert lineage["cost_preflight_summary"]["route_decision"]["selected_model_id"] == "balanced_standard_v1"
    assert lineage["cost_preflight_summary"]["estimated_cost_usd"] > 0


def test_113p_routed_records_preserve_101p_approval_action_evidence_where_applicable():
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request, decision="require_confirmation")
    selected = selection(option_index=1)
    approval = approved_async_delegation_packet(
        selected,
        authorization(selected, approval_evidence_id=None),
        task_request,
        budget_policy(),
        preflight,
    )
    auth = authorization(selected, approval_evidence_id=approval.packet.packet_id)
    record, followup_registry = create_followup_record(
        selection_record=selected,
        auth=auth,
        task_request=task_request,
        preflight=preflight,
        approval=approval,
    )
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    route = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    )

    assert route.status == "routed"
    assert route.lineage_summary["upstream_lineage"]["upstream_lineage"]["approval_packet_id"] == approval.packet.packet_id
    assert route.lineage_summary["async_authority_state"]["completion_events"][-1]["approval_evidence"]["action_packet_id"] == approval.packet.packet_id


def test_113p_routed_records_preserve_102p_111p_112p_lineage():
    route = routed_completion()

    lineage = route.lineage_summary
    assert lineage["upstream_lineage"]["followup_delegation_id"]
    assert lineage["upstream_lineage"]["async_packet_id"] == route.packet_id
    assert lineage["upstream_lineage"]["async_handle_id"] == route.handle_id
    assert lineage["upstream_lineage"]["upstream_lineage"]["followup_delegation_stage"] == "111P"
    assert lineage["attempt_stage"] == "112P"
    assert lineage["event_candidate_id"] == route.event_candidate_id


def test_113p_duplicate_route_attempts_return_existing_route_without_duplicates():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    transport = FakeTelegramTransport()
    route_registry = FollowUpCompletionLoopRegistry()

    first = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        transport=transport,
        route_registry=route_registry,
    )
    second = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        transport=transport,
        route_registry=route_registry,
    )

    assert first == second
    assert len(route_registry.list_followup_completion_routes()) == 1
    assert len(route_registry.inbox.list_records()) == 1
    assert len(route_registry.delivery_registry.list_deliveries()) == 1
    assert len(transport.calls) == 1


def test_113p_rejects_candidates_without_known_112p_attempt():
    record, followup_registry = create_followup_record()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=FollowUpExecutionAttemptRegistry(),
        execution_fixture=fixture(),
    )
    route = routed_completion(
        attempt=attempt,
        attempt_registry=FollowUpExecutionAttemptRegistry(),
        followup_registry=followup_registry,
    )

    assert route.status == "blocked"
    assert route.rejection_reason == "blocked_unknown_112p_attempt"


def test_113p_rejects_attempts_without_known_111p_delegation():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    route = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=type(followup_registry)(),
    )

    assert route.status == "blocked"
    assert route.rejection_reason == "blocked_unknown_111p_followup_delegation"


def test_113p_rejects_owner_robot_delegation_packet_handle_mismatches():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )

    assert routed_completion(
        attempt=replace(attempt, owner_id="other-owner"),
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    ).rejection_reason == "blocked_unknown_112p_attempt"
    assert routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        binding=owner_binding(robot_id="other-robot"),
    ).rejection_reason == "blocked_robot_mismatch"

    event = attempt.completion_event_candidate
    assert event is not None
    tampered = replace(attempt, completion_event_candidate=replace(event, handle_id="other-handle"))
    attempt_registry.store(tampered)
    route = routed_completion(
        attempt=tampered,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    )
    assert route.status == "blocked"
    assert route.rejection_reason == "blocked_handle_id_mismatch"


def test_113p_rejects_unsupported_event_types():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    event = attempt.completion_event_candidate
    assert event is not None
    tampered = replace(attempt, completion_event_candidate=replace(event, completion_status="cancelled"))
    attempt_registry.store(tampered)
    route = routed_completion(
        attempt=tampered,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    )

    assert route.status == "blocked"
    assert route.rejection_reason == "blocked_unsupported_event_type"


def test_113p_rejects_live_execution_memory_mutation_and_acknowledgement_requests():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    event = attempt.completion_event_candidate
    assert event is not None

    live = replace(attempt, completion_event_candidate=replace(event, provider_call_authorized=True))
    attempt_registry.store(live)
    assert routed_completion(
        attempt=live,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    ).rejection_reason == "blocked_live_execution_request"

    memory = replace(attempt, completion_event_candidate=replace(event, memory_access_expanded=True))
    attempt_registry.store(memory)
    assert routed_completion(
        attempt=memory,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    ).rejection_reason == "blocked_memory_mutation_request"

    attempt_registry.store(attempt)
    state = followup_registry.get_authority_state(record.followup_delegation_id)
    assert state is not None and state.handle is not None
    followup_registry.authority_states_by_id[record.followup_delegation_id] = replace(
        state,
        handle=replace(
            state.handle,
            original_request_evidence={
                **state.handle.original_request_evidence,
                "request_payload": {
                    **state.handle.original_request_evidence["request_payload"],
                    "acknowledgement_binding_requested": True,
                },
            },
        ),
    )
    assert routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
    ).rejection_reason == "blocked_114p_acknowledgement_behavior"


def test_113p_uses_existing_104p_surface_and_105p_delivery_contracts():
    route_registry = FollowUpCompletionLoopRegistry()
    route = routed_completion(route_registry=route_registry)

    surface = route_registry.get_surface(route.surface_id)
    delivery = route_registry.delivery_registry.get_delivery(route.delivery_record_id)
    assert surface is not None
    assert delivery is not None
    assert surface.lineage_summary["inbox_stage"] == "103P"
    assert delivery.delivery_kind == OWNER_ASYNC_RESULT_NOTIFICATION
    assert delivery.telegram_chat_id == "telegram-chat-112p"


def test_113p_get_and_list_routes_are_deterministic():
    route_registry = FollowUpCompletionLoopRegistry()
    route = routed_completion(route_registry=route_registry)

    assert get_followup_completion_route(route_registry=route_registry, route_id=route.route_id) == route
    assert list_followup_completion_routes(route_registry=route_registry) == (route,)


def test_113p_updates_local_authority_state_through_103p_path():
    record, followup_registry = create_followup_record()
    attempt_registry = FollowUpExecutionAttemptRegistry()
    attempt = execute_record(
        record=record,
        registry=followup_registry,
        attempt_registry=attempt_registry,
        execution_fixture=fixture(),
    )
    route_registry = FollowUpCompletionLoopRegistry()
    route = routed_completion(
        attempt=attempt,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        route_registry=route_registry,
    )

    assert route.status == "routed"
    updated = followup_registry.get_authority_state(record.followup_delegation_id)
    assert updated is not None
    assert updated.packet.state == "completed"
    assert serialize_async_delegation_authority_state(updated)["completion_events"][-1]["event_id"] == route.event_candidate_id


def test_113p_does_not_call_live_telegram_models_tools_workers_or_memory():
    text = LOOP_PATH.read_text()

    for forbidden in ["openai.", "anthropic.", "requests.", "httpx.", "subprocess.", "asyncio.create_task", "memory_center", "memory_service", "telegram.Bot"]:
        assert forbidden not in text


def test_113p_114p_plus_remains_unauthorized():
    roadmap = ROADMAP_PATH.read_text()

    assert "116P and later remain unauthorized" in roadmap or "116P+ remains unauthorized" in roadmap
