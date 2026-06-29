from __future__ import annotations

from dataclasses import dataclass


FOUNDER_DAILY_USE_LOOP_STAGE = "202P"
FOUNDER_DAILY_USE_LOOP_STATUS = "ready_for_founder_daily_use_v0"


@dataclass(frozen=True, slots=True)
class FounderDailyUseLoop:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    today_overview: str
    next_prep: str
    pending_suggestions: int
    pending_approvals: int
    pending_drafts: int
    pending_memory_reviews: int
    usage_cost_snapshot: str
    setup_warnings: tuple[str, ...]
    recommended_next_action: str
    source_trace_summary: str
    local_loop_only: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    autonomous_background_actions_allowed: bool
    billing_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != FOUNDER_DAILY_USE_LOOP_STAGE:
            raise ValueError("202P founder loops must identify the 202P stage.")
        if self.status != FOUNDER_DAILY_USE_LOOP_STATUS:
            raise ValueError("202P founder loops must use the daily use status.")
        if not all((self.today_overview, self.next_prep, self.usage_cost_snapshot, self.recommended_next_action, self.source_trace_summary)):
            raise ValueError("202P founder loops require the daily operating card fields.")
        if min(self.pending_suggestions, self.pending_approvals, self.pending_drafts, self.pending_memory_reviews) < 0:
            raise ValueError("202P founder loop counts must be non-negative.")
        if not self.local_loop_only or not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("202P founder loops must remain local, redacted, and approval-preserving.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
                self.autonomous_background_actions_allowed,
                self.billing_allowed,
            )
        ):
            raise ValueError("202P founder loops must not expand external action, background, or billing authority.")


def build_founder_daily_use_loop(
    *,
    owner_id: str,
    robot_id: str,
    today_overview: str | None = None,
    next_prep: str | None = None,
    pending_suggestions: int = 0,
    pending_approvals: int = 0,
    pending_drafts: int = 0,
    pending_memory_reviews: int = 0,
    usage_cost_snapshot: str | None = None,
    setup_warnings: tuple[str, ...] = (),
    source_trace_summary: str | None = None,
) -> FounderDailyUseLoop:
    recommended = _recommended_next_action(
        pending_suggestions=pending_suggestions,
        pending_approvals=pending_approvals,
        pending_drafts=pending_drafts,
        pending_memory_reviews=pending_memory_reviews,
        next_prep=next_prep,
    )
    return FounderDailyUseLoop(
        stage=FOUNDER_DAILY_USE_LOOP_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FOUNDER_DAILY_USE_LOOP_STATUS,
        today_overview=today_overview or "No live daily brief injected; run /daily_brief for real context or explicit fallback.",
        next_prep=next_prep or "No meeting prep injected; run /prep when Calendar/Gmail/Memory context is available.",
        pending_suggestions=pending_suggestions,
        pending_approvals=pending_approvals,
        pending_drafts=pending_drafts,
        pending_memory_reviews=pending_memory_reviews,
        usage_cost_snapshot=usage_cost_snapshot or "No local usage entries injected; /usage will show the local estimated ledger boundary.",
        setup_warnings=setup_warnings or ("Check /status or /checkup for Calendar, Gmail, Documents, Memory, and action boundaries.",),
        recommended_next_action=recommended,
        source_trace_summary=source_trace_summary or "Source trace not injected; important outputs must show real source trace or explicit fallback.",
        local_loop_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        autonomous_background_actions_allowed=False,
        billing_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_founder_daily_use_loop(loop: FounderDailyUseLoop) -> str:
    return "\n".join(
        [
            "Founder Daily Loop",
            "",
            f"Stage: {loop.stage}",
            f"Status: {loop.status}",
            "",
            "Today overview:",
            f"- {loop.today_overview}",
            "",
            "Next useful prep:",
            f"- {loop.next_prep}",
            "",
            "Queues:",
            f"- Pending suggestions: {loop.pending_suggestions}",
            f"- Pending approvals: {loop.pending_approvals}",
            f"- Pending drafts: {loop.pending_drafts}",
            f"- Pending memory reviews: {loop.pending_memory_reviews}",
            "",
            "Usage/cost:",
            f"- {loop.usage_cost_snapshot}",
            "",
            "Setup warnings:",
            *[f"- {warning}" for warning in loop.setup_warnings],
            "",
            "Source trace:",
            f"- {loop.source_trace_summary}",
            "",
            "Recommended next action:",
            f"- {loop.recommended_next_action}",
            "",
            "Gmail send: disabled",
            "Gmail modify/archive/delete: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "Autonomous background actions: disabled",
            "External writes: disabled",
            "Billing: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )


def _recommended_next_action(
    *,
    pending_suggestions: int,
    pending_approvals: int,
    pending_drafts: int,
    pending_memory_reviews: int,
    next_prep: str | None,
) -> str:
    if pending_approvals:
        return "Review /approvals before materializing any output."
    if pending_drafts:
        return "Review /drafts and approve, reject, edit, or expire the top draft."
    if pending_suggestions:
        return "Open /suggestions and choose the highest-priority safe next action."
    if pending_memory_reviews:
        return "Open /memory_review and approve, reject, or edit pending memory proposals."
    if next_prep:
        return "Run /prep for the next meeting and verify source trace."
    return "Run /daily_brief, then /prep, then /usage to start the founder daily routine."
