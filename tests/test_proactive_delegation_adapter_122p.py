from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.action_packet_approval import ActionPacketDecision, apply_action_packet_decision, create_action_packet, submit_action_packet_for_approval
from app.async_delegation_authority import build_async_delegation_action_packet_request
from app.context_scan_candidate_source import ContextScanCandidateSourceRegistry, create_context_scan_candidate_source, create_local_context_scan_authorization
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate, evaluate_cost_preflight
from app.followup_delegation_authority import FollowUpDelegationRegistry
from app.followup_draft_planner import FollowUpDraftOption, FollowUpDraftPlanRecord
from app.followup_intent_review import FollowUpIntentReviewQueue
from app.proactive_delegation_adapter import (
    AUTHORIZATION_KIND,
    PROACTIVE_DELEGATION_ADAPTER_STAGE,
    ProactiveDelegationAdapterRegistry,
    authorize_proactive_delegation_registration_local,
    get_proactive_delegation_adapter_record,
    list_proactive_delegation_adapter_records,
    register_proactive_delegation_from_existing_selection,
)
from app.proactive_opportunity_detection import ProactiveOpportunityRegistry, detect_proactive_opportunity_from_context_source
from app.proactive_suggestion_adapter import ProactiveSuggestionAdapterRegistry, adapt_proactive_suggestion_to_followup_intent, authorize_proactive_suggestion_adapter_local
from app.proactive_telegram_suggestion import ProactiveTelegramSuggestionRegistry, deliver_proactive_telegram_suggestion_local, render_proactive_telegram_suggestion
from app.telegram_async_result_delivery import TelegramOwnerBinding
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionRecord
from app.telegram_followup_choice_surface import PASSIVE_BUTTON_LABELS_BY_OPTION_KIND, TelegramFollowUpChoiceSurfaceRecord


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_delegation_adapter.py"

ALLOWED_SOURCE_TYPES = [
    "mock_email_thread",
    "mock_calendar_event",
    "mock_document",
    "mock_task_item",
    "mock_crm_note",
    "mock_invoice_record",
    "mock_message_thread",
    "mock_memory_snapshot",
]
DEFAULT_SCOPES = ["metadata_only", "summary_fixture", "selected_fields_fixture", "local_test_snapshot"]


class FakeTelegramTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[str, ...]]] = []

    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict[str, object]:
        self.calls.append((chat_id, text, buttons))
        return {
            "transport": "fake_telegram_local",
            "chat_id": chat_id,
            "message_fingerprint": f"{len(text)}:{len(buttons)}",
        }


def source_registry() -> ContextScanCandidateSourceRegistry:
    return ContextScanCandidateSourceRegistry()


def opportunity_registry() -> ProactiveOpportunityRegistry:
    return ProactiveOpportunityRegistry()


def suggestion_registry() -> ProactiveTelegramSuggestionRegistry:
    return ProactiveTelegramSuggestionRegistry()


def suggestion_adapter_registry() -> ProactiveSuggestionAdapterRegistry:
    return ProactiveSuggestionAdapterRegistry()


def delegation_adapter_registry() -> ProactiveDelegationAdapterRegistry:
    return ProactiveDelegationAdapterRegistry()


def followup_registry() -> FollowUpDelegationRegistry:
    return FollowUpDelegationRegistry()


def followup_queue() -> FollowUpIntentReviewQueue:
    return FollowUpIntentReviewQueue()


def create_context_authorization(registry: ContextScanCandidateSourceRegistry, **overrides):
    values = {
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "allowed_scan_scopes": DEFAULT_SCOPES,
    }
    values.update(overrides)
    return create_local_context_scan_authorization(registry=registry, **values)


def create_source(registry: ContextScanCandidateSourceRegistry, authorization_id: str, **overrides):
    values = {
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "authorization_id": authorization_id,
        "source_type": "mock_document",
        "source_status": "authorized_local_fixture",
        "scan_scope": "summary_fixture",
        "fixture_id": "fixture-122p-default",
        "source_title": "Default source",
        "source_summary": "Default safe fixture summary.",
        "source_timestamp": "2026-06-20T08:00:00Z",
        "source_hint": "local-only fixture",
        "provenance_notes": "safe fixture summary only",
        "retention_policy": "keep_until_fixture_rotation",
    }
    values.update(overrides)
    return create_context_scan_candidate_source(registry=registry, **values)


