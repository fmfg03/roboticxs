from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import NAMESPACE_URL, uuid5

from app.async_delegation_authority import (
    AsyncDelegationAuthorityState,
    AsyncDelegationCompletionEvent,
    serialize_async_delegation_authority_state,
)
from app.async_delegation_inbox import (
    AsyncDelegationCompletionInbox,
    AsyncDelegationInboxRecord,
    AsyncDelegationRegistry,
    create_async_delegation_registry,
)
from app.async_result_surface import AsyncResultSurface, build_async_result_surface
from app.followup_delegation_authority import FollowUpDelegationRegistry, FollowUpDelegationRequestRecord
from app.followup_execution_skeleton import (
    FOLLOWUP_EXECUTION_SKELETON_STAGE,
    FollowUpExecutionAttemptRecord,
    FollowUpExecutionAttemptRegistry,
)
from app.telegram_async_result_delivery import (
    TelegramAsyncResultDeliveryRecord,
    TelegramAsyncResultDeliveryRegistry,
    TelegramAsyncResultTransport,
    TelegramOwnerBinding,
    deliver_async_result_surface_to_telegram,
)


FOLLOWUP_COMPLETION_LOOP_STAGE = "113P"
ROUTE_STATUSES = frozenset({"routed", "blocked"})
ROUTABLE_ATTEMPT_STATUSES = frozenset({"completed_candidate", "failed_candidate"})
DELIVERED_TRANSPORT_KIND = "injected_local_only"
FORBIDDEN_REQUEST_FLAGS = frozenset(
    {
        "authority_expansion_requested",
        "live_dispatch_requested",
        "requires_tool_call",
        "tool_call_requested",
        "requires_model_call",
        "model_call_requested",
        "requires_memory_mutation",
        "memory_mutation_requested",
        "requires_external_effect",
        "external_effect_requested",
        "requires_telegram_send",
        "telegram_send_requested",
        "bind_telegram_callback_requested",
        "acknowledgement_binding_requested",
    }
)


@dataclass(frozen=True, slots=True)
class FollowUpCompletionLoopRouteRecord:
    route_id: str
    owner_id: str
    robot_id: str
    delegation_id: str
    packet_id: str
    handle_id: str
    attempt_id: str
    event_candidate_id: str
    event_status: str
    source_stage: str
    routed_stage: str
    inbox_record_id: str | None
    surface_id: str | None
    delivery_record_id: str | None
    send_transport: str | None
    live_send_allowed: bool
    acknowledgement_bound: bool
    memory_mutation_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str
    status: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in ROUTE_STATUSES:
            raise ValueError("Unsupported 113P follow-up completion loop route status.")
        if self.routed_stage != FOLLOWUP_COMPLETION_LOOP_STAGE:
            raise ValueError("113P route records must identify the 113P stage.")
        if self.live_send_allowed is not False:
            raise ValueError("113P route records must not authorize live sending.")
        if self.acknowledgement_bound is not False:
            raise ValueError("113P route records must not bind acknowledgement behavior.")
        if self.memory_mutation_allowed is not False:
            raise ValueError("113P route records must not authorize memory mutation.")


