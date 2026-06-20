from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE, ContextScanCandidateSourceRegistry
from app.followup_intent_review import FOLLOWUP_INTENT_REVIEW_STAGE, FOLLOWUP_SOURCE_ACTION, FollowUpIntentReviewQueue, FollowUpIntentReviewRecord
from app.proactive_opportunity_detection import PROACTIVE_OPPORTUNITY_DETECTION_STAGE, ProactiveOpportunityCandidateRecord
from app.proactive_telegram_suggestion import (
    PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
    ProactiveTelegramSuggestionDeliveryRecord,
    ProactiveTelegramSuggestionRegistry,
    ProactiveTelegramSuggestionSurfaceRecord,
)


PROACTIVE_SUGGESTION_ADAPTER_STAGE = "121P"
DEFAULT_RECORD_CREATED_AT = "2026-06-20T00:00:00Z"
AUTHORIZATION_KIND = "adapt_proactive_suggestion_to_followup_loop"

NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE = {
    "meeting_brief_missing": "prepare_meeting_brief",
    "document_review_needed": "review_document",
    "lead_followup_due": "draft_followup",
    "invoice_due_soon": "prepare_checklist",
    "customer_issue_needs_attention": "summarize_context",
    "stale_proposal_followup": "draft_followup",
    "task_deadline_risk": "summarize_context",
    "unread_context_needs_summary": "summarize_context",
    "memory_gap_detected": "review_memory_gap",
    "boundary_review_needed": "review_boundary",
}
ADAPTER_STATUSES = frozenset(
    {
        "adapted_to_followup_intent",
        "duplicate_existing",
        "rejected_invalid_lineage",
        "rejected_missing_owner_authorization",
        "rejected_sensitive_data",
        "rejected_no_opportunity",
    }
)


@dataclass(frozen=True, slots=True)
class ProactiveSuggestionAdapterAuthorizationRecord:
    authorization_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    delivery_record_id: str
    suggestion_surface_id: str
    opportunity_id: str
    authorization_kind: str
    granted_by_owner: bool
    authorization_stage: str
    created_at: str

    def __post_init__(self) -> None:
        if self.authorization_kind != AUTHORIZATION_KIND:
            raise ValueError("rejected_invalid_authorization_kind")
        if self.granted_by_owner is not True:
            raise ValueError("rejected_missing_owner_authorization")
        if self.authorization_stage != PROACTIVE_SUGGESTION_ADAPTER_STAGE:
            raise ValueError("rejected_invalid_authorization_stage")
        if not self.owner_id:
            raise ValueError("rejected_unknown_owner")
        if not self.robot_id:
            raise ValueError("rejected_unknown_robot")
        if not self.chat_id:
            raise ValueError("rejected_missing_chat_id")