def owner_binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "telegram_chat_id": "telegram-chat-122p",
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def unsafe_replace_record(record, **overrides):
    values = {field: getattr(record, field) for field in record.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(record.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


def proactive_flow(source_overrides: dict[str, object]):
    candidate_registry = source_registry()
    opportunity_store = opportunity_registry()
    suggestion_store = suggestion_registry()
    suggestion_adapter_store = suggestion_adapter_registry()
    queue = followup_queue()
    auth = create_context_authorization(candidate_registry)
    source = create_source(candidate_registry, auth.authorization_id, **source_overrides)
    opportunity = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=opportunity_store,
        owner_id="owner-122p",
        robot_id="robot-122p",
    )
    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=suggestion_store,
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
    )
    delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=surface,
        owner_binding=owner_binding(),
        transport=FakeTelegramTransport(),
        registry=suggestion_store,
    )
    suggestion_authorization = authorize_proactive_suggestion_adapter_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        delivery_record_id=delivery.delivery_record_id,
        suggestion_surface_id=surface.suggestion_surface_id,
        opportunity_id=opportunity.opportunity_id,
        registry=suggestion_adapter_store,
    )
    adapter = adapt_proactive_suggestion_to_followup_intent(
        delivery_record=delivery,
        suggestion_registry=suggestion_store,
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        queue=queue,
        adapter_registry=suggestion_adapter_store,
        authorization_record=suggestion_authorization,
        owner_id="owner-122p",
        robot_id="robot-122p",
    )
    return {
        "candidate_registry": candidate_registry,
        "opportunity_registry": opportunity_store,
        "suggestion_registry": suggestion_store,
        "suggestion_adapter_registry": suggestion_adapter_store,
        "followup_queue": queue,
        "source": source,
        "opportunity": opportunity,
        "surface": surface,
        "delivery": delivery,
        "adapter": adapter,
        "followup_intent": queue.get_record(adapter.followup_intent_review_record_id),
    }


def option_id(followup_intent_id: str, option_kind: str) -> str:
    return "option_" + uuid5(NAMESPACE_URL, f"{followup_intent_id}|{option_kind}").hex[:12]


