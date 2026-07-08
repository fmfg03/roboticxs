from __future__ import annotations

from dataclasses import dataclass

from app.daily_loop_outcome_tracker import DailyLoopOutcomeRecord
from app.draft_revision_loop import DraftRevisionReceipt
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.memory_correction_loop import MemoryCorrectionReceipt
from app.pilot_safety_incident_log import PilotSafetyIncident
from app.pilot_support_issue_capture import PilotSupportIssueReceipt
from app.usage_cost_ledger import UsageCostLedgerEntry, summarize_usage_cost_ledger


PILOT_WEEKLY_REPORT_STAGE = "220P"
PILOT_WEEKLY_REPORT_STATUS = "local_pilot_weekly_report_v0"


@dataclass(frozen=True, slots=True)
class PilotWeeklyReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    active_days: int
    loops_run: int
    prep_packs_generated: int
    suggestions_accepted: int
    suggestions_dismissed: int
    drafts_created: int
    drafts_revised: int
    drafts_approved: int
    memories_approved: int
    memories_corrected: int
    memories_forgotten: int
    documents_reviewed: int
    feedback_tags: tuple[tuple[str, int], ...]
    issues_opened: int
    issues_resolved: int
    safety_incidents: int
    estimated_cost_usd: float
    top_product_learnings: tuple[str, ...]
    fallback_status: str
    local_report_only: bool
    live_data_claimed: bool
    external_ticket_created: bool
    crm_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_WEEKLY_REPORT_STAGE:
            raise ValueError("220P pilot weekly reports must identify the 220P stage.")
        if self.status != PILOT_WEEKLY_REPORT_STATUS:
            raise ValueError("220P pilot weekly reports must use the weekly report status.")
        if min(
            self.active_days,
            self.loops_run,
            self.prep_packs_generated,
            self.suggestions_accepted,
            self.suggestions_dismissed,
            self.drafts_created,
            self.drafts_revised,
            self.drafts_approved,
            self.memories_approved,
            self.memories_corrected,
            self.memories_forgotten,
            self.documents_reviewed,
            self.issues_opened,
            self.issues_resolved,
            self.safety_incidents,
        ) < 0:
            raise ValueError("220P pilot weekly report counts must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("220P pilot weekly report cost must be non-negative.")
        if len(self.top_product_learnings) > 3:
            raise ValueError("220P pilot weekly reports must show at most the top 3 learnings.")
        if not self.local_report_only or self.live_data_claimed or self.external_ticket_created:
            raise ValueError("220P pilot weekly reports must remain local and must not claim live data.")
        if any(
            (
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("220P pilot weekly reports must not expand external authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("220P pilot weekly reports must be redacted and approval-preserving.")


def build_pilot_weekly_report(
    *,
    owner_id: str,
    robot_id: str,
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
    issue_receipts: tuple[PilotSupportIssueReceipt, ...] = (),
    safety_incidents: tuple[PilotSafetyIncident, ...] = (),
    draft_revisions: tuple[DraftRevisionReceipt, ...] = (),
    memory_corrections: tuple[MemoryCorrectionReceipt, ...] = (),
) -> PilotWeeklyReport:
    scoped_feedback = tuple(
        entry for entry in feedback_entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    scoped_outcomes = tuple(record for record in outcome_records if record.owner_id == owner_id and record.robot_id == robot_id)
    scoped_issues = tuple(receipt for receipt in issue_receipts if receipt.owner_id == owner_id and receipt.robot_id == robot_id)
    scoped_safety = tuple(incident for incident in safety_incidents if incident.owner_id == owner_id and incident.robot_id == robot_id)
    scoped_draft_revisions = tuple(
        receipt for receipt in draft_revisions if receipt.owner_id == owner_id and receipt.robot_id == robot_id
    )
    scoped_memory_corrections = tuple(
        receipt for receipt in memory_corrections if receipt.owner_id == owner_id and receipt.robot_id == robot_id
    )
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=usage_entries)
    top_tags = _count_by_tag(scoped_feedback)[:5]
    return PilotWeeklyReport(
        stage=PILOT_WEEKLY_REPORT_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_WEEKLY_REPORT_STATUS,
        active_days=_active_days(scoped_outcomes, scoped_feedback, scoped_issues, scoped_safety),
        loops_run=len(scoped_outcomes),
        prep_packs_generated=_count_command(usage_summary.command_breakdown, "/prep"),
        suggestions_accepted=_count_feedback(scoped_feedback, "suggestion", {"useful"}),
        suggestions_dismissed=_count_feedback(scoped_feedback, "suggestion", {"wrong", "noisy", "stale", "not_useful"}),
        drafts_created=_count_outcome(scoped_outcomes, "draft_created"),
        drafts_revised=len(scoped_draft_revisions),
        drafts_approved=_count_outcome(scoped_outcomes, "draft_approved"),
        memories_approved=_count_outcome(scoped_outcomes, "memory_approved"),
        memories_corrected=sum(1 for receipt in scoped_memory_corrections if receipt.local_receipt_created),
        memories_forgotten=_count_feedback(scoped_feedback, "memory", {"stale", "wrong", "not_useful"}),
        documents_reviewed=_count_outcome(scoped_outcomes, "document_reviewed") + usage_summary.documents_reviewed,
        feedback_tags=top_tags,
        issues_opened=len(scoped_issues),
        issues_resolved=sum(1 for receipt in scoped_issues if receipt.status == "resolved"),
        safety_incidents=len(scoped_safety),
        estimated_cost_usd=usage_summary.total_estimated_cost_usd,
        top_product_learnings=_top_learnings(top_tags, scoped_issues, scoped_safety),
        fallback_status=_fallback_status(scoped_feedback, scoped_outcomes, scoped_issues, scoped_safety, usage_entries),
        local_report_only=True,
        live_data_claimed=False,
        external_ticket_created=False,
        crm_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_pilot_weekly_report(report: PilotWeeklyReport) -> str:
    lines = [
        "Pilot Weekly Report",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        f"Fallback: {report.fallback_status}",
        "",
        "Weekly value:",
        f"- Active days: {report.active_days}",
        f"- Loops run: {report.loops_run}",
        f"- Prep packs generated: {report.prep_packs_generated}",
        f"- Suggestions accepted: {report.suggestions_accepted}",
        f"- Suggestions dismissed: {report.suggestions_dismissed}",
        f"- Drafts created: {report.drafts_created}",
        f"- Drafts revised: {report.drafts_revised}",
        f"- Drafts approved: {report.drafts_approved}",
        f"- Memories approved: {report.memories_approved}",
        f"- Memories corrected: {report.memories_corrected}",
        f"- Memories forgotten: {report.memories_forgotten}",
        f"- Documents reviewed: {report.documents_reviewed}",
        f"- Issues opened: {report.issues_opened}",
        f"- Issues resolved: {report.issues_resolved}",
        f"- Safety incidents: {report.safety_incidents}",
        f"- Estimated cost: ${report.estimated_cost_usd:.6f}",
        "",
        "Top feedback tags:",
    ]
    if report.feedback_tags:
        lines.extend(f"- {tag}: {count}" for tag, count in report.feedback_tags)
    else:
        lines.append("- none yet")
    lines.extend(["", "Top 3 product learnings:"])
    if report.top_product_learnings:
        lines.extend(f"- {learning}" for learning in report.top_product_learnings)
    else:
        lines.append("- no_local_weekly_data_yet")
    lines.extend(
        [
            "",
            "Local report only: yes",
            "Live data claimed: no",
            "External ticket: no",
            "CRM write: disabled",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "WhatsApp: disabled",
            "Destructive actions: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def _count_by_tag(entries: tuple[FeedbackLedgerEntry, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.tag] = counts.get(entry.tag, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _count_feedback(entries: tuple[FeedbackLedgerEntry, ...], item_type: str, tags: set[str]) -> int:
    return sum(1 for entry in entries if entry.item_type == item_type and entry.tag in tags)


def _count_outcome(records: tuple[DailyLoopOutcomeRecord, ...], outcome: str) -> int:
    return sum(1 for record in records if record.outcome == outcome)


def _count_command(command_breakdown: tuple[tuple[str, int], ...], command: str) -> int:
    return next((count for command_name, count in command_breakdown if command_name == command), 0)


def _active_days(
    outcomes: tuple[DailyLoopOutcomeRecord, ...],
    feedback: tuple[FeedbackLedgerEntry, ...],
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
) -> int:
    dates = {
        timestamp[:10]
        for timestamp in (
            *(record.created_at for record in outcomes),
            *(entry.created_at for entry in feedback),
            *(receipt.created_at for receipt in issues),
            *(incident.created_at for incident in safety),
        )
        if timestamp
    }
    return len(dates)


def _top_learnings(
    feedback_tags: tuple[tuple[str, int], ...],
    issues: tuple[PilotSupportIssueReceipt, ...],
    safety: tuple[PilotSafetyIncident, ...],
) -> tuple[str, ...]:
    learnings: list[str] = []
    if feedback_tags:
        tag, count = feedback_tags[0]
        learnings.append(f"Feedback trend: {tag} appeared {count} time(s).")
    if issues:
        category_counts: dict[str, int] = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        category, count = sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))[0]
        learnings.append(f"Support trend: {category} issue(s) appeared {count} time(s).")
    if safety:
        incident_counts: dict[str, int] = {}
        for incident in safety:
            incident_counts[incident.incident_type] = incident_counts.get(incident.incident_type, 0) + 1
        incident_type, count = sorted(incident_counts.items(), key=lambda item: (-item[1], item[0]))[0]
        learnings.append(f"Safety trend: {incident_type} blocked {count} time(s).")
    return tuple(learnings[:3])


def _fallback_status(
    feedback_entries: tuple[FeedbackLedgerEntry, ...],
    outcome_records: tuple[DailyLoopOutcomeRecord, ...],
    issue_receipts: tuple[PilotSupportIssueReceipt, ...],
    safety_incidents: tuple[PilotSafetyIncident, ...],
    usage_entries: tuple[UsageCostLedgerEntry, ...],
) -> str:
    if feedback_entries or outcome_records or issue_receipts or safety_incidents or usage_entries:
        return "local_weekly_signals_available"
    return "no_local_weekly_data_yet"
