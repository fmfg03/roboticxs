from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.conversation_history import (
    clear_conversation_turns,
    detect_clear_conversation_command,
    get_conversation_turn_by_source,
    list_recent_conversation_turns,
    record_conversation_turn,
)
from app.config import Settings
from app.db import init_db
from app.models import ConversationTurn


@pytest.fixture
def session(tmp_path):
    db = init_db(f"sqlite:///{tmp_path / 'history.db'}")
    with db.session() as active_session:
        yield active_session


def record(session, *, user_id: str, robot_id: str, message_id: str, text: str, reply: str, now: datetime):
    return record_conversation_turn(
        session=session,
        user_id=user_id,
        robot_id=robot_id,
        source_channel="telegram",
        source_message_id=message_id,
        user_text=text,
        assistant_text=reply,
        max_turns=6,
        ttl_minutes=120,
        now=now,
    )


def test_recent_history_is_ordered_bounded_and_isolated(session):
    base = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    for index in range(4):
        record(
            session,
            user_id="user-a",
            robot_id="robot-a",
            message_id=str(index),
            text=f"user {index}",
            reply=f"assistant {index}",
            now=base + timedelta(minutes=index),
        )
    record(
        session,
        user_id="user-b",
        robot_id="robot-b",
        message_id="other",
        text="private other user text",
        reply="private other user reply",
        now=base + timedelta(minutes=4),
    )

    turns = list_recent_conversation_turns(
        session=session,
        user_id="user-a",
        robot_id="robot-a",
        source_channel="telegram",
        max_turns=2,
        ttl_minutes=120,
        now=base + timedelta(minutes=5),
    )

    assert [(turn.user_text, turn.assistant_text) for turn in turns] == [
        ("user 2", "assistant 2"),
        ("user 3", "assistant 3"),
    ]
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 3


def test_expired_turns_are_hard_deleted(session):
    now = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)
    record(
        session,
        user_id="user-a",
        robot_id="robot-a",
        message_id="old",
        text="old user text",
        reply="old assistant text",
        now=now - timedelta(minutes=121),
    )

    turns = list_recent_conversation_turns(
        session=session,
        user_id="user-a",
        robot_id="robot-a",
        source_channel="telegram",
        max_turns=6,
        ttl_minutes=120,
        now=now,
    )

    assert turns == []
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 0


def test_duplicate_source_message_returns_original_turn(session):
    now = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)
    first = record(
        session,
        user_id="user-a",
        robot_id="robot-a",
        message_id="42",
        text="first input",
        reply="first reply",
        now=now,
    )
    duplicate = record(
        session,
        user_id="user-a",
        robot_id="robot-a",
        message_id="42",
        text="changed input",
        reply="changed reply",
        now=now + timedelta(minutes=1),
    )

    assert duplicate.id == first.id
    assert duplicate.user_text == "first input"
    assert get_conversation_turn_by_source(
        session=session,
        user_id="user-a",
        robot_id="robot-a",
        source_channel="telegram",
        source_message_id="42",
    ).assistant_text == "first reply"
    assert session.scalar(select(func.count()).select_from(ConversationTurn)) == 1


def test_clear_removes_only_target_conversation(session):
    now = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)
    record(session, user_id="user-a", robot_id="robot-a", message_id="1", text="a", reply="a", now=now)
    record(session, user_id="user-b", robot_id="robot-b", message_id="2", text="b", reply="b", now=now)

    cleared = clear_conversation_turns(
        session=session,
        user_id="user-a",
        robot_id="robot-a",
        source_channel="telegram",
    )

    assert cleared == 1
    remaining = session.scalars(select(ConversationTurn)).all()
    assert [(turn.user_id, turn.robot_id) for turn in remaining] == [("user-b", "robot-b")]


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("clear conversation", "en"),
        ("Forget this conversation", "en"),
        ("borra esta conversación", "es"),
        ("Empecemos de cero", "es"),
    ],
)
def test_clear_command_is_explicit_and_bilingual(text: str, language: str):
    assert detect_clear_conversation_command(text) == language


def test_ordinary_forget_request_is_not_misclassified_as_session_clear():
    assert detect_clear_conversation_command("forget memory 123") is None


def test_history_configuration_cannot_exceed_session_retention_caps():
    settings = Settings(
        conversation_history_max_turns=500,
        conversation_history_ttl_minutes=999999,
    )

    assert settings.conversation_history_max_turns == 6
    assert settings.conversation_history_ttl_minutes == 1440