def make_selection(
    *,
    followup_intent_record,
    selected_option_kind: str,
    option_metadata_overrides: dict[str, object] | None = None,
    selection_status: str = "selected_pending_authorization",
) -> TelegramFollowUpChoiceSelectionRecord:
    selected_option_id = option_id(followup_intent_record.followup_intent_id, selected_option_kind)
    cancel_option_id = option_id(followup_intent_record.followup_intent_id, "cancel_followup")
    plan_id = "draft_plan_" + uuid5(NAMESPACE_URL, followup_intent_record.followup_intent_id).hex[:12]
    surface_id = "choice_surface_" + uuid5(NAMESPACE_URL, plan_id).hex[:12]
    selection_id = "selection_" + uuid5(NAMESPACE_URL, f"{surface_id}|{selected_option_id}").hex[:12]

    selected_option = FollowUpDraftOption(
        option_id=selected_option_id,
        label=PASSIVE_BUTTON_LABELS_BY_OPTION_KIND[selected_option_kind],
        description="Local-only proactive follow-up bridge option.",
        option_kind=selected_option_kind,
        local_only=True,
        creates_authority=False,
    )
    cancel_option = FollowUpDraftOption(
        option_id=cancel_option_id,
        label=PASSIVE_BUTTON_LABELS_BY_OPTION_KIND["cancel_followup"],
        description="Cancel without delegating.",
        option_kind="cancel_followup",
        local_only=True,
        creates_authority=False,
    )
    draft_plan = FollowUpDraftPlanRecord(
        draft_plan_id=plan_id,
        followup_intent_id=followup_intent_record.followup_intent_id,
        acknowledgement_id=followup_intent_record.acknowledgement_id,
        delivery_id=followup_intent_record.delivery_id,
        surface_id=followup_intent_record.surface_id,
        inbox_record_id=followup_intent_record.inbox_record_id,
        owner_id=followup_intent_record.owner_id,
        robot_id=followup_intent_record.robot_id,
        telegram_chat_id=followup_intent_record.telegram_chat_id,
        status="drafted",
        title="Proactive delegated follow-up",
        summary="Choose a governed local-only delegation.",
        options=(selected_option, cancel_option),
        lineage_summary={
            "planner_stage": "108P",
            "followup_stage": followup_intent_record.lineage_summary.get("followup_stage"),
            "followup_intent_id": followup_intent_record.followup_intent_id,
            "acknowledgement_stage": followup_intent_record.lineage_summary.get("acknowledgement_stage"),
            "acknowledgement_id": followup_intent_record.acknowledgement_id,
            "delivery_stage": followup_intent_record.lineage_summary.get("delivery_stage"),
            "delivery_id": followup_intent_record.delivery_id,
            "surface_id": followup_intent_record.surface_id,
            "inbox_record_id": followup_intent_record.inbox_record_id,
            "owner_id": followup_intent_record.owner_id,
            "robot_id": followup_intent_record.robot_id,
            "telegram_chat_id": followup_intent_record.telegram_chat_id,
            "source_action": followup_intent_record.source_action,
            "upstream_lineage": deepcopy(followup_intent_record.lineage_summary),
        },
        rejection_reason=None,
    )
    metadata_by_ref = {
        selected_option_id: {
            "option_id": selected_option_id,
            "option_kind": selected_option_kind,
            "label": selected_option.label,
            "local_only": True,
            "creates_authority": False,
            "implies_execution": False,
            "implies_memory_mutation": False,
            "implies_external_send": False,
            "implies_model_call": False,
            "implies_tool_call": False,
            "implies_delegation_creation": False,
            "implies_action_packet_creation": False,
            "implies_approval_creation": False,
        },
        cancel_option_id: {
            "option_id": cancel_option_id,
            "option_kind": "cancel_followup",
            "label": cancel_option.label,
            "local_only": True,
            "creates_authority": False,
            "implies_execution": False,
            "implies_memory_mutation": False,
            "implies_external_send": False,
            "implies_model_call": False,
            "implies_tool_call": False,
            "implies_delegation_creation": False,
            "implies_action_packet_creation": False,
            "implies_approval_creation": False,
        },
    }
    if option_metadata_overrides is not None:
        metadata_by_ref[selected_option_id].update(option_metadata_overrides)
    choice_surface = TelegramFollowUpChoiceSurfaceRecord(
        choice_surface_id=surface_id,
        draft_plan_id=draft_plan.draft_plan_id,
        followup_intent_id=draft_plan.followup_intent_id,
        acknowledgement_id=draft_plan.acknowledgement_id,
        delivery_id=draft_plan.delivery_id,
        source_surface_id=draft_plan.surface_id,
        inbox_record_id=draft_plan.inbox_record_id,
        owner_id=draft_plan.owner_id,
        robot_id=draft_plan.robot_id,
        telegram_chat_id=draft_plan.telegram_chat_id,
        status="delivered",
        text="Rendered proactive follow-up choice surface.",
        button_labels=(selected_option.label, cancel_option.label),
        option_refs=(selected_option_id, cancel_option_id),
        lineage_summary={
            "choice_surface_stage": "109P",
            "draft_planner_stage": "108P",
            "followup_stage": draft_plan.lineage_summary.get("followup_stage"),
            "followup_intent_id": draft_plan.followup_intent_id,
            "acknowledgement_stage": draft_plan.lineage_summary.get("acknowledgement_stage"),
            "acknowledgement_id": draft_plan.acknowledgement_id,
            "delivery_stage": draft_plan.lineage_summary.get("delivery_stage"),
            "delivery_id": draft_plan.delivery_id,
            "source_surface_stage": draft_plan.lineage_summary.get("source_stage", "120P"),
            "source_surface_id": draft_plan.surface_id,
            "inbox_stage": "121P",
            "inbox_record_id": draft_plan.inbox_record_id,
            "telegram_policy_boundary_stage": "95P",
            "owner_id": draft_plan.owner_id,
            "robot_id": draft_plan.robot_id,
            "telegram_chat_id": draft_plan.telegram_chat_id,
            "option_refs": (selected_option_id, cancel_option_id),
            "option_metadata_by_ref": metadata_by_ref,
            "upstream_lineage": deepcopy(draft_plan.lineage_summary),
        },
        transport_receipt={"transport": "fake_telegram_local"},
        rejection_reason=None,
    )
    selection = TelegramFollowUpChoiceSelectionRecord(
        selection_id=selection_id,
        choice_surface_id=choice_surface.choice_surface_id,
        draft_plan_id=choice_surface.draft_plan_id,
        selected_option_id=selected_option_id,
        selected_option_kind=selected_option_kind,
        followup_intent_id=choice_surface.followup_intent_id,
        acknowledgement_id=choice_surface.acknowledgement_id,
        delivery_id=choice_surface.delivery_id,
        source_surface_id=choice_surface.source_surface_id,
        inbox_record_id=choice_surface.inbox_record_id,
        owner_id=choice_surface.owner_id,
        robot_id=choice_surface.robot_id,
        telegram_chat_id=choice_surface.telegram_chat_id,
        status="selected_pending_authorization",
        response_text="Registered local proactive selection only.",
        lineage_summary={
            "selection_stage": "110P",
            "selection_status": "selected_pending_authorization",
            "choice_surface_stage": "109P",
            "choice_surface_id": choice_surface.choice_surface_id,
            "draft_planner_stage": "108P",
            "draft_plan_id": choice_surface.draft_plan_id,
            "followup_stage": choice_surface.lineage_summary.get("followup_stage"),
            "followup_intent_id": choice_surface.followup_intent_id,
            "acknowledgement_stage": choice_surface.lineage_summary.get("acknowledgement_stage"),
            "acknowledgement_id": choice_surface.acknowledgement_id,
            "delivery_stage": choice_surface.lineage_summary.get("delivery_stage"),
            "delivery_id": choice_surface.delivery_id,
            "source_surface_stage": choice_surface.lineage_summary.get("source_surface_stage"),
            "source_surface_id": choice_surface.source_surface_id,
            "inbox_stage": choice_surface.lineage_summary.get("inbox_stage"),
            "inbox_record_id": choice_surface.inbox_record_id,
            "telegram_policy_boundary_stage": "95P",
            "owner_id": choice_surface.owner_id,
            "robot_id": choice_surface.robot_id,
            "telegram_chat_id": choice_surface.telegram_chat_id,
            "selected_option_id": selected_option_id,
            "selected_option_kind": selected_option_kind,
            "upstream_lineage": deepcopy(choice_surface.lineage_summary),
        },
        rejection_reason=None,
    )
    if selection_status != "selected_pending_authorization":
        selection = unsafe_replace_record(
            selection,
            status=selection_status,
            lineage_summary={**selection.lineage_summary, "selection_status": selection_status},
        )
    return selection


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-122p",
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "task_class": "async_delegation",
        "routing_mode": "balanced",
        "sensitivity": "ordinary",
        "requires_tools": False,
        "requires_long_context": False,
        "input_chars_estimate": 1200,
        "expected_output_chars": 800,
        "context_item_count": 2,
        "active_skill_id": "basic_assistant",
        "memory_context_used": True,
        "routine_requested": True,
        "async_delegation_requested": True,
        "authority_expansion_requested": False,
    }
    values.update(overrides)
    return TaskCostRequest(**values)


