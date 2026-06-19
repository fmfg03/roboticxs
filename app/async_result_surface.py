from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import NAMESPACE_URL, uuid5

from app.async_delegation_inbox import AsyncDelegationInboxRecord


ASYNC_RESULT_SURFACE_STAGE = "104P"
SURFACE_STATUSES = frozenset({"completed", "failed", "unavailable"})
ACTION_KINDS = frozenset({"acknowledge", "dismiss", "request_followup", "view_lineage_summary"})
USER_VISIBLE_ACTIONS = {
    "acknowledge": "Marcar revisado",
    "dismiss": "Descartar",
    "request_followup": "Pedir seguimiento",
    "view_lineage_summary": "Ver lineage",
}
PRIVATE_EVIDENCE_KEYS = frozenset(
    {
        "original_request_evidence",
        "cost_preflight_evidence",
        "approval_evidence",
        "request_snapshot",
        "packet",
        "handle",
        "trace_records",
    }
)


@dataclass(frozen=True, slots=True)
class AsyncResultActionOption:
    action_id: str
    label: str
    action_kind: str
    local_only: bool
    creates_authority: bool

    def __post_init__(self) -> None:
        if self.action_kind not in ACTION_KINDS:
            raise ValueError("Unsupported async result action kind.")
        if self.local_only is not True:
            raise ValueError("Async result actions must remain local-only.")
        if self.creates_authority is not False:
            raise ValueError("Async result actions must not create authority.")


@dataclass(frozen=True, slots=True)
class AsyncResultMessageEnvelope:
    channel: str
    recipient_owner_id: str | None
    robot_id: str | None
    text: str
    buttons: tuple[str, ...]
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("104P only supports local Telegram-compatible envelopes.")
        if self.send_allowed is not False:
            raise ValueError("104P envelopes must not authorize sending.")


@dataclass(frozen=True, slots=True)
class AsyncResultSurface:
    surface_id: str
    inbox_record_id: str
    handle_id: str | None
    owner_id: str | None
    robot_id: str | None
    request_id: str | None
    task_label: str
    status: str
    title: str
    summary: str
    cost_summary: str | None
    route_summary: str | None
    safety_note: str | None
    action_options: tuple[AsyncResultActionOption, ...]
    lineage_summary: dict[str, object]
    telegram_envelope: AsyncResultMessageEnvelope | None

    def __post_init__(self) -> None:
        if self.status not in SURFACE_STATUSES:
            raise ValueError("Surface status must be completed, failed, or unavailable.")


def build_async_result_surface(inbox_record: AsyncDelegationInboxRecord) -> AsyncResultSurface | None:
    if not isinstance(inbox_record, AsyncDelegationInboxRecord):
        raise TypeError("104P surfaces require a 103P inbox record.")
    if inbox_record.status == "quarantined":
        return None
    if inbox_record.status == "duplicate" and inbox_record.bound_completion_event is None:
        return None

    event = inbox_record.bound_completion_event
    if event is None:
        return None

    completion_status = str(event.get("completion_status") or inbox_record.event_kind)
    if completion_status not in {"completed", "failed"}:
        return None

    request_evidence = _dict_copy(event.get("original_request_evidence"))
    cost_evidence = _dict_copy(event.get("cost_preflight_evidence"))
    approval_evidence = _dict_copy(event.get("approval_evidence"))
    payload_summary = _dict_copy(event.get("completion_payload_summary"))

    task_label = _task_label(request_evidence)
    status = "completed" if completion_status == "completed" else "failed"
    title = "Resultado listo" if status == "completed" else "Resultado no disponible"
    summary = _surface_summary(
        status=status,
        payload_summary=payload_summary,
        reason_code=str(event.get("reason_code") or inbox_record.reason or ""),
    )
    route_summary = _route_summary(request_evidence=request_evidence, cost_evidence=cost_evidence)
    cost_summary = _cost_summary(cost_evidence)
    safety_note = _safety_note(status=status)
    action_options = _action_options(status=status)
    lineage_summary = {
        "inbox_stage": "103P",
        "inbox_record_id": inbox_record.inbox_record_id,
        "event_id": event.get("event_id"),
        "handle_id": inbox_record.handle_id,
        "delegation_id": event.get("delegation_id"),
        "request_id": inbox_record.request_id,
        "cost_preflight_request_id": None if cost_evidence is None else cost_evidence.get("request_id"),
        "selected_provider_id": _route_value(cost_evidence, "selected_provider_id"),
        "selected_model_id": _route_value(cost_evidence, "selected_model_id"),
        "request_evidence": request_evidence,
        "cost_preflight_evidence": cost_evidence,
        "approval_evidence": approval_evidence,
        "source_stage": event.get("source_stage"),
    }
    surface = AsyncResultSurface(
        surface_id=_stable_id(
            "async_result_surface",
            event.get("event_id"),
            inbox_record.handle_id,
            inbox_record.request_id,
            status,
            task_label,
            summary,
        ),
        inbox_record_id=inbox_record.inbox_record_id,
        handle_id=inbox_record.handle_id,
        owner_id=inbox_record.owner_id,
        robot_id=inbox_record.robot_id,
        request_id=inbox_record.request_id,
        task_label=task_label,
        status=status,
        title=title,
        summary=summary,
        cost_summary=cost_summary,
        route_summary=route_summary,
        safety_note=safety_note,
        action_options=action_options,
        lineage_summary=lineage_summary,
        telegram_envelope=None,
    )
    return replace(surface, telegram_envelope=build_async_result_message_envelope(surface=surface, channel="telegram"))


