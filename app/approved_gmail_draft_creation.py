from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
from email.message import EmailMessage
import json
import os
from typing import Protocol
from urllib.request import Request, urlopen

from app.google_oauth_workspace import resolve_google_workspace_access_token
from app.user_confirmation_runtime import (
    CONFIRMATION_STATUS_APPROVED,
    USER_CONFIRMATION_RUNTIME_STAGE,
    UserConfirmationReceipt,
)


APPROVED_GMAIL_DRAFT_CREATION_STAGE = "185P"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED = "gmail_draft_created"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID = "blocked_missing_confirmation_id"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND = "blocked_confirmation_not_found"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED = "blocked_confirmation_not_approved"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED = "blocked_gmail_not_connected"
APPROVED_GMAIL_DRAFT_CREATION_STATUS_FAILED_CLOSED = "blocked_gmail_draft_failed_closed"
APPROVED_GMAIL_DRAFT_CREATION_STATUSES = frozenset(
    {
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED,
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID,
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND,
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED,
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED,
        APPROVED_GMAIL_DRAFT_CREATION_STATUS_FAILED_CLOSED,
    }
)
GMAIL_DRAFTS_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
DEFAULT_TO_HEADER = "draft-review@example.invalid"
DEFAULT_TIMEOUT_SECONDS = 30


class GmailDraftHttpClientProtocol(Protocol):
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: dict,
        timeout_seconds: int,
    ) -> dict:
        ...


class UrllibGmailDraftHttpClient:
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: dict,
        timeout_seconds: int,
    ) -> dict:
        request = Request(
            url,
            data=json.dumps(body, sort_keys=True).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True, slots=True)
class GmailDraftCreationConfig:
    access_token: str
    timeout_seconds: int
    to_header: str


@dataclass(frozen=True, slots=True)
class ApprovedGmailDraftCreationRecord:
    stage: str
    owner_id: str
    robot_id: str
    confirmation_id: str
    source_stage: str
    status: str
    subject: str
    body_preview: str
    draft_id: str | None
    gmail_message_id: str | None
    error_code: str | None
    owner_requested: bool
    gmail_draft_created: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    calendar_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != APPROVED_GMAIL_DRAFT_CREATION_STAGE:
            raise ValueError("185P Gmail draft creation records must identify the 185P stage.")
        if self.source_stage != USER_CONFIRMATION_RUNTIME_STAGE:
            raise ValueError("185P Gmail draft creation must originate from 178P confirmations.")
        if self.status not in APPROVED_GMAIL_DRAFT_CREATION_STATUSES:
            raise ValueError("185P Gmail draft creation status must be supported.")
        if not self.owner_requested:
            raise ValueError("185P Gmail draft creation requires owner request.")
        if self.gmail_draft_created != (self.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED):
            raise ValueError("185P Gmail draft created flag must match status.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.calendar_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("185P Gmail draft creation must not expand authority.")


def load_gmail_draft_creation_config(env: dict[str, str] | None = None) -> GmailDraftCreationConfig:
    source = os.environ if env is None else env
    access_token = source.get("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", "").strip()
    if not access_token:
        access_token = resolve_google_workspace_access_token(env=source)
    return GmailDraftCreationConfig(
        access_token=access_token,
        timeout_seconds=int(source.get("ROBOTICXS_GMAIL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        to_header=source.get("ROBOTICXS_GMAIL_DRAFT_TO", DEFAULT_TO_HEADER).strip() or DEFAULT_TO_HEADER,
    )


def build_approved_gmail_draft_creation(
    *,
    owner_id: str,
    robot_id: str,
    confirmation_id: str,
    confirmations: tuple[UserConfirmationReceipt, ...] = (),
    env: dict[str, str] | None = None,
    http_client: GmailDraftHttpClientProtocol | None = None,
) -> ApprovedGmailDraftCreationRecord:
    normalized_confirmation_id = confirmation_id.strip()
    for receipt in confirmations:
        if receipt.owner_id != owner_id or receipt.robot_id != robot_id:
            raise ValueError("rejected_gmail_draft_creation_owner_robot_mismatch")
    if not normalized_confirmation_id:
        return _record(owner_id=owner_id, robot_id=robot_id, confirmation_id="", status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID)
    receipt = next((item for item in confirmations if item.confirmation_id == normalized_confirmation_id), None)
    if receipt is None:
        return _record(owner_id=owner_id, robot_id=robot_id, confirmation_id=normalized_confirmation_id, status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND)
    if receipt.confirmation_status != CONFIRMATION_STATUS_APPROVED:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED,
            receipt=receipt,
        )
    config = load_gmail_draft_creation_config(env=env)
    if not config.access_token:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED,
            receipt=receipt,
            error_code="missing_access_token",
        )
    if config.timeout_seconds <= 0:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_FAILED_CLOSED,
            receipt=receipt,
            error_code="rejected_invalid_timeout_seconds",
        )
    client = http_client or UrllibGmailDraftHttpClient()
    try:
        payload = client.post_json(
            GMAIL_DRAFTS_ENDPOINT,
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Accept": "application/json",
            },
            body={"message": {"raw": _raw_message(receipt=receipt, to_header=config.to_header)}},
            timeout_seconds=config.timeout_seconds,
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_FAILED_CLOSED,
            receipt=receipt,
            error_code="gmail_draft_create_failed_closed",
        )
    draft_id = payload.get("id")
    message = payload.get("message")
    message_id = message.get("id") if isinstance(message, dict) else None
    if not isinstance(draft_id, str) or not draft_id.strip():
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_FAILED_CLOSED,
            receipt=receipt,
            error_code="missing_draft_id",
        )
    return _record(
        owner_id=owner_id,
        robot_id=robot_id,
        confirmation_id=normalized_confirmation_id,
        status=APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED,
        receipt=receipt,
        draft_id=draft_id.strip(),
        gmail_message_id=message_id.strip() if isinstance(message_id, str) and message_id.strip() else None,
    )


