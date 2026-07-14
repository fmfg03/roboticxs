from __future__ import annotations

from dataclasses import dataclass

from app.model_router_runtime import ModelRouterRuntimeDecision, route_model_for_task
from app.usage_cost_ledger import UsageCostLedgerEntry, build_usage_cost_ledger_entry


COST_AWARE_MODEL_ROUTING_STAGE = "198P"
CUSTOMER_MODES = ("Economy", "Balanced", "Premium")
MODE_CONFIRMATION_THRESHOLDS_USD = {
    "economy": 0.002,
    "balanced": 0.01,
    "premium": 0.0,
}
TASK_CLASS_TO_COMMAND = {
    "SIMPLE_CLASSIFICATION": "/status",
    "EXTRACTION": "/context",
    "DRAFTING": "/draft",
    "DOCUMENT_REVIEW": "/document",
    "SENSITIVE_REVIEW": "/review",
}


@dataclass(frozen=True, slots=True)
class CostAwareRoutingReceipt:
    stage: str
    owner_id: str
    robot_id: str
    task_id: str
    command: str
    task_class: str
    customer_mode: str
    provider: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    confirmation_required: bool
    confirmation_reason: str
    source_trace: tuple[str, ...]
    routing_decision: ModelRouterRuntimeDecision
    ledger_entry: UsageCostLedgerEntry
    local_estimate_only: bool
    provider_call_made: bool
    external_write_allowed: bool
    live_billing_checked: bool
    connector_activation_allowed: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != COST_AWARE_MODEL_ROUTING_STAGE:
            raise ValueError("198P cost-aware routing receipts must identify the 198P stage.")
        if self.customer_mode not in CUSTOMER_MODES:
            raise ValueError("198P cost-aware routing mode must be Economy, Balanced, or Premium.")
        if self.routing_decision.task_id != self.task_id:
            raise ValueError("198P routing receipt must bind to the model router task id.")
        if self.ledger_entry.task_id != self.task_id:
            raise ValueError("198P routing receipt must bind to the usage ledger task id.")
        if self.ledger_entry.estimated_cost_usd != self.estimated_cost_usd:
            raise ValueError("198P routing receipt must preserve the ledger cost estimate.")
        if not self.source_trace:
            raise ValueError("198P routing receipt requires source trace.")
        if min(self.estimated_input_tokens, self.estimated_output_tokens) < 0:
            raise ValueError("198P routing token estimates must be non-negative.")
        if self.estimated_cost_usd < 0:
            raise ValueError("198P routing cost estimate must be non-negative.")
        if not self.local_estimate_only or not self.approval_gate_preserved:
            raise ValueError("198P routing must remain local and preserve approval semantics.")
        if any(
            (
                self.provider_call_made,
                self.external_write_allowed,
                self.live_billing_checked,
                self.connector_activation_allowed,
            )
        ):
            raise ValueError("198P routing must not expand provider, connector, billing, or external-write authority.")


def build_cost_aware_routing_receipt(
    *,
    owner_id: str,
    robot_id: str,
    task_id: str,
    task_class: str,
    text: str,
    command: str | None = None,
    source_trace: tuple[str, ...] = ("owner_request",),
    status: str = "estimated",
    created_at: str | None = None,
) -> CostAwareRoutingReceipt:
    routing = route_model_for_task(
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=task_id,
        task_class=task_class,
        text=text,
    )
    customer_mode = routing.mode.title()
    normalized_command = command or TASK_CLASS_TO_COMMAND[routing.task_class]
    estimate = round(routing.estimated_cost_usd, 6)
    confirmation_required, confirmation_reason = _confirmation_state(mode=routing.mode, estimated_cost_usd=estimate)
    ledger_entry = build_usage_cost_ledger_entry(
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=task_id,
        command=normalized_command,
        task_class=routing.task_class.lower(),
        provider=routing.provider,
        model=routing.model,
        model_mode=routing.mode,
        input_tokens=routing.estimated_input_tokens,
        output_tokens=routing.estimated_output_tokens,
        estimated_cost_usd=estimate,
        status=status,
        source="198p_cost_aware_router",
        created_at=created_at,
    )
    return CostAwareRoutingReceipt(
        stage=COST_AWARE_MODEL_ROUTING_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        task_id=task_id,
        command=normalized_command,
        task_class=routing.task_class,
        customer_mode=customer_mode,
        provider=routing.provider,
        model=routing.model,
        estimated_input_tokens=routing.estimated_input_tokens,
        estimated_output_tokens=routing.estimated_output_tokens,
        estimated_cost_usd=estimate,
        confirmation_required=confirmation_required,
        confirmation_reason=confirmation_reason,
        source_trace=tuple(_safe_trace_item(item) for item in source_trace if _safe_trace_item(item)),
        routing_decision=routing,
        ledger_entry=ledger_entry,
        local_estimate_only=True,
        provider_call_made=False,
        external_write_allowed=False,
        live_billing_checked=False,
        connector_activation_allowed=False,
        approval_gate_preserved=True,
    )


def render_cost_aware_routing_receipt(receipt: CostAwareRoutingReceipt) -> str:
    confirmation = "required" if receipt.confirmation_required else "not required"
    return "\n".join(
        [
            "Cost-Aware Model Routing",
            "",
            f"Stage: {receipt.stage}",
            f"Task: {receipt.task_id}",
            f"Command: {receipt.command}",
            f"Task class: {receipt.task_class}",
            f"Mode: {receipt.customer_mode}",
            f"Provider/model: {receipt.provider} / {receipt.model}",
            f"Estimated tokens: {receipt.estimated_input_tokens} in, {receipt.estimated_output_tokens} out",
            f"Estimated cost before run: ${receipt.estimated_cost_usd:.6f}",
            f"Confirmation: {confirmation} ({receipt.confirmation_reason})",
            f"Ledger source: {receipt.ledger_entry.source}",
            "Source trace:",
            *[f"- {item}" for item in receipt.source_trace],
            "",
            "Provider calls: disabled",
            "Live billing: disabled",
            "Connector activation: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
        ]
    )


def _confirmation_state(*, mode: str, estimated_cost_usd: float) -> tuple[bool, str]:
    if mode == "premium":
        return True, "premium_mode_requires_confirmation"
    threshold = MODE_CONFIRMATION_THRESHOLDS_USD[mode]
    if estimated_cost_usd > threshold:
        return True, "estimated_cost_above_mode_threshold"
    return False, "within_mode_threshold"


def _safe_trace_item(value: str) -> str:
    compact = " ".join(str(value).split())
    lowered = compact.lower()
    if any(marker in lowered for marker in ("authorization", "bearer", "client_secret", "access_token", "refresh_token", "secret-token")):
        return "[redacted]"
    return compact[:180]
