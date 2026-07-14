from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.action_packet_approval import ActionPacketApprovalState
from app.async_delegation_authority import (
    AsyncDelegationAuthorityState,
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    create_async_delegation_authority_state,
    register_async_delegation_handle,
    serialize_async_delegation_authority_state,
)
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    TaskCostRequest,
    serialize_budget_policy,
    serialize_cost_preflight_result,
    serialize_task_cost_request,
)
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionRecord


FOLLOWUP_DELEGATION_AUTHORITY_STAGE = "111P"
FOLLOWUP_PREPARATION_EFFECT_CLASS = "ASYNC_FOLLOWUP_PREPARATION"
FOLLOWUP_DELEGATION_STATUSES = frozenset({"registered", "duplicate", "blocked", "cancelled_no_action"})
FOLLOWUP_OPTION_KIND_TO_TASK_CLASS = {
    "deeper_summary": "FOLLOWUP_DEEPER_SUMMARY",
    "extract_questions": "FOLLOWUP_EXTRACT_QUESTIONS",
    "human_review_checklist": "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
    "compare_prior_version": "FOLLOWUP_COMPARE_PRIOR_VERSION",
}
FOLLOWUP_OPTION_KIND_TO_ALLOWED_ROUTING_MODES = {
    "deeper_summary": frozenset({"balanced", "premium", "byok"}),
    "extract_questions": frozenset({"balanced", "premium", "byok"}),
    "human_review_checklist": frozenset({"balanced", "premium", "byok"}),
    "compare_prior_version": frozenset({"balanced", "premium", "byok"}),
}
FOLLOWUP_OPTION_KIND_TO_ALLOWED_MODEL_IDS = {
    "deeper_summary": frozenset({"balanced_standard_v1", "advanced_reasoning_v1", "premium_strong_v1", "local-test-model"}),
    "extract_questions": frozenset({"balanced_standard_v1", "advanced_reasoning_v1", "premium_strong_v1", "local-test-model"}),
    "human_review_checklist": frozenset({"balanced_standard_v1", "advanced_reasoning_v1", "premium_strong_v1", "local-test-model"}),
    "compare_prior_version": frozenset({"balanced_standard_v1", "advanced_reasoning_v1", "premium_strong_v1", "local-test-model"}),
}
FORBIDDEN_OPTION_FLAGS = {
    "creates_authority": "blocked_authority_expanding_option",
    "implies_execution": "blocked_authority_expanding_option",
    "implies_memory_mutation": "blocked_memory_mutating_option",
    "implies_external_send": "blocked_external_effect_option",
    "implies_model_call": "blocked_external_effect_option",
    "implies_tool_call": "blocked_external_effect_option",
    "implies_delegation_creation": "blocked_authority_expanding_option",
    "implies_action_packet_creation": "blocked_authority_expanding_option",
    "implies_approval_creation": "blocked_authority_expanding_option",
}


@dataclass(frozen=True, slots=True)
class FollowUpDelegationAuthorizationEvidence:
    authorization_id: str
    authorization_kind: str
    selection_id: str
    owner_id: str
    robot_id: str
    selected_option_id: str
    selected_option_kind: str
    cost_preflight_request_id: str
    approval_evidence_id: str | None
    explicit_user_authorized: bool


@dataclass(frozen=True, slots=True)
class FollowUpDelegationRequestRecord:
    followup_delegation_id: str
    selection_id: str
    selected_option_id: str
    selected_option_kind: str
    followup_task_class: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    draft_plan_id: str
    choice_surface_id: str
    acknowledgement_id: str
    delivery_id: str
    source_surface_id: str
    inbox_record_id: str
    status: str
    async_packet_id: str | None
    async_handle_id: str | None
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in FOLLOWUP_DELEGATION_STATUSES:
            raise ValueError("Unsupported 111P follow-up delegation status.")


@dataclass(frozen=True, slots=True)
class FollowUpDelegationResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("111P only supports local Telegram-compatible response envelopes.")
        if self.send_allowed is not False:
            raise ValueError("111P response envelopes must keep send_allowed false.")


