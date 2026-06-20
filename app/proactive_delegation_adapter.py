from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import NAMESPACE_URL, uuid5

from app.action_packet_approval import ActionPacketApprovalState
from app.context_scan_candidate_source import CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE
from app.cost_governor import BudgetPolicy, CostPreflightResult, TaskCostRequest
from app.followup_delegation_authority import (
    FOLLOWUP_OPTION_KIND_TO_TASK_CLASS,
    FollowUpDelegationAuthorizationEvidence,
    FollowUpDelegationRegistry,
    create_followup_delegation_from_selection,
)
from app.proactive_opportunity_detection import PROACTIVE_OPPORTUNITY_DETECTION_STAGE
from app.proactive_suggestion_adapter import (
    PROACTIVE_SUGGESTION_ADAPTER_STAGE,
    ProactiveSuggestionFollowupAdapterRecord,
)
from app.proactive_telegram_suggestion import PROACTIVE_TELEGRAM_SUGGESTION_STAGE
from app.telegram_followup_choice_selection import (
    TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE,
    TelegramFollowUpChoiceSelectionRecord,
)


PROACTIVE_DELEGATION_ADAPTER_STAGE = "122P"
DEFAULT_RECORD_CREATED_AT = "2026-06-20T00:00:00Z"
AUTHORIZATION_KIND = "authorize_proactive_delegation_registration"

ADAPTER_STATUSES = frozenset(
    {
        "delegated_registered",
        "duplicate_existing",
        "rejected_invalid_lineage",
        "rejected_missing_owner_authorization",
        "rejected_unsupported_task_class",
        "rejected_sensitive_data",
        "rejected_cancelled_selection",
    }
)
ALLOWED_SELECTION_STATUSES = frozenset(
    {
        "selected_pending_authorization",
        "explicitly_authorized_for_proactive_delegation",
    }
)
ALLOWED_INTENT_KINDS = frozenset(
    {
        "prepare_meeting_brief",
        "review_document",
        "draft_followup",
        "prepare_checklist",
        "summarize_context",
        "review_memory_gap",
        "review_boundary",
    }
)
INTENT_KIND_TO_ALLOWED_OPTION_KIND = {
    "summarize_context": "deeper_summary",
    "review_document": "human_review_checklist",
    "review_boundary": "human_review_checklist",
    "draft_followup": "extract_questions",
    "prepare_checklist": "human_review_checklist",
    "review_memory_gap": "human_review_checklist",
}
HIGH_RISK_DECISION_DOMAINS = frozenset({"payment", "refund", "legal", "tax", "medical", "employment"})
HIGH_RISK_OPTION_FLAGS = frozenset(
    {
        "implies_payment_decision",
        "implies_refund_decision",
        "implies_legal_decision",
        "implies_tax_decision",
        "implies_medical_decision",
        "implies_employment_decision",
        "requires_live_connector_read",
        "implies_live_connector_read",
        "implies_external_write",
        "requires_model_call",
        "requires_tool_call",
    }
)


@dataclass(frozen=True, slots=True)
class ProactiveDelegationAuthorizationRecord:
    authorization_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    proactive_adapter_id: str
    followup_selection_id: str
    authorization_kind: str
    granted_by_owner: bool
    authorization_stage: str
    cost_lineage_id: str
    action_approval_evidence_id: str | None
    created_at: str

    def __post_init__(self) -> None:
        if self.authorization_kind != AUTHORIZATION_KIND:
            raise ValueError("rejected_invalid_authorization_kind")
        if self.granted_by_owner is not True:
            raise ValueError("rejected_missing_owner_authorization")
        if self.authorization_stage != PROACTIVE_DELEGATION_ADAPTER_STAGE:
            raise ValueError("rejected_invalid_authorization_stage")
        if not self.owner_id:
            raise ValueError("rejected_unknown_owner")
        if not self.robot_id:
            raise ValueError("rejected_unknown_robot")
        if not self.chat_id:
            raise ValueError("rejected_missing_chat_id")
        if not self.proactive_adapter_id:
            raise ValueError("rejected_missing_proactive_adapter_id")
        if not self.followup_selection_id:
            raise ValueError("rejected_missing_followup_selection_id")
        if not self.cost_lineage_id:
            raise ValueError("rejected_missing_cost_lineage")


