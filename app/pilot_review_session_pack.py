from __future__ import annotations

from dataclasses import dataclass

from app.daily_loop_outcome_tracker import DailyLoopOutcomeRecord
from app.draft_revision_loop import DraftRevisionReceipt
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.first_friendly_user_activation import FirstFriendlyUserActivationReceipt
from app.memory_correction_loop import MemoryCorrectionReceipt
from app.pilot_safety_incident_log import PilotSafetyIncident
from app.pilot_support_issue_capture import PilotSupportIssueReceipt
from app.usage_cost_ledger import UsageCostLedgerEntry, summarize_usage_cost_ledger


PILOT_REVIEW_SESSION_PACK_STAGE = "224P"
PILOT_REVIEW_SESSION_PACK_STATUS = "local_pilot_review_session_pack_v0"


@dataclass(frozen=True, slots=True)
class PilotReviewSessionPack:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    pilot_user_id: str
    pilot_alias: str
    what_user_tried: tuple[str, ...]
    what_worked: tuple[str, ...]
    where_stuck: tuple[str, ...]
    best_output: str
    worst_output: str
    missing_connector_or_context: tuple[str, ...]
    confusing_command_or_copy: tuple[str, ...]
    safety_blocks: tuple[str, ...]
    recommended_product_fixes: tuple[str, ...]
    estimated_cost_usd: float
    fallback_status: str
    local_review_only: bool
    live_data_claimed: bool
    external_ticket_created: bool
    crm_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool
    source_trace_preserved: bool
    usage_cost_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_REVIEW_SESSION_PACK_STAGE:
            raise ValueError("224P review packs must identify the 224P stage.")
        if self.status != PILOT_REVIEW_SESSION_PACK_STATUS:
            raise ValueError("224P review packs must use the review pack status.")
        if not self.pilot_user_id.strip() or not self.pilot_alias.strip():
            raise ValueError("224P review packs require pilot user id and alias.")
        if self.estimated_cost_usd < 0:
            raise ValueError("224P review pack cost must be non-negative.")
        if any(
            (
                not self.local_review_only,
                self.live_data_claimed,
                self.external_ticket_created,
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("224P review packs must remain local and must not expand external authority.")
        if not all((self.secrets_redacted, self.approval_gate_preserved, self.source_trace_preserved, self.usage_cost_preserved)):
            raise ValueError("224P review packs must preserve redaction, approval, trace, and cost semantics.")


def parse_pilot_review_argument(argument: str | None, *, fallback_pilot_user_id: str) -> tuple[str, str]:
    if not argument or not argument.strip():
        return fallback_pilot_user_id, "Friendly pilot"
    stripped = argument.strip()
    parts = stripped.split(maxsplit=1)
    if parts[0].isdigit() or parts[0].startswith("pilot-"):
        return parts[0], parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Friendly pilot"
    return fallback_pilot_user_id, stripped


def build_pilot_review_session_pack(
    *,
    owner_id: str,
    robot_id: str,
    pilot_user_id: str = "local-friendly-user",
    pilot_alias: str = "Friendly pilot",
    activation_receipts: tuple[FirstFriendlyUserActivationReceipt, ...] = (),
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
    issue_receipts: tuple[PilotSupportIssueReceipt, ...] = (),
    safety_incidents: tuple[PilotSafetyIncident, ...] = (),
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
    draft_revisions: tuple[DraftRevisionReceipt, ...] = (),
    memory_corrections: tuple[MemoryCorrectionReceipt, ...] = (),
) -> PilotReviewSessionPack:
    user_id = pilot_user_id.strip() or "local-friendly-user"
    alias = pilot_alias.strip() or _alias_from_activation(user_id, activation_receipts) or "Friendly pilot"
    scoped_activations = tuple(
        receipt
        for receipt in activation_receipts
        if receipt.owner_id == owner_id and receipt.robot_id == robot_id and receipt.pilot_user_id == user_id
    )
    scoped_feedback = tuple(
        entry for entry in feedback_entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    scoped_outcomes = tuple(record for record in outcome_records if record.owner_id == owner_id and record.robot_id == robot_id)
    scoped_issues = tuple(
        receipt
        for receipt in issue_receipts
        if receipt.owner_id == owner_id and receipt.robot_id == robot_id and receipt.pilot_user_id == user_id
    )
    scoped_safety = tuple(
        incident
        for incident in safety_incidents
        if incident.owner_id == owner_id and incident.robot_id == robot_id and incident.pilot_user_id == user_id
    )
    scoped_draft_revisions = tuple(
        receipt for receipt in draft_revisions if receipt.owner_id == owner_id and receipt.robot_id == robot_id
    )
    scoped_memory_corrections = tuple(
        receipt for receipt in memory_corrections if receipt.owner_id == owner_id and receipt.robot_id == robot_id
    )
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=usage_entries)
    return PilotReviewSessionPack(
        stage=PILOT_REVIEW_SESSION_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_REVIEW_SESSION_PACK_STATUS,
        pilot_user_id=user_id,
        pilot_alias=alias,
        what_user_tried=_what_user_tried(scoped_activations, scoped_outcomes, usage_summary.command_breakdown),
        what_worked=_what_worked(scoped_feedback, scoped_outcomes, scoped_draft_revisions, scoped_memory_corrections),
        where_stuck=_where_stuck(scoped_issues, scoped_safety, usage_summary.failed_tasks),
        best_output=_best_output(scoped_feedback),
        worst_output=_worst_output(scoped_feedback, scoped_issues),
        missing_connector_or_context=_missing_context(scoped_issues, scoped_safety, usage_summary.failed_tasks),
        confusing_command_or_copy=_confusing_copy(scoped_issues, scoped_feedback),
        safety_blocks=tuple(f"{incident.incident_type}: {incident.reason}" for incident in scoped_safety[:5]) or ("none_recorded",),
        recommended_product_fixes=_recommended_fixes(scoped_feedback, scoped_issues, scoped_safety),
        estimated_cost_usd=usage_summary.total_estimated_cost_usd,
        fallback_status=_fallback_status(
            scoped_activations,
            scoped_feedback,
            scoped_outcomes,
            scoped_issues,
            scoped_safety,
            usage_entries,
            scoped_draft_revisions,
            scoped_memory_corrections,
        ),
        local_review_only=True,
        live_data_claimed=False,
        external_ticket_created=False,
        crm_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
        source_trace_preserved=True,
        usage_cost_preserved=True,
    )


def render_pilot_review_session_pack(pack: PilotReviewSessionPack) -> str:
    lines = [
        "Pilot Review Session Pack",
        "",
        f"Stage: {pack.stage}",
        f"Status: {pack.status}",
        f"Pilot: {pack.pilot_alias}",
        f"Pilot user id: {pack.pilot_user_id}",
        f"Fallback: {pack.fallback_status}",
        f"Estimated cost: ${pack.estimated_cost_usd:.6f}",
        "",
        "What the user tried:",
        *_bullet_lines(pack.what_user_tried),
        "",
        "What worked:",
        *_bullet_lines(pack.what_worked),
        "",
        "Where they got stuck:",
        *_bullet_lines(pack.where_stuck),
        "",
        f"Best output: {pack.best_output}",
        f"Worst output: {pack.worst_output}",
        "",
        "Missing connector/context:",
        *_bullet_lines(pack.missing_connector_or_context),
        "",
        "Confusing command/copy:",
        *_bullet_lines(pack.confusing_command_or_copy),
        "",
        "Safety blocks:",
        *_bullet_lines(pack.safety_blocks),
        "",
        "Recommended product fixes:",
        *_bullet_lines(pack.recommended_product_fixes),
        "",
        "Safety:",
        "- Local review only: yes",
        "- Live data claimed: no",
        "- External ticket: no",
        "- CRM write: disabled",
        "- Gmail send: disabled",
        "- Calendar writes: disabled",
        "- WhatsApp: disabled",
        "- Destructive actions: disabled",
        "- External writes: disabled",
        "- Approval gate: preserved",
        "- Source trace: preserved",
        "- Usage/cost: preserved",
        "- Secrets: redacted",
    ]
    return "\n".join(lines)


def _alias_from_activation(user_id: str, activations: tuple[FirstFriendlyUserActivationReceipt, ...]) -> str:
    return next((receipt.pilot_alias for receipt in activations if receipt.pilot_user_id == user_id), "")


def _what_user_tried(
    activations: tuple[FirstFriendlyUserActivationReceipt, ...],
    outcomes: tuple[DailyLoopOutcomeRecord, ...],
    command_breakdown: tuple[tuple[str, int], ...],
) -> tuple[str, ...]:
    tried: list[str] = []
    if activations:
        tried.append("/pilot_activate")
    tried.extend(command for command, count in command_breakdown if count > 0)
    tried.extend(f"/founder_outcome:{record.outcome}" for record in outcomes[:5])
    return tuple(dict.fromkeys(tried)) or ("no_local_session_activity_yet",)


def _what_worked(
    feedback: tuple[FeedbackLedgerEntry, ...],
    outcomes: tuple[DailyLoopOutcomeRecord, ...],
    draft_revisions: tuple[DraftRevisionReceipt, ...],
    memory_corrections: tuple[MemoryCorrectionReceipt, ...],
) -> tuple[str, ...]:
    worked = [f"{entry.item_type}/{entry.item_id}: useful" for entry in feedback if entry.tag == "useful"]
    worked.extend(f"outcome:{record.outcome}" for record in outcomes if record.outcome not in {"no_action", "blocked_by_missing_connector"})
    if draft_revisions:
        worked.append(f"draft revisions: {len(draft_revisions)}")
    if any(receipt.local_receipt_created for receipt in memory_corrections):
        worked.append("memory corrections captured")
    return tuple(worked[:6]) or ("no_positive_signal_recorded_yet",)


def _where_stuck(
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
    failed_tasks: int,
) -> tuple[str, ...]:
    stuck = [f"{issue.category}: {issue.comment or issue.item_id}" for issue in issues]
    stuck.extend(f"safety:{incident.incident_type}" for incident in safety)
    if failed_tasks:
        stuck.append(f"usage failures/blocked tasks: {failed_tasks}")
    return tuple(stuck[:6]) or ("no_blocker_recorded_yet",)


def _best_output(feedback: tuple[FeedbackLedgerEntry, ...]) -> str:
    return next((f"{entry.item_type}/{entry.item_id} ({entry.source_trace_id})" for entry in feedback if entry.tag == "useful"), "not_recorded_yet")


def _worst_output(feedback: tuple[FeedbackLedgerEntry, ...], issues: tuple[PilotSupportIssueReceipt, ...]) -> str:
    negative = {"wrong", "noisy", "stale", "missing_source", "bad_draft", "too_verbose", "not_useful"}
    item = next((entry for entry in feedback if entry.tag in negative), None)
    if item is not None:
        return f"{item.item_type}/{item.item_id}: {item.tag}"
    issue = next(iter(issues), None)
    if issue is not None:
        return f"{issue.category}/{issue.item_id}: {issue.severity}"
    return "not_recorded_yet"


def _missing_context(
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
    failed_tasks: int,
) -> tuple[str, ...]:
    missing = [issue.comment or issue.item_id for issue in issues if issue.category in {"missing_context", "wrong_output"}]
    missing.extend(incident.reason for incident in safety if "connector" in incident.incident_type or "scope" in incident.incident_type)
    if failed_tasks:
        missing.append("usage ledger has failed or blocked task(s)")
    return tuple(missing[:5]) or ("none_recorded",)


def _confusing_copy(issues: tuple[PilotSupportIssueReceipt, ...], feedback: tuple[FeedbackLedgerEntry, ...]) -> tuple[str, ...]:
    confusing = [issue.comment or issue.item_id for issue in issues if issue.category == "confusing"]
    confusing.extend(f"{entry.item_type}/{entry.item_id}: too_verbose" for entry in feedback if entry.tag == "too_verbose")
    return tuple(confusing[:5]) or ("none_recorded",)


def _recommended_fixes(
    feedback: tuple[FeedbackLedgerEntry, ...],
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
) -> tuple[str, ...]:
    fixes: list[str] = []
    if any(entry.tag == "missing_source" for entry in feedback) or any(issue.category == "missing_context" for issue in issues):
        fixes.append("P1: improve source/context visibility before next pilot session")
    if any(entry.tag in {"bad_draft", "wrong"} for entry in feedback) or any(issue.category == "wrong_output" for issue in issues):
        fixes.append("P1: tune output quality for the failing item type")
    if any(issue.category == "confusing" for issue in issues) or any(entry.tag == "too_verbose" for entry in feedback):
        fixes.append("P2: simplify Telegram copy and command guidance")
    if safety:
        fixes.append("P0: review safety blocks before expanding pilot")
    return tuple(fixes[:5]) or ("no_prioritized_fix_recorded_yet",)


def _fallback_status(
    activations: tuple[FirstFriendlyUserActivationReceipt, ...],
    feedback: tuple[FeedbackLedgerEntry, ...],
    outcomes: tuple[DailyLoopOutcomeRecord, ...],
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
    usage: tuple[UsageCostLedgerEntry, ...],
    draft_revisions: tuple[DraftRevisionReceipt, ...],
    memory_corrections: tuple[MemoryCorrectionReceipt, ...],
) -> str:
    if activations or feedback or outcomes or issues or safety or usage or draft_revisions or memory_corrections:
        return "local_review_signals_available"
    return "no_local_review_data_yet"


def _bullet_lines(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]
