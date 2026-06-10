from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Literal

from app.budget_authority import (
    BudgetAuthorityRequest,
    BudgetAuthorityResult,
    evaluate_budget_authority,
)


ConversationClassification = Literal[
    "CURIOSITY",
    "SIGNAL",
    "CANDIDATE_IDEA",
    "EXECUTION_PRIORITY",
    "ROUTINE",
    "DECISION",
    "OPEN_LOOP",
    "CRISIS_OR_SENSITIVE",
    "CONTEXT_UPDATE",
    "NO_ACTION",
]

NextStepDecision = Literal[
    "NO_ACTION",
    "ANSWER_ONLY",
    "NOTE_PROPOSED",
    "MEMORY_UPDATE_PROPOSED",
    "BACKLOG_ITEM",
    "OPEN_LOOP_CREATED",
    "DECISION_RECORDED",
    "STORY_RECOMMENDED",
    "SPEC_RECOMMENDED",
    "EXECUTION_PLAN",
    "ESCALATE_OR_CONFIRM",
]

ContinuityItemType = Literal[
    "FACT",
    "PREFERENCE",
    "GOAL",
    "VALUE",
    "RISK",
    "OPERATING_PATTERN",
    "COMMUNICATION_STYLE",
    "PROJECT_CONTEXT",
    "OPEN_LOOP",
    "DECISION",
    "INFERENCE",
    "STRATEGIC_OPINION",
]

AuthorityLevel = Literal[
    "CONFIRMED_FACT",
    "USER_STATED",
    "USER_CONFIRMED",
    "SYSTEM_INFERENCE",
    "STRATEGIC_RECOMMENDATION",
    "LOW_AUTHORITY_SIGNAL",
]

SensitivityLevel = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "SENSITIVE",
    "BLOCKED",
]

AllowedInfluenceScope = Literal[
    "TONE_ONLY",
    "PLANNING",
    "PRIORITY_GATING",
    "PROACTIVE_INTERVENTION",
    "MEMORY_PROPOSAL_ONLY",
    "EXPORT_ONLY",
    "DO_NOT_USE_FOR_DECISIONS",
]

StorageTarget = Literal[
    "EXISTING_MEMORY_PROPOSAL_FLOW",
    "FUTURE_CRITERIO_STORE",
    "SESSION_ONLY",
    "DO_NOT_STORE",
]

ContinuityAuthorityDecision = Literal[
    "ALLOW",
    "ALLOW_WITH_LABEL",
    "ASK_CONFIRMATION",
    "DRAFT_ONLY",
    "ESCALATE",
    "BLOCK",
]


@dataclass(frozen=True, slots=True)
class ConversationContinuityRequest:
    raw_text: str
    source_channel: str = "telegram"
    known_open_loops: tuple[str, ...] = ()
    known_priorities: tuple[str, ...] = ()
    active_projects: tuple[str, ...] = ()
    cash_or_client_pressure_present: bool = False
    sensitive_context_present: bool = False
    budget_context: BudgetAuthorityRequest | BudgetAuthorityResult | dict | None = None


@dataclass(frozen=True, slots=True)
class ConversationContinuityResult:
    classification: ConversationClassification
    secondary_labels: tuple[str, ...]
    confidence: float
    reason: str
    next_step_decision: NextStepDecision
    memory_candidate: "ContinuityMemoryCandidate | None" = None
    priority_gate_result: "PriorityGateResult | None" = None
    daily_start_plan: "DailyStartPlan | None" = None
    authority_result: "ContinuityAuthorityResult | None" = None
    budget_decision: BudgetAuthorityResult | None = None
    external_execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class ContinuityMemoryCandidate:
    content: str
    item_type: ContinuityItemType
    reason: str
    authority_level: AuthorityLevel
    sensitivity_level: SensitivityLevel
    source_event_ref: str
    confirmation_required: bool
    confirmed_by_user: bool
    expiration_policy: str
    allowed_influence_scope: AllowedInfluenceScope
    storage_target: StorageTarget

    def __post_init__(self) -> None:
        confirmation_required = self.confirmation_required
        confirmed_by_user = self.confirmed_by_user
        storage_target = self.storage_target

        if self.authority_level == "SYSTEM_INFERENCE" and storage_target not in {"SESSION_ONLY", "DO_NOT_STORE"}:
            confirmation_required = True
            confirmed_by_user = False
        if self.sensitivity_level == "SENSITIVE":
            confirmation_required = True
        if self.sensitivity_level == "BLOCKED":
            confirmation_required = True
            confirmed_by_user = False
            storage_target = "DO_NOT_STORE"

        object.__setattr__(self, "confirmation_required", confirmation_required)
        object.__setattr__(self, "confirmed_by_user", confirmed_by_user)
        object.__setattr__(self, "storage_target", storage_target)


