from __future__ import annotations

from dataclasses import dataclass

from app.daily_loop_outcome_tracker import DailyLoopOutcomeRecord
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.first_friendly_user_activation import FirstFriendlyUserActivationReceipt
from app.pilot_learning_queue import PilotLearningQueue
from app.pilot_safety_incident_log import PilotSafetyIncident
from app.pilot_support_issue_capture import PilotSupportIssueReceipt
from app.usage_cost_ledger import UsageCostLedgerEntry, summarize_usage_cost_ledger


PAID_PILOT_READINESS_GATE_STAGE = "226P"
PAID_PILOT_READINESS_GATE_STATUS = "local_paid_pilot_readiness_gate_v0"
PAID_PILOT_DECISIONS = ("READY_FOR_PAID_PILOT", "READY_WITH_LIMITATIONS", "NOT_READY")


@dataclass(frozen=True, slots=True)
class PaidPilotReadinessCheck:
    name: str
    status: str
    evidence: str

    def __post_init__(self) -> None:
        if self.status not in {"pass", "watch", "fail"}:
            raise ValueError("226P paid pilot readiness check status is unsupported.")
        if not all((self.name, self.evidence)):
            raise ValueError("226P paid pilot readiness checks require name and evidence.")


@dataclass(frozen=True, slots=True)
class PaidPilotReadinessGate:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    decision: str
    reason: str
    checks: tuple[PaidPilotReadinessCheck, ...]
    active_days: int
    activated_users: int
    useful_output_rate: float
    draft_approval_rate: float
    suggestion_acceptance_rate: float
    memory_correction_rate: float
    high_or_critical_issues: int
    safety_incidents: int
    cost_per_active_pilot_user_usd: float
    manual_support_burden: float
    fallback_status: str
    local_gate_only: bool
    billing_enabled: bool
    payment_link_created: bool
    external_ticket_created: bool
    crm_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    external_write_allowed: bool
    live_data_claimed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool
    source_trace_preserved: bool
    usage_cost_preserved: bool
    pilot_data_boundary_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PAID_PILOT_READINESS_GATE_STAGE:
            raise ValueError("226P readiness gates must identify the 226P stage.")
        if self.status != PAID_PILOT_READINESS_GATE_STATUS:
            raise ValueError("226P readiness gates must use the readiness gate status.")
        if self.decision not in PAID_PILOT_DECISIONS:
            raise ValueError("226P paid pilot readiness decision is unsupported.")
        if len(self.checks) < 9:
            raise ValueError("226P readiness gates must evaluate the paid pilot checks.")
        if min(
            self.active_days,
            self.activated_users,
            self.high_or_critical_issues,
            self.safety_incidents,
        ) < 0:
            raise ValueError("226P paid pilot readiness counts must be non-negative.")
        if not all(0 <= value <= 1 for value in (self.useful_output_rate, self.draft_approval_rate, self.suggestion_acceptance_rate)):
            raise ValueError("226P paid pilot readiness rates must be between 0 and 1.")
        if self.memory_correction_rate < 0 or self.cost_per_active_pilot_user_usd < 0 or self.manual_support_burden < 0:
            raise ValueError("226P paid pilot readiness derived metrics must be non-negative.")
        if any(
            (
                not self.local_gate_only,
                self.billing_enabled,
                self.payment_link_created,
                self.external_ticket_created,
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
                self.external_write_allowed,
                self.live_data_claimed,
            )
        ):
            raise ValueError("226P paid pilot readiness must remain local and must not expand authority.")
        if not all(
            (
                self.secrets_redacted,
                self.approval_gate_preserved,
                self.source_trace_preserved,
                self.usage_cost_preserved,
                self.pilot_data_boundary_preserved,
            )
        ):
            raise ValueError("226P paid pilot readiness must preserve redaction, approval, trace, cost, and boundary semantics.")


