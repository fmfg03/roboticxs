from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.config import Settings
from app.model_router import estimate_route


MODEL_ROUTER_RUNTIME_STAGE = "169P"
MODEL_ROUTER_MODES = ("economy", "balanced", "premium")
MODEL_ROUTER_TASK_CLASSES = (
    "SIMPLE_CLASSIFICATION",
    "EXTRACTION",
    "DRAFTING",
    "DOCUMENT_REVIEW",
    "SENSITIVE_REVIEW",
)
TASK_CLASS_TO_ROUTE_CLASS = {
    "SIMPLE_CLASSIFICATION": "SIMPLE_CLASSIFICATION",
    "EXTRACTION": "EXTRACTION",
    "DRAFTING": "DRAFTING",
    "DOCUMENT_REVIEW": "LONG_CONTEXT",
    "SENSITIVE_REVIEW": "SENSITIVE_REVIEW",
}
TASK_CLASS_TO_MODE = {
    "SIMPLE_CLASSIFICATION": "economy",
    "EXTRACTION": "economy",
    "DRAFTING": "balanced",
    "DOCUMENT_REVIEW": "balanced",
    "SENSITIVE_REVIEW": "premium",
}
TASK_CLASS_TO_REASON = {
    "SIMPLE_CLASSIFICATION": "Cheap deterministic classification work should use Economy.",
    "EXTRACTION": "Structured extraction can usually stay in Economy.",
    "DRAFTING": "Drafting needs stronger composition quality, so it uses Balanced.",
    "DOCUMENT_REVIEW": "Document review needs long-context handling, so it uses Balanced.",
    "SENSITIVE_REVIEW": "Sensitive review needs the strongest local tier and a boundary reminder.",
}


@dataclass(frozen=True, slots=True)
class ModelRouterRuntimeDecision:
    stage: str
    owner_id: str
    robot_id: str
    task_id: str
    task_class: str
    route_task_class: str
    mode: str
    provider: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    reason: str
    route_reason_json: str
    sensitive_boundary_required: bool
    long_context_required: bool
    local_estimate_only: bool
    provider_call_made: bool
    raw_provider_switching_allowed: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    billing_reconciliation_authorized: bool

    def __post_init__(self) -> None:
        if self.stage != MODEL_ROUTER_RUNTIME_STAGE:
            raise ValueError("169P model router decisions must identify the 169P stage.")
        if self.task_class not in MODEL_ROUTER_TASK_CLASSES:
            raise ValueError("169P model router task class must be known.")
        if self.mode not in MODEL_ROUTER_MODES:
            raise ValueError("169P model router mode must be Economy, Balanced, or Premium.")
        if self.mode != TASK_CLASS_TO_MODE[self.task_class]:
            raise ValueError("169P model router mode must match the task class policy.")
        if min(self.estimated_input_tokens, self.estimated_output_tokens) < 0:
            raise ValueError("169P model router token estimates must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("169P model router cost estimate must be non-negative.")
        if not self.local_estimate_only:
            raise ValueError("169P model router decisions must remain local estimates.")
        if any(
            (
                self.provider_call_made,
                self.raw_provider_switching_allowed,
                self.connector_activation_allowed,
                self.external_write_allowed,
                self.billing_reconciliation_authorized,
            )
        ):
            raise ValueError("169P model router decisions must not expand provider, billing, connector, or external authority.")


def route_model_for_task(
    *,
    owner_id: str,
    robot_id: str,
    task_id: str,
    task_class: str,
    text: str,
) -> ModelRouterRuntimeDecision:
    normalized_task_class = task_class.strip().upper()
    if normalized_task_class not in MODEL_ROUTER_TASK_CLASSES:
        raise ValueError("169P model router task class must be known.")
    mode = TASK_CLASS_TO_MODE[normalized_task_class]
    route_task_class = TASK_CLASS_TO_ROUTE_CLASS[normalized_task_class]
    route = estimate_route(
        text=text,
        task_id=task_id,
        task_family=normalized_task_class,
        task_class=route_task_class,
        settings=Settings(
            database_url="sqlite:////tmp/roboticxs-model-router-runtime.db",
            default_provider="local",
            default_model="local",
            default_routing_mode=mode,
        ),
    )
    reason = json.loads(str(route["reason"]))
    selected_mode = str(reason["selected_mode"])
    if selected_mode != mode:
        route = estimate_route(
            text=f"{mode} {text}",
            task_id=task_id,
            task_family=normalized_task_class,
            task_class=route_task_class,
            settings=Settings(
                database_url="sqlite:////tmp/roboticxs-model-router-runtime.db",
                default_provider="local",
                default_model="local",
                default_routing_mode=mode,
            ),
        )
    return ModelRouterRuntimeDecision(
        stage=MODEL_ROUTER_RUNTIME_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=task_id,
        task_class=normalized_task_class,
        route_task_class=route_task_class,
        mode=mode,
        provider=str(route["provider"]),
        model=str(route["model"]),
        estimated_input_tokens=int(route["estimated_input_tokens"]),
        estimated_output_tokens=int(route["estimated_output_tokens"]),
        estimated_cost_usd=float(route["estimated_cost_usd"]),
        reason=TASK_CLASS_TO_REASON[normalized_task_class],
        route_reason_json=str(route["reason"]),
        sensitive_boundary_required=normalized_task_class == "SENSITIVE_REVIEW",
        long_context_required=normalized_task_class == "DOCUMENT_REVIEW",
        local_estimate_only=True,
        provider_call_made=False,
        raw_provider_switching_allowed=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        billing_reconciliation_authorized=False,
    )


def render_model_router_decision(decision: ModelRouterRuntimeDecision) -> str:
    return "\n".join(
        [
            "Model Router",
            "",
            f"Stage: {decision.stage}",
            f"Task class: {decision.task_class}",
            f"Mode: {decision.mode.title()}",
            f"Provider/model: {decision.provider} / {decision.model}",
            f"Estimated tokens: {decision.estimated_input_tokens} in, {decision.estimated_output_tokens} out",
            f"Estimated cost: ${decision.estimated_cost_usd:.6f}",
            f"Why: {decision.reason}",
            "",
            "Provider calls: disabled",
            "Raw provider switching: disabled",
            "Connector activation: disabled",
            "External writes: disabled",
            "Billing reconciliation: disabled",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.model_router_runtime")
    parser.add_argument("task_class")
    parser.add_argument("text")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    decision = route_model_for_task(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id="local-route",
        task_class=args.task_class,
        text=args.text,
    )
    if args.as_json:
        print(json.dumps(asdict(decision), sort_keys=True, indent=2))
    else:
        print(render_model_router_decision(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
