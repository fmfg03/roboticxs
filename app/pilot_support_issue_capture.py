from __future__ import annotations

from dataclasses import dataclass


PILOT_SUPPORT_ISSUE_CAPTURE_STAGE = "218P"
PILOT_SUPPORT_ISSUE_CAPTURE_STATUS = "local_pilot_issue_captured_v0"
PILOT_ISSUE_COMMANDS = (
    "/report_issue",
    "/report_bug",
    "/report_confusing",
    "/report_wrong",
    "/report_missing",
    "/report_slow",
)
PILOT_ISSUE_CATEGORIES_BY_COMMAND = {
    "/report_issue": "general",
    "/report_bug": "bug",
    "/report_confusing": "confusing",
    "/report_wrong": "wrong_output",
    "/report_missing": "missing_context",
    "/report_slow": "slow_or_costly",
}
PILOT_ISSUE_SEVERITIES = ("low", "medium", "high", "critical")
DEFAULT_ISSUE_CREATED_AT = "2026-07-08T00:00:00Z"


@dataclass(frozen=True, slots=True)
class PilotSupportIssueReceipt:
    stage: str
    owner_id: str
    robot_id: str
    pilot_user_id: str
    issue_id: str
    command: str
    item_id: str
    severity: str
    category: str
    comment: str
    source_trace_id: str
    created_at: str
    status: str
    local_capture_only: bool
    external_ticket_created: bool
    crm_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_SUPPORT_ISSUE_CAPTURE_STAGE:
            raise ValueError("218P pilot issue receipts must identify the 218P stage.")
        if self.status != PILOT_SUPPORT_ISSUE_CAPTURE_STATUS:
            raise ValueError("218P pilot issue receipts must use the issue capture status.")
        if self.command not in PILOT_ISSUE_COMMANDS:
            raise ValueError("218P pilot issue command is unsupported.")
        if self.severity not in PILOT_ISSUE_SEVERITIES:
            raise ValueError("218P pilot issue severity is unsupported.")
        if not all((self.owner_id, self.robot_id, self.pilot_user_id, self.issue_id, self.item_id, self.created_at)):
            raise ValueError("218P pilot issue receipts require identity, item binding, and timestamp.")
        if not self.local_capture_only or self.external_ticket_created:
            raise ValueError("218P pilot issue capture must remain local.")
        if any(
            (
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("218P pilot issue capture must not expand external authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("218P pilot issue receipts must be redacted and approval-preserving.")


def parse_pilot_issue_argument(argument: str | None) -> tuple[str, str, str]:
    parts = (argument or "").strip().split(maxsplit=2)
    if not parts:
        return "medium", "pilot-unspecified", ""
    severity = parts[0].lower()
    if severity in PILOT_ISSUE_SEVERITIES:
        item_id = parts[1] if len(parts) >= 2 else "pilot-unspecified"
        comment = parts[2] if len(parts) >= 3 else ""
        return severity, item_id, comment
    item_id = parts[0]
    comment = " ".join(parts[1:]) if len(parts) > 1 else ""
    return "medium", item_id, comment


def build_pilot_support_issue_receipt(
    *,
    owner_id: str,
    robot_id: str,
    pilot_user_id: str,
    command: str,
    severity: str,
    item_id: str,
    comment: str = "",
    source_trace_id: str | None = None,
    created_at: str = DEFAULT_ISSUE_CREATED_AT,
) -> PilotSupportIssueReceipt:
    normalized_command = command.strip()
    normalized_severity = severity.strip().lower() or "medium"
    normalized_item_id = item_id.strip() or "pilot-unspecified"
    category = PILOT_ISSUE_CATEGORIES_BY_COMMAND.get(normalized_command, "general")
    issue_id = f"issue-{category}-{normalized_item_id}-{normalized_severity}".replace(" ", "-")
    return PilotSupportIssueReceipt(
        stage=PILOT_SUPPORT_ISSUE_CAPTURE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        pilot_user_id=pilot_user_id.strip() or "unknown-pilot-user",
        issue_id=issue_id,
        command=normalized_command,
        item_id=normalized_item_id,
        severity=normalized_severity,
        category=category,
        comment=_redact_comment(comment),
        source_trace_id=(source_trace_id or "source_trace_not_provided").strip() or "source_trace_not_provided",
        created_at=created_at,
        status=PILOT_SUPPORT_ISSUE_CAPTURE_STATUS,
        local_capture_only=True,
        external_ticket_created=False,
        crm_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_pilot_support_issue_receipt(receipt: PilotSupportIssueReceipt) -> str:
    lines = [
        "Pilot Support Issue",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Issue id: {receipt.issue_id}",
        f"Pilot user: {receipt.pilot_user_id}",
        f"Command: {receipt.command}",
        f"Item: {receipt.item_id}",
        f"Severity: {receipt.severity}",
        f"Category: {receipt.category}",
    ]
    if receipt.comment:
        lines.append(f"Comment: {receipt.comment}")
    lines.extend(
        [
            f"Source trace: {receipt.source_trace_id}",
            f"Created at: {receipt.created_at}",
            "",
            "Receipt:",
            "- Local capture only: yes",
            "- External ticket: no",
            "- CRM write: disabled",
            "- Gmail send: disabled",
            "- Calendar writes: disabled",
            "- WhatsApp: disabled",
            "- Destructive actions: disabled",
            "- Approval gate: preserved",
            "- Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def render_pilot_issue_usage() -> str:
    return "\n".join(
        [
            "Pilot Support Issue",
            "",
            "Usage:",
            "- /report_issue [severity] <item_id> [comment]",
            "- /report_bug [severity] <item_id> [comment]",
            "- /report_confusing [severity] <item_id> [comment]",
            "- /report_wrong [severity] <item_id> [comment]",
            "- /report_missing [severity] <item_id> [comment]",
            "- /report_slow [severity] <item_id> [comment]",
            "",
            "Severities:",
            "- low, medium, high, critical",
            "",
            "Examples:",
            "- /report_bug high prep-next source trace missing",
            "- /report_confusing daily-brief-today too much setup text",
        ]
    )


def _redact_comment(comment: str) -> str:
    redacted = comment.strip()
    for marker in ("authorization", "bearer", "token", "secret", "client_secret", "refresh_token", "access_token"):
        redacted = redacted.replace(marker, "[redacted]")
        redacted = redacted.replace(marker.upper(), "[redacted]")
    return redacted
