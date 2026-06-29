from __future__ import annotations

from dataclasses import dataclass

from app.feedback_ledger_tags import FeedbackLedgerEntry


PREP_QUALITY_TUNING_STAGE = "207P"
PREP_QUALITY_TUNING_STATUS = "local_prep_quality_tuning_v0"
PREP_QUALITY_TAGS = frozenset(
    {"missing_context", "wrong_context", "weak_agenda", "bad_risk", "bad_next_step", "too_verbose", "not_actionable"}
)


@dataclass(frozen=True, slots=True)
class PrepQualityFinding:
    prep_id: str
    action: str
    reason_codes: tuple[str, ...]
    source_trace_id: str

    def __post_init__(self) -> None:
        if self.action not in {"keep", "tighten", "require_source_review", "rewrite_next_step", "block_stale_prep"}:
            raise ValueError("207P prep quality action is unsupported.")
        if not self.prep_id or not self.reason_codes:
            raise ValueError("207P prep quality findings require id and reasons.")


@dataclass(frozen=True, slots=True)
class PrepQualityTuningReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    findings: tuple[PrepQualityFinding, ...]
    feedback_entries_used: int
    local_tuning_only: bool
    external_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PREP_QUALITY_TUNING_STAGE:
            raise ValueError("207P prep quality reports must identify the 207P stage.")
        if self.status != PREP_QUALITY_TUNING_STATUS:
            raise ValueError("207P prep quality reports must use the tuning status.")
        if not self.local_tuning_only or self.external_write_allowed:
            raise ValueError("207P prep quality tuning must remain local only.")
        if self.gmail_send_allowed or self.calendar_write_allowed:
            raise ValueError("207P prep quality tuning must not expand connector write authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("207P prep quality tuning must be redacted and approval-preserving.")


def build_prep_quality_tuning_report(
    *,
    owner_id: str,
    robot_id: str,
    feedback_entries: tuple[FeedbackLedgerEntry, ...] = (),
) -> PrepQualityTuningReport:
    scoped = tuple(
        entry
        for entry in feedback_entries
        if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.item_type == "prep" and entry.tag in PREP_QUALITY_TAGS
    )
    by_prep: dict[str, list[FeedbackLedgerEntry]] = {}
    for entry in scoped:
        by_prep.setdefault(entry.item_id, []).append(entry)
    findings = tuple(_finding(prep_id=prep_id, entries=tuple(entries)) for prep_id, entries in sorted(by_prep.items()))
    return PrepQualityTuningReport(
        stage=PREP_QUALITY_TUNING_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PREP_QUALITY_TUNING_STATUS,
        findings=findings,
        feedback_entries_used=len(scoped),
        local_tuning_only=True,
        external_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_prep_quality_tuning_report(report: PrepQualityTuningReport) -> str:
    lines = [
        "Prep Quality Tuning",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        f"Feedback entries used: {report.feedback_entries_used}",
        "",
        "Findings:",
    ]
    if report.findings:
        lines.extend(
            f"- {finding.prep_id}: {finding.action} ({', '.join(finding.reason_codes)}; source {finding.source_trace_id})"
            for finding in report.findings
        )
    else:
        lines.append("- No prep quality feedback injected yet; prep output unchanged.")
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


def _finding(*, prep_id: str, entries: tuple[FeedbackLedgerEntry, ...]) -> PrepQualityFinding:
    tags = tuple(entry.tag for entry in entries)
    source_trace_id = next((entry.source_trace_id for entry in entries if entry.source_trace_id), "source_trace_not_provided")
    if "wrong_context" in tags:
        return PrepQualityFinding(prep_id, "block_stale_prep", ("wrong_context", "source_review_required"), source_trace_id)
    if "missing_context" in tags or "bad_risk" in tags:
        return PrepQualityFinding(prep_id, "require_source_review", tuple(sorted(set(tags))), source_trace_id)
    if "bad_next_step" in tags or "not_actionable" in tags:
        return PrepQualityFinding(prep_id, "rewrite_next_step", tuple(sorted(set(tags))), source_trace_id)
    if "weak_agenda" in tags or "too_verbose" in tags:
        return PrepQualityFinding(prep_id, "tighten", tuple(sorted(set(tags))), source_trace_id)
    return PrepQualityFinding(prep_id, "keep", ("no_quality_change",), source_trace_id)
