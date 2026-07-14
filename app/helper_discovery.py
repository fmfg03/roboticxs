from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Callable
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.memory_service import create_proposed_memory
from app.models import HelperDiscoverySession, Robot, Task, TaskRun, User
from app.robbie_conversation import RobbieConversationError, generate_robbie_reply


HELPER_DISCOVERY_TTL_HOURS = 24
HELPER_DISCOVERY_QUESTIONS: tuple[tuple[str, str], ...] = (
    (
        "situation",
        "¿Qué situación de tu vida o de tu familia te gustaría que Robbie te ayudara a manejar mejor?",
    ),
    (
        "recurring_load",
        "¿Qué cosas se repiten, se te pueden pasar o te consumen más tiempo y energía en esa situación?",
    ),
    (
        "people_and_roles",
        "¿Quiénes participan y qué responsabilidad tienes tú actualmente? Comparte solo lo que te resulte cómodo.",
    ),
    (
        "desired_help",
        "¿Qué clase de ayuda te serviría más: recordar, organizar, guiar paso a paso, preparar mensajes, dar seguimiento u otra?",
    ),
    (
        "boundaries",
        "¿Qué no quieres que Robbie haga, guarde o comparta?",
    ),
)

_YES = {"si", "sí", "acepto", "comenzar", "empezar"}
_NO = {"no", "no acepto", "ahora no"}
_SAVE_PROFILE = {"guardar perfil", "si guardar", "sí guardar", "conservar perfil"}
_DO_NOT_SAVE = {"no guardar", "no conservar", "descartar perfil"}
_PAUSE = {"/pausar", "pausar"}
_CONTINUE = {"/continuar", "continuar"}
_CANCEL = {"/cancelar", "cancelar entrevista", "cancelar"}


@dataclass(frozen=True, slots=True)
class HelperDiscoveryReply:
    reply_text: str
    status: str
    proposal_id: str | None = None


SummaryGenerator = Callable[..., str]


