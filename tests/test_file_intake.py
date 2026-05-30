from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import DocumentTask, FileIntakeAttempt


def build_document_update(*, user_id: int = 123456, name: str = "Francisco") -> dict:
    return {
        "update_id": 7001,
        "message": {
            "message_id": 42,
            "date": 1710000000,
            "chat": {"id": user_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": name,
                "username": name.lower(),
            },
            "document": {
                "file_id": "telegram_file_abc",
                "file_unique_id": "unique_abc",
                "file_name": "nda.pdf",
                "mime_type": "application/pdf",
                "file_size": 48291,
            },
        },
    }


@pytest.mark.anyio
async def test_document_metadata_payload_is_accepted(client):
    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    reply = response.json()["reply"]["text"].lower()
    assert "received the file metadata" in reply
    assert "nda.pdf" in reply


@pytest.mark.anyio
async def test_file_intake_attempt_persists_metadata_only(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    after = db_counts()
    assert after["file_intakes"] == before["file_intakes"] + 1
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]

    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileIntakeAttempt).order_by(FileIntakeAttempt.created_at.desc()))
        assert attempt is not None
        assert attempt.telegram_file_id == "telegram_file_abc"
        assert attempt.telegram_file_unique_id == "unique_abc"
        assert attempt.file_name == "nda.pdf"
        assert attempt.mime_type == "application/pdf"
        assert attempt.file_size == 48291
        assert attempt.status == "METADATA_RECEIVED"


@pytest.mark.anyio
async def test_file_intake_links_to_correct_user_robot_and_task(client):
    response = await client.post("/api/telegram/webhook", json=build_document_update(user_id=777, name="Alicia"))
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileIntakeAttempt).where(FileIntakeAttempt.task_id == task_id))
        assert attempt is not None
        assert attempt.task_id == task_id
        assert attempt.user_id is not None
        assert attempt.robot_id is not None


@pytest.mark.anyio
async def test_file_intake_creates_runtime_records_without_document_or_memory_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


@pytest.mark.anyio
async def test_file_intake_reply_makes_boundaries_explicit(client):
    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    reply = response.json()["reply"]["text"].lower()
    assert "did not download" in reply
    assert "did not download, parse, ocr, review, or store the file contents" in reply
    assert "review document: <text>" in reply


def test_file_intake_model_has_no_raw_content_fields():
    columns = {column.name for column in FileIntakeAttempt.__table__.columns}
    assert "raw_bytes" not in columns
    assert "file_bytes" not in columns
    assert "downloaded_file_path" not in columns
    assert "full_text" not in columns
    assert "extracted_text" not in columns
    assert "ocr_text" not in columns


@pytest.mark.anyio
async def test_invalid_payload_without_text_or_document_still_returns_422(client):
    response = await client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 7002,
            "message": {
                "message_id": 43,
                "date": 1710000000,
                "chat": {"id": 123456, "type": "private"},
                "from": {"id": 123456, "first_name": "Francisco"},
            },
        },
    )
    assert response.status_code == 422
