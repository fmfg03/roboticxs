from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import (
    CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
    ContextScanCandidateSourceRecord,
    ContextScanCandidateSourceRegistry,
)
from app.proactive_opportunity_detection import (
    PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
    ProactiveOpportunityCandidateRecord,
)
from app.telegram_async_result_delivery import TelegramAsyncResultTransport, TelegramOwnerBinding


PROACTIVE_TELEGRAM_SUGGESTION_STAGE = "120P"
DEFAULT_RECORD_CREATED_AT = "2026-06-20T00:00:00Z"
TELEGRAM_TRANSPORT = "injected_local_only"
DELIVERY_MODE = "injected_local_only"

ALLOWED_OPPORTUNITY_TYPES = frozenset(
    {
        "meeting_brief_missing",
        "document_review_needed",
        "lead_followup_due",
        "invoice_due_soon",
        "customer_issue_needs_attention",
        "stale_proposal_followup",
        "task_deadline_risk",
        "unread_context_needs_summary",
        "memory_gap_detected",
        "boundary_review_needed",
    }
)
DELIVERY_STATUSES = frozenset(
    {
        "delivered_local",
        "duplicate_existing",
        "rejected_invalid_lineage",
        "rejected_sensitive_data",
        "rejected_no_opportunity",
    }
)
SAFE_EVIDENCE_KEYS = frozenset(
    {
        "candidate_source_id",
        "source_type",
        "source_category",
        "fixture_id",
        "source_title",
        "timestamp",
        "authorization_id",
        "scan_scope",
        "source_summary",
        "source_hint",
        "trigger_reason",
        "memory_item_id",
        "memory_kind",
        "memory_status",
        "memory_source",
    }
)


