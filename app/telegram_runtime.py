from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.config import Settings
from app.hermes_runtime import (
    HermesRuntimeRequest,
    HermesRuntimeResponse,
    dispatch_hermes_runtime_request,
)
from app.memory_service import (
    approve_proposal,
    create_proposed_memory,
    get_proposal_by_id,
    reject_proposal,
)
from app.memory_control import list_active_memories
from app.memory_control import forget_active_memory
from app.models import Robot, Task, TaskRun, User


TELEGRAM_RUNTIME_CHANNEL = "telegram"
TELEGRAM_CONVERSATION_REPLY = (
    "Hermes runtime foundation is available. Telegram/channel integration is active. "
    "Full skills are not implemented yet."
)
TELEGRAM_EMPTY_TEXT_REPLY = "No recibí texto para procesar."
TELEGRAM_UNSUPPORTED_REPLY = "Por ahora solo puedo procesar mensajes de texto."
TELEGRAM_MALFORMED_REPLY = "No pude procesar ese mensaje por ahora."
TELEGRAM_RUNTIME_WEBHOOK_PATH = "/api/telegram/runtime/webhook"
TELEGRAM_MEMORY_APPROVE_PATTERN = re.compile(
    r"^(?:aprobar|approve)\s+(?:memoria|memory)\s+([0-9a-f-]{36})$",
    re.IGNORECASE,
)
TELEGRAM_MEMORY_REJECT_PATTERN = re.compile(
    r"^(?:rechazar|reject)\s+(?:memoria|memory)\s+([0-9a-f-]{36})$",
    re.IGNORECASE,
)
TELEGRAM_MEMORY_INTENT_PREFIXES = (
    "recuerda que ",
    "acuérdate que ",
    "acuerdate que ",
    "guarda que ",
    "quiero que recuerdes que ",
    "remember that ",
    "save that ",
    "please remember that ",
    "i want you to remember that ",
)
TELEGRAM_MEMORY_RECALL_PHRASES_ES = {
    "qué recuerdas de mí",
    "que recuerdas de mi",
    "qué sabes de mí",
    "que sabes de mi",
    "muéstrame mis memorias",
    "muestrame mis memorias",
    "lista mis memorias",
}
TELEGRAM_MEMORY_RECALL_PHRASES_EN = {
    "what do you remember about me",
    "what do you remember",
    "what do you know about me",
    "show my memories",
    "list my memories",
}
TELEGRAM_MEMORY_FORGET_PATTERNS = (
    ("es", re.compile(r"^(?:olvida|olvidar|borra|elimina)\s+memoria\s+(\S+)$", re.IGNORECASE)),
    ("en", re.compile(r"^(?:forget|delete|remove)\s+memory\s+(\S+)$", re.IGNORECASE)),
    ("en", re.compile(r"^forget\s+memoria\s+(\S+)$", re.IGNORECASE)),
)


class TelegramRuntimeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TelegramBotRuntimeConfig:
    token_configured: bool


@dataclass(frozen=True, slots=True)
class TelegramRuntimeSmokeReadiness:
    ready: bool
    runtime_webhook_path: str
    token_configured: bool
    webhook_url_configured: bool
    webhook_url_valid: bool
    diagnostics: dict[str, object]
    failure_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TelegramRuntimeMessage:
    chat_id: int
    user_id: int
    message_id: int
    text: str
    username: str | None = None
    first_name: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TelegramPreparedSend:
    method: str
    payload: dict[str, int | str]
    token_configured: bool


@dataclass(frozen=True, slots=True)
class TelegramRuntimeResult:
    ok: bool
    message: TelegramRuntimeMessage
    hermes_request: HermesRuntimeRequest
    hermes_response: HermesRuntimeResponse
    prepared_send: TelegramPreparedSend
    unsupported_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramConversationLoopResult:
    ok: bool
    prepared_send: TelegramPreparedSend | None
    trace: dict[str, str]
    message: TelegramRuntimeMessage | None = None
    hermes_request: HermesRuntimeRequest | None = None
    hermes_response: HermesRuntimeResponse | None = None
    error_code: str | None = None
    unsupported: bool = False
    ignored: bool = False


