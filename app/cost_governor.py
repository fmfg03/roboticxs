from __future__ import annotations

from dataclasses import dataclass
from math import ceil


COST_GOVERNOR_STAGE = "100P"

TASK_CLASSES = frozenset(
    {
        "simple_classification",
        "extraction",
        "drafting",
        "research",
        "reasoning",
        "tool_planning",
        "sensitive_review",
        "long_context",
        "creative",
        "routine",
        "async_delegation",
    }
)
ROUTING_MODES = frozenset({"economy", "balanced", "premium", "byok"})
COST_DECISIONS = frozenset({"allow", "downgrade", "require_confirmation", "block"})
BUDGET_STATES = frozenset(
    {"within_budget", "near_limit", "confirmation_required", "over_budget", "policy_invalid"}
)
CAPABILITY_TIERS = frozenset({"basic", "standard", "advanced", "premium"})
TRUST_LEVELS = frozenset({"trusted", "constrained", "unsafe", "untrusted"})
AVAILABILITY_STATES = frozenset({"available", "unavailable"})
SENSITIVITY_CLASSES = frozenset(
    {"ordinary", "personal", "caregiver", "medical", "legal", "financial", "safety_critical"}
)
SENSITIVE_CLASSES = frozenset({"personal", "caregiver", "medical", "legal", "financial", "safety_critical"})
TIER_RANK = {"basic": 1, "standard": 2, "advanced": 3, "premium": 4}
TASK_CLASS_MIN_TIER = {
    "simple_classification": "basic",
    "extraction": "basic",
    "drafting": "basic",
    "research": "standard",
    "reasoning": "advanced",
    "tool_planning": "standard",
    "sensitive_review": "advanced",
    "long_context": "advanced",
    "creative": "basic",
    "routine": "standard",
    "async_delegation": "standard",
}
TASK_OUTPUT_FLOORS = {
    "simple_classification": 32,
    "extraction": 48,
    "drafting": 96,
    "research": 128,
    "reasoning": 192,
    "tool_planning": 96,
    "sensitive_review": 160,
    "long_context": 160,
    "creative": 128,
    "routine": 96,
    "async_delegation": 128,
}


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    policy_id: str
    owner_id: str
    robot_id: str
    routing_mode_allowlist: tuple[str, ...]
    default_routing_mode: str
    max_estimated_cost_usd: float
    confirmation_cost_usd: float
    max_input_tokens: int
    max_output_tokens: int
    long_context_confirmation_tokens: int
    byok_allowed: bool
    async_delegation_allowed: bool
    premium_allowed_without_confirmation: bool
    allowed_task_classes: tuple[str, ...]
    sensitive_task_min_tier: str
    unsafe_model_block: bool
    untrusted_model_block: bool
    requires_trace: bool

    def __post_init__(self) -> None:
        if not self.policy_id or not self.owner_id or not self.robot_id:
            raise ValueError("BudgetPolicy requires policy, owner, and robot identifiers.")
        if not self.routing_mode_allowlist or any(mode not in ROUTING_MODES for mode in self.routing_mode_allowlist):
            raise ValueError("BudgetPolicy requires a non-empty routing-mode allowlist.")
        if self.default_routing_mode not in self.routing_mode_allowlist:
            raise ValueError("BudgetPolicy default routing mode must be allowlisted.")
        if self.confirmation_cost_usd > self.max_estimated_cost_usd:
            raise ValueError("BudgetPolicy confirmation threshold must be below or equal to hard max.")
        if any(value <= 0 for value in (self.max_input_tokens, self.max_output_tokens, self.long_context_confirmation_tokens)):
            raise ValueError("BudgetPolicy token ceilings must be positive.")
        if any(task_class not in TASK_CLASSES for task_class in self.allowed_task_classes):
            raise ValueError("BudgetPolicy allowed task classes must be known.")
        if self.sensitive_task_min_tier not in CAPABILITY_TIERS:
            raise ValueError("BudgetPolicy sensitive task minimum tier must be known.")
        if not self.unsafe_model_block or not self.untrusted_model_block or not self.requires_trace:
            raise ValueError("100P policies must block unsafe and untrusted models and require trace output.")