@dataclass(slots=True)
class FollowUpCompletionLoopRegistry:
    routes_by_id: dict[str, FollowUpCompletionLoopRouteRecord] = field(default_factory=dict)
    inbox: AsyncDelegationCompletionInbox = field(default_factory=AsyncDelegationCompletionInbox)
    delivery_registry: TelegramAsyncResultDeliveryRegistry = field(default_factory=TelegramAsyncResultDeliveryRegistry)
    surface_by_id: dict[str, AsyncResultSurface] = field(default_factory=dict)
    inbox_record_by_id: dict[str, AsyncDelegationInboxRecord] = field(default_factory=dict)
    authority_state_by_route_id: dict[str, AsyncDelegationAuthorityState] = field(default_factory=dict)

    def get_followup_completion_route(self, route_id: str) -> FollowUpCompletionLoopRouteRecord | None:
        return self.routes_by_id.get(route_id)

    def list_followup_completion_routes(self) -> tuple[FollowUpCompletionLoopRouteRecord, ...]:
        return tuple(self.routes_by_id[key] for key in sorted(self.routes_by_id))

    def get_surface(self, surface_id: str) -> AsyncResultSurface | None:
        return self.surface_by_id.get(surface_id)

    def get_inbox_record(self, inbox_record_id: str) -> AsyncDelegationInboxRecord | None:
        return self.inbox_record_by_id.get(inbox_record_id)

    def store(
        self,
        *,
        route: FollowUpCompletionLoopRouteRecord,
        inbox_record: AsyncDelegationInboxRecord | None = None,
        surface: AsyncResultSurface | None = None,
        delivery: TelegramAsyncResultDeliveryRecord | None = None,
        authority_state: AsyncDelegationAuthorityState | None = None,
        inbox: AsyncDelegationCompletionInbox | None = None,
    ) -> FollowUpCompletionLoopRouteRecord:
        self.routes_by_id[route.route_id] = route
        if inbox_record is not None:
            self.inbox_record_by_id[inbox_record.inbox_record_id] = inbox_record
        if surface is not None:
            self.surface_by_id[surface.surface_id] = surface
        if delivery is not None:
            self.delivery_registry.store(delivery)
        if authority_state is not None:
            self.authority_state_by_route_id[route.route_id] = authority_state
        if inbox is not None:
            self.inbox = inbox
        return route


