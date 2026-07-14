from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.db import init_db
from app.models import ConversationTurn
from app.robbie_conversation import RobbieConversationError, RobbieConversationReply
from app.telegram_runtime import run_telegram_conversation_loop


def build_update(text: str, *, message_id: int, user_id: int = 3003) -> dict:
    return {
        "update_id": 8000 + message_id,
        "message": {
            "message_id": message_id,
            "from": {"id": user_id, "first_name": "Test"},
            "chat": {"id": user_id, "type": "private"},
            "text": text,
        },
    }


@pytest.fixture
def session(tmp_path):
    db = init_db(f"sqlite:///{tmp_path / 'runtime-history.db'}")
    with db.session() as active_session:
        yield active_session


def history_settings() -> Settings:
    return Settings(
        conversation_enabled=True,
        conversation_history_enabled=True,
        conversation_history_max_turns=6,
        conversation_history_ttl_minutes=120,
    )


def test_second_message_receives_first_turn_as_session_context(session):
    calls: list[dict[str, object]] = []

    def generate(**kwargs) -> RobbieConversationReply:
        calls.append(kwargs)
        return RobbieConversationReply(
            text="First answer" if len(calls) == 1 else "Second answer",
            provider="ollama_local",
            model="test-model",
            input_tokens=10,
            output_tokens=4,
        )

    first = run_telegram_conversation_loop(
        update=build_update("I have a report and a call", message_id=1),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )
    second = run_telegram_conversation_loop(
        update=build_update("Which should I do first?", message_id=2),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )

    assert first.trace["dispatch"] == "robbie_local_model"
    assert second.trace["dispatch"] == "robbie_local_model"
    assert calls[0]["recent_turns"] == []
    assert calls[1]["recent_turns"] == [("I have a report and a call", "First answer")]
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 2


def test_telegram_retry_replays_saved_answer_without_second_model_call(session):
    calls = 0

    def generate(**_) -> RobbieConversationReply:
        nonlocal calls
        calls += 1
        return RobbieConversationReply(
            text="Stable answer",
            provider="ollama_local",
            model="test-model",
            input_tokens=10,
            output_tokens=4,
        )

    update = build_update("Help me prioritize", message_id=33)
    first = run_telegram_conversation_loop(
        update=update,
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )
    retry = run_telegram_conversation_loop(
        update=update,
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )

    assert calls == 1
    assert retry.trace["dispatch"] == "robbie_conversation_replay"
    assert retry.prepared_send.payload == first.prepared_send.payload
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 1


def test_guarded_request_is_not_retained(session):
    def generate(**_):
        raise AssertionError("guarded request must not reach the model")

    result = run_telegram_conversation_loop(
        update=build_update("Send an email to the client", message_id=44),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )

    assert result.trace["dispatch"] == "robbie_action_boundary"
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 0


def test_failed_model_request_is_not_retained(session):
    def generate(**_):
        raise RobbieConversationError("provider unavailable")

    result = run_telegram_conversation_loop(
        update=build_update("Help me prioritize", message_id=45),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )

    assert result.trace["dispatch"] == "robbie_local_model_fallback"
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 0


def test_clear_command_deletes_recent_turns_without_model_call(session):
    def generate(**_) -> RobbieConversationReply:
        return RobbieConversationReply(
            text="Stored answer",
            provider="ollama_local",
            model="test-model",
            input_tokens=10,
            output_tokens=4,
        )

    run_telegram_conversation_loop(
        update=build_update("My temporary topic", message_id=50),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=generate,
    )

    def fail_generate(**_):
        raise AssertionError("clear command must not reach the model")

    cleared = run_telegram_conversation_loop(
        update=build_update("clear conversation", message_id=51),
        settings=history_settings(),
        session=session,
        conversation_reply_generator=fail_generate,
    )

    assert cleared.trace["dispatch"] == "robbie_conversation_clear"
    assert "approved memories were not changed" in str(cleared.prepared_send.payload["text"])
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 0