def synthetic_preflight(
    request: TaskCostRequest,
    *,
    decision: str = "allow",
    selected_model_id: str = "balanced_standard_v1",
) -> CostPreflightResult:
    token_estimate = TokenUsageEstimate(
        estimated_input_tokens=300,
        estimated_output_tokens=220,
        estimated_total_tokens=520,
        estimation_basis="test_fixture",
        long_context_applied=False,
    )
    route = ModelRouteDecision(
        selected_provider_id="local_fixture",
        selected_model_id=selected_model_id,
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=(selected_model_id,),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id=selected_model_id,
        candidate_model_ids=(selected_model_id,),
        decision=decision,
        reason_code="allow_selected_eligible_route" if decision != "require_confirmation" else "confirmation_cost_threshold",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.03,
        budget_state="within_budget" if decision != "require_confirmation" else "confirmation_required",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision=decision,
        budget_policy_id="policy-122p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=decision == "require_confirmation",
        blocked=False,
        trace=(trace,),
    )


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-122p",
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "routing_mode_allowlist": ("economy", "balanced", "premium", "byok"),
        "default_routing_mode": "balanced",
        "max_estimated_cost_usd": 0.08,
        "confirmation_cost_usd": 0.02,
        "max_input_tokens": 4000,
        "max_output_tokens": 1800,
        "long_context_confirmation_tokens": 2400,
        "byok_allowed": False,
        "async_delegation_allowed": True,
        "premium_allowed_without_confirmation": False,
        "allowed_task_classes": (
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
        ),
        "sensitive_task_min_tier": "advanced",
        "unsafe_model_block": True,
        "untrusted_model_block": True,
        "requires_trace": True,
    }
    values.update(overrides)
    return BudgetPolicy(**values)