@dataclass(slots=True)
class FollowUpDelegationRegistry:
    records_by_id: dict[str, FollowUpDelegationRequestRecord] = field(default_factory=dict)
    authority_states_by_id: dict[str, AsyncDelegationAuthorityState] = field(default_factory=dict)

    def get_record(self, followup_delegation_id: str) -> FollowUpDelegationRequestRecord | None:
        return self.records_by_id.get(followup_delegation_id)

    def get_authority_state(self, followup_delegation_id: str) -> AsyncDelegationAuthorityState | None:
        return self.authority_states_by_id.get(followup_delegation_id)

    def store(
        self,
        record: FollowUpDelegationRequestRecord,
        *,
        authority_state: AsyncDelegationAuthorityState | None = None,
    ) -> FollowUpDelegationRequestRecord:
        self.records_by_id[record.followup_delegation_id] = record
        if authority_state is not None:
            self.authority_states_by_id[record.followup_delegation_id] = authority_state
        return record

    def list_records(self) -> tuple[FollowUpDelegationRequestRecord, ...]:
        return tuple(self.records_by_id[key] for key in sorted(self.records_by_id))


def create_followup_delegation_from_selection(
    *,
    selection_record: object,
    authorization_evidence: object | None,
    cost_preflight_evidence: object | None,
    task_cost_request: object | None,
    budget_policy: object | None,
    approval_evidence: object | None,
    followup_registry: FollowUpDelegationRegistry,
    occurred_at: str,
) -> FollowUpDelegationRequestRecord:
    seed_selection = selection_record if isinstance(selection_record, TelegramFollowUpChoiceSelectionRecord) else None
    seed_authorization = authorization_evidence if isinstance(authorization_evidence, FollowUpDelegationAuthorizationEvidence) else None
    followup_delegation_id = _followup_delegation_id(
        selection_record=seed_selection,
        authorization_evidence=seed_authorization,
    )
    existing = followup_registry.get_record(followup_delegation_id)
    if existing is not None:
        return existing

    if not isinstance(selection_record, TelegramFollowUpChoiceSelectionRecord):
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=None,
                followup_task_class="",
                rejection_reason="blocked_unknown_selection_record",
            )
        )

    followup_task_class = FOLLOWUP_OPTION_KIND_TO_TASK_CLASS.get(selection_record.selected_option_kind, "")
    if selection_record.status == "cancelled_no_action" or selection_record.selected_option_kind == "cancel_followup":
        return followup_registry.store(
            _cancelled_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
            )
        )

    selection_rejection = _selection_block_reason(selection_record=selection_record)
    if selection_rejection is not None:
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason=selection_rejection,
            )
        )

    if not isinstance(authorization_evidence, FollowUpDelegationAuthorizationEvidence):
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason="blocked_missing_followup_delegation_authorization",
            )
        )

    authorization_rejection = _authorization_block_reason(
        selection_record=selection_record,
        authorization_evidence=authorization_evidence,
    )
    if authorization_rejection is not None:
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason=authorization_rejection,
            )
        )

    if not isinstance(cost_preflight_evidence, CostPreflightResult):
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason="blocked_missing_cost_preflight_lineage",
            )
        )
    if not isinstance(task_cost_request, TaskCostRequest):
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason="blocked_missing_cost_preflight_task_request",
            )
        )
    if not isinstance(budget_policy, BudgetPolicy):
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason="blocked_missing_budget_policy",
            )
        )

    cost_rejection = _cost_lineage_block_reason(
        selection_record=selection_record,
        authorization_evidence=authorization_evidence,
        cost_preflight_evidence=cost_preflight_evidence,
        task_cost_request=task_cost_request,
        budget_policy=budget_policy,
    )
    if cost_rejection is not None:
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason=cost_rejection,
            )
        )

    approval_required = cost_preflight_evidence.decision == "require_confirmation"
    if approval_required:
        approval_rejection = _approval_block_reason(
            selection_record=selection_record,
            authorization_evidence=authorization_evidence,
            approval_evidence=approval_evidence,
        )
        if approval_rejection is not None:
            return followup_registry.store(
                _blocked_record(
                    followup_delegation_id=followup_delegation_id,
                    selection_record=selection_record,
                    followup_task_class=followup_task_class,
                    rejection_reason=approval_rejection,
                )
            )

    authority_state = create_async_delegation_authority_state(
        request=_build_async_request(
            followup_delegation_id=followup_delegation_id,
            selection_record=selection_record,
            authorization_evidence=authorization_evidence,
            task_cost_request=task_cost_request,
            followup_task_class=followup_task_class,
        ),
        task_cost_request=task_cost_request,
        budget_policy=budget_policy,
        cost_preflight=cost_preflight_evidence,
        occurred_at=occurred_at,
    )
    if approval_required:
        assert isinstance(approval_evidence, ActionPacketApprovalState)
        authority_state = bind_async_delegation_approval(
            authority_state=authority_state,
            approval_state=approval_evidence,
            occurred_at=occurred_at,
        )
    authority_state = register_async_delegation_handle(
        authority_state=authority_state,
        occurred_at=occurred_at,
    )
    if authority_state.packet.state != "registered" or authority_state.handle is None:
        return followup_registry.store(
            _blocked_record(
                followup_delegation_id=followup_delegation_id,
                selection_record=selection_record,
                followup_task_class=followup_task_class,
                rejection_reason=authority_state.trace_records[-1].reason_code,
            ),
            authority_state=authority_state,
        )

    record = FollowUpDelegationRequestRecord(
        followup_delegation_id=followup_delegation_id,
        selection_id=selection_record.selection_id,
        selected_option_id=selection_record.selected_option_id,
        selected_option_kind=selection_record.selected_option_kind,
        followup_task_class=followup_task_class,
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        telegram_chat_id=selection_record.telegram_chat_id,
        draft_plan_id=selection_record.draft_plan_id,
        choice_surface_id=selection_record.choice_surface_id,
        acknowledgement_id=selection_record.acknowledgement_id,
        delivery_id=selection_record.delivery_id,
        source_surface_id=selection_record.source_surface_id,
        inbox_record_id=selection_record.inbox_record_id,
        status="registered",
        async_packet_id=_async_packet_id(authority_state=authority_state),
        async_handle_id=authority_state.handle.handle_id,
        lineage_summary=_lineage_summary(
            selection_record=selection_record,
            authorization_evidence=authorization_evidence,
            cost_preflight_evidence=cost_preflight_evidence,
            task_cost_request=task_cost_request,
            budget_policy=budget_policy,
            approval_evidence=approval_evidence if isinstance(approval_evidence, ActionPacketApprovalState) else None,
            authority_state=authority_state,
            followup_task_class=followup_task_class,
            status="registered",
        ),
        rejection_reason=None,
    )
    return followup_registry.store(record, authority_state=authority_state)


