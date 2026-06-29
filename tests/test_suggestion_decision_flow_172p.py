from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.proactive_suggestion_loop import (
    ProactiveSuggestionSignal,
    build_proactive_suggestion_loop_records,
)
from app.suggestion_decision_flow import (
    DECISION_STATUS_MISSING_SUGGESTION_ID,
    DECISION_STATUS_RECORDED,
    DECISION_STATUS_SUGGESTION_NOT_FOUND,
    SUGGESTION_DECISION_FLOW_STAGE,
    SuggestionDecisionReceipt,
    build_suggestion_decision_receipt,
    render_suggestion_decision_receipt,
)
from app.suggestion_inbox import build_suggestion_inbox


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SUGGESTION_DECISION_FLOW_172P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def inbox():
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-1",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="meeting_related_document",
                title="Prepare Victor meeting",
                summary="calendar event and PDF are available",
                source_refs=("calendar:evt-1", "document:doc-1"),
            ),
        ),
    )
    return build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=suggestions,
    )


@pytest.mark.parametrize(
    "choice",
    ["dismiss", "snooze", "save_memory", "create_draft", "ask_followup"],
)
def test_172p_records_supported_suggestion_decisions_without_execution(choice: str):
    local_inbox = inbox()
    record = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=local_inbox.items[0].suggestion_id,
        choice=choice,
        inbox=local_inbox,
    )

    assert record.stage == SUGGESTION_DECISION_FLOW_STAGE
    assert record.choice == choice
    assert record.decision_status == DECISION_STATUS_RECORDED
    assert record.suggestion_title == "Prepare Victor meeting"
    assert record.local_receipt_created is True
    assert record.owner_requested is True
    assert record.no_action_taken is True
    assert record.draft_created is False
    assert record.memory_written is False
    assert record.snooze_scheduled is False
    assert record.followup_question_sent is False
    assert record.callback_bound is False
    assert record.live_send_allowed is False
    assert record.execution_allowed is False
    assert record.connector_activation_allowed is False
    assert record.model_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False


def test_172p_blocks_missing_or_unknown_suggestion_id_as_local_receipt():
    local_inbox = inbox()

    missing = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="",
        choice="dismiss",
        inbox=local_inbox,
    )
    unknown = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id="missing-suggestion",
        choice="dismiss",
        inbox=local_inbox,
    )

    assert missing.decision_status == DECISION_STATUS_MISSING_SUGGESTION_ID
    assert unknown.decision_status == DECISION_STATUS_SUGGESTION_NOT_FOUND
    assert missing.no_action_taken is True
    assert unknown.no_action_taken is True


def test_172p_rejects_owner_robot_mismatch_and_invalid_choice():
    local_inbox = inbox()

    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_suggestion_decision_receipt(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            suggestion_id=local_inbox.items[0].suggestion_id,
            choice="dismiss",
            inbox=local_inbox,
        )
    with pytest.raises(ValueError, match="invalid_suggestion_decision_choice"):
        build_suggestion_decision_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            suggestion_id=local_inbox.items[0].suggestion_id,
            choice="send_email",
            inbox=local_inbox,
        )


def test_172p_render_declares_receipt_and_boundaries():
    local_inbox = inbox()
    rendered = render_suggestion_decision_receipt(
        build_suggestion_decision_receipt(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            suggestion_id=local_inbox.items[0].suggestion_id,
            choice="create_draft",
            inbox=local_inbox,
        )
    )

    assert "Suggestion Decision" in rendered
    assert "Stage: 172P" in rendered
    assert "Choice: create_draft" in rendered
    assert "Status: recorded_local_receipt" in rendered
    assert "No action has been taken." in rendered
    assert "Draft created: false" in rendered
    assert "Memory written: false" in rendered
    assert "Snooze scheduled: false" in rendered
    assert "External writes: disabled" in rendered


def test_172p_rejects_authority_expansion():
    local_inbox = inbox()
    valid = build_suggestion_decision_receipt(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_id=local_inbox.items[0].suggestion_id,
        choice="ask_followup",
        inbox=local_inbox,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        SuggestionDecisionReceipt(**{**asdict(valid), "external_write_allowed": True})


def test_172p_reference_and_roadmap_close_decision_flow_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "172P is Suggestion Decision Flow v0 only." in reference
    assert "No action has been taken" in reference
    assert "does not authorize drafts, memory writes, scheduler snoozes" in reference
    assert '"stage_id":"172P","stage_name":"Suggestion Decision Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "194P and later remain unauthorized" in roadmap
