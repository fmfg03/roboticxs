from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import Task
from tests.test_attention_summary import build_text_update, ensure_user_and_robot


@pytest.mark.anyio
@pytest.mark.parametrize(
    "command",
    [
        "preflight web",
        "REVISAR TAREA WEB",
        "evaluar trámite web",
        "web workflow preflight",
        "check web workflow",
    ],
)
async def test_web_preflight_commands_match_exact_case_insensitive(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preflight web" in reply
    assert "Resultado: NEEDS_INFO" in reply


@pytest.mark.anyio
async def test_web_preflight_does_not_use_fuzzy_matching(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("preflight web por favor"))
    assert response.status_code == 200
    assert "Preflight web" not in response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        latest_task = session.scalar(select(Task).order_by(Task.created_at.desc()))
        assert latest_task is not None
        assert latest_task.kind == "GENERAL_TASK"


@pytest.mark.anyio
async def test_web_preflight_preparable_response(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes preparar checklist para la verificación en el portal del gobierno"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preflight web" in reply
    assert "Resultado: PREPARABLE" in reply
    assert "Lo que puedo hacer ahora" in reply
    assert "No usé navegador, Webwright ni Playwright." in reply


@pytest.mark.anyio
async def test_web_preflight_requires_login_response(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes entrar a mi cuenta del portal privado para revisar el trámite"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Resultado: REQUIRES_LOGIN" in reply
    assert "probablemente requeriría login" in reply
    assert "No hice login." in reply


@pytest.mark.anyio
async def test_web_preflight_requires_confirmation_response(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes sacar una cita en el portal de verificación"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Resultado: REQUIRES_CONFIRMATION" in reply
    assert "tendría que detenerse antes del envío para pedir confirmación" in reply


@pytest.mark.anyio
async def test_web_preflight_blocked_wins_for_payment(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes entrar a Telmex y pagar mi recibo"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "No. Esa acción está bloqueada." in reply
    assert "no puede ejecutar pagos" in reply


@pytest.mark.anyio
async def test_web_preflight_blocked_wins_for_legal_acceptance(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes aceptar términos y enviar el formulario"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "No. Esa acción está bloqueada." in reply
    assert "aceptar términos legales" in reply


@pytest.mark.anyio
async def test_web_preflight_not_supported_response(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes scrapear un portal con captcha"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Resultado: NOT_SUPPORTED" in reply
    assert "no está cubierta por el preflight local actual" in reply
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
async def test_web_preflight_limits_always_appear(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("preflight web"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Límites" in reply
    assert "No abrí ningún sitio web." in reply
    assert "No usé navegador, Webwright ni Playwright." in reply
    assert "No acepté términos legales." in reply