@dataclass(frozen=True, slots=True)
class PriorityGateRequest:
    message: str
    cash_relevance: bool = False
    active_client_relevance: bool = False
    core_product_relevance: bool = False
    family_operational_or_cognitive_risk_reduction: bool = False
    demo_delivery_or_sale_unblock: bool = False
    dispersion_risk: bool = False


@dataclass(frozen=True, slots=True)
class PriorityGateResult:
    classification: str
    recommendation: str
    why: str
    do_now: str
    do_not_do_now: str
    backlog_handling: str
    priority_score: int


@dataclass(frozen=True, slots=True)
class DailyStartRequest:
    known_open_loops: tuple[str, ...] = ()
    known_priorities: tuple[str, ...] = ()
    cash_or_client_pressure_present: bool = False
    energy_level: str | None = None
    family_constraints: tuple[str, ...] = ()
    deadline_pressure: bool = False
    non_urgent_backlog: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DailyStartPlan:
    state: str
    starting_priority: str
    commitments: tuple[str, ...]
    first_concrete_action: str
    transition_to_next_block: str
    distractions_to_avoid: tuple[str, ...]
    backlog_parking: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.commitments) > 3:
            object.__setattr__(self, "commitments", self.commitments[:3])


@dataclass(frozen=True, slots=True)
class NextStepRequest:
    classification: ConversationClassification
    has_memory_candidate: bool = False
    daily_start_requested: bool = False
    priority_gate_result: PriorityGateResult | None = None
    authority_result: "ContinuityAuthorityResult | None" = None


@dataclass(frozen=True, slots=True)
class NextStepDecisionResult:
    decision: NextStepDecision
    reason: str


@dataclass(frozen=True, slots=True)
class ContinuityAuthorityRequest:
    item_type: ContinuityItemType
    authority_level: AuthorityLevel
    sensitivity_level: SensitivityLevel
    allowed_influence_scope: AllowedInfluenceScope
    uses_sensitive_context: bool = False
    proactive_recommendation: bool = False
    confirmation_present: bool = False


@dataclass(frozen=True, slots=True)
class ContinuityAuthorityResult:
    decision: ContinuityAuthorityDecision
    label_required: bool
    confirmation_required: bool
    reason: str
    allowed_to_influence_planning: bool
    allowed_to_store: bool
    allowed_to_trigger_proactive_intervention: bool


@dataclass(frozen=True, slots=True)
class ProactiveInterventionRequest:
    repeated_bottleneck: bool = False
    repeated_dispersion: bool = False
    missed_follow_up: bool = False
    unresolved_open_loop: bool = False
    dependency_gap: bool = False
    priority_conflict: bool = False
    high_leverage_opportunity: bool = False
    uses_sensitive_context: bool = False
    confirmation_present: bool = False


@dataclass(frozen=True, slots=True)
class ProactiveInterventionResult:
    eligible: bool
    observation: str
    implication: str
    recommendation: str
    what_not_to_do: str
    classification: str
    authority_label: str
    authority_result: ContinuityAuthorityResult


