from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.caregiver_telegram_mvp import (
    CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH,
    run_caregiver_telegram_mvp,
    serialize_caregiver_telegram_mvp_result,
)
from app.db import init_db
from app.orchestrator import process_telegram_message
from app.routine_execution_engine import (
    RoutineDefinition,
    execute_routine_locally,
    serialize_routine_run,
)
from app.schemas import HealthResponse, TelegramWebhookResponse
from app.skills import seed_skill_manifest
from app.telegram_adapter import normalize_telegram_update
from app.telegram_runtime import (
    build_telegram_conversation_webhook_response,
    run_telegram_conversation_loop,
)
from app.telegram_policy_chain import (
    serialize_policy_chain_result,
    run_telegram_policy_chain,
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
        message = update.get("message") if isinstance(update, dict) else None
        sender = message.get("from") if isinstance(message, dict) else None
        chat = message.get("chat") if isinstance(message, dict) else None
        sender_id = sender.get("id") if isinstance(sender, dict) else None
        chat_type = chat.get("type") if isinstance(chat, dict) else None
        if (
            not isinstance(sender_id, int)
            or not app.state.settings.is_telegram_user_allowed(sender_id)
            or (
                sender_id != app.state.settings.telegram_owner_id
                and chat_type != "private"
            )
        ):
            return {}
        with app.state.db.session() as session:
            result = run_telegram_conversation_loop(update=update, settings=app.state.settings, session=session)
        if result.prepared_send is None:
            return {}
        return {
            "method": result.prepared_send.method,
            **result.prepared_send.payload,
        }

    @app.post("/api/telegram/runtime/diagnostic")
    async def telegram_runtime_diagnostic(update: dict) -> dict:
        with app.state.db.session() as session:
            result = run_telegram_conversation_loop(update=update, settings=app.state.settings, session=session)
        return build_telegram_conversation_webhook_response(result)

    @app.post("/api/telegram/policy-chain/webhook")
    async def telegram_policy_chain_webhook(update: dict) -> dict:
        with app.state.db.session() as session:
            result = run_telegram_policy_chain(update=update, settings=app.state.settings, session=session)
        return serialize_policy_chain_result(result)

    @app.post(CAREGIVER_TELEGRAM_MVP_WEBHOOK_PATH)
    async def caregiver_telegram_mvp_webhook(update: dict) -> dict:
        with app.state.db.session() as session:
            result = run_caregiver_telegram_mvp(update=update, settings=app.state.settings, session=session)
        return serialize_caregiver_telegram_mvp_result(result)

    @app.post("/api/routines/local-execute")
    async def routine_local_execute(payload: dict) -> dict:
        definition = RoutineDefinition(
            routine_id=str(payload.get("routine_id", "local_routine")),
            label=str(payload.get("label", "Local routine")),
            trigger_text=str(payload.get("trigger_text", "")),
            kind=str(payload.get("kind", "general")),
            explicit_user_approved=bool(payload.get("explicit_user_approved", True)),
            manual_start_required=bool(payload.get("manual_start_required", True)),
            wake_signal_present=bool(payload.get("wake_signal_present", True)),
            budget_preflight_allowed=bool(payload.get("budget_preflight_allowed", True)),
        )
        update = payload.get("update")
        if not isinstance(update, dict):
            update = {
                "update_id": 98001,
                "message": {
                    "message_id": 980,
                    "date": 1710000000,
                    "chat": {"id": 98001, "type": "private"},
                    "from": {"id": 98001, "is_bot": False, "first_name": "Routine"},
                    "text": definition.trigger_text,
                },
            }
        with app.state.db.session() as session:
            run = execute_routine_locally(
                definition=definition,
                update=update,
                settings=app.state.settings,
                session=session,
                force_failure=bool(payload.get("force_failure", False)),
            )
        return serialize_routine_run(run)

    return app


app = create_app()