@dataclass(frozen=True, slots=True)
class TaskCostRequest:
    request_id: str
    owner_id: str
    robot_id: str
    task_class: str
    routing_mode: str
    sensitivity: str
    requires_tools: bool
    requires_long_context: bool
    input_chars_estimate: int
    expected_output_chars: int
    context_item_count: int
    active_skill_id: str | None = None
    memory_context_used: bool = False
    routine_requested: bool = False
    async_delegation_requested: bool = False
    authority_expansion_requested: bool = False

    def __post_init__(self) -> None:
        if not self.request_id or not self.owner_id or not self.robot_id:
            raise ValueError("TaskCostRequest requires request, owner, and robot identifiers.")
        if self.sensitivity not in SENSITIVITY_CLASSES:
            raise ValueError("TaskCostRequest sensitivity must be known.")
        if min(
            self.input_chars_estimate,
            self.expected_output_chars,
            self.context_item_count,
        ) < 0:
            raise ValueError("TaskCostRequest estimates must be non-negative.")


@dataclass(frozen=True, slots=True)
class TokenUsageEstimate:
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_tokens: int
    estimation_basis: str
    long_context_applied: bool

    def __post_init__(self) -> None:
        if min(self.estimated_input_tokens, self.estimated_output_tokens, self.estimated_total_tokens) < 0:
            raise ValueError("TokenUsageEstimate values must be non-negative.")
        if self.estimated_total_tokens != self.estimated_input_tokens + self.estimated_output_tokens:
            raise ValueError("TokenUsageEstimate total tokens must equal input plus output.")


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    provider_id: str
    model_id: str
    display_name: str
    enabled: bool
    availability: str
    routing_modes: tuple[str, ...]
    task_classes: tuple[str, ...]
    max_context_tokens: int
    capability_tier: str
    trust_level: str
    safe_for_sensitive: bool
    supports_tools: bool
    supports_long_context: bool
    estimated_input_cost_per_1k_usd: float
    estimated_output_cost_per_1k_usd: float
    selection_priority: int

    def __post_init__(self) -> None:
        if not self.provider_id or not self.model_id or not self.display_name:
            raise ValueError("ModelCatalogEntry requires provider, model, and display name.")
        if self.availability not in AVAILABILITY_STATES:
            raise ValueError("ModelCatalogEntry availability must be known.")
        if any(mode not in ROUTING_MODES for mode in self.routing_modes):
            raise ValueError("ModelCatalogEntry routing modes must be known.")
        if any(task_class not in TASK_CLASSES for task_class in self.task_classes):
            raise ValueError("ModelCatalogEntry task classes must be known.")
        if self.capability_tier not in CAPABILITY_TIERS or self.trust_level not in TRUST_LEVELS:
            raise ValueError("ModelCatalogEntry capability tier and trust level must be known.")
        if self.max_context_tokens <= 0 or self.selection_priority < 0:
            raise ValueError("ModelCatalogEntry context limit and selection priority must be valid.")


@dataclass(frozen=True, slots=True)
class ModelRouteDecision:
    selected_provider_id: str | None
    selected_model_id: str | None
    selected_capability_tier: str | None
    selected_trust_level: str | None
    candidate_models_considered: tuple[str, ...]
    rejected_candidates: tuple[str, ...]
    downgrade_from_model_id: str | None
    decision_reason: str


@dataclass(frozen=True, slots=True)
class CostTraceRecord:
    request_id: str
    task_class: str
    routing_mode: str
    candidate_model_id: str | None
    decision: str
    reason_code: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    budget_state: str
    authority_expanded: bool = False
    tool_action_authorized: bool = False
    memory_access_expanded: bool = False
    external_effect_authorized: bool = False
    model_provider_access_authorized: bool = False

    def __post_init__(self) -> None:
        if self.decision not in COST_DECISIONS:
            raise ValueError("CostTraceRecord decision must be a known cost decision.")
        if self.budget_state not in BUDGET_STATES:
            raise ValueError("CostTraceRecord budget state must be known.")
        if any(
            (
                self.authority_expanded,
                self.tool_action_authorized,
                self.memory_access_expanded,
                self.external_effect_authorized,
                self.model_provider_access_authorized,
            )
        ):
            raise ValueError("100P traces must remain non-authority-expanding.")