def build_followup_delegation_response_envelope(
    record: FollowUpDelegationRequestRecord,
) -> FollowUpDelegationResponseEnvelope:
    if record.status == "registered":
        text = "Registre tu seguimiento autorizado para preparacion async. Todavia no ejecute nada."
    elif record.status == "cancelled_no_action":
        text = "No tome ninguna accion de seguimiento."
    else:
        text = "No pude registrar ese seguimiento en esta version."
    return FollowUpDelegationResponseEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=text,
        send_allowed=False,
    )


def _selection_block_reason(selection_record: TelegramFollowUpChoiceSelectionRecord) -> str | None:
    if selection_record.status == "blocked":
        return selection_record.rejection_reason or "blocked_selection_record"
    if selection_record.status == "duplicate":
        return "blocked_duplicate_only_selection"
    if selection_record.status != "selected_pending_authorization":
        return f"blocked_selection_status_{selection_record.status}"
    if selection_record.selected_option_kind not in FOLLOWUP_OPTION_KIND_TO_TASK_CLASS:
        return "blocked_unknown_option_kind"
    if selection_record.lineage_summary.get("choice_surface_id") != selection_record.choice_surface_id:
        return "blocked_choice_surface_mismatch"
    if selection_record.lineage_summary.get("draft_plan_id") != selection_record.draft_plan_id:
        return "blocked_draft_plan_mismatch"
    if selection_record.lineage_summary.get("owner_id") != selection_record.owner_id:
        return "blocked_owner_mismatch"
    if selection_record.lineage_summary.get("robot_id") != selection_record.robot_id:
        return "blocked_robot_mismatch"
    if selection_record.lineage_summary.get("telegram_chat_id") != selection_record.telegram_chat_id:
        return "blocked_selection_chat_mismatch"

    option_metadata = _selected_option_metadata(selection_record=selection_record)
    if option_metadata is None:
        return "blocked_unknown_selected_option_id"
    if option_metadata.get("option_id") != selection_record.selected_option_id:
        return "blocked_selected_option_mismatch"
    if option_metadata.get("option_kind") != selection_record.selected_option_kind:
        return "blocked_selected_option_mismatch"
    if option_metadata.get("local_only") is not True:
        return "blocked_non_local_followup_option"
    for key, rejection_reason in FORBIDDEN_OPTION_FLAGS.items():
        if bool(option_metadata.get(key)):
            return rejection_reason
    return None


