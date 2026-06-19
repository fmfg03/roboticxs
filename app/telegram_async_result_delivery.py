from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from app.async_result_surface import (
    ACTION_KINDS,
    AsyncResultMessageEnvelope,
    AsyncResultSurface,
    render_async_result_surface_text,
)
from app.telegram_policy_chain import POLICY_CHAIN_STAGE


TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE = "105P"
OWNER_ASYNC_RESULT_NOTIFICATION = "OWNER_ASYNC_RESULT_NOTIFICATION"
DELIVERY_STATUSES = frozenset({"delivered", "duplicate", "blocked", "failed"})
PASSIVE_BUTTON_ACTION_KINDS = ACTION_KINDS
PASSIVE_BUTTON_LABELS = frozenset(
    {
        "Marcar revisado",
        "Descartar",
        "Pedir seguimiento",
        "Ver lineage",
        "Ver resumen de trazabilidad",
        "Acknowledge",
        "Dismiss",
        "Request follow-up",
        "View lineage summary",
    }
)


class TelegramAsyncResultTransport(Protocol):
    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict:
        ...


@dataclass(frozen=True, slots=True)
class TelegramOwnerBinding:
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    channel: str = "telegram"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class TelegramAsyncResultDeliveryRecord:
    delivery_id: str
    surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    delivery_kind: str
    status: str
    text: str
    button_labels: tuple[str, ...]
    lineage_summary: dict[str, object]
    transport_receipt: dict | None
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.delivery_kind != OWNER_ASYNC_RESULT_NOTIFICATION:
            raise ValueError("105P only supports owner async result notifications.")
        if self.status not in DELIVERY_STATUSES:
            raise ValueError("Unsupported Telegram async result delivery status.")


@dataclass(slots=True)
class TelegramAsyncResultDeliveryRegistry:
    deliveries_by_id: dict[str, TelegramAsyncResultDeliveryRecord] = field(default_factory=dict)

    def get_delivery(self, delivery_id: str) -> TelegramAsyncResultDeliveryRecord | None:
        return self.deliveries_by_id.get(delivery_id)

    def store(self, record: TelegramAsyncResultDeliveryRecord) -> TelegramAsyncResultDeliveryRecord:
        self.deliveries_by_id[record.delivery_id] = record
        return record

    def list_deliveries(self) -> tuple[TelegramAsyncResultDeliveryRecord, ...]:
        return tuple(self.deliveries_by_id.values())


def find_telegram_owner_binding(
    *,
    bindings: tuple[TelegramOwnerBinding, ...],
    owner_id: str | None,
    robot_id: str | None,
) -> TelegramOwnerBinding | None:
    for binding in bindings:
        if binding.owner_id == owner_id and binding.robot_id == robot_id:
            return binding
    return None


def deliver_async_result_surface_to_telegram(
    *,
    surface: AsyncResultSurface,
    owner_binding: TelegramOwnerBinding | None,
    transport: TelegramAsyncResultTransport,
    registry: TelegramAsyncResultDeliveryRegistry,
    telegram_chat_id: str | None = None,
) -> TelegramAsyncResultDeliveryRecord:
    if not isinstance(surface, AsyncResultSurface):
        raise TypeError("105P delivery requires a 104P AsyncResultSurface.")

    envelope = surface.telegram_envelope
    if envelope is None:
        return registry.store(_blocked_record(surface=surface, owner_binding=owner_binding, reason="rejected_missing_104p_envelope"))

    return deliver_async_result_message_envelope_to_telegram(
        surface=surface,
        envelope=envelope,
        owner_binding=owner_binding,
        transport=transport,
        registry=registry,
        telegram_chat_id=telegram_chat_id,
    )


def deliver_async_result_message_envelope_to_telegram(
    *,
    surface: AsyncResultSurface,
    envelope: AsyncResultMessageEnvelope,
    owner_binding: TelegramOwnerBinding | None,
    transport: TelegramAsyncResultTransport,
    registry: TelegramAsyncResultDeliveryRegistry,
    telegram_chat_id: str | None = None,
) -> TelegramAsyncResultDeliveryRecord:
    if not isinstance(surface, AsyncResultSurface):
        raise TypeError("105P delivery requires the source 104P AsyncResultSurface.")
    if not isinstance(envelope, AsyncResultMessageEnvelope):
        raise TypeError("105P delivery requires a 104P AsyncResultMessageEnvelope.")

    reason = _validate_delivery_request(surface=surface, envelope=envelope, owner_binding=owner_binding, telegram_chat_id=telegram_chat_id)
    if reason is not None:
        return registry.store(_blocked_record(surface=surface, owner_binding=owner_binding, reason=reason))

    assert owner_binding is not None
    target_chat_id = owner_binding.telegram_chat_id if telegram_chat_id is None else telegram_chat_id
    delivery_id = _delivery_id(
        surface=surface,
        envelope=envelope,
        telegram_chat_id=target_chat_id,
    )
    existing = registry.get_delivery(delivery_id)
    if existing is not None:
        return existing

    try:
        receipt = transport.deliver(target_chat_id, envelope.text, envelope.buttons)
    except Exception:
        return registry.store(
            _record(
                surface=surface,
                telegram_chat_id=target_chat_id,
                text=envelope.text,
                buttons=envelope.buttons,
                status="failed",
                transport_receipt=None,
                rejection_reason="transport_delivery_failed",
            )
        )

    return registry.store(
        _record(
            surface=surface,
            telegram_chat_id=target_chat_id,
            text=envelope.text,
            buttons=envelope.buttons,
            status="delivered",
            transport_receipt=receipt,
            rejection_reason=None,
        )
    )


