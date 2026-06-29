from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.proactive_suggestion_loop import (
    ProactiveSuggestionLoopRecord,
    ProactiveSuggestionSignal,
    build_proactive_suggestion_loop_records,
)
from app.suggestion_inbox import (
    SUGGESTION_INBOX_STAGE,
    SuggestionInbox,
    SuggestionInboxItem,
    build_suggestion_inbox,
    render_suggestion_inbox,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/SUGGESTION_INBOX_171P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def suggestion(owner_id: str = "local-owner", robot_id: str = "roboticxs-dev") -> ProactiveSuggestionLoopRecord:
    return build_proactive_suggestion_loop_records(
        owner_id=owner_id,
        robot_id=robot_id,
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-1",
                owner_id=owner_id,
                robot_id=robot_id,
                trigger_type="meeting_related_document",
                title="Prepare Victor meeting",
                summary="calendar event and PDF are available",
                source_refs=("calendar:evt-1", "document:doc-1"),
            ),
        ),
    )[0]


def test_171p_builds_empty_local_suggestion_inbox():
    inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=(),
    )

    assert inbox.stage == SUGGESTION_INBOX_STAGE
    assert inbox.items == ()
    assert inbox.local_read_only is True
    assert inbox.no_action_taken is True
    assert inbox.decision_flow_allowed is False
    assert inbox.draft_creation_allowed is False
    assert inbox.memory_write_allowed is False
    assert inbox.external_write_allowed is False
    assert "No pending suggestions" in render_suggestion_inbox(inbox)


def test_171p_builds_pending_items_from_170p_suggestions():
    inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=(suggestion(),),
    )

    assert len(inbox.items) == 1
    item = inbox.items[0]
    assert item.stage == "171P"
    assert item.status == "pending"
    assert item.title == "Prepare Victor meeting"
    assert item.trigger_type == "meeting_related_document"
    assert item.suggested_next_step == "offer_prep_pack"
    assert item.source_refs == ("calendar:evt-1", "document:doc-1")
    assert item.no_action_taken is True
    assert item.live_send_allowed is False
    assert item.callback_binding_allowed is False
    assert item.execution_allowed is False
    assert item.memory_write_allowed is False
    assert item.draft_creation_allowed is False
    assert item.external_write_allowed is False
    assert item.connector_activation_allowed is False


def test_171p_filters_suggestions_by_owner_and_robot():
    inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=(
            suggestion(),
            suggestion(owner_id="other-owner"),
            suggestion(robot_id="other-robot"),
        ),
    )

    assert len(inbox.items) == 1
    assert inbox.items[0].owner_id == "local-owner"
    assert inbox.items[0].robot_id == "roboticxs-dev"


def test_171p_render_includes_boundaries_and_non_sensitive_sources():
    rendered = render_suggestion_inbox(
        build_suggestion_inbox(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            suggestions=(suggestion(),),
        )
    )

    assert "Suggestion Inbox" in rendered
    assert "Stage: 171P" in rendered
    assert "Status: 1 pending suggestion(s)" in rendered
    assert "trigger: meeting_related_document" in rendered
    assert "sources: calendar:evt-1, document:doc-1" in rendered
    assert "No action has been taken." in rendered
    assert "Decision flow: disabled" in rendered
    assert "Draft creation: disabled" in rendered
    assert "Memory writes: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_171p_rejects_authority_expansion():
    valid_item = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=(suggestion(),),
    ).items[0]

    with pytest.raises(ValueError, match="must not expand authority"):
        SuggestionInboxItem(**{**asdict(valid_item), "execution_allowed": True})

    valid_inbox = build_suggestion_inbox(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestions=(),
    )
    with pytest.raises(ValueError, match="must not authorize decisions"):
        SuggestionInbox(**{**asdict(valid_inbox), "decision_flow_allowed": True})


def test_171p_reference_and_roadmap_close_suggestion_inbox_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "171P is Suggestion Inbox v0 only." in reference
    assert "No action has been taken" in reference
    assert "does not authorize suggestion decisions" in reference
    assert '"stage_id":"171P","stage_name":"Suggestion Inbox v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "209P and later remain unauthorized" in roadmap