def approval_decision(packet_state, *, choice: str, occurred_at: str = "2026-06-20T11:05:00Z") -> ActionPacketDecision:
    return ActionPacketDecision(
        packet_id=packet_state.packet.packet_id,
        packet_version=packet_state.packet.packet_version,
        decision=choice,
        actor_id=packet_state.packet.actor_id,
        actor_role=packet_state.packet.actor_role,
        owner_id=packet_state.packet.owner_id,
        robot_id=packet_state.packet.robot_id,
        reason_code=f"{choice}_proactive_delegation",
        edit_payload=None,
        resume_token_id=None,
        occurred_at=occurred_at,
    )


def approved_async_delegation_packet(selection_record, authorization_id, cost_request, policy, preflight):
    from app.followup_delegation_authority import FollowUpDelegationAuthorizationEvidence

    packet_auth = FollowUpDelegationAuthorizationEvidence(
        authorization_id=authorization_id,
        authorization_kind="followup_delegation_authorization",
        selection_id=selection_record.selection_id,
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        selected_option_id=selection_record.selected_option_id,
        selected_option_kind=selection_record.selected_option_kind,
        cost_preflight_request_id=cost_request.request_id,
        approval_evidence_id=None,
        explicit_user_authorized=True,
    )
    request = build_async_delegation_action_packet_request(
        request=register_request(selection_record, packet_auth, cost_request),
        cost_preflight=preflight,
        task_cost_request=cost_request,
        budget_policy=policy,
        actor_id=selection_record.owner_id,
        actor_role="owner_admin",
    )
    approval_state = create_action_packet(request=request, occurred_at="2026-06-20T11:00:00Z")
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=selection_record.owner_id,
        actor_role="owner_admin",
        occurred_at="2026-06-20T11:01:00Z",
    )
    return apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )


def register_request(selection_record, auth, cost_request):
    from app.async_delegation_authority import AsyncDelegationRequest
    from app.followup_delegation_authority import FOLLOWUP_OPTION_KIND_TO_TASK_CLASS

    task_class = FOLLOWUP_OPTION_KIND_TO_TASK_CLASS[selection_record.selected_option_kind]
    delegation_id = "followup_delegation_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                selection_record.selection_id,
                selection_record.selected_option_id,
                selection_record.selected_option_kind,
                selection_record.owner_id,
                selection_record.robot_id,
                selection_record.draft_plan_id,
                selection_record.choice_surface_id,
                auth.cost_preflight_request_id,
                auth.authorization_id,
            ]
        ),
    ).hex[:12]
    return AsyncDelegationRequest(
        delegation_id=delegation_id,
        source_stage="111P",
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        actor_id=selection_record.owner_id,
        actor_role="owner_admin",
        task_class="async_delegation",
        requested_capability=f"prepare_{task_class.lower()}",
        requested_route_mode=cost_request.routing_mode,
        request_payload={
            "followup_task_class": task_class,
            "selected_option_id": selection_record.selected_option_id,
            "selected_option_kind": selection_record.selected_option_kind,
            "selection_id": selection_record.selection_id,
            "draft_plan_id": selection_record.draft_plan_id,
            "choice_surface_id": selection_record.choice_surface_id,
            "acknowledgement_id": selection_record.acknowledgement_id,
            "delivery_id": selection_record.delivery_id,
            "source_surface_id": selection_record.source_surface_id,
            "inbox_record_id": selection_record.inbox_record_id,
            "authorization_id": auth.authorization_id,
            "effect_class": "ASYNC_FOLLOWUP_PREPARATION",
            "send_allowed": False,
        },
        required_policy_trace=("telegram_policy_chain_95p", "followup_delegation_authority_111p"),
        required_memory_projection_request_id=None,
        required_routine_run_id=None,
        expires_at=None,
        authority_expansion_requested=False,
        live_dispatch_requested=False,
    )