def _authorization_block_reason(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence,
) -> str | None:
    if authorization_evidence.authorization_kind != "followup_delegation_authorization":
        return "blocked_invalid_followup_delegation_authorization"
    if authorization_evidence.explicit_user_authorized is not True:
        return "blocked_explicit_followup_authorization_required"
    if authorization_evidence.selection_id != selection_record.selection_id:
        return "blocked_selection_id_mismatch"
    if authorization_evidence.owner_id != selection_record.owner_id:
        return "blocked_owner_mismatch"
    if authorization_evidence.robot_id != selection_record.robot_id:
        return "blocked_robot_mismatch"
    if authorization_evidence.selected_option_id != selection_record.selected_option_id:
        return "blocked_selected_option_mismatch"
    if authorization_evidence.selected_option_kind != selection_record.selected_option_kind:
        return "blocked_selected_option_mismatch"
    return None


def _cost_lineage_block_reason(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence,
    cost_preflight_evidence: CostPreflightResult,
    task_cost_request: TaskCostRequest,
    budget_policy: BudgetPolicy,
) -> str | None:
    if cost_preflight_evidence.request_id != authorization_evidence.cost_preflight_request_id:
        return "blocked_cost_preflight_request_id_mismatch"
    if task_cost_request.request_id != cost_preflight_evidence.request_id:
        return "blocked_cost_preflight_request_id_mismatch"
    if task_cost_request.owner_id != selection_record.owner_id or budget_policy.owner_id != selection_record.owner_id:
        return "blocked_owner_mismatch"
    if task_cost_request.robot_id != selection_record.robot_id or budget_policy.robot_id != selection_record.robot_id:
        return "blocked_robot_mismatch"
    if task_cost_request.task_class != "async_delegation":
        return "blocked_cost_preflight_task_class_mismatch"
    if task_cost_request.async_delegation_requested is not True:
        return "blocked_async_delegation_not_requested"
    if task_cost_request.authority_expansion_requested:
        return "blocked_authority_expansion_attempt"
    if budget_policy.async_delegation_allowed is not True:
        return "blocked_async_delegation_disabled_by_policy"
    if cost_preflight_evidence.decision == "block" or cost_preflight_evidence.blocked:
        return cost_preflight_evidence.trace[-1].reason_code
    allowed_modes = FOLLOWUP_OPTION_KIND_TO_ALLOWED_ROUTING_MODES[selection_record.selected_option_kind]
    if task_cost_request.routing_mode not in allowed_modes:
        return "blocked_selected_route_mismatch"
    route = cost_preflight_evidence.route_decision
    if route is None or route.selected_model_id is None:
        return "blocked_selected_route_mismatch"
    if route.selected_model_id not in FOLLOWUP_OPTION_KIND_TO_ALLOWED_MODEL_IDS[selection_record.selected_option_kind]:
        return "blocked_selected_route_mismatch"
    return None


