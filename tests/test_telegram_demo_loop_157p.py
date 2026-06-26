from __future__ import annotations

import json
from pathlib import Path

from app.telegram_demo_loop import (
    TELEGRAM_DEMO_LOOP_STAGE,
    build_telegram_demo_loop_transcript,
    main,
    render_telegram_demo_loop_transcript,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/TELEGRAM_DEMO_LOOP_157P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_157p_demo_loop_builds_customer_product_transcript_without_external_writes():
    transcript = build_telegram_demo_loop_transcript()

    assert transcript.stage == TELEGRAM_DEMO_LOOP_STAGE
    assert transcript.status == "completed_local_demo"
    assert transcript.local_only is True
    assert transcript.telegram_api_called is False
    assert transcript.connector_activation_allowed is False
    assert transcript.external_write_allowed is False
    assert transcript.memory_center_mutated is False
    assert transcript.model_call_allowed is False
    assert transcript.tool_call_allowed is False
    assert transcript.worker_dispatch_allowed is False
    assert [step.command.split()[0] for step in transcript.steps] == [
        "/start",
        "/status",
        "/today",
        "/prep",
        "/memory_pending",
        "/inbox_done",
    ]
    assert all(step.authorized for step in transcript.steps)
    assert all(not step.external_write_allowed for step in transcript.steps)
    assert "Welcome. Your private robot is online." in transcript.steps[0].reply_text
    assert "Setup Check" in transcript.steps[1].reply_text
    assert "Today" in transcript.steps[2].reply_text
    assert "Meeting Prep Pack" in transcript.steps[3].reply_text
    assert "Memory Review" in transcript.steps[4].reply_text
    assert "Task Inbox Decision" in transcript.steps[5].reply_text


def test_157p_demo_loop_render_is_short_deterministic_and_boundary_labeled():
    rendered = render_telegram_demo_loop_transcript(build_telegram_demo_loop_transcript())

    assert rendered.startswith("Telegram Demo Loop\n")
    assert "Stage: 157P" in rendered
    assert "Local-only: true" in rendered
    assert "Telegram API called: false" in rendered
    assert "1. /start - First-run onboarding" in rendered
    assert "4. /prep " in rendered
    assert "6. /inbox_done pending-memory:demo-proposal-157p" in rendered
    assert "Connector activation: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "No external action was taken." in rendered


def test_157p_cli_json_output_is_structured(capsys):
    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["stage"] == "157P"
    assert payload["telegram_api_called"] is False
    assert payload["steps"][0]["command"] == "/start"


def test_157p_reference_and_roadmap_close_demo_loop_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "local deterministic demo transcript" in reference
    assert "does not send Telegram messages" in reference
    assert "mutate Memory Center" in reference
    assert '"stage_id":"157P","stage_name":"Telegram Demo Loop v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "186P and later remain unauthorized" in roadmap