def classify_conversation_event(request: ConversationContinuityRequest) -> ConversationContinuityResult:
    text = _normalize(request.raw_text)
    budget_decision = _evaluate_budget_context(request.budget_context)

    classification, reason, confidence, secondary_labels = _classify_text(text, request)
    memory_candidate = _candidate_for_classification(classification=classification, request=request)
    priority_gate_result = _priority_gate_for_classification(classification=classification, request=request)
    daily_start_plan = _daily_start_for_classification(classification=classification, request=request)
    authority_result = _authority_for_candidate(memory_candidate)
    next_step = resolve_next_step(
        NextStepRequest(
            classification=classification,
            has_memory_candidate=memory_candidate is not None,
            daily_start_requested=daily_start_plan is not None,
            priority_gate_result=priority_gate_result,
            authority_result=authority_result,
        )
    )

    if budget_decision is not None and budget_decision.decision in {"DEFER", "BLOCK"}:
        next_step = NextStepDecisionResult(
            decision="ESCALATE_OR_CONFIRM",
            reason=f"Budget authority returned {budget_decision.decision}.",
        )

    return ConversationContinuityResult(
        classification=classification,
        secondary_labels=secondary_labels,
        confidence=confidence,
        reason=reason,
        next_step_decision=next_step.decision,
        memory_candidate=memory_candidate,
        priority_gate_result=priority_gate_result,
        daily_start_plan=daily_start_plan,
        authority_result=authority_result,
        budget_decision=budget_decision,
        external_execution_authorized=False,
    )


def build_continuity_memory_candidate(
    *,
    content: str,
    item_type: ContinuityItemType,
    reason: str,
    authority_level: AuthorityLevel,
    sensitivity_level: SensitivityLevel = "LOW",
    source_event_ref: str = "session_event",
    confirmation_required: bool = False,
    confirmed_by_user: bool = False,
    expiration_policy: str = "review_before_promotion",
    allowed_influence_scope: AllowedInfluenceScope = "MEMORY_PROPOSAL_ONLY",
    storage_target: StorageTarget = "SESSION_ONLY",
) -> ContinuityMemoryCandidate:
    return ContinuityMemoryCandidate(
        content=content,
        item_type=item_type,
        reason=reason,
        authority_level=authority_level,
        sensitivity_level=sensitivity_level,
        source_event_ref=source_event_ref,
        confirmation_required=confirmation_required,
        confirmed_by_user=confirmed_by_user,
        expiration_policy=expiration_policy,
        allowed_influence_scope=allowed_influence_scope,
        storage_target=storage_target,
    )


def evaluate_priority_gate(request: PriorityGateRequest) -> PriorityGateResult:
    score = 0
    reasons: list[str] = []
    if request.cash_relevance:
        score += 3
        reasons.append("cash impact")
    if request.active_client_relevance:
        score += 3
        reasons.append("active client impact")
    if request.core_product_relevance:
        score += 2
        reasons.append("Roboticxs or Zaubern core relevance")
    if request.family_operational_or_cognitive_risk_reduction:
        score += 2
        reasons.append("risk reduction")
    if request.demo_delivery_or_sale_unblock:
        score += 2
        reasons.append("demo, delivery, or sale unblock")
    if request.dispersion_risk:
        score -= 3
        reasons.append("dispersion risk")

    must_backlog = request.dispersion_risk and not (
        request.cash_relevance or request.active_client_relevance or request.demo_delivery_or_sale_unblock
    )
    should_do_now = score >= 3 and not must_backlog

    if should_do_now:
        return PriorityGateResult(
            classification="PRIORITY",
            recommendation="Do now under a short execution plan.",
            why=", ".join(reasons) or "meets current priority criteria",
            do_now="Close the smallest cash/client/core unblock first.",
            do_not_do_now="Do not open unrelated research while this priority is active.",
            backlog_handling="Park adjacent ideas until the current priority closes.",
            priority_score=score,
        )

    return PriorityGateResult(
        classification="BACKLOG",
        recommendation="Not now. Backlog.",
        why=", ".join(reasons) or "does not beat current cash/client/core priorities",
        do_now="Continue the current A/B priority.",
        do_not_do_now="Do not open GitHub, papers, repos, or speculative research for this idea now.",
        backlog_handling="Capture as a backlog item with a short reason and revisit after current priority closes.",
        priority_score=score,
    )


