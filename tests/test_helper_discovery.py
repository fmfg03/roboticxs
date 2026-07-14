from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import func, select

from app.config import Settings, get_settings
from app.db import init_db
from app.helper_discovery import (
    HELPER_DISCOVERY_QUESTIONS,
    create_helper_context_invite,
    handle_helper_discovery,
)
from app.helper_interview import AdaptiveInterviewTurn
from app.models import (
    HelperContextInvite,
    HelperDiscoverySession,
    HelperProcessingConsent,
    MemoryItem,
    ProposedMemory,
    Robot,
    User,
)


MARIA_ID = 8891693168
OWNER_ID = 892216787


@pytest.fixture
def session(tmp_path):
    db = init_db(f"sqlite:///{tmp_path / 'helper-discovery.db'}")
    with db.session() as active_session:
        yield active_session


def settings() -> Settings:
    return Settings(
        telegram_owner_id=OWNER_ID,
        telegram_allowed_user_ids=frozenset({MARIA_ID}),
        helper_discovery_enabled=True,
        conversation_enabled=True,
    )


def make_identity(session, *, telegram_user_id: int, name: str) -> tuple[User, Robot]:
    user = User(telegram_user_id=telegram_user_id, first_name=name)
    session.add(user)
    session.flush()
    robot = Robot(user_id=user.id, name=f"{name}'s Robot")
    session.add(robot)
    session.flush()
    return user, robot


def fake_adaptive_turn(**kwargs) -> AdaptiveInterviewTurn:
    answers = kwargs["answers"]
    step = len(answers)
    ready = step >= len(HELPER_DISCOVERY_QUESTIONS)
    question = "" if ready else HELPER_DISCOVERY_QUESTIONS[min(step, len(HELPER_DISCOVERY_QUESTIONS) - 1)][1]
    return AdaptiveInterviewTurn(
        acknowledgement="Entiendo; usaré lo que acabas de contarme.",
        extracted_facts=tuple(),
        missing_topics=tuple(),
        next_question=question,
        ready_to_summarize=ready,
        support_ideas=tuple(),
        risk_level="none",
        provider="test",
        model="test",
    )


def send(
    session,
    user: User,
    robot: Robot,
    text: str,
    *,
    now: datetime | None = None,
):
    return handle_helper_discovery(
        session=session,
        settings=settings(),
        user=user,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text=text,
        first_name="María",
        summary_generator=lambda **_: "Resumen seguro con tres apoyos concretos y límites humanos.",
        turn_generator=fake_adaptive_turn,
        now=now,
    )


