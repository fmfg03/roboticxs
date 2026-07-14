from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ModelRouteDecision, TokenUsageEvent


SPEND_COMMAND = "what did you spend"
TOKEN_USAGE_COMMAND = "show token usage"


@dataclass(slots=True)
class UsageSummary:
    total_estimated_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_usage_events: int
    provider_model_breakdown: list[dict[str, str | int | float]]
    task_family_breakdown: list[dict[str, str | int]]
    task_class_breakdown: list[dict[str, str | int]]
    highest_cost_routes: list[dict[str, str | float]]

    @property
    def is_empty(self) -> bool:
        return self.total_usage_events == 0


def is_spend_command(text: str) -> bool:
    return text.strip().lower() == SPEND_COMMAND


def is_token_usage_command(text: str) -> bool:
    return text.strip().lower() in {TOKEN_USAGE_COMMAND, "/usage", "usage", "show usage"}


def build_usage_summary(*, session: Session, user_id: str, robot_id: str) -> UsageSummary:
    events = session.scalars(
        select(TokenUsageEvent)
        .where(TokenUsageEvent.user_id == user_id, TokenUsageEvent.robot_id == robot_id)
        .order_by(TokenUsageEvent.created_at.desc())
    ).all()
    if not events:
        return UsageSummary(
            total_estimated_cost_usd=0.0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            total_usage_events=0,
            provider_model_breakdown=[],
            task_family_breakdown=[],
            task_class_breakdown=[],
            highest_cost_routes=[],
        )

    task_ids = [event.task_id for event in events]
    routes = session.scalars(
        select(ModelRouteDecision)
        .where(ModelRouteDecision.task_id.in_(task_ids))
        .order_by(ModelRouteDecision.created_at.desc())
    ).all()
    routes_by_task_id = {route.task_id: route for route in routes}

    provider_model_totals: dict[tuple[str, str], dict[str, str | int | float]] = defaultdict(
        lambda: {"events": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    )
    task_family_totals: dict[str, int] = defaultdict(int)
    task_class_totals: dict[str, int] = defaultdict(int)

    total_input_tokens = 0
    total_output_tokens = 0
    total_estimated_cost_usd = 0.0

    for event in events:
        total_input_tokens += event.input_tokens
        total_output_tokens += event.output_tokens
        total_estimated_cost_usd += event.estimated_cost_usd

        provider_key = (event.provider, event.model)
        provider_totals = provider_model_totals[provider_key]
        provider_totals["events"] += 1
        provider_totals["input_tokens"] += event.input_tokens
        provider_totals["output_tokens"] += event.output_tokens
        provider_totals["estimated_cost_usd"] += event.estimated_cost_usd

        route = routes_by_task_id.get(event.task_id)
        reason = _parse_route_reason(route.reason) if route is not None else {}
        task_family = reason.get("task_family", "UNKNOWN")
        task_class = reason.get("task_class", route.task_class if route is not None else "UNKNOWN")
        task_family_totals[str(task_family)] += 1
        task_class_totals[str(task_class)] += 1

    provider_model_breakdown = [
        {
            "provider": provider,
            "model": model,
            "events": int(values["events"]),
            "input_tokens": int(values["input_tokens"]),
            "output_tokens": int(values["output_tokens"]),
            "estimated_cost_usd": round(float(values["estimated_cost_usd"]), 6),
        }
        for (provider, model), values in sorted(
            provider_model_totals.items(),
            key=lambda item: (-float(item[1]["estimated_cost_usd"]), item[0][0], item[0][1]),
        )
    ]
    task_family_breakdown = [
        {"task_family": task_family, "events": count}
        for task_family, count in sorted(task_family_totals.items(), key=lambda item: (-item[1], item[0]))
    ]
    task_class_breakdown = [
        {"task_class": task_class, "events": count}
        for task_class, count in sorted(task_class_totals.items(), key=lambda item: (-item[1], item[0]))
    ]
    highest_cost_routes = _build_highest_cost_routes(routes)

    return UsageSummary(
        total_estimated_cost_usd=round(total_estimated_cost_usd, 6),
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_tokens=total_input_tokens + total_output_tokens,
        total_usage_events=len(events),
        provider_model_breakdown=provider_model_breakdown,
        task_family_breakdown=task_family_breakdown,
        task_class_breakdown=task_class_breakdown,
        highest_cost_routes=highest_cost_routes,
    )


def _build_highest_cost_routes(routes: list[ModelRouteDecision]) -> list[dict[str, str | float]]:
    highest_cost_routes = []
    for route in sorted(routes, key=lambda item: (-item.estimated_cost_usd, item.created_at), reverse=False)[:3]:
        reason = _parse_route_reason(route.reason)
        highest_cost_routes.append(
            {
                "task_id": route.task_id,
                "task_family": str(reason.get("task_family", "UNKNOWN")),
                "task_class": str(reason.get("task_class", route.task_class)),
                "provider": route.provider,
                "model": route.model,
                "estimated_cost_usd": round(route.estimated_cost_usd, 6),
            }
        )
    return highest_cost_routes


def _parse_route_reason(reason_text: str) -> dict[str, object]:
    try:
        parsed = json.loads(reason_text)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