def build_daily_start_plan(request: DailyStartRequest) -> DailyStartPlan:
    starting_priority = _select_starting_priority(request)
    commitments = _select_commitments(request, starting_priority)
    state_parts = ["Start from one bounded block, not a long list."]
    if request.cash_or_client_pressure_present:
        state_parts.append("Cash or active client pressure is present.")
    if request.deadline_pressure:
        state_parts.append("Deadline pressure is present.")
    if request.family_constraints:
        state_parts.append("Family or operating constraints should shape the block.")

    return DailyStartPlan(
        state=" ".join(state_parts),
        starting_priority=starting_priority,
        commitments=commitments,
        first_concrete_action=f"Open the smallest artifact or message needed for: {starting_priority}.",
        transition_to_next_block="After the first concrete action, decide whether to continue, hand off, or park the remaining loop.",
        distractions_to_avoid=(
            "new repo exploration",
            "papers or tool research",
            "non-urgent backlog grooming",
        ),
        backlog_parking=request.non_urgent_backlog or ("Park interesting non-urgent ideas until the starting priority closes.",),
    )


def resolve_next_step(request: NextStepRequest) -> NextStepDecisionResult:
    if request.authority_result and request.authority_result.decision in {"ASK_CONFIRMATION", "ESCALATE", "BLOCK"}:
        return NextStepDecisionResult(
            decision="ESCALATE_OR_CONFIRM",
            reason="Authority result requires confirmation, escalation, or blocking.",
        )
    if request.daily_start_requested:
        return NextStepDecisionResult(decision="EXECUTION_PLAN", reason="Daily Start or execution planning was requested.")
    if request.classification == "CANDIDATE_IDEA":
        return NextStepDecisionResult(decision="BACKLOG_ITEM", reason="Candidate ideas default to backlog.")
    if request.classification == "CURIOSITY":
        return NextStepDecisionResult(decision="ANSWER_ONLY", reason="Curiosity does not create task/story/spec work.")
    if request.classification == "SIGNAL":
        return NextStepDecisionResult(decision="ANSWER_ONLY", reason="Signal may be answered or parked without roadmap work.")
    if request.classification == "OPEN_LOOP":
        return NextStepDecisionResult(decision="OPEN_LOOP_CREATED", reason="The message contains an unresolved commitment.")
    if request.classification == "DECISION":
        return NextStepDecisionResult(decision="DECISION_RECORDED", reason="The message states a decision.")
    if request.classification == "CRISIS_OR_SENSITIVE":
        return NextStepDecisionResult(decision="ESCALATE_OR_CONFIRM", reason="Sensitive context must be constrained.")
    if request.has_memory_candidate:
        return NextStepDecisionResult(decision="NOTE_PROPOSED", reason="A note can be proposed without direct storage.")
    return NextStepDecisionResult(decision="NO_ACTION", reason="No action is required.")