def _validate_delivery_request(
    *,
    surface: AsyncResultSurface,
    envelope: AsyncResultMessageEnvelope,
    owner_binding: TelegramOwnerBinding | None,
    telegram_chat_id: str | None,
) -> str | None:
    if surface.status not in {"completed", "failed"}:
        return "rejected_non_deliverable_surface_status"
    if not surface.owner_id or not surface.robot_id:
        return "rejected_missing_owner_or_robot"
    if not _surface_has_accepted_lineage(surface):
        return "rejected_missing_103p_104p_lineage"
    if envelope.channel != "telegram":
        return "rejected_non_telegram_channel"
    if envelope.send_allowed is not False:
        return "rejected_send_allowed_envelope"
    if envelope.recipient_owner_id != surface.owner_id:
        return "rejected_owner_mismatch"
    if envelope.robot_id != surface.robot_id:
        return "rejected_robot_mismatch"
    if envelope.text != render_async_result_surface_text(surface):
        return "rejected_non_104p_rendered_text"
    if owner_binding is None:
        return "rejected_unknown_telegram_binding"
    if owner_binding.channel != "telegram":
        return "rejected_non_telegram_binding"
    if owner_binding.enabled is not True:
        return "rejected_disabled_telegram_binding"
    if owner_binding.owner_id != surface.owner_id:
        return "rejected_owner_mismatch"
    if owner_binding.robot_id != surface.robot_id:
        return "rejected_robot_mismatch"
    if not owner_binding.telegram_chat_id:
        return "rejected_unknown_telegram_recipient"
    if telegram_chat_id is not None and telegram_chat_id != owner_binding.telegram_chat_id:
        return "rejected_third_party_recipient"
    if not _buttons_are_passive(surface=surface, envelope=envelope):
        return "rejected_non_passive_buttons"
    return None


def _surface_has_accepted_lineage(surface: AsyncResultSurface) -> bool:
    lineage = surface.lineage_summary
    if lineage.get("inbox_stage") != "103P":
        return False
    if lineage.get("inbox_record_id") != surface.inbox_record_id:
        return False
    if lineage.get("source_stage") is None:
        return False
    request_evidence = lineage.get("request_evidence")
    cost_evidence = lineage.get("cost_preflight_evidence")
    approval_evidence = lineage.get("approval_evidence")
    if request_evidence is not None and not isinstance(request_evidence, dict):
        return False
    if cost_evidence is not None and not isinstance(cost_evidence, dict):
        return False
    if approval_evidence is not None and not isinstance(approval_evidence, dict):
        return False
    return True


def _buttons_are_passive(*, surface: AsyncResultSurface, envelope: AsyncResultMessageEnvelope) -> bool:
    allowed_labels = tuple(option.label for option in surface.action_options)
    if envelope.buttons != allowed_labels:
        return False
    for option in surface.action_options:
        if option.action_kind not in PASSIVE_BUTTON_ACTION_KINDS:
            return False
        if option.local_only is not True:
            return False
        if option.creates_authority is not False:
            return False
        if option.label not in PASSIVE_BUTTON_LABELS:
            return False
    return True


def _blocked_record(
    *,
    surface: AsyncResultSurface,
    owner_binding: TelegramOwnerBinding | None,
    reason: str,
) -> TelegramAsyncResultDeliveryRecord:
    return _record(
        surface=surface,
        telegram_chat_id="" if owner_binding is None else owner_binding.telegram_chat_id,
        text=render_async_result_surface_text(surface),
        buttons=tuple(option.label for option in surface.action_options),
        status="blocked",
        transport_receipt=None,
        rejection_reason=reason,
    )


def _record(
    *,
    surface: AsyncResultSurface,
    telegram_chat_id: str,
    text: str,
    buttons: tuple[str, ...],
    status: str,
    transport_receipt: dict | None,
    rejection_reason: str | None,
) -> TelegramAsyncResultDeliveryRecord:
    return TelegramAsyncResultDeliveryRecord(
        delivery_id=_delivery_id(
            surface=surface,
            envelope=surface.telegram_envelope,
            telegram_chat_id=telegram_chat_id,
        ),
        surface_id=surface.surface_id,
        inbox_record_id=surface.inbox_record_id,
        owner_id=surface.owner_id or "",
        robot_id=surface.robot_id or "",
        telegram_chat_id=telegram_chat_id,
        delivery_kind=OWNER_ASYNC_RESULT_NOTIFICATION,
        status=status,
        text=text,
        button_labels=buttons,
        lineage_summary={
            "delivery_stage": TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE,
            "surface_stage": "104P",
            "telegram_policy_boundary_stage": POLICY_CHAIN_STAGE,
            "surface_id": surface.surface_id,
            "inbox_record_id": surface.inbox_record_id,
            "owner_id": surface.owner_id,
            "robot_id": surface.robot_id,
            "request_id": surface.request_id,
            "upstream_lineage": surface.lineage_summary,
        },
        transport_receipt=transport_receipt,
        rejection_reason=rejection_reason,
    )


def _delivery_id(
    *,
    surface: AsyncResultSurface,
    envelope: AsyncResultMessageEnvelope | None,
    telegram_chat_id: str,
) -> str:
    text = render_async_result_surface_text(surface) if envelope is None else envelope.text
    text_hash = sha256(text.encode("utf-8")).hexdigest()[:16]
    return "telegram_async_delivery_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                surface.surface_id,
                surface.inbox_record_id,
                surface.owner_id or "",
                surface.robot_id or "",
                telegram_chat_id,
                OWNER_ASYNC_RESULT_NOTIFICATION,
                text_hash,
            ]
        ),
    ).hex[:12]
