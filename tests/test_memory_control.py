from __future__ import annotations

import pytest
from sqlalchemy import select

from app.memory_control import is_memory_control_help_request
from app.models import MemoryItem, TokenUsageEvent


def build_update(text: str, user_id: int = 123456, name: str = "Francisco") -> dict:
    return {
        "update_id": 10001,
        "message": {
            "message_id": 501,
            "date": 1710000000,
            "chat": {"id": user_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": name,
                "username": name.lower(),
            },
            "text": text,
        },
    }


async def seed_active_memory(client, text: str, user_id: int = 123456, name: str = "Francisco") -> str:
    await client.post("/api/telegram/webhook", json=build_update(text, user_id=user_id, name=name))
    await client.post("/api/telegram/webhook", json=build_update("APPROVE", user_id=user_id, name=name))
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        return memory.id


@pytest.mark.anyio
async def test_what_do_you_remember_lists_active_memories_for_same_user(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    assert response.status_code == 200
    body = response.json()
    assert memory_id in body["reply"]["text"]
    assert "Preference:" in body["reply"]["text"]


@pytest.mark.anyio
async def test_memory_listing_isolated_by_user_robot(client):
    await seed_active_memory(client, "Remember that I prefer short direct answers.", user_id=111, name="UserA")
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember", user_id=222, name="UserB"))
    assert response.status_code == 200
    assert "No tengo memorias locales aprobadas" in response.json()["reply"]["text"]


@pytest.mark.parametrize(
    "text",
    [
        "how do i control memory",
        "memory help",
        "what memory commands can i use",
        "cómo controlo tu memoria",
        "como controlo tu memoria",
        "cómo controlo lo que recuerdas",
    ],
)
def test_memory_control_help_detector_matches_explicit_help_requests(text):
    assert is_memory_control_help_request(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "what do you remember",
        "what memory proposals are pending",
        "forget memory mem_123",
        "APPROVE",
        "REJECT",
    ],
)
def test_memory_control_help_detector_does_not_match_existing_memory_commands(text):
    assert is_memory_control_help_request(text) is False


@pytest.mark.anyio
async def test_memory_control_help_response_lists_commands_and_boundaries(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("how do i control memory"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "what do you remember" in reply
    assert "what memory proposals are pending" in reply
    assert "APPROVE" in reply
    assert "REJECT" in reply
    assert "forget memory <id>" in reply
    assert "propuesta pendiente" in reply
    assert "memoria local" in reply
    assert "Solo se guarda si respondes APPROVE" in reply
    assert "REJECT la descarta" in reply
    assert "elimina una memoria local activa" in reply
    assert "No crea leads" in reply
    assert "no toca CRM" in reply
    assert "no abre pipeline" in reply
    assert "no hace handoff" in reply
    assert "no notifica a nadie" in reply
    assert "no escribe en sistemas externos" in reply
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_memory_control_help_spanish_alias_works(client):
    response = await client.post("/api/telegram/webhook", json=build_update("¿cómo controlo tu memoria?"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Puedes controlar la memoria local de Robbie" in reply
    assert "what do you remember" in reply


@pytest.mark.anyio
async def test_pending_memory_review_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "No tienes propuestas de memoria pendientes."


@pytest.mark.anyio
async def test_pending_memory_review_lists_only_pending_proposals(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Propuestas de memoria pendientes:" in reply
    assert "Preferencia de trabajo pendiente" in reply
    assert "You prefer short direct answers." in reply
    assert "Estado: pendiente de aprobación." in reply
    assert "APPROVE" in reply
    assert "REJECT" in reply
    assert "Esto es lo que recuerdo en la memoria local de tu robot:" not in reply


@pytest.mark.anyio
async def test_pending_memory_review_does_not_show_active_memories(client):
    await seed_active_memory(client, "Remember that I prefer short direct answers.")
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "No tienes propuestas de memoria pendientes."


@pytest.mark.anyio
async def test_active_memory_listing_does_not_show_pending_proposals(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preferencia de trabajo pendiente" not in reply
    assert "Estado: pendiente de aprobación." not in reply
    assert "You prefer short direct answers." not in reply


@pytest.mark.anyio
async def test_forget_memory_marks_memory_forgotten(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    response = await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Listo. Eliminé esa memoria local."
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_forgotten_memory_no_longer_appears_in_listing(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    assert response.status_code == 200
    assert memory_id not in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_other_user_cannot_forget_memory(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.", user_id=111, name="UserA")
    response = await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}", user_id=222, name="UserB"))
    assert response.status_code == 200
    assert "could not find" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "ACTIVE"


@pytest.mark.anyio
async def test_normal_task_uses_only_active_memory_context(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    assert "used your saved" not in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_normal_task_with_active_memory_shows_context_indicator(client, db_counts):
    await seed_active_memory(client, "Remember that I prefer short direct answers.")
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    assert "used your saved preferences" in response.json()["reply"]["text"].lower()
    after = db_counts()
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_memory_list_and_forget_turns_log_tokens(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    with client.app.state.db.session() as session:
        before = len(session.scalars(select(TokenUsageEvent)).all())
    await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    with client.app.state.db.session() as session:
        after = len(session.scalars(select(TokenUsageEvent)).all())
    assert after == before + 2


@pytest.mark.anyio
async def test_pending_memory_review_isolated_by_user_robot(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers.", user_id=111, name="UserA"))
    response = await client.post(
        "/api/telegram/webhook",
        json=build_update("what memory proposals are pending", user_id=222, name="UserB"),
    )
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "No tienes propuestas de memoria pendientes."