def evaluate_continuity_authority(request: ContinuityAuthorityRequest) -> ContinuityAuthorityResult:
    label_required = request.authority_level in {"SYSTEM_INFERENCE", "STRATEGIC_RECOMMENDATION"} or request.item_type in {
        "INFERENCE",
        "STRATEGIC_OPINION",
    }
    confirmation_required = False

    if request.sensitivity_level == "BLOCKED":
        return ContinuityAuthorityResult(
            decision="BLOCK",
            label_required=True,
            confirmation_required=True,
            reason="Blocked sensitivity cannot be stored or used for planning.",
            allowed_to_influence_planning=False,
            allowed_to_store=False,
            allowed_to_trigger_proactive_intervention=False,
        )
    if request.uses_sensitive_context and request.proactive_recommendation and not request.confirmation_present:
        return ContinuityAuthorityResult(
            decision="ESCALATE",
            label_required=True,
            confirmation_required=True,
            reason="Sensitive context cannot silently trigger proactive recommendations.",
            allowed_to_influence_planning=False,
            allowed_to_store=False,
            allowed_to_trigger_proactive_intervention=False,
        )
    if request.authority_level == "SYSTEM_INFERENCE" or request.sensitivity_level == "SENSITIVE":
        confirmation_required = not request.confirmation_present
        if confirmation_required:
            return ContinuityAuthorityResult(
                decision="ASK_CONFIRMATION",
                label_required=True,
                confirmation_required=True,
                reason="Inference or sensitive criterio requires user confirmation before durable use.",
                allowed_to_influence_planning=False,
                allowed_to_store=False,
                allowed_to_trigger_proactive_intervention=False,
            )
    if request.authority_level == "STRATEGIC_RECOMMENDATION":
        return ContinuityAuthorityResult(
            decision="ALLOW_WITH_LABEL",
            label_required=True,
            confirmation_required=False,
            reason="Strategic recommendation must be labeled and not presented as fact.",
            allowed_to_influence_planning=request.allowed_influence_scope in {"PLANNING", "PRIORITY_GATING"},
            allowed_to_store=False,
            allowed_to_trigger_proactive_intervention=False,
        )
    if request.allowed_influence_scope == "DO_NOT_USE_FOR_DECISIONS":
        return ContinuityAuthorityResult(
            decision="DRAFT_ONLY",
            label_required=label_required,
            confirmation_required=False,
            reason="The item is available only as non-decision context.",
            allowed_to_influence_planning=False,
            allowed_to_store=request.sensitivity_level in {"LOW", "MEDIUM"},
            allowed_to_trigger_proactive_intervention=False,
        )

    return ContinuityAuthorityResult(
        decision="ALLOW_WITH_LABEL" if label_required else "ALLOW",
        label_required=label_required,
        confirmation_required=False,
        reason="Low-risk confirmed or user-stated context fits the requested influence scope.",
        allowed_to_influence_planning=request.allowed_influence_scope in {
            "PLANNING",
            "PRIORITY_GATING",
            "PROACTIVE_INTERVENTION",
        },
        allowed_to_store=request.sensitivity_level in {"LOW", "MEDIUM", "HIGH"},
        allowed_to_trigger_proactive_intervention=request.allowed_influence_scope == "PROACTIVE_INTERVENTION",
    )


def evaluate_proactive_intervention(request: ProactiveInterventionRequest) -> ProactiveInterventionResult:
    evidence_flags = (
        request.repeated_bottleneck,
        request.repeated_dispersion,
        request.missed_follow_up,
        request.unresolved_open_loop,
        request.dependency_gap,
        request.priority_conflict,
        request.high_leverage_opportunity,
    )
    has_evidence = any(evidence_flags)
    authority = evaluate_continuity_authority(
        ContinuityAuthorityRequest(
            item_type="INFERENCE",
            authority_level="SYSTEM_INFERENCE",
            sensitivity_level="SENSITIVE" if request.uses_sensitive_context else "MEDIUM",
            allowed_influence_scope="PROACTIVE_INTERVENTION",
            uses_sensitive_context=request.uses_sensitive_context,
            proactive_recommendation=True,
            confirmation_present=request.confirmation_present,
        )
    )
    eligible = has_evidence and authority.allowed_to_trigger_proactive_intervention

    return ProactiveInterventionResult(
        eligible=eligible,
        observation="Evidence present." if has_evidence else "No repeated bottleneck, open loop, dependency, or priority evidence.",
        implication="Intervention may be useful." if has_evidence else "Do not interrupt proactively.",
        recommendation="Suggest one bounded next step." if eligible else "Do not proactively intervene.",
        what_not_to_do="Do not use sensitive inference silently or create external actions.",
        classification="PROACTIVE_ELIGIBLE" if eligible else "PROACTIVE_NOT_ELIGIBLE",
        authority_label="[Inference]" if authority.label_required else "[User-stated]",
        authority_result=authority,
    )