@dataclass(frozen=True, slots=True)
class CostPreflightResult:
    request_id: str
    decision: str
    budget_policy_id: str | None
    token_estimate: TokenUsageEstimate
    route_decision: ModelRouteDecision | None
    estimated_cost_usd: float
    confirmation_required: bool
    blocked: bool
    trace: tuple[CostTraceRecord, ...]
    data_only: bool = True
    tool_action_authorization: bool = False
    permission_expansion_authorized: bool = False
    memory_access_authorized: bool = False
    external_effect_authorized: bool = False
    model_provider_access_authorized: bool = False
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.decision not in COST_DECISIONS:
            raise ValueError("CostPreflightResult decision must be known.")
        if self.blocked != (self.decision == "block"):
            raise ValueError("CostPreflightResult blocked flag must match decision.")
        if self.confirmation_required != (self.decision == "require_confirmation"):
            raise ValueError("CostPreflightResult confirmation flag must match decision.")
        if not self.data_only:
            raise ValueError("100P results must remain data-only.")
        if any(
            (
                self.tool_action_authorization,
                self.permission_expansion_authorized,
                self.memory_access_authorized,
                self.external_effect_authorized,
                self.model_provider_access_authorized,
                self.execution_authorized,
            )
        ):
            raise ValueError("100P results must not expand authority.")


def default_budget_policy(*, owner_id: str, robot_id: str) -> BudgetPolicy:
    return BudgetPolicy(
        policy_id="cost_governor_policy_100p_v0",
        owner_id=owner_id,
        robot_id=robot_id,
        routing_mode_allowlist=("economy", "balanced", "premium", "byok"),
        default_routing_mode="balanced",
        max_estimated_cost_usd=0.08,
        confirmation_cost_usd=0.02,
        max_input_tokens=4000,
        max_output_tokens=1800,
        long_context_confirmation_tokens=2400,
        byok_allowed=False,
        async_delegation_allowed=False,
        premium_allowed_without_confirmation=False,
        allowed_task_classes=tuple(sorted(TASK_CLASSES)),
        sensitive_task_min_tier="advanced",
        unsafe_model_block=True,
        untrusted_model_block=True,
        requires_trace=True,
    )


def default_model_catalog() -> tuple[ModelCatalogEntry, ...]:
    return (
        ModelCatalogEntry(
            provider_id="local_fixture",
            model_id="economy_basic_v1",
            display_name="Local Economy Basic",
            enabled=True,
            availability="available",
            routing_modes=("economy", "balanced"),
            task_classes=(
                "simple_classification",
                "extraction",
                "drafting",
                "creative",
                "routine",
            ),
            max_context_tokens=3200,
            capability_tier="basic",
            trust_level="trusted",
            safe_for_sensitive=False,
            supports_tools=False,
            supports_long_context=False,
            estimated_input_cost_per_1k_usd=0.0005,
            estimated_output_cost_per_1k_usd=0.0008,
            selection_priority=10,
        ),
        ModelCatalogEntry(
            provider_id="local_fixture",
            model_id="balanced_standard_v1",
            display_name="Local Balanced Standard",
            enabled=True,
            availability="available",
            routing_modes=("economy", "balanced", "premium"),
            task_classes=tuple(sorted(TASK_CLASSES - {"long_context"})),
            max_context_tokens=6000,
            capability_tier="standard",
            trust_level="trusted",
            safe_for_sensitive=True,
            supports_tools=True,
            supports_long_context=False,
            estimated_input_cost_per_1k_usd=0.0011,
            estimated_output_cost_per_1k_usd=0.0016,
            selection_priority=20,
        ),
        ModelCatalogEntry(
            provider_id="local_fixture",
            model_id="advanced_reasoning_v1",
            display_name="Local Advanced Reasoning",
            enabled=True,
            availability="available",
            routing_modes=("balanced", "premium"),
            task_classes=tuple(sorted(TASK_CLASSES)),
            max_context_tokens=12000,
            capability_tier="advanced",
            trust_level="trusted",
            safe_for_sensitive=True,
            supports_tools=True,
            supports_long_context=True,
            estimated_input_cost_per_1k_usd=0.0022,
            estimated_output_cost_per_1k_usd=0.0031,
            selection_priority=30,
        ),
        ModelCatalogEntry(
            provider_id="local_fixture",
            model_id="premium_strong_v1",
            display_name="Local Premium Strong",
            enabled=True,
            availability="available",
            routing_modes=("premium",),
            task_classes=tuple(sorted(TASK_CLASSES)),
            max_context_tokens=16000,
            capability_tier="premium",
            trust_level="trusted",
            safe_for_sensitive=True,
            supports_tools=True,
            supports_long_context=True,
            estimated_input_cost_per_1k_usd=0.0045,
            estimated_output_cost_per_1k_usd=0.0065,
            selection_priority=40,
        ),
        ModelCatalogEntry(
            provider_id="local_byok_placeholder",
            model_id="byok_placeholder_v1",
            display_name="Local BYOK Placeholder",
            enabled=True,
            availability="available",
            routing_modes=("byok",),
            task_classes=tuple(sorted(TASK_CLASSES)),
            max_context_tokens=12000,
            capability_tier="advanced",
            trust_level="trusted",
            safe_for_sensitive=True,
            supports_tools=True,
            supports_long_context=True,
            estimated_input_cost_per_1k_usd=0.003,
            estimated_output_cost_per_1k_usd=0.004,
            selection_priority=50,
        ),
    )