@dataclass(frozen=True, slots=True)
class ProactiveTelegramSuggestionSurfaceRecord:
    suggestion_surface_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    opportunity_id: str
    candidate_source_id: str
    authorization_id: str
    source_stage: str
    detection_stage: str
    suggestion_stage: str
    opportunity_type: str
    opportunity_category: str
    title: str
    summary: str
    trigger_reason: str
    suggested_next_step_type: str
    confidence: str
    safe_evidence_refs: tuple[dict[str, object], ...]
    display_text: str
    telegram_transport: str
    live_send_allowed: bool
    callback_binding_allowed: bool
    followup_adapter_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    sensitive_data_blocked: bool
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
        if self.opportunity_type not in ALLOWED_OPPORTUNITY_TYPES:
            raise ValueError("rejected_unsupported_opportunity_type")
        if self.telegram_transport != TELEGRAM_TRANSPORT:
            raise ValueError("rejected_invalid_telegram_transport")
        if self.live_send_allowed is not False:
            raise ValueError("rejected_live_send_not_allowed")
        if any(
            (
                self.callback_binding_allowed,
                self.followup_adapter_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class ProactiveTelegramSuggestionDeliveryRecord:
    delivery_record_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    suggestion_surface_id: str
    opportunity_id: str
    candidate_source_id: str
    delivery_stage: str
    delivery_mode: str
    delivery_status: str
    live_send_allowed: bool
    callback_binding_allowed: bool
    followup_adapter_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.delivery_stage != PROACTIVE_TELEGRAM_SUGGESTION_STAGE:
            raise ValueError("rejected_invalid_delivery_stage")
        if self.delivery_mode != DELIVERY_MODE:
            raise ValueError("rejected_invalid_delivery_mode")
        if self.delivery_status not in DELIVERY_STATUSES:
            raise ValueError("rejected_invalid_delivery_status")
        if self.live_send_allowed is not False:
            raise ValueError("rejected_live_send_not_allowed")
        if any(
            (
                self.callback_binding_allowed,
                self.followup_adapter_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ProactiveTelegramSuggestionRegistry:
    surfaces_by_id: dict[str, ProactiveTelegramSuggestionSurfaceRecord] = field(default_factory=dict)
    surface_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    deliveries_by_id: dict[str, ProactiveTelegramSuggestionDeliveryRecord] = field(default_factory=dict)
    delivery_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_surface(self, record: ProactiveTelegramSuggestionSurfaceRecord) -> ProactiveTelegramSuggestionSurfaceRecord:
        self.surfaces_by_id[record.suggestion_surface_id] = record
        self.surface_ids_by_dedupe_key[record.dedupe_key] = record.suggestion_surface_id
        return record

    def get_surface(self, suggestion_surface_id: str) -> ProactiveTelegramSuggestionSurfaceRecord | None:
        return self.surfaces_by_id.get(suggestion_surface_id)

    def get_surface_by_dedupe_key(self, dedupe_key: str) -> ProactiveTelegramSuggestionSurfaceRecord | None:
        suggestion_surface_id = self.surface_ids_by_dedupe_key.get(dedupe_key)
        if suggestion_surface_id is None:
            return None
        return self.surfaces_by_id.get(suggestion_surface_id)

    def list_surfaces(self) -> tuple[ProactiveTelegramSuggestionSurfaceRecord, ...]:
        return tuple(self.surfaces_by_id[key] for key in sorted(self.surfaces_by_id))

    def store_delivery(self, record: ProactiveTelegramSuggestionDeliveryRecord) -> ProactiveTelegramSuggestionDeliveryRecord:
        self.deliveries_by_id[record.delivery_record_id] = record
        self.delivery_ids_by_dedupe_key[record.dedupe_key] = record.delivery_record_id
        return record

    def get_delivery(self, delivery_record_id: str) -> ProactiveTelegramSuggestionDeliveryRecord | None:
        return self.deliveries_by_id.get(delivery_record_id)

    def get_delivery_by_dedupe_key(self, dedupe_key: str) -> ProactiveTelegramSuggestionDeliveryRecord | None:
        delivery_record_id = self.delivery_ids_by_dedupe_key.get(dedupe_key)
        if delivery_record_id is None:
            return None
        return self.deliveries_by_id.get(delivery_record_id)

    def list_deliveries(self) -> tuple[ProactiveTelegramSuggestionDeliveryRecord, ...]:
        return tuple(self.deliveries_by_id[key] for key in sorted(self.deliveries_by_id))


def render_proactive_telegram_suggestion(
    *,
    opportunity_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    registry: ProactiveTelegramSuggestionRegistry,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveTelegramSuggestionSurfaceRecord:
    validated_opportunity, source_record = _validate_opportunity(
        opportunity_record=opportunity_record,
        source_registry=source_registry,
        owner_id=owner_id,
        robot_id=robot_id,
    )
    if not chat_id:
        raise ValueError("rejected_missing_chat_id")

    dedupe_key = _stable_id(
        "proactive_telegram_suggestion_surface",
        validated_opportunity.owner_id,
        validated_opportunity.robot_id,
        chat_id,
        validated_opportunity.opportunity_id,
    )
    existing = registry.get_surface_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    safe_evidence_refs = _safe_evidence_refs(validated_opportunity.safe_evidence_refs if hasattr(validated_opportunity, "safe_evidence_refs") else validated_opportunity.evidence_refs)
    suggestion_surface_id = _stable_id("proactive_telegram_suggestion_surface_id", dedupe_key)
    return registry.store_surface(
        ProactiveTelegramSuggestionSurfaceRecord(
            suggestion_surface_id=suggestion_surface_id,
            owner_id=validated_opportunity.owner_id,
            robot_id=validated_opportunity.robot_id,
            chat_id=chat_id,
            opportunity_id=validated_opportunity.opportunity_id,
            candidate_source_id=validated_opportunity.candidate_source_id,
            authorization_id=validated_opportunity.authorization_id,
            source_stage=CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            detection_stage=PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            suggestion_stage=PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            opportunity_type=validated_opportunity.opportunity_type,
            opportunity_category=validated_opportunity.opportunity_category,
            title=validated_opportunity.title,
            summary=validated_opportunity.summary,
            trigger_reason=validated_opportunity.trigger_reason,
            suggested_next_step_type=validated_opportunity.suggested_next_step_type,
            confidence=validated_opportunity.confidence,
            safe_evidence_refs=safe_evidence_refs,
            display_text=_display_text(validated_opportunity),
            telegram_transport=TELEGRAM_TRANSPORT,
            live_send_allowed=False,
            callback_binding_allowed=False,
            followup_adapter_allowed=False,
            async_delegation_allowed=False,
            execution_allowed=False,
            memory_write_allowed=False,
            external_write_allowed=False,
            worker_dispatch_allowed=False,
            sensitive_data_blocked=False,
            dedupe_key=dedupe_key,
            lineage_summary={
                "source_stage": CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
                "detection_stage": PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
                "suggestion_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
                "candidate_source_id": validated_opportunity.candidate_source_id,
                "authorization_id": validated_opportunity.authorization_id,
                "opportunity_id": validated_opportunity.opportunity_id,
                "source_created_delivery": False,
                "opportunity_created_delivery": False,
                "source_stage_sent_telegram": False,
                "suggestion_stage_authorized": True,
                "suggestion_delivery_stage_authorized": True,
                "telegram_suggestion_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
                "delivery_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
                "source_title": source_record.source_title,
                "source_summary": source_record.source_summary,
                "safe_source_ref": {
                    "source_type": source_record.source_type,
                    "source_category": source_record.source_category,
                    "fixture_id": source_record.fixture_id,
                    "timestamp": source_record.source_timestamp,
                },
                "upstream_lineage": validated_opportunity.lineage_summary,
            },
            created_at=created_at,
        )
    )


def deliver_proactive_telegram_suggestion_local(
    *,
    surface_record: object,
    owner_binding: TelegramOwnerBinding | None,
    transport: TelegramAsyncResultTransport,
    registry: ProactiveTelegramSuggestionRegistry,
    telegram_chat_id: str | None = None,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveTelegramSuggestionDeliveryRecord:
    if not isinstance(surface_record, ProactiveTelegramSuggestionSurfaceRecord):
        raise TypeError("120P delivery requires a ProactiveTelegramSuggestionSurfaceRecord.")

    target_chat_id = surface_record.chat_id if telegram_chat_id is None else telegram_chat_id
    dedupe_key = _stable_id(
        "proactive_telegram_suggestion_delivery",
        surface_record.suggestion_surface_id,
        surface_record.opportunity_id,
        target_chat_id,
    )
    existing = registry.get_delivery_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    rejection_status = _delivery_rejection_status(
        surface_record=surface_record,
        owner_binding=owner_binding,
        telegram_chat_id=telegram_chat_id,
    )
    if rejection_status is not None:
        return registry.store_delivery(
            _delivery_record(
                surface_record=surface_record,
                chat_id=target_chat_id,
                delivery_status=rejection_status,
                dedupe_key=dedupe_key,
                created_at=created_at,
            )
        )

    assert owner_binding is not None
    transport.deliver(target_chat_id, surface_record.display_text, ())
    return registry.store_delivery(
        _delivery_record(
            surface_record=surface_record,
            chat_id=target_chat_id,
            delivery_status="delivered_local",
            dedupe_key=dedupe_key,
            created_at=created_at,
        )
    )


def get_proactive_telegram_suggestion_surface(
    *,
    registry: ProactiveTelegramSuggestionRegistry,
    suggestion_surface_id: str,
) -> ProactiveTelegramSuggestionSurfaceRecord | None:
    return registry.get_surface(suggestion_surface_id)


def get_proactive_telegram_suggestion_delivery(
    *,
    registry: ProactiveTelegramSuggestionRegistry,
    delivery_record_id: str,
) -> ProactiveTelegramSuggestionDeliveryRecord | None:
    return registry.get_delivery(delivery_record_id)


def list_proactive_telegram_suggestions(
    *,
    registry: ProactiveTelegramSuggestionRegistry,
) -> tuple[ProactiveTelegramSuggestionSurfaceRecord, ...]:
    return registry.list_surfaces()


def list_proactive_telegram_deliveries(
    *,
    registry: ProactiveTelegramSuggestionRegistry,
) -> tuple[ProactiveTelegramSuggestionDeliveryRecord, ...]:
    return registry.list_deliveries()


def _validate_opportunity(
    *,
    opportunity_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    owner_id: str,
    robot_id: str,
) -> tuple[ProactiveOpportunityCandidateRecord, ContextScanCandidateSourceRecord]:
    if not isinstance(opportunity_record, ProactiveOpportunityCandidateRecord):
        raise ValueError("rejected_unknown_119p_opportunity_record")
    if not opportunity_record.owner_id:
        raise ValueError("rejected_unknown_owner")
    if not opportunity_record.robot_id:
        raise ValueError("rejected_unknown_robot")
    if opportunity_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if opportunity_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if opportunity_record.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
        raise ValueError("rejected_missing_118p_source_lineage")
    if opportunity_record.detection_stage != PROACTIVE_OPPORTUNITY_DETECTION_STAGE:
        raise ValueError("rejected_invalid_detection_stage")
    if opportunity_record.opportunity_type == "no_opportunity":
        raise ValueError("rejected_no_opportunity")
    if opportunity_record.opportunity_type not in ALLOWED_OPPORTUNITY_TYPES:
        raise ValueError("rejected_unsupported_opportunity_type")
    if opportunity_record.sensitive_data_blocked:
        raise ValueError("rejected_sensitive_data")
    if opportunity_record.live_connector_allowed:
        raise ValueError("rejected_live_connector_read_required")
    if opportunity_record.execution_allowed:
        raise ValueError("rejected_execution_implied")
    if opportunity_record.memory_write_allowed:
        raise ValueError("rejected_memory_mutation_implied")
    if opportunity_record.followup_adapter_allowed:
        raise ValueError("rejected_followup_adapter_implied")
    if opportunity_record.async_delegation_allowed:
        raise ValueError("rejected_async_delegation_implied")
    if opportunity_record.worker_dispatch_allowed:
        raise ValueError("rejected_worker_dispatch_implied")
    if opportunity_record.external_write_allowed:
        raise ValueError("rejected_external_write_implied")
    if opportunity_record.lineage_summary.get("model_calls_required") is True:
        raise ValueError("rejected_model_call_required")
    if opportunity_record.lineage_summary.get("tool_calls_required") is True:
        raise ValueError("rejected_tool_call_required")

    source_record = source_registry.get_candidate(opportunity_record.candidate_source_id)
    if source_record is None:
        raise ValueError("rejected_missing_118p_source_lineage")
    if source_record.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
        raise ValueError("rejected_missing_118p_source_lineage")
    if source_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if source_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if source_record.authorization_id != opportunity_record.authorization_id:
        raise ValueError("rejected_missing_118p_source_lineage")
    if source_record.candidate_source_id != opportunity_record.candidate_source_id:
        raise ValueError("rejected_missing_118p_source_lineage")
    if source_record.live_connector_allowed:
        raise ValueError("rejected_live_connector_read_required")
    if source_record.external_read_allowed:
        raise ValueError("rejected_live_connector_read_required")

    authorization = source_registry.get_authorization(opportunity_record.authorization_id)
    if authorization is None:
        raise ValueError("rejected_missing_118p_source_lineage")
    if authorization.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if authorization.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if authorization.authorization_status != "active":
        raise ValueError("rejected_missing_118p_source_lineage")
    if authorization.live_connector_allowed or authorization.external_read_allowed:
        raise ValueError("rejected_live_connector_read_required")
    return opportunity_record, source_record


def _safe_evidence_refs(evidence_refs: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    safe_refs: list[dict[str, object]] = []
    for ref in evidence_refs:
        safe_refs.append({key: value for key, value in ref.items() if key in SAFE_EVIDENCE_KEYS})
    return tuple(safe_refs)


def _display_text(opportunity_record: ProactiveOpportunityCandidateRecord) -> str:
    opening = {
        "meeting_brief_missing": "I noticed tomorrow's meeting may be missing a brief.",
        "document_review_needed": "I found a document in authorized context that may need review.",
        "lead_followup_due": "I noticed a lead may be due for follow-up.",
        "invoice_due_soon": "This invoice appears close to its due date in the local fixture.",
        "customer_issue_needs_attention": "I noticed a customer issue that may need attention.",
        "stale_proposal_followup": "I noticed a proposal may need follow-up.",
        "task_deadline_risk": "I noticed a task may be at deadline risk.",
        "unread_context_needs_summary": "I noticed some authorized context may need a summary.",
        "memory_gap_detected": "I noticed a possible memory gap in authorized local context.",
        "boundary_review_needed": "I noticed a boundary that may need review.",
    }[opportunity_record.opportunity_type]
    why = {
        "meeting_brief_missing": "It may matter because the event looks upcoming and lacks briefing context.",
        "document_review_needed": "It may matter because the source includes a clear review signal.",
        "lead_followup_due": "It may matter because the lead appears open or stale.",
        "invoice_due_soon": "It may matter because the due window looks close.",
        "customer_issue_needs_attention": "It may matter because the thread suggests a complaint or escalation.",
        "stale_proposal_followup": "It may matter because the proposal appears stale or unanswered.",
        "task_deadline_risk": "It may matter because the task shows deadline or blocker risk.",
        "unread_context_needs_summary": "It may matter because the thread appears unread or long.",
        "memory_gap_detected": "It may matter because missing context could reduce future usefulness.",
        "boundary_review_needed": "It may matter because the boundary context looks conflicting or unclear.",
    }[opportunity_record.opportunity_type]
    next_step = f"I can help with `{opportunity_record.suggested_next_step_type}` if you approve a next step later."
    return f"{opening} {why} {next_step} No action has been taken."


def _delivery_rejection_status(
    *,
    surface_record: ProactiveTelegramSuggestionSurfaceRecord,
    owner_binding: TelegramOwnerBinding | None,
    telegram_chat_id: str | None,
) -> str | None:
    if surface_record.sensitive_data_blocked:
        return "rejected_sensitive_data"
    if surface_record.opportunity_type not in ALLOWED_OPPORTUNITY_TYPES:
        return "rejected_no_opportunity"
    if owner_binding is None:
        return "rejected_invalid_lineage"
    if owner_binding.channel != "telegram":
        return "rejected_invalid_lineage"
    if owner_binding.enabled is not True:
        return "rejected_invalid_lineage"
    if owner_binding.owner_id != surface_record.owner_id:
        return "rejected_invalid_lineage"
    if owner_binding.robot_id != surface_record.robot_id:
        return "rejected_invalid_lineage"
    if not owner_binding.telegram_chat_id:
        return "rejected_invalid_lineage"
    if telegram_chat_id is not None and telegram_chat_id != owner_binding.telegram_chat_id:
        return "rejected_invalid_lineage"
    return None


def _delivery_record(
    *,
    surface_record: ProactiveTelegramSuggestionSurfaceRecord,
    chat_id: str,
    delivery_status: str,
    dedupe_key: str,
    created_at: str,
) -> ProactiveTelegramSuggestionDeliveryRecord:
    return ProactiveTelegramSuggestionDeliveryRecord(
        delivery_record_id=_stable_id("proactive_telegram_suggestion_delivery_id", dedupe_key),
        owner_id=surface_record.owner_id,
        robot_id=surface_record.robot_id,
        chat_id=chat_id,
        suggestion_surface_id=surface_record.suggestion_surface_id,
        opportunity_id=surface_record.opportunity_id,
        candidate_source_id=surface_record.candidate_source_id,
        delivery_stage=PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
        delivery_mode=DELIVERY_MODE,
        delivery_status=delivery_status,
        live_send_allowed=False,
        callback_binding_allowed=False,
        followup_adapter_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        external_write_allowed=False,
        worker_dispatch_allowed=False,
        dedupe_key=dedupe_key,
        lineage_summary={
            "delivery_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            "suggestion_surface_id": surface_record.suggestion_surface_id,
            "opportunity_id": surface_record.opportunity_id,
            "candidate_source_id": surface_record.candidate_source_id,
            "source_stage": CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            "detection_stage": PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            "source_stage_sent_telegram": False,
            "suggestion_delivery_stage_authorized": True,
            "telegram_suggestion_stage": PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
            "upstream_lineage": surface_record.lineage_summary,
        },
        created_at=created_at,
    )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
