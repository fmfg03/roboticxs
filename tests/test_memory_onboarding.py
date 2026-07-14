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


@pytest.mark.anyio
async def test_business_automation_request_alone_does_not_create_upgrade_interest_proposal(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_update("¿Puedes automatizar mi CRM y crear leads para mi equipo?"),
    )
    assert response.status_code == 200
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_explicit_agentius_interest_creates_pending_upgrade_interest_proposal(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "propuesta local de interés" in reply
    assert "apruebes o rechaces" in reply
    assert "visible para ti" in reply
    assert "la podrás borrar después" in reply
    assert "No voy a crear un lead" in reply
    assert "abrir pipeline" in reply
    assert "avisar a nadie" in reply
    assert "hacer handoff" in reply
    assert "CRM" in reply
    assert "usar conectores" in reply
    assert "abrir navegador" in reply
    assert "mandar email o WhatsApp" in reply
    assert "tocar sistemas externos" in reply
    assert "Responde APPROVE para guardarla como memoria local" in reply
    assert "REJECT para descartarla" in reply
    assert "automatizar seguimiento de clientes en CRM" in reply
    after = db_counts()
    assert after["proposals"] == before["proposals"] + 1
    assert after["memories"] == before["memories"]
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal.memory_type == "UPGRADE_INTEREST"
        assert proposal.status == "PENDING"
        assert proposal.proposed_content == "Interés local para revisar después con Agentius: automatizar seguimiento de clientes en CRM."


@pytest.mark.anyio
async def test_approve_upgrade_interest_creates_active_local_memory(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Guarda este interés de Agentius: automatizar seguimiento de clientes en CRM."))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Guardado como nota local de interés" in reply
    assert "no crea lead" in reply
    assert "no abre pipeline" in reply
    assert "no avisa a nadie" in reply
    assert "no hace handoff" in reply
    assert "no toca CRM" in reply
    assert "no usa conectores" in reply
    assert "no abre navegador" in reply
    assert "no manda email o WhatsApp" in reply
    assert "no toca sistemas externos" in reply
    after = db_counts()
    assert after["memories"] == before["memories"] + 1
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        assert proposal.status == "APPROVED"
        assert memory.status == "ACTIVE"
        assert memory.memory_type == "UPGRADE_INTEREST"
        assert memory.display_label == "Interés local"
        assert memory.content == "Interés local para revisar después con Agentius: automatizar seguimiento de clientes en CRM."


@pytest.mark.anyio
async def test_reject_upgrade_interest_does_not_create_memory(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Quiero revisar esto para Agentius después."))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("REJECT"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Discarded. I will not remember that."
    after = db_counts()
    assert after["memories"] == before["memories"]
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal.status == "REJECTED"


@pytest.mark.anyio
async def test_pending_upgrade_interest_is_visible_in_pending_memory_review(client):
    await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Propuestas de memoria pendientes:" in reply
    assert "Interés local pendiente" in reply
    assert "Interés local para revisar después con Agentius: automatizar seguimiento de clientes en CRM." in reply
    assert "Estado: pendiente de aprobación." in reply
    assert "Esto no crea lead, CRM, pipeline, handoff, notificación, connectors, browser, email/WhatsApp ni external writes." in reply
    assert "Responde APPROVE para guardarla como memoria local, o REJECT para descartarla." in reply
    assert "memoria local de tu robot" not in reply
    assert "guardado como nota local de interés" not in reply.lower()


@pytest.mark.anyio
async def test_approved_upgrade_interest_is_visible_in_memory_listing(client):
    await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto como algo que quiero revisar para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "memoria local de tu robot" in reply
    assert "Interés local:" in reply
    assert "Interés local para revisar después con Agentius: automatizar seguimiento de clientes en CRM." in reply
    assert "lead" not in reply.lower()
    assert "pipeline" not in reply.lower()
    assert "oportunidad comercial" not in reply.lower()
    assert "crm record" not in reply.lower()
    assert "sync to crm" not in reply.lower()
    assert "enviado a agentius" not in reply.lower()
    assert "handoff" not in reply.lower()
    assert "notificación" not in reply.lower()
    assert "crm conectado" not in reply.lower()


@pytest.mark.anyio
async def test_approved_upgrade_interest_can_be_forgotten_with_existing_memory_flow(client):
    await client.post("/api/telegram/webhook", json=build_update("Guarda esto para Agentius después."))
    await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        memory_id = memory.id
    response = await client.post("/api/telegram/webhook", json=build_update(f"forget memory {memory_id}"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert reply == "Listo. Eliminé esa memoria local."
    assert "lead" not in reply.lower()
    assert "pipeline" not in reply.lower()
    assert "handoff" not in reply.lower()
    assert "notificación" not in reply.lower()
    assert "crm" not in reply.lower()
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_mixed_memory_listing_keeps_normal_and_upgrade_interest_local_and_clear(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto como algo que quiero revisar para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    response = await client.post("/api/telegram/webhook", json=build_update("what do you remember"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preference:" in reply
    assert "Interés local:" in reply
    assert "automatizar seguimiento de clientes en CRM" in reply
    assert "lead" not in reply.lower()
    assert "pipeline" not in reply.lower()
    assert "oportunidad" not in reply.lower()
    assert "enviado" not in reply.lower()
    assert "handoff" not in reply.lower()
    assert "notificación" not in reply.lower()
    assert "crm conectado" not in reply.lower()


@pytest.mark.anyio
async def test_approved_upgrade_interest_disappears_from_pending_memory_review_and_stays_only_active(client):
    await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "No tienes propuestas de memoria pendientes."


@pytest.mark.anyio
async def test_rejected_upgrade_interest_disappears_from_pending_memory_review_and_stays_inactive(client):
    await client.post(
        "/api/telegram/webhook",
        json=build_update("Guarda esto para Agentius después: automatizar seguimiento de clientes en CRM."),
    )
    await client.post("/api/telegram/webhook", json=build_update("REJECT"))
    response = await client.post("/api/telegram/webhook", json=build_update("what memory proposals are pending"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "No tienes propuestas de memoria pendientes."


@pytest.mark.anyio
@pytest.mark.parametrize(
    "text",
    [
        "sí, me interesa",
        "me interesa",
        "sí, guárdalo",
    ],
)
async def test_isolated_follow_up_interest_messages_do_not_create_upgrade_interest_proposal(client, db_counts, text):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update(text))
    assert response.status_code == 200
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]