def route_followup_execution_candidate(
    *,
    attempt_record: object,
    attempt_registry: FollowUpExecutionAttemptRegistry,
    followup_registry: FollowUpDelegationRegistry,
    route_registry: FollowUpCompletionLoopRegistry,
    owner_binding: TelegramOwnerBinding | None,
    transport: TelegramAsyncResultTransport,
) -> FollowUpCompletionLoopRouteRecord:
    if not isinstance(attempt_record, FollowUpExecutionAttemptRecord):
        route_id = _stable_id("followup_completion_route", "unknown")
        existing = route_registry.get_followup_completion_route(route_id)
        if existing is not None:
            return existing
        return route_registry.store(
            route=_blocked_route(
                route_id=route_id,
                attempt_record=None,
                rejection_reason="blocked_unknown_112p_attempt_record",
            )
        )

    route_id = _route_id(attempt_record=attempt_record)
    existing = route_registry.get_followup_completion_route(route_id)
    if existing is not None:
        return existing

    rejection_reason = _route_block_reason(
        attempt_record=attempt_record,
        attempt_registry=attempt_registry,
        followup_registry=followup_registry,
        owner_binding=owner_binding,
    )
    if rejection_reason is not None:
        return route_registry.store(
            route=_blocked_route(
                route_id=route_id,
                attempt_record=attempt_record,
                rejection_reason=rejection_reason,
            )
        )

    delegation_record = followup_registry.get_record(attempt_record.followup_delegation_id)
    authority_state = followup_registry.get_authority_state(attempt_record.followup_delegation_id)
    assert delegation_record is not None
    assert authority_state is not None
    event = _event_candidate(attempt_record=attempt_record)
    assert event is not None

    receipt = route_registry.inbox.receive_event(
        event=event,
        registry=create_async_delegation_registry(authority_state),
    )
    if receipt.record.status != "accepted":
        return route_registry.store(
            route=_blocked_route(
                route_id=route_id,
                attempt_record=attempt_record,
                rejection_reason=receipt.record.reason or "blocked_103p_inbox_rejected_candidate",
            ),
            inbox_record=receipt.record,
            inbox=receipt.inbox,
        )

    updated_authority_state = receipt.registry.authority_states[0]
    followup_registry.authority_states_by_id[attempt_record.followup_delegation_id] = updated_authority_state
    surface = build_async_result_surface(receipt.record)
    if surface is None:
        return route_registry.store(
            route=_blocked_route(
                route_id=route_id,
                attempt_record=attempt_record,
                rejection_reason="blocked_missing_104p_surface",
            ),
            inbox_record=receipt.record,
            inbox=receipt.inbox,
            authority_state=updated_authority_state,
        )

    delivery = deliver_async_result_surface_to_telegram(
        surface=surface,
        owner_binding=owner_binding,
        transport=transport,
        registry=route_registry.delivery_registry,
        telegram_chat_id=attempt_record.telegram_chat_id,
    )
    if delivery.status != "delivered":
        return route_registry.store(
            route=_blocked_route(
                route_id=route_id,
                attempt_record=attempt_record,
                rejection_reason=delivery.rejection_reason or "blocked_105p_delivery_failed",
            ),
            inbox_record=receipt.record,
            surface=surface,
            delivery=delivery,
            authority_state=updated_authority_state,
            inbox=receipt.inbox,
        )

    route = FollowUpCompletionLoopRouteRecord(
        route_id=route_id,
        owner_id=attempt_record.owner_id,
        robot_id=attempt_record.robot_id,
        delegation_id=attempt_record.followup_delegation_id,
        packet_id=attempt_record.async_packet_id,
        handle_id=attempt_record.async_handle_id,
        attempt_id=attempt_record.execution_attempt_id,
        event_candidate_id=event.event_id,
        event_status=event.completion_status,
        source_stage=FOLLOWUP_EXECUTION_SKELETON_STAGE,
        routed_stage=FOLLOWUP_COMPLETION_LOOP_STAGE,
        inbox_record_id=receipt.record.inbox_record_id,
        surface_id=surface.surface_id,
        delivery_record_id=delivery.delivery_id,
        send_transport=DELIVERED_TRANSPORT_KIND,
        live_send_allowed=False,
        acknowledgement_bound=False,
        memory_mutation_allowed=False,
        dedupe_key=_dedupe_key(attempt_record=attempt_record, event=event),
        lineage_summary=_route_lineage_summary(
            attempt_record=attempt_record,
            delegation_record=delegation_record,
            authority_state=updated_authority_state,
            event=event,
            inbox_record=receipt.record,
            surface=surface,
            delivery=delivery,
        ),
        created_at=_created_at(route_registry=route_registry),
        status="routed",
        rejection_reason=None,
    )
    return route_registry.store(
        route=route,
        inbox_record=receipt.record,
        surface=surface,
        delivery=delivery,
        authority_state=updated_authority_state,
        inbox=receipt.inbox,
    )


def get_followup_completion_route(
    *,
    route_registry: FollowUpCompletionLoopRegistry,
    route_id: str,
) -> FollowUpCompletionLoopRouteRecord | None:
    return route_registry.get_followup_completion_route(route_id)


def list_followup_completion_routes(
    *,
    route_registry: FollowUpCompletionLoopRegistry,
) -> tuple[FollowUpCompletionLoopRouteRecord, ...]:
    return route_registry.list_followup_completion_routes()