def get_telegram_bot_runtime_config(settings: Settings) -> TelegramBotRuntimeConfig:
    return TelegramBotRuntimeConfig(token_configured=bool(settings.telegram_bot_token))


def build_telegram_runtime_smoke_readiness(settings: Settings) -> TelegramRuntimeSmokeReadiness:
    token = settings.telegram_bot_token or ""
    webhook_url = settings.telegram_public_webhook_url or ""
    token_configured = bool(token.strip())
    webhook_url_configured = bool(webhook_url.strip())
    webhook_url_valid = _is_valid_public_webhook_url(webhook_url, token=token)

    failure_reasons: list[str] = []
    if not token_configured:
        failure_reasons.append("telegram_bot_token_missing")
    if not webhook_url_configured:
        failure_reasons.append("telegram_public_webhook_url_missing")
    elif not webhook_url_valid:
        failure_reasons.append("telegram_public_webhook_url_invalid")

    diagnostics: dict[str, object] = {
        "stage": "81P",
        "runtime_webhook_path": TELEGRAM_RUNTIME_WEBHOOK_PATH,
        "telegram_bot_token": "configured_redacted" if token_configured else "missing",
        "telegram_public_webhook_url_configured": webhook_url_configured,
        "telegram_public_webhook_url_valid": webhook_url_valid,
        "external_telegram_api_call": False,
        "automatic_webhook_registration": False,
        "production_deployment": False,
    }
    if webhook_url_configured:
        diagnostics["telegram_public_webhook_url"] = (
            "redacted_token_in_url" if token and token in webhook_url else webhook_url
        )

    return TelegramRuntimeSmokeReadiness(
        ready=not failure_reasons,
        runtime_webhook_path=TELEGRAM_RUNTIME_WEBHOOK_PATH,
        token_configured=token_configured,
        webhook_url_configured=webhook_url_configured,
        webhook_url_valid=webhook_url_valid,
        diagnostics=diagnostics,
        failure_reasons=tuple(failure_reasons),
    )


def parse_telegram_text_update(update: dict) -> TelegramRuntimeMessage:
    if not isinstance(update, dict):
        raise TelegramRuntimeError("Telegram update must be a JSON object.")

    message = update.get("message")
    if not isinstance(message, dict):
        raise TelegramRuntimeError("Telegram update missing message payload.")

    if "document" in message:
        raise TelegramRuntimeError("Telegram document/file payloads are not supported in 79P.")
    if "voice" in message or "audio" in message:
        raise TelegramRuntimeError("Telegram voice/audio payloads are not supported in 79P.")

    chat = message.get("chat")
    sender = message.get("from")
    text = message.get("text")
    message_id = message.get("message_id")

    if not isinstance(chat, dict) or not isinstance(sender, dict):
        raise TelegramRuntimeError("Telegram update missing chat or sender payload.")

    chat_id = chat.get("id")
    user_id = sender.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int) or not isinstance(message_id, int):
        raise TelegramRuntimeError("Telegram update missing required chat, user, or message id.")

    if not isinstance(text, str) or not text.strip():
        raise TelegramRuntimeError("Only non-empty Telegram text messages are supported in 79P.")

    username = sender.get("username")
    first_name = sender.get("first_name")

    return TelegramRuntimeMessage(
        chat_id=chat_id,
        user_id=user_id,
        message_id=message_id,
        text=text.strip(),
        username=username if isinstance(username, str) and username.strip() else None,
        first_name=first_name if isinstance(first_name, str) and first_name.strip() else None,
        metadata={
            "update_id": str(update.get("update_id", "")),
            "chat_type": str(chat.get("type", "")),
            "telegram_runtime_stage": "79P",
        },
    )


