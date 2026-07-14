from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import desc, select

from app.document_control import list_active_document_tasks
from app.file_intake_control import list_active_file_intakes, list_file_retrieval_enablement_requests
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.memory_control import list_active_memories
from app.models import ProposedMemory, Task, TaskRun
from app.reply_composer import compose_robot_folder_empty_reply, compose_robot_folder_reply
from app.safety import evaluate_safety


SECTION_ABOUT = "Sobre mí"
SECTION_FAMILY = "Familia y personas importantes"
SECTION_HOME = "Casa y servicios"
SECTION_CAR = "Auto y trámites"
SECTION_DOCUMENTS = "Documentos importantes"
SECTION_PREFERENCES = "Preferencias de trabajo"
SECTION_TASKS = "Tareas y pendientes recurrentes"
SECTION_LIMITS = "Límites del robot"
SECTION_PENDING = "Pendiente de aprobación"
SECTION_OTHER = "Otros datos guardados"

SECTION_ORDER = [
    SECTION_ABOUT,
    SECTION_FAMILY,
    SECTION_HOME,
    SECTION_CAR,
    SECTION_DOCUMENTS,
    SECTION_PREFERENCES,
    SECTION_TASKS,
    SECTION_LIMITS,
    SECTION_PENDING,
    SECTION_OTHER,
]

DISPLAYABLE_MEMORY_TYPES = {"USER_PROFILE", "WORK_PREFERENCE", "BOUNDARY_MEMORY"}


@dataclass(slots=True)
class RobotFolderSection:
    title: str
    items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RobotFolderState:
    first_name: str | None
    active_memories: list
    pending_memories: list
    active_file_intakes: list
    active_document_tasks: list
    unresolved_task_runs: list
    retrieval_enablement_requests: list


