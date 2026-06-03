from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy import desc, select

from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.memory_control import list_active_memories
from app.models import ProposedMemory
from app.reply_composer import compose_super_familiar_empty_reply, compose_super_familiar_reply
from app.safety import evaluate_safety


FAMILY_KEYWORDS = ("familia", "suegros", "papás", "papas", "padres", "mamá", "mama", "papá", "papa", "parents", "in-laws")
GROCERY_KEYWORDS = ("súper", "super", "supermercado", "mandado", "compras", "groceries", "walmart", "costco", "lista")
PREFERENCE_KEYWORDS = ("marca", "prefer", "prefieren", "preferencia", "sustitución", "sustitucion", "no comprar", "evitar", "deslactosada", "integral")
BUDGET_KEYWORDS = ("presupuesto", "budget")
STORE_KEYWORDS = ("tienda", "walmart", "costco")
SCHEDULE_KEYWORDS = ("entrega", "delivery", "horario", "semanal", "cada semana", "recurrente")
APPROVAL_KEYWORDS = ("aprueba", "aprobación", "aprobacion", "antes de pagar")
LIST_PATTERNS = (
    re.compile(r"lista del s[úu]per:\s*(.+)", re.IGNORECASE),
    re.compile(r"lista del supermercado:\s*(.+)", re.IGNORECASE),
    re.compile(r"comprar\s+(.+?)(?:\s+cada semana|\s+semanalmente|$)", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class SuperFamiliarContext:
    family_targets: tuple[str, ...]
    known_preferences: tuple[str, ...]
    base_items: tuple[str, ...]
    pending_memory_count: int
    missing_info: tuple[str, ...]
    has_explicit_grocery_context: bool


def process_super_familiar(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="SUPER_FAMILIAR_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare super familiar brief", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    grocery_context = collect_super_familiar_context(context=context)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="SUPER_FAMILIAR_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = (
        compose_super_familiar_reply(grocery_context)
        if grocery_context.has_explicit_grocery_context
        else compose_super_familiar_empty_reply(grocery_context)
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def collect_super_familiar_context(*, context) -> SuperFamiliarContext:
    active_memories = list_active_memories(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    pending_memories = context.session.scalars(
        select(ProposedMemory)
        .where(
            ProposedMemory.user_id == context.user.id,
            ProposedMemory.robot_id == context.robot.id,
            ProposedMemory.status == "PENDING",
        )
        .order_by(desc(ProposedMemory.created_at))
    ).all()

    family_targets: list[str] = []
    known_preferences: list[str] = []
    base_items: list[str] = []
    known_target = False
    known_products = False
    known_preference = False
    known_budget = False
    known_store = False
    known_schedule = False
    known_approver = False

    for memory in active_memories:
        normalized = memory.content.lower()
        if not _contains_any(normalized, GROCERY_KEYWORDS):
            continue

        if _contains_any(normalized, FAMILY_KEYWORDS):
            known_target = True
            for target in _extract_family_targets(normalized):
                if target not in family_targets:
                    family_targets.append(target)

        items = _extract_base_items(memory.content)
        if items:
            known_products = True
            for item in items:
                if item not in base_items:
                    base_items.append(item)

        if _contains_any(normalized, PREFERENCE_KEYWORDS):
            known_preference = True
            known_preferences.append(memory.content.rstrip("."))
        if _contains_any(normalized, BUDGET_KEYWORDS):
            known_budget = True
            known_preferences.append(memory.content.rstrip("."))
        if _contains_any(normalized, STORE_KEYWORDS):
            known_store = True
        if _contains_any(normalized, SCHEDULE_KEYWORDS):
            known_schedule = True
        if _contains_any(normalized, APPROVAL_KEYWORDS):
            known_approver = True

    pending_memory_count = sum(
        1
        for proposal in pending_memories
        if _contains_any(proposal.proposed_content.lower(), GROCERY_KEYWORDS + FAMILY_KEYWORDS)
    )

    missing_info = []
    if not known_target:
        missing_info.append("¿Para quién es el súper?")
    if not known_products:
        missing_info.append("¿Qué productos se compran casi siempre?")
    if not known_preference:
        missing_info.append("¿Qué marcas o sustituciones prefieren?")
    if not known_budget:
        missing_info.append("¿Cuál es el presupuesto aproximado?")
    if not known_store:
        missing_info.append("¿Qué tienda suelen usar?")
    if not known_schedule:
        missing_info.append("¿Qué día u horario conviene?")
    if not known_approver:
        missing_info.append("¿Quién aprueba antes de pagar?")

    has_explicit_grocery_context = bool(family_targets or known_preferences or base_items)
    return SuperFamiliarContext(
        family_targets=tuple(family_targets),
        known_preferences=tuple(known_preferences),
        base_items=tuple(base_items),
        pending_memory_count=pending_memory_count,
        missing_info=tuple(missing_info),
        has_explicit_grocery_context=has_explicit_grocery_context,
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _extract_family_targets(normalized: str) -> tuple[str, ...]:
    targets: list[str] = []
    if "suegros" in normalized or "in-laws" in normalized:
        targets.append("Suegros")
    if any(term in normalized for term in ("papás", "papas", "padres", "parents")):
        targets.append("Papás")
    if "familia" in normalized and not targets:
        targets.append("Familia registrada")
    return tuple(targets)


def _extract_base_items(content: str) -> tuple[str, ...]:
    extracted: list[str] = []
    for pattern in LIST_PATTERNS:
        match = pattern.search(content)
        if match is None:
            continue
        for item in _split_items(match.group(1)):
            if item not in extracted:
                extracted.append(item)
    return tuple(extracted)


def _split_items(value: str) -> tuple[str, ...]:
    normalized = value.strip().rstrip(".")
    normalized = normalized.replace(" y ", ", ")
    items: list[str] = []
    for part in normalized.split(","):
        cleaned = part.strip(" .")
        if not cleaned or len(cleaned.split()) > 5:
            continue
        items.append(cleaned[0].upper() + cleaned[1:] if cleaned else cleaned)
    return tuple(items)
