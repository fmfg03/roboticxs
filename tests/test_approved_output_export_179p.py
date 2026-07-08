from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_draft_queue import build_action_draft_queue
from app.approved_output_export import (
    APPROVED_OUTPUT_EXPORT_STAGE,
    EXPORT_STATUS_CONFIRMATION_NOT_FOUND,
    EXPORT_STATUS_CREATED,
    EXPORT_STATUS_MISSING_CONFIRMATION_ID,
    EXPORT_STATUS_NOT_APPROVED,
    ApprovedOutputExportRecord,
    build_approved_output_export,
    render_approved_output_export,
)
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox
from app.user_confirmation_runtime import build_user_confirmation_receipt


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/APPROVED_OUTPUT_EXPORT_179P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def confirmation(choice: str = "approve"):
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-179p",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="email_thread_no_followup",
                title="Draft approved export",
                summary="thread needs follow-up",
                source_refs=("gmail:thread-179p",),
            ),
        ),
    )
    inbox = build_suggestion_inbox(owner_id="local-owner", robot_id="roboticxs-dev", suggestions=suggestions)
    decision = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=inbox.items[0].suggestion_id,
        choice="create_draft",
        inbox=inbox,
    )
    queue = build_action_draft_queue(owner_id="local-owner", robot_id="roboticxs-dev", decisions=(decision,))
    return build_user_confirmation_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        draft_id=queue.drafts[0].draft_id,
        choice=choice,
        queue=queue,
    )


@pytest.mark.parametrize("export_format", ["text", "email_draft", "local_file"])
def test_179p_creates_local_export_payload_from_approved_confirmation(export_format: str):
    approved = confirmation()
    record = build_approved_output_export(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=approved.confirmation_id,
        export_format=export_format,
        confirmations=(approved,),
    )

    assert record.stage == APPROVED_OUTPUT_EXPORT_STAGE
    assert record.export_status == EXPORT_STATUS_CREATED
    assert record.export_format == export_format
    assert record.title == "Draft for: Draft approved export"
    assert record.local_export_payload_created is True
    assert record.payload_preview
    assert record.gmail_draft_created is False
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.calendar_write_allowed is False
    assert record.local_file_written is False
    assert record.task_persisted is False
    assert record.memory_center_mutated is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False


def test_179p_blocks_missing_unknown_and_not_approved_confirmations():
    rejected = confirmation("reject")

    missing = build_approved_output_export(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id="",
        export_format="text",
    )
    unknown = build_approved_output_export(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id="missing-confirmation",
        export_format="text",
    )
    not_approved = build_approved_output_export(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=rejected.confirmation_id,
        export_format="text",
        confirmations=(rejected,),
    )

    assert missing.export_status == EXPORT_STATUS_MISSING_CONFIRMATION_ID
    assert unknown.export_status == EXPORT_STATUS_CONFIRMATION_NOT_FOUND
    assert not_approved.export_status == EXPORT_STATUS_NOT_APPROVED
    assert missing.local_export_payload_created is False
    assert unknown.local_export_payload_created is False
    assert not_approved.local_export_payload_created is False


def test_179p_rejects_invalid_format_owner_mismatch_and_authority_expansion():
    approved = confirmation()

    with pytest.raises(ValueError, match="invalid_approved_output_export_format"):
        build_approved_output_export(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            confirmation_id=approved.confirmation_id,
            export_format="gmail_send",
            confirmations=(approved,),
        )
    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_approved_output_export(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            confirmation_id=approved.confirmation_id,
            export_format="text",
            confirmations=(approved,),
        )
    valid = build_approved_output_export(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=approved.confirmation_id,
        export_format="text",
        confirmations=(approved,),
    )
    with pytest.raises(ValueError, match="must not expand authority"):
        ApprovedOutputExportRecord(**{**asdict(valid), "external_write_allowed": True})


def test_179p_render_declares_local_payload_and_boundaries():
    approved = confirmation()
    rendered = render_approved_output_export(
        build_approved_output_export(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            confirmation_id=approved.confirmation_id,
            export_format="email_draft",
            confirmations=(approved,),
        )
    )

    assert "Approved Output Export" in rendered
    assert "Stage: 179P" in rendered
    assert "Format: email_draft" in rendered
    assert "Status: local_export_payload_created" in rendered
    assert "Local export payload created: true" in rendered
    assert "Gmail draft creation: disabled" in rendered
    assert "Local file write: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No external action was taken." in rendered


def test_179p_reference_and_roadmap_close_approved_output_export_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "179P is Approved Output Export v0 only." in reference
    assert "Local file writes" in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"179P","stage_name":"Approved Output Export v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "224P and later remain unauthorized" in roadmap
