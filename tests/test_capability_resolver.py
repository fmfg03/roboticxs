from __future__ import annotations

import pytest

from tests.test_attention_summary import build_text_update, ensure_user_and_robot


@pytest.mark.anyio
@pytest.mark.parametrize(
    "command",
    [
        "qué puedes hacer",
        "QUÉ HABILIDADES TIENES",
        "habilidades",
        "skill catalog",
        "what can you do",
        "what skills do you have",
    ],
)
async def test_capability_catalog_commands_match_exact_case_insensitive(client, command):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(command))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Estas son las habilidades que Robbie tiene hoy:" in reply
    assert "Disponible ahora" in reply
    assert "Planeado" in reply
    assert "Bloqueado" in reply


@pytest.mark.anyio
async def test_capability_catalog_does_not_use_fuzzy_matching(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("skill catalog please"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Estas son las habilidades que Robbie tiene hoy:" not in reply


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("¿puedes decirme qué se me pasó?", 'Escribe: "qué se me pasó".'),
        ("puedes mostrarme lo que robbie sabe", 'Escribe: "mi información importante".'),
        ("can you help me with what did i miss", 'Escribe: "qué se me pasó".'),
    ],
)
async def test_capability_query_resolves_available_read_only(client, query, expected):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(query))
    assert response.status_code == 200
    assert expected in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_capability_query_resolves_needs_approval_for_memory(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("puedes recordar esto para después"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "necesita aprobación" in reply
    assert "proponerte memoria" in reply


@pytest.mark.anyio
async def test_capability_query_resolves_available_draft_only_super_familiar(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("¿puedes ayudarme con el súper de mis suegros?"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Sí, puedo ayudarte en modo preparación." in reply
    assert "no puedo entrar a Walmart" in reply
    assert "crear carrito" in reply
    assert "hacer pedidos" in reply


@pytest.mark.anyio
async def test_capability_query_resolves_action_approval_packets_as_available_draft_only(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes ayudarme a aprobar una acción?"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "puedo prepararte un paquete de aprobación" in reply.lower()
    assert "No voy a ejecutar nada ni enviar nada." in reply


@pytest.mark.anyio
async def test_capability_query_routes_web_workflow_requests_to_preflight_response(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes ayudarme con un trámite web de verificación"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preflight web" in reply
    assert "Resultado: NEEDS_INFO" in reply
    assert "No usé navegador, Webwright ni Playwright." in reply
    assert "No envié formularios." in reply


@pytest.mark.anyio
async def test_capability_query_blocked_for_payment(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("¿puedes pagar Telmex?"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "está bloqueada" in reply
    assert "no puede ejecutar pagos" in reply


@pytest.mark.anyio
async def test_capability_query_blocked_wins_over_planned(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("puedes pagar el súper de mis papás"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "está bloqueada" in reply
    assert "Súper Familiar" not in reply


@pytest.mark.anyio
async def test_capability_catalog_marks_super_familiar_as_available_draft_only(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("qué puedes hacer"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Disponible ahora" in reply
    assert "Súper Familiar — Prepara una vista local de súper familiar" in reply


@pytest.mark.anyio
async def test_capability_catalog_marks_web_workflow_preflight_as_available_draft_only(client):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update("qué puedes hacer"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Web Workflow Preflight — Evalúa localmente si una tarea web puede prepararse" in reply


@pytest.mark.anyio
async def test_capability_query_routes_unsupported_web_task_to_not_supported(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes scrapear un portal con captcha"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Preflight web" in reply
    assert "Resultado: NOT_SUPPORTED" in reply
    assert "No abrí ningún sitio web." in reply
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
@pytest.mark.parametrize(
    "query",
    [
        "puedes aceptar términos por mí",
        "puedes cambiar mi password",
        "puedes borrar cuenta externa",
    ],
)
async def test_capability_query_blocked_for_legal_credentials_destructive(client, query):
    await ensure_user_and_robot(client)
    response = await client.post("/api/telegram/webhook", json=build_text_update(query))
    assert response.status_code == 200
    assert "está bloqueada" in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_capability_query_agentius_candidate(client, db_counts):
    await ensure_user_and_robot(client)
    before = db_counts()
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("¿puedes automatizar mi CRM y el seguimiento de clientes de mi equipo?"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "workflow de negocio" in reply
    assert "candidato para Agentius" in reply
    assert "No voy a crear un lead" in reply
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
async def test_capability_query_unknown_fallback(client):
    await ensure_user_and_robot(client)
    response = await client.post(
        "/api/telegram/webhook",
        json=build_text_update("puedes ayudarme con algo rarísimo no clasificado"),
    )
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "No puedo clasificar esa petición con el catálogo local actual." in reply
    assert "qué puedes hacer" in reply