def _route_block_reason(
    *,
    attempt_record: FollowUpExecutionAttemptRecord,
    attempt_registry: FollowUpExecutionAttemptRegistry,
    followup_registry: FollowUpDelegationRegistry,
    owner_binding: TelegramOwnerBinding | None,
) -> str | None:
    known_attempt = attempt_registry.get_record(attempt_record.execution_attempt_id)
    if known_attempt is None or known_attempt != attempt_record:
        return "blocked_unknown_112p_attempt"
    if attempt_record.status not in ROUTABLE_ATTEMPT_STATUSES:
        return f"blocked_unroutable_attempt_status_{attempt_record.status}"

    event = _event_candidate(attempt_record=attempt_record)
    if event is None:
        return "blocked_missing_event_candidate"
    if event.source_stage != FOLLOWUP_EXECUTION_SKELETON_STAGE:
        return "blocked_event_source_stage_mismatch"
    if event.completion_status not in {"completed", "failed"}:
        return "blocked_unsupported_event_type"
    if attempt_record.status == "completed_candidate" and event.completion_status != "completed":
        return "blocked_event_status_mismatch"
    if attempt_record.status == "failed_candidate" and event.completion_status != "failed":
        return "blocked_event_status_mismatch"
    if event.owner_id != attempt_record.owner_id:
        return "blocked_owner_mismatch"
    if event.robot_id != attempt_record.robot_id:
        return "blocked_robot_mismatch"
    if event.delegation_id != attempt_record.followup_delegation_id:
        return "blocked_delegation_id_mismatch"
    if event.handle_id != attempt_record.async_handle_id:
        return "blocked_handle_id_mismatch"
    if event.execution_authorized or event.provider_call_authorized or event.tool_authority_granted:
        return "blocked_live_execution_request"
    if event.external_effect_authorized or event.live_dispatch_authorized or event.authority_expanded:
        return "blocked_external_effect_request"
    if event.memory_access_expanded:
        return "blocked_memory_mutation_request"

    delegation_record = followup_registry.get_record(attempt_record.followup_delegation_id)
    if delegation_record is None:
        return "blocked_unknown_111p_followup_delegation"
    if delegation_record.status != "registered":
        return f"blocked_followup_delegation_status_{delegation_record.status}"
    if delegation_record.owner_id != attempt_record.owner_id:
        return "blocked_owner_mismatch"
    if delegation_record.robot_id != attempt_record.robot_id:
        return "blocked_robot_mismatch"
    if delegation_record.telegram_chat_id != attempt_record.telegram_chat_id:
        return "blocked_chat_mismatch"
    if delegation_record.async_packet_id != attempt_record.async_packet_id:
        return "blocked_packet_id_mismatch"
    if delegation_record.async_handle_id != attempt_record.async_handle_id:
        return "blocked_handle_id_mismatch"

    authority_state = followup_registry.get_authority_state(attempt_record.followup_delegation_id)
    if authority_state is None:
        return "blocked_missing_102p_async_lineage"
    authority_rejection = _authority_state_block_reason(
        attempt_record=attempt_record,
        authority_state=authority_state,
        event=event,
    )
    if authority_rejection is not None:
        return authority_rejection

    request_evidence = event.original_request_evidence
    if not request_evidence:
        return "blocked_missing_100p_112p_lineage"
    request_payload = request_evidence.get("request_payload")
    if not isinstance(request_payload, dict):
        return "blocked_missing_100p_112p_lineage"
    if request_payload.get("followup_task_class") != attempt_record.followup_task_class:
        return "blocked_task_class_mismatch"
    if request_payload.get("send_allowed") is not False:
        return "blocked_external_effect_request"
    for flag in FORBIDDEN_REQUEST_FLAGS:
        if bool(request_payload.get(flag)) or bool(request_evidence.get(flag)):
            if "memory_mutation" in flag:
                return "blocked_memory_mutation_request"
            if "acknowledgement" in flag or "callback" in flag:
                return "blocked_114p_acknowledgement_behavior"
            if "tool_call" in flag or "model_call" in flag:
                return "blocked_live_execution_request"
            if "telegram_send" in flag or "external_effect" in flag:
                return "blocked_external_effect_request"
            return "blocked_114p_acknowledgement_behavior"

    authority_request_evidence = authority_state.handle.original_request_evidence
    authority_request_payload = authority_request_evidence.get("request_payload")
    if not isinstance(authority_request_payload, dict):
        return "blocked_missing_100p_112p_lineage"
    for flag in FORBIDDEN_REQUEST_FLAGS:
        if bool(authority_request_payload.get(flag)) or bool(authority_request_evidence.get(flag)):
            if "memory_mutation" in flag:
                return "blocked_memory_mutation_request"
            if "acknowledgement" in flag or "callback" in flag:
                return "blocked_114p_acknowledgement_behavior"
            if "tool_call" in flag or "model_call" in flag:
                return "blocked_live_execution_request"
            if "telegram_send" in flag or "external_effect" in flag:
                return "blocked_external_effect_request"
            return "blocked_114p_acknowledgement_behavior"

    if owner_binding is None:
        return "blocked_unknown_telegram_binding"
    if owner_binding.channel != "telegram":
        return "blocked_non_telegram_binding"
    if owner_binding.enabled is not True:
        return "blocked_disabled_telegram_binding"
    if owner_binding.owner_id != attempt_record.owner_id:
        return "blocked_owner_mismatch"
    if owner_binding.robot_id != attempt_record.robot_id:
        return "blocked_robot_mismatch"
    if owner_binding.telegram_chat_id != attempt_record.telegram_chat_id:
        return "blocked_chat_mismatch"
    return None