@pytest.mark.parametrize(
    ("source_kwargs", "selected_option_kind", "expected_intent_kind", "expected_task_class"),
    [
        (
            {
                "source_type": "mock_message_thread",
                "fixture_id": "fixture-message",
                "source_title": "Support thread",
                "source_summary": "Customer complaint escalation with refund request.",
            },
            "deeper_summary",
            "summarize_context",
            "FOLLOWUP_DEEPER_SUMMARY",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-document",
                "source_title": "NDA draft",
                "source_summary": "Contract review needed before signature.",
            },
            "human_review_checklist",
            "review_document",
            "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        ),
        (
            {
                "source_type": "mock_memory_snapshot",
                "source_status": "authorized_memory_snapshot",
                "scan_scope": "local_test_snapshot",
                "fixture_id": "fixture-boundary",
                "source_title": "Boundary snapshot",
                "source_summary": "Conflicting boundary and robot limit unclear.",
            },
            "human_review_checklist",
            "review_boundary",
            "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        ),
    ],
)
def test_122p_valid_proactive_selection_registers_governed_async_delegation(
    source_kwargs,
    selected_option_kind,
    expected_intent_kind,
    expected_task_class,
):
    flow = proactive_flow(source_kwargs)
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind=selected_option_kind,
    )
    adapter_store = delegation_adapter_registry()
    followup_store = followup_registry()
    task_request = task_cost_request()
    preflight = synthetic_preflight(task_request)
    policy = budget_policy()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=task_request.request_id,
        registry=adapter_store,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        adapter_registry=adapter_store,
        followup_registry=followup_store,
        occurred_at="2026-06-20T12:00:00Z",
    )

    assert record.adapter_status == "delegated_registered"
    assert record.normalized_intent_kind == expected_intent_kind
    assert record.mapped_task_class == expected_task_class
    assert record.owner_id == flow["adapter"].owner_id == "owner-122p"
    assert record.robot_id == flow["adapter"].robot_id == "robot-122p"
    assert record.chat_id == "telegram-chat-122p"
    assert record.followup_intent_review_record_id == flow["adapter"].followup_intent_review_record_id
    assert record.delivery_record_id == flow["adapter"].delivery_record_id
    assert record.suggestion_surface_id == flow["adapter"].suggestion_surface_id
    assert record.opportunity_id == flow["adapter"].opportunity_id
    assert record.candidate_source_id == flow["adapter"].candidate_source_id
    assert record.uses_existing_delegation_authority is True
    assert record.delegation_packet_id is not None
    assert record.delegation_handle_id is not None
    assert record.execution_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.live_connector_allowed is False
    assert record.telegram_send_allowed is False
    assert record.memory_write_allowed is False
    assert record.external_write_allowed is False
    assert record.lineage_summary["upstream_lineage"]["followup_delegation"]["async_delegation_stage"] == "102P"
    assert record.lineage_summary["upstream_lineage"]["followup_delegation"]["followup_delegation_stage"] == "111P"
    followup_records = followup_store.list_records()
    assert len(followup_records) == 1
    assert followup_records[0].status == "registered"