def build_hermes_request_from_telegram(message: TelegramRuntimeMessage) -> HermesRuntimeRequest:
    return HermesRuntimeRequest(
        user_id=str(message.user_id),
        channel=TELEGRAM_RUNTIME_CHANNEL,
        text=message.text,
        metadata={
            "telegram_chat_id": str(message.chat_id),
            "telegram_message_id": str(message.message_id),
            "telegram_username": message.username or "",
            "telegram_first_name": message.first_name or "",
            **message.metadata,
        },
    )


def prepare_telegram_text_send(
    *,
    chat_id: int,
    text: str,
    config: TelegramBotRuntimeConfig,
) -> TelegramPreparedSend:
    return TelegramPreparedSend(
        method="sendMessage",
        payload={"chat_id": chat_id, "text": text},
        token_configured=config.token_configured,
    )


def handle_telegram_runtime_update(
    *,
    update: dict,
    settings: Settings,
) -> TelegramRuntimeResult:
    message = parse_telegram_text_update(update)
    hermes_request = build_hermes_request_from_telegram(message)
    hermes_response = dispatch_hermes_runtime_request(hermes_request)
    prepared_send = prepare_telegram_text_send(
        chat_id=message.chat_id,
        text=hermes_response.text,
        config=get_telegram_bot_runtime_config(settings),
    )

    return TelegramRuntimeResult(
        ok=hermes_response.status == "ok",
        message=message,
        hermes_request=hermes_request,
        hermes_response=hermes_response,
        prepared_send=prepared_send,
    )


def run_telegram_conversation_loop(
    *,
    update: dict,
    settings: Settings,
    session=None,
    dispatch=dispatch_hermes_runtime_request,
) -> TelegramConversationLoopResult:
    trace = {
        "stage": "80P",
        "loop": "telegram_conversation_loop",
        "persistence": "deferred",
        "external_telegram_api_call": "false",
    }
    config = get_telegram_bot_runtime_config(settings)

    try:
        message = parse_telegram_text_update(update)
    except TelegramRuntimeError as exc:
        chat_id = _extract_chat_id(update)
        error_code = _classify_parse_error(str(exc))
        if chat_id is None:
            return TelegramConversationLoopResult(
                ok=False,
                prepared_send=None,
                trace={**trace, "error_code": error_code},
                error_code=error_code,
                ignored=True,
            )

        reply_text = TELEGRAM_UNSUPPORTED_REPLY if error_code == "unsupported_non_text" else TELEGRAM_EMPTY_TEXT_REPLY
        if error_code == "malformed_payload":
            reply_text = TELEGRAM_MALFORMED_REPLY
        return TelegramConversationLoopResult(
            ok=False,
            prepared_send=prepare_telegram_text_send(chat_id=chat_id, text=reply_text, config=config),
            trace={**trace, "error_code": error_code},
            error_code=error_code,
            unsupported=error_code == "unsupported_non_text",
            ignored=False,
        )

    hermes_request = build_hermes_request_from_telegram(message)
    if session is not None:
        memory_result = _handle_telegram_memory_proposal_loop(
            session=session,
            message=message,
            config=config,
            trace=trace,
        )
        if memory_result is not None:
            return memory_result

    try:
        hermes_response = dispatch(hermes_request)
    except Exception as exc:  # pragma: no cover - exercised through tests with an injected dispatcher.
        return TelegramConversationLoopResult(
            ok=False,
            message=message,
            hermes_request=hermes_request,
            prepared_send=prepare_telegram_text_send(
                chat_id=message.chat_id,
                text=TELEGRAM_MALFORMED_REPLY,
                config=config,
            ),
            trace={
                **trace,
                "error_code": "runtime_dispatch_error",
                "error_type": type(exc).__name__,
            },
            error_code="runtime_dispatch_error",
        )

    active_response = HermesRuntimeResponse(
        status=hermes_response.status,
        text=TELEGRAM_CONVERSATION_REPLY if hermes_response.status == "ok" else TELEGRAM_MALFORMED_REPLY,
        task_id=hermes_response.task_id,
        safety_decision=hermes_response.safety_decision,
        metadata={
            **hermes_response.metadata,
            "telegram_conversation_loop": "active",
            "persistence": "deferred",
        },
    )
    return TelegramConversationLoopResult(
        ok=active_response.status == "ok",
        message=message,
        hermes_request=hermes_request,
        hermes_response=active_response,
        prepared_send=prepare_telegram_text_send(
            chat_id=message.chat_id,
            text=active_response.text,
            config=config,
        ),
        trace={**trace, "dispatch": "hermes_runtime_foundation"},
    )


