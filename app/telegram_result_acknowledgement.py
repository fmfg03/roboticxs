from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.telegram_async_result_delivery import OWNER_ASYNC_RESULT_NOTIFICATION, TelegramAsyncResultDeliveryRecord, TelegramAsyncResultDeliveryRegistry


TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE = "106P"
OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT = "OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT"
ACKNOWLEDGEMENT_STATUSES = frozenset({"recorded", "duplicate", "blocked"})
CALLBACK_ACTIONS = frozenset({"acknowledge", "dismiss", "view_lineage_summary", "request_followup_pending"})
CALLBACK_ACTION_ALIASES = {
    "request_followup": "request_followup_pending",
}


@dataclass(frozen=True, slots=True)
class TelegramResultCallbackPayload:
    delivery_id: str
    surface_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    action: str


@dataclass(frozen=True, slots=True)
class TelegramResultAcknowledgementRecord:
    acknowledgement_id: str
    delivery_id: str
    surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    callback_action: str
    status: str
    response_text: str
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status != "blocked" and self.callback_action not in CALLBACK_ACTIONS:
            raise ValueError("Unsupported Telegram result acknowledgement action.")
        if self.status not in ACKNOWLEDGEMENT_STATUSES:
            raise ValueError("Unsupported Telegram result acknowledgement status.")


@dataclass(frozen=True, slots=True)
class TelegramAcknowledgementResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("106P only supports local Telegram-compatible acknowledgement envelopes.")
        if self.send_allowed is not False:
            raise ValueError("106P acknowledgement envelopes must not authorize sending.")


@dataclass(slots=True)
class TelegramResultAcknowledgementRegistry:
    acknowledgements_by_id: dict[str, TelegramResultAcknowledgementRecord] = field(default_factory=dict)

    def get_acknowledgement(self, acknowledgement_id: str) -> TelegramResultAcknowledgementRecord | None:
        return self.acknowledgements_by_id.get(acknowledgement_id)

    def store(self, record: TelegramResultAcknowledgementRecord) -> TelegramResultAcknowledgementRecord:
        self.acknowledgements_by_id[record.acknowledgement_id] = record
        return record

    def list_acknowledgements(self) -> tuple[TelegramResultAcknowledgementRecord, ...]:
        return tuple(self.acknowledgements_by_id.values())


def bind_telegram_result_acknowledgement(
    *,
    delivery_registry: TelegramAsyncResultDeliveryRegistry,
    callback_payload: TelegramResultCallbackPayload,
    registry: TelegramResultAcknowledgementRegistry,
) -> TelegramResultAcknowledgementRecord:
    if not isinstance(callback_payload, TelegramResultCallbackPayload):
        raise TypeError("106P acknowledgement binding requires a deterministic TelegramResultCallbackPayload.")

    callback_action = _normalize_callback_action(callback_payload.action)
    acknowledgement_id = _acknowledgement_id(
        delivery_id=callback_payload.delivery_id,
        surface_id=callback_payload.surface_id,
        owner_id=callback_payload.owner_id,
        robot_id=callback_payload.robot_id,
        telegram_chat_id=callback_payload.telegram_chat_id,
        callback_action=callback_action,
    )
    existing = registry.get_acknowledgement(acknowledgement_id)
    if existing is not None:
        return existing

    delivery_record = delivery_registry.get_delivery(callback_payload.delivery_id)
    if delivery_record is None:
        return registry.store(
            _blocked_record(
                callback_payload=callback_payload,
                callback_action=callback_action,
                rejection_reason="rejected_unknown_delivery_id",
            )
        )

    rejection_reason = _validate_callback_binding(
        delivery_record=delivery_record,
        callback_payload=callback_payload,
        callback_action=callback_action,
    )
    if rejection_reason is not None:
        return registry.store(
            _blocked_record(
                callback_payload=callback_payload,
                callback_action=callback_action,
                rejection_reason=rejection_reason,
                delivery_record=delivery_record,
            )
        )

    return registry.store(
        TelegramResultAcknowledgementRecord(
            acknowledgement_id=acknowledgement_id,
            delivery_id=delivery_record.delivery_id,
            surface_id=delivery_record.surface_id,
            inbox_record_id=delivery_record.inbox_record_id,
            owner_id=delivery_record.owner_id,
            robot_id=delivery_record.robot_id,
            telegram_chat_id=delivery_record.telegram_chat_id,
            callback_action=callback_action,
            status="recorded",
            response_text=_response_text(delivery_record=delivery_record, callback_action=callback_action),
            lineage_summary=_lineage_summary(delivery_record=delivery_record, callback_action=callback_action),
            rejection_reason=None,
        )
    )


