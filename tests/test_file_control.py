from __future__ import annotations

import pytest
from sqlalchemy import desc, select

from app.file_retrieval_adapter import (
    FileRetrievalAdapterResult,
    MockOnlyFileRetrievalAdapter,
    build_file_retrieval_adapter_request,
    is_live_file_retrieval_enabled,
)
from app.config import Settings
from app.models import FileIntakeAttempt, FileRetrievalAttempt, FileRetrievalEnablementRequest, Task
from tests.test_file_intake import build_document_update


async def create_file_intake(client, *, user_id: int = 123456, name: str = "Francisco") -> str:
    response = await client.post("/api/telegram/webhook", json=build_document_update(user_id=user_id, name=name))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileIntakeAttempt).order_by(desc(FileIntakeAttempt.created_at)))
        assert attempt is not None
        return attempt.id


@pytest.mark.anyio
async def test_list_files_shows_same_user_robot_active_records(client):
    first_id = await create_file_intake(client)
    second_id = await create_file_intake(client)

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8001,
        "message": {
            "message_id": 50,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what files did you receive",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert first_id in reply
    assert second_id in reply
    assert "nda.pdf" in reply
    assert "application/pdf" in reply
    assert "I have not downloaded, parsed, OCRed, reviewed, or stored the file contents." in reply


@pytest.mark.anyio
async def test_list_files_excludes_forgotten_records(client):
    kept_id = await create_file_intake(client)
    forgotten_id = await create_file_intake(client)

    forget_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8002,
        "message": {
            "message_id": 51,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"forget file {forgotten_id}",
        },
    })
    assert forget_response.status_code == 200

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8003,
        "message": {
            "message_id": 52,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what files did you receive",
        },
    })
    reply = response.json()["reply"]["text"]
    assert kept_id in reply
    assert forgotten_id not in reply


@pytest.mark.anyio
async def test_list_files_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8004,
        "message": {
            "message_id": 53,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what files did you receive",
        },
    })
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "I do not have any active retained file metadata records for this robot."


@pytest.mark.anyio
async def test_forget_file_marks_record_forgotten(client):
    file_id = await create_file_intake(client)

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8005,
        "message": {
            "message_id": 54,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"forget file {file_id}",
        },
    })
    assert response.status_code == 200
    assert "no longer retain that file metadata record as active" in response.json()["reply"]["text"].lower()

    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileIntakeAttempt).where(FileIntakeAttempt.id == file_id))
        assert attempt is not None
        assert attempt.status == "FORGOTTEN"


@pytest.mark.anyio
async def test_list_files_is_scoped_by_user_robot(client):
    own_id = await create_file_intake(client)
    other_id = await create_file_intake(client, user_id=777, name="Alicia")

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8006,
        "message": {
            "message_id": 55,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what files did you receive",
        },
    })
    reply = response.json()["reply"]["text"]
    assert own_id in reply
    assert other_id not in reply


@pytest.mark.anyio
async def test_cross_user_cannot_forget_foreign_file(client):
    file_id = await create_file_intake(client)

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8007,
        "message": {
            "message_id": 56,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": f"forget file {file_id}",
        },
    })
    assert response.status_code == 200
    assert "could not find an active file metadata record" in response.json()["reply"]["text"].lower()

    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileIntakeAttempt).where(FileIntakeAttempt.id == file_id))
        assert attempt is not None
        assert attempt.status == "METADATA_RECEIVED"


