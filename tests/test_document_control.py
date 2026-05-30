from __future__ import annotations

import pytest
from sqlalchemy import desc, select

from app.models import DocumentTask
from tests.test_document_review import LONG_DOCUMENT, build_update


def review_document_command(command_prefix: str, text: str) -> str:
    return f"{command_prefix}: {text}"


async def create_document_record(client, text: str, *, user_id: int = 123456, name: str = "Francisco") -> str:
    response = await client.post("/api/telegram/webhook", json=build_update(text, user_id=user_id, name=name))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        document_task = session.scalar(select(DocumentTask).order_by(desc(DocumentTask.created_at)))
        assert document_task is not None
        return document_task.id


@pytest.mark.anyio
async def test_list_documents_shows_same_user_robot_active_records(client):
    first_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))
    second_id = await create_document_record(
        client,
        review_document_command("summarize document", "Service terms require renewal notice within ten days."),
    )

    response = await client.post("/api/telegram/webhook", json=build_update("what documents did you review"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert first_id in reply
    assert second_id in reply
    assert "REVIEW" in reply
    assert "SUMMARY" in reply
    assert "DRAFTED" in reply


@pytest.mark.anyio
async def test_document_listing_excludes_forgotten_records(client):
    kept_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))
    forgotten_id = await create_document_record(
        client,
        review_document_command("prepare notes from document", "Board notes mention vendor approval and renewal checkpoints."),
    )

    forget_response = await client.post("/api/telegram/webhook", json=build_update(f"forget document {forgotten_id}"))
    assert forget_response.status_code == 200

    response = await client.post("/api/telegram/webhook", json=build_update("what documents did you review"))
    reply = response.json()["reply"]["text"]
    assert kept_id in reply
    assert forgotten_id not in reply


@pytest.mark.anyio
async def test_document_listing_does_not_expose_other_users_records(client):
    own_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))
    other_id = await create_document_record(
        client,
        review_document_command("summarize document", "Counterparty asks for fee changes after signature."),
        user_id=777,
        name="Alicia",
    )

    response = await client.post("/api/telegram/webhook", json=build_update("what documents did you review"))
    reply = response.json()["reply"]["text"]
    assert own_id in reply
    assert other_id not in reply


@pytest.mark.anyio
async def test_forget_document_marks_record_forgotten(client):
    document_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))

    response = await client.post("/api/telegram/webhook", json=build_update(f"forget document {document_id}"))
    assert response.status_code == 200
    assert "no longer retain that document-review record" in response.json()["reply"]["text"].lower()

    with client.app.state.db.session() as session:
        document_task = session.scalar(select(DocumentTask).where(DocumentTask.id == document_id))
        assert document_task is not None
        assert document_task.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_other_user_cannot_forget_document_record(client):
    document_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))

    response = await client.post(
        "/api/telegram/webhook",
        json=build_update(f"forget document {document_id}", user_id=777, name="Alicia"),
    )
    assert response.status_code == 200
    assert "could not find that active document-review record" in response.json()["reply"]["text"].lower()

    with client.app.state.db.session() as session:
        document_task = session.scalar(select(DocumentTask).where(DocumentTask.id == document_id))
        assert document_task is not None
        assert document_task.status == "DRAFTED"


@pytest.mark.anyio
async def test_missing_document_id_returns_safe_not_found_reply(client):
    response = await client.post(
        "/api/telegram/webhook",
        json=build_update("forget document 00000000-0000-0000-0000-000000000000"),
    )
    assert response.status_code == 200
    assert response.json()["scope_decision"] == "CLARIFY"
    assert "could not find that active document-review record" in response.json()["reply"]["text"].lower()


@pytest.mark.anyio
async def test_document_control_turns_create_logging_without_memory_artifacts(client, db_counts):
    document_id = await create_document_record(client, review_document_command("review document", LONG_DOCUMENT))

    before = db_counts()
    list_response = await client.post("/api/telegram/webhook", json=build_update("what documents did you review"))
    assert list_response.status_code == 200
    after_list = db_counts()
    assert after_list["tasks"] == before["tasks"] + 1
    assert after_list["task_runs"] == before["task_runs"] + 1
    assert after_list["safety"] == before["safety"] + 1
    assert after_list["routes"] == before["routes"] + 1
    assert after_list["tokens"] == before["tokens"] + 1
    assert after_list["proposals"] == before["proposals"]
    assert after_list["memories"] == before["memories"]
    assert after_list["documents"] == before["documents"]

    forget_response = await client.post("/api/telegram/webhook", json=build_update(f"forget document {document_id}"))
    assert forget_response.status_code == 200
    after_forget = db_counts()
    assert after_forget["tasks"] == after_list["tasks"] + 1
    assert after_forget["task_runs"] == after_list["task_runs"] + 1
    assert after_forget["safety"] == after_list["safety"] + 1
    assert after_forget["routes"] == after_list["routes"] + 1
    assert after_forget["tokens"] == after_list["tokens"] + 1
    assert after_forget["proposals"] == after_list["proposals"]
    assert after_forget["memories"] == after_list["memories"]
    assert after_forget["documents"] == after_list["documents"]
