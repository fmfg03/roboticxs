from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.followup_completion_loop import FOLLOWUP_COMPLETION_LOOP_STAGE, FollowUpCompletionLoopRegistry, FollowUpCompletionLoopRouteRecord
from app.telegram_async_result_delivery import OWNER_ASYNC_RESULT_NOTIFICATION, TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE, TelegramAsyncResultDeliveryRecord


FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE = "114P"
ALLOWED_ACKNOWLEDGEMENT_ACTIONS = frozenset(
    {
        "acknowledge_followup_result",
        "dismiss_followup_result",
        "request_followup_result_lineage_summary",
    }
)
ACKNOWLEDGEMENT_STATUSES = frozenset(
    {
        "acknowledged",
        "dismissed",
        "lineage_summary_requested",
        "blocked",
    }
)


@dataclass(frozen=True, slots=True)
class FollowUpResultAcknowledgementCallbackPayload:
    owner_id: str
    robot_id: str
    chat_id: str
    route_id: str
    delivery_record_id: str
    surface_id: str
    inbox_record_id: str
    event_candidate_id: str
    attempt_id: str
    delegation_id: str
    packet_id: str
    handle_id: str
    action: str


@dataclass(frozen=True, slots=True)
class FollowUpResultAcknowledgementRecord:
    acknowledgement_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    route_id: str
    delivery_record_id: str
    surface_id: str
    inbox_record_id: str
    event_candidate_id: str
    attempt_id: str
    delegation_id: str
    packet_id: str
    handle_id: str
    action: str
    status: str
    source_stage: str
    acknowledged_stage: str
    memory_mutation_allowed: bool
    new_delegation_allowed: bool
    external_write_allowed: bool
    live_send_allowed: bool
    acknowledgement_bound: bool
    dedupe_key: str
    response_text: str
    lineage_summary: str | None
    lineage_metadata: dict[str, object]
    created_at: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in ACKNOWLEDGEMENT_STATUSES:
            raise ValueError("Unsupported 114P acknowledgement status.")
        if self.status != "blocked" and self.action not in ALLOWED_ACKNOWLEDGEMENT_ACTIONS:
            raise ValueError("Unsupported 114P acknowledgement action.")
        if self.source_stage != FOLLOWUP_COMPLETION_LOOP_STAGE:
            raise ValueError("114P acknowledgements must originate from 113P routes.")
        if self.acknowledged_stage != FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE:
            raise ValueError("114P acknowledgements must identify the 114P stage.")
        if self.memory_mutation_allowed is not False:
            raise ValueError("114P acknowledgements must not authorize memory mutation.")
        if self.new_delegation_allowed is not False:
            raise ValueError("114P acknowledgements must not authorize new delegations.")
        if self.external_write_allowed is not False:
            raise ValueError("114P acknowledgements must not authorize external writes.")
        if self.live_send_allowed is not False:
            raise ValueError("114P acknowledgements must not authorize live send.")


@dataclass(frozen=True, slots=True)
class FollowUpResultAcknowledgementResponseEnvelope:
    channel: str
    chat_id: str
    text: str
    live_send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("114P only supports local Telegram-compatible acknowledgement envelopes.")
        if self.live_send_allowed is not False:
            raise ValueError("114P envelopes must keep live_send_allowed false.")


@dataclass(slots=True)
class FollowUpResultAcknowledgementRegistry:
    acknowledgements_by_id: dict[str, FollowUpResultAcknowledgementRecord] = field(default_factory=dict)

    def get_followup_result_acknowledgement(self, acknowledgement_id: str) -> FollowUpResultAcknowledgementRecord | None:
        return self.acknowledgements_by_id.get(acknowledgement_id)

    def store(self, record: FollowUpResultAcknowledgementRecord) -> FollowUpResultAcknowledgementRecord:
        self.acknowledgements_by_id[record.acknowledgement_id] = record
        return record

    def list_followup_result_acknowledgements(self) -> tuple[FollowUpResultAcknowledgementRecord, ...]:
        return tuple(self.acknowledgements_by_id[key] for key in sorted(self.acknowledgements_by_id))


