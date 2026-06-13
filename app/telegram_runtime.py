from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.hermes_runtime import (
    HermesRuntimeRequest,
    HermesRuntimeResponse,
    dispatch_hermes_runtime_request,
)


TELEGRAM_RUNTIME_CHANNEL = "telegram"
TELEGRAM_CONVERSATION_REPLY = (
    "Hermes runtime foundation is available. Telegram/channel integration is active. "
    "Full skills are not implemented yet."
)
TELEGRAM_EMPTY_TEXT_REPLY = "No recibí texto para procesar."
TELEGRAM_UNSUPPORTED_REPLY = "Por ahora solo puedo procesar mensajes de texto."
TELEGRAM_MALFORMED_REPLY = "No pude procesar ese mensaje por ahora."


class TelegramRuntimeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TelegramBotRuntimeConfig:
    token_configured: bool


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