def handle_helper_discovery(
    *,
    session: Session,
    settings: Settings,
    user: User,
    robot: Robot,
    telegram_user_id: int,
    text: str,
    first_name: str | None,
    summary_generator: SummaryGenerator | None = None,
    now: datetime | None = None,
) -> HelperDiscoveryReply | None:
    if (
        not settings.helper_discovery_enabled
        or not settings.is_telegram_user_allowed(telegram_user_id)
        or telegram_user_id == settings.telegram_owner_id
    ):
        return None

    current_time = now or datetime.now(timezone.utc)
    normalized = _normalize(text)
    record = _get_session(session=session, user_id=user.id, robot_id=robot.id)

    if record is None:
        record = _new_session(
            session=session,
            user_id=user.id,
            robot_id=robot.id,
            now=current_time,
        )
        return HelperDiscoveryReply(
            reply_text=_consent_message(first_name),
            status=record.status,
        )

    if _is_expired(record, current_time):
        _clear_session(record, status="CANCELLED", now=current_time)
        return HelperDiscoveryReply(
            reply_text=(
                "La entrevista anterior caducó y eliminé sus respuestas temporales. "
                "Envía /start cuando quieras comenzar de nuevo."
            ),
            status=record.status,
        )

    if normalized in _CANCEL:
        _clear_session(record, status="CANCELLED", now=current_time)
        return HelperDiscoveryReply(
            reply_text="Entrevista cancelada. Eliminé las respuestas temporales y no guardé ninguna memoria.",
            status=record.status,
        )

    if normalized == "/start":
        if record.status in {"ACTIVE", "PAUSED"}:
            record.status = "ACTIVE"
            record.updated_at = current_time
            return HelperDiscoveryReply(
                reply_text="Continuamos donde nos quedamos.\n\n" + _current_question(record),
                status=record.status,
            )
        _reset_for_consent(record, now=current_time)
        return HelperDiscoveryReply(reply_text=_consent_message(first_name), status=record.status)

    if record.status == "WAITING_CONSENT":
        if normalized in _YES:
            record.status = "ACTIVE"
            record.current_step = 0
            record.consented_at = current_time
            record.expires_at = current_time + timedelta(hours=HELPER_DISCOVERY_TTL_HOURS)
            record.updated_at = current_time
            return HelperDiscoveryReply(
                reply_text=(
                    "Gracias. Guardaré tus respuestas solo como estado temporal durante esta entrevista. "
                    "Puedes usar /pausar o /cancelar en cualquier momento.\n\n"
                    + HELPER_DISCOVERY_QUESTIONS[0][1]
                ),
                status=record.status,
            )
        if normalized in _NO:
            _clear_session(record, status="DECLINED", now=current_time)
            return HelperDiscoveryReply(
                reply_text="Entendido. No iniciaré la entrevista ni guardaré información.",
                status=record.status,
            )
        return HelperDiscoveryReply(
            reply_text="Antes de comenzar necesito tu consentimiento. Responde SÍ para empezar o NO para salir.",
            status=record.status,
        )

    if record.status == "PAUSED":
        if normalized in _CONTINUE:
            record.status = "ACTIVE"
            record.updated_at = current_time
            return HelperDiscoveryReply(
                reply_text="Continuamos.\n\n" + _current_question(record),
                status=record.status,
            )
        return HelperDiscoveryReply(
            reply_text="La entrevista está pausada. Envía /continuar para seguir o /cancelar para eliminarla.",
            status=record.status,
        )

    if record.status == "ACTIVE":
        if normalized in _PAUSE:
            record.status = "PAUSED"
            record.updated_at = current_time
            return HelperDiscoveryReply(
                reply_text="Pausé la entrevista. Tus respuestas temporales caducarán en 24 horas. Envía /continuar cuando quieras seguir.",
                status=record.status,
            )

        answers = _load_answers(record.answers_json)
        key, _ = HELPER_DISCOVERY_QUESTIONS[record.current_step]
        answers[key] = " ".join(text.split())[:2000]
        record.answers_json = json.dumps(answers, ensure_ascii=False, sort_keys=True)
        record.current_step += 1
        record.updated_at = current_time

        if record.current_step < len(HELPER_DISCOVERY_QUESTIONS):
            return HelperDiscoveryReply(
                reply_text=HELPER_DISCOVERY_QUESTIONS[record.current_step][1],
                status=record.status,
            )

        generator = summary_generator or generate_helper_support_summary
        try:
            summary = generator(answers=answers, settings=settings)
        except Exception:
            summary = build_fallback_summary(answers)
        record.summary = summary.strip()[:2500]
        record.status = "READY_FOR_REVIEW"
        record.updated_at = current_time
        return HelperDiscoveryReply(
            reply_text=(
                "Esto es lo que entendí y cómo puedo ayudarte:\n\n"
                f"{record.summary}\n\n"
                "Nada de esto es memoria activa todavía. Si quieres conservar este perfil, responde GUARDAR PERFIL. "
                "Si no, responde NO GUARDAR."
            ),
            status=record.status,
        )

    if record.status == "READY_FOR_REVIEW":
        if normalized in _SAVE_PROFILE:
            proposal = _create_profile_proposal(
                session=session,
                user=user,
                robot=robot,
                summary=record.summary or build_fallback_summary({}),
            )
            record.status = "COMPLETED"
            record.proposal_id = proposal.id
            record.answers_json = "{}"
            record.completed_at = current_time
            record.updated_at = current_time
            return HelperDiscoveryReply(
                reply_text=(
                    "Preparé esta propuesta de memoria, pero todavía no está activa:\n\n"
                    f'"{proposal.proposed_content}"\n\n'
                    f"APROBAR memoria {proposal.id}\n"
                    f"RECHAZAR memoria {proposal.id}"
                ),
                status=record.status,
                proposal_id=proposal.id,
            )
        if normalized in _DO_NOT_SAVE or normalized in _NO:
            _clear_session(record, status="COMPLETED", now=current_time)
            return HelperDiscoveryReply(
                reply_text="Entendido. Eliminé las respuestas temporales y no creé ninguna memoria.",
                status=record.status,
            )
        return HelperDiscoveryReply(
            reply_text="Responde GUARDAR PERFIL para crear una propuesta de memoria o NO GUARDAR para eliminar la entrevista.",
            status=record.status,
        )

    return None


def generate_helper_support_summary(*, answers: dict[str, str], settings: Settings) -> str:
    evidence = "\n".join(
        f"- {key}: {value[:1200]}"
        for key, value in answers.items()
        if value.strip()
    )
    prompt = f"""Usa únicamente las respuestas de la entrevista incluidas abajo.
Redacta en español un resumen breve para la propia usuaria con esta estructura:
1. Lo que entendí.
2. Hasta tres formas concretas en que Robbie puede ayudar.
3. Límites y cosas que requieren confirmación humana.

No diagnostiques a nadie. No decidas medicación ni tratamientos. No inventes hechos, urgencias o permisos.
No propongas compartir información, contactar familiares ni ejecutar acciones externas sin autorización.

RESPUESTAS:
{evidence}
"""
    try:
        reply = generate_robbie_reply(
            text=prompt,
            approved_memories=[],
            settings=settings,
            recent_turns=[],
        )
    except RobbieConversationError:
        return build_fallback_summary(answers)
    return reply.text.strip()[:2500]


