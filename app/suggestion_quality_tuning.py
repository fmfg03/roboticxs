from __future__ import annotations

from dataclasses import dataclass

from app.daily_loop_outcome_tracker import DailyLoopOutcomeRecord
from app.feedback_ledger_tags import FeedbackLedgerEntry


SUGGESTION_QUALITY_TUNING_STAGE = "206P"
SUGGESTION_QUALITY_TUNING_STATUS = "local_suggestion_quality_tuning_v0"
NEGATIVE_SUGGESTION_TAGS = frozenset({"wrong", "noisy", "stale", "missing_source", "not_useful"})
POSITIVE_SUGGESTION_TAGS = frozenset({"useful"})


@dataclass(frozen=True, slots=True)
class SuggestionQualityDecision:
    suggestion_id: str
    action: str
    adjusted_priority: str
    adjusted_confidence: float
    reason_codes: tuple[str, ...]
    source_trace_id: str

    def __post_init__(self) -> None:
        if self.action not in {"promote", "keep", "downgrade", "suppress"}:
            raise ValueError("206P suggestion quality action is unsupported.")
        if self.adjusted_priority not in {"P0", "P1", "P2", "P3", "SUPPRESSED"}:
            raise ValueError("206P suggestion quality priority is unsupported.")
        if not 0 <= self.adjusted_confidence <= 1:
            raise ValueError("206P suggestion quality confidence must be bounded.")
        if not self.suggestion_id or not self.reason_codes:
            raise ValueError("206P suggestion quality decisions require id and reason codes.")


@dataclass(frozen=True, slots=True)
class SuggestionQualityTuningReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    decisions: tuple[SuggestionQualityDecision, ...]
    feedback_entries_used: int
    outcomes_used: int
    local_tuning_only: bool
    external_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != SUGGESTION_QUALITY_TUNING_STAGE:
            raise ValueError("206P suggestion quality reports must identify the 206P stage.")
        if self.status != SUGGESTION_QUALITY_TUNING_STATUS:
            raise ValueError("206P suggestion quality reports must use the tuning status.")
        if not self.local_tuning_only or self.external_write_allowed:
            raise ValueError("206P suggestion quality tuning must remain local only.")
        if self.gmail_send_allowed or self.calendar_write_allowed:
            raise ValueError("206P suggestion quality tuning must not expand connector write authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("206P suggestion quality tuning must be redacted and approval-preserving.")


def build_suggestion_quality_tuning_report(
    *,
    owner_id: str,
    robot_id: str,
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
    outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
) -> SuggestionQualityTuningReport:
    scoped_feedback = tuple(
        entry
        for entry in feedback_entries
        if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.item_type == "suggestion"
    )
    scoped_outcomes = tuple(
        outcome for outcome in outcome_records if outcome.owner_id == owner_id and outcome.robot_id == robot_id
    )
    by_suggestion: dict[str, list[FeedbackLedgerEntry]] = {}
    for entry in scoped_feedback:
        by_suggestion.setdefault(entry.item_id, []).append(entry)
    decisions = tuple(
        _decision_for_suggestion(suggestion_id=suggestion_id, entries=tuple(entries))
        for suggestion_id, entries in sorted(by_suggestion.items())
    )
    return SuggestionQualityTuningReport(
        stage=SUGGESTION_QUALITY_TUNING_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=SUGGESTION_QUALITY_TUNING_STATUS,
        decisions=decisions,
        feedback_entries_used=len(scoped_feedback),
        outcomes_used=len(scoped_outcomes),
        local_tuning_only=True,
        external_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_suggestion_quality_tuning_report(report: SuggestionQualityTuningReport) -> str:
    lines = [
        "Suggestion Quality Tuning",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        f"Feedback entries used: {report.feedback_entries_used}",
        f"Outcome records used: {report.outcomes_used}",
        "",
        "Decisions:",
    ]
    if report.decisions:
        for decision in report.decisions:
            lines.append(
                f"- {decision.suggestion_id}: {decision.action} -> {decision.adjusted_priority} "
                f"({', '.join(decision.reason_codes)}; source {decision.source_trace_id})"
            )
    else:
        lines.append("- No suggestion feedback injected yet; ranking unchanged.")
    lines.extend(
        [
            "",
            "Local tuning only: yes",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def _decision_for_suggestion(*, suggestion_id: str, entries: tuple[FeedbackLedgerEntry, ...]) -> SuggestionQualityDecision:
    tags = tuple(entry.tag for entry in entries)
    negative_count = sum(1 for tag in tags if tag in NEGATIVE_SUGGESTION_TAGS)
    positive_count = sum(1 for tag in tags if tag in POSITIVE_SUGGESTION_TAGS)
    source_trace_id = next((entry.source_trace_id for entry in entries if entry.source_trace_id), "source_trace_not_provided")
    if negative_count >= 2 or "wrong" in tags or "stale" in tags:
        return SuggestionQualityDecision(
            suggestion_id=suggestion_id,
            action="suppress",
            adjusted_priority="SUPPRESSED",
            adjusted_confidence=0.1,
            reason_codes=("negative_feedback", "stale_or_wrong_signal"),
            source_trace_id=source_trace_id,
        )
    if negative_count == 1:
        return SuggestionQualityDecision(
            suggestion_id=suggestion_id,
            action="downgrade",
            adjusted_priority="P3",
            adjusted_confidence=0.35,
            reason_codes=("negative_feedback",),
            source_trace_id=source_trace_id,
        )
    if positive_count:
        return SuggestionQualityDecision(
            suggestion_id=suggestion_id,
            action="promote",
            adjusted_priority="P1",
            adjusted_confidence=0.8,
            reason_codes=("positive_feedback",),
            source_trace_id=source_trace_id,
        )
    return SuggestionQualityDecision(
        suggestion_id=suggestion_id,
        action="keep",
        adjusted_priority="P2",
        adjusted_confidence=0.55,
        reason_codes=("no_quality_change",),
        source_trace_id=source_trace_id,
    )