def export_continuity_candidates(candidates: tuple[ContinuityMemoryCandidate, ...]) -> dict[str, list[ContinuityMemoryCandidate]]:
    grouped: dict[str, list[ContinuityMemoryCandidate]] = {
        "facts": [],
        "preferences": [],
        "goals": [],
        "values": [],
        "risks": [],
        "inferences": [],
        "strategic_recommendations": [],
        "decisions": [],
        "open_loops": [],
    }
    mapping = {
        "FACT": "facts",
        "PREFERENCE": "preferences",
        "GOAL": "goals",
        "VALUE": "values",
        "RISK": "risks",
        "INFERENCE": "inferences",
        "OPERATING_PATTERN": "inferences",
        "STRATEGIC_OPINION": "strategic_recommendations",
        "DECISION": "decisions",
        "OPEN_LOOP": "open_loops",
    }
    for candidate in candidates:
        key = mapping.get(candidate.item_type)
        if key is not None:
            grouped[key].append(candidate)
    return grouped


def _classify_text(
    text: str, request: ConversationContinuityRequest
) -> tuple[ConversationClassification, str, float, tuple[str, ...]]:
    if _contains_any(text, _DAILY_START_TRIGGERS):
        return "EXECUTION_PRIORITY", "Daily Start trigger detected.", 0.95, ("DAILY_START",)
    if request.sensitive_context_present or _contains_any(text, _SENSITIVE_TERMS):
        return "CRISIS_OR_SENSITIVE", "Sensitive health, family-care, medication, or mental-health context detected.", 0.82, ()
    if request.cash_or_client_pressure_present or _contains_any(text, _EXECUTION_TERMS):
        return "EXECUTION_PRIORITY", "Payment, deadline, client, delivery, or committed-work signal detected.", 0.86, ()
    if _contains_any(text, _DECISION_TERMS):
        return "DECISION", "Explicit decision language detected.", 0.82, ()
    if _contains_any(text, _OPEN_LOOP_TERMS):
        return "OPEN_LOOP", "Unresolved commitment or follow-up language detected.", 0.78, ()
    if _contains_any(text, _CANDIDATE_IDEA_TERMS):
        return "CANDIDATE_IDEA", "Candidate idea language detected.", 0.82, ()
    if _contains_any(text, _CURIOSITY_TERMS):
        return "CURIOSITY", "Exploratory repo, paper, tool, or question language detected.", 0.8, ()
    if _contains_any(text, _ROUTINE_TERMS):
        return "ROUTINE", "Routine language detected.", 0.75, ()
    if _contains_any(text, _CONTEXT_UPDATE_TERMS):
        return "CONTEXT_UPDATE", "Context update language detected.", 0.72, ()
    if "?" in text:
        return "SIGNAL", "Question signal detected without execution language.", 0.65, ()
    return "NO_ACTION", "Reflective or conversational text without an action commitment.", 0.62, ()


def _candidate_for_classification(
    *, classification: ConversationClassification, request: ConversationContinuityRequest
) -> ContinuityMemoryCandidate | None:
    if classification == "DECISION":
        return build_continuity_memory_candidate(
            content=request.raw_text,
            item_type="DECISION",
            reason="User stated a decision.",
            authority_level="USER_STATED",
            storage_target="EXISTING_MEMORY_PROPOSAL_FLOW",
        )
    if classification == "OPEN_LOOP":
        return build_continuity_memory_candidate(
            content=request.raw_text,
            item_type="OPEN_LOOP",
            reason="User described an unresolved commitment.",
            authority_level="USER_STATED",
            storage_target="EXISTING_MEMORY_PROPOSAL_FLOW",
        )
    if classification == "CONTEXT_UPDATE":
        return build_continuity_memory_candidate(
            content=request.raw_text,
            item_type="PROJECT_CONTEXT",
            reason="User provided context that may help later planning.",
            authority_level="USER_STATED",
            storage_target="EXISTING_MEMORY_PROPOSAL_FLOW",
        )
    if classification == "CRISIS_OR_SENSITIVE":
        return build_continuity_memory_candidate(
            content=request.raw_text,
            item_type="INFERENCE",
            reason="Sensitive context can only be labeled and confirmation-gated.",
            authority_level="SYSTEM_INFERENCE",
            sensitivity_level="SENSITIVE",
            storage_target="DO_NOT_STORE",
            allowed_influence_scope="DO_NOT_USE_FOR_DECISIONS",
        )
    return None