def build_fallback_summary(answers: dict[str, str]) -> str:
    situation = answers.get("situation", "la situación que describiste")
    recurring_load = answers.get("recurring_load", "las tareas y situaciones que se repiten")
    desired_help = answers.get("desired_help", "organización y seguimiento")
    boundaries = answers.get("boundaries", "todo lo que no autorices expresamente")
    return (
        f"Lo que entendí: quieres apoyo con {situation[:500]}. La carga que más se repite es {recurring_load[:500]}.\n\n"
        "Formas de ayudar:\n"
        "1. Convertir situaciones recurrentes en rutinas cortas y pasos claros.\n"
        "2. Preparar recordatorios, listas o borradores para que tú los revises.\n"
        f"3. Dar seguimiento de la forma que pediste: {desired_help[:500]}.\n\n"
        f"Límites: no guardaré ni compartiré {boundaries[:500]}; tampoco tomaré decisiones médicas ni ejecutaré acciones externas sin confirmación."
    )[:2500]


def _get_session(*, session: Session, user_id: str, robot_id: str) -> HelperDiscoverySession | None:
    return session.scalar(
        select(HelperDiscoverySession).where(
            HelperDiscoverySession.user_id == user_id,
            HelperDiscoverySession.robot_id == robot_id,
        )
    )


def _new_session(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    now: datetime,
) -> HelperDiscoverySession:
    record = HelperDiscoverySession(
        user_id=user_id,
        robot_id=robot_id,
        status="WAITING_CONSENT",
        current_step=0,
        answers_json="{}",
        expires_at=now + timedelta(hours=HELPER_DISCOVERY_TTL_HOURS),
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.flush()
    return record


def _reset_for_consent(record: HelperDiscoverySession, *, now: datetime) -> None:
    record.status = "WAITING_CONSENT"
    record.current_step = 0
    record.answers_json = "{}"
    record.summary = None
    record.proposal_id = None
    record.consented_at = None
    record.completed_at = None
    record.expires_at = now + timedelta(hours=HELPER_DISCOVERY_TTL_HOURS)
    record.updated_at = now


def _clear_session(record: HelperDiscoverySession, *, status: str, now: datetime) -> None:
    record.status = status
    record.current_step = 0
    record.answers_json = "{}"
    record.summary = None
    record.proposal_id = None
    record.expires_at = None
    record.completed_at = now if status == "COMPLETED" else None
    record.updated_at = now


def _create_profile_proposal(
    *,
    session: Session,
    user: User,
    robot: Robot,
    summary: str,
):
    audit_text = "Helper Discovery profile proposal explicitly requested by the user."
    task = Task(
        user_id=user.id,
        robot_id=robot.id,
        kind="HELPER_DISCOVERY_PROFILE_PROPOSAL",
        input_text=audit_text,
        scope_decision="ANSWER",
        task_class="EXTRACTION",
    )
    session.add(task)
    session.flush()
    session.add(TaskRun(task_id=task.id, status="completed"))
    return create_proposed_memory(
        session=session,
        user_id=user.id,
        robot_id=robot.id,
        task_id=task.id,
        memory_type="USER_PROFILE",
        proposed_content=summary[:2500],
        source_text=audit_text,
        importance="normal",
    )


def _load_answers(raw: str) -> dict[str, str]:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in parsed.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _current_question(record: HelperDiscoverySession) -> str:
    step = min(max(record.current_step, 0), len(HELPER_DISCOVERY_QUESTIONS) - 1)
    return HELPER_DISCOVERY_QUESTIONS[step][1]


def _is_expired(record: HelperDiscoverySession, now: datetime) -> bool:
    if record.expires_at is None or record.status in {"COMPLETED", "DECLINED", "CANCELLED"}:
        return False
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


def _consent_message(first_name: str | None) -> str:
    greeting = f"Hola, {first_name}." if first_name else "Hola."
    return (
        f"{greeting} Soy Robbie. Quiero conocerte para entender dónde puedo reducirte carga y proponerte ayuda concreta.\n\n"
        "Si aceptas, haré cinco preguntas, una por vez. Tus respuestas serán temporales durante 24 horas, "
        "no se compartirán con Francisco ni con otra persona y no se convertirán en memoria sin otra aprobación explícita.\n\n"
        "Responde SÍ para comenzar o NO para salir."
    )


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(without_accents.split())
