from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.telegram_runtime import (
    TELEGRAM_RUNTIME_WEBHOOK_PATH,
    build_telegram_runtime_smoke_readiness,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_RUNTIME_SMOKE_MANUAL_WIRING_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
RUNTIME_PATH = REPO_ROOT / "app/telegram_runtime.py"
CONFIG_PATH = REPO_ROOT / "app/config.py"
TEST_TOKEN = "123456:" + "ABCdefSecretTokenForReadiness"
PUBLIC_WEBHOOK_URL = f"https://roboticxs.example.com{TELEGRAM_RUNTIME_WEBHOOK_PATH}"


def test_missing_token_and_webhook_config_fail_safely():
    readiness = build_telegram_runtime_smoke_readiness(Settings())

    assert readiness.ready is False
    assert readiness.token_configured is False
    assert readiness.webhook_url_configured is False
    assert readiness.webhook_url_valid is False
    assert readiness.runtime_webhook_path == TELEGRAM_RUNTIME_WEBHOOK_PATH
    assert readiness.failure_reasons == (
        "telegram_bot_token_missing",
        "telegram_public_webhook_url_missing",
    )
    assert readiness.diagnostics["telegram_bot_token"] == "missing"


def test_valid_local_smoke_config_reports_ready_without_exposing_token():
    readiness = build_telegram_runtime_smoke_readiness(
        Settings(
            telegram_bot_token=TEST_TOKEN,
            telegram_public_webhook_url=PUBLIC_WEBHOOK_URL,
        )
    )
    rendered = repr(readiness.diagnostics) + repr(readiness)

    assert readiness.ready is True
    assert readiness.failure_reasons == ()
    assert readiness.token_configured is True
    assert readiness.webhook_url_configured is True
    assert readiness.webhook_url_valid is True
    assert readiness.diagnostics["telegram_bot_token"] == "configured_redacted"
    assert readiness.diagnostics["external_telegram_api_call"] is False
    assert readiness.diagnostics["automatic_webhook_registration"] is False
    assert readiness.diagnostics["production_deployment"] is False
    assert TEST_TOKEN not in rendered


def test_webhook_url_validation_is_safe_and_rejects_bad_urls():
    invalid_urls = [
        "http://roboticxs.example.com/api/telegram/runtime/webhook",
        "https://roboticxs.example.com/api/telegram/webhook",
        f"https://roboticxs.example.com/{TEST_TOKEN}/api/telegram/runtime/webhook",
        "https://roboticxs.example.com/api/telegram/runtime/webhook with-space",
        "https://localhost/api/telegram/runtime/webhook",
    ]

    for webhook_url in invalid_urls:
        readiness = build_telegram_runtime_smoke_readiness(
            Settings(telegram_bot_token=TEST_TOKEN, telegram_public_webhook_url=webhook_url)
        )

        assert readiness.ready is False
        assert readiness.failure_reasons == ("telegram_public_webhook_url_invalid",)
        assert TEST_TOKEN not in repr(readiness.diagnostics)


def test_get_settings_reads_public_webhook_url_without_printing_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("TELEGRAM_PUBLIC_WEBHOOK_URL", PUBLIC_WEBHOOK_URL)

    settings = get_settings()
    readiness = build_telegram_runtime_smoke_readiness(settings)

    assert settings.telegram_bot_token == TEST_TOKEN
    assert settings.telegram_public_webhook_url == PUBLIC_WEBHOOK_URL
    assert readiness.ready is True
    assert TEST_TOKEN not in repr(readiness)


def test_runtime_smoke_document_exists_with_required_sections_and_decision_text():
    text = DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Why this stage exists",
        "Required environment variables",
        "Secret handling rules",
        "Webhook path",
        "Manual webhook setup checklist",
        "Manual smoke checklist",
        "Readiness behavior",
        "Redacted diagnostics",
        "What is intentionally not implemented",
        "Failure modes",
        "Future stages unlocked",
        "Authority boundaries",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "81P establishes a safe manual Telegram runtime smoke path.",
        "It does not implement production deployment.",
        "It does not automatically register Telegram webhooks.",
        "It does not call the real Telegram API in tests.",
        "It does not commit Telegram secrets.",
        "It does not implement caregiver routines.",
        "It does not implement document intake.",
        "It does not implement memory writes.",
        "It does not implement ProposedMemory writes.",
        "It does not implement retrieval.",
        "It does not implement connectors.",
        "It does not implement proactive messaging.",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_PUBLIC_WEBHOOK_URL",
        "POST /api/telegram/runtime/webhook",
    ]:
        assert required in text


def test_runtime_smoke_makes_no_real_telegram_api_call_or_webhook_registration():
    runtime_text = RUNTIME_PATH.read_text()
    config_text = CONFIG_PATH.read_text()

    for forbidden in [
        "requests",
        "httpx",
        "urllib",
        "socket",
        "setWebhook",
        "api.telegram.org",
        "subprocess",
    ]:
        assert forbidden not in runtime_text
        assert forbidden not in config_text


def test_no_raw_token_or_env_secret_is_committed_in_81p_files():
    for path in [
        DOC_PATH,
        RUNTIME_PATH,
        CONFIG_PATH,
        REPO_ROOT / "tests/test_telegram_runtime_smoke.py",
    ]:
        text = path.read_text()

        assert TEST_TOKEN not in text
        assert ("TELEGRAM_BOT_TOKEN" + "=") not in text
        assert ".env" not in str(path)


def test_runtime_smoke_boundaries_do_not_add_forbidden_product_behavior():
    runtime_text = RUNTIME_PATH.read_text()

    for forbidden in [
        "file_retrieval",
        "document_control",
        "voice_caregiver",
        "caregiver_relay",
        "scheduler",
    ]:
        assert forbidden not in runtime_text
    assert "import connector" not in runtime_text
    assert "connectors." not in runtime_text


def test_roadmap_marks_81p_complete_and_later_82p_without_inventing_83p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/reference/TELEGRAM_RUNTIME_SMOKE_MANUAL_WIRING_v0_1.md"' in text
    assert '"tests/test_telegram_runtime_smoke.py"' in text
    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"83P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
