from __future__ import annotations

from dataclasses import dataclass

from app.feedback_ledger_tags import FeedbackLedgerEntry
from app.pilot_review_session_pack import PilotReviewSessionPack
from app.pilot_safety_incident_log import PilotSafetyIncident
from app.pilot_support_issue_capture import PilotSupportIssueReceipt
from app.usage_cost_ledger import UsageCostLedgerEntry, summarize_usage_cost_ledger


PILOT_LEARNING_QUEUE_STAGE = "225P"
PILOT_LEARNING_QUEUE_STATUS = "local_pilot_learning_queue_v0"
SUPPORTED_LEARNING_PRIORITIES = ("P0", "P1", "P2", "P3")


@dataclass(frozen=True, slots=True)
class PilotLearningQueueItem:
    learning_id: str
    priority: str
    title: str
    reason: str
    source: str
    recommended_action: str

    def __post_init__(self) -> None:
        if self.priority not in SUPPORTED_LEARNING_PRIORITIES:
            raise ValueError("225P learning queue priority is unsupported.")
        if not all((self.learning_id, self.title, self.reason, self.source, self.recommended_action)):
            raise ValueError("225P learning queue items require id, title, reason, source, and action.")


@dataclass(frozen=True, slots=True)
class PilotLearningQueue:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    items: tuple[PilotLearningQueueItem, ...]
    total_items: int
    priority_counts: tuple[tuple[str, int], ...]
    fallback_status: str
    local_queue_only: bool
    external_ticket_created: bool
    backlog_write_allowed: bool
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
        if self.stage != PILOT_LEARNING_QUEUE_STAGE:
            raise ValueError("225P learning queues must identify the 225P stage.")
        if self.status != PILOT_LEARNING_QUEUE_STATUS:
            raise ValueError("225P learning queues must use the learning queue status.")
        if self.total_items != len(self.items):
            raise ValueError("225P learning queue count must match items.")
        if any(
            (
                not self.local_queue_only,
                self.external_ticket_created,
                self.backlog_write_allowed,
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("225P learning queues must remain local and must not expand external authority.")
        if not all((self.secrets_redacted, self.approval_gate_preserved, self.source_trace_preserved, self.usage_cost_preserved)):
            raise ValueError("225P learning queues must preserve redaction, approval, trace, and cost semantics.")


def build_pilot_learning_queue(
    *,
    owner_id: str,
    robot_id: str,
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    issue_receipts: tuple[PilotSupportIssueReceipt, ...] = (),
    safety_incidents: tuple[PilotSafetyIncident, ...] = (),
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
    review_packs: tuple[PilotReviewSessionPack, ...] = (),
) -> PilotLearningQueue:
    scoped_feedback = tuple(
        entry for entry in feedback_entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    scoped_issues = tuple(receipt for receipt in issue_receipts if receipt.owner_id == owner_id and receipt.robot_id == robot_id)
    scoped_safety = tuple(incident for incident in safety_incidents if incident.owner_id == owner_id and incident.robot_id == robot_id)
    scoped_reviews = tuple(pack for pack in review_packs if pack.owner_id == owner_id and pack.robot_id == robot_id)
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=usage_entries)
    items = _dedupe_items(
        (
            *_items_from_safety(scoped_safety),
            *_items_from_issues(scoped_issues),
            *_items_from_feedback(scoped_feedback),
            *_items_from_reviews(scoped_reviews),
            *_items_from_usage(usage_summary.failed_tasks, usage_summary.total_estimated_cost_usd),
        )
    )
    ordered = tuple(sorted(items, key=lambda item: (SUPPORTED_LEARNING_PRIORITIES.index(item.priority), item.learning_id)))
    return PilotLearningQueue(
        stage=PILOT_LEARNING_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_LEARNING_QUEUE_STATUS,
        items=ordered,
        total_items=len(ordered),
        priority_counts=_priority_counts(ordered),
        fallback_status="local_learning_signals_available" if ordered else "no_local_learning_signals_yet",
        local_queue_only=True,
        external_ticket_created=False,
        backlog_write_allowed=False,
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


def render_pilot_learning_queue(queue: PilotLearningQueue) -> str:
    lines = [
        "Pilot Learning Queue",
        "",
        f"Stage: {queue.stage}",
        f"Status: {queue.status}",
        f"Fallback: {queue.fallback_status}",
        f"Items: {queue.total_items}",
        "",
        "Priority counts:",
    ]
    lines.extend(f"- {priority}: {count}" for priority, count in queue.priority_counts)
    lines.extend(["", "Learning backlog:"])
    if queue.items:
        for item in queue.items:
            lines.extend(
                [
                    f"- {item.priority} {item.learning_id}: {item.title}",
                    f"  Reason: {item.reason}",
                    f"  Source: {item.source}",
                    f"  Action: {item.recommended_action}",
                ]
            )
    else:
        lines.append("- no_local_learning_signals_yet")
    lines.extend(
        [
            "",
            "Safety:",
            "- Local queue only: yes",
            "- External ticket: no",
            "- Backlog write: disabled",
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
    )
    return "\n".join(lines)


def _items_from_safety(incidents: tuple[PilotSafetyIncident, ...]) -> tuple[PilotLearningQueueItem, ...]:
    return tuple(
        PilotLearningQueueItem(
            learning_id=f"safety-{incident.incident_type}",
            priority="P0",
            title=f"Review safety block: {incident.incident_type}",
            reason=incident.reason,
            source=f"safety:{incident.incident_id}:{incident.source_trace_id}",
            recommended_action="Resolve or document the safety boundary before expanding pilot usage.",
        )
        for incident in incidents
    )


def _items_from_issues(issues: tuple[PilotSupportIssueReceipt, ...]) -> tuple[PilotLearningQueueItem, ...]:
    priority_by_severity = {"critical": "P0", "high": "P0", "medium": "P1", "low": "P2"}
    return tuple(
        PilotLearningQueueItem(
            learning_id=f"issue-{issue.category}-{issue.item_id}",
            priority=priority_by_severity[issue.severity],
            title=f"Fix pilot issue: {issue.category}",
            reason=issue.comment or f"{issue.command} on {issue.item_id}",
            source=f"issue:{issue.issue_id}:{issue.source_trace_id}",
            recommended_action="Triage the issue into the next local product patch before the next pilot session.",
        )
        for issue in issues
    )


def _items_from_feedback(entries: tuple[FeedbackLedgerEntry, ...]) -> tuple[PilotLearningQueueItem, ...]:
    negative_priority = {
        "missing_source": "P1",
        "bad_draft": "P1",
        "wrong": "P1",
        "stale": "P2",
        "noisy": "P2",
        "too_verbose": "P2",
        "not_useful": "P2",
    }
    return tuple(
        PilotLearningQueueItem(
            learning_id=f"feedback-{entry.tag}-{entry.item_type}",
            priority=negative_priority[entry.tag],
            title=f"Improve {entry.item_type} feedback: {entry.tag}",
            reason=entry.comment or f"{entry.tag} on {entry.item_id}",
            source=f"feedback:{entry.feedback_id}:{entry.source_trace_id}",
            recommended_action="Tune the affected product surface and verify with the next pilot review.",
        )
        for entry in entries
        if entry.tag in negative_priority
    )


def _items_from_reviews(reviews: tuple[PilotReviewSessionPack, ...]) -> tuple[PilotLearningQueueItem, ...]:
    items: list[PilotLearningQueueItem] = []
    for pack in reviews:
        for fix in pack.recommended_product_fixes:
            priority = fix.split(":", 1)[0] if ":" in fix else "P2"
            if priority not in SUPPORTED_LEARNING_PRIORITIES:
                priority = "P2"
            items.append(
                PilotLearningQueueItem(
                    learning_id=f"review-{_slug(pack.pilot_user_id)}-{_slug(fix)}",
                    priority=priority,
                    title="Apply pilot review learning",
                    reason=fix,
                    source=f"review:{pack.pilot_user_id}:{pack.fallback_status}",
                    recommended_action="Convert the review learning into a scoped local patch or explicitly defer it.",
                )
            )
    return tuple(items)


def _items_from_usage(failed_tasks: int, total_cost: float) -> tuple[PilotLearningQueueItem, ...]:
    items: list[PilotLearningQueueItem] = []
    if failed_tasks:
        items.append(
            PilotLearningQueueItem(
                learning_id="usage-failed-or-blocked",
                priority="P1",
                title="Investigate failed or blocked pilot tasks",
                reason=f"{failed_tasks} local usage task(s) failed or were blocked.",
                source="usage_cost_ledger:failed_tasks",
                recommended_action="Review the commands behind failed usage before increasing pilot load.",
            )
        )
    if total_cost >= 0.05:
        items.append(
            PilotLearningQueueItem(
                learning_id="usage-cost-watch",
                priority="P2",
                title="Review pilot cost trend",
                reason=f"Estimated local cost reached ${total_cost:.6f}.",
                source="usage_cost_ledger:estimated_cost",
                recommended_action="Check model routing or verbosity before inviting more users.",
            )
        )
    return tuple(items)


def _dedupe_items(items: tuple[PilotLearningQueueItem, ...]) -> tuple[PilotLearningQueueItem, ...]:
    by_id: dict[str, PilotLearningQueueItem] = {}
    for item in items:
        current = by_id.get(item.learning_id)
        if current is None or SUPPORTED_LEARNING_PRIORITIES.index(item.priority) < SUPPORTED_LEARNING_PRIORITIES.index(current.priority):
            by_id[item.learning_id] = item
    return tuple(by_id.values())


def _priority_counts(items: tuple[PilotLearningQueueItem, ...]) -> tuple[tuple[str, int], ...]:
    return tuple((priority, sum(1 for item in items if item.priority == priority)) for priority in SUPPORTED_LEARNING_PRIORITIES)


def _slug(value: str) -> str:
    safe = [character.lower() if character.isalnum() else "-" for character in value.strip()]
    compact = "-".join(part for part in "".join(safe).split("-") if part)
    return compact or "local"
