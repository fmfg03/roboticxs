from __future__ import annotations

from pathlib import Path

from app.inbox_item_decision import build_inbox_item_decision, render_inbox_item_decision
from app.open_loops_command import build_open_loops_command_record
from app.personal_admin_inbox import build_personal_admin_inbox_record, render_personal_admin_inbox
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)
from tests.test_open_loops_command_142p import PendingProposalFixture, suggestion_scan


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/TASK_INBOX_FLOW_154P_v0_1.md"


def inbox_record(*, pending_memory: bool = True, suggestions: bool = True):
    pending = (PendingProposalFixture(),) if pending_memory else ()
    scan = suggestion_scan() if suggestions else suggestion_scan(ok=False, error_code="missing_access_token")
    open_loops = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=scan,
        memory_snapshot=build_memory_center_telegram_snapshot(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            source_bundle=TelegramMemoryCenterSourceBundle(
                pending_memory_proposals=pending,
            ),
        ),
    )
    return build_personal_admin_inbox_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        open_loops_record=open_loops,
    )


def test_154p_task_inbox_renders_customer_states_and_boundaries():
    rendered = render_personal_admin_inbox(inbox_record())

    assert rendered.startswith("Task Inbox\n")
    assert "Stage: 146P" not in rendered
    assert "Inbox type:" in rendered
    assert "Robot task inbox, not Gmail." in rendered
    assert "States:" in rendered
    assert "pending:" in rendered
    assert "done:" in rendered
    assert "dismissed:" in rendered
    assert "needs approval:" in rendered
    assert "blocked:" in rendered
    assert "Items:" in rendered
    assert "needs approval | pending-memory:" in rendered
    assert "Suggested next action:" in rendered
    assert "/inbox_done <item_id>" in rendered
    assert "/inbox_dismiss <item_id>" in rendered
    assert "Gmail inbox: unavailable" in rendered
    assert "Gmail writes: disabled" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Model calls: disabled" in rendered
    assert "No inbox item was resolved or dismissed." in rendered


def test_154p_task_inbox_empty_state_is_useful():
    rendered = render_personal_admin_inbox(inbox_record(pending_memory=False, suggestions=False))

    assert "Status: empty" in rendered
    assert "Empty: no robot task inbox items are visible right now." in rendered
    assert "Use /today to see the current daily view." in rendered
    assert "Gmail inbox: unavailable" in rendered


def test_154p_done_and_dismiss_receipts_are_local_only():
    done = render_inbox_item_decision(
        build_inbox_item_decision(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            item_id="pending-memory:proposal-1",
            choice="done",
        )
    )
    dismissed = render_inbox_item_decision(
        build_inbox_item_decision(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            item_id="meeting-suggestion:abc",
            choice="dismiss",
        )
    )

    assert done.startswith("Task Inbox Decision\n")
    assert "Status: done" in done
    assert "Receipt status: marked_done_local_receipt" in done
    assert "Status: dismissed" in dismissed
    assert "Receipt status: dismissed_local_receipt" in dismissed
    for rendered in (done, dismissed):
        assert "Stage: 147P" not in rendered
        assert "local receipt for the robot task inbox" in rendered
        assert "Evidence deleted: false" in rendered
        assert "Persisted state written: false" in rendered
        assert "Gmail inbox: unavailable" in rendered
        assert "Gmail writes: disabled" in rendered
        assert "Memory Center mutation: disabled" in rendered
        assert "Model calls: disabled" in rendered
        assert "No inbox evidence was deleted." in rendered


def test_154p_reference_and_roadmap_close_task_inbox_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "154P is a customer-facing Telegram Task Inbox stage." in reference
    assert "does not add new commands" in reference
    assert "persist inbox state" in reference
    assert "The customer-facing name is `Task Inbox`." in reference
    assert '"stage_id":"154P","stage_name":"Task Inbox Flow v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "159P and later remain unauthorized" in roadmap
