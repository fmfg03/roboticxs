from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import MemoryItem, ProposedMemory


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


@pytest.mark.anyio
async def test_memory_proposal_creates_pending_proposal_only(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    assert response.status_code == 200
    body = response.json()
    assert "Reply APPROVE to save it or REJECT to discard it." in body["reply"]["text"]
    after = db_counts()
    assert after["proposals"] == before["proposals"] + 1
    assert after["memories"] == before["memories"]
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_approve_creates_active_memory(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Saved to your robot memory."
    after = db_counts()
    assert after["memories"] == before["memories"] + 1
    assert after["tokens"] == before["tokens"] + 1
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        assert proposal.status == "APPROVED"
        assert memory.status == "ACTIVE"


@pytest.mark.anyio
async def test_reject_does_not_create_memory(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Remember this my timezone is Europe/Berlin."))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("REJECT"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Discarded. I will not remember that."
    after = db_counts()
    assert after["memories"] == before["memories"]
    assert after["tokens"] == before["tokens"] + 1
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal.status == "REJECTED"


@pytest.mark.anyio
async def test_boundary_memory_is_typed_correctly(client):
    await client.post("/api/telegram/webhook", json=build_update("Never send messages to clients without asking me first."))
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal.memory_type == "BOUNDARY_MEMORY"
        assert proposal.status == "PENDING"


@pytest.mark.anyio
async def test_approve_without_pending_returns_safe_reply(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    assert "There is no pending memory" in response.json()["reply"]["text"]
    after = db_counts()
    assert after["memories"] == before["memories"]
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_cross_user_isolation_prevents_other_user_approval(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers.", user_id=111, name="UserA"))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE", user_id=222, name="UserB"))
    assert response.status_code == 200
    assert "There is no pending memory" in response.json()["reply"]["text"]
    after = db_counts()
    assert after["memories"] == before["memories"]
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.user_id != "").order_by(ProposedMemory.created_at.desc()))
        assert proposal.status == "PENDING"


@pytest.mark.anyio
async def test_repeated_messages_reuse_same_user_and_robot(client, db_counts):
    before = db_counts()
    await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    middle = db_counts()
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    after = db_counts()
    assert middle["users"] == before["users"] + 1
    assert middle["robots"] == before["robots"] + 1
    assert after["users"] == middle["users"]
    assert after["robots"] == middle["robots"]


@pytest.mark.anyio
async def test_skill_manifest_persists_and_user_robot_are_created(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    after = db_counts()
    assert after["users"] == before["users"] + 1
    assert after["robots"] == before["robots"] + 1
    assert after["skills"] >= 1


@pytest.mark.anyio
async def test_unsafe_memory_intent_does_not_create_proposal(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("Remember that pay this invoice immediately."))
    assert response.status_code == 200
    body = response.json()
    assert "cannot save that as memory" in body["reply"]["text"].lower()
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["tasks"] == before["tasks"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_negative_my_case_does_not_trigger_memory_proposal(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("My invoice is late"))
    assert response.status_code == 200
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]
    assert response.json()["scope_decision"] in {"CLARIFY", "ANSWER"}


@pytest.mark.anyio
async def test_positive_my_name_case_still_creates_proposal(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("My name is Francisco"))
    assert response.status_code == 200
    after = db_counts()
    assert after["proposals"] == before["proposals"] + 1
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal.memory_type == "USER_PROFILE"


@pytest.mark.anyio
async def test_new_pending_proposal_expires_previous_one(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    await client.post("/api/telegram/webhook", json=build_update("Remember that my timezone is Europe/Berlin."))
    with client.app.state.db.session() as session:
        proposals = session.scalars(select(ProposedMemory).order_by(ProposedMemory.created_at.asc())).all()
        assert len(proposals) == 2
        assert proposals[0].status == "EXPIRED"
        assert proposals[1].status == "PENDING"


@pytest.mark.anyio
async def test_decision_turn_logs_token_usage(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    after = db_counts()
    assert after["tokens"] == before["tokens"] + 1