def _approval_block_reason(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence,
    approval_evidence: object | None,
) -> str | None:
    if not isinstance(approval_evidence, ActionPacketApprovalState):
        return "blocked_missing_required_approval_evidence"
    if approval_evidence.packet.action_type != "async_delegation":
        return "blocked_generic_approval_evidence_does_not_bind"
    if approval_evidence.packet.state != "approved" or approval_evidence.resume_token is None:
        return "blocked_missing_required_approval_evidence"
    if approval_evidence.packet.owner_id != selection_record.owner_id:
        return "blocked_owner_mismatch"
    if approval_evidence.packet.robot_id != selection_record.robot_id:
        return "blocked_robot_mismatch"
    if authorization_evidence.approval_evidence_id not in {approval_evidence.packet.packet_id, approval_evidence.resume_token.token_id}:
        return "blocked_approval_evidence_mismatch"
    return None


def _build_async_request(
    *,
    followup_delegation_id: str,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence,
    task_cost_request: TaskCostRequest,
    followup_task_class: str,
) -> AsyncDelegationRequest:
    requested_capability = f"prepare_{followup_task_class.lower()}"
    return AsyncDelegationRequest(
        delegation_id=followup_delegation_id,
        source_stage=FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        actor_id=selection_record.owner_id,
        actor_role="owner_admin",
        task_class="async_delegation",
        requested_capability=requested_capability,
        requested_route_mode=task_cost_request.routing_mode,
        request_payload={
            "followup_task_class": followup_task_class,
            "selected_option_id": selection_record.selected_option_id,
            "selected_option_kind": selection_record.selected_option_kind,
            "selection_id": selection_record.selection_id,
            "draft_plan_id": selection_record.draft_plan_id,
            "choice_surface_id": selection_record.choice_surface_id,
            "acknowledgement_id": selection_record.acknowledgement_id,
            "delivery_id": selection_record.delivery_id,
            "source_surface_id": selection_record.source_surface_id,
            "inbox_record_id": selection_record.inbox_record_id,
            "authorization_id": authorization_evidence.authorization_id,
            "effect_class": FOLLOWUP_PREPARATION_EFFECT_CLASS,
            "send_allowed": False,
        },
        required_policy_trace=("telegram_policy_chain_95p", "followup_delegation_authority_111p"),
        required_memory_projection_request_id=None,
        required_routine_run_id=None,
        expires_at=None,
        authority_expansion_requested=False,
        live_dispatch_requested=False,
    )


