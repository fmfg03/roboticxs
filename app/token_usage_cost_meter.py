from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json

from app.cost_governor import CostPreflightResult, TaskCostRequest


TOKEN_USAGE_COST_METER_STAGE = "168P"
USAGE_STATUS_VALUES = ("estimated", "completed", "failed", "blocked")
DEFAULT_MONTH = "2026-06"
LOCAL_ESTIMATE_BOUNDARY = "Local estimated usage only. Not live billing or provider reconciliation."


@dataclass(frozen=True, slots=True)
class UsageTaskRunRecord:
    stage: str
    owner_id: str
    robot_id: str
    task_id: str
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
    created_at: str
    source: str
    boundary: str
    local_estimate_only: bool
    live_billing_checked: bool
    provider_call_made: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    persistence_authorized: bool
    billing_reconciliation_authorized: bool

    def __post_init__(self) -> None:
        if self.stage != TOKEN_USAGE_COST_METER_STAGE:
            raise ValueError("168P usage records must identify the 168P stage.")
        if self.status not in USAGE_STATUS_VALUES:
            raise ValueError("168P usage status must be known.")
        if self.status == "failed" and not self.failure_reason:
            raise ValueError("168P failed usage records must include a failure reason.")
        if min(self.input_tokens, self.output_tokens, self.latency_ms) < 0:
            raise ValueError("168P usage token and latency values must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("168P estimated cost must be non-negative.")
        if not self.local_estimate_only:
            raise ValueError("168P usage records must remain local estimates.")
        if any(
            (
                self.live_billing_checked,
                self.provider_call_made,
                self.connector_activation_allowed,
                self.external_write_allowed,
                self.persistence_authorized,
                self.billing_reconciliation_authorized,
            )
        ):
            raise ValueError("168P usage records must not expand billing, provider, persistence, or external authority.")


@dataclass(frozen=True, slots=True)
class UsageCostSummary:
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
    model_mode_breakdown: tuple[tuple[str, int], ...]
    task_class_breakdown: tuple[tuple[str, int], ...]
    boundary: str
    live_billing_checked: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != TOKEN_USAGE_COST_METER_STAGE:
            raise ValueError("168P usage summaries must identify the 168P stage.")
        if self.total_tokens != self.total_input_tokens + self.total_output_tokens:
            raise ValueError("168P usage summary total tokens must match input plus output.")
        if self.total_tasks == 0 and self.most_expensive_task_id is not None:
            raise ValueError("168P empty usage summaries must not name an expensive task.")
        if self.live_billing_checked or self.external_write_allowed:
            raise ValueError("168P usage summaries must not check billing or allow external writes.")


def is_usage_cost_meter_command(text: str) -> bool:
    return text.strip().lower() in {"/usage", "usage", "show usage"}


def build_usage_task_run_record(
    *,
    owner_id: str,
    robot_id: str,
    task_id: str,
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
    created_at: str | None = None,
    source: str = "local_meter",
) -> UsageTaskRunRecord:
    return UsageTaskRunRecord(
        stage=TOKEN_USAGE_COST_METER_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=task_id,
        task_class=task_class,
        provider=provider,
        model=model,
        model_mode=model_mode,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=round(float(estimated_cost_usd), 6),
        latency_ms=latency_ms,
        status=status,
        failure_reason=failure_reason,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        source=source,
        boundary=LOCAL_ESTIMATE_BOUNDARY,
        local_estimate_only=True,
        live_billing_checked=False,
        provider_call_made=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        persistence_authorized=False,
        billing_reconciliation_authorized=False,
    )


def build_usage_task_run_record_from_cost_preflight(
    *,
    request: TaskCostRequest,
    result: CostPreflightResult,
    latency_ms: int = 0,
    status: str | None = None,
    failure_reason: str | None = None,
    created_at: str | None = None,
) -> UsageTaskRunRecord:
    route = result.route_decision
    return build_usage_task_run_record(
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        task_id=request.request_id,
        task_class=request.task_class,
        provider=route.selected_provider_id if route and route.selected_provider_id else "local_unrouted",
        model=route.selected_model_id if route and route.selected_model_id else "unrouted",
        model_mode=request.routing_mode,
        input_tokens=result.token_estimate.estimated_input_tokens,
        output_tokens=result.token_estimate.estimated_output_tokens,
        estimated_cost_usd=result.estimated_cost_usd,
        latency_ms=latency_ms,
        status=status or ("blocked" if result.blocked else "estimated"),
        failure_reason=failure_reason or ("cost_preflight_blocked" if result.blocked else None),
        created_at=created_at,
        source="cost_preflight_100p",
    )


def summarize_usage_costs(
    *,
    owner_id: str,
    robot_id: str,
    records: tuple[UsageTaskRunRecord, ...],
    month: str = DEFAULT_MONTH,
) -> UsageCostSummary:
    scoped = tuple(
        record
        for record in records
        if record.owner_id == owner_id and record.robot_id == robot_id and record.created_at.startswith(month)
    )
    total_input = sum(record.input_tokens for record in scoped)
    total_output = sum(record.output_tokens for record in scoped)
    total_cost = round(sum(record.estimated_cost_usd for record in scoped), 6)
    most_expensive = max(scoped, key=lambda record: (record.estimated_cost_usd, record.created_at), default=None)
    return UsageCostSummary(
        stage=TOKEN_USAGE_COST_METER_STAGE,
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
        documents_reviewed=sum(1 for record in scoped if record.task_class in {"document_review", "long_context"}),
        model_mode_breakdown=_count_by(scoped, "model_mode"),
        task_class_breakdown=_count_by(scoped, "task_class"),
        boundary=LOCAL_ESTIMATE_BOUNDARY,
        live_billing_checked=False,
        external_write_allowed=False,
    )


def render_usage_cost_summary(summary: UsageCostSummary) -> str:
    lines = [
        "Usage this month",
        "",
        f"Stage: {summary.stage}",
        f"Month: {summary.month}",
        f"Tasks run: {summary.total_tasks}",
        f"Estimated cost: ${summary.total_estimated_cost_usd:.6f}",
        f"Input tokens: {summary.total_input_tokens}",
        f"Output tokens: {summary.total_output_tokens}",
        f"Total tokens: {summary.total_tokens}",
        f"Documents reviewed: {summary.documents_reviewed}",
        f"Most expensive task: {_render_expensive_task(summary)}",
        "",
        "Model mode:",
        *_render_breakdown(summary.model_mode_breakdown),
        "",
        "Task classes:",
        *_render_breakdown(summary.task_class_breakdown),
        "",
        summary.boundary,
        "Live billing: disabled",
        "Provider calls: disabled",
        "External writes: disabled",
    ]
    return "\n".join(lines)


def _count_by(records: tuple[UsageTaskRunRecord, ...], attr: str) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(getattr(record, attr))
        counts[key] = counts.get(key, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _render_breakdown(items: tuple[tuple[str, int], ...]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in items]


def _render_expensive_task(summary: UsageCostSummary) -> str:
    if not summary.most_expensive_task_id:
        return "none"
    return f"{summary.most_expensive_task_id} (${summary.most_expensive_task_cost_usd:.6f})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.token_usage_cost_meter")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    summary = summarize_usage_costs(owner_id="local-owner", robot_id="roboticxs-dev", records=(), month=DEFAULT_MONTH)
    if args.as_json:
        print(json.dumps(asdict(summary), sort_keys=True, indent=2))
    else:
        print(render_usage_cost_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