def build_telegram_conversation_webhook_response(result: TelegramConversationLoopResult) -> dict:
    body: dict[str, object] = {
        "ok": result.ok,
        "trace": result.trace,
        "unsupported": result.unsupported,
        "ignored": result.ignored,
    }
    if result.error_code is not None:
        body["error_code"] = result.error_code

    if result.message is not None:
        body.update(
            {
                "chat_id": result.message.chat_id,
                "user_id": result.message.user_id,
                "message_id": result.message.message_id,
            }
        )

    if result.hermes_request is not None:
        body["hermes_request"] = {
            "user_id": result.hermes_request.user_id,
            "channel": result.hermes_request.channel,
            "text": result.hermes_request.text,
            "metadata": result.hermes_request.metadata,
        }

    if result.prepared_send is not None:
        body["prepared_send"] = {
            "method": result.prepared_send.method,
            "payload": result.prepared_send.payload,
            "token_configured": result.prepared_send.token_configured,
        }

    if result.hermes_response is not None:
        body["hermes_response"] = {
            "status": result.hermes_response.status,
            "text": result.hermes_response.text,
            "task_id": result.hermes_response.task_id,
            "safety_decision": result.hermes_response.safety_decision,
            "metadata": result.hermes_response.metadata,
        }

    return body


def _handle_telegram_memory_proposal_loop(
    *,
    session,
    message: TelegramRuntimeMessage,
    config: TelegramBotRuntimeConfig,
    trace: dict[str, str],
) -> TelegramConversationLoopResult | None:
    approval_match = TELEGRAM_MEMORY_APPROVE_PATTERN.match(message.text.strip())
    rejection_match = TELEGRAM_MEMORY_REJECT_PATTERN.match(message.text.strip())
    proposal_payload = _extract_telegram_memory_proposal(message.text)
    forget_payload = _detect_telegram_memory_forget(message.text)
    recall_language = _detect_telegram_memory_recall(message.text)

    if (
        approval_match is None
        and rejection_match is None
        and proposal_payload is None
        and forget_payload is None
        and recall_language is None
    ):
        return None

    user, robot = _resolve_runtime_user_and_robot(session=session, message=message)
    if approval_match is not None or rejection_match is not None:
        proposal_id = (approval_match or rejection_match).group(1)
        proposal = get_proposal_by_id(
            session=session,
            user_id=user.id,
            robot_id=robot.id,
            proposal_id=proposal_id,
        )
        if proposal is None:
            reply_text = "No encontré una propuesta de memoria pendiente con ese ID."
            status = "invalid_id"
            ok = False
        elif proposal.status != "PENDING":
            reply_text = "Esa propuesta de memoria ya fue finalizada."
            status = "already_finalized"
            ok = False
        elif approval_match is not None:
            approve_proposal(session=session, proposal=proposal)
            reply_text = "Listo. Guardé esa memoria local."
            status = "approved"
            ok = True
        else:
            reject_proposal(session=session, proposal=proposal)
            reply_text = "Listo. No guardaré esa memoria."
            status = "rejected"
            ok = True

        return _build_memory_loop_result(
            message=message,
            config=config,
            trace={**trace, "stage": "82P", "memory_proposal_loop": status},
            reply_text=reply_text,
            ok=ok,
            error_code=None if ok else f"memory_proposal_{status}",
        )

    if forget_payload is not None:
        language, memory_id = forget_payload
        memory = forget_active_memory(
            session=session,
            user_id=user.id,
            robot_id=robot.id,
            memory_id=memory_id,
        )
        if memory is None:
            reply_text = (
                "I could not find an active memory with that id."
                if language == "en"
                else "No encontré una memoria activa con ese id."
            )
            return _build_memory_loop_result(
                message=message,
                config=config,
                trace={**trace, "stage": "84P", "active_memory_forget": "not_found"},
                reply_text=reply_text,
                ok=False,
                error_code="active_memory_forget_not_found",
            )

        reply_text = "Done. I forgot that memory." if language == "en" else "Listo. Olvidé esa memoria."
        return _build_memory_loop_result(
            message=message,
            config=config,
            trace={**trace, "stage": "84P", "active_memory_forget": "forgotten"},
            reply_text=reply_text,
            ok=True,
        )

    if recall_language is not None:
        memories = list_active_memories(session=session, user_id=user.id, robot_id=robot.id)
        reply_text = _compose_telegram_active_memory_recall_reply(
            language=recall_language,
            memories=[(memory.id, memory.content) for memory in memories],
        )
        return _build_memory_loop_result(
            message=message,
            config=config,
            trace={**trace, "stage": "83P", "active_memory_recall": "listed"},
            reply_text=reply_text,
            ok=True,
        )

    task = Task(
        user_id=user.id,
        robot_id=robot.id,
        kind="TELEGRAM_MEMORY_PROPOSAL",
        input_text=message.text,
        scope_decision="ANSWER",
        task_class="EXTRACTION",
    )
    session.add(task)
    session.flush()
    session.add(TaskRun(task_id=task.id, status="completed"))
    proposal = create_proposed_memory(
        session=session,
        user_id=user.id,
        robot_id=robot.id,
        task_id=task.id,
        memory_type=proposal_payload["memory_type"],
        proposed_content=proposal_payload["content"],
        source_text=message.text,
        importance=proposal_payload["importance"],
    )
    reply_text = _compose_telegram_memory_proposal_reply(content=proposal.proposed_content, proposal_id=proposal.id)
    return _build_memory_loop_result(
        message=message,
        config=config,
        trace={**trace, "stage": "82P", "memory_proposal_loop": "proposal_created"},
        reply_text=reply_text,
        ok=True,
    )


