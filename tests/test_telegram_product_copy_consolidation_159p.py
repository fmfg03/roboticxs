from __future__ import annotations

from pathlib import Path

from app.runnable_telegram_robot_mvp import (
    NO_ACTION_TAKEN_LINE,
    PRODUCT_APPROVAL_BOUNDARY_LINES,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
    render_unknown_command_reply,
)
from app.telegram_document_intake_stub import (
    build_telegram_document_intake_stub_record,
    render_telegram_document_intake_stub,
    TelegramDocumentIntakeMetadata,
)
from tests.test_telegram_product_shell_150p import valid_config


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/TELEGRAM_PRODUCT_COPY_CONSOLIDATION_159P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_159p_shared_approval_boundaries_appear_on_main_product_surfaces():
    surfaces = (
        render_start_command_reply(valid_config()),
        render_help_command_reply(),
        render_status_command_reply(valid_config()),
    )

    for reply in surfaces:
        assert "Approval boundaries:" in reply
        for line in PRODUCT_APPROVAL_BOUNDARY_LINES:
            assert line in reply
    assert all(NO_ACTION_TAKEN_LINE in reply for reply in surfaces[:2])


def test_159p_unknown_command_uses_product_areas_and_no_external_action_copy():
    reply = render_unknown_command_reply()

    assert "Available areas:" in reply
    assert "Documents: send a file for draft-only intake" in reply
    assert NO_ACTION_TAKEN_LINE in reply
    assert "Stage:" not in reply


def test_159p_document_copy_is_metadata_only_and_draft_only():
    record = build_telegram_document_intake_stub_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document=TelegramDocumentIntakeMetadata(
            file_id="copy-159p-file",
            file_unique_id=None,
            file_name="contract.pdf",
            mime_type="application/pdf",
            file_size=None,
        ),
    )
    reply = render_telegram_document_intake_stub(record)

    assert "Document review is currently draft-only." in reply
    assert "I received Telegram metadata only." in reply
    assert "External writes: disabled" in reply


def test_159p_reference_and_roadmap_close_copy_consolidation_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "159P is copy consolidation only." in reference
    assert "does not add commands" in reference
    assert "Memory Center mutation" in reference
    assert '"stage_id":"159P","stage_name":"Telegram Product Copy Consolidation v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "194P and later remain unauthorized" in roadmap