def _lineage_summary(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence,
    cost_preflight_evidence: CostPreflightResult,
    task_cost_request: TaskCostRequest,
    budget_policy: BudgetPolicy,
    approval_evidence: ActionPacketApprovalState | None,
    authority_state: AsyncDelegationAuthorityState,
    followup_task_class: str,
    status: str,
) -> dict[str, object]:
    serialized_state = serialize_async_delegation_authority_state(authority_state)
    packet = serialized_state["packet"]
    handle = serialized_state["handle"]
    return {
        "followup_delegation_stage": FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
        "selection_stage": selection_record.lineage_summary.get("selection_stage"),
        "selection_id": selection_record.selection_id,
        "selected_option_id": selection_record.selected_option_id,
        "selected_option_kind": selection_record.selected_option_kind,
        "followup_task_class": followup_task_class,
        "status": status,
        "choice_surface_stage": selection_record.lineage_summary.get("choice_surface_stage"),
        "choice_surface_id": selection_record.choice_surface_id,
        "draft_planner_stage": selection_record.lineage_summary.get("draft_planner_stage"),
        "draft_plan_id": selection_record.draft_plan_id,
        "followup_stage": selection_record.lineage_summary.get("followup_stage"),
        "followup_intent_id": selection_record.followup_intent_id,
        "acknowledgement_stage": selection_record.lineage_summary.get("acknowledgement_stage"),
        "acknowledgement_id": selection_record.acknowledgement_id,
        "delivery_stage": selection_record.lineage_summary.get("delivery_stage"),
        "delivery_id": selection_record.delivery_id,
        "source_surface_stage": selection_record.lineage_summary.get("source_surface_stage"),
        "source_surface_id": selection_record.source_surface_id,
        "inbox_stage": selection_record.lineage_summary.get("inbox_stage"),
        "inbox_record_id": selection_record.inbox_record_id,
        "owner_id": selection_record.owner_id,
        "robot_id": selection_record.robot_id,
        "telegram_chat_id": selection_record.telegram_chat_id,
        "authorization_id": authorization_evidence.authorization_id,
        "authorization_kind": authorization_evidence.authorization_kind,
        "authorization_stage": FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
        "cost_preflight_stage": "100P",
        "cost_preflight_request_id": cost_preflight_evidence.request_id,
        "cost_preflight_summary": serialize_cost_preflight_result(cost_preflight_evidence),
        "task_cost_request_summary": serialize_task_cost_request(task_cost_request),
        "budget_policy_summary": serialize_budget_policy(budget_policy),
        "approval_stage": None if approval_evidence is None else "101P",
        "approval_packet_id": None if approval_evidence is None else approval_evidence.packet.packet_id,
        "approval_resume_token_id": None if approval_evidence is None or approval_evidence.resume_token is None else approval_evidence.resume_token.token_id,
        "async_delegation_stage": authority_state.stage,
        "async_packet_id": _async_packet_id(authority_state=authority_state),
        "async_handle_id": None if handle is None else handle["handle_id"],
        "async_packet_summary": {
            "delegation_id": packet["delegation_id"],
            "packet_version": packet["packet_version"],
            "state": packet["state"],
            "decision": packet["decision"],
            "source_stage": packet["source_stage"],
            "task_class": packet["task_class"],
            "selected_provider_id": packet["selected_provider_id"],
            "selected_model_id": packet["selected_model_id"],
            "action_packet_id": packet["action_packet_id"],
            "approval_resume_token_id": packet["approval_resume_token_id"],
            "non_dispatching": packet["non_dispatching"],
            "execution_authorized": packet["execution_authorized"],
            "provider_call_authorized": packet["provider_call_authorized"],
            "external_effect_authorized": packet["external_effect_authorized"],
            "live_dispatch_authorized": packet["live_dispatch_authorized"],
        },
        "upstream_lineage": selection_record.lineage_summary,
    }


def _cancelled_record(
    *,
    followup_delegation_id: str,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
) -> FollowUpDelegationRequestRecord:
    return FollowUpDelegationRequestRecord(
        followup_delegation_id=followup_delegation_id,
        selection_id=selection_record.selection_id,
        selected_option_id=selection_record.selected_option_id,
        selected_option_kind=selection_record.selected_option_kind,
        followup_task_class="",
        owner_id=selection_record.owner_id,
        robot_id=selection_record.robot_id,
        telegram_chat_id=selection_record.telegram_chat_id,
        draft_plan_id=selection_record.draft_plan_id,
        choice_surface_id=selection_record.choice_surface_id,
        acknowledgement_id=selection_record.acknowledgement_id,
        delivery_id=selection_record.delivery_id,
        source_surface_id=selection_record.source_surface_id,
        inbox_record_id=selection_record.inbox_record_id,
        status="cancelled_no_action",
        async_packet_id=None,
        async_handle_id=None,
        lineage_summary={
            "followup_delegation_stage": FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
            "selection_stage": selection_record.lineage_summary.get("selection_stage"),
            "selection_id": selection_record.selection_id,
            "selected_option_kind": selection_record.selected_option_kind,
            "owner_id": selection_record.owner_id,
            "robot_id": selection_record.robot_id,
            "telegram_chat_id": selection_record.telegram_chat_id,
            "upstream_lineage": selection_record.lineage_summary,
        },
        rejection_reason=None,
    )


