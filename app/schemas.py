from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TelegramDocumentMetadata(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramReply(BaseModel):
    chat_id: int
    text: str


class TelegramWebhookResponse(BaseModel):
    ok: bool
    reply: TelegramReply
    task_id: str
    scope_decision: str
    safety_decision: str
    model_route_decision_id: str
    token_usage_event_id: str


class HealthResponse(BaseModel):
    status: str
    service: str


class TelegramMessageEnvelope(BaseModel):
    chat_id: int
    telegram_user_id: int
    first_name: str
    username: str | None
    text: str
    document: TelegramDocumentMetadata | None = None
    raw_update: dict[str, Any]