def _authority_state_block_reason(
    *,
    attempt_record: FollowUpExecutionAttemptRecord,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
) -> str | None:
    if authority_state.stage != "102P":
        return "blocked_missing_102p_async_lineage"
    handle = authority_state.handle
    packet = authority_state.packet
    if handle is None:
        return "blocked_missing_102p_async_lineage"
    if packet.state != "registered" or handle.status != "registered":
        return "blocked_unroutable_async_handle_status"
    if packet.delegation_id != attempt_record.followup_delegation_id:
        return "blocked_delegation_id_mismatch"
    if f"{packet.delegation_id}:v{packet.packet_version}" != attempt_record.async_packet_id:
        return "blocked_packet_id_mismatch"
    if handle.handle_id != attempt_record.async_handle_id:
        return "blocked_handle_id_mismatch"
    if packet.owner_id != attempt_record.owner_id or handle.owner_id != attempt_record.owner_id:
        return "blocked_owner_mismatch"
    if packet.robot_id != attempt_record.robot_id or handle.robot_id != attempt_record.robot_id:
        return "blocked_robot_mismatch"
    if packet.execution_authorized or handle.execution_authorized:
        return "blocked_live_execution_request"
    if packet.provider_call_authorized or handle.provider_call_authorized:
        return "blocked_live_execution_request"
    if packet.external_effect_authorized or handle.external_effect_authorized:
        return "blocked_external_effect_request"
    if packet.live_dispatch_authorized or handle.live_dispatch_authorized or handle.dispatch_authorized:
        return "blocked_live_execution_request"
    if packet.authority_expanded or handle.authority_expanded:
        return "blocked_live_execution_request"
    if event.cost_preflight_evidence.get("request_id") != handle.cost_preflight_request_id:
        return "blocked_cost_preflight_request_mismatch"
    if event.cost_preflight_evidence.get("route_decision", {}).get("selected_model_id") != handle.selected_model_id:
        return "blocked_route_model_mismatch"
    approval_evidence = event.approval_evidence
    if handle.approval_evidence is None:
        if approval_evidence is not None:
            return "blocked_approval_evidence_mismatch"
        return None
    if approval_evidence != handle.approval_evidence:
        return "blocked_approval_evidence_mismatch"
    return None


def _event_candidate(
    *,
    attempt_record: FollowUpExecutionAttemptRecord,
) -> AsyncDelegationCompletionEvent | None:
    if attempt_record.status == "completed_candidate":
        return attempt_record.completion_event_candidate
    if attempt_record.status == "failed_candidate":
        return attempt_record.failure_event_candidate
    return None