@dataclass(frozen=True, slots=True)
class ProactiveDelegationAdapterRecord:
    proactive_delegation_adapter_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    proactive_adapter_id: str
    delivery_record_id: str
    suggestion_surface_id: str
    opportunity_id: str
    candidate_source_id: str
    source_authorization_id: str
    source_stage: str
    detection_stage: str
    suggestion_stage: str
    adapter_stage: str
    delegation_adapter_stage: str
    followup_intent_review_record_id: str
    followup_plan_id: str
    followup_choice_surface_id: str
    followup_selection_id: str
    explicit_owner_delegation_authorization_id: str
    normalized_intent_kind: str
    selected_option_id: str
    mapped_task_class: str
    delegation_packet_id: str | None
    delegation_handle_id: str | None
    adapter_status: str
    uses_existing_delegation_authority: bool
    execution_allowed: bool
    worker_dispatch_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    live_connector_allowed: bool
    telegram_send_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
            raise ValueError("rejected_invalid_source_stage")
        if self.detection_stage != PROACTIVE_OPPORTUNITY_DETECTION_STAGE:
            raise ValueError("rejected_invalid_detection_stage")
        if self.suggestion_stage != PROACTIVE_TELEGRAM_SUGGESTION_STAGE:
            raise ValueError("rejected_invalid_suggestion_stage")
        if self.adapter_stage != PROACTIVE_SUGGESTION_ADAPTER_STAGE:
            raise ValueError("rejected_invalid_adapter_stage")
        if self.delegation_adapter_stage != PROACTIVE_DELEGATION_ADAPTER_STAGE:
            raise ValueError("rejected_invalid_delegation_adapter_stage")
        if self.normalized_intent_kind not in ALLOWED_INTENT_KINDS:
            raise ValueError("rejected_invalid_normalized_intent_kind")
        if self.adapter_status not in ADAPTER_STATUSES:
            raise ValueError("rejected_invalid_adapter_status")
        if self.uses_existing_delegation_authority is not True:
            raise ValueError("rejected_parallel_authority_not_allowed")
        if any(
            (
                self.execution_allowed,
                self.worker_dispatch_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.live_connector_allowed,
                self.telegram_send_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ProactiveDelegationAdapterRegistry:
    authorizations_by_id: dict[str, ProactiveDelegationAuthorizationRecord] = field(default_factory=dict)
    records_by_id: dict[str, ProactiveDelegationAdapterRecord] = field(default_factory=dict)
    record_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_authorization(
        self,
        record: ProactiveDelegationAuthorizationRecord,
    ) -> ProactiveDelegationAuthorizationRecord:
        self.authorizations_by_id[record.authorization_id] = record
        return record

    def get_authorization(self, authorization_id: str) -> ProactiveDelegationAuthorizationRecord | None:
        return self.authorizations_by_id.get(authorization_id)

    def store_record(self, record: ProactiveDelegationAdapterRecord) -> ProactiveDelegationAdapterRecord:
        self.records_by_id[record.proactive_delegation_adapter_id] = record
        self.record_ids_by_dedupe_key[record.dedupe_key] = record.proactive_delegation_adapter_id
        return record

    def get_record(self, proactive_delegation_adapter_id: str) -> ProactiveDelegationAdapterRecord | None:
        return self.records_by_id.get(proactive_delegation_adapter_id)

    def get_record_by_dedupe_key(self, dedupe_key: str) -> ProactiveDelegationAdapterRecord | None:
        record_id = self.record_ids_by_dedupe_key.get(dedupe_key)
        if record_id is None:
            return None
        return self.records_by_id.get(record_id)

    def list_records(self) -> tuple[ProactiveDelegationAdapterRecord, ...]:
        return tuple(self.records_by_id[key] for key in sorted(self.records_by_id))


def authorize_proactive_delegation_registration_local(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    proactive_adapter_id: str,
    followup_selection_id: str,
    cost_lineage_id: str,
    registry: ProactiveDelegationAdapterRegistry,
    action_approval_evidence_id: str | None = None,
    granted_by_owner: bool = True,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveDelegationAuthorizationRecord:
    authorization_id = _stable_id(
        "proactive_delegation_authorization",
        owner_id,
        robot_id,
        chat_id,
        proactive_adapter_id,
        followup_selection_id,
        cost_lineage_id,
        action_approval_evidence_id or "no-approval",
        AUTHORIZATION_KIND,
    )
    existing = registry.get_authorization(authorization_id)
    if existing is not None:
        return existing
    return registry.store_authorization(
        ProactiveDelegationAuthorizationRecord(
            authorization_id=authorization_id,
            owner_id=owner_id,
            robot_id=robot_id,
            chat_id=chat_id,
            proactive_adapter_id=proactive_adapter_id,
            followup_selection_id=followup_selection_id,
            authorization_kind=AUTHORIZATION_KIND,
            granted_by_owner=granted_by_owner,
            authorization_stage=PROACTIVE_DELEGATION_ADAPTER_STAGE,
            cost_lineage_id=cost_lineage_id,
            action_approval_evidence_id=action_approval_evidence_id,
            created_at=created_at,
        )
    )


def register_proactive_delegation_from_existing_selection(
    *,
    proactive_adapter_record: object,
    selection_record: object,
    delegation_authorization_record: object,
    cost_preflight_evidence: object | None,
    task_cost_request: object | None,
    budget_policy: object | None,
    adapter_registry: ProactiveDelegationAdapterRegistry,
    followup_registry: FollowUpDelegationRegistry,
    approval_evidence: object | None = None,
    occurred_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveDelegationAdapterRecord:
    validated_adapter = _validate_proactive_adapter_record(proactive_adapter_record)
    validated_selection = _validate_selection_record(selection_record)
    _validate_selection_linkage(selection_record=validated_selection, proactive_adapter_record=validated_adapter)
    validated_authorization = _validate_delegation_authorization(
        delegation_authorization_record=delegation_authorization_record,
        proactive_adapter_record=validated_adapter,
        selection_record=validated_selection,
    )

    dedupe_key = _stable_id(
        "proactive_delegation_adapter",
        validated_adapter.adapter_id,
        validated_selection.selection_id,
        validated_authorization.authorization_id,
    )
    existing = adapter_registry.get_record_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    if validated_selection.status == "cancelled_no_action":
        return adapter_registry.store_record(
            _adapter_record(
                proactive_adapter_record=validated_adapter,
                selection_record=validated_selection,
                delegation_authorization_record=validated_authorization,
                mapped_task_class="",
                delegation_packet_id=None,
                delegation_handle_id=None,
                adapter_status="rejected_cancelled_selection",
                dedupe_key=dedupe_key,
                followup_lineage=None,
                created_at=occurred_at,
            )
        )

    lineage_status = _lineage_rejection_status(proactive_adapter_record=validated_adapter)
    if lineage_status is not None:
        return adapter_registry.store_record(
            _adapter_record(
                proactive_adapter_record=validated_adapter,
                selection_record=validated_selection,
                delegation_authorization_record=validated_authorization,
                mapped_task_class="",
                delegation_packet_id=None,
                delegation_handle_id=None,
                adapter_status=lineage_status,
                dedupe_key=dedupe_key,
                followup_lineage=None,
                created_at=occurred_at,
            )
        )

    mapping_status, mapping = _mapped_task_class(
        normalized_intent_kind=validated_adapter.normalized_intent_kind,
        selection_record=validated_selection,
    )
    if mapping_status != "ok":
        return adapter_registry.store_record(
            _adapter_record(
                proactive_adapter_record=validated_adapter,
                selection_record=validated_selection,
                delegation_authorization_record=validated_authorization,
                mapped_task_class="",
                delegation_packet_id=None,
                delegation_handle_id=None,
                adapter_status=mapping_status,
                dedupe_key=dedupe_key,
                followup_lineage=None,
                created_at=occurred_at,
            )
        )

    followup_authorization = FollowUpDelegationAuthorizationEvidence(
        authorization_id=validated_authorization.authorization_id,
        authorization_kind="followup_delegation_authorization",
        selection_id=validated_selection.selection_id,
        owner_id=validated_selection.owner_id,
        robot_id=validated_selection.robot_id,
        selected_option_id=validated_selection.selected_option_id,
        selected_option_kind=validated_selection.selected_option_kind,
        cost_preflight_request_id=validated_authorization.cost_lineage_id,
        approval_evidence_id=validated_authorization.action_approval_evidence_id,
        explicit_user_authorized=True,
    )

    followup_record = create_followup_delegation_from_selection(
        selection_record=_selection_for_followup_delegation(validated_selection),
        authorization_evidence=followup_authorization,
        cost_preflight_evidence=cost_preflight_evidence,
        task_cost_request=task_cost_request,
        budget_policy=budget_policy,
        approval_evidence=approval_evidence,
        followup_registry=followup_registry,
        occurred_at=occurred_at,
    )
    adapter_status = _followup_result_status(followup_record.status, followup_record.rejection_reason)
    return adapter_registry.store_record(
        _adapter_record(
            proactive_adapter_record=validated_adapter,
            selection_record=validated_selection,
            delegation_authorization_record=validated_authorization,
            mapped_task_class=mapping,
            delegation_packet_id=followup_record.async_packet_id,
            delegation_handle_id=followup_record.async_handle_id,
            adapter_status=adapter_status,
            dedupe_key=dedupe_key,
            followup_lineage=followup_record.lineage_summary,
            created_at=occurred_at,
        )
    )


def get_proactive_delegation_adapter_record(
    *,
    adapter_registry: ProactiveDelegationAdapterRegistry,
    proactive_delegation_adapter_id: str,
) -> ProactiveDelegationAdapterRecord | None:
    return adapter_registry.get_record(proactive_delegation_adapter_id)


def list_proactive_delegation_adapter_records(
    *,
    adapter_registry: ProactiveDelegationAdapterRegistry,
) -> tuple[ProactiveDelegationAdapterRecord, ...]:
    return adapter_registry.list_records()


def _validate_proactive_adapter_record(proactive_adapter_record: object) -> ProactiveSuggestionFollowupAdapterRecord:
    if not isinstance(proactive_adapter_record, ProactiveSuggestionFollowupAdapterRecord):
        raise ValueError("rejected_invalid_lineage")
    if proactive_adapter_record.adapter_stage != PROACTIVE_SUGGESTION_ADAPTER_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if proactive_adapter_record.adapter_status not in {"adapted_to_followup_intent", "duplicate_existing"}:
        raise ValueError("rejected_invalid_lineage")
    if proactive_adapter_record.normalized_intent_kind not in ALLOWED_INTENT_KINDS:
        raise ValueError("rejected_invalid_lineage")
    if any(
        (
            proactive_adapter_record.planner_called,
            proactive_adapter_record.choice_surface_created,
            proactive_adapter_record.selection_bound,
            proactive_adapter_record.delegation_created,
            proactive_adapter_record.execution_allowed,
            proactive_adapter_record.telegram_send_allowed,
            proactive_adapter_record.memory_write_allowed,
            proactive_adapter_record.external_write_allowed,
            proactive_adapter_record.worker_dispatch_allowed,
            proactive_adapter_record.live_connector_allowed,
        )
    ):
        raise ValueError("rejected_invalid_lineage")
    return proactive_adapter_record


def _validate_selection_record(selection_record: object) -> TelegramFollowUpChoiceSelectionRecord:
    if not isinstance(selection_record, TelegramFollowUpChoiceSelectionRecord):
        raise ValueError("rejected_invalid_lineage")
    if selection_record.lineage_summary.get("selection_stage") != TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if selection_record.status == "cancelled_no_action":
        return selection_record
    if selection_record.status not in ALLOWED_SELECTION_STATUSES:
        raise ValueError("rejected_invalid_lineage")
    if selection_record.owner_id != selection_record.lineage_summary.get("owner_id"):
        raise ValueError("rejected_invalid_lineage")
    if selection_record.robot_id != selection_record.lineage_summary.get("robot_id"):
        raise ValueError("rejected_invalid_lineage")
    if selection_record.telegram_chat_id != selection_record.lineage_summary.get("telegram_chat_id"):
        raise ValueError("rejected_invalid_lineage")
    if _selected_option_metadata(selection_record) is None:
        raise ValueError("rejected_invalid_lineage")
    return selection_record


def _validate_selection_linkage(
    *,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    proactive_adapter_record: ProactiveSuggestionFollowupAdapterRecord,
) -> None:
    if selection_record.status == "cancelled_no_action":
        return
    if selection_record.followup_intent_id != proactive_adapter_record.followup_intent_review_record_id:
        raise ValueError("rejected_invalid_lineage")
    followup_lineage = _selection_followup_lineage(selection_record)
    if followup_lineage is None:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("followup_stage") != "107P":
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("source_kind") != "proactive_suggestion":
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("adapter_stage") != PROACTIVE_SUGGESTION_ADAPTER_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("acknowledgement_id") != proactive_adapter_record.explicit_owner_adapter_authorization_id:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("delivery_id") != proactive_adapter_record.delivery_record_id:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("surface_id") != proactive_adapter_record.suggestion_surface_id:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("owner_id") != proactive_adapter_record.owner_id:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("robot_id") != proactive_adapter_record.robot_id:
        raise ValueError("rejected_invalid_lineage")
    if followup_lineage.get("telegram_chat_id") != proactive_adapter_record.chat_id:
        raise ValueError("rejected_invalid_lineage")
    upstream_lineage = followup_lineage.get("upstream_lineage")
    if not isinstance(upstream_lineage, dict):
        raise ValueError("rejected_invalid_lineage")
    opportunity_lineage = upstream_lineage.get("opportunity")
    delivery_lineage = upstream_lineage.get("delivery")
    surface_lineage = upstream_lineage.get("surface")
    if not isinstance(opportunity_lineage, dict) or not isinstance(delivery_lineage, dict) or not isinstance(surface_lineage, dict):
        raise ValueError("rejected_invalid_lineage")
    if opportunity_lineage.get("candidate_source_id") != proactive_adapter_record.candidate_source_id:
        raise ValueError("rejected_invalid_lineage")
    if surface_lineage.get("opportunity_id") != proactive_adapter_record.opportunity_id:
        raise ValueError("rejected_invalid_lineage")
    if delivery_lineage.get("suggestion_surface_id") != proactive_adapter_record.suggestion_surface_id:
        raise ValueError("rejected_invalid_lineage")
    if delivery_lineage.get("opportunity_id") != proactive_adapter_record.opportunity_id:
        raise ValueError("rejected_invalid_lineage")


def _validate_delegation_authorization(
    *,
    delegation_authorization_record: object,
    proactive_adapter_record: ProactiveSuggestionFollowupAdapterRecord,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
) -> ProactiveDelegationAuthorizationRecord:
    if not isinstance(delegation_authorization_record, ProactiveDelegationAuthorizationRecord):
        raise ValueError("rejected_missing_owner_authorization")
    if delegation_authorization_record.authorization_stage != PROACTIVE_DELEGATION_ADAPTER_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.authorization_kind != AUTHORIZATION_KIND:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.granted_by_owner is not True:
        raise ValueError("rejected_missing_owner_authorization")
    if delegation_authorization_record.owner_id != proactive_adapter_record.owner_id:
        raise ValueError("rejected_missing_owner_authorization")
    if delegation_authorization_record.owner_id != selection_record.owner_id:
        raise ValueError("rejected_missing_owner_authorization")
    if delegation_authorization_record.robot_id != proactive_adapter_record.robot_id:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.robot_id != selection_record.robot_id:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.chat_id != proactive_adapter_record.chat_id:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.chat_id != selection_record.telegram_chat_id:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.proactive_adapter_id != proactive_adapter_record.adapter_id:
        raise ValueError("rejected_invalid_lineage")
    if delegation_authorization_record.followup_selection_id != selection_record.selection_id:
        raise ValueError("rejected_invalid_lineage")
    return delegation_authorization_record


def _selection_followup_lineage(selection_record: TelegramFollowUpChoiceSelectionRecord) -> dict[str, object] | None:
    choice_surface_lineage = selection_record.lineage_summary.get("upstream_lineage")
    if not isinstance(choice_surface_lineage, dict):
        return None
    draft_plan_lineage = choice_surface_lineage.get("upstream_lineage")
    if not isinstance(draft_plan_lineage, dict):
        return None
    followup_lineage = draft_plan_lineage.get("upstream_lineage")
    if not isinstance(followup_lineage, dict):
        return None
    return followup_lineage


def _lineage_rejection_status(
    *,
    proactive_adapter_record: ProactiveSuggestionFollowupAdapterRecord,
) -> str | None:
    upstream_lineage = proactive_adapter_record.lineage_summary.get("upstream_lineage")
    if not isinstance(upstream_lineage, dict):
        return "rejected_invalid_lineage"
    source_lineage = upstream_lineage.get("source")
    delivery_lineage = upstream_lineage.get("delivery")
    opportunity_lineage = upstream_lineage.get("opportunity")
    if not isinstance(source_lineage, dict) or not isinstance(delivery_lineage, dict) or not isinstance(opportunity_lineage, dict):
        return "rejected_invalid_lineage"
    if bool(opportunity_lineage.get("sensitive_data_blocked")):
        return "rejected_sensitive_data"
    if bool(source_lineage.get("live_connector_allowed")) or bool(source_lineage.get("external_read_allowed")):
        return "rejected_invalid_lineage"
    if bool(opportunity_lineage.get("live_connector_allowed")):
        return "rejected_invalid_lineage"
    if bool(opportunity_lineage.get("model_calls_required")) or bool(opportunity_lineage.get("tool_calls_required")):
        return "rejected_invalid_lineage"
    if bool(delivery_lineage.get("live_send_allowed")) or bool(delivery_lineage.get("callback_binding_allowed")):
        return "rejected_invalid_lineage"
    return None


def _mapped_task_class(
    *,
    normalized_intent_kind: str,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
) -> tuple[str, str]:
    if selection_record.status == "cancelled_no_action":
        return "rejected_cancelled_selection", ""
    if normalized_intent_kind not in INTENT_KIND_TO_ALLOWED_OPTION_KIND:
        return "rejected_unsupported_task_class", ""
    option_metadata = _selected_option_metadata(selection_record)
    if option_metadata is None:
        return "rejected_invalid_lineage", ""
    if _option_requires_blocking_capability(option_metadata):
        return "rejected_invalid_lineage", ""
    expected_option_kind = INTENT_KIND_TO_ALLOWED_OPTION_KIND[normalized_intent_kind]
    if selection_record.selected_option_kind != expected_option_kind:
        return "rejected_unsupported_task_class", ""
    mapped_task_class = FOLLOWUP_OPTION_KIND_TO_TASK_CLASS.get(expected_option_kind)
    if not mapped_task_class:
        return "rejected_unsupported_task_class", ""
    return "ok", mapped_task_class


def _selection_for_followup_delegation(
    selection_record: TelegramFollowUpChoiceSelectionRecord,
) -> TelegramFollowUpChoiceSelectionRecord:
    if selection_record.status == "selected_pending_authorization":
        return selection_record
    return replace(selection_record, status="selected_pending_authorization")


def _selected_option_metadata(
    selection_record: TelegramFollowUpChoiceSelectionRecord,
) -> dict[str, object] | None:
    choice_surface_lineage = selection_record.lineage_summary.get("upstream_lineage")
    if not isinstance(choice_surface_lineage, dict):
        return None
    metadata_by_ref = choice_surface_lineage.get("option_metadata_by_ref")
    if not isinstance(metadata_by_ref, dict):
        return None
    entry = metadata_by_ref.get(selection_record.selected_option_id)
    if not isinstance(entry, dict):
        return None
    return dict(entry)


def _option_requires_blocking_capability(option_metadata: dict[str, object]) -> bool:
    if option_metadata.get("local_only") is not True:
        return True
    if option_metadata.get("creates_authority") is not False:
        return True
    for key in (
        "implies_execution",
        "implies_memory_mutation",
        "implies_external_send",
        "implies_model_call",
        "implies_tool_call",
        "implies_delegation_creation",
        "implies_action_packet_creation",
        "implies_approval_creation",
    ):
        if bool(option_metadata.get(key)):
            return True
    for key in HIGH_RISK_OPTION_FLAGS:
        if bool(option_metadata.get(key)):
            return True
    decision_domain = option_metadata.get("decision_domain")
    if isinstance(decision_domain, str) and decision_domain in HIGH_RISK_DECISION_DOMAINS:
        return True
    return False


def _followup_result_status(status: str, rejection_reason: str | None) -> str:
    if status == "registered":
        return "delegated_registered"
    if status == "cancelled_no_action":
        return "rejected_cancelled_selection"
    if rejection_reason in {
        "blocked_missing_followup_delegation_authorization",
        "blocked_explicit_followup_authorization_required",
    }:
        return "rejected_missing_owner_authorization"
    if rejection_reason in {"blocked_unknown_option_kind"}:
        return "rejected_unsupported_task_class"
    return "rejected_invalid_lineage"


def _adapter_record(
    *,
    proactive_adapter_record: ProactiveSuggestionFollowupAdapterRecord,
    selection_record: TelegramFollowUpChoiceSelectionRecord,
    delegation_authorization_record: ProactiveDelegationAuthorizationRecord,
    mapped_task_class: str,
    delegation_packet_id: str | None,
    delegation_handle_id: str | None,
    adapter_status: str,
    dedupe_key: str,
    followup_lineage: dict[str, object] | None,
    created_at: str,
) -> ProactiveDelegationAdapterRecord:
    proactive_delegation_adapter_id = _stable_id("proactive_delegation_adapter_id", dedupe_key)
    return ProactiveDelegationAdapterRecord(
        proactive_delegation_adapter_id=proactive_delegation_adapter_id,
        owner_id=proactive_adapter_record.owner_id,
        robot_id=proactive_adapter_record.robot_id,
        chat_id=proactive_adapter_record.chat_id,
        proactive_adapter_id=proactive_adapter_record.adapter_id,
        delivery_record_id=proactive_adapter_record.delivery_record_id,
        suggestion_surface_id=proactive_adapter_record.suggestion_surface_id,
        opportunity_id=proactive_adapter_record.opportunity_id,
        candidate_source_id=proactive_adapter_record.candidate_source_id,
        source_authorization_id=proactive_adapter_record.authorization_id,
        source_stage=CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
        detection_stage=PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
        suggestion_stage=PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
        adapter_stage=PROACTIVE_SUGGESTION_ADAPTER_STAGE,
        delegation_adapter_stage=PROACTIVE_DELEGATION_ADAPTER_STAGE,
        followup_intent_review_record_id=proactive_adapter_record.followup_intent_review_record_id,
        followup_plan_id=selection_record.draft_plan_id,
        followup_choice_surface_id=selection_record.choice_surface_id,
        followup_selection_id=selection_record.selection_id,
        explicit_owner_delegation_authorization_id=delegation_authorization_record.authorization_id,
        normalized_intent_kind=proactive_adapter_record.normalized_intent_kind,
        selected_option_id=selection_record.selected_option_id,
        mapped_task_class=mapped_task_class,
        delegation_packet_id=delegation_packet_id,
        delegation_handle_id=delegation_handle_id,
        adapter_status=adapter_status,
        uses_existing_delegation_authority=True,
        execution_allowed=False,
        worker_dispatch_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        live_connector_allowed=False,
        telegram_send_allowed=False,
        memory_write_allowed=False,
        external_write_allowed=False,
        dedupe_key=dedupe_key,
        lineage_summary={
            "source_stage": CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            "detection_stage": PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            "suggestion_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            "adapter_stage": PROACTIVE_SUGGESTION_ADAPTER_STAGE,
            "delegation_adapter_stage": PROACTIVE_DELEGATION_ADAPTER_STAGE,
            "selection_stage": selection_record.lineage_summary.get("selection_stage"),
            "followup_stage": selection_record.lineage_summary.get("followup_stage"),
            "choice_surface_stage": selection_record.lineage_summary.get("choice_surface_stage"),
            "draft_planner_stage": selection_record.lineage_summary.get("draft_planner_stage"),
            "owner_id": proactive_adapter_record.owner_id,
            "robot_id": proactive_adapter_record.robot_id,
            "chat_id": proactive_adapter_record.chat_id,
            "delivery_record_id": proactive_adapter_record.delivery_record_id,
            "suggestion_surface_id": proactive_adapter_record.suggestion_surface_id,
            "opportunity_id": proactive_adapter_record.opportunity_id,
            "candidate_source_id": proactive_adapter_record.candidate_source_id,
            "source_authorization_id": proactive_adapter_record.authorization_id,
            "followup_intent_review_record_id": proactive_adapter_record.followup_intent_review_record_id,
            "followup_selection_id": selection_record.selection_id,
            "selected_option_id": selection_record.selected_option_id,
            "selected_option_kind": selection_record.selected_option_kind,
            "normalized_intent_kind": proactive_adapter_record.normalized_intent_kind,
            "mapped_task_class": mapped_task_class,
            "explicit_owner_delegation_authorization_id": delegation_authorization_record.authorization_id,
            "cost_lineage_id": delegation_authorization_record.cost_lineage_id,
            "approval_evidence_id": delegation_authorization_record.action_approval_evidence_id,
            "uses_existing_delegation_authority": True,
            "execution_allowed": False,
            "worker_dispatch_allowed": False,
            "model_call_allowed": False,
            "tool_call_allowed": False,
            "live_connector_allowed": False,
            "telegram_send_allowed": False,
            "memory_write_allowed": False,
            "external_write_allowed": False,
            "upstream_lineage": {
                "proactive_adapter": proactive_adapter_record.lineage_summary,
                "selection": selection_record.lineage_summary,
                "followup_delegation": followup_lineage,
            },
        },
        created_at=created_at,
    )


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