def build_task_cost_request(
    *,
    request_id: str,
    owner_id: str,
    robot_id: str,
    text: str,
    memory_context_used: bool = False,
    context_item_count: int = 0,
    active_skill_id: str | None = None,
    routine_requested: bool = False,
) -> TaskCostRequest:
    normalized = text.strip().lower()
    routing_mode = _routing_mode_from_text(normalized)
    task_class = _task_class_from_text(normalized, routine_requested=routine_requested)
    sensitivity = _sensitivity_from_text(normalized)
    return TaskCostRequest(
        request_id=request_id,
        owner_id=owner_id,
        robot_id=robot_id,
        task_class=task_class,
        routing_mode=routing_mode,
        sensitivity=sensitivity,
        requires_tools=_contains_any(
            normalized,
            ("tool", "tools", "plan", "steps", "workflow", "crm", "email", "browser"),
        ),
        requires_long_context="long context" in normalized or len(normalized) > 6000,
        input_chars_estimate=max(len(text), 1),
        expected_output_chars=_expected_output_chars_for_text(normalized),
        context_item_count=context_item_count,
        active_skill_id=active_skill_id,
        memory_context_used=memory_context_used,
        routine_requested=routine_requested,
        async_delegation_requested="async delegation" in normalized or "delegate async" in normalized,
        authority_expansion_requested=_contains_any(
            normalized,
            ("grant permission", "bypass policy", "skip approval", "override budget", "authorize tools"),
        ),
    )


def estimate_token_usage(request: TaskCostRequest) -> TokenUsageEstimate:
    input_tokens = max(ceil(request.input_chars_estimate / 4), 1)
    output_floor = TASK_OUTPUT_FLOORS.get(request.task_class, 48)
    output_tokens = max(ceil(request.expected_output_chars / 4), output_floor)
    long_context_applied = request.requires_long_context or request.task_class == "long_context"
    if long_context_applied:
        input_tokens += min(512, 64 + (request.context_item_count * 24))
    return TokenUsageEstimate(
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_total_tokens=input_tokens + output_tokens,
        estimation_basis="char_ratio_fixture_v0",
        long_context_applied=long_context_applied,
    )


