from __future__ import annotations

from dataclasses import dataclass


PROACTIVE_PRIORITY_ENGINE_STAGE = "194P"
PRIORITY_LEVELS = frozenset({"P0", "P1", "P2", "P3"})


@dataclass(frozen=True, slots=True)
class ProactivePriorityDecision:
    stage: str
    suggestion_id: str
    priority: str
    confidence: str
    reason_codes: tuple[str, ...]
    safe_next_action: str
    source_trace: tuple[str, ...]
    no_action_taken: bool
    live_send_allowed: bool
    execution_allowed: bool
    external_write_allowed: bool
    model_call_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != PROACTIVE_PRIORITY_ENGINE_STAGE:
            raise ValueError("194P priority decisions must identify the 194P stage.")
        if self.priority not in PRIORITY_LEVELS:
            raise ValueError("194P priority must be P0, P1, P2, or P3.")
        if self.confidence not in {"low", "medium", "high"}:
            raise ValueError("194P priority confidence must be supported.")
        if not self.reason_codes:
            raise ValueError("194P priority decisions require reason codes.")
        if not self.no_action_taken:
            raise ValueError("194P priority decisions must not take action.")
        if any((self.live_send_allowed, self.execution_allowed, self.external_write_allowed, self.model_call_allowed)):
            raise ValueError("194P priority decisions must not expand authority.")


def build_proactive_priority_decision(suggestion: object) -> ProactivePriorityDecision:
    trigger = str(getattr(suggestion, "trigger_type", ""))
    title = str(getattr(suggestion, "title", ""))
    summary = str(getattr(suggestion, "summary", getattr(suggestion, "suggestion_text", "")))
    source_refs = tuple(str(ref) for ref in getattr(suggestion, "source_refs", ()))
    priority, confidence, reasons = _classify(trigger=trigger, title=title, summary=summary, source_refs=source_refs)
    return ProactivePriorityDecision(
        stage=PROACTIVE_PRIORITY_ENGINE_STAGE,
        suggestion_id=str(getattr(suggestion, "suggestion_id", "")),
        priority=priority,
        confidence=confidence,
        reason_codes=reasons,
        safe_next_action=_safe_next_action(priority=priority, trigger=trigger),
        source_trace=source_refs,
        no_action_taken=True,
        live_send_allowed=False,
        execution_allowed=False,
        external_write_allowed=False,
        model_call_allowed=False,
    )


def render_proactive_priority_decision(decision: ProactivePriorityDecision) -> tuple[str, ...]:
    return (
        f"  priority: {decision.priority}",
        f"  priority confidence: {decision.confidence}",
        f"  priority reasons: {', '.join(decision.reason_codes)}",
        f"  safe next action: {decision.safe_next_action}",
        f"  priority source trace: {_source_trace(decision.source_trace)}",
    )


def _classify(*, trigger: str, title: str, summary: str, source_refs: tuple[str, ...]) -> tuple[str, str, tuple[str, ...]]:
    text = " ".join((trigger, title, summary, " ".join(source_refs))).lower()
    reasons: list[str] = []
    if "due" in text or "deadline" in text or "tomorrow" in text:
        reasons.append("time_sensitive")
    if "meeting" in text or "calendar" in text:
        reasons.append("meeting_related")
    if "follow" in text or "email" in text:
        reasons.append("follow_up_risk")
    if "pdf" in text or "document" in text or "contract" in text:
        reasons.append("document_context")
    if not reasons:
        reasons.append("low_signal")
    if {"time_sensitive", "meeting_related"}.issubset(reasons):
        return "P0", "high", tuple(reasons)
    if "time_sensitive" in reasons or "follow_up_risk" in reasons:
        return "P1", "high" if len(reasons) > 1 else "medium", tuple(reasons)
    if "meeting_related" in reasons or "document_context" in reasons:
        return "P2", "medium", tuple(reasons)
    return "P3", "low", tuple(reasons)


def _safe_next_action(*, priority: str, trigger: str) -> str:
    if priority in {"P0", "P1"}:
        return "Review now; choose an explicit owner-approved action if useful."
    if trigger == "email_thread_no_followup":
        return "Review before creating any owner-approved follow-up draft."
    return "Review when convenient; no action is automatic."


def _source_trace(source_refs: tuple[str, ...]) -> str:
    return ", ".join(source_refs) if source_refs else "none"
