from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


BudgetAuthorityDecision = Literal[
    "ALLOW",
    "ALLOW_WITH_CAP",
    "ASK_CONFIRMATION",
    "DOWNGRADE_MODEL",
    "DEFER",
    "BLOCK",
]

TaskClass = Literal[
    "GENERAL_TASK",
    "SIMPLE_CLASSIFICATION",
    "MEMORY_PROPOSAL",
    "MEMORY_DECISION",
    "FILE_INTAKE",
    "DOCUMENT_REVIEW",
    "ATTENTION_SUMMARY",
    "ROBOT_FOLDER",
    "SUPER_FAMILIAR",
    "WEB_PREFLIGHT",
    "ACTION_APPROVAL_PACKET",
    "RETRIEVAL_CONTROL",
    "USAGE_REPORTING",
    "CONVERSATION_CONTINUITY_FUTURE",
    "CAREGIVER_FUTURE",
    "VOICE_FUTURE",
    "RESEARCH_RADAR_FUTURE",
    "EXTERNAL_SKILL_FUTURE",
]


BILLING_TRUTH_DISCLAIMER = "local estimate only; not billing truth"

FUTURE_DEFER_TASK_CLASSES = frozenset(
    {
        "CONVERSATION_CONTINUITY_FUTURE",
        "CAREGIVER_FUTURE",
        "VOICE_FUTURE",
        "RESEARCH_RADAR_FUTURE",
    }
)
FUTURE_BLOCK_TASK_CLASSES = frozenset({"EXTERNAL_SKILL_FUTURE"})


@dataclass(frozen=True, slots=True)
class BudgetAuthorityPolicy:
    policy_id: str = "default_budget_authority_policy_v0"
    daily_estimated_cost_cap: float = 1.00
    monthly_estimated_cost_cap: float = 20.00
    premium_model_confirmation_threshold: float = 0.10
    long_context_confirmation_threshold_tokens: int = 24_000
    default_retry_cap: int = 1
    default_tool_call_cap: int = 3
    blocked_tool_classes: tuple[str, ...] = (
        "EXTERNAL_WRITE",
        "CONNECTOR_EXECUTION",
        "LIVE_RETRIEVAL",
        "PAYMENT_EXECUTION",
    )
    allowed_modes: tuple[str, ...] = (
        "ECONOMY",
        "BALANCED",
        "PREMIUM_WITH_CONFIRMATION",
        "BYOK",
    )


DEFAULT_BUDGET_AUTHORITY_POLICY = BudgetAuthorityPolicy()


@dataclass(frozen=True, slots=True)
class BudgetAuthorityRequest:
    task_class: str
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost: float = 0.0
    model_tier: str = "economy"
    mode: str = "ECONOMY"
    premium_requested: bool = False
    confirmation_present: bool = False
    retry_count: int = 0
    tool_call_count: int = 0
    tool_classes: tuple[str, ...] = ()
    requires_long_context: bool = False


@dataclass(frozen=True, slots=True)
class BudgetAuthorityResult:
    decision: BudgetAuthorityDecision
    task_class: str
    reason: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    model_tier: str
    cap_applied: bool
    confirmation_required: bool
    blocked_reason: str | None
    downgrade_target: str | None
    retry_cap: int
    tool_call_cap: int
    cost_basis: str = BILLING_TRUTH_DISCLAIMER
    denied_authorizations: tuple[str, ...] = field(
        default=(
            "connectors",
            "browser",
            "live_retrieval",
            "email",
            "whatsapp",
            "crm",
            "lead_gen",
            "handoff",
            "payment",
            "external_writes",
        )
    )


DEFAULT_TASK_DECISIONS: dict[str, BudgetAuthorityDecision] = {
    "GENERAL_TASK": "ALLOW_WITH_CAP",
    "SIMPLE_CLASSIFICATION": "ALLOW",
    "MEMORY_PROPOSAL": "ALLOW_WITH_CAP",
    "MEMORY_DECISION": "ALLOW",
    "FILE_INTAKE": "ALLOW_WITH_CAP",
    "DOCUMENT_REVIEW": "ALLOW_WITH_CAP",
    "ATTENTION_SUMMARY": "ALLOW_WITH_CAP",
    "ROBOT_FOLDER": "ALLOW_WITH_CAP",
    "SUPER_FAMILIAR": "ALLOW_WITH_CAP",
    "WEB_PREFLIGHT": "ALLOW_WITH_CAP",
    "ACTION_APPROVAL_PACKET": "ALLOW_WITH_CAP",
    "RETRIEVAL_CONTROL": "ALLOW",
    "USAGE_REPORTING": "ALLOW",
}