def build_safe_lineage_summary(delivery_record: TelegramAsyncResultDeliveryRecord) -> str:
    upstream = delivery_record.lineage_summary.get("upstream_lineage")
    route_summary = _safe_route_summary(upstream)
    cost_summary = _safe_cost_summary(upstream)

    lines = [
        "Resumen de trazabilidad:",
        "- Resultado generado desde una tarea async aceptada.",
        "- Entregado a tu canal Telegram autorizado.",
    ]
    if cost_summary or route_summary:
        detail = "Costo y ruta/modelo preservados internamente."
        if cost_summary and route_summary:
            detail = f"Costo {cost_summary} y ruta/modelo {route_summary} preservados internamente."
        elif cost_summary:
            detail = f"Costo {cost_summary} preservado internamente."
        elif route_summary:
            detail = f"Ruta/modelo {route_summary} preservados internamente."
        lines.append(f"- {detail}")
    else:
        lines.append("- Costo y ruta/modelo preservados internamente.")
    lines.append("- No se ejecuto ninguna accion externa.")
    return "\n".join(lines)


def build_acknowledgement_response_envelope(
    acknowledgement_record: TelegramResultAcknowledgementRecord,
) -> TelegramAcknowledgementResponseEnvelope:
    return TelegramAcknowledgementResponseEnvelope(
        channel="telegram",
        telegram_chat_id=acknowledgement_record.telegram_chat_id,
        text=acknowledgement_record.response_text,
        send_allowed=False,
    )


def _normalize_callback_action(action: str) -> str:
    normalized = CALLBACK_ACTION_ALIASES.get(action, action)
    if normalized not in CALLBACK_ACTIONS:
        return normalized
    return normalized


def _validate_callback_binding(
    *,
    delivery_record: TelegramAsyncResultDeliveryRecord,
    callback_payload: TelegramResultCallbackPayload,
    callback_action: str,
) -> str | None:
    if delivery_record.delivery_kind != OWNER_ASYNC_RESULT_NOTIFICATION:
        return "rejected_non_owner_async_result_notification"
    if delivery_record.status == "blocked":
        return "rejected_blocked_delivery_record"
    if delivery_record.status == "failed":
        return "rejected_failed_delivery_record"
    if delivery_record.status != "delivered":
        return "rejected_non_delivered_record"
    if callback_action not in CALLBACK_ACTIONS:
        return "rejected_unknown_callback_action"
    if callback_payload.owner_id != delivery_record.owner_id:
        return "rejected_owner_mismatch"
    if callback_payload.robot_id != delivery_record.robot_id:
        return "rejected_robot_mismatch"
    if callback_payload.telegram_chat_id != delivery_record.telegram_chat_id:
        return "rejected_chat_mismatch"
    if callback_payload.surface_id != delivery_record.surface_id:
        return "rejected_surface_mismatch"
    return None


def _response_text(*, delivery_record: TelegramAsyncResultDeliveryRecord, callback_action: str) -> str:
    if callback_action == "acknowledge":
        return "Listo. Marque este resultado como revisado."
    if callback_action == "dismiss":
        return "Listo. Descarte este resultado de tu vista."
    if callback_action == "view_lineage_summary":
        return build_safe_lineage_summary(delivery_record)
    if callback_action == "request_followup_pending":
        return "Registre tu solicitud de seguimiento como pendiente. En esta version no ejecuto seguimiento automatico."
    raise ValueError("Unsupported callback action.")


