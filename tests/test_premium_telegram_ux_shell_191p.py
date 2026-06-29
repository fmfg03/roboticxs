from __future__ import annotations

from pathlib import Path

import pytest

from app.premium_telegram_ux_shell import (
    PRODUCT_INTENTS,
    TelegramUxCard,
    build_premium_telegram_help_sections,
    build_premium_telegram_home_sections,
    build_premium_telegram_status_sections,
    render_premium_shell_boundaries,
    render_telegram_ux_card,
    render_telegram_ux_sections,
)
from app.runnable_telegram_robot_mvp import (
    build_telegram_robot_startup_report,
    load_telegram_robot_config_from_env,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    validate_telegram_robot_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/PREMIUM_TELEGRAM_UX_SHELL_191P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_valid_config():
    return validate_telegram_robot_config(
        load_telegram_robot_config_from_env(
            env={
                "ROBOTICXS_TELEGRAM_BOT_TOKEN": "token-191p",
                "ROBOTICXS_TELEGRAM_OWNER_IDS": "111111111",
                "ROBOTICXS_TELEGRAM_DEV_MODE": "true",
            }
        )
    )


def test_191p_card_renderer_allows_only_approved_states():
    rendered = render_telegram_ux_card(
        TelegramUxCard(
            title="Pilot",
            state="ready",
            primary_action="/pilot",
            summary="Run the controlled pilot flow.",
        )
    )

    assert "State: ready" in rendered
    with pytest.raises(ValueError, match="rejected_unknown_telegram_ux_state"):
        TelegramUxCard(title="Bad", state="online", primary_action="/bad", summary="Bad state.")


def test_191p_home_sections_cover_product_intents():
    rendered = "\n".join(render_telegram_ux_sections(build_premium_telegram_home_sections()))

    for intent in PRODUCT_INTENTS:
        assert intent in rendered
    assert "/pilot" in rendered
    assert "State: approval-required" in rendered
    assert "State: draft-only" in rendered


def test_191p_start_help_and_status_use_grouped_shell_not_flat_command_dump():
    config = build_valid_config()
    start = render_start_command_reply(config)
    help_text = render_help_command_reply()
    status = render_status_command_reply(config)

    assert "Premium control shell" in start
    assert "Command Center" in start
    assert "Work Queue" in start
    assert "Controls" in start
    assert "Roboticxs Command Center" in help_text
    assert "Daily Flow" in help_text
    assert "Review Flow" in help_text
    assert "Control Flow" in help_text
    assert "Runtime" in status
    assert "Sources" in status
    assert "Safety" in status
    assert "Premium Telegram UX Shell: active" in status
    assert "Today: /today, /miss, /daily_brief, /demo, /pilot" not in start


def test_191p_status_and_startup_do_not_claim_forbidden_authority():
    config = build_valid_config()
    text = "\n".join(
        [
            render_status_command_reply(config),
            build_telegram_robot_startup_report(config),
            "\n".join(render_premium_shell_boundaries()),
        ]
    )

    forbidden_claims = (
        "Gmail send: enabled",
        "Calendar writes: enabled",
        "Gmail modify/archive/label/delete: enabled",
        "Automatic Memory Center mutation: enabled",
        "External irreversible actions: enabled",
        "Autonomous execution: enabled",
    )
    for claim in forbidden_claims:
        assert claim not in text
    assert "Gmail send: disabled" in text
    assert "Calendar writes: disabled" in text


def test_191p_reference_and_roadmap_close_shell_without_execution_changes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "191P upgrades the Telegram product shell" in reference
    assert "It does not change command execution behavior." in reference
    assert '"stage_id":"191P","stage_name":"Premium Telegram UX Shell v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "199P and later remain unauthorized" in roadmap
