from __future__ import annotations

from dataclasses import dataclass


DAILY_LOOP_OUTCOME_TRACKER_STAGE = "205P"
DAILY_LOOP_OUTCOME_TRACKER_STATUS = "tracked_daily_loop_outcome_v0"
SUPPORTED_DAILY_LOOP_OUTCOMES = (
    "no_action",
    "viewed",
    "suggestion_opened",
    "draft_created",
    "draft_approved",
    "memory_approved",
    "document_reviewed",
    "setup_issue_found",
    "blocked_by_missing_connector",
)


@dataclass(frozen=True, slots=True)
class DailyLoopOutcomeRecord:
    stage: str
    owner_id: str
    robot_id: str
    loop_id: str
    outcome: str
    note: str
    source_trace_id: str
    created_at: str
    status: str
    local_tracker_only: bool
    external_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != DAILY_LOOP_OUTCOME_TRACKER_STAGE:
            raise ValueError("205P daily loop outcomes must identify the 205P stage.")
        if self.status != DAILY_LOOP_OUTCOME_TRACKER_STATUS:
            raise ValueError("205P daily loop outcomes must use the tracker status.")
        if self.outcome not in SUPPORTED_DAILY_LOOP_OUTCOMES:
            raise ValueError("205P daily loop outcome is unsupported.")
        if not self.loop_id or not self.created_at:
            raise ValueError("205P daily loop outcomes require loop id and timestamp.")
        if not self.local_tracker_only or self.external_write_allowed:
            raise ValueError("205P daily loop outcomes must remain local only.")
        if self.gmail_send_allowed or self.calendar_write_allowed:
            raise ValueError("205P daily loop outcomes must not expand connector write authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("205P daily loop outcomes must be redacted and approval-preserving.")


def parse_daily_loop_outcome_argument(argument: str | None) -> tuple[str, str, str]:
    parts = (argument or "").strip().split(maxsplit=2)
    if len(parts) < 2:
        return "", "", ""
    loop_id = parts[0].strip()
    outcome = parts[1].strip().lower()
    note = parts[2].strip() if len(parts) == 3 else ""
    return loop_id, outcome, note


def build_daily_loop_outcome_record(
    *,
    owner_id: str,
    robot_id: str,
    loop_id: str,
    outcome: str,
    note: str = "",
    source_trace_id: str | None = None,
    created_at: str = "2026-06-30T00:00:00Z",
) -> DailyLoopOutcomeRecord:
    return DailyLoopOutcomeRecord(
        stage=DAILY_LOOP_OUTCOME_TRACKER_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        loop_id=loop_id.strip(),
        outcome=outcome.strip().lower(),
        note=_redact_note(note),
        source_trace_id=(source_trace_id or "source_trace_not_provided").strip() or "source_trace_not_provided",
        created_at=created_at,
        status=DAILY_LOOP_OUTCOME_TRACKER_STATUS,
        local_tracker_only=True,
        external_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_daily_loop_outcome_record(record: DailyLoopOutcomeRecord) -> str:
    lines = [
        "Daily Loop Outcome",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        "",
        f"Loop: {record.loop_id}",
        f"Outcome: {record.outcome}",
    ]
    if record.note:
        lines.append(f"Note: {record.note}")
    lines.extend(
        [
            f"Source trace: {record.source_trace_id}",
            f"Created: {record.created_at}",
            "",
            "Local tracker only: yes",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def render_daily_loop_outcome_usage() -> str:
    return "\n".join(
        [
            "Daily Loop Outcome",
            "",
            "Usage:",
            "- /founder_outcome <loop_id> <outcome> [note]",
            "",
            "Outcomes:",
            f"- {', '.join(SUPPORTED_DAILY_LOOP_OUTCOMES)}",
        ]
    )


def _redact_note(note: str) -> str:
    compact = " ".join(note.strip().split())
    if not compact:
        return ""
    lowered = compact.lower()
    if any(marker in lowered for marker in ("token", "secret", "password", "authorization:", "bearer ")):
        return "[redacted-sensitive-note]"
    return compact[:240]