def bind_followup_result_acknowledgement(
    *,
    route_registry: FollowUpCompletionLoopRegistry,
    callback_payload: FollowUpResultAcknowledgementCallbackPayload,
    registry: FollowUpResultAcknowledgementRegistry,
) -> FollowUpResultAcknowledgementRecord:
    if not isinstance(callback_payload, FollowUpResultAcknowledgementCallbackPayload):
        raise TypeError("114P acknowledgement binding requires a deterministic callback payload.")

    acknowledgement_id = _acknowledgement_id(callback_payload=callback_payload)
    existing = registry.get_followup_result_acknowledgement(acknowledgement_id)
    if existing is not None:
        return existing

    route = route_registry.get_followup_completion_route(callback_payload.route_id)
    if route is None:
        return registry.store(
            _blocked_record(
                callback_payload=callback_payload,
                rejection_reason="rejected_unknown_113p_route",
            )
        )

    delivery = route_registry.delivery_registry.get_delivery(callback_payload.delivery_record_id)
    if delivery is None:
        return registry.store(
            _blocked_record(
                callback_payload=callback_payload,
                route=route,
                rejection_reason="rejected_unknown_delivery_record",
            )
        )

    rejection_reason = _validation_error(
        route=route,
        delivery=delivery,
        callback_payload=callback_payload,
        route_registry=route_registry,
    )
    if rejection_reason is not None:
        return registry.store(
            _blocked_record(
                callback_payload=callback_payload,
                route=route,
                delivery=delivery,
                rejection_reason=rejection_reason,
            )
        )

    summary = _lineage_summary_text(route=route, delivery=delivery) if callback_payload.action == "request_followup_result_lineage_summary" else None
    return registry.store(
        FollowUpResultAcknowledgementRecord(
            acknowledgement_id=acknowledgement_id,
            owner_id=route.owner_id,
            robot_id=route.robot_id,
            chat_id=delivery.telegram_chat_id,
            route_id=route.route_id,
            delivery_record_id=delivery.delivery_id,
            surface_id=route.surface_id or "",
            inbox_record_id=route.inbox_record_id or "",
            event_candidate_id=route.event_candidate_id,
            attempt_id=route.attempt_id,
            delegation_id=route.delegation_id,
            packet_id=route.packet_id,
            handle_id=route.handle_id,
            action=callback_payload.action,
            status=_status_for_action(callback_payload.action),
            source_stage=FOLLOWUP_COMPLETION_LOOP_STAGE,
            acknowledged_stage=FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
            memory_mutation_allowed=False,
            new_delegation_allowed=False,
            external_write_allowed=False,
            live_send_allowed=False,
            acknowledgement_bound=True,
            dedupe_key=_dedupe_key(callback_payload=callback_payload),
            response_text=_response_text(action=callback_payload.action, summary=summary),
            lineage_summary=summary,
            lineage_metadata=_lineage_metadata(route=route, delivery=delivery, action=callback_payload.action),
            created_at=_created_at(registry=registry),
            rejection_reason=None,
        )
    )


def get_followup_result_acknowledgement(
    *,
    registry: FollowUpResultAcknowledgementRegistry,
    acknowledgement_id: str,
) -> FollowUpResultAcknowledgementRecord | None:
    return registry.get_followup_result_acknowledgement(acknowledgement_id)


def list_followup_result_acknowledgements(
    *,
    registry: FollowUpResultAcknowledgementRegistry,
) -> tuple[FollowUpResultAcknowledgementRecord, ...]:
    return registry.list_followup_result_acknowledgements()


def build_followup_result_acknowledgement_response_envelope(
    record: FollowUpResultAcknowledgementRecord,
) -> FollowUpResultAcknowledgementResponseEnvelope:
    return FollowUpResultAcknowledgementResponseEnvelope(
        channel="telegram",
        chat_id=record.chat_id,
        text=record.response_text,
        live_send_allowed=False,
    )