def build_async_result_message_envelope(
    surface: AsyncResultSurface,
    *,
    channel: str = "telegram",
) -> AsyncResultMessageEnvelope:
    return AsyncResultMessageEnvelope(
        channel=channel,
        recipient_owner_id=surface.owner_id,
        robot_id=surface.robot_id,
        text=render_async_result_surface_text(surface),
        buttons=tuple(option.label for option in surface.action_options),
        send_allowed=False,
    )


def render_async_result_surface_text(surface: AsyncResultSurface) -> str:
    lines = [surface.title, "", f"Tarea: {surface.task_label}", f"Estado: {surface.status}"]
    if surface.cost_summary is not None:
        lines.append(f"Costo estimado: {surface.cost_summary}")
    if surface.route_summary is not None:
        lines.append(f"Ruta/modelo: {surface.route_summary}")
    if surface.safety_note is not None:
        lines.append(f"Nota: {surface.safety_note}")
    lines.extend(("", "Resultado:", surface.summary, "", "Acciones disponibles:"))
    lines.extend(option.label for option in surface.action_options)
    return "\n".join(lines)


def _action_options(*, status: str) -> tuple[AsyncResultActionOption, ...]:
    action_kinds = ("acknowledge", "dismiss", "view_lineage_summary")
    if status == "completed":
        action_kinds = ("acknowledge", "dismiss", "request_followup", "view_lineage_summary")
    return tuple(
        AsyncResultActionOption(
            action_id=_stable_id("async_result_action", status, action_kind),
            label=USER_VISIBLE_ACTIONS[action_kind],
            action_kind=action_kind,
            local_only=True,
            creates_authority=False,
        )
        for action_kind in action_kinds
    )


def _task_label(request_evidence: dict[str, object] | None) -> str:
    if not request_evidence:
        return "Tarea asincrona"
    payload = request_evidence.get("request_payload")
    if isinstance(payload, dict):
        summary = payload.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    capability = request_evidence.get("requested_capability")
    if isinstance(capability, str) and capability.strip():
        return capability.strip()
    return "Tarea asincrona"


def _surface_summary(
    *,
    status: str,
    payload_summary: dict[str, object] | None,
    reason_code: str,
) -> str:
    if status == "failed":
        summary = _payload_summary_text(payload_summary)
        if summary is not None:
            return summary
        return "La tarea no pudo completarse bajo la autoridad registrada."
    summary = _payload_summary_text(payload_summary)
    if summary is not None:
        return summary
    return "El resultado fue registrado localmente sin ejecutar acciones externas."


def _payload_summary_text(payload_summary: dict[str, object] | None) -> str | None:
    if not payload_summary:
        return None
    if any(key in PRIVATE_EVIDENCE_KEYS for key in payload_summary):
        return "El resultado fue resumido sin exponer evidencia privada."
    summary = payload_summary.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    bullet_lines: list[str] = []
    for key in sorted(payload_summary):
        if key in PRIVATE_EVIDENCE_KEYS:
            continue
        value = payload_summary[key]
        if isinstance(value, str) and value.strip():
            bullet_lines.append(f"- {value.strip()}")
        elif isinstance(value, list):
            for item in value[:4]:
                if isinstance(item, str) and item.strip():
                    bullet_lines.append(f"- {item.strip()}")
        elif isinstance(value, bool):
            bullet_lines.append(f"- {key}: {'si' if value else 'no'}")
    if bullet_lines:
        return "\n".join(bullet_lines[:4])
    return None


def _cost_summary(cost_evidence: dict[str, object] | None) -> str | None:
    if not cost_evidence:
        return None
    estimated_cost = cost_evidence.get("estimated_cost_usd")
    if isinstance(estimated_cost, (int, float)):
        return f"${estimated_cost:.2f}"
    return None


def _route_summary(
    *,
    request_evidence: dict[str, object] | None,
    cost_evidence: dict[str, object] | None,
) -> str | None:
    route_mode = None if request_evidence is None else request_evidence.get("requested_route_mode")
    model_id = _route_value(cost_evidence, "selected_model_id")
    provider_id = _route_value(cost_evidence, "selected_provider_id")
    parts = [str(route_mode) for route_mode in (route_mode,) if isinstance(route_mode, str) and route_mode]
    if isinstance(model_id, str) and model_id:
        parts.append(model_id)
    elif isinstance(provider_id, str) and provider_id:
        parts.append(provider_id)
    return " / ".join(parts) if parts else None


def _route_value(cost_evidence: dict[str, object] | None, key: str) -> object:
    if not cost_evidence:
        return None
    route_decision = cost_evidence.get("route_decision")
    if isinstance(route_decision, dict) and key in route_decision:
        return route_decision.get(key)
    return cost_evidence.get(key)


def _safety_note(*, status: str) -> str:
    if status == "failed":
        return "Solo se genero una vista local. No se autorizo ninguna accion externa."
    return "Resultado local listo para revision. No se ejecuto ninguna accion externa."


def _dict_copy(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    copied: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, dict):
            nested = _dict_copy(item)
            copied[key] = {} if nested is None else nested
        elif isinstance(item, list):
            copied[key] = list(item)
        elif isinstance(item, tuple):
            copied[key] = list(item)
        else:
            copied[key] = item
    return copied


def _stable_id(prefix: str, *parts: object) -> str:
    joined = "|".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_" + uuid5(NAMESPACE_URL, joined).hex[:12]
