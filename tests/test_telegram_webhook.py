from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import MemoryItem, ProposedMemory, Task


def build_update(text: str) -> dict:
    return {
        "update_id": 10001,
        "message": {
            "message_id": 501,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {
                "id": 123456,
                "is_bot": False,
                "first_name": "Francisco",
                "username": "francisco",
            },
            "text": text
        },
    }


@pytest.mark.anyio
async def test_valid_telegram_webhook_returns_reply(client):
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["reply"]["chat_id"] == 123456
    assert body["scope_decision"] == "ANSWER"
    assert body["safety_decision"] in {"ALLOW", "DRAFT_ONLY"}


@pytest.mark.anyio
async def test_valid_telegram_webhook_persists_core_records(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_unknown_message_still_falls_through_to_general_task(client):
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "GENERAL_TASK"


@pytest.mark.anyio
async def test_memory_proposal_intent_stays_outside_registry_and_creates_pending_only(client):
    response = await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Reply APPROVE to save it or REJECT to discard it." in reply
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "MEMORY_PROPOSAL"
        assert proposal is not None
        assert proposal.status == "PENDING"
        assert memory is None


@pytest.mark.anyio
async def test_payment_execution_is_blocked(client):
    response = await client.post("/api/telegram/webhook", json=build_update("Please pay this invoice now"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK" or body["safety_decision"] == "BLOCK"


@pytest.mark.anyio
async def test_external_send_requires_confirmation(client):
    response = await client.post("/api/telegram/webhook", json=build_update("Send this follow-up email to Victor"))
    assert response.status_code == 200
    body = response.json()
    assert body["safety_decision"] == "ASK_CONFIRMATION"


@pytest.mark.anyio
async def test_professional_advice_is_refused_without_pretending(client):
    response = await client.post("/api/telegram/webhook", json=build_update("I need legal advice for this contract"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "REFUSE_SCOPE"
    assert "cannot provide legal" in body["reply"]["text"].lower() or "cannot provide" in body["reply"]["text"].lower()


@pytest.mark.anyio
async def test_invalid_telegram_payload_does_not_crash(client):
    response = await client.post("/api/telegram/webhook", json={"update_id": 10001})
    assert response.status_code == 422
