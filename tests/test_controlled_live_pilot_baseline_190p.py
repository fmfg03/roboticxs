from __future__ import annotations

from pathlib import Path

from app.controlled_live_pilot_baseline import (
    CONTROLLED_LIVE_PILOT_BASELINE_STAGE,
    CONTROLLED_LIVE_PILOT_STATUS,
    FixtureGmailDraftHttpClient,
    build_controlled_live_pilot_baseline,
    render_controlled_live_pilot_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CONTROLLED_LIVE_PILOT_BASELINE_190P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_190p_fixture_happy_path_builds_complete_controlled_pilot_receipt():
    receipt = build_controlled_live_pilot_baseline(owner_id="owner-190p", robot_id="robot-190p")

    assert receipt.stage == CONTROLLED_LIVE_PILOT_BASELINE_STAGE
    assert receipt.status == CONTROLLED_LIVE_PILOT_STATUS
    assert receipt.mode == "fixture"
    assert [step.name for step in receipt.steps] == [
        "Daily brief",
        "Meeting prep",
        "Suggestion",
        "Draft intent",
        "Draft queue",
        "Approval",
        "Gmail draft",
        "Source receipt",
        "Usage receipt",
    ]
    assert receipt.suggestion_inbox.items
    assert receipt.draft_queue.drafts
    assert receipt.confirmation.confirmation_status == "approved_pending_export_local_receipt"
    assert receipt.gmail_draft_creation.gmail_draft_created is True
    assert receipt.gmail_draft_creation.draft_id == "draft-190p-fixture"
    assert receipt.source_receipt_created is True
    assert receipt.usage_receipt_created is True


def test_190p_live_capable_mode_uses_injected_gmail_draft_client_without_send_authority():
    client = FixtureGmailDraftHttpClient()

    receipt = build_controlled_live_pilot_baseline(
        owner_id="owner-190p",
        robot_id="robot-190p",
        gmail_draft_http_client=client,
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "live-token-redacted"},
    )

    assert receipt.mode == "live_capable"
    assert receipt.gmail_draft_created is True
    assert len(client.calls) == 1
    assert receipt.gmail_send_allowed is False
    assert receipt.gmail_modify_allowed is False
    assert receipt.gmail_delete_allowed is False
    assert receipt.calendar_write_allowed is False
    assert receipt.external_write_allowed is False


def test_190p_source_and_usage_receipts_show_used_and_missing_sources():
    receipt = build_controlled_live_pilot_baseline(owner_id="owner-190p", robot_id="robot-190p")
    rendered = render_controlled_live_pilot_receipt(receipt)

    assert "Source Trace Receipt" in rendered
    assert "- Calendar: used" in rendered
    assert "- Gmail: used" in rendered
    assert "- Memory: used" in rendered
    assert "- Documents: not_connected" in rendered
    assert "Usage & Cost Ledger" in rendered
    assert "Tasks run: 3" in rendered
    assert "Estimated cost" in rendered


def test_190p_renderer_is_secret_free_and_states_no_irreversible_action():
    receipt = build_controlled_live_pilot_baseline(
        owner_id="owner-190p",
        robot_id="robot-190p",
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "super-secret-token-190p"},
    )

    rendered = render_controlled_live_pilot_receipt(receipt)

    assert "super-secret-token-190p" not in rendered
    assert "No email was sent." in rendered
    assert "No external irreversible action was taken." in rendered
    assert "Gmail send: disabled" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "OAuth flow/token refresh: disabled" in rendered


def test_190p_reference_and_roadmap_close_pilot_without_new_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "190P adds an owner-requested controlled pilot receipt" in reference
    assert "Gmail send" in reference
    assert "no fast path cache" in reference
    assert '"stage_id":"190P","stage_name":"Controlled Live Pilot Baseline v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "223P and later remain unauthorized" in roadmap