def _lineage_summary(
    *,
    delivery_record: TelegramAsyncResultDeliveryRecord,
    callback_action: str,
) -> dict[str, object]:
    return {
        "acknowledgement_stage": TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE,
        "callback_category": OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT,
        "callback_action": callback_action,
        "delivery_stage": delivery_record.lineage_summary.get("delivery_stage"),
        "delivery_id": delivery_record.delivery_id,
        "surface_id": delivery_record.surface_id,
        "inbox_record_id": delivery_record.inbox_record_id,
        "owner_id": delivery_record.owner_id,
        "robot_id": delivery_record.robot_id,
        "telegram_chat_id": delivery_record.telegram_chat_id,
        "upstream_lineage": delivery_record.lineage_summary,
    }


def _blocked_record(
    *,
    callback_payload: TelegramResultCallbackPayload,
    callback_action: str,
    rejection_reason: str,
    delivery_record: TelegramAsyncResultDeliveryRecord | None = None,
) -> TelegramResultAcknowledgementRecord:
    return TelegramResultAcknowledgementRecord(
        acknowledgement_id=_acknowledgement_id(
            delivery_id=callback_payload.delivery_id,
            surface_id=callback_payload.surface_id,
            owner_id=callback_payload.owner_id,
            robot_id=callback_payload.robot_id,
            telegram_chat_id=callback_payload.telegram_chat_id,
            callback_action=callback_action,
        ),
        delivery_id=callback_payload.delivery_id,
        surface_id=callback_payload.surface_id,
        inbox_record_id="" if delivery_record is None else delivery_record.inbox_record_id,
        owner_id=callback_payload.owner_id,
        robot_id=callback_payload.robot_id,
        telegram_chat_id=callback_payload.telegram_chat_id,
        callback_action=callback_action,
        status="blocked",
        response_text="No pude registrar esa interaccion en esta version.",
        lineage_summary={
            "acknowledgement_stage": TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE,
            "callback_category": OWNER_ASYNC_RESULT_ACKNOWLEDGEMENT,
            "callback_action": callback_action,
            "delivery_id": callback_payload.delivery_id,
            "surface_id": callback_payload.surface_id,
            "owner_id": callback_payload.owner_id,
            "robot_id": callback_payload.robot_id,
            "telegram_chat_id": callback_payload.telegram_chat_id,
            "upstream_lineage": None if delivery_record is None else delivery_record.lineage_summary,
        },
        rejection_reason=rejection_reason,
    )


def _acknowledgement_id(
    *,
    delivery_id: str,
    surface_id: str,
    owner_id: str,
    robot_id: str,
    telegram_chat_id: str,
    callback_action: str,
) -> str:
    return "telegram_result_ack_" + uuid5(
        NAMESPACE_URL,
        "|".join([delivery_id, surface_id, owner_id, robot_id, telegram_chat_id, callback_action]),
    ).hex[:12]


def _safe_route_summary(upstream: object) -> str | None:
    if not isinstance(upstream, dict):
        return None
    cost_evidence = upstream.get("cost_preflight_evidence")
    if not isinstance(cost_evidence, dict):
        return None
    route_decision = cost_evidence.get("route_decision")
    route_mode = None
    request_evidence = upstream.get("request_evidence")
    if isinstance(request_evidence, dict):
        requested_route_mode = request_evidence.get("requested_route_mode")
        if isinstance(requested_route_mode, str) and requested_route_mode:
            route_mode = requested_route_mode
    selected_model_id = None
    if isinstance(route_decision, dict):
        route_model = route_decision.get("selected_model_id")
        if isinstance(route_model, str) and route_model:
            selected_model_id = route_model
    parts = [part for part in (route_mode, selected_model_id) if part]
    return " / ".join(parts) if parts else None


def _safe_cost_summary(upstream: object) -> str | None:
    if not isinstance(upstream, dict):
        return None
    cost_evidence = upstream.get("cost_preflight_evidence")
    if not isinstance(cost_evidence, dict):
        return None
    estimated_cost = cost_evidence.get("estimated_cost_usd")
    if isinstance(estimated_cost, (int, float)):
        return f"${estimated_cost:.2f}"
    return None
