from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models import ConversationTurn


CLEAR_CONTEXT_COMMANDS = {
    "en": {
        "clear conversation",
        "clear this conversation",
        "forget this conversation",
        "start over",
    },
    "es": {
        "borra esta conversación",
        "borra esta conversacion",
        "olvida esta conversación",
        "olvida esta conversacion",
        "empecemos de cero",
    },
}
CONVERSATION_CLEARED_REPLY = {
    "en": "Done. I cleared this conversation's recent context. Your approved memories were not changed.",
    "es": "Listo. Borré el contexto reciente de esta conversación. Tus memorias aprobadas no cambiaron.",
}


def detect_clear_conversation_command(text: str) -> str | None:
    normalized = " ".join(text.strip().lower().lstrip("¿").rstrip("?").split())
    for language, commands in CLEAR_CONTEXT_COMMANDS.items():
        if normalized in commands:
            return language
    return None


def get_conversation_turn_by_source(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    source_channel: str,
    source_message_id: str,
) -> ConversationTurn | None:
    return session.scalar(
        select(ConversationTurn).where(
            ConversationTurn.user_id == user_id,
            ConversationTurn.robot_id == robot_id,
            ConversationTurn.source_channel == source_channel,
            ConversationTurn.source_message_id == source_message_id,
        )
    )


def list_recent_conversation_turns(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    source_channel: str,
    max_turns: int,
    ttl_minutes: int,
    now: datetime | None = None,
) -> list[ConversationTurn]:
    prune_conversation_turns(
        session=session,
        user_id=user_id,
        robot_id=robot_id,
        source_channel=source_channel,
        max_turns=max_turns,
        ttl_minutes=ttl_minutes,
        now=now,
    )
    newest_first = session.scalars(
        select(ConversationTurn)
        .where(
            ConversationTurn.user_id == user_id,
            ConversationTurn.robot_id == robot_id,
            ConversationTurn.source_channel == source_channel,
        )
        .order_by(desc(ConversationTurn.created_at))
        .limit(max_turns)
    ).all()
    return list(reversed(newest_first))


def record_conversation_turn(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    source_channel: str,
    source_message_id: str,
    user_text: str,
    assistant_text: str,
    max_turns: int,
    ttl_minutes: int,
    now: datetime | None = None,
) -> ConversationTurn:
    existing = get_conversation_turn_by_source(
        session=session,
        user_id=user_id,
        robot_id=robot_id,
        source_channel=source_channel,
        source_message_id=source_message_id,
    )
    if existing is not None:
        return existing
    turn = ConversationTurn(
        user_id=user_id,
        robot_id=robot_id,
        source_channel=source_channel,
        source_message_id=source_message_id,
        user_text=user_text.strip()[:8000],
        assistant_text=assistant_text.strip()[:3900],
        created_at=now or datetime.now(timezone.utc),
    )
    session.add(turn)
    session.flush()
    prune_conversation_turns(
        session=session,
        user_id=user_id,
        robot_id=robot_id,
        source_channel=source_channel,
        max_turns=max_turns,
        ttl_minutes=ttl_minutes,
        now=now,
    )
    return turn


def clear_conversation_turns(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    source_channel: str,
) -> int:
    result = session.execute(
        delete(ConversationTurn).where(
            ConversationTurn.user_id == user_id,
            ConversationTurn.robot_id == robot_id,
            ConversationTurn.source_channel == source_channel,
        ).execution_options(synchronize_session=False)
    )
    return int(result.rowcount or 0)


def prune_conversation_turns(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    source_channel: str,
    max_turns: int,
    ttl_minutes: int,
    now: datetime | None = None,
) -> None:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(minutes=ttl_minutes)
    scope = (
        ConversationTurn.user_id == user_id,
        ConversationTurn.robot_id == robot_id,
        ConversationTurn.source_channel == source_channel,
    )
    session.execute(
        delete(ConversationTurn)
        .where(*scope, ConversationTurn.created_at < cutoff)
        .execution_options(synchronize_session=False)
    )
    excess_ids = session.scalars(
        select(ConversationTurn.id)
        .where(*scope)
        .order_by(desc(ConversationTurn.created_at))
        .offset(max_turns)
    ).all()
    if excess_ids:
        session.execute(
            delete(ConversationTurn)
            .where(ConversationTurn.id.in_(excess_ids))
            .execution_options(synchronize_session=False)
        )
