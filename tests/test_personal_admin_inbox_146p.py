from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.open_loops_command import build_open_loops_command_record
from app.personal_admin_inbox import (
    PERSONAL_ADMIN_INBOX_STAGE,
    PersonalAdminInboxRecord,
    build_personal_admin_inbox_record,
    render_personal_admin_inbox,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)
from tests.test_open_loops_command_142p import PendingProposalFixture, suggestion_scan


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def open_loops_record():
    return build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(),
        memory_snapshot=build_memory_center_telegram_snapshot(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            source_bundle=TelegramMemoryCenterSourceBundle(
                pending_memory_proposals=(PendingProposalFixture(),),
            ),
        ),
    )


def test_146p_builds_read_only_personal_admin_inbox():
    record = build_personal_admin_inbox_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        open_loops_record=open_loops_record(),
    )

    assert record.stage == PERSONAL_ADMIN_INBOX_STAGE
    assert record.status == "completed_with_items"
    assert record.source_stages == ("142P", "144P", "145P")
    assert any(item.startswith("pending-memory:") for item in record.inbox_items)
    assert record.inbox_items
    assert record.read_only is True
    assert record.item_resolution_allowed is False
    assert record.memory_center_mutated is False
    assert record.external_write_allowed is False


def test_146p_render_names_disabled_resolution_and_writes():
    rendered = render_personal_admin_inbox(
        build_personal_admin_inbox_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            open_loops_record=open_loops_record(),
        )
    )

    assert "Task Inbox" in rendered
    assert "Stage: 146P" not in rendered
    assert "States:" in rendered
    assert "needs approval | pending-memory:" in rendered
    assert "Robot task inbox, not Gmail." in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "No inbox item was resolved or dismissed." in rendered


def test_146p_record_rejects_authority_expansion():
    valid = build_personal_admin_inbox_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        open_loops_record=open_loops_record(),
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        PersonalAdminInboxRecord(**{**asdict(valid), "item_resolution_allowed": True})


def test_146p_roadmap_records_inbox_and_blocks_147p_plus():
    roadmap = ROADMAP_PATH.read_text()

    assert '"stage_id":"146P","stage_name":"Personal Admin Inbox v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "193P and later remain unauthorized" in roadmap