def evaluate_cost_preflight(
    *,
    request: TaskCostRequest,
    budget_policy: BudgetPolicy | object | None,
    model_catalog: tuple[ModelCatalogEntry, ...] | None = None,
) -> CostPreflightResult:
    token_estimate = estimate_token_usage(request)
    catalog = tuple(model_catalog or default_model_catalog())

    invalid_policy_result = _invalid_policy_result(request=request, token_estimate=token_estimate)
    if not isinstance(budget_policy, BudgetPolicy):
        return invalid_policy_result

    try:
        budget_policy.__post_init__()
    except ValueError:
        return invalid_policy_result

    if request.task_class not in TASK_CLASSES:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_unknown_task_class",
            budget_state="policy_invalid",
        )
    if request.routing_mode not in ROUTING_MODES:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_unknown_routing_mode",
            budget_state="policy_invalid",
        )
    if request.authority_expansion_requested:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_authority_expansion_attempt",
            budget_state="policy_invalid",
        )
    if request.task_class not in budget_policy.allowed_task_classes:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_task_class_not_allowed",
            budget_state="policy_invalid",
        )
    if request.routing_mode not in budget_policy.routing_mode_allowlist:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_routing_mode_not_allowed",
            budget_state="policy_invalid",
        )
    if request.routing_mode == "byok" and not budget_policy.byok_allowed:
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code="blocked_byok_not_allowed",
            budget_state="policy_invalid",
        )
    if token_estimate.estimated_input_tokens > budget_policy.max_input_tokens or token_estimate.estimated_output_tokens > budget_policy.max_output_tokens:
        reason = "blocked_long_context_limit" if request.requires_long_context else "blocked_over_budget"
        return _blocked_result(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            estimated_cost_usd=0.0,
            route_decision=None,
            reason_code=reason,
            budget_state="over_budget",
        )

    candidate_evaluations = _evaluate_candidates(
        request=request,
        budget_policy=budget_policy,
        token_estimate=token_estimate,
        catalog=catalog,
    )
    eligible = [candidate for candidate in candidate_evaluations if candidate["eligible"]]
    rejected_ids = tuple(candidate["entry"].model_id for candidate in candidate_evaluations if not candidate["eligible"])
    considered_ids = tuple(candidate["entry"].model_id for candidate in candidate_evaluations)
    traces = tuple(candidate["trace"] for candidate in candidate_evaluations)

    if not eligible:
        return CostPreflightResult(
            request_id=request.request_id,
            decision="block",
            budget_policy_id=budget_policy.policy_id,
            token_estimate=token_estimate,
            route_decision=ModelRouteDecision(
                selected_provider_id=None,
                selected_model_id=None,
                selected_capability_tier=None,
                selected_trust_level=None,
                candidate_models_considered=considered_ids,
                rejected_candidates=rejected_ids,
                downgrade_from_model_id=None,
                decision_reason="blocked_no_eligible_model",
            ),
            estimated_cost_usd=0.0,
            confirmation_required=False,
            blocked=True,
            trace=traces
            + (
                _trace(
                    request=request,
                    decision="block",
                    reason_code="blocked_no_eligible_model",
                    token_estimate=token_estimate,
                    estimated_cost_usd=0.0,
                    budget_state="over_budget",
                ),
            ),
        )

    selected = _select_candidate(
        request=request,
        budget_policy=budget_policy,
        eligible=eligible,
    )
    selected_entry = selected["entry"]
    selected_cost = float(selected["estimated_cost_usd"])
    downgrade_from_model_id = selected.get("downgrade_from_model_id")
    route_decision = ModelRouteDecision(
        selected_provider_id=selected_entry.provider_id,
        selected_model_id=selected_entry.model_id,
        selected_capability_tier=selected_entry.capability_tier,
        selected_trust_level=selected_entry.trust_level,
        candidate_models_considered=considered_ids,
        rejected_candidates=rejected_ids,
        downgrade_from_model_id=downgrade_from_model_id,
        decision_reason=str(selected["reason_code"]),
    )

    if selected_cost > budget_policy.max_estimated_cost_usd:
        return CostPreflightResult(
            request_id=request.request_id,
            decision="block",
            budget_policy_id=budget_policy.policy_id,
            token_estimate=token_estimate,
            route_decision=route_decision,
            estimated_cost_usd=selected_cost,
            confirmation_required=False,
            blocked=True,
            trace=traces
            + (
                _trace(
                    request=request,
                    decision="block",
                    reason_code="blocked_over_budget",
                    token_estimate=token_estimate,
                    estimated_cost_usd=selected_cost,
                    budget_state="over_budget",
                ),
            ),
        )

    confirmation_needed = False
    confirmation_reason = "confirmation_cost_threshold"
    if request.requires_long_context and token_estimate.estimated_total_tokens > budget_policy.long_context_confirmation_tokens:
        confirmation_needed = True
        confirmation_reason = "confirmation_long_context_threshold"
    elif request.routing_mode == "premium" and not budget_policy.premium_allowed_without_confirmation and downgrade_from_model_id is None:
        confirmation_needed = True
        confirmation_reason = "confirmation_premium_route_requires_approval"
    elif selected_cost > budget_policy.confirmation_cost_usd:
        confirmation_needed = True

    if selected_entry.safe_for_sensitive is False and _is_sensitive_request(request):
        return CostPreflightResult(
            request_id=request.request_id,
            decision="block",
            budget_policy_id=budget_policy.policy_id,
            token_estimate=token_estimate,
            route_decision=route_decision,
            estimated_cost_usd=selected_cost,
            confirmation_required=False,
            blocked=True,
            trace=traces
            + (
                _trace(
                    request=request,
                    decision="block",
                    reason_code="blocked_sensitive_candidate_policy",
                    token_estimate=token_estimate,
                    estimated_cost_usd=selected_cost,
                    budget_state="over_budget",
                ),
            ),
        )

    if request.task_class == "async_delegation":
        confirmation_needed = True
        confirmation_reason = "blocked_async_without_cost_preflight"

    if confirmation_needed:
        return CostPreflightResult(
            request_id=request.request_id,
            decision="require_confirmation",
            budget_policy_id=budget_policy.policy_id,
            token_estimate=token_estimate,
            route_decision=route_decision,
            estimated_cost_usd=selected_cost,
            confirmation_required=True,
            blocked=False,
            trace=traces
            + (
                _trace(
                    request=request,
                    decision="require_confirmation",
                    reason_code=confirmation_reason,
                    token_estimate=token_estimate,
                    estimated_cost_usd=selected_cost,
                    budget_state="confirmation_required",
                ),
            ),
        )

    final_decision = "downgrade" if downgrade_from_model_id is not None else "allow"
    final_reason = "downgrade_cheapest_adequate_route" if final_decision == "downgrade" else "allow_selected_eligible_route"
    return CostPreflightResult(
        request_id=request.request_id,
        decision=final_decision,
        budget_policy_id=budget_policy.policy_id,
        token_estimate=token_estimate,
        route_decision=route_decision,
        estimated_cost_usd=selected_cost,
        confirmation_required=False,
        blocked=False,
        trace=traces
        + (
            _trace(
                request=request,
                decision=final_decision,
                reason_code=final_reason,
                token_estimate=token_estimate,
                estimated_cost_usd=selected_cost,
                budget_state="within_budget",
            ),
        ),
    )