@dataclass(frozen=True, slots=True)
class ProactiveSuggestionFollowupAdapterRecord:
    adapter_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    delivery_record_id: str
    suggestion_surface_id: str
    opportunity_id: str
    candidate_source_id: str
    authorization_id: str
    source_stage: str
    detection_stage: str
    suggestion_stage: str
    adapter_stage: str
    opportunity_type: str
    opportunity_category: str
    suggested_next_step_type: str
    normalized_intent_kind: str
    followup_intent_review_record_id: str
    explicit_owner_adapter_authorization_id: str
    adapter_status: str
    planner_called: bool
    choice_surface_created: bool
    selection_bound: bool
    delegation_created: bool
    execution_allowed: bool
    telegram_send_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    live_connector_allowed: bool
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
        if self.normalized_intent_kind not in set(NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE.values()):
            raise ValueError("rejected_invalid_normalized_intent_kind")
        if self.adapter_status not in ADAPTER_STATUSES:
            raise ValueError("rejected_invalid_adapter_status")
        if any(
            (
                self.planner_called,
                self.choice_surface_created,
                self.selection_bound,
                self.delegation_created,
                self.execution_allowed,
                self.telegram_send_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
                self.live_connector_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ProactiveSuggestionAdapterRegistry:
    authorizations_by_id: dict[str, ProactiveSuggestionAdapterAuthorizationRecord] = field(default_factory=dict)
    adapters_by_id: dict[str, ProactiveSuggestionFollowupAdapterRecord] = field(default_factory=dict)
    adapter_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_authorization(
        self,
        record: ProactiveSuggestionAdapterAuthorizationRecord,
    ) -> ProactiveSuggestionAdapterAuthorizationRecord:
        self.authorizations_by_id[record.authorization_id] = record
        return record

    def get_authorization(self, authorization_id: str) -> ProactiveSuggestionAdapterAuthorizationRecord | None:
        return self.authorizations_by_id.get(authorization_id)

    def store_adapter(self, record: ProactiveSuggestionFollowupAdapterRecord) -> ProactiveSuggestionFollowupAdapterRecord:
        self.adapters_by_id[record.adapter_id] = record
        self.adapter_ids_by_dedupe_key[record.dedupe_key] = record.adapter_id
        return record

    def get_adapter(self, adapter_id: str) -> ProactiveSuggestionFollowupAdapterRecord | None:
        return self.adapters_by_id.get(adapter_id)

    def get_adapter_by_dedupe_key(self, dedupe_key: str) -> ProactiveSuggestionFollowupAdapterRecord | None:
        adapter_id = self.adapter_ids_by_dedupe_key.get(dedupe_key)
        if adapter_id is None:
            return None
        return self.adapters_by_id.get(adapter_id)

    def list_adapters(self) -> tuple[ProactiveSuggestionFollowupAdapterRecord, ...]:
        return tuple(self.adapters_by_id[key] for key in sorted(self.adapters_by_id))


def authorize_proactive_suggestion_adapter_local(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    delivery_record_id: str,
    suggestion_surface_id: str,
    opportunity_id: str,
    registry: ProactiveSuggestionAdapterRegistry,
    granted_by_owner: bool = True,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveSuggestionAdapterAuthorizationRecord:
    authorization_id = _stable_id(
        "proactive_suggestion_adapter_authorization",
        owner_id,
        robot_id,
        chat_id,
        delivery_record_id,
        suggestion_surface_id,
        opportunity_id,
        AUTHORIZATION_KIND,
    )
    existing = registry.get_authorization(authorization_id)
    if existing is not None:
        return existing
    record = ProactiveSuggestionAdapterAuthorizationRecord(
        authorization_id=authorization_id,
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        delivery_record_id=delivery_record_id,
        suggestion_surface_id=suggestion_surface_id,
        opportunity_id=opportunity_id,
        authorization_kind=AUTHORIZATION_KIND,
        granted_by_owner=granted_by_owner,
        authorization_stage=PROACTIVE_SUGGESTION_ADAPTER_STAGE,
        created_at=created_at,
    )
    return registry.store_authorization(record)


def adapt_proactive_suggestion_to_followup_intent(
    *,
    delivery_record: object,
    suggestion_registry: ProactiveTelegramSuggestionRegistry,
    opportunity_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    queue: FollowUpIntentReviewQueue,
    adapter_registry: ProactiveSuggestionAdapterRegistry,
    authorization_record: object,
    owner_id: str,
    robot_id: str,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveSuggestionFollowupAdapterRecord:
    validated_delivery, validated_surface, validated_opportunity = _validate_lineage(
        delivery_record=delivery_record,
        suggestion_registry=suggestion_registry,
        opportunity_record=opportunity_record,
        source_registry=source_registry,
        owner_id=owner_id,
        robot_id=robot_id,
    )
    validated_authorization = _validate_authorization(
        authorization_record=authorization_record,
        delivery_record=validated_delivery,
        surface_record=validated_surface,
        opportunity_record=validated_opportunity,
        owner_id=owner_id,
        robot_id=robot_id,
    )

    dedupe_key = _stable_id(
        "proactive_suggestion_followup_adapter",
        validated_delivery.delivery_record_id,
        validated_surface.suggestion_surface_id,
        validated_opportunity.opportunity_id,
        validated_authorization.authorization_id,
    )
    existing = adapter_registry.get_adapter_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    followup_record = _create_followup_intent_review_record(
        delivery_record=validated_delivery,
        surface_record=validated_surface,
        opportunity_record=validated_opportunity,
        authorization_record=validated_authorization,
        queue=queue,
    )
    adapter_id = _stable_id("proactive_suggestion_followup_adapter_id", dedupe_key)
    return adapter_registry.store_adapter(
        ProactiveSuggestionFollowupAdapterRecord(
            adapter_id=adapter_id,
            owner_id=validated_delivery.owner_id,
            robot_id=validated_delivery.robot_id,
            chat_id=validated_delivery.chat_id,
            delivery_record_id=validated_delivery.delivery_record_id,
            suggestion_surface_id=validated_surface.suggestion_surface_id,
            opportunity_id=validated_opportunity.opportunity_id,
            candidate_source_id=validated_surface.candidate_source_id,
            authorization_id=validated_surface.authorization_id,
            source_stage=CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            detection_stage=PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            suggestion_stage=PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            adapter_stage=PROACTIVE_SUGGESTION_ADAPTER_STAGE,
            opportunity_type=validated_opportunity.opportunity_type,
            opportunity_category=validated_opportunity.opportunity_category,
            suggested_next_step_type=validated_opportunity.suggested_next_step_type,
            normalized_intent_kind=NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE[validated_opportunity.opportunity_type],
            followup_intent_review_record_id=followup_record.followup_intent_id,
            explicit_owner_adapter_authorization_id=validated_authorization.authorization_id,
            adapter_status="adapted_to_followup_intent",
            planner_called=False,
            choice_surface_created=False,
            selection_bound=False,
            delegation_created=False,
            execution_allowed=False,
            telegram_send_allowed=False,
            memory_write_allowed=False,
            external_write_allowed=False,
            worker_dispatch_allowed=False,
            live_connector_allowed=False,
            dedupe_key=dedupe_key,
            lineage_summary={
                "source_kind": "proactive_suggestion",
                "source_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
                "adapter_stage": PROACTIVE_SUGGESTION_ADAPTER_STAGE,
                "source_action": FOLLOWUP_SOURCE_ACTION,
                "planner_called": False,
                "choice_surface_created": False,
                "selection_bound": False,
                "delegation_created": False,
                "execution_allowed": False,
                "authorization_id": validated_authorization.authorization_id,
                "delivery_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
                "delivery_record_id": validated_delivery.delivery_record_id,
                "suggestion_surface_id": validated_surface.suggestion_surface_id,
                "opportunity_id": validated_opportunity.opportunity_id,
                "candidate_source_id": validated_surface.candidate_source_id,
                "authorization_source_id": validated_surface.authorization_id,
                "normalized_intent_kind": NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE[validated_opportunity.opportunity_type],
                "upstream_lineage": {
                    "source": validated_surface.lineage_summary,
                    "delivery": validated_delivery.lineage_summary,
                    "opportunity": validated_opportunity.lineage_summary,
                },
            },
            created_at=created_at,
        )
    )


def get_proactive_suggestion_adapter_record(
    *,
    adapter_registry: ProactiveSuggestionAdapterRegistry,
    adapter_id: str,
) -> ProactiveSuggestionFollowupAdapterRecord | None:
    return adapter_registry.get_adapter(adapter_id)


def list_proactive_suggestion_adapter_records(
    *,
    adapter_registry: ProactiveSuggestionAdapterRegistry,
) -> tuple[ProactiveSuggestionFollowupAdapterRecord, ...]:
    return adapter_registry.list_adapters()


def _validate_lineage(
    *,
    delivery_record: object,
    suggestion_registry: ProactiveTelegramSuggestionRegistry,
    opportunity_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    owner_id: str,
    robot_id: str,
) -> tuple[ProactiveTelegramSuggestionDeliveryRecord, ProactiveTelegramSuggestionSurfaceRecord, ProactiveOpportunityCandidateRecord]:
    if not isinstance(delivery_record, ProactiveTelegramSuggestionDeliveryRecord):
        raise ValueError("rejected_unknown_delivery_record")
    if delivery_record.delivery_stage != PROACTIVE_TELEGRAM_SUGGESTION_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if delivery_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if delivery_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if delivery_record.delivery_status != "delivered_local":
        raise ValueError("rejected_invalid_lineage")
    if delivery_record.delivery_mode != "injected_local_only":
        raise ValueError("rejected_invalid_lineage")
    if delivery_record.live_send_allowed:
        raise ValueError("rejected_invalid_lineage")
    if any(
        (
            delivery_record.callback_binding_allowed,
            delivery_record.followup_adapter_allowed,
            delivery_record.async_delegation_allowed,
            delivery_record.execution_allowed,
            delivery_record.memory_write_allowed,
            delivery_record.external_write_allowed,
            delivery_record.worker_dispatch_allowed,
        )
    ):
        raise ValueError("rejected_invalid_lineage")

    surface_record = suggestion_registry.get_surface(delivery_record.suggestion_surface_id)
    if surface_record is None:
        raise ValueError("rejected_invalid_lineage")
    if surface_record.suggestion_stage != PROACTIVE_TELEGRAM_SUGGESTION_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if surface_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if surface_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if surface_record.chat_id != delivery_record.chat_id:
        raise ValueError("rejected_chat_mismatch")
    if surface_record.suggestion_surface_id != delivery_record.suggestion_surface_id:
        raise ValueError("rejected_invalid_lineage")
    if surface_record.opportunity_id != delivery_record.opportunity_id:
        raise ValueError("rejected_invalid_lineage")
    if surface_record.candidate_source_id != delivery_record.candidate_source_id:
        raise ValueError("rejected_invalid_lineage")
    if surface_record.sensitive_data_blocked:
        raise ValueError("rejected_sensitive_data")
    if surface_record.telegram_transport != "injected_local_only":
        raise ValueError("rejected_invalid_lineage")
    if surface_record.live_send_allowed:
        raise ValueError("rejected_invalid_lineage")
    if any(
        (
            surface_record.callback_binding_allowed,
            surface_record.followup_adapter_allowed,
            surface_record.async_delegation_allowed,
            surface_record.execution_allowed,
            surface_record.memory_write_allowed,
            surface_record.external_write_allowed,
            surface_record.worker_dispatch_allowed,
        )
    ):
        raise ValueError("rejected_invalid_lineage")

    if not isinstance(opportunity_record, ProactiveOpportunityCandidateRecord):
        raise ValueError("rejected_invalid_lineage")
    if opportunity_record.detection_stage != PROACTIVE_OPPORTUNITY_DETECTION_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if opportunity_record.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if opportunity_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if opportunity_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if opportunity_record.opportunity_id != surface_record.opportunity_id:
        raise ValueError("rejected_invalid_lineage")
    if opportunity_record.opportunity_type == "no_opportunity":
        raise ValueError("rejected_no_opportunity")
    if opportunity_record.sensitive_data_blocked:
        raise ValueError("rejected_sensitive_data")
    if opportunity_record.opportunity_type not in NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE:
        raise ValueError("rejected_invalid_lineage")
    if any(
        (
            opportunity_record.live_connector_allowed,
            opportunity_record.execution_allowed,
            opportunity_record.memory_write_allowed,
            opportunity_record.external_write_allowed,
            opportunity_record.async_delegation_allowed,
            opportunity_record.followup_adapter_allowed,
            opportunity_record.worker_dispatch_allowed,
        )
    ):
        raise ValueError("rejected_invalid_lineage")
    lineage_summary = opportunity_record.lineage_summary
    if not isinstance(lineage_summary, dict):
        raise ValueError("rejected_invalid_lineage")
    if lineage_summary.get("model_calls_required") or lineage_summary.get("tool_calls_required"):
        raise ValueError("rejected_invalid_lineage")

    source_record = source_registry.get_candidate(opportunity_record.candidate_source_id)
    if source_record is None:
        raise ValueError("rejected_invalid_lineage")
    if source_record.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if source_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if source_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if source_record.candidate_source_id != surface_record.candidate_source_id:
        raise ValueError("rejected_invalid_lineage")
    if source_record.authorization_id != surface_record.authorization_id:
        raise ValueError("rejected_invalid_lineage")
    if source_record.live_connector_allowed or source_record.external_read_allowed:
        raise ValueError("rejected_invalid_lineage")
    return delivery_record, surface_record, opportunity_record


def _validate_authorization(
    *,
    authorization_record: object,
    delivery_record: ProactiveTelegramSuggestionDeliveryRecord,
    surface_record: ProactiveTelegramSuggestionSurfaceRecord,
    opportunity_record: ProactiveOpportunityCandidateRecord,
    owner_id: str,
    robot_id: str,
) -> ProactiveSuggestionAdapterAuthorizationRecord:
    if not isinstance(authorization_record, ProactiveSuggestionAdapterAuthorizationRecord):
        raise ValueError("rejected_missing_owner_authorization")
    if authorization_record.authorization_stage != PROACTIVE_SUGGESTION_ADAPTER_STAGE:
        raise ValueError("rejected_invalid_lineage")
    if authorization_record.authorization_kind != AUTHORIZATION_KIND:
        raise ValueError("rejected_invalid_lineage")
    if authorization_record.granted_by_owner is not True:
        raise ValueError("rejected_missing_owner_authorization")
    if authorization_record.owner_id != owner_id:
        raise ValueError("rejected_non_owner_authorization")
    if authorization_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if authorization_record.chat_id != delivery_record.chat_id:
        raise ValueError("rejected_chat_mismatch")
    if authorization_record.delivery_record_id != delivery_record.delivery_record_id:
        raise ValueError("rejected_invalid_lineage")
    if authorization_record.suggestion_surface_id != surface_record.suggestion_surface_id:
        raise ValueError("rejected_invalid_lineage")
    if authorization_record.opportunity_id != opportunity_record.opportunity_id:
        raise ValueError("rejected_invalid_lineage")
    return authorization_record


def _create_followup_intent_review_record(
    *,
    delivery_record: ProactiveTelegramSuggestionDeliveryRecord,
    surface_record: ProactiveTelegramSuggestionSurfaceRecord,
    opportunity_record: ProactiveOpportunityCandidateRecord,
    authorization_record: ProactiveSuggestionAdapterAuthorizationRecord,
    queue: FollowUpIntentReviewQueue,
) -> FollowUpIntentReviewRecord:
    followup_intent_id = _stable_id(
        "proactive_followup_intent_review_record",
        delivery_record.delivery_record_id,
        surface_record.suggestion_surface_id,
        opportunity_record.opportunity_id,
        authorization_record.authorization_id,
    )
    existing = queue.get_record(followup_intent_id)
    if existing is not None:
        return existing

    record = FollowUpIntentReviewRecord(
        followup_intent_id=followup_intent_id,
        acknowledgement_id=authorization_record.authorization_id,
        delivery_id=delivery_record.delivery_record_id,
        surface_id=surface_record.suggestion_surface_id,
        inbox_record_id=_stable_id("proactive_followup_adapter_input", delivery_record.delivery_record_id),
        owner_id=delivery_record.owner_id,
        robot_id=delivery_record.robot_id,
        telegram_chat_id=delivery_record.chat_id,
        source_action=FOLLOWUP_SOURCE_ACTION,
        status="pending_review",
        review_summary=_review_summary(opportunity_record=opportunity_record),
        lineage_summary={
            "followup_stage": FOLLOWUP_INTENT_REVIEW_STAGE,
            "source_kind": "proactive_suggestion",
            "source_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            "adapter_stage": PROACTIVE_SUGGESTION_ADAPTER_STAGE,
            "acknowledgement_stage": PROACTIVE_SUGGESTION_ADAPTER_STAGE,
            "acknowledgement_id": authorization_record.authorization_id,
            "delivery_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            "delivery_id": delivery_record.delivery_record_id,
            "surface_id": surface_record.suggestion_surface_id,
            "inbox_record_id": _stable_id("proactive_followup_adapter_input", delivery_record.delivery_record_id),
            "owner_id": delivery_record.owner_id,
            "robot_id": delivery_record.robot_id,
            "telegram_chat_id": delivery_record.chat_id,
            "source_action": FOLLOWUP_SOURCE_ACTION,
            "planner_called": False,
            "delegation_created": False,
            "execution_allowed": False,
            "normalized_intent_kind": NORMALIZED_INTENT_KIND_BY_OPPORTUNITY_TYPE[opportunity_record.opportunity_type],
            "upstream_lineage": {
                "delivery": delivery_record.lineage_summary,
                "surface": surface_record.lineage_summary,
                "opportunity": opportunity_record.lineage_summary,
            },
        },
        rejection_reason=None,
    )
    return queue.store(record)


def _review_summary(*, opportunity_record: ProactiveOpportunityCandidateRecord) -> str:
    return (
        f"Adapted proactive suggestion for {opportunity_record.opportunity_type} into follow-up review only. "
        "No planner, choice surface, selection, delegation, or execution was triggered."
    )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
