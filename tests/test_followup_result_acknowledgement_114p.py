from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.followup_result_acknowledgement import (
    FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
    FollowUpResultAcknowledgementCallbackPayload,
    FollowUpResultAcknowledgementRegistry,
    build_followup_result_acknowledgement_response_envelope,
    bind_followup_result_acknowledgement,
    get_followup_result_acknowledgement,
    list_followup_result_acknowledgements,
)
from tests.test_followup_completion_loop_113p import FollowUpCompletionLoopRegistry, routed_completion
from tests.test_telegram_result_acknowledgement_106p import delivered_record as generic_delivered_record


REPO_ROOT = Path(__file__).resolve().parents[1]
ACK_PATH = REPO_ROOT / "app/followup_result_acknowledgement.py"


def routed_delivery():
    route_registry = FollowUpCompletionLoopRegistry()
    route = routed_completion(route_registry=route_registry)
    delivery = route_registry.delivery_registry.get_delivery(route.delivery_record_id)
    assert delivery is not None
    return route, delivery, route_registry


def callback_payload(route, delivery, **overrides) -> FollowUpResultAcknowledgementCallbackPayload:
    values = {
        "owner_id": route.owner_id,
        "robot_id": route.robot_id,
        "chat_id": delivery.telegram_chat_id,
        "route_id": route.route_id,
        "delivery_record_id": delivery.delivery_id,
        "surface_id": route.surface_id,
        "inbox_record_id": route.inbox_record_id,
        "event_candidate_id": route.event_candidate_id,
        "attempt_id": route.attempt_id,
        "delegation_id": route.delegation_id,
        "packet_id": route.packet_id,
        "handle_id": route.handle_id,
        "action": "acknowledge_followup_result",
    }
    values.update(overrides)
    return FollowUpResultAcknowledgementCallbackPayload(**values)


def test_114p_acknowledge_callback_creates_local_acknowledgement_record():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "acknowledged"
    assert record.action == "acknowledge_followup_result"
    assert record.acknowledgement_bound is True
    assert record.live_send_allowed is False
    assert record.memory_mutation_allowed is False
    assert record.new_delegation_allowed is False
    assert record.external_write_allowed is False


def test_114p_dismiss_callback_creates_local_dismissed_record():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="dismiss_followup_result"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "dismissed"
    assert record.action == "dismiss_followup_result"
    assert "dismissed locally" in record.response_text


def test_114p_lineage_summary_callback_returns_safe_deterministic_summary():
    route, delivery, route_registry = routed_delivery()
    registry = FollowUpResultAcknowledgementRegistry()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="request_followup_result_lineage_summary"),
        registry=registry,
    )
    envelope = build_followup_result_acknowledgement_response_envelope(record)

    assert record.status == "lineage_summary_requested"
    assert record.lineage_summary is not None
    assert "Follow-up result lineage summary:" in record.lineage_summary
    assert "No memory mutation, new delegation, external write, or live send was authorized." in record.lineage_summary
    assert envelope.live_send_allowed is False
    assert envelope.text == record.response_text


def test_114p_repeated_acknowledgement_deduplicates_without_duplicate_records():
    route, delivery, route_registry = routed_delivery()
    registry = FollowUpResultAcknowledgementRegistry()
    payload = callback_payload(route, delivery)

    first = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )
    second = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )

    assert first == second
    assert len(list_followup_result_acknowledgements(registry=registry)) == 1
    assert get_followup_result_acknowledgement(
        registry=registry,
        acknowledgement_id=first.acknowledgement_id,
    ) == first


def test_114p_repeated_dismiss_deduplicates_without_duplicate_records():
    route, delivery, route_registry = routed_delivery()
    registry = FollowUpResultAcknowledgementRegistry()
    payload = callback_payload(route, delivery, action="dismiss_followup_result")

    first = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )
    second = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )

    assert first == second
    assert len(list_followup_result_acknowledgements(registry=registry)) == 1


def test_114p_repeated_lineage_summary_is_deterministic_and_side_effect_free():
    route, delivery, route_registry = routed_delivery()
    registry = FollowUpResultAcknowledgementRegistry()
    payload = callback_payload(route, delivery, action="request_followup_result_lineage_summary")

    first = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )
    second = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=payload,
        registry=registry,
    )

    assert first == second
    assert first.lineage_summary == second.lineage_summary
    assert len(route_registry.list_followup_completion_routes()) == 1
    assert len(route_registry.delivery_registry.list_deliveries()) == 1


def test_114p_wrong_owner_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, owner_id="other-owner"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_owner_mismatch"


def test_114p_wrong_robot_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, robot_id="other-robot"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_robot_mismatch"


def test_114p_wrong_chat_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, chat_id="other-chat"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_chat_mismatch"


def test_114p_unknown_delivery_record_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, delivery_record_id="delivery-missing"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unknown_delivery_record"


def test_114p_delivery_not_linked_to_113p_followup_completion_route_is_rejected():
    route, delivery, route_registry = routed_delivery()
    generic_delivery = generic_delivered_record()
    route_registry.delivery_registry.store(generic_delivery)

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, delivery_record_id=generic_delivery.delivery_id),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_delivery_route_lineage_mismatch"


def test_114p_mismatched_route_surface_delivery_lineage_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, surface_id="surface-other"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_surface_lineage_mismatch"


def test_114p_unsupported_acknowledgement_action_is_rejected():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="archive_followup_result"),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_unsupported_acknowledgement_action"


def test_114p_memory_mutation_followup_execution_and_external_write_actions_are_rejected():
    route, delivery, route_registry = routed_delivery()
    registry = FollowUpResultAcknowledgementRegistry()

    memory = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="memory_write_followup_result"),
        registry=registry,
    )
    execution = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="execute_followup_now"),
        registry=registry,
    )
    external = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action="external_write_followup_result"),
        registry=registry,
    )

    assert memory.rejection_reason == "rejected_memory_mutation_action"
    assert execution.rejection_reason == "rejected_new_followup_execution_action"
    assert external.rejection_reason == "rejected_external_write_action"


def test_114p_acknowledgement_preserves_100p_through_113p_lineage_without_new_side_effects():
    route, delivery, route_registry = routed_delivery()

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.source_stage == "113P"
    assert record.acknowledged_stage == FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE
    assert record.lineage_metadata["upstream_lineage"]["followup_completion_loop_stage"] == "113P"
    assert record.lineage_metadata["upstream_lineage"]["upstream_lineage"]["followup_execution_stage"] == "112P"


def test_114p_does_not_mutate_memory_or_create_followup_work_or_call_live_integrations():
    text = ACK_PATH.read_text()

    assert "MemoryCenter" not in text
    assert "memory proposal" not in text.lower()
    assert "register_async_delegation_handle" not in text
    assert "delegate_task" not in text
    assert "openai" not in text.lower()
    assert "anthropic" not in text.lower()
    assert "requests" not in text.lower()
    assert "httpx" not in text.lower()


def test_114p_rejects_non_routed_113p_records():
    route, delivery, route_registry = routed_delivery()
    blocked_route = replace(route, status="blocked", rejection_reason="blocked_105p_delivery_failed")
    route_registry.routes_by_id[route.route_id] = blocked_route

    record = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(blocked_route, delivery),
        registry=FollowUpResultAcknowledgementRegistry(),
    )

    assert record.status == "blocked"
    assert record.rejection_reason == "rejected_non_routed_113p_route"