def _build_memory_loop_result(
    *,
    message: TelegramRuntimeMessage,
    config: TelegramBotRuntimeConfig,
    trace: dict[str, str],
    reply_text: str,
    ok: bool,
    error_code: str | None = None,
) -> TelegramConversationLoopResult:
    hermes_request = build_hermes_request_from_telegram(message)
    hermes_response = HermesRuntimeResponse(
        status="ok" if ok else "safe_fallback",
        text=reply_text,
        task_id=None,
        safety_decision=None,
        metadata={
            "telegram_memory_proposal_loop": "active",
            "active_memory_requires_explicit_approval": "true",
            "external_source_scan": "false",
        },
    )
    return TelegramConversationLoopResult(
        ok=ok,
        message=message,
        hermes_request=hermes_request,
        hermes_response=hermes_response,
        prepared_send=prepare_telegram_text_send(chat_id=message.chat_id, text=reply_text, config=config),
        trace=trace,
        error_code=error_code,
    )


def _resolve_runtime_user_and_robot(*, session, message: TelegramRuntimeMessage) -> tuple[User, Robot]:
    user = session.query(User).filter(User.telegram_user_id == message.user_id).one_or_none()
    if user is None:
        user = User(
            telegram_user_id=message.user_id,
            first_name=message.first_name or "Telegram",
            username=message.username,
        )
        session.add(user)
        session.flush()

    robot = session.query(Robot).filter(Robot.user_id == user.id, Robot.active.is_(True)).one_or_none()
    if robot is None:
        robot = Robot(user_id=user.id, name=f"{user.first_name}'s Robot")
        session.add(robot)
        session.flush()
    return user, robot


