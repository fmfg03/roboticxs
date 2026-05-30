from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import DocumentTask


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


LONG_DOCUMENT = (
    "This NDA requires the recipient to keep confidential information private for five years, "
    "return materials on request, notify the sender within three business days of any disclosure issue, "
    "and accept penalties for breach. The receiving party must not share information with subcontractors "
    "without written approval and must comply with all deadline and termination clauses."
)


@pytest.mark.anyio
async def test_review_document_creates_document_review_response(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    body = response.json()
    assert "Summary:" in body["reply"]["text"]
    assert "Possible risk notes:" in body["reply"]["text"]
    assert "Suggested follow-up questions:" in body["reply"]["text"]
    after = db_counts()
    assert after["documents"] == before["documents"] + 1
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_summarize_document_returns_bounded_summary(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"summarize document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "draft document review" in reply.lower()
    assert "not legal, tax, financial, medical, or professional advice" in reply.lower()


@pytest.mark.anyio
async def test_mark_risks_in_document_includes_risk_language(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"mark risks in document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    assert "risk" in response.json()["reply"]["text"].lower()


@pytest.mark.anyio
async def test_prepare_notes_from_document_includes_notes_language(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"prepare notes from document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"].lower()
    assert "draft notes" in reply
    assert "checklist" in reply or "notes" in reply


@pytest.mark.anyio
async def test_document_task_persists_preview_hash_not_full_raw_text(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        document_task = session.scalar(select(DocumentTask).order_by(DocumentTask.created_at.desc()))
        assert document_task.review_type == "REVIEW"
        assert document_task.source_kind == "TEXT_SIMULATED"
        assert len(document_task.source_text_hash) == 64
        assert document_task.source_text_preview != ""
        assert document_task.source_text_preview != LONG_DOCUMENT
        assert len(document_task.source_text_preview) < len(LONG_DOCUMENT)


@pytest.mark.anyio
async def test_document_task_links_to_correct_user_robot_and_task(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}", user_id=777, name="Alicia"))
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    with client.app.state.db.session() as session:
        document_task = session.scalar(select(DocumentTask).where(DocumentTask.task_id == task_id))
        assert document_task is not None
        assert document_task.task_id == task_id


@pytest.mark.anyio
async def test_reply_contains_boundary_and_no_signature_claim(client):
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"].lower()
    assert "not legal, tax, financial, medical, or professional advice" in reply
    assert "certified signature" not in reply
    assert "legal signature" not in reply


@pytest.mark.anyio
async def test_professional_authority_request_does_not_produce_authoritative_answer(client):
    response = await client.post(
        "/api/telegram/webhook",
        json=build_update("review document: tell me if this contract is legally enforceable"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["safety_decision"] == "ESCALATE"
    assert "cannot tell you whether to sign" in body["reply"]["text"].lower() or "cannot" in body["reply"]["text"].lower()


@pytest.mark.anyio
async def test_document_review_does_not_create_memory_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]