def _priority_gate_for_classification(
    *, classification: ConversationClassification, request: ConversationContinuityRequest
) -> PriorityGateResult | None:
    if classification not in {"CANDIDATE_IDEA", "EXECUTION_PRIORITY"}:
        return None

    text = _normalize(request.raw_text)
    return evaluate_priority_gate(
        PriorityGateRequest(
            message=request.raw_text,
            cash_relevance=request.cash_or_client_pressure_present or _contains_any(text, _CASH_TERMS),
            active_client_relevance=_contains_any(text, _CLIENT_TERMS),
            core_product_relevance=_contains_any(text, _CORE_PRODUCT_TERMS),
            family_operational_or_cognitive_risk_reduction=_contains_any(text, _RISK_REDUCTION_TERMS),
            demo_delivery_or_sale_unblock=_contains_any(text, _UNBLOCK_TERMS),
            dispersion_risk=classification == "CANDIDATE_IDEA" or _contains_any(text, _DISPERSION_TERMS),
        )
    )


def _daily_start_for_classification(
    *, classification: ConversationClassification, request: ConversationContinuityRequest
) -> DailyStartPlan | None:
    text = _normalize(request.raw_text)
    if classification == "EXECUTION_PRIORITY" and _contains_any(text, _DAILY_START_TRIGGERS):
        return build_daily_start_plan(
            DailyStartRequest(
                known_open_loops=request.known_open_loops,
                known_priorities=request.known_priorities,
                cash_or_client_pressure_present=request.cash_or_client_pressure_present,
                non_urgent_backlog=tuple(project for project in request.active_projects if project not in request.known_priorities),
            )
        )
    if classification == "EXECUTION_PRIORITY":
        priority = request.raw_text.strip() or "current execution priority"
        return build_daily_start_plan(
            DailyStartRequest(
                known_open_loops=request.known_open_loops,
                known_priorities=(priority,),
                cash_or_client_pressure_present=request.cash_or_client_pressure_present,
            )
        )
    return None


def _authority_for_candidate(candidate: ContinuityMemoryCandidate | None) -> ContinuityAuthorityResult | None:
    if candidate is None:
        return None
    return evaluate_continuity_authority(
        ContinuityAuthorityRequest(
            item_type=candidate.item_type,
            authority_level=candidate.authority_level,
            sensitivity_level=candidate.sensitivity_level,
            allowed_influence_scope=candidate.allowed_influence_scope,
            uses_sensitive_context=candidate.sensitivity_level in {"SENSITIVE", "BLOCKED"},
            proactive_recommendation=False,
            confirmation_present=candidate.confirmed_by_user,
        )
    )


def _evaluate_budget_context(
    budget_context: BudgetAuthorityRequest | BudgetAuthorityResult | dict | None,
) -> BudgetAuthorityResult | None:
    if budget_context is None:
        return None
    if isinstance(budget_context, BudgetAuthorityResult):
        return budget_context
    if isinstance(budget_context, BudgetAuthorityRequest):
        return evaluate_budget_authority(budget_context)
    if isinstance(budget_context, dict):
        task_class = "CONVERSATION_CONTINUITY_FUTURE" if budget_context.get("future_stage_requested") else "SIMPLE_CLASSIFICATION"
        if budget_context.get("high_cost") or budget_context.get("requires_long_context"):
            task_class = "GENERAL_TASK"
        return evaluate_budget_authority(
            BudgetAuthorityRequest(
                task_class=task_class,
                estimated_input_tokens=int(budget_context.get("estimated_input_tokens", 0)),
                estimated_output_tokens=int(budget_context.get("estimated_output_tokens", 0)),
                estimated_cost=float(budget_context.get("estimated_cost", 0.0)),
                model_tier=str(budget_context.get("model_tier", "economy")),
                premium_requested=bool(budget_context.get("premium_requested", False)),
                confirmation_present=bool(budget_context.get("confirmation_present", False)),
                requires_long_context=bool(budget_context.get("requires_long_context", False)),
                tool_classes=tuple(budget_context.get("tool_classes", ())),
            )
        )
    return None


