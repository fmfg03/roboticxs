from __future__ import annotations

from pathlib import Path

import pytest

from app.hermes_runtime_bootstrap import (
    DEFAULT_LOCAL_STATE_DIR,
    DEFAULT_OWNER_DISPLAY_NAME,
    DEFAULT_OWNER_ID,
    DEFAULT_ROBOT_ID,
    DEFAULT_RUNTIME_MODE,
    NEXT_STAGE,
    build_hermes_runtime_bootstrap_status,
    load_hermes_runtime_config_from_env,
    main,
    render_hermes_runtime_bootstrap_report,
    run_hermes_runtime_bootstrap,
    validate_hermes_runtime_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = REPO_ROOT / "app/hermes_runtime_bootstrap.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_129p_loads_runtime_config_with_safe_local_defaults():
    config = load_hermes_runtime_config_from_env(env={})

    assert config.runtime_mode == DEFAULT_RUNTIME_MODE
    assert config.robot_id == DEFAULT_ROBOT_ID
    assert config.owner_id == DEFAULT_OWNER_ID
    assert config.owner_display_name == DEFAULT_OWNER_DISPLAY_NAME
    assert config.local_state_dir == DEFAULT_LOCAL_STATE_DIR
    assert config.feature_flags.telegram_enabled is False
    assert config.feature_flags.connectors_enabled is False
    assert config.feature_flags.model_calls_enabled is False
    assert config.feature_flags.tools_enabled is False
    assert config.feature_flags.workers_enabled is False


def test_129p_accepts_explicit_owner_and_robot_env_overrides():
    config = load_hermes_runtime_config_from_env(
        env={
            "ROBOTICXS_RUNTIME_MODE": "local-dev",
            "ROBOTICXS_ROBOT_ID": "roboticxs-francisco",
            "ROBOTICXS_OWNER_ID": "francisco",
            "ROBOTICXS_OWNER_DISPLAY_NAME": "Francisco",
            "ROBOTICXS_LOCAL_STATE_DIR": "/tmp/roboticxs-state",
        }
    )

    assert config.robot_id == "roboticxs-francisco"
    assert config.owner_id == "francisco"
    assert config.owner_display_name == "Francisco"
    assert config.local_state_dir == "/tmp/roboticxs-state"


@pytest.mark.parametrize(
    ("env_key", "error_code"),
    [
        ("ROBOTICXS_ENABLE_TELEGRAM", "rejected_telegram_enabled_in_129p"),
        ("ROBOTICXS_ENABLE_CONNECTORS", "rejected_connectors_enabled_in_129p"),
        ("ROBOTICXS_ENABLE_MODEL_CALLS", "rejected_model_calls_enabled_in_129p"),
        ("ROBOTICXS_ENABLE_TOOLS", "rejected_tools_enabled_in_129p"),
        ("ROBOTICXS_ENABLE_WORKERS", "rejected_workers_enabled_in_129p"),
    ],
)
def test_129p_rejects_live_integration_flags(env_key: str, error_code: str):
    config = load_hermes_runtime_config_from_env(env={env_key: "true"})

    with pytest.raises(ValueError, match=error_code):
        validate_hermes_runtime_config(config)


def test_129p_builds_runtime_online_status_for_valid_local_config():
    status = build_hermes_runtime_bootstrap_status(
        config=load_hermes_runtime_config_from_env(env={}),
        generated_at="2026-06-21T12:00:00Z",
    )

    assert status.runtime_online is True
    assert status.runtime_mode == "local-dev"
    assert status.robot_id == DEFAULT_ROBOT_ID
    assert status.owner_id == DEFAULT_OWNER_ID
    assert status.roadmap_closed_through == "132P"
    assert status.next_stage_authorized is False
    assert status.next_stage == NEXT_STAGE
    assert status.telegram_enabled is False
    assert status.connectors_enabled is False
    assert status.model_calls_enabled is False
    assert status.tools_enabled is False
    assert status.workers_enabled is False
    assert status.external_writes_enabled is False
    assert status.memory_mutation_enabled is False
    assert "meeting_brief_demo_flow" in status.available_local_features
    assert "document_review_demo_flow" in status.available_local_features
    assert "demo_result_delivery_surface" in status.available_local_features
    assert "runnable_telegram_robot_mvp" in status.available_local_features


def test_129p_reports_missing_optional_module_as_unavailable_not_crash():
    status = build_hermes_runtime_bootstrap_status(
        config=load_hermes_runtime_config_from_env(env={}),
        module_candidates=(
            ("hermes_runtime_bootstrap", "app.hermes_runtime_bootstrap", True),
            ("missing_optional_feature", "app.this_module_does_not_exist_129p", False),
        ),
    )

    assert status.runtime_online is True
    assert status.unavailable_features == ("missing_optional_feature",)


def test_129p_text_report_contains_required_runtime_lines():
    report = run_hermes_runtime_bootstrap(generated_at="2026-06-21T12:00:00Z")

    assert "Hermes Runtime: online" in report.rendered_text
    assert f"Robot: {DEFAULT_ROBOT_ID}" in report.rendered_text
    assert f"Owner: {DEFAULT_OWNER_ID}" in report.rendered_text
    assert "Mode: local-dev" in report.rendered_text
    assert "Roadmap: 95P-132P CLOSED_COMMITTED" in report.rendered_text
    assert "Telegram: disabled" in report.rendered_text
    assert "Connectors: disabled" in report.rendered_text
    assert "LLM/model calls: disabled" in report.rendered_text
    assert "Tools: disabled" in report.rendered_text
    assert "Workers: disabled" in report.rendered_text
    assert "Memory Center: local/read-only bootstrap check" in report.rendered_text
    assert "Telegram Robot MVP: available if env is configured" in report.rendered_text
    assert "Daily Brief: available if local records exist" in report.rendered_text
    assert "Meeting Brief Demo: available if local records exist" in report.rendered_text
    assert "Document Review Demo: available if local records exist" in report.rendered_text
    assert "Next authorized stage: 133P+ remains unauthorized." in report.rendered_text


def test_129p_json_report_is_renderable():
    report = run_hermes_runtime_bootstrap(output_format="json")

    assert '"runtime_online": true' in report.rendered_text
    assert '"roadmap_closed_through": "132P"' in report.rendered_text


def test_129p_main_prints_report_and_returns_zero(capsys: pytest.CaptureFixture[str]):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Hermes Runtime: online" in captured.out
    assert captured.err == ""


def test_129p_main_returns_nonzero_for_invalid_live_enabled_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setenv("ROBOTICXS_ENABLE_TELEGRAM", "true")

    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "Hermes Runtime: offline" in captured.err
    assert "rejected_telegram_enabled_in_129p" in captured.err


def test_129p_bootstrap_module_has_no_network_or_external_execution_imports():
    text = BOOTSTRAP_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "api.telegram.org",
        "setWebhook",
        "uvicorn.run",
    ]:
        assert forbidden not in text


def test_129p_roadmap_registers_runtime_bootstrap_stage_and_132p_closed_with_133p_plus_block():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"129P","stage_name":"Hermes Runtime Bootstrap v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"130P","stage_name":"Runnable Telegram Robot MVP v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"131P","stage_name":"Telegram What Did I Miss Command v0","status":"CLOSED_COMMITTED"' in roadmap
    assert '"stage_id":"132P","stage_name":"Telegram Meeting Brief Command v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "133P and later remain unauthorized" in roadmap