@pytest.mark.anyio
async def test_retrieve_file_preflight_persists_request_metadata_only(client, db_counts):
    file_id = await create_file_intake(client)
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8010,
        "message": {
            "message_id": 59,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"].lower()
    assert "i recorded your request to retrieve nda.pdf" in reply
    assert "did not call telegram getfile" in reply
    assert "did not download the file" in reply
    assert "did not review it" in reply
    after = db_counts()
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"] + 1
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert attempt is not None
        assert attempt.file_intake_id == file_id
        assert attempt.request_kind == "RETRIEVE"
        assert attempt.status == "DISABLED_BY_POLICY"


@pytest.mark.anyio
async def test_prepare_file_for_review_preflight_persists_request_metadata_only(client):
    file_id = await create_file_intake(client)
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011,
        "message": {
            "message_id": 60,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"prepare file {file_id} for review",
        },
    })
    assert response.status_code == 200
    assert "prepare for review nda.pdf" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert attempt is not None
        assert attempt.request_kind == "PREPARE_FOR_REVIEW"
        assert attempt.status == "DISABLED_BY_POLICY"


@pytest.mark.anyio
async def test_retrieve_file_preflight_uses_adapter_result_status(client, monkeypatch):
    file_id = await create_file_intake(client)

    class StubAdapter:
        def plan_retrieval(self, *, request):
            return FileRetrievalAdapterResult(
                adapter_kind="test_stub",
                live_retrieval_enabled=False,
                status="READY_FOR_RETRIEVAL_WHEN_ENABLED",
                reason_code="TEST_STUB",
            )

    monkeypatch.setattr("app.flows.file_control_flow.get_file_retrieval_adapter", lambda settings: StubAdapter())
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_5,
        "message": {
            "message_id": 60_5,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        attempt = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert attempt is not None
        assert attempt.status == "READY_FOR_RETRIEVAL_WHEN_ENABLED"


def test_default_retrieval_policy_is_disabled():
    settings = Settings()
    assert settings.file_retrieval_enabled is False
    assert is_live_file_retrieval_enabled(settings=settings) is False


@pytest.mark.anyio
async def test_show_file_retrieval_status_reports_disabled_policy(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_6,
        "message": {
            "message_id": 60_6,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show file retrieval status",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "File retrieval status: disabled_by_policy." in reply
    assert "Reason: FILE_RETRIEVAL_DISABLED_BY_POLICY." in reply
    assert "Live retrieval is not active." in reply
    assert "will not call Telegram getFile" in reply
    assert "download files" in reply
    assert "parse PDFs" in reply
    assert "OCR content" in reply
    assert "store raw bytes" in reply
    assert "store extracted text" in reply
    assert "claim the file was reviewed" in reply


@pytest.mark.anyio
async def test_show_retrieval_policy_reports_disabled_policy(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_7,
        "message": {
            "message_id": 60_7,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval policy",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "File retrieval status: disabled_by_policy." in reply
    assert "Reason: FILE_RETRIEVAL_DISABLED_BY_POLICY." in reply


@pytest.mark.anyio
async def test_request_file_retrieval_enablement_records_metadata_only_request(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_8,
        "message": {
            "message_id": 60_8,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "I recorded your request for file retrieval enablement." in reply
    assert "Retrieval remains disabled." in reply
    assert "Reason: FILE_RETRIEVAL_DISABLED_BY_POLICY." in reply
    assert "will not call Telegram getFile" in reply
    after = db_counts()
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"] + 1
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        assert request.status == "REQUESTED_DISABLED"
        assert request.reason_code == "FILE_RETRIEVAL_DISABLED_BY_POLICY"


@pytest.mark.anyio
async def test_request_retrieval_enablement_alias_records_same_request(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9,
        "message": {
            "message_id": 60_9,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request retrieval enablement",
        },
    })
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        assert request.status == "REQUESTED_DISABLED"


@pytest.mark.anyio
async def test_list_pending_retrieval_enablement_requests_shows_same_user_robot_requests_only(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_1,
        "message": {
            "message_id": 60_9_1,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_2,
        "message": {
            "message_id": 60_9_2,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": "request file retrieval enablement",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_3,
        "message": {
            "message_id": 60_9_3,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what retrieval enablement requests are pending",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Here are the pending retrieval enablement requests for this robot:" in reply
    assert "REQUESTED_DISABLED" in reply
    assert "FILE_RETRIEVAL_DISABLED_BY_POLICY" in reply
    assert "Retrieval remains disabled." in reply


@pytest.mark.anyio
async def test_list_pending_retrieval_enablement_requests_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_4,
        "message": {
            "message_id": 60_9_4,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what retrieval enablement requests are pending",
        },
    })
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "I do not have any pending retrieval enablement requests for this robot."


@pytest.mark.anyio
async def test_approve_retrieval_enablement_request_marks_request_without_enabling_retrieval(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_5,
        "message": {
            "message_id": 60_9_5,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        request_id = request.id
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_6,
        "message": {
            "message_id": 60_9_6,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"approve retrieval enablement request {request_id}",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Retrieval enablement request approved." in reply
    assert "Retrieval remains disabled." in reply
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).where(FileRetrievalEnablementRequest.id == request_id))
        assert request is not None
        assert request.status == "APPROVED_PENDING_POLICY_CHANGE"
    settings = Settings()
    assert settings.file_retrieval_enabled is False


@pytest.mark.anyio
async def test_approve_retrieval_enablement_request_routes_to_specific_control_path_not_fallback(client, db_counts):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_6_1,
        "message": {
            "message_id": 60_9_6_1,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        request_id = request.id
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_6_2,
        "message": {
            "message_id": 60_9_6_2,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"approve retrieval enablement request {request_id}",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Retrieval enablement request approved." in reply
    assert "Retrieval remains disabled." in reply
    assert "I can help with meeting prep" not in reply
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        request = session.scalar(select(FileRetrievalEnablementRequest).where(FileRetrievalEnablementRequest.id == request_id))
        assert latest_task is not None
        assert latest_task.input_text == f"approve retrieval enablement request {request_id}"
        assert request is not None
        assert request.status == "APPROVED_PENDING_POLICY_CHANGE"


@pytest.mark.anyio
async def test_reject_retrieval_enablement_request_marks_request_without_enabling_retrieval(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_7,
        "message": {
            "message_id": 60_9_7,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        request_id = request.id
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_8,
        "message": {
            "message_id": 60_9_8,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"reject retrieval enablement request {request_id}",
        },
    })
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).where(FileRetrievalEnablementRequest.id == request_id))
        assert request is not None
        assert request.status == "REJECTED"


@pytest.mark.anyio
async def test_resolve_retrieval_enablement_request_rejects_missing_or_foreign_ids_safely(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_9,
        "message": {
            "message_id": 60_9_9,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        request_id = request.id
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_10,
        "message": {
            "message_id": 60_9_10,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": f"approve retrieval enablement request {request_id}",
        },
    })
    assert response.status_code == 200
    assert "could not find a pending retrieval enablement request" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).where(FileRetrievalEnablementRequest.id == request_id))
        assert request is not None
        assert request.status == "REQUESTED_DISABLED"


@pytest.mark.anyio
async def test_show_retrieval_enablement_request_history_lists_pending_and_resolved_same_user_robot_only(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_11,
        "message": {
            "message_id": 60_9_11,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_12,
        "message": {
            "message_id": 60_9_12,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        requests = session.scalars(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at))).all()
        assert len(requests) >= 2
        pending_id = requests[0].id
        approve_id = requests[1].id
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_13,
        "message": {
            "message_id": 60_9_13,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"approve retrieval enablement request {approve_id}",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_14,
        "message": {
            "message_id": 60_9_14,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": "request file retrieval enablement",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_15,
        "message": {
            "message_id": 60_9_15,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval enablement request history",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Here is the retrieval enablement request history for this robot:" in reply
    assert pending_id in reply
    assert approve_id in reply
    assert "REQUESTED_DISABLED" in reply
    assert "APPROVED_PENDING_POLICY_CHANGE" in reply
    assert "FILE_RETRIEVAL_DISABLED_BY_POLICY" in reply
    assert "Retrieval remains disabled." in reply


@pytest.mark.anyio
async def test_retrieval_enablement_request_history_alias_works(client):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_16,
        "message": {
            "message_id": 60_9_16,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_17,
        "message": {
            "message_id": 60_9_17,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what retrieval enablement requests do you have",
        },
    })
    assert response.status_code == 200
    assert "retrieval enablement request history" in response.json()["reply"]["text"].lower()


@pytest.mark.anyio
async def test_retrieval_enablement_request_history_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_18,
        "message": {
            "message_id": 60_9_18,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval enablement request history",
        },
    })
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "I do not have any retrieval enablement request history for this robot."


@pytest.mark.anyio
async def test_show_retrieval_control_summary_reports_policy_counts_and_recent_outcomes(client):
    file_id = await create_file_intake(client)
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_19,
        "message": {
            "message_id": 60_9_19,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_20,
        "message": {
            "message_id": 60_9_20,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_21,
        "message": {
            "message_id": 60_9_21,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    with client.app.state.db.session() as session:
        requests = session.scalars(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at))).all()
        assert len(requests) >= 2
        approve_id = requests[1].id
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_22,
        "message": {
            "message_id": 60_9_22,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"approve retrieval enablement request {approve_id}",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_23,
        "message": {
            "message_id": 60_9_23,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval control summary",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Retrieval control summary:" in reply
    assert "- Retrieval policy: DISABLED_BY_POLICY" in reply
    assert "- Reason: FILE_RETRIEVAL_DISABLED_BY_POLICY" in reply
    assert "- Pending file retrieval intents: 1" in reply
    assert "- Pending retrieval enablement requests: 1" in reply
    assert "APPROVED_PENDING_POLICY_CHANGE" in reply
    assert "REQUESTED_DISABLED" in reply
    assert "Retrieval remains disabled." in reply


@pytest.mark.anyio
async def test_show_file_retrieval_controls_alias_works(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_24,
        "message": {
            "message_id": 60_9_24,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show file retrieval controls",
        },
    })
    assert response.status_code == 200
    assert "retrieval control summary" in response.json()["reply"]["text"].lower()


@pytest.mark.anyio
async def test_show_retrieval_control_report_reports_policy_counts_and_recent_outcomes(client):
    file_id = await create_file_intake(client)
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_25,
        "message": {
            "message_id": 60_9_25,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_26,
        "message": {
            "message_id": 60_9_26,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_27,
        "message": {
            "message_id": 60_9_27,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval control report",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Retrieval control report:" in reply
    assert "- Retrieval policy: DISABLED_BY_POLICY" in reply
    assert "- Reason: FILE_RETRIEVAL_DISABLED_BY_POLICY" in reply
    assert "- Pending file retrieval intents: 1" in reply
    assert "- Pending retrieval enablement requests: 1" in reply
    assert "REQUESTED_DISABLED" in reply
    assert "Retrieval remains disabled." in reply


@pytest.mark.anyio
async def test_show_file_retrieval_audit_report_alias_works(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8011_9_28,
        "message": {
            "message_id": 60_9_28,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show file retrieval audit report",
        },
    })
    assert response.status_code == 200
    assert "retrieval control report" in response.json()["reply"]["text"].lower()


@pytest.mark.anyio
async def test_retrieve_file_preflight_rejects_missing_or_foreign_ids_safely(client):
    file_id = await create_file_intake(client, user_id=777, name="Alicia")
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8012,
        "message": {
            "message_id": 61,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    assert response.status_code == 200
    assert "could not find an active file metadata record" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        assert session.query(FileRetrievalAttempt).count() == 0


@pytest.mark.anyio
async def test_list_pending_file_retrievals_shows_same_user_robot_pending_records_only(client):
    kept_file_id = await create_file_intake(client)
    other_file_id = await create_file_intake(client, user_id=777, name="Alicia")
    await client.post("/api/telegram/webhook", json={
        "update_id": 8014,
        "message": {
            "message_id": 63,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {kept_file_id}",
        },
    })
    await client.post("/api/telegram/webhook", json={
        "update_id": 8015,
        "message": {
            "message_id": 64,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": f"retrieve file {other_file_id}",
        },
    })
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8016,
        "message": {
            "message_id": 65,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what file retrievals are pending",
        },
    })
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Here are the pending file retrieval requests for this robot:" in reply
    assert "DISABLED_BY_POLICY" in reply
    assert "nda.pdf" in reply
    assert "I have not called Telegram getFile" in reply


@pytest.mark.anyio
async def test_list_pending_file_retrievals_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8017,
        "message": {
            "message_id": 66,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what file retrievals are pending",
        },
    })
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "I do not have any pending file retrieval requests for this robot."


@pytest.mark.anyio
async def test_cancel_file_retrieval_marks_pending_request_cancelled(client):
    file_id = await create_file_intake(client)
    preflight = await client.post("/api/telegram/webhook", json={
        "update_id": 8018,
        "message": {
            "message_id": 67,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    assert preflight.status_code == 200
    with client.app.state.db.session() as session:
        retrieval = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert retrieval is not None
        retrieval_id = retrieval.id

    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8019,
        "message": {
            "message_id": 68,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"cancel file retrieval {retrieval_id}",
        },
    })
    assert response.status_code == 200
    assert "no longer keep that file retrieval request pending" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        retrieval = session.scalar(select(FileRetrievalAttempt).where(FileRetrievalAttempt.id == retrieval_id))
        assert retrieval is not None
        assert retrieval.status == "CANCELLED"


@pytest.mark.anyio
async def test_cancel_file_retrieval_rejects_missing_or_foreign_ids_safely(client):
    file_id = await create_file_intake(client)
    await client.post("/api/telegram/webhook", json={
        "update_id": 8020,
        "message": {
            "message_id": 69,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    with client.app.state.db.session() as session:
        retrieval = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert retrieval is not None
        retrieval_id = retrieval.id
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021,
        "message": {
            "message_id": 70,
            "date": 1710000000,
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False, "first_name": "Alicia", "username": "alicia"},
            "text": f"cancel file retrieval {retrieval_id}",
        },
    })
    assert response.status_code == 200
    assert "could not find a pending file retrieval request" in response.json()["reply"]["text"].lower()
    with client.app.state.db.session() as session:
        retrieval = session.scalar(select(FileRetrievalAttempt).where(FileRetrievalAttempt.id == retrieval_id))
        assert retrieval is not None
        assert retrieval.status == "DISABLED_BY_POLICY"


@pytest.mark.anyio
async def test_file_retrieval_enablement_request_turn_creates_runtime_records_without_new_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5,
        "message": {
            "message_id": 70_5,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"] + 1
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


@pytest.mark.anyio
async def test_file_retrieval_enablement_request_control_turns_create_runtime_records_without_new_artifacts(client, db_counts):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_1,
        "message": {
            "message_id": 70_5_1,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    before = db_counts()
    list_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_2,
        "message": {
            "message_id": 70_5_2,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what retrieval enablement requests are pending",
        },
    })
    assert list_response.status_code == 200
    after_list = db_counts()
    assert after_list["tasks"] == before["tasks"] + 1
    assert after_list["task_runs"] == before["task_runs"] + 1
    assert after_list["safety"] == before["safety"] + 1
    assert after_list["routes"] == before["routes"] + 1
    assert after_list["tokens"] == before["tokens"] + 1
    assert after_list["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]
    assert after_list["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    with client.app.state.db.session() as session:
        request = session.scalar(select(FileRetrievalEnablementRequest).order_by(desc(FileRetrievalEnablementRequest.created_at)))
        assert request is not None
        request_id = request.id
    resolve_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_3,
        "message": {
            "message_id": 70_5_3,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"approve retrieval enablement request {request_id}",
        },
    })
    assert resolve_response.status_code == 200
    after_resolve = db_counts()
    assert after_resolve["tasks"] == after_list["tasks"] + 1
    assert after_resolve["task_runs"] == after_list["task_runs"] + 1
    assert after_resolve["safety"] == after_list["safety"] + 1
    assert after_resolve["routes"] == after_list["routes"] + 1
    assert after_resolve["tokens"] == after_list["tokens"] + 1
    assert after_resolve["file_retrieval_enablement_requests"] == after_list["file_retrieval_enablement_requests"]
    assert after_resolve["file_retrieval_attempts"] == after_list["file_retrieval_attempts"]
    assert after_resolve["file_intakes"] == after_list["file_intakes"]
    assert after_resolve["documents"] == after_list["documents"]
    assert after_resolve["memories"] == after_list["memories"]
    assert after_resolve["proposals"] == after_list["proposals"]


@pytest.mark.anyio
async def test_retrieval_enablement_request_history_turn_creates_runtime_records_without_new_artifacts(client, db_counts):
    await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_4,
        "message": {
            "message_id": 70_5_4,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "request file retrieval enablement",
        },
    })
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_5,
        "message": {
            "message_id": 70_5_5,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval enablement request history",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


@pytest.mark.anyio
async def test_retrieval_control_summary_turn_creates_runtime_records_without_new_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_6,
        "message": {
            "message_id": 70_5_6,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval control summary",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


@pytest.mark.anyio
async def test_retrieval_control_report_turn_creates_runtime_records_without_new_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8021_5_7,
        "message": {
            "message_id": 70_5_7,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show retrieval control report",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


@pytest.mark.anyio
async def test_file_control_turns_create_runtime_records_without_new_artifacts(client, db_counts):
    file_id = await create_file_intake(client)

    before = db_counts()
    list_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8008,
        "message": {
            "message_id": 57,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what files did you receive",
        },
    })
    assert list_response.status_code == 200
    after_list = db_counts()
    assert after_list["tasks"] == before["tasks"] + 1
    assert after_list["task_runs"] == before["task_runs"] + 1
    assert after_list["safety"] == before["safety"] + 1
    assert after_list["routes"] == before["routes"] + 1
    assert after_list["tokens"] == before["tokens"] + 1
    assert after_list["documents"] == before["documents"]
    assert after_list["memories"] == before["memories"]
    assert after_list["proposals"] == before["proposals"]
    assert after_list["file_intakes"] == before["file_intakes"]

    forget_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8009,
        "message": {
            "message_id": 58,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"forget file {file_id}",
        },
    })
    assert forget_response.status_code == 200
    after_forget = db_counts()
    assert after_forget["tasks"] == after_list["tasks"] + 1
    assert after_forget["task_runs"] == after_list["task_runs"] + 1
    assert after_forget["safety"] == after_list["safety"] + 1
    assert after_forget["routes"] == after_list["routes"] + 1
    assert after_forget["tokens"] == after_list["tokens"] + 1
    assert after_forget["documents"] == after_list["documents"]
    assert after_forget["memories"] == after_list["memories"]
    assert after_forget["proposals"] == after_list["proposals"]
    assert after_forget["file_intakes"] == after_list["file_intakes"]


@pytest.mark.anyio
async def test_file_retrieval_preflight_turn_creates_runtime_records_without_new_content_artifacts(client, db_counts):
    file_id = await create_file_intake(client)
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8013,
        "message": {
            "message_id": 62,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"] + 1
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_file_retrieval_control_turns_create_runtime_records_without_new_content_artifacts(client, db_counts):
    file_id = await create_file_intake(client)
    await client.post("/api/telegram/webhook", json={
        "update_id": 8022,
        "message": {
            "message_id": 71,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"retrieve file {file_id}",
        },
    })
    with client.app.state.db.session() as session:
        retrieval = session.scalar(select(FileRetrievalAttempt).order_by(desc(FileRetrievalAttempt.created_at)))
        assert retrieval is not None
        retrieval_id = retrieval.id

    before = db_counts()
    list_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8023,
        "message": {
            "message_id": 72,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "what file retrievals are pending",
        },
    })
    assert list_response.status_code == 200
    after_list = db_counts()
    assert after_list["tasks"] == before["tasks"] + 1
    assert after_list["task_runs"] == before["task_runs"] + 1
    assert after_list["safety"] == before["safety"] + 1
    assert after_list["routes"] == before["routes"] + 1
    assert after_list["tokens"] == before["tokens"] + 1
    assert after_list["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after_list["documents"] == before["documents"]
    assert after_list["memories"] == before["memories"]
    assert after_list["proposals"] == before["proposals"]
    assert after_list["file_intakes"] == before["file_intakes"]

    cancel_response = await client.post("/api/telegram/webhook", json={
        "update_id": 8024,
        "message": {
            "message_id": 73,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": f"cancel file retrieval {retrieval_id}",
        },
    })
    assert cancel_response.status_code == 200
    after_cancel = db_counts()
    assert after_cancel["tasks"] == after_list["tasks"] + 1
    assert after_cancel["task_runs"] == after_list["task_runs"] + 1
    assert after_cancel["safety"] == after_list["safety"] + 1
    assert after_cancel["routes"] == after_list["routes"] + 1
    assert after_cancel["tokens"] == after_list["tokens"] + 1
    assert after_cancel["file_retrieval_attempts"] == after_list["file_retrieval_attempts"]
    assert after_cancel["documents"] == after_list["documents"]
    assert after_cancel["memories"] == after_list["memories"]
    assert after_cancel["proposals"] == after_list["proposals"]
    assert after_cancel["file_intakes"] == after_list["file_intakes"]


@pytest.mark.anyio
async def test_file_retrieval_policy_status_turn_creates_runtime_records_without_new_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json={
        "update_id": 8024_5,
        "message": {
            "message_id": 73_5,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False, "first_name": "Francisco", "username": "francisco"},
            "text": "show file retrieval status",
        },
    })
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["file_intakes"] == before["file_intakes"]
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]


def test_file_intake_model_still_has_no_raw_content_fields():
    columns = {column.name for column in FileIntakeAttempt.__table__.columns}
    assert "raw_bytes" not in columns
    assert "file_bytes" not in columns
    assert "downloaded_file_path" not in columns
    assert "full_text" not in columns
    assert "extracted_text" not in columns
    assert "ocr_text" not in columns


def test_file_retrieval_attempt_model_has_no_raw_content_fields():
    columns = {column.name for column in FileRetrievalAttempt.__table__.columns}
    assert "raw_bytes" not in columns
    assert "file_bytes" not in columns
    assert "downloaded_file_path" not in columns
    assert "full_text" not in columns
    assert "extracted_text" not in columns
    assert "ocr_text" not in columns


def test_mock_retrieval_adapter_contract_is_hard_disabled():
    file_intake = FileIntakeAttempt(
        user_id="u1",
        robot_id="r1",
        task_id="t1",
        telegram_file_id="telegram-file-1",
        telegram_file_unique_id="telegram-unique-1",
        file_name="nda.pdf",
        mime_type="application/pdf",
        file_size=48291,
    )
    adapter_request = build_file_retrieval_adapter_request(
        file_intake=file_intake,
        request_kind="RETRIEVE",
        user_id="u1",
        robot_id="r1",
    )
    settings = Settings()
    result = MockOnlyFileRetrievalAdapter(retrieval_enabled=settings.file_retrieval_enabled).plan_retrieval(request=adapter_request)
    assert adapter_request.file_name == "nda.pdf"
    assert adapter_request.mime_type == "application/pdf"
    assert adapter_request.file_size == 48291
    assert result.adapter_kind == "mock_disabled"
    assert result.live_retrieval_enabled is False
    assert result.status == "DISABLED_BY_POLICY"
    assert result.reason_code == "FILE_RETRIEVAL_DISABLED_BY_POLICY"
    assert is_live_file_retrieval_enabled(settings=settings) is False
