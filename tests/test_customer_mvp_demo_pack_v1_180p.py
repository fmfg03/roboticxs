from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.customer_mvp_demo_pack_v1 import (
    CUSTOMER_MVP_DEMO_PACK_V1_STAGE,
    CUSTOMER_MVP_DEMO_PACK_V1_STATUS,
    CustomerMvpDemoPackV1,
    CustomerMvpDemoPackV1Step,
    build_customer_mvp_demo_pack_v1,
    render_customer_mvp_demo_pack_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CUSTOMER_MVP_DEMO_PACK_V1_180P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_180p_builds_deterministic_customer_mvp_demo_pack():
    pack = build_customer_mvp_demo_pack_v1()

    assert pack.stage == CUSTOMER_MVP_DEMO_PACK_V1_STAGE
    assert pack.status == CUSTOMER_MVP_DEMO_PACK_V1_STATUS
    assert pack.local_only is True
    assert pack.deterministic is True
    assert tuple(step.command.split()[0] for step in pack.steps) == (
        "/start",
        "/status",
        "/today",
        "/prep",
        "/suggestions",
        "/suggestion_draft",
        "/drafts",
        "/draft_approve",
        "/export_text",
    )
    assert pack.telegram_api_called is False
    assert pack.connector_activation_allowed is False
    assert pack.external_write_allowed is False
    assert pack.memory_center_mutated is False
    assert pack.model_call_allowed is False
    assert pack.tool_call_allowed is False
    assert pack.worker_dispatch_allowed is False


def test_180p_demo_steps_cover_product_loop_outputs():
    pack = build_customer_mvp_demo_pack_v1()
    demo_text = "\n\n".join(step.reply_text for step in pack.steps)

    assert "Today" in demo_text
    assert "Meeting Prep Pack" in demo_text
    assert "Suggestion Inbox" in demo_text
    assert "Suggestion Decision" in demo_text
    assert "Action Draft Queue" in demo_text
    assert "User Confirmation Receipt" in demo_text
    assert "Approved Output Export" in demo_text
    assert "Status: local_export_payload_created" in demo_text
    assert "No external action was taken." in demo_text


def test_180p_render_declares_demo_path_and_boundaries():
    rendered = render_customer_mvp_demo_pack_v1(build_customer_mvp_demo_pack_v1())

    assert "Customer MVP Demo Pack v1" in rendered
    assert "Stage: 180P" in rendered
    assert "Status: completed_local_customer_mvp_demo_v1" in rendered
    assert "/export_text" in rendered
    assert "Loop proven:" in rendered
    assert "Telegram API called: false" in rendered
    assert "External writes: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "No external action was taken." in rendered


def test_180p_rejects_authority_expansion():
    pack = build_customer_mvp_demo_pack_v1()
    step = pack.steps[0]

    with pytest.raises(ValueError, match="must not expand authority"):
        CustomerMvpDemoPackV1Step(**{**asdict(step), "external_write_allowed": True})
    with pytest.raises(ValueError, match="must not expand authority"):
        CustomerMvpDemoPackV1(**{**asdict(pack), "external_write_allowed": True})


def test_180p_reference_and_roadmap_close_customer_demo_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "180P is Customer MVP Demo Pack v1 only." in reference
    assert "Demo status is `completed_local_customer_mvp_demo_v1`" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"180P","stage_name":"Customer MVP Demo Pack v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "209P and later remain unauthorized" in roadmap