def render_approved_gmail_draft_creation(record: ApprovedGmailDraftCreationRecord) -> str:
    lines = [
        "Approved Gmail Draft Creation",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Confirmation id: {record.confirmation_id or 'none'}",
        f"Gmail draft id: {record.draft_id or 'none'}",
        f"Gmail message id: {record.gmail_message_id or 'none'}",
        f"Subject: {record.subject or 'not available'}",
        "",
        "Body preview:",
        f"- {record.body_preview or 'No Gmail draft was created.'}",
    ]
    if record.error_code:
        lines.extend(["", f"Reason: {record.error_code}", "Next: run /checkup"])
    lines.extend(
        [
            "",
            "Meaning:",
            *_meaning_lines(record),
            "",
            "Boundaries:",
            f"Gmail draft created: {'true' if record.gmail_draft_created else 'false'}",
            "Gmail send: disabled",
            "Gmail modify/archive/label: disabled",
            "Gmail delete: disabled",
            "Calendar writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No email was sent.",
        ]
    )
    return "\n".join(lines)


def _meaning_lines(record: ApprovedGmailDraftCreationRecord) -> tuple[str, ...]:
    if record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED:
        return ("- A Gmail draft was created after explicit owner confirmation.", "- Review and send manually in Gmail.")
    if record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_MISSING_CONFIRMATION_ID:
        return ("- No confirmation id was provided.", "- Approve a local draft before creating a Gmail draft.")
    if record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CONFIRMATION_NOT_FOUND:
        return ("- That confirmation is not available in the current local context.", "- No Gmail draft was created.")
    if record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_NOT_APPROVED:
        return ("- That confirmation is not approved.", "- No Gmail draft was created.")
    if record.status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_GMAIL_NOT_CONNECTED:
        return ("- Gmail draft creation is not connected.", "- Configure Gmail and rerun /checkup.")
    return ("- Gmail draft creation failed closed.", "- No email was sent or modified.")


def _record(
    *,
    owner_id: str,
    robot_id: str,
    confirmation_id: str,
    status: str,
    receipt: UserConfirmationReceipt | None = None,
    draft_id: str | None = None,
    gmail_message_id: str | None = None,
    error_code: str | None = None,
) -> ApprovedGmailDraftCreationRecord:
    return ApprovedGmailDraftCreationRecord(
        stage=APPROVED_GMAIL_DRAFT_CREATION_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        confirmation_id=confirmation_id,
        source_stage=USER_CONFIRMATION_RUNTIME_STAGE,
        status=status,
        subject=_subject(receipt),
        body_preview=_body_preview(receipt),
        draft_id=draft_id,
        gmail_message_id=gmail_message_id,
        error_code=error_code,
        owner_requested=True,
        gmail_draft_created=status == APPROVED_GMAIL_DRAFT_CREATION_STATUS_CREATED,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _raw_message(*, receipt: UserConfirmationReceipt, to_header: str) -> str:
    message = EmailMessage()
    message["To"] = to_header
    message["Subject"] = _subject(receipt)
    message.set_content(_body(receipt))
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")


def _subject(receipt: UserConfirmationReceipt | None) -> str:
    if receipt is None or not receipt.draft_title:
        return ""
    return _bounded(f"Roboticxs draft: {receipt.draft_title}", 120)


def _body(receipt: UserConfirmationReceipt) -> str:
    return "\n".join(
        [
            f"Approved local draft: {receipt.draft_title}",
            "",
            "This Gmail draft was created after explicit Roboticxs owner confirmation.",
            f"Source confirmation: {receipt.confirmation_id}",
            "",
            "Review before sending. Roboticxs did not send this email.",
        ]
    )


def _body_preview(receipt: UserConfirmationReceipt | None) -> str:
    if receipt is None:
        return ""
    return _bounded(_body(receipt), 240)


def _bounded(value: str, limit: int) -> str:
    return " ".join(value.split())[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.approved_gmail_draft_creation")
    parser.add_argument("confirmation_id", nargs="?", default="")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = build_approved_gmail_draft_creation(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        confirmation_id=args.confirmation_id,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_approved_gmail_draft_creation(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
