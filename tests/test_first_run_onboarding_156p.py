from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import render_start_command_reply
from tests.test_telegram_product_shell_150p import valid_config


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FIRST_RUN_ONBOARDING_156P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_156p_start_is_first_run_onboarding_not_a_tutorial_or_secret_leak():
    reply = render_start_command_reply(valid_config())

    assert reply.startswith("Roboticxs\n\nWelcome. Your private robot is online.")
    assert "What I can do now:" in reply
    assert "What needs setup:" in reply
    assert "Approval boundaries:" in reply
    assert "Choose first useful action:" in reply
    assert "- /today for your daily view" in reply
    assert "- /prep <suggestion_id> for meeting prep" in reply
    assert "- /status for setup and capability status" in reply
    assert "Calendar reads need read-only Google setup." in reply
    assert "Gmail is not connected to the task inbox yet." in reply
    assert "I do not remember new facts without approval." in reply
    assert "secret-bot-token-150p" not in reply
    assert "tutorial" not in reply.lower()


def test_156p_reference_and_roadmap_close_first_run_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "156P is reply-copy and command-surface orientation only." in reference
    assert "does not add new commands" in reference
    assert "connector activation" in reference
    assert '"stage_id":"156P","stage_name":"First-Run Onboarding v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "177P and later remain unauthorized" in roadmap
