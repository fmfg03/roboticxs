from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import MemoryItem, ProposedMemory


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
RUNTIME_PATH = REPO_ROOT / "app/telegram_runtime.py"


def build_text_update(text: str = "hola", user_id: int = 82001) -> dict:
    return {
        "update_id": 82001,
        "message": {
            "message_id": 82002,
            "from": {"id": user_id, "username": "memory_user", "first_name": "Memoria"},
            "chat": {"id": user_id, "type": "private"},
            "text": text,
        },
    }


def extract_proposal_id(reply: str) -> str:
    match = re.search(r"APROBAR memoria ([0-9a-f-]{36})", reply)
    assert match is not None
    return match.group(1)


@pytest.mark.anyio
async def test_spanish_memory_intent_creates_inert_proposed_memory(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update("recuerda que prefiero respuestas cortas"),
    )

    assert response.status_code == 200
    body = response.json()
    reply = body["prepared_send"]["payload"]["text"]
    proposal_id = extract_proposal_id(reply)

    assert body["ok"] is True
    assert body["trace"]["stage"] == "82P"
    assert body["trace"]["memory_proposal_loop"] == "proposal_created"
    assert "Puedo recordar esto:" in reply
    assert '"Prefieres respuestas cortas."' in reply
    assert f"APROBAR memoria {proposal_id}" in reply
    assert f"RECHAZAR memoria {proposal_id}" in reply
    after = db_counts()
    assert after["proposals"] == before["proposals"] + 1
    assert after["memories"] == before["memories"]

    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal is not None
        assert proposal.status == "PENDING"
        assert proposal.proposed_content == "Prefieres respuestas cortas."
        assert proposal.memory_type == "WORK_PREFERENCE"
        assert session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc())) is None


@pytest.mark.anyio
async def test_english_memory_intent_creates_proposed_memory(client):
    response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update("remember that I prefer short replies", user_id=82003),
    )

    assert response.status_code == 200
    reply = response.json()["prepared_send"]["payload"]["text"]
    proposal_id = extract_proposal_id(reply)
    assert '"You prefer short replies."' in reply
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal is not None
        assert proposal.status == "PENDING"
        assert proposal.proposed_content == "You prefer short replies."


@pytest.mark.anyio
async def test_normal_text_does_not_create_proposed_memory_or_active_memory(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/runtime/webhook", json=build_text_update("hola"))

    assert response.status_code == 200
    body = response.json()
    assert body["trace"]["stage"] == "80P"
    assert body["prepared_send"]["method"] == "sendMessage"
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_approval_command_activates_memory(client, db_counts):
    proposal_response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82004),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    before_approval = db_counts()

    approval_response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update(f"APROBAR memoria {proposal_id}", user_id=82004),
    )

    assert approval_response.status_code == 200
    body = approval_response.json()
    assert body["ok"] is True
    assert body["trace"]["stage"] == "82P"
    assert body["trace"]["memory_proposal_loop"] == "approved"
    assert body["prepared_send"]["payload"]["text"] == "Listo. Guardé esa memoria local."
    after_approval = db_counts()
    assert after_approval["proposals"] == before_approval["proposals"]
    assert after_approval["memories"] == before_approval["memories"] + 1

    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        assert proposal.status == "APPROVED"
        assert memory.content == "Prefieres respuestas cortas."
        assert memory.status == "ACTIVE"


@pytest.mark.anyio
async def test_rejection_command_rejects_memory_without_active_write(client, db_counts):
    proposal_response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82005),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    before_rejection = db_counts()

    rejection_response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update(f"RECHAZAR memoria {proposal_id}", user_id=82005),
    )

    assert rejection_response.status_code == 200
    body = rejection_response.json()
    assert body["ok"] is True
    assert body["trace"]["memory_proposal_loop"] == "rejected"
    assert body["prepared_send"]["payload"]["text"] == "Listo. No guardaré esa memoria."
    after_rejection = db_counts()
    assert after_rejection["proposals"] == before_rejection["proposals"]
    assert after_rejection["memories"] == before_rejection["memories"]

    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal.status == "REJECTED"


@pytest.mark.anyio
async def test_invalid_proposal_id_fails_safely(client):
    invalid_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update(f"APROBAR memoria {invalid_id}"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error_code"] == "memory_proposal_invalid_id"
    assert body["prepared_send"]["payload"]["text"] == "No encontré una propuesta de memoria pendiente con ese ID."


@pytest.mark.anyio
async def test_duplicate_approval_and_rejection_after_approval_are_safe(client, db_counts):
    proposal_response = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82006),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post("/api/telegram/runtime/webhook", json=build_text_update(f"APROBAR memoria {proposal_id}", user_id=82006))
    after_first_approval = db_counts()

    duplicate_approval = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update(f"APROBAR memoria {proposal_id}", user_id=82006),
    )
    rejection_after_approval = await client.post(
        "/api/telegram/runtime/webhook",
        json=build_text_update(f"RECHAZAR memoria {proposal_id}", user_id=82006),
    )

    assert duplicate_approval.json()["ok"] is False
    assert duplicate_approval.json()["error_code"] == "memory_proposal_already_finalized"
    assert rejection_after_approval.json()["ok"] is False
    assert rejection_after_approval.json()["error_code"] == "memory_proposal_already_finalized"
    assert db_counts()["memories"] == after_first_approval["memories"]


def test_telegram_memory_runtime_does_not_add_forbidden_paths():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "file_retrieval",
        "document_control",
        "voice_caregiver",
        "caregiver_relay",
        "connector",
        "scheduler",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
    ]:
        assert forbidden not in text


def test_required_memory_proposal_loop_document_exists_with_decision_text():
    text = DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Why this stage exists",
        "Memory proposal loop",
        "Supported user phrases",
        "Approval commands",
        "Rejection commands",
        "Active memory creation rule",
        "Duplicate/invalid proposal behavior",
        "What is intentionally not implemented",
        "Authority boundaries",
        "Privacy boundaries",
        "Future stages unlocked",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "82P establishes a Telegram memory proposal loop.",
        "It creates proposed-memory candidates only from explicit user memory intent.",
        "It does not create active memory automatically.",
        "It does not extract memory from normal conversation.",
        "It does not scan external sources.",
        "It does not implement Context Scan.",
        "It does not implement retrieval.",
        "It does not implement connectors.",
        "It does not implement caregiver routines.",
        "It does not implement document intake.",
        "It does not implement voice handling.",
        "It requires explicit user approval before a memory becomes active.",
    ]:
        assert required in text


def test_roadmap_marks_82p_complete_without_inventing_83p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md"' in text
    assert '"tests/test_telegram_memory_proposal_loop.py"' in text
    assert '"stage_id":"83P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
