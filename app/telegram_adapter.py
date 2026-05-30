from __future__ import annotations

from fastapi import HTTPException

from app.schemas import TelegramDocumentMetadata, TelegramMessageEnvelope


def normalize_telegram_update(update: dict) -> TelegramMessageEnvelope:
    message = update.get("message")
    if not isinstance(message, dict):
        raise HTTPException(status_code=422, detail="Telegram update missing message payload")

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")
    first_name = sender.get("first_name")

    if not isinstance(chat_id, int) or not isinstance(telegram_user_id, int) or not isinstance(first_name, str):
        raise HTTPException(status_code=422, detail="Telegram update missing required sender fields")

    text = message.get("text")
    normalized_text = text.strip() if isinstance(text, str) and text.strip() else ""

    document = _normalize_document_metadata(message.get("document"))
    if not normalized_text and document is None:
        raise HTTPException(status_code=422, detail="Only text messages or document metadata are supported")

    return TelegramMessageEnvelope(
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        first_name=first_name,
        username=sender.get("username"),
        text=normalized_text,
        document=document,
        raw_update=update,
    )


def _normalize_document_metadata(document_payload: object) -> TelegramDocumentMetadata | None:
    if not isinstance(document_payload, dict):
        return None

    file_id = document_payload.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        return None

    file_unique_id = document_payload.get("file_unique_id")
    file_name = document_payload.get("file_name")
    mime_type = document_payload.get("mime_type")
    file_size = document_payload.get("file_size")

    return TelegramDocumentMetadata(
        file_id=file_id.strip(),
        file_unique_id=file_unique_id if isinstance(file_unique_id, str) and file_unique_id.strip() else None,
        file_name=file_name if isinstance(file_name, str) and file_name.strip() else None,
        mime_type=mime_type if isinstance(mime_type, str) and mime_type.strip() else None,
        file_size=file_size if isinstance(file_size, int) else None,
    )