def can_dispatch_async_delegation(preflight_result: CostPreflightResult | None) -> bool:
    return bool(
        preflight_result is not None
        and preflight_result.decision == "allow"
        and preflight_result.execution_authorized
        and preflight_result.route_decision is not None
    )


def serialize_cost_preflight_result(result: CostPreflightResult | None) -> dict[str, object] | None:
    if result is None:
        return None
    return {
        "request_id": result.request_id,
        "decision": result.decision,
        "budget_policy_id": result.budget_policy_id,
        "token_estimate": {
            "estimated_input_tokens": result.token_estimate.estimated_input_tokens,
            "estimated_output_tokens": result.token_estimate.estimated_output_tokens,
            "estimated_total_tokens": result.token_estimate.estimated_total_tokens,
            "estimation_basis": result.token_estimate.estimation_basis,
            "long_context_applied": result.token_estimate.long_context_applied,
        },
        "route_decision": None
        if result.route_decision is None
        else {
            "selected_provider_id": result.route_decision.selected_provider_id,
            "selected_model_id": result.route_decision.selected_model_id,
            "selected_capability_tier": result.route_decision.selected_capability_tier,
            "selected_trust_level": result.route_decision.selected_trust_level,
            "candidate_models_considered": list(result.route_decision.candidate_models_considered),
            "rejected_candidates": list(result.route_decision.rejected_candidates),
            "downgrade_from_model_id": result.route_decision.downgrade_from_model_id,
            "decision_reason": result.route_decision.decision_reason,
        },
        "estimated_cost_usd": result.estimated_cost_usd,
        "confirmation_required": result.confirmation_required,
        "blocked": result.blocked,
        "data_only": result.data_only,
        "tool_action_authorization": result.tool_action_authorization,
        "permission_expansion_authorized": result.permission_expansion_authorized,
        "memory_access_authorized": result.memory_access_authorized,
        "external_effect_authorized": result.external_effect_authorized,
        "model_provider_access_authorized": result.model_provider_access_authorized,
        "execution_authorized": result.execution_authorized,
        "trace": [
            {
                "request_id": trace.request_id,
                "task_class": trace.task_class,
                "routing_mode": trace.routing_mode,
                "candidate_model_id": trace.candidate_model_id,
                "decision": trace.decision,
                "reason_code": trace.reason_code,
                "estimated_input_tokens": trace.estimated_input_tokens,
                "estimated_output_tokens": trace.estimated_output_tokens,
                "estimated_cost_usd": trace.estimated_cost_usd,
                "budget_state": trace.budget_state,
                "authority_expanded": trace.authority_expanded,
                "tool_action_authorized": trace.tool_action_authorized,
                "memory_access_expanded": trace.memory_access_expanded,
                "external_effect_authorized": trace.external_effect_authorized,
                "model_provider_access_authorized": trace.model_provider_access_authorized,
            }
            for trace in result.trace
        ],
    }


def _evaluate_candidates(
    *,
    request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    token_estimate: TokenUsageEstimate,
    catalog: tuple[ModelCatalogEntry, ...],
) -> list[dict[str, object]]:
    evaluations: list[dict[str, object]] = []
    required_tier = _required_capability_tier(request=request, budget_policy=budget_policy)
    for entry in sorted(catalog, key=lambda item: (item.selection_priority, item.provider_id, item.model_id)):
        estimated_cost_usd = _estimate_cost_for_entry(entry=entry, token_estimate=token_estimate)
        rejection = _candidate_rejection_reason(
            request=request,
            budget_policy=budget_policy,
            token_estimate=token_estimate,
            entry=entry,
            required_tier=required_tier,
        )
        evaluations.append(
            {
                "entry": entry,
                "estimated_cost_usd": estimated_cost_usd,
                "eligible": rejection is None,
                "trace": _trace(
                    request=request,
                    decision="allow" if rejection is None else "block",
                    reason_code="candidate_eligible" if rejection is None else rejection,
                    token_estimate=token_estimate,
                    estimated_cost_usd=estimated_cost_usd,
                    budget_state="within_budget" if rejection is None else "over_budget",
                    candidate_model_id=entry.model_id,
                ),
            }
        )
    return evaluations


