from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import MemoryItem, ProposedMemory
from app.telegram_runtime import _detect_telegram_memory_forget


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md"
FORGET_DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_ACTIVE_MEMORY_FORGET_v0_1.md"
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


def extract_recall_memory_ids(reply: str) -> list[str]:
    return re.findall(r"\[id: ([0-9a-f-]{36})\]", reply)


def test_detect_telegram_memory_forget_supports_authorized_phrases():
    memory_id = "00000000-0000-0000-0000-000000000084"

    for phrase in [
        "olvida memoria",
        "olvidar memoria",
        "borra memoria",
        "elimina memoria",
    ]:
        assert _detect_telegram_memory_forget(f"{phrase} {memory_id}") == ("es", memory_id)

    for phrase in [
        "forget memory",
        "delete memory",
        "remove memory",
        "forget memoria",
    ]:
        assert _detect_telegram_memory_forget(f"{phrase} {memory_id}") == ("en", memory_id)


async def create_approved_memory(client, *, user_id: int, text: str = "remember that I prefer short replies") -> str:
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(text, user_id=user_id),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"APPROVE memory {proposal_id}", user_id=user_id),
    )
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal is not None
        memory = session.scalar(
            select(MemoryItem).where(
                MemoryItem.user_id == proposal.user_id,
                MemoryItem.robot_id == proposal.robot_id,
                MemoryItem.content == proposal.proposed_content,
                MemoryItem.status == "ACTIVE",
            )
        )
        assert memory is not None
        return memory.id


@pytest.mark.anyio
async def test_spanish_memory_intent_creates_inert_proposed_memory(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/runtime/diagnostic",
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
        "/api/telegram/runtime/diagnostic",
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
    response = await client.post("/api/telegram/runtime/diagnostic", json=build_text_update("hola"))

    assert response.status_code == 200
    body = response.json()
    assert body["trace"]["stage"] == "80P"
    assert body["prepared_send"]["method"] == "sendMessage"
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_spanish_memory_recall_empty_state_does_not_create_memory(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("¿qué recuerdas de mí?", user_id=83001),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["trace"]["stage"] == "83P"
    assert body["trace"]["active_memory_recall"] == "listed"
    assert body["prepared_send"]["payload"]["text"] == (
        "Todavía no tengo memorias aprobadas sobre ti. "
        'Puedes decir "recuerda que ..." y te pediré aprobación antes de guardarlo.'
    )
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_english_memory_recall_empty_state_does_not_create_memory(client, db_counts):
    before = db_counts()
    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("what do you remember about me?", user_id=83002),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trace"]["stage"] == "83P"
    assert body["prepared_send"]["payload"]["text"] == (
        "I do not have any approved memories about you yet. "
        'You can say "remember that ..." and I will ask for approval before saving it.'
    )
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]


@pytest.mark.anyio
async def test_memory_recall_lists_only_approved_active_memories_after_approval(client):
    first_proposal = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=83003),
    )
    first_id = extract_proposal_id(first_proposal.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"APROBAR memoria {first_id}", user_id=83003),
    )
    second_proposal = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer direct answers", user_id=83003),
    )
    second_id = extract_proposal_id(second_proposal.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"APPROVE memory {second_id}", user_id=83003),
    )

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("show my memories", user_id=83003),
    )

    assert response.status_code == 200
    reply = response.json()["prepared_send"]["payload"]["text"]
    assert reply.startswith("Here is what I remember about you:\n\n")
    assert "1. You prefer direct answers." in reply
    assert "2. Prefieres respuestas cortas." in reply
    assert len(extract_recall_memory_ids(reply)) == 2


@pytest.mark.anyio
async def test_memory_recall_excludes_pending_proposals(client):
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer short replies", user_id=83004),
    )
    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("what do you remember", user_id=83004),
    )

    assert response.status_code == 200
    reply = response.json()["prepared_send"]["payload"]["text"]
    assert "I do not have any approved memories about you yet." in reply
    assert "You prefer short replies." not in reply


@pytest.mark.anyio
async def test_memory_recall_excludes_rejected_proposals(client):
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer short replies", user_id=83005),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"REJECT memory {proposal_id}", user_id=83005),
    )

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("list my memories", user_id=83005),
    )

    assert response.status_code == 200
    reply = response.json()["prepared_send"]["payload"]["text"]
    assert "I do not have any approved memories about you yet." in reply
    assert "You prefer short replies." not in reply


@pytest.mark.anyio
async def test_memory_recall_isolated_by_telegram_user_and_robot(client):
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer short replies", user_id=83006),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"APPROVE memory {proposal_id}", user_id=83006),
    )

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("what do you know about me?", user_id=83007),
    )

    assert response.status_code == 200
    reply = response.json()["prepared_send"]["payload"]["text"]
    assert "I do not have any approved memories about you yet." in reply
    assert "You prefer short replies." not in reply


@pytest.mark.anyio
async def test_spanish_forget_command_deactivates_active_memory(client):
    memory_id = await create_approved_memory(
        client,
        user_id=84001,
        text="recuerda que prefiero respuestas cortas",
    )

    forget_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"olvida memoria {memory_id}", user_id=84001),
    )
    recall_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("muéstrame mis memorias", user_id=84001),
    )

    assert forget_response.status_code == 200
    body = forget_response.json()
    assert body["ok"] is True
    assert body["trace"]["stage"] == "84P"
    assert body["trace"]["active_memory_forget"] == "forgotten"
    assert body["prepared_send"]["payload"]["text"] == "Listo. Olvidé esa memoria."
    assert recall_response.json()["prepared_send"]["payload"]["text"].startswith("Todavía no tengo memorias aprobadas")
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_english_forget_command_deactivates_active_memory(client):
    memory_id = await create_approved_memory(client, user_id=84002)

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"forget memory {memory_id}", user_id=84002),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["trace"]["stage"] == "84P"
    assert body["prepared_send"]["payload"]["text"] == "Done. I forgot that memory."
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_forget_pending_proposal_id_fails_without_changing_proposal(client):
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer direct answers", user_id=84003),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"forget memory {proposal_id}", user_id=84003),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["trace"]["stage"] == "84P"
    assert body["prepared_send"]["payload"]["text"] == "I could not find an active memory with that id."
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal.status == "PENDING"
        assert session.scalar(select(MemoryItem).where(MemoryItem.id == proposal_id)) is None