def build_paid_pilot_readiness_gate(
    *,
    owner_id: str,
    robot_id: str,
    activation_receipts: tuple[FirstFriendlyUserActivationReceipt, ...] = (),
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
    issue_receipts: tuple[PilotSupportIssueReceipt, ...] = (),
    safety_incidents: tuple[PilotSafetyIncident, ...] = (),
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
    learning_queue: PilotLearningQueue | None = None,
) -> PaidPilotReadinessGate:
    activations = tuple(receipt for receipt in activation_receipts if receipt.owner_id == owner_id and receipt.robot_id == robot_id)
    feedback = tuple(
        entry for entry in feedback_entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    outcomes = tuple(record for record in outcome_records if record.owner_id == owner_id and record.robot_id == robot_id)
    issues = tuple(receipt for receipt in issue_receipts if receipt.owner_id == owner_id and receipt.robot_id == robot_id)
    safety = tuple(incident for incident in safety_incidents if incident.owner_id == owner_id and incident.robot_id == robot_id)
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=usage_entries)
    active_days = _active_days(outcomes, feedback, issues, safety)
    activated_users = len(activations)
    useful_outputs = _useful_outputs(feedback, outcomes)
    total_output_signals = _total_output_signals(feedback, outcomes)
    useful_output_rate = _rate(useful_outputs, total_output_signals)
    drafts_created = _count_outcome(outcomes, "draft_created")
    drafts_approved = _count_outcome(outcomes, "draft_approved")
    draft_approval_rate = _rate(drafts_approved, drafts_created)
    suggestion_positive = _count_feedback(feedback, "suggestion", {"useful"})
    suggestion_negative = _count_feedback(feedback, "suggestion", {"wrong", "noisy", "stale", "not_useful", "missing_source"})
    suggestion_acceptance_rate = _rate(suggestion_positive, suggestion_positive + suggestion_negative)
    memory_corrections = _count_feedback(feedback, "memory", {"wrong", "stale", "duplicate", "not_useful"})
    memories_approved = _count_outcome(outcomes, "memory_approved")
    memory_correction_rate = round(memory_corrections / max(1, memories_approved), 3)
    severe_issues = sum(1 for issue in issues if issue.severity in {"high", "critical"})
    severe_safety = sum(1 for incident in safety if incident.severity in {"high", "critical"})
    cost_per_user = round(usage_summary.total_estimated_cost_usd / max(1, activated_users), 6)
    manual_support_burden = round(len(issues) / max(1, active_days), 3)
    p0_learnings = 0
    if learning_queue is not None and learning_queue.owner_id == owner_id and learning_queue.robot_id == robot_id:
        p0_learnings = sum(1 for item in learning_queue.items if item.priority == "P0")
    checks = (
        _check("Activation success", activated_users >= 1, activated_users > 0, f"{activated_users} local activation receipt(s)."),
        _check("Day-7 usage", active_days >= 7, active_days >= 3, f"{active_days} active local day(s)."),
        _check("Useful output rate", useful_output_rate >= 0.6, useful_output_rate >= 0.3, f"{useful_output_rate:.3f} useful output rate."),
        _check("Draft approval rate", draft_approval_rate >= 0.5, drafts_created == 0 or draft_approval_rate >= 0.25, f"{drafts_approved}/{drafts_created} draft approvals."),
        _check(
            "Suggestion acceptance rate",
            suggestion_acceptance_rate >= 0.5,
            suggestion_positive + suggestion_negative == 0 or suggestion_acceptance_rate >= 0.25,
            f"{suggestion_positive}/{suggestion_positive + suggestion_negative} suggestion accepts.",
        ),
        _check("Memory correction rate", memory_correction_rate <= 0.5, memory_correction_rate <= 1.0, f"{memory_correction_rate:.3f} corrections per approved memory."),
        _check("Issue severity", severe_issues == 0, severe_issues <= 1, f"{severe_issues} high/critical issue(s)."),
        _check("Safety incidents", severe_safety == 0 and p0_learnings == 0, severe_safety == 0, f"{severe_safety} high/critical incident(s), {p0_learnings} P0 learning(s)."),
        _check("Cost per active pilot user", cost_per_user <= 0.25, cost_per_user <= 1.0, f"${cost_per_user:.6f} estimated local cost per activated user."),
        _check("Manual support burden", manual_support_burden <= 0.5, manual_support_burden <= 1.0, f"{manual_support_burden:.3f} issue(s) per active day."),
    )
    decision = _decision(checks)
    return PaidPilotReadinessGate(
        stage=PAID_PILOT_READINESS_GATE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PAID_PILOT_READINESS_GATE_STATUS,
        decision=decision,
        reason=_reason(decision, checks),
        checks=checks,
        active_days=active_days,
        activated_users=activated_users,
        useful_output_rate=useful_output_rate,
        draft_approval_rate=draft_approval_rate,
        suggestion_acceptance_rate=suggestion_acceptance_rate,
        memory_correction_rate=memory_correction_rate,
        high_or_critical_issues=severe_issues,
        safety_incidents=len(safety),
        cost_per_active_pilot_user_usd=cost_per_user,
        manual_support_burden=manual_support_burden,
        fallback_status="local_paid_pilot_signals_available" if activations or feedback or outcomes or issues or safety or usage_entries else "no_local_paid_pilot_signals_yet",
        local_gate_only=True,
        billing_enabled=False,
        payment_link_created=False,
        external_ticket_created=False,
        crm_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        external_write_allowed=False,
        live_data_claimed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
        source_trace_preserved=True,
        usage_cost_preserved=True,
        pilot_data_boundary_preserved=True,
    )


