from __future__ import annotations

import pytest
from sqlalchemy import select

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
    assert "do not have any approved memories" in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_forget_memory_marks_memory_forgotten(client):
    memory_id = await seed_active_memory(client, "Remember that I prefer short direct answers.")
    response = await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Forgotten. I will no longer use that memory."
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
