from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.action_draft_queue import build_action_draft_queue
from app.approved_gmail_draft_creation import (
    APPROVED_GMAIL_DRAFT_CREATION_STAGE,
    APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND,
    APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED,
    APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED,
    APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID,
    APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED,
    ApprovedGmailDraftCreationRecord,
    build_approved_gmail_draft_creation,
    render_approved_gmail_draft_creation,
)
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.suggestion_decision_flow import build_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox
from app.user_confirmation_runtime import build_user_confirmation_receipt


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/APPROVED_GMAIL_DRAFT_CREATION_185P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


class FakeGmailDraftHttpClient:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {"id": "draft-185p", "message": {"id": "msg-185p"}}
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: dict,
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.payload


def confirmation(choice: str = "approve"):
    suggestions = build_proactive_suggestion_loop_records(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-185p",
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                trigger_type="email_thread_no_followup",
                title="Draft Gmail follow-up",
                summary="thread needs follow-up",
                source_refs=("gmail:thread-185p",),
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


def test_185p_approved_confirmation_creates_gmail_draft_only():
    approved = confirmation()
    client = FakeGmailDraftHttpClient()
    record = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=approved.confirmation_id,
        confirmations=(approved,),
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "gmail-token-185p"},
        http_client=client,
    )
    rendered = render_approved_gmail_draft_creation(record)

    assert record.stage == APPROVED_GMAIL_DRAFT_CREATION_STAGE
    assert record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED
    assert record.draft_id == "draft-185p"
    assert record.gmail_message_id == "msg-185p"
    assert record.gmail_draft_created is True
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.gmail_delete_allowed is False
    assert record.external_write_allowed is False
    assert len(client.calls) == 1
    assert client.calls[0]["url"].endswith("/drafts")
    assert "/send" not in str(client.calls)
    assert "/modify" not in str(client.calls)
    assert "/trash" not in str(client.calls)
    assert "Approved Gmail Draft Creation" in rendered
    assert "Gmail draft created: true" in rendered
    assert "Gmail send: disabled" in rendered
    assert "Gmail modify/archive/label: disabled" in rendered
    assert "Gmail delete: disabled" in rendered
    assert "No email was sent." in rendered


def test_185p_missing_gmail_token_fails_closed_with_checkup_guidance():
    approved = confirmation()
    client = FakeGmailDraftHttpClient()
    record = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=approved.confirmation_id,
        confirmations=(approved,),
        env={},
        http_client=client,
    )
    rendered = render_approved_gmail_draft_creation(record)

    assert record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED
    assert record.error_code == "missing_access_token"
    assert record.gmail_draft_created is False
    assert client.calls == []
    assert "Next: run /checkup" in rendered
    assert "No email was sent." in rendered


def test_185p_missing_unknown_and_not_approved_confirmations_are_blocked():
    rejected = confirmation("reject")

    missing = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id="",
        confirmations=(rejected,),
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "gmail-token-185p"},
        http_client=FakeGmailDraftHttpClient(),
    )
    unknown = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id="missing-confirmation",
        confirmations=(rejected,),
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "gmail-token-185p"},
        http_client=FakeGmailDraftHttpClient(),
    )
    not_approved = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=rejected.confirmation_id,
        confirmations=(rejected,),
        env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "gmail-token-185p"},
        http_client=FakeGmailDraftHttpClient(),
    )

    assert missing.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID
    assert unknown.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND
    assert not_approved.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED
    assert missing.gmail_draft_created is False
    assert unknown.gmail_draft_created is False
    assert not_approved.gmail_draft_created is False


def test_185p_rejects_owner_robot_mismatch_and_authority_expansion():
    approved = confirmation()

    with pytest.raises(ValueError, match="owner_robot_mismatch"):
        build_approved_gmail_draft_creation(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            confirmation_id=approved.confirmation_id,
            confirmations=(approved,),
        )
    valid = build_approved_gmail_draft_creation(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        confirmation_id=approved.confirmation_id,
        confirmations=(approved,),
        env={},
    )
    with pytest.raises(ValueError, match="must not expand authority"):
        ApprovedGmailDraftCreationRecord(**{**asdict(valid), "gmail_send_allowed": True})


def test_185p_receipt_excludes_secrets_and_auth_headers():
    approved = confirmation()
    rendered = render_approved_gmail_draft_creation(
        build_approved_gmail_draft_creation(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            confirmation_id=approved.confirmation_id,
            confirmations=(approved,),
            env={"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "gmail-token-185p"},
            http_client=FakeGmailDraftHttpClient(),
        )
    )

    for forbidden in ("gmail-token-185p", "Authorization", "Bearer", "refresh-token", "client-secret"):
        assert forbidden not in rendered


def test_185p_reference_and_roadmap_close_gmail_draft_creation_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "185P - Approved Gmail Draft Creation v0" in reference
    assert "185P is approved Gmail draft creation only." in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"185P","stage_name":"Approved Gmail Draft Creation v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "204P and later remain unauthorized" in roadmap