def _extract_telegram_memory_proposal(text: str) -> dict[str, str] | None:
    stripped = text.strip()
    normalized = stripped.lower()
    for prefix in TELEGRAM_MEMORY_INTENT_PREFIXES:
        if normalized.startswith(prefix):
            raw_content = stripped[len(prefix) :].strip()
            if not raw_content:
                return None
            return _classify_telegram_memory_content(raw_content)
    return None


def _detect_telegram_memory_recall(text: str) -> str | None:
    normalized = _normalize_telegram_recall_text(text)
    if normalized in TELEGRAM_MEMORY_RECALL_PHRASES_ES:
        return "es"
    if normalized in TELEGRAM_MEMORY_RECALL_PHRASES_EN:
        return "en"
    return None


def _detect_telegram_memory_forget(text: str) -> tuple[str, str] | None:
    stripped = " ".join(text.strip().split())
    for language, pattern in TELEGRAM_MEMORY_FORGET_PATTERNS:
        match = pattern.match(stripped)
        if match is not None:
            return language, match.group(1)
    return None


def _normalize_telegram_recall_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.lstrip("¿").rstrip("?").strip()
    return " ".join(normalized.split())


def _compose_telegram_active_memory_recall_reply(*, language: str, memories: list[tuple[str, str]]) -> str:
    if not memories:
        if language == "en":
            return (
                "I do not have any approved memories about you yet. "
                "You can say \"remember that ...\" and I will ask for approval before saving it."
            )
        return (
            "Todavía no tengo memorias aprobadas sobre ti. "
            "Puedes decir \"recuerda que ...\" y te pediré aprobación antes de guardarlo."
        )

    if language == "en":
        header = "Here is what I remember about you:"
    else:
        header = "Esto es lo que recuerdo de ti:"
    lines = [header, ""]
    lines.extend(f"{index}. {content} [id: {memory_id}]" for index, (memory_id, content) in enumerate(memories, start=1))
    return "\n".join(lines)


def _classify_telegram_memory_content(raw_content: str) -> dict[str, str]:
    content = raw_content.strip().rstrip(".")
    lowered = content.lower()
    spanish_preference_prefixes = ("prefiero ", "me gusta ")
    english_preference_prefixes = ("i prefer ",)

    for prefix in spanish_preference_prefixes:
        if lowered.startswith(prefix):
            detail = content[len(prefix) :].strip()
            return {
                "memory_type": "WORK_PREFERENCE",
                "content": f"Prefieres {detail}.",
                "importance": "high",
            }
    for prefix in english_preference_prefixes:
        if lowered.startswith(prefix):
            detail = content[len(prefix) :].strip()
            return {
                "memory_type": "WORK_PREFERENCE",
                "content": f"You prefer {detail}.",
                "importance": "high",
            }
    return {
        "memory_type": "TASK_MEMORY",
        "content": f"{content}.",
        "importance": "normal",
    }


def _compose_telegram_memory_proposal_reply(*, content: str, proposal_id: str) -> str:
    return (
        "Puedo recordar esto:\n\n"
        f"\"{content}\"\n\n"
        "Responde:\n"
        f"APROBAR memoria {proposal_id}\n"
        f"RECHAZAR memoria {proposal_id}"
    )


def _extract_chat_id(update: object) -> int | None:
    if not isinstance(update, dict):
        return None
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


def _classify_parse_error(message: str) -> str:
    if "document/file" in message or "voice/audio" in message:
        return "unsupported_non_text"
    if "non-empty Telegram text" in message:
        return "empty_text"
    return "malformed_payload"


def _is_valid_public_webhook_url(webhook_url: str, *, token: str) -> bool:
    if not webhook_url:
        return False
    normalized = webhook_url.strip()
    if not normalized.startswith("https://"):
        return False
    if not normalized.endswith(TELEGRAM_RUNTIME_WEBHOOK_PATH):
        return False
    if token and token in normalized:
        return False
    if any(character.isspace() for character in normalized):
        return False
    return "." in normalized.removeprefix("https://").split("/", 1)[0]