def evaluate_budget_authority(
    request: BudgetAuthorityRequest,
    policy: BudgetAuthorityPolicy = DEFAULT_BUDGET_AUTHORITY_POLICY,
) -> BudgetAuthorityResult:
    blocked_tool_class = _first_blocked_tool_class(request=request, policy=policy)
    if blocked_tool_class is not None:
        return _result(
            request=request,
            policy=policy,
            decision="BLOCK",
            reason=f"Blocked tool class {blocked_tool_class}; {BILLING_TRUTH_DISCLAIMER}.",
            blocked_reason=f"BLOCKED_TOOL_CLASS:{blocked_tool_class}",
        )

    if request.task_class in FUTURE_BLOCK_TASK_CLASSES:
        return _result(
            request=request,
            policy=policy,
            decision="BLOCK",
            reason=f"{request.task_class} is not approved in 65P; {BILLING_TRUTH_DISCLAIMER}.",
            blocked_reason="FUTURE_STAGE_NOT_APPROVED",
        )

    if request.task_class in FUTURE_DEFER_TASK_CLASSES:
        return _result(
            request=request,
            policy=policy,
            decision="DEFER",
            reason=f"{request.task_class} is deferred until its approved future stage; {BILLING_TRUTH_DISCLAIMER}.",
            blocked_reason="FUTURE_STAGE_DEFERRED",
        )

    if request.retry_count >= policy.default_retry_cap:
        return _result(
            request=request,
            policy=policy,
            decision="DEFER",
            reason=f"Retry cap reached at {policy.default_retry_cap}; {BILLING_TRUTH_DISCLAIMER}.",
            blocked_reason="RETRY_CAP_REACHED",
        )

    if _premium_requires_confirmation(request=request, policy=policy):
        downgrade_target = "balanced" if _requires_premium_tier(request) and request.mode != "BYOK" else None
        decision: BudgetAuthorityDecision = "DOWNGRADE_MODEL" if downgrade_target else "ASK_CONFIRMATION"
        return _result(
            request=request,
            policy=policy,
            decision=decision,
            reason=f"Premium model use requires confirmation before higher-cost model spend; {BILLING_TRUTH_DISCLAIMER}.",
            confirmation_required=decision == "ASK_CONFIRMATION",
            downgrade_target=downgrade_target,
            cap_applied=decision == "DOWNGRADE_MODEL",
        )

    if _long_context_requires_confirmation_or_cap(request=request, policy=policy):
        return _result(
            request=request,
            policy=policy,
            decision="ALLOW_WITH_CAP",
            reason=f"Long context threshold reached; capped mode applies unless confirmed; {BILLING_TRUTH_DISCLAIMER}.",
            cap_applied=True,
            confirmation_required=False,
        )

    if request.tool_call_count > policy.default_tool_call_cap:
        return _result(
            request=request,
            policy=policy,
            decision="ALLOW_WITH_CAP",
            reason=f"Tool-call cap exceeded; capped local policy applies; {BILLING_TRUTH_DISCLAIMER}.",
            cap_applied=True,
        )

    if _estimated_cost_exceeds_cap(request=request, policy=policy):
        return _result(
            request=request,
            policy=policy,
            decision="BLOCK",
            reason=f"Estimated task cost exceeds local authority cap; {BILLING_TRUTH_DISCLAIMER}.",
            blocked_reason="ESTIMATED_COST_CAP_EXCEEDED",
        )

    if _document_review_requires_confirmation(request=request, policy=policy):
        return _result(
            request=request,
            policy=policy,
            decision="ASK_CONFIRMATION",
            reason=f"Document review may require higher spend and needs confirmation; {BILLING_TRUTH_DISCLAIMER}.",
            confirmation_required=True,
        )

    decision = DEFAULT_TASK_DECISIONS.get(request.task_class, "ALLOW_WITH_CAP")
    return _result(
        request=request,
        policy=policy,
        decision=decision,
        reason=f"{request.task_class} fits default budget authority policy; {BILLING_TRUTH_DISCLAIMER}.",
        cap_applied=decision == "ALLOW_WITH_CAP",
    )


def _first_blocked_tool_class(*, request: BudgetAuthorityRequest, policy: BudgetAuthorityPolicy) -> str | None:
    blocked = set(policy.blocked_tool_classes)
    for tool_class in request.tool_classes:
        if tool_class in blocked:
            return tool_class
    return None


def _premium_requires_confirmation(*, request: BudgetAuthorityRequest, policy: BudgetAuthorityPolicy) -> bool:
    cost_threshold = request.estimated_cost >= policy.premium_model_confirmation_threshold
    return (_requires_premium_tier(request) or cost_threshold) and not request.confirmation_present


def _requires_premium_tier(request: BudgetAuthorityRequest) -> bool:
    return request.model_tier.lower() == "premium" or request.premium_requested


def _long_context_requires_confirmation_or_cap(*, request: BudgetAuthorityRequest, policy: BudgetAuthorityPolicy) -> bool:
    estimated_tokens = request.estimated_input_tokens + request.estimated_output_tokens
    return request.requires_long_context or estimated_tokens >= policy.long_context_confirmation_threshold_tokens


def _estimated_cost_exceeds_cap(*, request: BudgetAuthorityRequest, policy: BudgetAuthorityPolicy) -> bool:
    return request.estimated_cost > policy.daily_estimated_cost_cap


def _document_review_requires_confirmation(*, request: BudgetAuthorityRequest, policy: BudgetAuthorityPolicy) -> bool:
    if request.task_class != "DOCUMENT_REVIEW" or request.confirmation_present:
        return False
    return request.estimated_cost >= policy.premium_model_confirmation_threshold


def _result(
    *,
    request: BudgetAuthorityRequest,
    policy: BudgetAuthorityPolicy,
    decision: BudgetAuthorityDecision,
    reason: str,
    cap_applied: bool = False,
    confirmation_required: bool = False,
    blocked_reason: str | None = None,
    downgrade_target: str | None = None,
) -> BudgetAuthorityResult:
    return BudgetAuthorityResult(
        decision=decision,
        task_class=request.task_class,
        reason=reason,
        estimated_input_tokens=request.estimated_input_tokens,
        estimated_output_tokens=request.estimated_output_tokens,
        estimated_cost=request.estimated_cost,
        model_tier=request.model_tier,
        cap_applied=cap_applied,
        confirmation_required=confirmation_required,
        blocked_reason=blocked_reason,
        downgrade_target=downgrade_target,
        retry_cap=policy.default_retry_cap,
        tool_call_cap=policy.default_tool_call_cap,
    )