@pytest.mark.anyio
async def test_forget_rejected_proposal_id_fails_without_changing_proposal(client):
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remember that I prefer short replies", user_id=84004),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"REJECT memory {proposal_id}", user_id=84004),
    )

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"forget memory {proposal_id}", user_id=84004),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["prepared_send"]["payload"]["text"] == "I could not find an active memory with that id."
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).where(ProposedMemory.id == proposal_id))
        assert proposal.status == "REJECTED"


@pytest.mark.anyio
async def test_forget_other_users_active_memory_fails_without_leaking_or_changing_it(client):
    memory_id = await create_approved_memory(client, user_id=84005)

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"delete memory {memory_id}", user_id=84006),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["trace"]["active_memory_forget"] == "not_found"
    assert body["prepared_send"]["payload"]["text"] == "I could not find an active memory with that id."
    assert memory_id not in body["prepared_send"]["payload"]["text"]
    with client.app.state.db.session() as session:
        memory = session.scalar(select(MemoryItem).where(MemoryItem.id == memory_id))
        assert memory.status == "ACTIVE"


@pytest.mark.anyio
async def test_invalid_forget_id_returns_safe_failure(client):
    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("remove memory not-a-valid-id", user_id=84007),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["trace"]["stage"] == "84P"
    assert body["prepared_send"]["payload"]["text"] == "I could not find an active memory with that id."


@pytest.mark.anyio
async def test_already_forgotten_memory_returns_same_safe_failure(client):
    memory_id = await create_approved_memory(client, user_id=84008)
    await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"forget memory {memory_id}", user_id=84008),
    )

    response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"forget memory {memory_id}", user_id=84008),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["trace"]["active_memory_forget"] == "not_found"
    assert body["prepared_send"]["payload"]["text"] == "I could not find an active memory with that id."


@pytest.mark.anyio
async def test_approval_command_activates_memory(client, db_counts):
    proposal_response = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82004),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    before_approval = db_counts()

    approval_response = await client.post(
        "/api/telegram/runtime/diagnostic",
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
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82005),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    before_rejection = db_counts()

    rejection_response = await client.post(
        "/api/telegram/runtime/diagnostic",
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
        "/api/telegram/runtime/diagnostic",
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
        "/api/telegram/runtime/diagnostic",
        json=build_text_update("recuerda que prefiero respuestas cortas", user_id=82006),
    )
    proposal_id = extract_proposal_id(proposal_response.json()["prepared_send"]["payload"]["text"])
    await client.post("/api/telegram/runtime/diagnostic", json=build_text_update(f"APROBAR memoria {proposal_id}", user_id=82006))
    after_first_approval = db_counts()

    duplicate_approval = await client.post(
        "/api/telegram/runtime/diagnostic",
        json=build_text_update(f"APROBAR memoria {proposal_id}", user_id=82006),
    )
    rejection_after_approval = await client.post(
        "/api/telegram/runtime/diagnostic",
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


def test_required_active_memory_forget_document_exists_with_boundary_text():
    text = FORGET_DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Runtime path",
        "Intent precedence",
        "Supported forget phrases",
        "Success responses",
        "Safe failure responses",
        "Forget rule",
        "Recall ID visibility",
        "What is intentionally not implemented",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "Stage 84P is implemented pending review.",
        "84P adds deterministic active-memory forget commands to the Telegram runtime webhook.",
        "POST /api/telegram/runtime/webhook",
        "POST /api/telegram/webhook",
        "approval/rejection",
        "active memory forget",
        "active memory recall",
        "The failure response is identical for missing, inactive, invalid, already-forgotten, and foreign IDs.",
        "It only transitions `ACTIVE` memory to `FORGOTTEN`",
        "1. <memory content> [id: <memory_id>]",
        "85P",
        "`NEXT_ELIGIBLE`",
    ]:
        assert required in text


def test_roadmap_marks_84p_closed_and_85p_pending_without_inventing_86p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md"' in text
    assert '"tests/test_telegram_memory_proposal_loop.py"' in text
    assert '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"docs/reference/TELEGRAM_ACTIVE_MEMORY_FORGET_v0_1.md"' in text
    assert '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"87P"' in text
    assert '"stage_id":"87P","stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"88P"' in text
    assert '"stage_id":"88P","stage_name":"Routine Wake Gate / Zero-Token Preflight v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"89P"' in text
    assert '"stage_id":"89P","stage_name":"Roboticxs Automation Blueprints v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"90P"' in text
    assert '"stage_id":"90P","stage_name":"Roboticxs Command Surface Policy v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"91P"' in text
    assert '"stage_id":"91P","stage_name":"Skill Activation Scope Guard v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"92P"' in text
    assert '"stage_id":"92P","stage_name":"Hermes Tool Authority Guard v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"94P"' in text
    assert '"next_eligible_stage_name":"Telegram MVP on Hermes Gateway v0"' in text
    assert '"stage_id":"93P","stage_name":"Roboticxs Memory Center Bridge v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"94P","stage_name":"Telegram MVP on Hermes Gateway v0","status":"CLOSED_COMMITTED"' in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
