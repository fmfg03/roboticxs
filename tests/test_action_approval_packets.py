from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import Task
from tests.test_attention_summary import build_text_update, ensure_user_and_robot


@pytest.mark.anyio
@pytest.mark.parametrize(
    "command",
    [
        "preparar aprobación",
        "PAQUETE DE APROBACIÓN",
        "revisar acción",
        "qué tendría que aprobar",
        "approval packet",
        "prepare approval",
    ],
)
async def test_exact_approval_commands_route_to_flow(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Paquete de aprobación preparado" in reply
    assert "No voy a ejecutar nada ni enviar nada." in reply


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("command", "expected_task"),
    [
        ("preparar aprobación para pagar telmex", "pagar telmex"),
        ("paquete de aprobación para agendar verificación", "agendar verificación"),
        ("revisar acción mandar correo a Juan", "mandar correo a Juan"),
        ("prepare approval for family groceries", "family groceries"),
    ],
)
async def test_trailing_task_text_is_preserved(client, command, expected_task):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    assert expected_task in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_payment_execution_request_is_blocked(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para pagar telmex"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "La acción está bloqueada en esta versión." in reply
    assert "No puedo ejecutar pagos ni iniciar cargos." in reply
    assert "No puedo ejecutar pagos ni guardar datos de tarjeta/CVV." in reply


@pytest.mark.anyio
async def test_manual_payment_preparation_is_local_only(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para preparar checklist para que yo pague telmex manualmente"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preparación local para pago manual solamente." in reply
    assert "No voy a ejecutar nada ni enviar nada." in reply
    assert "No puedo ejecutar pagos ni guardar datos de tarjeta/CVV." in reply


@pytest.mark.anyio
async def test_checkout_without_payment_requires_later_confirmation(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para preparar carrito del súper sin pagar"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preparación de revisión de carrito o pedido, sin checkout ni pago." in reply
    assert "No puedo crear checkout ni colocar pedidos." in reply
    assert "Tendrías que confirmar:" in reply


@pytest.mark.anyio
async def test_send_external_message_requires_later_confirmation(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para mandar correo a Juan"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preparación de mensaje o correo para revisión posterior." in reply
    assert "No voy a enviar correos ni mensajes." in reply


@pytest.mark.anyio
async def test_schedule_external_event_requires_later_confirmation(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para agendar verificación"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preparación de cita o evento externo para revisión posterior." in reply
    assert "No voy a reservar ni agendar citas." in reply


@pytest.mark.anyio
async def test_legal_or_professional_decision_is_blocked(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para aceptar contrato"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "decisión legal o profesional" in reply
    assert "No doy consejo legal, fiscal, médico, financiero ni laboral." in reply


@pytest.mark.anyio
async def test_credential_or_permission_change_is_blocked(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para cambiar mi contraseña"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "credenciales, permisos o configuración sensible" in reply
    assert "No puedo cambiar contraseñas, permisos ni métodos de pago." in reply


@pytest.mark.anyio
async def test_destructive_action_is_blocked(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para borrar mi cuenta de banco"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "destructiva y está bloqueada" in reply
    assert "No puedo borrar cuentas, archivos o registros." in reply


@pytest.mark.anyio
async def test_vague_task_needs_more_information(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para eso"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Necesito más información antes de preparar el paquete." in reply
    assert "Qué tipo de tarea es." in reply


@pytest.mark.anyio
async def test_response_always_contains_no_execution_boundary(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("approval packet"))
    assert response.status_code == 200
    assert "No voy a ejecutar nada ni enviar nada." in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_action_approval_no_side_effects_and_runtime_records_only(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("preparar aprobación para mandar correo a Juan"),
    )
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["proposals"] == before["proposals"]
    assert after["memories"] == before["memories"]
    assert after["documents"] == before["documents"]
    assert after["file_intakes"] == before["file_intakes"]
    assert after["file_retrieval_attempts"] == before["file_retrieval_attempts"]
    assert after["file_retrieval_enablement_requests"] == before["file_retrieval_enablement_requests"]


@pytest.mark.anyio
async def test_prior_stage_commands_still_route(client):
    await ensure_user_and_robot(client)
    commands = [
        "qué se me pasó",
        "mi información importante",
        "qué puedes hacer",
        "súper familiar",
        "preflight web",
    ]
    for command in commands:
        response = await client.post("/api/telegram/webhook", json=build_text_update(command))
        assert response.status_code == 200
        assert response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_action_approval_fuzzy_command_does_not_match_exact_flow(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("approval packet please"))
    assert response.status_code == 200
    assert "Paquete de aprobación preparado" not in response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "GENERAL_TASK"