def _route_lineage_summary(
    *,
    attempt_record: FollowUpExecutionAttemptRecord,
    delegation_record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
    inbox_record: AsyncDelegationInboxRecord,
    surface: AsyncResultSurface,
    delivery: TelegramAsyncResultDeliveryRecord,
) -> dict[str, object]:
    return {
        "followup_completion_loop_stage": FOLLOWUP_COMPLETION_LOOP_STAGE,
        "attempt_stage": FOLLOWUP_EXECUTION_SKELETON_STAGE,
        "followup_delegation_stage": delegation_record.lineage_summary.get("followup_delegation_stage"),
        "attempt_id": attempt_record.execution_attempt_id,
        "event_candidate_id": event.event_id,
        "event_status": event.completion_status,
        "async_authority_state": serialize_async_delegation_authority_state(authority_state),
        "inbox_record": {
            "inbox_record_id": inbox_record.inbox_record_id,
            "event_id": inbox_record.event_id,
            "status": inbox_record.status,
            "reason": inbox_record.reason,
            "event_kind": inbox_record.event_kind,
        },
        "surface_summary": {
            "surface_id": surface.surface_id,
            "status": surface.status,
            "title": surface.title,
            "summary": surface.summary,
        },
        "delivery_summary": {
            "delivery_id": delivery.delivery_id,
            "status": delivery.status,
            "telegram_chat_id": delivery.telegram_chat_id,
            "delivery_kind": delivery.delivery_kind,
        },
        "upstream_lineage": attempt_record.lineage_summary,
    }


def _blocked_route(
    *,
    route_id: str,
    attempt_record: FollowUpExecutionAttemptRecord | None,
    rejection_reason: str,
) -> FollowUpCompletionLoopRouteRecord:
    event = None if attempt_record is None else _event_candidate(attempt_record=attempt_record)
    return FollowUpCompletionLoopRouteRecord(
        route_id=route_id,
        owner_id="" if attempt_record is None else attempt_record.owner_id,
        robot_id="" if attempt_record is None else attempt_record.robot_id,
        delegation_id="" if attempt_record is None else attempt_record.followup_delegation_id,
        packet_id="" if attempt_record is None else attempt_record.async_packet_id,
        handle_id="" if attempt_record is None else attempt_record.async_handle_id,
        attempt_id="" if attempt_record is None else attempt_record.execution_attempt_id,
        event_candidate_id="" if event is None else event.event_id,
        event_status="" if event is None else event.completion_status,
        source_stage=FOLLOWUP_EXECUTION_SKELETON_STAGE,
        routed_stage=FOLLOWUP_COMPLETION_LOOP_STAGE,
        inbox_record_id=None,
        surface_id=None,
        delivery_record_id=None,
        send_transport=None,
        live_send_allowed=False,
        acknowledgement_bound=False,
        memory_mutation_allowed=False,
        dedupe_key=route_id,
        lineage_summary={
            "followup_completion_loop_stage": FOLLOWUP_COMPLETION_LOOP_STAGE,
            "upstream_lineage": None if attempt_record is None else attempt_record.lineage_summary,
        },
        created_at="route_blocked_local",
        status="blocked",
        rejection_reason=rejection_reason,
    )


def _route_id(*, attempt_record: FollowUpExecutionAttemptRecord) -> str:
    event = _event_candidate(attempt_record=attempt_record)
    return _stable_id(
        "followup_completion_route",
        attempt_record.execution_attempt_id,
        "" if event is None else event.event_id,
        attempt_record.async_handle_id,
        attempt_record.async_packet_id,
        attempt_record.followup_delegation_id,
    )


def _dedupe_key(
    *,
    attempt_record: FollowUpExecutionAttemptRecord,
    event: AsyncDelegationCompletionEvent,
) -> str:
    return _stable_id(
        "followup_completion_route_dedupe",
        attempt_record.execution_attempt_id,
        event.event_id,
        event.handle_id,
        event.delegation_id,
    )


def _created_at(*, route_registry: FollowUpCompletionLoopRegistry) -> str:
    return f"route_local_{len(route_registry.routes_by_id) + 1:04d}"


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