def _validation_error(
    *,
    route: FollowUpCompletionLoopRouteRecord,
    delivery: TelegramAsyncResultDeliveryRecord,
    callback_payload: FollowUpResultAcknowledgementCallbackPayload,
    route_registry: FollowUpCompletionLoopRegistry,
) -> str | None:
    if callback_payload.action not in ALLOWED_ACKNOWLEDGEMENT_ACTIONS:
        if "memory" in callback_payload.action:
            return "rejected_memory_mutation_action"
        if "external" in callback_payload.action or "write" in callback_payload.action:
            return "rejected_external_write_action"
        if "execute" in callback_payload.action or "followup_now" in callback_payload.action:
            return "rejected_new_followup_execution_action"
        return "rejected_unsupported_acknowledgement_action"
    if route.status != "routed":
        return "rejected_non_routed_113p_route"
    if route.routed_stage != FOLLOWUP_COMPLETION_LOOP_STAGE:
        return "rejected_non_113p_followup_completion_route"
    if route.delivery_record_id != delivery.delivery_id:
        return "rejected_delivery_route_lineage_mismatch"
    if delivery.status != "delivered":
        return "rejected_non_delivered_105p_delivery_record"
    if delivery.delivery_kind != OWNER_ASYNC_RESULT_NOTIFICATION:
        return "rejected_non_owner_followup_result_delivery"
    if delivery.lineage_summary.get("delivery_stage") != TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE:
        return "rejected_non_105p_delivery_record"
    if route.owner_id != callback_payload.owner_id or delivery.owner_id != callback_payload.owner_id:
        return "rejected_owner_mismatch"
    if route.robot_id != callback_payload.robot_id or delivery.robot_id != callback_payload.robot_id:
        return "rejected_robot_mismatch"
    if delivery.telegram_chat_id != callback_payload.chat_id:
        return "rejected_chat_mismatch"
    if route.surface_id != callback_payload.surface_id or delivery.surface_id != callback_payload.surface_id:
        return "rejected_surface_lineage_mismatch"
    if route.inbox_record_id != callback_payload.inbox_record_id:
        return "rejected_inbox_lineage_mismatch"
    if route.event_candidate_id != callback_payload.event_candidate_id:
        return "rejected_event_candidate_lineage_mismatch"
    if route.attempt_id != callback_payload.attempt_id:
        return "rejected_attempt_lineage_mismatch"
    if route.delegation_id != callback_payload.delegation_id:
        return "rejected_delegation_lineage_mismatch"
    if route.packet_id != callback_payload.packet_id:
        return "rejected_packet_lineage_mismatch"
    if route.handle_id != callback_payload.handle_id:
        return "rejected_handle_lineage_mismatch"
    if callback_payload.route_id != route.route_id or callback_payload.delivery_record_id != delivery.delivery_id:
        return "rejected_delivery_route_lineage_mismatch"
    if route.lineage_summary.get("followup_completion_loop_stage") != FOLLOWUP_COMPLETION_LOOP_STAGE:
        return "rejected_non_113p_followup_completion_route"
    upstream = route.lineage_summary.get("upstream_lineage")
    if not isinstance(upstream, dict):
        return "rejected_missing_100p_113p_lineage"
    if route_registry.get_surface(route.surface_id or "") is None:
        return "rejected_surface_lineage_mismatch"
    if route_registry.get_inbox_record(route.inbox_record_id or "") is None:
        return "rejected_inbox_lineage_mismatch"
    return None


def _status_for_action(action: str) -> str:
    if action == "acknowledge_followup_result":
        return "acknowledged"
    if action == "dismiss_followup_result":
        return "dismissed"
    if action == "request_followup_result_lineage_summary":
        return "lineage_summary_requested"
    raise ValueError("Unsupported 114P acknowledgement action.")


def _response_text(*, action: str, summary: str | None) -> str:
    if action == "acknowledge_followup_result":
        return "Follow-up result acknowledged locally. No new execution, memory action, or external write was started."
    if action == "dismiss_followup_result":
        return "Follow-up result dismissed locally. No new execution, memory action, or external write was started."
    if action == "request_followup_result_lineage_summary":
        return summary or "No lineage summary available."
    raise ValueError("Unsupported 114P acknowledgement action.")