def test_allowed_user_ids_are_parsed_without_changing_owner(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_OWNER_ID", str(OWNER_ID))
    monkeypatch.setenv("ROBOTICXS_TELEGRAM_ALLOWED_USER_IDS", f"{OWNER_ID}, {MARIA_ID}, invalid, -10")
    configured = get_settings()

    assert configured.telegram_owner_id == OWNER_ID
    assert configured.telegram_allowed_user_ids == frozenset({OWNER_ID, MARIA_ID})
    assert configured.is_telegram_user_allowed(OWNER_ID) is True
    assert configured.is_telegram_user_allowed(MARIA_ID) is True
    assert configured.is_telegram_user_allowed(111111111) is False


def test_allowlist_fails_closed_without_founder_owner():
    configured = Settings(
        telegram_owner_id=None,
        telegram_allowed_user_ids=frozenset({MARIA_ID}),
    )

    assert configured.is_telegram_user_allowed(MARIA_ID) is False


def test_start_requests_consent_without_storing_sensitive_answers(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")

    reply = send(session, user, robot, "/start")
    record = session.scalar(select(HelperDiscoverySession))

    assert reply is not None
    assert reply.status == "WAITING_CONSENT"
    assert "Responde SÍ" in reply.reply_text
    assert "no se compartirán con Francisco" in reply.reply_text
    assert record is not None
    assert record.answers_json == "{}"
    assert record.consented_at is None


def test_declining_consent_stores_no_answers_or_memory(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    send(session, user, robot, "/start")

    reply = send(session, user, robot, "no")
    record = session.scalar(select(HelperDiscoverySession))

    assert reply is not None
    assert reply.status == "DECLINED"
    assert record is not None and record.answers_json == "{}"
    assert session.scalar(select(func.count()).select_from(ProposedMemory)) == 0
    assert session.scalar(select(func.count()).select_from(MemoryItem)) == 0


def test_interview_asks_one_question_at_a_time_and_creates_pending_profile_only(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    send(session, user, robot, "/start")
    consent = send(session, user, robot, "sí")

    assert consent is not None
    assert consent.status == "ACTIVE"
    assert HELPER_DISCOVERY_QUESTIONS[0][1] in consent.reply_text

    answers = [
        "Quiero organizar el apoyo para mi mamá.",
        "Las rutinas y pendientes se repiten y me consumen energía.",
        "Participamos mi mamá, Francisco y yo; yo coordino.",
        "Quiero guías paso a paso, recordatorios y seguimiento.",
        "No compartir nada sin preguntarme y no tomar decisiones médicas.",
    ]
    final_reply = None
    for index, answer in enumerate(answers):
        final_reply = send(session, user, robot, answer)
        assert final_reply is not None
        if index < len(answers) - 1:
            assert final_reply.status == "ACTIVE"
            expected_question = HELPER_DISCOVERY_QUESTIONS[index + 1][1].split("?", 1)[0] + "?"
            assert expected_question in final_reply.reply_text

    assert final_reply is not None
    assert final_reply.status == "READY_FOR_REVIEW"
    assert "Nada de esto es memoria activa" in final_reply.reply_text
    assert session.scalar(select(func.count()).select_from(ProposedMemory)) == 0

    saved = send(session, user, robot, "guardar perfil")
    proposal = session.scalar(select(ProposedMemory))
    record = session.scalar(select(HelperDiscoverySession))

    assert saved is not None
    assert saved.status == "COMPLETED"
    assert saved.proposal_id is not None
    assert "APROBAR memoria" in saved.reply_text
    assert proposal is not None and proposal.status == "PENDING"
    assert proposal.user_id == user.id
    assert proposal.robot_id == robot.id
    assert session.scalar(select(func.count()).select_from(MemoryItem)) == 0
    assert record is not None and record.answers_json == "{}"


def test_pause_resume_and_cancel_clear_temporary_answers(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    send(session, user, robot, "/start")
    send(session, user, robot, "sí")
    send(session, user, robot, "Necesito apoyo familiar")

    paused = send(session, user, robot, "/pausar")
    resumed = send(session, user, robot, "/continuar")
    cancelled = send(session, user, robot, "/cancelar")
    record = session.scalar(select(HelperDiscoverySession))

    assert paused is not None and paused.status == "PAUSED"
    assert resumed is not None and resumed.status == "ACTIVE"
    assert cancelled is not None and cancelled.status == "CANCELLED"
    assert record is not None and record.answers_json == "{}"
    assert record.summary is None


def test_expired_session_is_cleared(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    started = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    send(session, user, robot, "/start", now=started)
    send(session, user, robot, "sí", now=started)
    send(session, user, robot, "Dato temporal", now=started)

    expired = send(session, user, robot, "continuar", now=started + timedelta(hours=25))
    record = session.scalar(select(HelperDiscoverySession))

    assert expired is not None
    assert expired.status == "CANCELLED"
    assert "caducó" in expired.reply_text
    assert record is not None and record.answers_json == "{}"


def test_sessions_are_isolated_by_user_and_robot(session):
    maria, maria_robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    other_id = 777777777
    other, other_robot = make_identity(session, telegram_user_id=other_id, name="Otra")
    configured = Settings(
        telegram_owner_id=OWNER_ID,
        telegram_allowed_user_ids=frozenset({MARIA_ID, other_id}),
        helper_discovery_enabled=True,
    )

    for user, robot, telegram_id, answer in (
        (maria, maria_robot, MARIA_ID, "Contexto de María"),
        (other, other_robot, other_id, "Contexto de otra persona"),
    ):
        handle_helper_discovery(
            session=session,
            settings=configured,
            user=user,
            robot=robot,
            telegram_user_id=telegram_id,
            text="/start",
            first_name=user.first_name,
        )
        handle_helper_discovery(
            session=session,
            settings=configured,
            user=user,
            robot=robot,
            telegram_user_id=telegram_id,
            text="sí",
            first_name=user.first_name,
            turn_generator=fake_adaptive_turn,
        )
        handle_helper_discovery(
            session=session,
            settings=configured,
            user=user,
            robot=robot,
            telegram_user_id=telegram_id,
            text=answer,
            first_name=user.first_name,
            turn_generator=fake_adaptive_turn,
        )

    records = session.scalars(select(HelperDiscoverySession).order_by(HelperDiscoverySession.user_id)).all()
    assert len(records) == 2
    stored_answers = [json.loads(record.answers_json)["situation"] for record in records]
    assert sorted(stored_answers) == ["Contexto de María", "Contexto de otra persona"]
    assert records[0].user_id != records[1].user_id
    assert records[0].robot_id != records[1].robot_id


def test_owner_never_enters_friendly_user_discovery(session):
    owner, robot = make_identity(session, telegram_user_id=OWNER_ID, name="Francisco")

    reply = handle_helper_discovery(
        session=session,
        settings=settings(),
        user=owner,
        robot=robot,
        telegram_user_id=OWNER_ID,
        text="/start",
        first_name="Francisco",
    )

    assert reply is None
    assert session.scalar(select(func.count()).select_from(HelperDiscoverySession)) == 0


def test_openai_processing_requires_explicit_consent_and_allows_local(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    configured = Settings(
        telegram_owner_id=OWNER_ID,
        telegram_allowed_user_ids=frozenset({MARIA_ID}),
        helper_discovery_enabled=True,
        helper_interview_provider="openai",
        openai_api_key="test-key",
    )

    start = handle_helper_discovery(
        session=session,
        settings=configured,
        user=user,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text="/start",
        first_name="María",
    )
    local = handle_helper_discovery(
        session=session,
        settings=configured,
        user=user,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text="local",
        first_name="María",
        turn_generator=fake_adaptive_turn,
    )
    consent = session.scalar(select(HelperProcessingConsent))

    assert start is not None and "API de OpenAI" in start.reply_text
    assert local is not None and local.status == "ACTIVE"
    assert consent is not None and consent.status == "DECLINED"


def test_shared_context_is_hidden_until_target_accepts(session):
    owner, _ = make_identity(session, telegram_user_id=OWNER_ID, name="Francisco")
    maria, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    create_helper_context_invite(
        session=session,
        source_user_id=owner.id,
        target_user_id=maria.id,
        context_text="Hay pérdida de secuencia al preparar el pastillero semanal.",
    )

    send(session, maria, robot, "/start")
    offer = send(session, maria, robot, "sí")

    captured: dict[str, str] = {}

    def contextual_turn(**kwargs) -> AdaptiveInterviewTurn:
        captured["context"] = kwargs["shared_context"]
        return AdaptiveInterviewTurn(
            acknowledgement="Gracias; usaré esa nota solo como punto de partida.",
            extracted_facts=tuple(),
            missing_topics=("recurring_load",),
            next_question="¿Qué parte de organizar el pastillero te preocupa más?",
            ready_to_summarize=False,
            support_ideas=tuple(),
            risk_level="none",
            provider="test",
            model="test",
        )

    accepted = handle_helper_discovery(
        session=session,
        settings=settings(),
        user=maria,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text="sí",
        first_name="María",
        turn_generator=contextual_turn,
    )
    invite = session.scalar(select(HelperContextInvite))

    assert offer is not None and offer.status == "WAITING_CONTEXT_CONSENT"
    assert "pastillero" not in offer.reply_text
    assert accepted is not None and "organizar el pastillero" in accepted.reply_text
    assert "pastillero semanal" in captured["context"]
    assert invite is not None and invite.status == "ACCEPTED"


def test_existing_active_session_pauses_for_new_openai_consent(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    send(session, user, robot, "/start")
    send(session, user, robot, "sí")
    send(session, user, robot, "Estoy pendiente de mi mamá")
    before = session.scalar(select(HelperDiscoverySession))
    before_answers = before.answers_json if before is not None else ""

    configured = Settings(
        telegram_owner_id=OWNER_ID,
        telegram_allowed_user_ids=frozenset({MARIA_ID}),
        helper_discovery_enabled=True,
        helper_interview_provider="openai",
        openai_api_key="test-key",
    )
    prompt = handle_helper_discovery(
        session=session,
        settings=configured,
        user=user,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text="Quiero recordatorios",
        first_name="María",
        turn_generator=fake_adaptive_turn,
    )
    after = session.scalar(select(HelperDiscoverySession))

    assert prompt is not None and prompt.status == "WAITING_PROCESSING_CONSENT"
    assert "API de OpenAI" in prompt.reply_text
    assert after is not None and after.answers_json == before_answers


def test_adaptive_reply_references_the_latest_answer(session):
    user, robot = make_identity(session, telegram_user_id=MARIA_ID, name="María")
    send(session, user, robot, "/start")
    send(session, user, robot, "sí")

    def specific_turn(**_kwargs) -> AdaptiveInterviewTurn:
        return AdaptiveInterviewTurn(
            acknowledgement="Entonces hoy tú cargas sola con estar pendiente de tu mamá.",
            extracted_facts=("La usuaria lleva sola la responsabilidad actual.",),
            missing_topics=("desired_help",),
            next_question="¿Qué te quitaría más peso: recordatorios, rutinas o seguimiento?",
            ready_to_summarize=False,
            support_ideas=tuple(),
            risk_level="none",
            provider="test",
            model="test",
        )

    reply = handle_helper_discovery(
        session=session,
        settings=settings(),
        user=user,
        robot=robot,
        telegram_user_id=MARIA_ID,
        text="Solo yo",
        first_name="María",
        turn_generator=specific_turn,
    )

    assert reply is not None
    assert "cargas sola" in reply.reply_text
    assert "¿Qué te quitaría más peso" in reply.reply_text
    assert reply.reply_text.count("?") == 1