def _blocked_record(
    *,
    followup_delegation_id: str,
    selection_record: TelegramFollowUpChoiceSelectionRecord | None,
    followup_task_class: str,
    rejection_reason: str,
) -> FollowUpDelegationRequestRecord:
    return FollowUpDelegationRequestRecord(
        followup_delegation_id=followup_delegation_id,
        selection_id="" if selection_record is None else selection_record.selection_id,
        selected_option_id="" if selection_record is None else selection_record.selected_option_id,
        selected_option_kind="" if selection_record is None else selection_record.selected_option_kind,
        followup_task_class=followup_task_class,
        owner_id="" if selection_record is None else selection_record.owner_id,
        robot_id="" if selection_record is None else selection_record.robot_id,
        telegram_chat_id="" if selection_record is None else selection_record.telegram_chat_id,
        draft_plan_id="" if selection_record is None else selection_record.draft_plan_id,
        choice_surface_id="" if selection_record is None else selection_record.choice_surface_id,
        acknowledgement_id="" if selection_record is None else selection_record.acknowledgement_id,
        delivery_id="" if selection_record is None else selection_record.delivery_id,
        source_surface_id="" if selection_record is None else selection_record.source_surface_id,
        inbox_record_id="" if selection_record is None else selection_record.inbox_record_id,
        status="blocked",
        async_packet_id=None,
        async_handle_id=None,
        lineage_summary={
            "followup_delegation_stage": FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
            "selection_id": None if selection_record is None else selection_record.selection_id,
            "selected_option_id": None if selection_record is None else selection_record.selected_option_id,
            "selected_option_kind": None if selection_record is None else selection_record.selected_option_kind,
            "owner_id": None if selection_record is None else selection_record.owner_id,
            "robot_id": None if selection_record is None else selection_record.robot_id,
            "telegram_chat_id": None if selection_record is None else selection_record.telegram_chat_id,
            "upstream_lineage": None if selection_record is None else selection_record.lineage_summary,
        },
        rejection_reason=rejection_reason,
    )


def _selected_option_metadata(selection_record: TelegramFollowUpChoiceSelectionRecord) -> dict[str, object] | None:
    upstream = selection_record.lineage_summary.get("upstream_lineage")
    if not isinstance(upstream, dict):
        return None
    metadata_by_ref = upstream.get("option_metadata_by_ref")
    if not isinstance(metadata_by_ref, dict):
        return None
    entry = metadata_by_ref.get(selection_record.selected_option_id)
    if not isinstance(entry, dict):
        return None
    return dict(entry)


def _followup_delegation_id(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord | None,
    authorization_evidence: FollowUpDelegationAuthorizationEvidence | None,
) -> str:
    if selection_record is None and authorization_evidence is None:
        return _stable_id("followup_delegation", "unknown")
    return _stable_id(
        "followup_delegation",
        "" if selection_record is None else selection_record.selection_id,
        "" if selection_record is None else selection_record.selected_option_id,
        "" if selection_record is None else selection_record.selected_option_kind,
        "" if selection_record is None else selection_record.owner_id,
        "" if selection_record is None else selection_record.robot_id,
        "" if selection_record is None else selection_record.draft_plan_id,
        "" if selection_record is None else selection_record.choice_surface_id,
        "" if authorization_evidence is None else authorization_evidence.cost_preflight_request_id,
        "" if authorization_evidence is None else authorization_evidence.authorization_id,
    )


def _async_packet_id(*, authority_state: AsyncDelegationAuthorityState) -> str:
    return f"{authority_state.packet.delegation_id}:v{authority_state.packet.packet_version}"


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
