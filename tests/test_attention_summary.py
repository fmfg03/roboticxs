from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import (
    BudgetPolicy,
    DocumentTask,
    FileIntakeAttempt,
    FileRetrievalEnablementRequest,
    FileRetrievalAttempt,
    MemoryItem,
    ProposedMemory,
    Robot,
    Task,
    TaskRun,
    TokenUsageEvent,
    User,
)
from tests.test_file_intake import build_document_update


def build_text_update(text: str, *, user_id: int = 123456, name: str = "Francisco") -> dict:
    return {
        "update_id": 990000,
        "message": {
            "message_id": 700,
            "date": 1710000000,
            "chat": {"id": user_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": name, "username": name.lower()},
            "text": text,
        },
    }


async def ensure_user_and_robot(client, *, user_id: int = 123456, name: str = "Francisco") -> tuple[str, str]:
    response = await client.post("/api/telegram/webhook", json=build_text_update("hello", user_id=user_id, name=name))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        user = session.scalar(select(User).where(User.telegram_user_id == user_id))
        assert user is not None
        robot = session.scalar(select(Robot).where(Robot.user_id == user.id, Robot.active.is_(True)))
        assert robot is not None
        return user.id, robot.id


@pytest.mark.anyio
@pytest.mark.parametrize("command", ["qué se me pasó", "WHAT DID I MISS", "Qué necesita mi atención"])
async def test_attention_summary_commands_match_exact_case_insensitive(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Robbie ya conoce" in reply or "Robbie conoce hoy" in reply


@pytest.mark.anyio
async def test_attention_summary_returns_ranked_local_findings(client):
    user_id, robot_id = await ensure_user_and_robot(client)

    await client.post("/api/telegram/webhook", json=build_document_update())

    with client.app.state.db.session() as session:
        session.add(
            BudgetPolicy(
                user_id=user_id,
                robot_id=robot_id,
                limit_amount=1.0,
                warn_threshold_percent=80,
                block_threshold_percent=100,
                status="ACTIVE",
            )
        )
        session.add(
            TokenUsageEvent(
                user_id=user_id,
                robot_id=robot_id,
                task_id="budget-task",
                provider="openai",
                model="gpt-5-mini",
                input_tokens=10,
                output_tokens=10,
                estimated_cost_usd=0.82,
                status="estimated",
            )
        )
        session.add(
            FileRetrievalEnablementRequest(
                user_id=user_id,
                robot_id=robot_id,
                task_id="enablement-task",
                status="REQUESTED_DISABLED",
                reason_code="FILE_RETRIEVAL_DISABLED_BY_POLICY",
            )
        )
        file_intake = session.scalar(select(FileIntakeAttempt).where(FileIntakeAttempt.user_id == user_id))
        assert file_intake is not None
        session.add(
            FileRetrievalAttempt(
                user_id=user_id,
                robot_id=robot_id,
                task_id="retrieval-task",
                file_intake_id=file_intake.id,
                request_kind="RETRIEVE",
                status="DISABLED_BY_POLICY",
            )
        )
        session.add(
            DocumentTask(
                user_id=user_id,
                robot_id=robot_id,
                task_id="doc-task",
                review_type="SUMMARY",
                source_kind="TEXT_SIMULATED",
                source_text_preview="NDA summary",
                source_text_hash="hash-1",
                status="DRAFTED",
            )
        )
        failed_task = Task(
            user_id=user_id,
            robot_id=robot_id,
            kind="GENERAL_TASK",
            input_text="old task",
            scope_decision="ANSWER",
            task_class="SIMPLE_CLASSIFICATION",
        )
        session.add(failed_task)
        session.flush()
        session.add(TaskRun(task_id=failed_task.id, status="failed"))
        session.add(
            ProposedMemory(
                user_id=user_id,
                robot_id=robot_id,
                task_id="proposal-task",
                memory_type="USER_PROFILE",
                proposed_content="Prefiere respuestas breves",
                source_text="recuerda esto",
                status="PENDING",
            )
        )
        session.add(
            MemoryItem(
                user_id=user_id,
                robot_id=robot_id,
                memory_type="WORK_PREFERENCE",
                content="Responder breve",
                display_label="Style",
                source="manual",
                status="ACTIVE",
                importance="high",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("qué se me pasó"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Encontré 7 cosas que necesitan atención usando solo lo que Robbie ya conoce:" in reply
    lines = [line.strip() for line in reply.splitlines() if line.strip().startswith(tuple(f"{i}." for i in range(1, 8)))]
    assert "1. Tu presupuesto está al 82%." == lines[0]
    assert "2. Tienes 1 solicitudes de enablement de retrieval pendientes." == lines[1]
    assert "3. Tienes 1 solicitudes de retrieval pendientes." == lines[2]
    assert "4. Hay 1 archivos recibidos que todavía no tienen revisión registrada." == lines[3]
    assert "5. Hay 1 documentos revisados recientemente que puedes conservar u olvidar." == lines[4]
    assert "6. Hay 1 tasks recientes que quedaron pendientes, bloqueados o fallidos." == lines[5]
    assert "7. Tienes 1 memorias pendientes de aprobación." == lines[6]
    assert "No revisé correo, WhatsApp, calendario ni web en vivo." in reply


@pytest.mark.anyio
async def test_attention_summary_empty_state_is_safe(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("qué se me pasó"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "No encontré nada pendiente con el estado local que Robbie conoce hoy." in reply
    assert "No revisé correo, WhatsApp, calendario, web ni archivos nuevos." in reply


@pytest.mark.anyio
async def test_attention_summary_is_scoped_by_user_and_robot(client):
    own_user_id, own_robot_id = await ensure_user_and_robot(client, user_id=123456, name="Francisco")
    other_user_id, other_robot_id = await ensure_user_and_robot(client, user_id=777, name="Alicia")

    with client.app.state.db.session() as session:
        session.add(
            FileRetrievalEnablementRequest(
                user_id=other_user_id,
                robot_id=other_robot_id,
                task_id="foreign-task",
                status="REQUESTED_DISABLED",
                reason_code="FILE_RETRIEVAL_DISABLED_BY_POLICY",
            )
        )
        session.add(
            MemoryItem(
                user_id=own_user_id,
                robot_id=own_robot_id,
                memory_type="WORK_PREFERENCE",
                content="Responder breve",
                display_label="Style",
                source="manual",
                status="ACTIVE",
                importance="high",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("what did I miss"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "solicitudes de enablement de retrieval" not in reply
    assert "memorias activas marcadas como importantes" in reply


@pytest.mark.anyio
async def test_attention_summary_creates_runtime_records_without_new_content_artifacts(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_text_update("qué se me pasó"))
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
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]


@pytest.mark.anyio
async def test_attention_summary_ignores_its_own_runtime_records_in_followup_runs(client):
    await ensure_user_and_robot(client)
    first = await client.post("/api/telegram/webhook", json=build_text_update("qué se me pasó"))
    assert first.status_code == 200
    second = await client.post("/api/telegram/webhook", json=build_text_update("qué se me pasó"))
    assert second.status_code == 200
    reply = second.json()["reply"]["text"]
    assert "tasks recientes que quedaron pendientes, bloqueados o fallidos" not in reply
