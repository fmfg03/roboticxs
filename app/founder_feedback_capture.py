from __future__ import annotations

from dataclasses import dataclass


FOUNDER_FEEDBACK_CAPTURE_STAGE = "203P"
FOUNDER_FEEDBACK_CAPTURE_STATUS = "captured_local_feedback_v0"
SUPPORTED_FEEDBACK_TAGS = (
    "useful",
    "wrong",
    "noisy",
    "stale",
    "missing_source",
    "bad_draft",
    "too_verbose",
    "not_useful",
    "missing_context",
    "wrong_context",
    "weak_agenda",
    "bad_risk",
    "bad_next_step",
    "not_actionable",
)


@dataclass(frozen=True, slots=True)
class FounderFeedbackCaptureReceipt:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    item_id: str
    item_type: str
    tag: str
    comment: str
    source_trace_id: str
    important_output_bound: bool
    local_capture_only: bool
    persisted: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != FOUNDER_FEEDBACK_CAPTURE_STAGE:
            raise ValueError("203P feedback receipts must identify the 203P stage.")
        if self.status != FOUNDER_FEEDBACK_CAPTURE_STATUS:
            raise ValueError("203P feedback receipts must use the capture status.")
        if self.tag not in SUPPORTED_FEEDBACK_TAGS:
            raise ValueError("203P feedback tag is unsupported.")
        if not self.item_id or not self.item_type:
            raise ValueError("203P feedback requires item binding.")
        if not self.important_output_bound:
            raise ValueError("203P feedback must bind to an important output type.")
        if not self.local_capture_only or self.persisted:
            raise ValueError("203P feedback capture is local and non-persistent until 204P.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("203P feedback must be redacted and approval-preserving.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("203P feedback must not expand external write authority.")


def parse_feedback_argument(argument: str | None) -> tuple[str, str, str]:
    parts = (argument or "").strip().split(maxsplit=2)
    if len(parts) < 2:
        return "", "", ""
    tag = parts[0].strip().lower()
    item_id = parts[1].strip()
    comment = parts[2].strip() if len(parts) == 3 else ""
    return tag, item_id, comment


def build_founder_feedback_capture_receipt(
    *,
    owner_id: str,
    robot_id: str,
    tag: str,
    item_id: str,
    comment: str = "",
    source_trace_id: str | None = None,
) -> FounderFeedbackCaptureReceipt:
    normalized_tag = tag.strip().lower()
    normalized_item_id = item_id.strip()
    item_type = infer_feedback_item_type(normalized_item_id)
    return FounderFeedbackCaptureReceipt(
        stage=FOUNDER_FEEDBACK_CAPTURE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FOUNDER_FEEDBACK_CAPTURE_STATUS,
        item_id=normalized_item_id,
        item_type=item_type,
        tag=normalized_tag,
        comment=_redact_comment(comment),
        source_trace_id=(source_trace_id or "source_trace_not_provided").strip() or "source_trace_not_provided",
        important_output_bound=item_type in IMPORTANT_FEEDBACK_ITEM_TYPES,
        local_capture_only=True,
        persisted=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


IMPORTANT_FEEDBACK_ITEM_TYPES = frozenset(
    {
        "founder_loop",
        "daily_brief",
        "prep",
        "suggestion",
        "draft",
        "approval",
        "memory",
        "document",
        "pilot",
    }
)


def infer_feedback_item_type(item_id: str) -> str:
    normalized = item_id.strip().lower().replace("_", "-")
    if normalized.startswith(("founder-loop", "founderloop")):
        return "founder_loop"
    if normalized.startswith(("daily-brief", "brief")):
        return "daily_brief"
    if normalized.startswith(("prep", "meeting")):
        return "prep"
    if normalized.startswith(("suggestion", "sugg")):
        return "suggestion"
    if normalized.startswith("draft"):
        return "draft"
    if normalized.startswith(("approval", "approve")):
        return "approval"
    if normalized.startswith(("memory", "mem")):
        return "memory"
    if normalized.startswith(("document", "doc")):
        return "document"
    if normalized.startswith("pilot"):
        return "pilot"
    return "unknown"


def render_founder_feedback_capture_receipt(receipt: FounderFeedbackCaptureReceipt) -> str:
    lines = [
        "Founder Feedback Capture",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        "",
        "Feedback:",
        f"- Item: {receipt.item_id}",
        f"- Type: {receipt.item_type}",
        f"- Tag: {receipt.tag}",
    ]
    if receipt.comment:
        lines.append(f"- Comment: {receipt.comment}")
    lines.extend(
        [
            f"- Source trace: {receipt.source_trace_id}",
            "",
            "Receipt:",
            "- Local capture only: yes",
            "- Persisted ledger: no, 204P required",
            "- Important output bound: yes",
            "",
            "Allowed tags:",
            f"- {', '.join(SUPPORTED_FEEDBACK_TAGS)}",
            "",
            "Gmail send: disabled",
            "Gmail modify/archive/delete: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def render_feedback_usage() -> str:
    return "\n".join(
        [
            "Founder Feedback Capture",
            "",
            "Usage:",
            "- /feedback useful <item_id>",
            "- /feedback wrong <item_id>",
            "- /feedback noisy <item_id>",
            "- /feedback stale <item_id>",
            "- /feedback missing_source <item_id>",
            "- /feedback bad_draft <item_id>",
            "- /feedback too_verbose <item_id>",
            "",
            "Examples:",
            "- /feedback useful founder-loop-today",
            "- /feedback missing_source prep-next",
            "- /feedback bad_draft draft-001 too generic",
            "",
            "Supported outputs:",
            "- founder loop, daily brief, prep, suggestions, drafts, approvals, memory, documents, pilot",
            "",
            "Local capture only. 204P is required before feedback is persisted.",
        ]
    )


def _redact_comment(comment: str) -> str:
    compact = " ".join(comment.strip().split())
    if not compact:
        return ""
    lowered = compact.lower()
    if any(marker in lowered for marker in ("token", "secret", "password", "authorization:", "bearer ")):
        return "[redacted-sensitive-comment]"
    return compact[:240]
