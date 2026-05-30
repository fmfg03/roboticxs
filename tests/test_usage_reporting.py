from __future__ import annotations

import pytest

from app.models import FileIntakeAttempt
from tests.test_document_review import LONG_DOCUMENT, build_update


async def seed_usage_activity(client, *, user_id: int = 123456, name: str = "Francisco"):
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow", user_id=user_id, name=name))
    assert response.status_code == 200
    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}", user_id=user_id, name=name))
    assert response.status_code == 200


@pytest.mark.anyio
async def test_what_did_you_spend_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json=build_update("what did you spend"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == (
        "I do not have prior usage records for this robot yet. This report uses local estimated logs only, not live billing."
    )


@pytest.mark.anyio
async def test_show_token_usage_empty_state_is_safe(client):
    response = await client.post("/api/telegram/webhook", json=build_update("show token usage"))
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == (
        "I do not have prior token usage records for this robot yet. This report uses local estimated logs only."
    )


@pytest.mark.anyio
async def test_usage_reporting_aggregates_local_cost_and_token_records(client):
    await seed_usage_activity(client)

    response = await client.post("/api/telegram/webhook", json=build_update("what did you spend"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Local estimated spend summary:" in reply
    assert "- Total usage events: 2" in reply
    assert "Provider/model breakdown:" in reply
    assert "Highest-cost local routes:" in reply
    assert "This is a local estimate from robot logs only, not live billing or provider reconciliation." in reply


@pytest.mark.anyio
async def test_show_token_usage_includes_family_and_task_breakdowns(client):
    await seed_usage_activity(client)

    response = await client.post("/api/telegram/webhook", json=build_update("show token usage"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Local token usage summary:" in reply
    assert "- Total usage events: 2" in reply
    assert "Flow family breakdown:" in reply
    assert "- DOCUMENT_REVIEW: 1 events" in reply
    assert "- GENERAL_TASK: 1 events" in reply
    assert "Task class breakdown:" in reply
    assert "This is local usage data only, derived from estimated robot logs." in reply


@pytest.mark.anyio
async def test_usage_reporting_is_scoped_by_user_and_robot(client):
    await seed_usage_activity(client, user_id=123456, name="Francisco")
    await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow", user_id=777, name="Alicia"))

    response = await client.post("/api/telegram/webhook", json=build_update("show token usage", user_id=777, name="Alicia"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "- Total usage events: 1" in reply
    assert "- GENERAL_TASK: 1 events" in reply
    assert "- DOCUMENT_REVIEW: 1 events" not in reply


@pytest.mark.anyio
async def test_usage_reporting_turns_create_runtime_records_without_new_artifacts(client, db_counts):
    await seed_usage_activity(client)

    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("what did you spend"))
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
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_usage_reporting_does_not_create_file_intake_records(client):
    await seed_usage_activity(client)

    response = await client.post("/api/telegram/webhook", json=build_update("show token usage"))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        assert session.query(FileIntakeAttempt).count() == 0


def test_file_intake_model_still_has_no_raw_content_fields():
    columns = {column.name for column in FileIntakeAttempt.__table__.columns}
    assert "raw_bytes" not in columns
    assert "file_bytes" not in columns
    assert "downloaded_file_path" not in columns
    assert "full_text" not in columns
    assert "extracted_text" not in columns
    assert "ocr_text" not in columns
