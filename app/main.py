from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.db import init_db
from app.orchestrator import process_telegram_message
from app.schemas import HealthResponse, TelegramWebhookResponse
from app.skills import seed_skill_manifest
from app.telegram_adapter import normalize_telegram_update


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

    return app


app = create_app()