def test_122p_unsupported_prepare_meeting_brief_is_rejected_without_delegation():
    flow = proactive_flow(
        {
            "source_type": "mock_calendar_event",
            "fixture_id": "fixture-calendar",
            "source_title": "Investor sync",
            "source_summary": "Upcoming event with missing brief.",
            "source_hint": "missing brief and empty briefing note",
            "source_timestamp": "2026-06-21T08:00:00Z",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="deeper_summary",
    )
    adapter_store = delegation_adapter_registry()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id="cost-request-122p",
        registry=adapter_store,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_cost_request()),
        task_cost_request=task_cost_request(),
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_registry(),
    )

    assert record.adapter_status == "rejected_unsupported_task_class"
    assert record.delegation_packet_id is None
    assert record.delegation_handle_id is None


def test_122p_duplicate_registration_returns_existing_record():
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
    )
    adapter_store = delegation_adapter_registry()
    followup_store = followup_registry()
    task_request = task_cost_request()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=task_request.request_id,
        registry=adapter_store,
    )

    first = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_request),
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_store,
    )
    second = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_request),
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_store,
    )

    assert second.proactive_delegation_adapter_id == first.proactive_delegation_adapter_id
    assert len(adapter_store.list_records()) == 1
    assert len(followup_store.list_records()) == 1


def test_122p_cancelled_selection_is_rejected():
    flow = proactive_flow(
        {
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="deeper_summary",
        selection_status="cancelled_no_action",
    )
    adapter_store = delegation_adapter_registry()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id="cost-request-122p",
        registry=adapter_store,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_cost_request()),
        task_cost_request=task_cost_request(),
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_registry(),
    )

    assert record.adapter_status == "rejected_cancelled_selection"
    assert record.delegation_handle_id is None


@pytest.mark.parametrize(
    ("authorization_overrides", "expected_reason"),
    [
        ({"granted_by_owner": False}, "rejected_missing_owner_authorization"),
        ({"owner_id": "other-owner"}, "rejected_missing_owner_authorization"),
        ({"robot_id": "other-robot"}, "rejected_invalid_lineage"),
        ({"chat_id": "other-chat"}, "rejected_invalid_lineage"),
    ],
)
def test_122p_authorization_mismatches_are_rejected(authorization_overrides, expected_reason):
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
    )
    adapter_store = delegation_adapter_registry()
    base_kwargs = {
        "owner_id": "owner-122p",
        "robot_id": "robot-122p",
        "chat_id": "telegram-chat-122p",
        "proactive_adapter_id": flow["adapter"].adapter_id,
        "followup_selection_id": selection.selection_id,
        "cost_lineage_id": "cost-request-122p",
        "registry": adapter_store,
    }
    if authorization_overrides.get("granted_by_owner") is False:
        with pytest.raises(ValueError, match=expected_reason):
            authorize_proactive_delegation_registration_local(**base_kwargs, granted_by_owner=False)
        return

    authorization = authorize_proactive_delegation_registration_local(**{**base_kwargs, **authorization_overrides})
    with pytest.raises(ValueError, match=expected_reason):
        register_proactive_delegation_from_existing_selection(
            proactive_adapter_record=flow["adapter"],
            selection_record=selection,
            delegation_authorization_record=authorization,
            cost_preflight_evidence=synthetic_preflight(task_cost_request()),
            task_cost_request=task_cost_request(),
            budget_policy=budget_policy(),
            adapter_registry=adapter_store,
            followup_registry=followup_registry(),
        )


def test_122p_unknown_adapter_and_selection_linkage_mismatch_are_rejected():
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
    )
    adapter_store = delegation_adapter_registry()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id="cost-request-122p",
        registry=adapter_store,
    )

    with pytest.raises(ValueError, match="rejected_invalid_lineage"):
        register_proactive_delegation_from_existing_selection(
            proactive_adapter_record=object(),
            selection_record=selection,
            delegation_authorization_record=authorization,
            cost_preflight_evidence=synthetic_preflight(task_cost_request()),
            task_cost_request=task_cost_request(),
            budget_policy=budget_policy(),
            adapter_registry=adapter_store,
            followup_registry=followup_registry(),
        )

    bad_selection = replace(selection, followup_intent_id="other-followup-intent")
    with pytest.raises(ValueError, match="rejected_invalid_lineage"):
        register_proactive_delegation_from_existing_selection(
            proactive_adapter_record=flow["adapter"],
            selection_record=bad_selection,
            delegation_authorization_record=authorization,
            cost_preflight_evidence=synthetic_preflight(task_cost_request()),
            task_cost_request=task_cost_request(),
            budget_policy=budget_policy(),
            adapter_registry=adapter_store,
            followup_registry=followup_registry(),
        )