def render_paid_pilot_readiness_gate(gate: PaidPilotReadinessGate) -> str:
    lines = [
        "Paid Pilot Readiness Gate",
        "",
        f"Stage: {gate.stage}",
        f"Status: {gate.status}",
        f"Decision: {gate.decision}",
        f"Reason: {gate.reason}",
        f"Fallback: {gate.fallback_status}",
        "",
        "Readiness metrics:",
        f"- Activated pilot users: {gate.activated_users}",
        f"- Active days: {gate.active_days}",
        f"- Useful output rate: {gate.useful_output_rate:.3f}",
        f"- Draft approval rate: {gate.draft_approval_rate:.3f}",
        f"- Suggestion acceptance rate: {gate.suggestion_acceptance_rate:.3f}",
        f"- Memory correction rate: {gate.memory_correction_rate:.3f}",
        f"- High/critical issues: {gate.high_or_critical_issues}",
        f"- Safety incidents: {gate.safety_incidents}",
        f"- Cost per active pilot user: ${gate.cost_per_active_pilot_user_usd:.6f}",
        f"- Manual support burden: {gate.manual_support_burden:.3f}",
        "",
        "Gate checks:",
    ]
    lines.extend(f"- {check.status.upper()} {check.name}: {check.evidence}" for check in gate.checks)
    lines.extend(
        [
            "",
            "Safety:",
            "- Local readiness gate only: yes",
            "- Billing enabled: no",
            "- Payment link created: no",
            "- External ticket: no",
            "- CRM write: disabled",
            "- Gmail send: disabled",
            "- Calendar writes: disabled",
            "- WhatsApp: disabled",
            "- Destructive actions: disabled",
            "- External writes: disabled",
            "- Live data claimed: no",
            "- Approval gate: preserved",
            "- Source trace: preserved",
            "- Usage/cost: preserved",
            "- Pilot data boundary: preserved",
            "- Secrets: redacted",
        ]
    )
    return "\n".join(lines)


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


def _count_outcome(records: tuple[DailyLoopOutcomeRecord, ...], outcome: str) -> int:
    return sum(1 for record in records if record.outcome == outcome)


def _count_feedback(entries: tuple[FeedbackLedgerEntry, ...], item_type: str, tags: set[str]) -> int:
    return sum(1 for entry in entries if entry.item_type == item_type and entry.tag in tags)


def _useful_outputs(entries: tuple[FeedbackLedgerEntry, ...], records: tuple[DailyLoopOutcomeRecord, ...]) -> int:
    useful_feedback = sum(1 for entry in entries if entry.tag == "useful")
    useful_outcomes = sum(
        1
        for record in records
        if record.outcome in {"suggestion_opened", "draft_created", "draft_approved", "memory_approved", "document_reviewed"}
    )
    return useful_feedback + useful_outcomes


def _total_output_signals(entries: tuple[FeedbackLedgerEntry, ...], records: tuple[DailyLoopOutcomeRecord, ...]) -> int:
    return len(entries) + sum(1 for record in records if record.outcome != "viewed")


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(1.0, numerator / denominator), 3)


def _check(name: str, passed: bool, watch: bool, evidence: str) -> PaidPilotReadinessCheck:
    status = "pass" if passed else "watch" if watch else "fail"
    return PaidPilotReadinessCheck(name=name, status=status, evidence=evidence)


def _decision(checks: tuple[PaidPilotReadinessCheck, ...]) -> str:
    if any(check.status == "fail" for check in checks):
        return "NOT_READY"
    if any(check.status == "watch" for check in checks):
        return "READY_WITH_LIMITATIONS"
    return "READY_FOR_PAID_PILOT"


def _reason(decision: str, checks: tuple[PaidPilotReadinessCheck, ...]) -> str:
    failing = tuple(check.name for check in checks if check.status == "fail")
    watch = tuple(check.name for check in checks if check.status == "watch")
    if decision == "NOT_READY":
        return "Blocking checks: " + ", ".join(failing)
    if decision == "READY_WITH_LIMITATIONS":
        return "Watch checks: " + ", ".join(watch)
    return "All local paid pilot readiness checks passed."
