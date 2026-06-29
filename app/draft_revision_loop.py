from __future__ import annotations

from dataclasses import dataclass


DRAFT_REVISION_LOOP_STAGE = "208P"
DRAFT_REVISION_LOOP_STATUS = "local_draft_revision_request_v0"
SUPPORTED_DRAFT_REVISIONS = ("shorter", "more_direct", "warmer", "spanish", "add_context", "remove_claims")


@dataclass(frozen=True, slots=True)
class DraftRevisionReceipt:
    stage: str
    owner_id: str
    robot_id: str
    draft_id: str
    revision_request: str
    approval_state: str
    source_trace_id: str
    status: str
    revised_body_created: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != DRAFT_REVISION_LOOP_STAGE:
            raise ValueError("208P draft revisions must identify the 208P stage.")
        if self.status != DRAFT_REVISION_LOOP_STATUS:
            raise ValueError("208P draft revisions must use the revision status.")
        if not self.draft_id:
            raise ValueError("208P draft revisions require draft id.")
        if self.revision_request not in SUPPORTED_DRAFT_REVISIONS:
            raise ValueError("208P draft revision request is unsupported.")
        if self.approval_state not in {"pending_revision", "pending_approval"}:
            raise ValueError("208P draft revision approval state is unsupported.")
        if self.gmail_send_allowed or self.calendar_write_allowed or self.external_write_allowed:
            raise ValueError("208P draft revisions must not expand external write authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("208P draft revisions must be redacted and approval-preserving.")


def parse_draft_revision_argument(argument: str | None) -> tuple[str, str]:
    parts = (argument or "").strip().split(maxsplit=1)
    if len(parts) != 2:
        return "", ""
    return parts[0].strip(), parts[1].strip().lower()


def build_draft_revision_receipt(
    *,
    owner_id: str,
    robot_id: str,
    draft_id: str,
    revision_request: str,
    source_trace_id: str | None = None,
) -> DraftRevisionReceipt:
    return DraftRevisionReceipt(
        stage=DRAFT_REVISION_LOOP_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        draft_id=draft_id.strip(),
        revision_request=revision_request.strip().lower(),
        approval_state="pending_revision",
        source_trace_id=(source_trace_id or "source_trace_not_provided").strip() or "source_trace_not_provided",
        status=DRAFT_REVISION_LOOP_STATUS,
        revised_body_created=True,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_draft_revision_receipt(receipt: DraftRevisionReceipt) -> str:
    return "\n".join(
        [
            "Draft Revision Loop",
            "",
            f"Stage: {receipt.stage}",
            f"Status: {receipt.status}",
            f"Draft: {receipt.draft_id}",
            f"Revision: {receipt.revision_request}",
            f"Approval state: {receipt.approval_state}",
            f"Source trace: {receipt.source_trace_id}",
            "Revised body: local candidate created",
            "",
            "Next safe step:",
            f"- Review /drafts, then approve/export only if the revised {receipt.draft_id} is correct.",
            "",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )


def render_draft_revision_usage() -> str:
    return "\n".join(
        [
            "Draft Revision Loop",
            "",
            "Usage:",
            "- /draft_revise <draft_id> shorter",
            "- /draft_revise <draft_id> more_direct",
            "- /draft_revise <draft_id> warmer",
            "- /draft_revise <draft_id> spanish",
            "- /draft_revise <draft_id> add_context",
            "- /draft_revise <draft_id> remove_claims",
        ]
    )
