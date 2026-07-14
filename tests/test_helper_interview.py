from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from app.config import Settings
from app.helper_interview import generate_helper_interview_turn
from app.robbie_conversation import RobbieConversationError


def _structured_response(payload: dict[str, object]) -> dict[str, object]:
    return {
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(payload, ensure_ascii=False),
                    }
                ],
            }
        ]
    }


def test_openai_turn_uses_store_false_and_strict_schema():
    captured: dict[str, object] = {}

    def transport(endpoint, payload, api_key, timeout):
        captured.update(
            endpoint=endpoint,
            payload=payload,
            api_key=api_key,
            timeout=timeout,
        )
        return _structured_response(
            {
                "acknowledgement": "Entiendo que hoy tú llevas sola esta responsabilidad.",
                "extracted_facts": ["La usuaria está sola a cargo."],
                "missing_topics": ["desired_help", "boundaries"],
                "next_question": "¿Qué te quitaría más peso ahora: recordatorios, rutinas o seguimiento?",
                "ready_to_summarize": False,
                "support_ideas": ["Recordatorios revisados por la usuaria"],
                "risk_level": "routine",
            }
        )

    settings = Settings(
        helper_interview_provider="openai",
        helper_interview_model="gpt-5.6-luna",
        helper_interview_timeout_seconds=9,
        openai_api_key="secret-test-key",
    )
    turn = generate_helper_interview_turn(
        answers={"people_and_roles": "Solo yo"},
        latest_user_text="Solo yo",
        shared_context="Contexto aceptado por la usuaria.",
        settings=settings,
        processing_mode="openai",
        transport=transport,
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is False
    assert payload["model"] == "gpt-5.6-luna"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert captured["api_key"] == "secret-test-key"
    assert turn.provider == "openai"
    assert "llevas sola" in turn.acknowledgement
    assert turn.next_question.count("?") == 1


def test_provider_failure_falls_back_to_contextual_question(monkeypatch: pytest.MonkeyPatch):
    def unavailable(*_args, **_kwargs):
        raise URLError("offline")

    def local_unavailable(**_kwargs):
        raise RobbieConversationError("offline")

    monkeypatch.setattr("app.helper_interview.generate_robbie_reply", local_unavailable)
    settings = Settings(
        helper_interview_provider="openai",
        openai_api_key="secret-test-key",
    )

    turn = generate_helper_interview_turn(
        answers={"situation": "Mi mamá tiene deterioro cognitivo"},
        latest_user_text="Estoy pendiente de mi mamá",
        shared_context="",
        settings=settings,
        processing_mode="openai",
        transport=unavailable,
    )

    assert turn.provider == "deterministic_fallback"
    assert "seguridad" in turn.next_question
    assert turn.next_question.count("?") == 1
