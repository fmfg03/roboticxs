from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import MemoryItem, ProposedMemory, Task
from tests.test_attention_summary import build_text_update, ensure_user_and_robot


@pytest.mark.anyio
@pytest.mark.parametrize(
    "command",
    [
        "súper familiar",
        "SUPER FAMILIAR",
        "preparar súper familiar",
        "lista del super familiar",
        "family groceries",
    ],
)
async def test_super_familiar_commands_match_exact_case_insensitive(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    assert "Súper Familiar" in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_super_familiar_does_not_use_fuzzy_matching(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("super familiar por favor"))
    assert response.status_code == 200
    assert "Súper Familiar" not in response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "GENERAL_TASK"


@pytest.mark.anyio
async def test_super_familiar_empty_setup_checklist_when_no_explicit_grocery_data(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("súper familiar"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Súper Familiar todavía no tiene suficiente información local." in reply
    assert "1. ¿Para quién es el súper?" in reply
    assert "7. ¿Quién aprueba antes de pagar?" in reply
    assert "No revisé Walmart, Costco, correo, WhatsApp, calendario, web ni archivos nuevos." in reply


@pytest.mark.anyio
async def test_super_familiar_preparation_view_from_explicit_approved_grocery_memories(client):
    user_id, robot_id = await ensure_user_and_robot(client)
    with client.app.state.db.session() as session:
        session.add_all(
            [
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="TASK_MEMORY",
                    content="Lista del súper: leche deslactosada, huevos, pan integral.",
                    display_label="Memory",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="TASK_MEMORY",
                    content="Mis suegros prefieren leche deslactosada y no comprar azúcar.",
                    display_label="Memory",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
                MemoryItem(
                    user_id=user_id,
                    robot_id=robot_id,
                    memory_type="TASK_MEMORY",
                    content="Presupuesto de súper: 1500 pesos para mis suegros.",
                    display_label="Memory",
                    source="telegram_text",
                    status="ACTIVE",
                    importance="high",
                ),
            ]
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("preparar súper familiar"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Para quién" in reply
    assert "- Suegros registrado en memoria aprobada." in reply
    assert "Lista base" in reply
    assert "- Leche deslactosada" in reply
    assert "- Huevos" in reply
    assert "- Pan integral" in reply
    assert "¿Qué tienda suelen usar?" in reply
    assert "¿Qué día u horario conviene?" in reply
    assert "¿Quién aprueba antes de pagar?" in reply
    assert "No puedo crear carrito ni checkout." in reply


@pytest.mark.anyio
async def test_generic_family_memory_does_not_create_base_list(client):
    user_id, robot_id = await ensure_user_and_robot(client)
    with client.app.state.db.session() as session:
        session.add(
            MemoryItem(
                user_id=user_id,
                robot_id=robot_id,
                memory_type="TASK_MEMORY",
                content="Mis suegros viven en Monterrey.",
                display_label="Memory",
                source="telegram_text",
                status="ACTIVE",
                importance="normal",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("super familiar"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Lista base" not in reply
    assert "Súper Familiar todavía no tiene suficiente información local." in reply


@pytest.mark.anyio
async def test_pending_grocery_memory_shown_only_as_pending(client):
    user_id, robot_id = await ensure_user_and_robot(client)
    with client.app.state.db.session() as session:
        session.add(
            ProposedMemory(
                user_id=user_id,
                robot_id=robot_id,
                task_id="pending-grocery",
                memory_type="TASK_MEMORY",
                proposed_content="Lista del súper: leche, yogurt y plátanos para mis papás.",
                source_text="remember this",
                status="PENDING",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("súper familiar"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Pendiente de aprobación" in reply
    assert "compras familiares" in reply
    assert "Lista base" not in reply
    assert "- Leche" not in reply


@pytest.mark.anyio
async def test_super_familiar_is_scoped_by_user_and_robot(client):
    own_user_id, own_robot_id = await ensure_user_and_robot(client, user_id=123456, name="Francisco")
    other_user_id, other_robot_id = await ensure_user_and_robot(client, user_id=777, name="Alicia")
    with client.app.state.db.session() as session:
        session.add(
            MemoryItem(
                user_id=other_user_id,
                robot_id=other_robot_id,
                memory_type="TASK_MEMORY",
                content="Lista del súper: salmón, quinoa y arándanos para mis padres.",
                display_label="Memory",
                source="telegram_text",
                status="ACTIVE",
                importance="high",
            )
        )
        session.add(
            MemoryItem(
                user_id=own_user_id,
                robot_id=own_robot_id,
                memory_type="TASK_MEMORY",
                content="Lista del súper: leche, huevos y pan para mis papás.",
                display_label="Memory",
                source="telegram_text",
                status="ACTIVE",
                importance="high",
            )
        )
        session.commit()

    response = await client.post("/api/telegram/webhook", json=build_text_update("lista del súper familiar"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Leche" in reply
    assert "Huevos" in reply
    assert "Salmón" not in reply


@pytest.mark.anyio
async def test_super_familiar_no_side_effects_and_runtime_records_only(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_text_update("súper familiar"))
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