def _select_starting_priority(request: DailyStartRequest) -> str:
    if request.cash_or_client_pressure_present:
        for priority in request.known_priorities:
            if _contains_any(_normalize(priority), _CASH_TERMS | _CLIENT_TERMS | _EXECUTION_TERMS):
                return priority
        return "cash/client unblock"
    if request.deadline_pressure and request.known_priorities:
        return request.known_priorities[0]
    if request.known_priorities:
        return request.known_priorities[0]
    if request.known_open_loops:
        return request.known_open_loops[0]
    return "identify and close the smallest real unblock"


def _select_commitments(request: DailyStartRequest, starting_priority: str) -> tuple[str, ...]:
    commitments = [f"Start: {starting_priority}"]
    if request.known_open_loops:
        commitments.append(f"Close or park: {request.known_open_loops[0]}")
    if request.deadline_pressure or request.cash_or_client_pressure_present:
        commitments.append("Send or prepare the next concrete delivery/payment step.")
    elif len(request.known_priorities) > 1:
        commitments.append(f"Park: {request.known_priorities[1]}")
    return tuple(commitments[:3])


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_any(text: str, terms: frozenset[str]) -> bool:
    return any(term in text for term in terms)


_DAILY_START_TRIGGERS = frozenset(
    {
        "que hago hoy",
        "por donde empiezo",
        "estoy atorado",
        "ayudame a arrancar",
    }
)
_SENSITIVE_TERMS = frozenset(
    {
        "medicacion",
        "medicina",
        "diagnostico",
        "depresion",
        "ansiedad",
        "salud mental",
        "crisis",
        "emergencia",
        "cuidador",
        "family-care",
        "riesgo familiar",
    }
)
_EXECUTION_TERMS = frozenset(
    {
        "pago",
        "factura",
        "invoice",
        "deadline",
        "entrega",
        "cliente",
        "commit",
        "comprometido",
        "cuenta bancaria",
        "cobrar",
        "sale",
        "demo",
    }
)
_CASH_TERMS = frozenset({"pago", "factura", "invoice", "cobrar", "cash", "cuenta bancaria"})
_CLIENT_TERMS = frozenset({"cliente", "client", "entrega", "delivery"})
_CORE_PRODUCT_TERMS = frozenset({"roboticxs", "zaubern", "core", "safety layer", "continuity"})
_RISK_REDUCTION_TERMS = frozenset({"riesgo", "risk", "familia", "operativo", "cognitivo"})
_UNBLOCK_TERMS = frozenset({"desbloquea", "unblock", "demo", "delivery", "entrega", "sale", "venta"})
_DISPERSION_TERMS = frozenset({"research", "investigar", "repo", "paper", "herramienta nueva"})
_DECISION_TERMS = frozenset({"decidi ", "decidimos", "decision:", "queda decidido", "vamos a hacer"})
_OPEN_LOOP_TERMS = frozenset({"pendiente", "falta", "tengo que", "hay que", "seguimiento", "follow up"})
_CANDIDATE_IDEA_TERMS = frozenset(
    {
        "podria servir para roboticxs",
        "podria servirnos",
        "seria util para roboticxs",
        "idea para roboticxs",
        "candidate idea",
    }
)
_CURIOSITY_TERMS = frozenset(
    {
        "mira este repo",
        "mira este paper",
        "mira esta herramienta",
        "nos sirve?",
        "que opinas de",
        "curiosidad",
        "explora",
    }
)
_ROUTINE_TERMS = frozenset({"rutina", "routine", "todos los dias", "cada semana"})
_CONTEXT_UPDATE_TERMS = frozenset({"contexto:", "update:", "actualizacion:", "para contexto", "nota de contexto"})
