from __future__ import annotations

from dataclasses import dataclass

from app.daily_loop_outcome_tracker import DailyLoopOutcomeRecord
from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.usage_cost_ledger import UsageCostLedgerEntry, summarize_usage_cost_ledger


PILOT_METRICS_SNAPSHOT_STAGE = "210P"
PILOT_METRICS_SNAPSHOT_STATUS = "local_pilot_metrics_snapshot_v0"


@dataclass(frozen=True, slots=True)
class PilotMetricsSnapshot:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    daily_loops_run: int
    suggestions_feedback_count: int
    suggestions_positive: int
    suggestions_negative: int
    drafts_created: int
    drafts_approved: int
    memory_changes: int
    document_reviews: int
    usage_tasks: int
    estimated_cost_usd: float
    blocked_actions: int
    top_feedback_tags: tuple[tuple[str, int], ...]
    fallback_status: str
    local_snapshot_only: bool
    live_data_claimed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_METRICS_SNAPSHOT_STAGE:
            raise ValueError("210P pilot metrics snapshots must identify the 210P stage.")
        if self.status != PILOT_METRICS_SNAPSHOT_STATUS:
            raise ValueError("210P pilot metrics snapshots must use the snapshot status.")
        if min(
            self.daily_loops_run,
            self.suggestions_feedback_count,
            self.suggestions_positive,
            self.suggestions_negative,
            self.drafts_created,
            self.drafts_approved,
            self.memory_changes,
            self.document_reviews,
            self.usage_tasks,
            self.blocked_actions,
        ) < 0:
            raise ValueError("210P pilot metrics counts must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("210P pilot metrics cost must be non-negative.")
        if not self.local_snapshot_only or self.live_data_claimed:
            raise ValueError("210P pilot metrics must remain a local snapshot without live data claims.")
        if any(
            (
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("210P pilot metrics must not expand external write authority.")
        if not self.secrets_redacted:
            raise ValueError("210P pilot metrics must be redacted.")


def build_pilot_metrics_snapshot(
    *,
    owner_id: str,
    robot_id: str,
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
) -> PilotMetricsSnapshot:
    scoped_feedback = tuple(
        entry for entry in feedback_entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    scoped_outcomes = tuple(
        record for record in outcome_records if record.owner_id == owner_id and record.robot_id == robot_id
    )
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=usage_entries)
    feedback_tags = _count_by_tag(scoped_feedback)
    suggestion_feedback = tuple(entry for entry in scoped_feedback if entry.item_type == "suggestion")
    positive_tags = {"useful"}
    negative_tags = {"wrong", "noisy", "stale", "missing_source", "bad_draft", "too_verbose", "not_useful"}
    return PilotMetricsSnapshot(
        stage=PILOT_METRICS_SNAPSHOT_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_METRICS_SNAPSHOT_STATUS,
        daily_loops_run=len(scoped_outcomes),
        suggestions_feedback_count=len(suggestion_feedback),
        suggestions_positive=sum(1 for entry in suggestion_feedback if entry.tag in positive_tags),
        suggestions_negative=sum(1 for entry in suggestion_feedback if entry.tag in negative_tags),
        drafts_created=_count_outcome(scoped_outcomes, "draft_created"),
        drafts_approved=_count_outcome(scoped_outcomes, "draft_approved"),
        memory_changes=_count_outcome(scoped_outcomes, "memory_approved") + _count_feedback_items(scoped_feedback, "memory"),
        document_reviews=_count_outcome(scoped_outcomes, "document_reviewed") + _count_feedback_items(scoped_feedback, "document"),
        usage_tasks=usage_summary.total_tasks,
        estimated_cost_usd=usage_summary.total_estimated_cost_usd,
        blocked_actions=_count_outcome(scoped_outcomes, "blocked_by_missing_connector") + usage_summary.failed_tasks,
        top_feedback_tags=feedback_tags[:5],
        fallback_status=_fallback_status(scoped_feedback, scoped_outcomes, usage_entries),
        local_snapshot_only=True,
        live_data_claimed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
    )


def render_pilot_metrics_snapshot(snapshot: PilotMetricsSnapshot) -> str:
    lines = [
        "Pilot Metrics Snapshot",
        "",
        f"Stage: {snapshot.stage}",
        f"Status: {snapshot.status}",
        f"Fallback: {snapshot.fallback_status}",
        "",
        "Usage and value:",
        f"- Daily loops run: {snapshot.daily_loops_run}",
        f"- Suggestion feedback: {snapshot.suggestions_feedback_count}",
        f"- Suggestions positive: {snapshot.suggestions_positive}",
        f"- Suggestions negative: {snapshot.suggestions_negative}",
        f"- Drafts created: {snapshot.drafts_created}",
        f"- Drafts approved: {snapshot.drafts_approved}",
        f"- Memory changes signaled: {snapshot.memory_changes}",
        f"- Document reviews: {snapshot.document_reviews}",
        f"- Usage tasks: {snapshot.usage_tasks}",
        f"- Estimated cost: ${snapshot.estimated_cost_usd:.6f}",
        f"- Blocked actions: {snapshot.blocked_actions}",
        "",
        "Top feedback tags:",
    ]
    if snapshot.top_feedback_tags:
        lines.extend(f"- {tag}: {count}" for tag, count in snapshot.top_feedback_tags)
    else:
        lines.append("- none yet")
    lines.extend(
        [
            "",
            "Local snapshot only: yes",
            "Live data claimed: no",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def _count_outcome(records: tuple[DailyLoopOutcomeRecord, ...], outcome: str) -> int:
    return sum(1 for record in records if record.outcome == outcome)


def _count_feedback_items(entries: tuple[FeedbackLedgerEntry, ...], item_type: str) -> int:
    return sum(1 for entry in entries if entry.item_type == item_type)


def _count_by_tag(entries: tuple[FeedbackLedgerEntry, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.tag] = counts.get(entry.tag, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _fallback_status(
    feedback_entries: tuple[FeedbackLedgerEntry, ...],
    outcome_records: tuple[DailyLoopOutcomeRecord, ...],
    usage_entries: tuple[UsageCostLedgerEntry, ...],
) -> str:
    if feedback_entries or outcome_records or usage_entries:
        return "local_metrics_available"
    return "no_local_metrics_yet"