def process_robot_folder(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="ROBOT_FOLDER_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare robot folder summary", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    state = collect_robot_folder_state(context=context, current_task_id=task.id)
    sections = build_robot_folder_sections(state=state)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="ROBOT_FOLDER_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_robot_folder_empty_reply() if not sections else compose_robot_folder_reply(sections)
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def collect_robot_folder_state(*, context, current_task_id: str) -> RobotFolderState:
    unresolved_task_runs = context.session.execute(
        select(TaskRun, Task)
        .join(Task, Task.id == TaskRun.task_id)
        .where(
            Task.user_id == context.user.id,
            Task.robot_id == context.robot.id,
            Task.id != current_task_id,
            Task.kind.notin_(("ATTENTION_STATUS", "ROBOT_FOLDER_STATUS")),
            TaskRun.status.in_(("pending", "failed", "blocked")),
        )
        .order_by(desc(TaskRun.created_at))
    ).all()
    pending_memories = context.session.scalars(
        select(ProposedMemory)
        .where(
            ProposedMemory.user_id == context.user.id,
            ProposedMemory.robot_id == context.robot.id,
            ProposedMemory.status == "PENDING",
        )
        .order_by(desc(ProposedMemory.created_at))
    ).all()
    return RobotFolderState(
        first_name=context.user.first_name,
        active_memories=list_active_memories(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
        ),
        pending_memories=pending_memories,
        active_file_intakes=list_active_file_intakes(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
        ),
        active_document_tasks=list_active_document_tasks(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
        ),
        unresolved_task_runs=unresolved_task_runs,
        retrieval_enablement_requests=list_file_retrieval_enablement_requests(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
        ),
    )


def build_robot_folder_sections(*, state: RobotFolderState) -> list[RobotFolderSection]:
    section_items: dict[str, list[str]] = {title: [] for title in SECTION_ORDER}

    for memory in state.active_memories:
        section_title = _classify_memory_section(memory_type=memory.memory_type, text=memory.content)
        if memory.memory_type in DISPLAYABLE_MEMORY_TYPES and section_title != SECTION_OTHER:
            item = _format_memory_line(memory.content)
            if item not in section_items[section_title]:
                section_items[section_title].append(item)
            continue
        section_items[section_title].append(_format_memory_count(section_title=section_title))

    section_items = _collapse_duplicate_count_placeholders(section_items)

    if state.active_file_intakes:
        section_items[SECTION_DOCUMENTS].append(f"Hay {len(state.active_file_intakes)} archivos registrados.")
    if state.active_document_tasks:
        section_items[SECTION_DOCUMENTS].append(
            f"Hay {len(state.active_document_tasks)} documentos revisados recientemente."
        )
    if state.unresolved_task_runs:
        section_items[SECTION_TASKS].append(
            f"Hay {len(state.unresolved_task_runs)} tasks con estado pendiente, bloqueado o fallido."
        )
    if state.retrieval_enablement_requests:
        section_items[SECTION_LIMITS].append("Retrieval sigue deshabilitado por política local.")
    if state.pending_memories:
        section_items[SECTION_PENDING].append(
            f"Hay {len(state.pending_memories)} memorias pendientes de aprobación."
        )

    if state.first_name and any(items for items in section_items.values()):
        section_items[SECTION_ABOUT].insert(0, f"Nombre: {state.first_name}")

    sections: list[RobotFolderSection] = []
    for title in SECTION_ORDER:
        items = section_items[title]
        if items:
            sections.append(RobotFolderSection(title=title, items=items))
    return sections


def _classify_memory_section(*, memory_type: str, text: str) -> str:
    normalized = text.lower()
    if memory_type == "BOUNDARY_MEMORY" or any(
        term in normalized for term in ("boundary", "ask before", "never ", "limit", "blocked", "confirm")
    ):
        return SECTION_LIMITS
    if memory_type == "WORK_PREFERENCE" or any(
        term in normalized for term in ("prefer", "preferred", "working hours", "tone", "format", "style")
    ):
        return SECTION_PREFERENCES
    if memory_type == "USER_PROFILE" or any(
        term in normalized for term in ("your name is", "your role is", "your timezone is", "idioma", "language")
    ):
        return SECTION_ABOUT
    if any(term in normalized for term in ("family", "caregiver", "parent", "child", "spouse", "relative", "papá", "mamá")):
        return SECTION_FAMILY
    if any(term in normalized for term in ("home", "house", "service", "bill", "utility", "telmex", "cfe", "internet")):
        return SECTION_HOME
    if any(term in normalized for term in ("car", "vehicle", "verification", "license", "insurance", "trámite", "tramite")):
        return SECTION_CAR
    if memory_type == "TASK_MEMORY":
        return SECTION_TASKS
    return SECTION_OTHER


def _format_memory_line(content: str) -> str:
    text = content.strip()
    if text.endswith("."):
        return f"- {text}"
    return f"- {text}."


def _format_memory_count(*, section_title: str) -> str:
    if section_title == SECTION_FAMILY:
        return "__COUNT_FAMILY__"
    if section_title == SECTION_HOME:
        return "__COUNT_HOME__"
    if section_title == SECTION_CAR:
        return "__COUNT_CAR__"
    if section_title == SECTION_TASKS:
        return "__COUNT_TASKS__"
    return "__COUNT_OTHER__"


def _collapse_duplicate_count_placeholders(section_items: dict[str, list[str]]) -> dict[str, list[str]]:
    mapping = {
        "__COUNT_FAMILY__": "Hay recuerdos activos relacionados con familia.",
        "__COUNT_HOME__": "Hay recuerdos activos relacionados con casa o servicios.",
        "__COUNT_CAR__": "Hay recuerdos activos relacionados con auto o trámites.",
        "__COUNT_TASKS__": "Hay recuerdos activos relacionados con tareas o pendientes.",
        "__COUNT_OTHER__": "Hay datos guardados adicionales.",
    }
    for title, items in section_items.items():
        collapsed: list[str] = []
        counts: dict[str, int] = {}
        for item in items:
            if item.startswith("__COUNT_"):
                counts[item] = counts.get(item, 0) + 1
            else:
                collapsed.append(item)
        for key, count in counts.items():
            if key == "__COUNT_FAMILY__":
                collapsed.append(f"Hay {count} recuerdos activos relacionados con familia.")
            elif key == "__COUNT_HOME__":
                collapsed.append(f"Hay {count} recuerdos activos relacionados con casa o servicios.")
            elif key == "__COUNT_CAR__":
                collapsed.append(f"Hay {count} recuerdos activos relacionados con auto o trámites.")
            elif key == "__COUNT_TASKS__":
                collapsed.append(f"Hay {count} recuerdos activos relacionados con tareas o pendientes.")
            else:
                collapsed.append(f"Hay {count} datos guardados adicionales.")
        section_items[title] = collapsed
    return section_items
