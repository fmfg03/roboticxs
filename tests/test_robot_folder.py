from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import (
    DocumentTask,
    FileIntakeAttempt,
    FileRetrievalEnablementRequest,
    MemoryItem,
    ProposedMemory,
    Robot,
    Task,
    TaskRun,
    User,
)
from tests.test_attention_summary import build_text_update, ensure_user_and_robot
from tests.test_file_intake import build_document_update


@pytest.mark.anyio
@pytest.mark.parametrize(
    "command",
    ["mi información importante", "LO QUE ROBBIE SABE", "Robot Folder", "what does robbie know"],
)
async def test_robot_folder_commands_match_exact_case_insensitive(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Mi información importante" in reply or "Todavía no tengo información importante organizada" in reply


@pytest.mark.anyio
async def test_robot_folder_does_not_use_fuzzy_matching(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("robot folder please"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Mi información importante" not in reply
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "GENERAL_TASK"


@pytest.mark.anyio
async def test_robot_folder_groups_local_data_into_expected_sections(client):
    user_id, robot_id = await ensure_user_and_robot(client)
    await client.post("/api/telegram/webhook", json=build_document_update())

    with client.app.state.db.session() as session:
        session.add_all(
            [
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="USER_PROFILE",
                    content="Your timezone is Europe/Berlin.",
                    display_label="Profile",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="TASK_MEMORY",
                    content="Remember my parents need a grocery check every week.",
                    display_label="Memory",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="normal",
                ),
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="WORK_PREFERENCE",
                    content="You prefer short answers.",
                    display_label="Preference",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Ask before sending messages to clients.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
                ProposedMemory(
                    user_id=user_id,
                    robot_id=robot_id,
                    task_id="proposal-task",
                    memory_type="USER_PROFILE",
                    proposed_content="Your language is Spanish.",
                    source_text="remember this",
                    status="PENDING",
                ),
            ]
        )
        file_intake = session.scalar(select(FileIntakeAttempt).where(FileIntakeAttempt.user_id == user_id))
        assert file_intake is not None
        session.add(
            DocumentTask(
                user_id=user_id,
                robot_id=robot_id,
                task_id="doc-task",
                review_type="SUMMARY",
                source_kind="TEXT_SIMULATED",
                source_text_preview="Service contract",
                source_text_hash="hash-robot-folder",
                status="DRAFTED",
            )
        )
        blocked_task = Task(
            user_id=user_id,
            robot_id=robot_id,
            kind="GENERAL_TASK",
            input_text="old blocked task",
            scope_decision="ANSWER",
            task_class="SIMPLE_CLASSIFICATION",
        )
        session.add(blocked_task)
        session.flush()
        session.add(TaskRun(task_id=blocked_task.id, status="blocked"))
        session.add(
            FileRetrievalEnablementRequest(
                user_id=user_id,
                robot_id=robot_id,
                task_id="enablement-task",
                status="REQUESTED_DISABLED",
                reason_code="FILE_RETRIEVAL_DISABLED_BY_POLICY",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("mi información importante"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Mi información importante" in reply
    assert "Sobre mí" in reply
    assert "Nombre: Francisco" in reply
    assert "- Your timezone is Europe/Berlin." in reply
    assert "Familia y personas importantes" in reply
    assert "Hay 1 recuerdos activos relacionados con familia." in reply
    assert "Documentos importantes" in reply
    assert "Hay 1 archivos registrados." in reply
    assert "Hay 1 documentos revisados recientemente." in reply
    assert "Preferencias de trabajo" in reply
    assert "- You prefer short answers." in reply
    assert "Tareas y pendientes recurrentes" in reply
    assert "Hay 1 tasks con estado pendiente, bloqueado o fallido." in reply
    assert "Límites del robot" in reply
    assert "- Ask before sending messages to clients." in reply
    assert "Retrieval sigue deshabilitado por política local." in reply
    assert "Pendiente de aprobación" in reply
    assert "Hay 1 memorias pendientes de aprobación." in reply
    assert "No revisé correo, WhatsApp, calendario, web ni archivos nuevos." in reply


@pytest.mark.anyio
async def test_robot_folder_is_scoped_by_user_and_robot(client):
    own_user_id, own_robot_id = await ensure_user_and_robot(client, user_id=123456, name="Francisco")
    other_user_id, other_robot_id = await ensure_user_and_robot(client, user_id=777, name="Alicia")

    with client.app.state.db.session() as session:
        session.add(
            MemoryItem(
                user_id=other_user_id,
                robot_id=other_robot_id,
                memory_type="USER_PROFILE",
                content="Your timezone is UTC.",
                display_label="Profile",
                source="telegram_text",
                status="ACTIVE",
                importance="high",
            )
        )
        session.add(
            ProposedMemory(
                user_id=other_user_id,
                robot_id=other_robot_id,
                task_id="other-proposal",
                memory_type="USER_PROFILE",
                proposed_content="Other pending memory",
                source_text="remember this",
                status="PENDING",
            )
        )
        session.add(
            MemoryItem(
                user_id=own_user_id,
                robot_id=own_robot_id,
                memory_type="WORK_PREFERENCE",
                content="You prefer short answers.",
                display_label="Preference",
                source="telegram_text",
                status="ACTIVE",
                importance="high",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("lo que robbie sabe"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "You prefer short answers." in reply
    assert "Your timezone is UTC." not in reply
    assert "Other pending memory" not in reply


@pytest.mark.anyio
async def test_robot_folder_empty_state_is_safe(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("robot folder"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Todavía no tengo información importante organizada para este robot." in reply
    assert "Solo usé estado local ya persistido." in reply


@pytest.mark.anyio
async def test_robot_folder_no_side_effects_and_runtime_records_only(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_text_update("mi información importante"))
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
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]


@pytest.mark.anyio
async def test_robot_folder_ignores_its_own_runtime_records_in_followup_runs(client):
    await ensure_user_and_robot(client)
    first = await client.post("/api/telegram/webhook", json=build_text_update("mi información importante"))
    assert first.status_code == 200
    second = await client.post("/api/telegram/webhook", json=build_text_update("mi información importante"))
    assert second.status_code == 200
    reply = second.json()["reply"]["text"]
    assert "tasks con estado pendiente, bloqueado o fallido" not in reply
