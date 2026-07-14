from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.token_usage_cost_meter import UsageTaskRunRecord


USAGE_COST_LEDGER_STAGE = "188P"
DEFAULT_LEDGER_MONTH = "2026-06"
LOCAL_LEDGER_BOUNDARY = "Local estimated usage ledger only. Not live billing or provider reconciliation."
LEDGER_STATUS_VALUES = frozenset({"estimated", "completed", "failed", "blocked"})
SECRET_REDACTION_LABEL = "[redacted]"
SECRET_MARKERS = (
    "authorization",
    "bearer",
    "refresh_token",
    "client_secret",
    "access_token",
    "api key",
    "secret",
    "token",
)


@dataclass(frozen=True, slots=True)
class UsageCostLedgerEntry:
    stage: str
    owner_id: str
    robot_id: str
    task_id: str
    command: str
    task_class: str
    provider: str
    model: str
    model_mode: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    status: str
    failure_reason: str | None
    source: str
    created_at: str
    local_estimate_only: bool
    live_billing_checked: bool
    provider_call_made: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    persistence_authorized: bool

    def __post_init__(self) -> None:
        if self.stage != USAGE_COST_LEDGER_STAGE:
            raise ValueError("188P usage ledger entries must identify the 188P stage.")
        if not self.owner_id or not self.robot_id or not self.task_id:
            raise ValueError("188P usage ledger entries require owner, robot, and task ids.")
        if self.status not in LEDGER_STATUS_VALUES:
            raise ValueError("188P usage ledger entry status must be known.")
        if self.status == "failed" and not self.failure_reason:
            raise ValueError("188P failed usage ledger entries must include a failure reason.")
        if min(self.input_tokens, self.output_tokens, self.latency_ms) < 0:
            raise ValueError("188P usage ledger token and latency values must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("188P usage ledger estimated cost must be non-negative.")
        if not self.local_estimate_only:
            raise ValueError("188P usage ledger entries must remain local estimates.")
        if any(
            (
                self.live_billing_checked,
                self.provider_call_made,
                self.connector_activation_allowed,
                self.external_write_allowed,
                self.persistence_authorized,
            )
        ):
            raise ValueError("188P usage ledger entries must not expand billing, provider, connector, persistence, or external authority.")


@dataclass(frozen=True, slots=True)
class UsageCostLedgerSummary:
    stage: str
    owner_id: str
    robot_id: str
    month: str
    total_tasks: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_estimated_cost_usd: float
    most_expensive_task_id: str | None
    most_expensive_task_cost_usd: float
    documents_reviewed: int
    failed_tasks: int
    command_breakdown: tuple[tuple[str, int], ...]
    task_class_breakdown: tuple[tuple[str, int], ...]
    model_mode_breakdown: tuple[tuple[str, int], ...]
    status_breakdown: tuple[tuple[str, int], ...]
    boundary: str
    live_billing_checked: bool
    provider_calls_made: bool
    external_write_allowed: bool
    persistence_authorized: bool

    def __post_init__(self) -> None:
        if self.stage != USAGE_COST_LEDGER_STAGE:
            raise ValueError("188P usage ledger summaries must identify the 188P stage.")
        if self.total_tokens != self.total_input_tokens + self.total_output_tokens:
            raise ValueError("188P usage ledger total tokens must match input plus output.")
        if self.total_tasks == 0 and self.most_expensive_task_id is not None:
            raise ValueError("188P empty usage ledger summaries must not name an expensive task.")
        if any(
            (
                self.live_billing_checked,
                self.provider_calls_made,
                self.external_write_allowed,
                self.persistence_authorized,
            )
        ):
            raise ValueError("188P usage ledger summaries must not expand authority.")


def build_usage_cost_ledger_entry(
    *,
    owner_id: str,
    robot_id: str,
    task_id: str,
    command: str,
    task_class: str,
    provider: str,
    model: str,
    model_mode: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
    latency_ms: int = 0,
    status: str = "estimated",
    failure_reason: str | None = None,
    source: str = "local_ledger_injected",
    created_at: str | None = None,
) -> UsageCostLedgerEntry:
    return UsageCostLedgerEntry(
        stage=USAGE_COST_LEDGER_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=_safe_text(task_id),
        command=_normalize_command(command),
        task_class=_safe_text(task_class),
        provider=_safe_text(provider),
        model=_safe_text(model),
        model_mode=_safe_text(model_mode),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=round(float(estimated_cost_usd), 6),
        latency_ms=latency_ms,
        status=status,
        failure_reason=_safe_optional_text(failure_reason),
        source=_safe_text(source),
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        local_estimate_only=True,
        live_billing_checked=False,
        provider_call_made=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        persistence_authorized=False,
    )


def build_usage_cost_ledger_entry_from_168p_record(
    *,
    command: str,
    record: UsageTaskRunRecord,
) -> UsageCostLedgerEntry:
    return build_usage_cost_ledger_entry(
        owner_id=record.owner_id,
        robot_id=record.robot_id,
        task_id=record.task_id,
        command=command,
        task_class=record.task_class,
        provider=record.provider,
        model=record.model,
        model_mode=record.model_mode,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        estimated_cost_usd=record.estimated_cost_usd,
        latency_ms=record.latency_ms,
        status=record.status,
        failure_reason=record.failure_reason,
        source=f"168p:{record.source}",
        created_at=record.created_at,
    )


def summarize_usage_cost_ledger(
    *,
    owner_id: str,
    robot_id: str,
    entries: tuple[UsageCostLedgerEntry, ...],
    month: str = DEFAULT_LEDGER_MONTH,
) -> UsageCostLedgerSummary:
    scoped = tuple(
        entry
        for entry in entries
        if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.created_at.startswith(month)
    )
    total_input = sum(entry.input_tokens for entry in scoped)
    total_output = sum(entry.output_tokens for entry in scoped)
    total_cost = round(sum(entry.estimated_cost_usd for entry in scoped), 6)
    most_expensive = max(scoped, key=lambda entry: (entry.estimated_cost_usd, entry.created_at), default=None)
    return UsageCostLedgerSummary(
        stage=USAGE_COST_LEDGER_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        month=month,
        total_tasks=len(scoped),
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_estimated_cost_usd=total_cost,
        most_expensive_task_id=most_expensive.task_id if most_expensive else None,
        most_expensive_task_cost_usd=round(most_expensive.estimated_cost_usd, 6) if most_expensive else 0.0,
        documents_reviewed=sum(1 for entry in scoped if entry.task_class in {"document_review", "long_context", "document_review_pack"}),
        failed_tasks=sum(1 for entry in scoped if entry.status in {"failed", "blocked"}),
        command_breakdown=_count_by(scoped, "command"),
        task_class_breakdown=_count_by(scoped, "task_class"),
        model_mode_breakdown=_count_by(scoped, "model_mode"),
        status_breakdown=_count_by(scoped, "status"),
        boundary=LOCAL_LEDGER_BOUNDARY,
        live_billing_checked=False,
        provider_calls_made=False,
        external_write_allowed=False,
        persistence_authorized=False,
    )


def render_usage_cost_ledger_summary(summary: UsageCostLedgerSummary) -> str:
    lines = [
        "Usage & Cost Ledger",
        "",
        f"Stage: {summary.stage}",
        f"Month: {summary.month}",
        f"Tasks run: {summary.total_tasks}",
        f"Estimated cost: ${summary.total_estimated_cost_usd:.6f}",
        f"Input tokens: {summary.total_input_tokens}",
        f"Output tokens: {summary.total_output_tokens}",
        f"Total tokens: {summary.total_tokens}",
        f"Documents reviewed: {summary.documents_reviewed}",
        f"Failures / blocked: {summary.failed_tasks}",
        f"Most expensive task: {_render_expensive_task(summary)}",
        "",
        "Commands:",
        *_render_breakdown(summary.command_breakdown),
        "",
        "Task classes:",
        *_render_breakdown(summary.task_class_breakdown),
        "",
        "Model mode:",
        *_render_breakdown(summary.model_mode_breakdown),
        "",
        "Status:",
        *_render_breakdown(summary.status_breakdown),
        "",
        summary.boundary,
        "Live billing: disabled",
        "Provider calls: disabled",
        "Persistence: disabled",
        "External writes: disabled",
    ]
    if summary.total_tasks == 0:
        lines.extend(
            [
                "",
                "No local usage records yet.",
                "Run product flows with injected local ledger entries to see usage here.",
            ]
        )
    return "\n".join(lines)


def _count_by(entries: tuple[UsageCostLedgerEntry, ...], attr: str) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        key = str(getattr(entry, attr))
        counts[key] = counts.get(key, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _render_breakdown(items: tuple[tuple[str, int], ...]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in items]


def _render_expensive_task(summary: UsageCostLedgerSummary) -> str:
    if not summary.most_expensive_task_id:
        return "none"
    return f"{summary.most_expensive_task_id} (${summary.most_expensive_task_cost_usd:.6f})"


def _normalize_command(value: str) -> str:
    safe = _safe_text(value)
    if not safe:
        return "unknown"
    return safe if safe.startswith("/") else f"/{safe}"


def _safe_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    safe = _safe_text(value)
    return safe or None


def _safe_text(value: str) -> str:
    compact = " ".join(str(value).split())
    lowered = compact.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        return SECRET_REDACTION_LABEL
    return compact[:240]