def _select_candidate(
    *,
    request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    eligible: list[dict[str, object]],
) -> dict[str, object]:
    if request.routing_mode == "economy":
        selected = min(eligible, key=_economy_sort_key)
        selected["reason_code"] = "economy_cheapest_adequate_route"
        return selected
    if request.routing_mode == "balanced":
        selected = min(eligible, key=_balanced_sort_key)
        selected["reason_code"] = "balanced_cheapest_adequate_route"
        return selected
    if request.routing_mode == "byok":
        selected = min(eligible, key=_economy_sort_key)
        selected["reason_code"] = "byok_local_placeholder_route"
        return selected

    strongest = min(eligible, key=_premium_sort_key)
    if budget_policy.premium_allowed_without_confirmation:
        strongest["reason_code"] = "premium_strongest_allowed_route"
        return strongest

    affordable = [
        candidate
        for candidate in eligible
        if float(candidate["estimated_cost_usd"]) <= budget_policy.confirmation_cost_usd
    ]
    if affordable:
        downgraded = min(affordable, key=_economy_sort_key)
        if downgraded["entry"].model_id != strongest["entry"].model_id:
            downgraded["reason_code"] = "downgrade_cheapest_adequate_route"
            downgraded["downgrade_from_model_id"] = strongest["entry"].model_id
            return downgraded
    strongest["reason_code"] = "premium_strongest_allowed_route"
    return strongest


def _candidate_rejection_reason(
    *,
    request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    token_estimate: TokenUsageEstimate,
    entry: ModelCatalogEntry,
    required_tier: str,
) -> str | None:
    if not entry.enabled:
        return "candidate_disabled"
    if entry.availability != "available":
        return "candidate_unavailable"
    if request.routing_mode not in entry.routing_modes:
        return "candidate_routing_mode_unsupported"
    if request.task_class not in entry.task_classes:
        return "candidate_task_class_unsupported"
    if token_estimate.estimated_total_tokens > entry.max_context_tokens:
        return "candidate_context_limit_exceeded"
    if request.requires_long_context and not entry.supports_long_context:
        return "candidate_requires_long_context_support"
    if request.requires_tools and not entry.supports_tools:
        return "candidate_requires_tool_support"
    if TIER_RANK[entry.capability_tier] < TIER_RANK[required_tier]:
        return "candidate_below_required_capability_tier"
    if _is_sensitive_request(request):
        if budget_policy.unsafe_model_block and entry.trust_level == "unsafe":
            return "candidate_sensitive_unsafe"
        if budget_policy.untrusted_model_block and entry.trust_level == "untrusted":
            return "candidate_sensitive_untrusted"
        if not entry.safe_for_sensitive:
            return "candidate_sensitive_not_safe"
    return None


def _required_capability_tier(*, request: TaskCostRequest, budget_policy: BudgetPolicy) -> str:
    required = TASK_CLASS_MIN_TIER.get(request.task_class, "standard")
    if request.routing_mode == "balanced":
        required = _max_tier(required, "standard")
    elif request.routing_mode == "byok":
        required = _max_tier(required, "advanced")
    if _is_sensitive_request(request):
        required = _max_tier(required, budget_policy.sensitive_task_min_tier)
    return required


def _is_sensitive_request(request: TaskCostRequest) -> bool:
    return request.task_class == "sensitive_review" or request.sensitivity in SENSITIVE_CLASSES


def _estimate_cost_for_entry(*, entry: ModelCatalogEntry, token_estimate: TokenUsageEstimate) -> float:
    input_cost = (token_estimate.estimated_input_tokens / 1000.0) * entry.estimated_input_cost_per_1k_usd
    output_cost = (token_estimate.estimated_output_tokens / 1000.0) * entry.estimated_output_cost_per_1k_usd
    return round(input_cost + output_cost, 6)


