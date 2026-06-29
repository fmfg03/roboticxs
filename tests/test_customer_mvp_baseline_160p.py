from __future__ import annotations

import json
from pathlib import Path

from app.customer_mvp_baseline import (
    CUSTOMER_MVP_BASELINE_STAGE,
    CUSTOMER_MVP_STATUS,
    build_customer_mvp_baseline_status,
    main,
    render_customer_mvp_baseline_status,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CUSTOMER_MVP_BASELINE_160P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_160p_customer_mvp_baseline_verifies_existing_product_surfaces_without_authority_expansion():
    status = build_customer_mvp_baseline_status()

    assert status.stage == CUSTOMER_MVP_BASELINE_STAGE
    assert status.status == CUSTOMER_MVP_STATUS
    assert status.demo_commands == (
        "/start",
        "/status",
        "/today",
        "/prep",
        "/memory_pending",
        "/inbox_done",
    )
    assert any(line.startswith("Today:") for line in status.product_menu_lines)
    assert any(line.startswith("Brief:") for line in status.product_menu_lines)
    assert any(line.startswith("Prep:") for line in status.product_menu_lines)
    assert any(line.startswith("Tasks:") for line in status.product_menu_lines)
    assert any(line.startswith("Memory:") for line in status.product_menu_lines)
    assert any(line.startswith("Documents:") for line in status.product_menu_lines)
    assert status.demo_deterministic is True
    assert status.setup_clear is True
    assert status.memory_review_clear is True
    assert status.task_inbox_functional is True
    assert status.meeting_prep_sellable is True
    assert status.document_intake_stub is True
    assert status.safety_language_visible is True
    assert status.no_secrets_included is True
    assert status.local_only is True
    assert status.telegram_api_called is False
    assert status.connector_activation_allowed is False
    assert status.external_write_allowed is False
    assert status.memory_center_mutated is False
    assert status.model_call_allowed is False
    assert status.tool_call_allowed is False
    assert status.worker_dispatch_allowed is False


def test_160p_customer_mvp_baseline_render_is_customer_demo_ready_and_boundary_labeled():
    rendered = render_customer_mvp_baseline_status(build_customer_mvp_baseline_status())

    assert rendered.startswith("Customer MVP Baseline\n")
    assert "Stage: 160P" in rendered
    assert "Status: customer_mvp_baseline_ready" in rendered
    assert "Demo loop:" in rendered
    assert "- /start, /status, /today, /prep, /memory_pending, /inbox_done" in rendered
    assert "- meeting prep sellable" in rendered
    assert "- document intake draft-only" in rendered
    assert "Connector activation: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_160p_customer_mvp_baseline_cli_json_output_is_structured(capsys):
    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["stage"] == "160P"
    assert payload["status"] == "customer_mvp_baseline_ready"
    assert payload["demo_deterministic"] is True
    assert payload["external_write_allowed"] is False


def test_160p_reference_and_roadmap_close_customer_mvp_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "160P is a local baseline contract only." in reference
    assert "does not add commands" in reference
    assert "Memory Center mutation" in reference
    assert '"stage_id":"160P","stage_name":"Customer MVP Baseline v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "203P and later remain unauthorized" in roadmap