def _lineage_summary_text(
    *,
    route: FollowUpCompletionLoopRouteRecord,
    delivery: TelegramAsyncResultDeliveryRecord,
) -> str:
    lines = [
        "Follow-up result lineage summary:",
        f"- Source stage: {route.source_stage}",
        f"- Completion loop stage: {route.routed_stage}",
        f"- Delivery stage: {delivery.lineage_summary.get('delivery_stage')}",
        f"- Event status: {route.event_status}",
        f"- Delegation: {route.delegation_id}",
        f"- Attempt: {route.attempt_id}",
        f"- Inbox record: {route.inbox_record_id}",
        f"- Surface: {route.surface_id}",
        f"- Delivery: {delivery.delivery_id}",
        "- No memory mutation, new delegation, external write, or live send was authorized.",
    ]
    return "\n".join(lines)


def _lineage_metadata(
    *,
    route: FollowUpCompletionLoopRouteRecord,
    delivery: TelegramAsyncResultDeliveryRecord,
    action: str,
) -> dict[str, object]:
    return {
        "acknowledgement_stage": FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
        "acknowledgement_action": action,
        "source_stage": route.source_stage,
        "route_stage": route.routed_stage,
        "delivery_stage": delivery.lineage_summary.get("delivery_stage"),
        "route_id": route.route_id,
        "delivery_record_id": delivery.delivery_id,
        "surface_id": route.surface_id,
        "inbox_record_id": route.inbox_record_id,
        "event_candidate_id": route.event_candidate_id,
        "attempt_id": route.attempt_id,
        "delegation_id": route.delegation_id,
        "packet_id": route.packet_id,
        "handle_id": route.handle_id,
        "owner_id": route.owner_id,
        "robot_id": route.robot_id,
        "chat_id": delivery.telegram_chat_id,
        "upstream_lineage": route.lineage_summary,
    }


def _blocked_record(
    *,
    callback_payload: FollowUpResultAcknowledgementCallbackPayload,
    rejection_reason: str,
    route: FollowUpCompletionLoopRouteRecord | None = None,
    delivery: TelegramAsyncResultDeliveryRecord | None = None,
) -> FollowUpResultAcknowledgementRecord:
    return FollowUpResultAcknowledgementRecord(
        acknowledgement_id=_acknowledgement_id(callback_payload=callback_payload),
        owner_id="" if route is None else route.owner_id,
        robot_id="" if route is None else route.robot_id,
        chat_id="" if delivery is None else delivery.telegram_chat_id,
        route_id=callback_payload.route_id,
        delivery_record_id=callback_payload.delivery_record_id,
        surface_id=callback_payload.surface_id,
        inbox_record_id=callback_payload.inbox_record_id,
        event_candidate_id=callback_payload.event_candidate_id,
        attempt_id=callback_payload.attempt_id,
        delegation_id=callback_payload.delegation_id,
        packet_id=callback_payload.packet_id,
        handle_id=callback_payload.handle_id,
        action=callback_payload.action,
        status="blocked",
        source_stage=FOLLOWUP_COMPLETION_LOOP_STAGE,
        acknowledged_stage=FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
        memory_mutation_allowed=False,
        new_delegation_allowed=False,
        external_write_allowed=False,
        live_send_allowed=False,
        acknowledgement_bound=False,
        dedupe_key=_dedupe_key(callback_payload=callback_payload),
        response_text="Follow-up result acknowledgement was rejected locally.",
        lineage_summary=None,
        lineage_metadata={
            "acknowledgement_stage": FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
            "route_id": callback_payload.route_id,
            "delivery_record_id": callback_payload.delivery_record_id,
        },
        created_at="ack_blocked_local",
        rejection_reason=rejection_reason,
    )


def _acknowledgement_id(
    *,
    callback_payload: FollowUpResultAcknowledgementCallbackPayload,
) -> str:
    return _stable_id(
        "followup_result_acknowledgement",
        callback_payload.route_id,
        callback_payload.delivery_record_id,
        callback_payload.surface_id,
        callback_payload.owner_id,
        callback_payload.robot_id,
        callback_payload.chat_id,
        callback_payload.action,
    )


def _dedupe_key(
    *,
    callback_payload: FollowUpResultAcknowledgementCallbackPayload,
) -> str:
    return _stable_id(
        "followup_result_acknowledgement_dedupe",
        callback_payload.route_id,
        callback_payload.delivery_record_id,
        callback_payload.action,
    )


def _created_at(*, registry: FollowUpResultAcknowledgementRegistry) -> str:
    return f"ack_local_{len(registry.acknowledgements_by_id) + 1:04d}"


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
