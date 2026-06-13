from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.db import init_db
from app.orchestrator import process_telegram_message
from app.schemas import HealthResponse, TelegramWebhookResponse
from app.skills import seed_skill_manifest
from app.telegram_adapter import normalize_telegram_update
from app.telegram_runtime import (
    build_telegram_conversation_webhook_response,
    run_telegram_conversation_loop,
)


def create_app() -> FastAPI:
    settings = get_settings()
    db = init_db(settings.database_url)
    with db.session() as session:
        seed_skill_manifest(session)

    app = FastAPI(title="Roboticxs Stage 1")
    app.state.settings = settings
    app.state.db = db

    @app.get("/health", response_model=HealthResponse)
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "roboticxs"}

    @app.post("/api/telegram/webhook", response_model=TelegramWebhookResponse)
    async def telegram_webhook(update: dict) -> dict:
        envelope = normalize_telegram_update(update)
        with app.state.db.session() as session:
            return process_telegram_message(session=session, settings=app.state.settings, envelope=envelope)

    @app.post("/api/telegram/runtime/webhook")
    async def telegram_runtime_webhook(update: dict) -> dict:
        with app.state.db.session() as session:
            result = run_telegram_conversation_loop(update=update, settings=app.state.settings, session=session)
        return build_telegram_conversation_webhook_response(result)

    return app


app = create_app()
