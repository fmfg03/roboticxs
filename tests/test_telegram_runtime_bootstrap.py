from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.hermes_runtime import HermesRuntimeRequest
from app.telegram_runtime import (
    TELEGRAM_RUNTIME_CHANNEL,
    TelegramRuntimeError,
    build_hermes_request_from_telegram,
    get_telegram_bot_runtime_config,
    handle_telegram_runtime_update,
    parse_telegram_text_update,
    prepare_telegram_text_send,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_BOT_RUNTIME_BOOTSTRAP_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
RUNTIME_PATH = REPO_ROOT / "app/telegram_runtime.py"


def build_text_update(text: str = "hello roboticxs") -> dict:
    return {
        "update_id": 79001,
        "message": {
            "message_id": 902,
            "date": 1710000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {
                "id": 987654,
                "is_bot": False,
                "first_name": "Francisco",
                "username": "francisco",
            },
            "text": text,
        },
    }


def test_parse_telegram_text_update_extracts_minimal_message_fields():
    message = parse_telegram_text_update(build_text_update("  hello runtime  "))

    assert message.chat_id == 123456
    assert message.user_id == 987654
    assert message.message_id == 902
    assert message.text == "hello runtime"
    assert message.username == "francisco"
    assert message.first_name == "Francisco"
    assert message.metadata["update_id"] == "79001"
    assert message.metadata["chat_type"] == "private"


def test_telegram_message_converts_to_hermes_runtime_request():
    message = parse_telegram_text_update(build_text_update("ship the channel"))
    request = build_hermes_request_from_telegram(message)

    assert isinstance(request, HermesRuntimeRequest)
    assert request.user_id == "987654"
    assert request.channel == TELEGRAM_RUNTIME_CHANNEL
    assert request.text == "ship the channel"
    assert request.metadata["telegram_chat_id"] == "123456"
    assert request.metadata["telegram_message_id"] == "902"
    assert request.metadata["telegram_username"] == "francisco"


def test_handle_telegram_runtime_update_dispatches_through_hermes_and_prepares_send():
    result = handle_telegram_runtime_update(update=build_text_update("hello"), settings=Settings())

    assert result.ok is True
    assert result.hermes_request.channel == "telegram"
    assert result.hermes_response.status == "ok"
    assert "Hermes runtime foundation is available." in result.hermes_response.text
    assert result.prepared_send.method == "sendMessage"
    assert result.prepared_send.payload == {
        "chat_id": 123456,
        "text": result.hermes_response.text,
    }
    assert result.prepared_send.token_configured is False


def test_sender_abstraction_records_token_presence_without_exposing_secret():
    config = get_telegram_bot_runtime_config(Settings(telegram_bot_token="secret-token"))
    prepared = prepare_telegram_text_send(chat_id=1, text="hello", config=config)

    assert prepared.token_configured is True
    assert prepared.payload == {"chat_id": 1, "text": "hello"}
    assert "secret-token" not in repr(prepared)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": {"chat": {"id": 1}, "from": {"id": 2}, "message_id": 3}},
        {"message": {"chat": {"id": 1}, "from": {"id": 2}, "message_id": 3, "text": "   "}},
        {"message": {"chat": {"id": 1}, "from": {"id": 2}, "message_id": 3, "document": {"file_id": "f"}}},
        {"message": {"chat": {"id": 1}, "from": {"id": 2}, "message_id": 3, "voice": {"file_id": "v"}}},
    ],
)
def test_missing_invalid_and_non_text_payloads_fail_safely(payload):
    with pytest.raises(TelegramRuntimeError):
        parse_telegram_text_update(payload)


def test_telegram_runtime_module_has_no_real_api_network_file_or_external_path():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "file_retrieval",
        "scheduler",
    ]:
        assert forbidden not in text
    assert "import connector" not in text
    assert "connectors." not in text


@pytest.mark.anyio
async def test_runtime_webhook_returns_prepared_send_without_persistence(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/runtime/webhook", json=build_text_update("hello"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["chat_id"] == 123456
    assert body["user_id"] == 987654
    assert body["message_id"] == 902
    assert body["hermes_request"]["channel"] == "telegram"
    assert body["prepared_send"]["method"] == "sendMessage"
    assert body["prepared_send"]["payload"]["chat_id"] == 123456
    assert body["prepared_send"]["token_configured"] is False
    assert body["hermes_response"]["status"] == "ok"
    assert body["trace"]["loop"] == "telegram_conversation_loop"

    after = db_counts()
    assert after == before


@pytest.mark.anyio
async def test_runtime_webhook_rejects_unsupported_payload_without_crashing(client):
    response = await client.post(
        "/api/telegram/runtime/webhook",
        json={"message": {"chat": {"id": 1}, "from": {"id": 2}, "message_id": 3, "document": {"file_id": "f"}}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["unsupported"] is True
    assert body["error_code"] == "unsupported_non_text"
    assert body["prepared_send"]["payload"]["text"] == "Por ahora solo puedo procesar mensajes de texto."


def test_telegram_runtime_document_exists_and_records_boundaries():
    text = DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Why Telegram follows Hermes",
        "Runtime channel flow",
        "Parser scope",
        "Hermes runtime adapter",
        "Sender abstraction",
        "Configuration boundary",
        "Web binding",
        "Unsupported payload behavior",
        "What is intentionally not implemented",
        "Authority boundaries",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for boundary in [
        "It does not call the Telegram API.",
        "It does not expose the bot token.",
        "caregiver runtime",
        "`MemoryItem` writes",
        "`ProposedMemory` writes",
        "retrieval",
        "connectors",
        "background/proactive messaging",
        "does not authorize 80P as `NEXT_ELIGIBLE`",
    ]:
        assert boundary in text


def test_roadmap_marks_79p_complete_and_later_stages_without_inventing_86p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"79P","stage_name":"Telegram Bot Runtime Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"app/telegram_runtime.py"' in text
    assert '"tests/test_telegram_runtime_bootstrap.py"' in text
    assert '"docs/reference/TELEGRAM_BOT_RUNTIME_BOOTSTRAP_v0_1.md"' in text
    assert '"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"IMPLEMENTED_PENDING_REVIEW"' in text
    assert '"stage_id":"86P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
