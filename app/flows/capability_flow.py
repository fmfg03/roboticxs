from __future__ import annotations

from dataclasses import dataclass

from app.capability_catalog import (
    STATUS_AGENTIUS_CANDIDATE,
    STATUS_AVAILABLE_READ_ONLY,
    STATUS_BLOCKED,
    STATUS_NEEDS_APPROVAL,
    STATUS_UNKNOWN,
    Capability,
    load_capability_catalog,
)
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.reply_composer import (
    compose_capability_catalog_reply,
    compose_capability_resolution_reply,
    compose_web_preflight_reply,
    compose_web_preflight_unknown_reply,
)
from app.safety import evaluate_safety
from app.web_preflight_policy import WEB_STATUS_UNKNOWN, classify_web_preflight


BLOCKED_KEYWORDS = (
    "pagar",
    "pago",
    "tarjeta",
    "checkout",
    "transferencia",
    "payment",
    "acepta términos",
    "acepta terminos",
    "aceptar términos",
    "aceptar terminos",
    "aceptar contrato",
    "contrato",
    "firma legal",
    "cambiar contraseña",
    "cambiar contrasena",
    "password",
    "permisos",
    "borrar cuenta",
    "eliminar cuenta",
    "delete account",
    "delete data",
    "refund",
    "reembolso",
)

ATTENTION_KEYWORDS = ("qué se me pasó", "what did i miss", "atención", "attention", "pendiente")
ROBOT_FOLDER_KEYWORDS = (
    "qué sabes",
    "información importante",
    "informacion importante",
    "robot folder",
    "lo que robbie sabe",
    "memoria",
    "remember",
    "know",
)
MEMORY_APPROVAL_KEYWORDS = (
    "recuerda",
    "recordar",
    "guarda esto",
    "aprobar memoria",
    "memoria pendiente",
    "olvidar memoria",
)
DOCUMENT_REVIEW_KEYWORDS = ("documento", "document", "resumir documento", "review document", "revisar documento")
APPROVAL_PACKET_KEYWORDS = (
    "approval packet",
    "prepare approval",
    "aprobar una acción",
    "aprobar una accion",
    "tendría que aprobar",
    "tendria que aprobar",
    "review an action before doing it",
    "revisar una acción antes de hacerla",
    "revisar una accion antes de hacerla",
)
FAMILY_GROCERY_KEYWORDS = (
    "súper",
    "super",
    "mandado",
    "compras",
    "walmart",
    "costco",
    "suegros",
    "papás",
    "papas",
    "padres",
    "parents",
    "groceries",
)
WEB_TASK_KEYWORDS = (
    "cita",
    "verificación",
    "verificacion",
    "trámite",
    "tramite",
    "portal",
    "formulario",
    "web",
    "browser",
    "página",
    "pagina",
    "sitio",
    "login",
    "iniciar sesión",
    "iniciar sesion",
)
AGENTIUS_KEYWORDS = (
    "crm",
    "equipo",
    "clientes",
    "workflow",
    "automatizar empresa",
    "customer support",
    "ventas",
    "pipeline",
    "aprobaciones",
    "negocio",
    "empresa",
    "operación",
    "operacion",
)


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    status: str
    capability_id: str | None
    display_name: str | None
    reason: str


def process_capability_catalog(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="CAPABILITY_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare capability catalog", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    catalog = load_capability_catalog()
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="CAPABILITY_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_capability_catalog_reply(catalog)
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_capability_query(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="CAPABILITY_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare capability resolution", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    catalog = load_capability_catalog()
    resolution = resolve_capability(context.envelope.text, catalog)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="CAPABILITY_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    if resolution.capability_id == "web_workflow_preflight":
        web_result = classify_web_preflight(context.envelope.text)
        if web_result.status == WEB_STATUS_UNKNOWN:
            reply_text = compose_web_preflight_unknown_reply()
        else:
            reply_text = compose_web_preflight_reply(result=web_result)
    else:
        reply_text = compose_capability_resolution_reply(resolution=resolution)
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def resolve_capability(text: str, catalog: list[Capability]) -> CapabilityResolution:
    normalized = text.strip().lstrip("¿").strip().lower()

    if _contains_any(normalized, BLOCKED_KEYWORDS):
        return CapabilityResolution(
            status=STATUS_BLOCKED,
            capability_id="blocked_sensitive_actions",
            display_name="Acciones sensibles bloqueadas",
            reason="blocked_sensitive_action",
        )

    if _contains_any(normalized, ATTENTION_KEYWORDS):
        capability = _find_capability(catalog, "attention_summary")
        return _resolution_from_capability(capability, reason="attention_summary")

    if _contains_any(normalized, ROBOT_FOLDER_KEYWORDS):
        capability = _find_capability(catalog, "robot_folder")
        return _resolution_from_capability(capability, reason="robot_folder")

    if _contains_any(normalized, MEMORY_APPROVAL_KEYWORDS):
        capability = _find_capability(catalog, "approved_memory")
        return _resolution_from_capability(capability, reason="approved_memory")

    if _contains_any(normalized, DOCUMENT_REVIEW_KEYWORDS):
        capability = _find_capability(catalog, "document_review_text")
        return _resolution_from_capability(capability, reason="document_review_text")

    if _contains_any(normalized, APPROVAL_PACKET_KEYWORDS):
        capability = _find_capability(catalog, "action_approval_packets")
        return _resolution_from_capability(capability, reason="action_approval_packets")

    if _contains_any(normalized, FAMILY_GROCERY_KEYWORDS):
        capability = _find_capability(catalog, "super_familiar")
        return _resolution_from_capability(capability, reason="super_familiar")

    if _contains_any(normalized, WEB_TASK_KEYWORDS):
        capability = _find_capability(catalog, "web_workflow_preflight")
        return _resolution_from_capability(capability, reason="web_workflow_preflight")

    if _contains_any(normalized, AGENTIUS_KEYWORDS):
        return CapabilityResolution(
            status=STATUS_AGENTIUS_CANDIDATE,
            capability_id=None,
            display_name=None,
            reason="agentius_candidate",
        )

    return CapabilityResolution(
        status=STATUS_UNKNOWN,
        capability_id=None,
        display_name=None,
        reason="unknown",
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _find_capability(catalog: list[Capability], capability_id: str) -> Capability:
    for capability in catalog:
        if capability.capability_id == capability_id:
            return capability
    raise LookupError(f"Missing capability catalog entry: {capability_id}")


def _resolution_from_capability(capability: Capability, *, reason: str) -> CapabilityResolution:
    return CapabilityResolution(
        status=capability.status,
        capability_id=capability.capability_id,
        display_name=capability.display_name,
        reason=reason,
    )
