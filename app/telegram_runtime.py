from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.hermes_runtime import (
    HermesRuntimeRequest,
    HermesRuntimeResponse,
    dispatch_hermes_runtime_request,
)


TELEGRAM_RUNTIME_CHANNEL = "telegram"


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