def test_122p_sensitive_data_lineage_is_rejected():
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
    )
    unsafe_adapter = unsafe_replace_record(
        flow["adapter"],
        lineage_summary={
            **flow["adapter"].lineage_summary,
            "upstream_lineage": {
                **flow["adapter"].lineage_summary["upstream_lineage"],
                "opportunity": {
                    **flow["adapter"].lineage_summary["upstream_lineage"]["opportunity"],
                    "sensitive_data_blocked": True,
                },
            },
        },
    )
    adapter_store = delegation_adapter_registry()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=unsafe_adapter.adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id="cost-request-122p",
        registry=adapter_store,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=unsafe_adapter,
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_cost_request()),
        task_cost_request=task_cost_request(),
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_registry(),
    )

    assert record.adapter_status == "rejected_sensitive_data"


@pytest.mark.parametrize(
    "metadata_overrides",
    [
        {"requires_live_connector_read": True},
        {"implies_model_call": True},
        {"requires_tool_call": True},
        {"implies_external_write": True},
        {"decision_domain": "payment"},
    ],
)
def test_122p_blocked_option_capabilities_are_rejected(metadata_overrides):
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
        option_metadata_overrides=metadata_overrides,
    )
    adapter_store = delegation_adapter_registry()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id="cost-request-122p",
        registry=adapter_store,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_cost_request()),
        task_cost_request=task_cost_request(),
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_registry(),
    )

    assert record.adapter_status == "rejected_invalid_lineage"
    assert record.delegation_packet_id is None
    assert record.delegation_handle_id is None


def test_122p_preserves_100p_and_101p_lineage_when_approval_is_required():
    flow = proactive_flow(
        {
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="deeper_summary",
        selection_status="explicitly_authorized_for_proactive_delegation",
    )
    adapter_store = delegation_adapter_registry()
    followup_store = followup_registry()
    task_request = task_cost_request()
    preflight = evaluate_cost_preflight(request=task_request, budget_policy=budget_policy())
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=task_request.request_id,
        registry=adapter_store,
    )
    approval = approved_async_delegation_packet(
        selection,
        authorization.authorization_id,
        task_request,
        budget_policy(),
        preflight,
    )
    authorization = unsafe_replace_record(
        authorization,
        action_approval_evidence_id=approval.packet.packet_id,
    )

    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=preflight,
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_store,
        approval_evidence=approval,
    )

    assert record.adapter_status == "delegated_registered"
    followup_lineage = record.lineage_summary["upstream_lineage"]["followup_delegation"]
    assert followup_lineage["cost_preflight_stage"] == "100P"
    assert followup_lineage["approval_stage"] == "101P"
    assert followup_lineage["approval_packet_id"] == approval.packet.packet_id
    assert followup_lineage["async_delegation_stage"] == "102P"


def test_122p_registry_helpers_return_records():
    flow = proactive_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        }
    )
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind="human_review_checklist",
    )
    adapter_store = delegation_adapter_registry()
    task_request = task_cost_request()
    authorization = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=task_request.request_id,
        registry=adapter_store,
    )
    record = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=authorization,
        cost_preflight_evidence=synthetic_preflight(task_request),
        task_cost_request=task_request,
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_registry(),
    )

    assert get_proactive_delegation_adapter_record(
        adapter_registry=adapter_store,
        proactive_delegation_adapter_id=record.proactive_delegation_adapter_id,
    ) == record
    assert list_proactive_delegation_adapter_records(adapter_registry=adapter_store) == (record,)
    assert authorization.authorization_kind == AUTHORIZATION_KIND
    assert authorization.authorization_stage == PROACTIVE_DELEGATION_ADAPTER_STAGE
    assert MODULE_PATH.is_file()