def _blocked_result(
    *,
    request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    token_estimate: TokenUsageEstimate,
    estimated_cost_usd: float,
    route_decision: ModelRouteDecision | None,
    reason_code: str,
    budget_state: str,
) -> CostPreflightResult:
    return CostPreflightResult(
        request_id=request.request_id,
        decision="block",
        budget_policy_id=budget_policy.policy_id,
        token_estimate=token_estimate,
        route_decision=route_decision,
        estimated_cost_usd=estimated_cost_usd,
        confirmation_required=False,
        blocked=True,
        trace=(
            _trace(
                request=request,
                decision="block",
                reason_code=reason_code,
                token_estimate=token_estimate,
                estimated_cost_usd=estimated_cost_usd,
                budget_state=budget_state,
            ),
        ),
    )


def _invalid_policy_result(*, request: TaskCostRequest, token_estimate: TokenUsageEstimate) -> CostPreflightResult:
    return CostPreflightResult(
        request_id=request.request_id,
        decision="block",
        budget_policy_id=None,
        token_estimate=token_estimate,
        route_decision=None,
        estimated_cost_usd=0.0,
        confirmation_required=False,
        blocked=True,
        trace=(
            _trace(
                request=request,
                decision="block",
                reason_code="blocked_invalid_budget_policy",
                token_estimate=token_estimate,
                estimated_cost_usd=0.0,
                budget_state="policy_invalid",
            ),
        ),
    )


def _trace(
    *,
    request: TaskCostRequest,
    decision: str,
    reason_code: str,
    token_estimate: TokenUsageEstimate,
    estimated_cost_usd: float,
    budget_state: str,
    candidate_model_id: str | None = None,
) -> CostTraceRecord:
    return CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=candidate_model_id,
        decision=decision,
        reason_code=reason_code,
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        budget_state=budget_state,
    )


def _expected_output_chars_for_text(text: str) -> int:
    if _contains_any(text, ("research", "reason", "analyze", "analysis", "long context")):
        return 720
    if _contains_any(text, ("draft", "summary", "write", "creative")):
        return 520
    return 240


def _routing_mode_from_text(text: str) -> str:
    if "byok" in text:
        return "byok"
    if "premium" in text:
        return "premium"
    if "economy" in text:
        return "economy"
    return "balanced"


def _task_class_from_text(text: str, *, routine_requested: bool) -> str:
    if routine_requested:
        return "routine"
    if "async delegation" in text or "delegate async" in text:
        return "async_delegation"
    if "long context" in text:
        return "long_context"
    if _contains_any(text, ("sensitive review", "policy review", "caregiver review")):
        return "sensitive_review"
    if _contains_any(text, ("reason", "analysis", "analyze")):
        return "reasoning"
    if "research" in text:
        return "research"
    if _contains_any(text, ("plan", "workflow", "steps", "tool")):
        return "tool_planning"
    if _contains_any(text, ("classify", "classification")):
        return "simple_classification"
    if _contains_any(text, ("extract", "pull out")):
        return "extraction"
    if _contains_any(text, ("creative", "brainstorm")):
        return "creative"
    return "drafting"


def _sensitivity_from_text(text: str) -> str:
    if _contains_any(text, ("medical", "medication", "dose")):
        return "medical"
    if "legal" in text:
        return "legal"
    if "financial" in text or "invoice" in text:
        return "financial"
    if "caregiver" in text:
        return "caregiver"
    if "personal" in text:
        return "personal"
    if "safety" in text or "danger" in text:
        return "safety_critical"
    return "ordinary"


def _economy_sort_key(candidate: dict[str, object]) -> tuple[float, int, str, str]:
    entry = candidate["entry"]
    assert isinstance(entry, ModelCatalogEntry)
    return (
        float(candidate["estimated_cost_usd"]),
        entry.selection_priority,
        entry.provider_id,
        entry.model_id,
    )


def _balanced_sort_key(candidate: dict[str, object]) -> tuple[int, float, int, str, str]:
    entry = candidate["entry"]
    assert isinstance(entry, ModelCatalogEntry)
    return (
        TIER_RANK[entry.capability_tier],
        float(candidate["estimated_cost_usd"]),
        entry.selection_priority,
        entry.provider_id,
        entry.model_id,
    )


def _premium_sort_key(candidate: dict[str, object]) -> tuple[int, float, int, str, str]:
    entry = candidate["entry"]
    assert isinstance(entry, ModelCatalogEntry)
    return (
        -TIER_RANK[entry.capability_tier],
        float(candidate["estimated_cost_usd"]),
        entry.selection_priority,
        entry.provider_id,
        entry.model_id,
    )


def _max_tier(left: str, right: str) -> str:
    return left if TIER_RANK[left] >= TIER_RANK[right] else right


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
