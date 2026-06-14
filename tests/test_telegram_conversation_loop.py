from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.hermes_runtime import HermesRuntimeRequest, HermesRuntimeResponse
from app.telegram_runtime import (
    TELEGRAM_CONVERSATION_REPLY,
    TELEGRAM_EMPTY_TEXT_REPLY,
    TELEGRAM_MALFORMED_REPLY,
    TELEGRAM_UNSUPPORTED_REPLY,
    build_telegram_conversation_webhook_response,
    run_telegram_conversation_loop,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_CONVERSATION_LOOP_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
RUNTIME_PATH = REPO_ROOT / "app/telegram_runtime.py"


def build_text_update(text: str = "hola") -> dict:
    return {
        "update_id": 1001,
        "message": {
            "message_id": 2002,
            "from": {"id": 3003, "username": "test_user"},
            "chat": {"id": 4004, "type": "private"},
            "text": text,
        },
    }


def test_valid_text_payload_returns_deterministic_telegram_reply():
    result = run_telegram_conversation_loop(update=build_text_update("hola"), settings=Settings())
    body = build_telegram_conversation_webhook_response(result)

    assert result.ok is True
    assert body["chat_id"] == 4004
    assert body["user_id"] == 3003
    assert body["message_id"] == 2002
    assert body["hermes_request"]["channel"] == "telegram"
    assert body["hermes_request"]["text"] == "hola"
    assert body["prepared_send"]["method"] == "sendMessage"
    assert body["prepared_send"]["payload"] == {"chat_id": 4004, "text": TELEGRAM_CONVERSATION_REPLY}
    assert body["hermes_response"]["text"] == TELEGRAM_CONVERSATION_REPLY
    assert body["trace"]["dispatch"] == "hermes_runtime_foundation"
    assert body["trace"]["external_telegram_api_call"] == "false"


def test_loop_dispatches_through_injected_hermes_runtime_boundary():
    calls: list[HermesRuntimeRequest] = []

    def dispatch(request: HermesRuntimeRequest) -> HermesRuntimeResponse:
        calls.append(request)
        return HermesRuntimeResponse(
            status="ok",
            text="foundation",
            task_id=None,
            safety_decision=None,
            metadata={"source": "test"},
        )

    result = run_telegram_conversation_loop(update=build_text_update("hola"), settings=Settings(), dispatch=dispatch)

    assert len(calls) == 1
    assert calls[0].channel == "telegram"
    assert calls[0].metadata["telegram_chat_id"] == "4004"
    assert result.hermes_response is not None
    assert result.hermes_response.metadata["telegram_conversation_loop"] == "active"


def test_empty_text_returns_safe_prompt_without_dispatching():
    def dispatch(_: HermesRuntimeRequest) -> HermesRuntimeResponse:
        raise AssertionError("empty text must not dispatch")

    result = run_telegram_conversation_loop(update=build_text_update("   "), settings=Settings(), dispatch=dispatch)

    assert result.ok is False
    assert result.error_code == "empty_text"
    assert result.prepared_send is not None
    assert result.prepared_send.payload == {"chat_id": 4004, "text": TELEGRAM_EMPTY_TEXT_REPLY}


def test_unsupported_non_text_returns_safe_fallback_without_file_handling():
    def dispatch(_: HermesRuntimeRequest) -> HermesRuntimeResponse:
        raise AssertionError("unsupported content must not dispatch")

    update = {
        "message": {
            "message_id": 2002,
            "from": {"id": 3003},
            "chat": {"id": 4004, "type": "private"},
            "document": {"file_id": "file-id"},
        }
    }
    result = run_telegram_conversation_loop(update=update, settings=Settings(), dispatch=dispatch)

    assert result.ok is False
    assert result.unsupported is True
    assert result.error_code == "unsupported_non_text"
    assert result.prepared_send is not None
    assert result.prepared_send.payload == {"chat_id": 4004, "text": TELEGRAM_UNSUPPORTED_REPLY}


def test_malformed_payload_returns_ignored_safe_error_without_stack_trace():
    result = run_telegram_conversation_loop(update={"update_id": 1}, settings=Settings())
    body = build_telegram_conversation_webhook_response(result)

    assert result.ok is False
    assert result.ignored is True
    assert result.prepared_send is None
    assert body["error_code"] == "malformed_payload"
    assert "Traceback" not in str(body)
    assert ".py" not in str(body)


def test_runtime_dispatch_error_returns_safe_fallback_without_stack_trace():
    def dispatch(_: HermesRuntimeRequest) -> HermesRuntimeResponse:
        raise RuntimeError("sensitive internal failure")

    result = run_telegram_conversation_loop(update=build_text_update("hola"), settings=Settings(), dispatch=dispatch)
    body = build_telegram_conversation_webhook_response(result)

    assert result.ok is False
    assert result.error_code == "runtime_dispatch_error"
    assert result.prepared_send is not None
    assert result.prepared_send.payload == {"chat_id": 4004, "text": TELEGRAM_MALFORMED_REPLY}
    assert body["trace"]["error_type"] == "RuntimeError"
    assert "sensitive internal failure" not in str(body)
    assert "Traceback" not in str(body)


@pytest.mark.anyio
async def test_runtime_webhook_route_uses_conversation_loop(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/runtime/webhook", json=build_text_update("hola"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["chat_id"] == 4004
    assert body["prepared_send"]["payload"] == {"chat_id": 4004, "text": TELEGRAM_CONVERSATION_REPLY}
    assert body["hermes_response"]["metadata"]["telegram_conversation_loop"] == "active"
    assert body["trace"]["persistence"] == "deferred"
    assert db_counts() == before


def test_telegram_conversation_module_has_no_network_file_or_external_paths():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "download",
        "file_retrieval",
        "scheduler",
    ]:
        assert forbidden not in text
    assert "import connector" not in text
    assert "connectors." not in text


def test_required_conversation_loop_document_exists_with_decision_text():
    text = DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Why this stage exists",
        "Conversation loop path",
        "Supported input",
        "Unsupported input",
        "Error behavior",
        "Trace behavior",
        "Runtime dispatch behavior",
        "Telegram response behavior",
        "What is intentionally not implemented",
        "Future stages unlocked",
        "Authority boundaries",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "80P establishes a minimal Telegram conversation loop for Roboticxs.",
        "It builds on the Hermes runtime foundation and Telegram runtime bootstrap.",
        "It supports text-message loop handling only.",
        "It does not implement caregiver routines.",
        "It does not implement document intake.",
        "It does not implement voice handling.",
        "It does not implement memory writes.",
        "It does not implement ProposedMemory writes.",
        "It does not implement retrieval.",
        "It does not implement connectors.",
        "It does not implement proactive messaging.",
        "It does not call the real Telegram API in tests.",
        "It does not authorize production deployment.",
    ]:
        assert required in text


def test_roadmap_marks_80p_complete_and_later_stages_without_inventing_86p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/reference/TELEGRAM_CONVERSATION_LOOP_v0_1.md"' in text
    assert '"tests/test_telegram_conversation_loop.py"' in text
    assert '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"87P"' in text
    assert '"stage_id":"87P","stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"88P"' in text
    assert '"stage_id":"88P","stage_name":"Routine Wake Gate / Zero-Token Preflight v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"89P"' in text
    assert '"stage_id":"89P","stage_name":"Roboticxs Automation Blueprints v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"90P"' in text
    assert '"stage_id":"90P","stage_name":"Roboticxs Command Surface Policy v0","status":"IMPLEMENTED_PENDING_REVIEW"' in text
    assert '"stage_id":"91P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
