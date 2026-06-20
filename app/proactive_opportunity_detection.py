from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import (
    ALLOWED_SCAN_SCOPES,
    ALLOWED_SOURCE_STATUSES,
    ALLOWED_SOURCE_TYPES,
    BLOCKED_SOURCE_STATUSES,
    BLOCKED_SOURCE_TYPES,
    CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
    CREDENTIAL_KEYWORDS,
    SENSITIVE_KEYWORDS,
    ContextScanCandidateSourceRecord,
    ContextScanCandidateSourceRegistry,
)
from app.memory_center_projection import MemoryCenterItem


PROACTIVE_OPPORTUNITY_DETECTION_STAGE = "119P"
DEFAULT_RECORD_CREATED_AT = "2026-06-20T00:00:00Z"
DETECTION_MODE = "deterministic_local"

OPPORTUNITY_TYPES = frozenset(
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
        "no_opportunity",
    }
)
OPPORTUNITY_CATEGORIES = frozenset(
    {
        "meeting",
        "document",
        "sales",
        "finance_admin",
        "customer_success",
        "task_management",
        "memory",
        "safety_boundary",
        "general_context",
    }
)
CONFIDENCE_VALUES = frozenset({"high", "medium", "low", "not_applicable"})
NEXT_STEP_TYPES = frozenset(
    {
        "prepare_brief",
        "review_document",
        "draft_followup",
        "summarize_context",
        "review_boundary",
        "no_action",
    }
)

CATEGORY_BY_OPPORTUNITY_TYPE = {
    "meeting_brief_missing": "meeting",
    "document_review_needed": "document",
    "lead_followup_due": "sales",
    "invoice_due_soon": "finance_admin",
    "customer_issue_needs_attention": "customer_success",
    "stale_proposal_followup": "sales",
    "task_deadline_risk": "task_management",
    "unread_context_needs_summary": "general_context",
    "memory_gap_detected": "memory",
    "boundary_review_needed": "safety_boundary",
    "no_opportunity": "general_context",
}
NEXT_STEP_BY_OPPORTUNITY_TYPE = {
    "meeting_brief_missing": "prepare_brief",
    "document_review_needed": "review_document",
    "lead_followup_due": "draft_followup",
    "invoice_due_soon": "review_document",
    "customer_issue_needs_attention": "draft_followup",
    "stale_proposal_followup": "draft_followup",
    "task_deadline_risk": "summarize_context",
    "unread_context_needs_summary": "summarize_context",
    "memory_gap_detected": "review_boundary",
    "boundary_review_needed": "review_boundary",
    "no_opportunity": "no_action",
}
CONFIDENCE_BY_OPPORTUNITY_TYPE = {
    "meeting_brief_missing": "high",
    "document_review_needed": "medium",
    "lead_followup_due": "high",
    "invoice_due_soon": "high",
    "customer_issue_needs_attention": "high",
    "stale_proposal_followup": "medium",
    "task_deadline_risk": "medium",
    "unread_context_needs_summary": "medium",
    "memory_gap_detected": "medium",
    "boundary_review_needed": "high",
    "no_opportunity": "not_applicable",
}


@dataclass(frozen=True, slots=True)
class ProactiveOpportunityCandidateRecord:
    opportunity_id: str
    owner_id: str
    robot_id: str
    candidate_source_id: str
    authorization_id: str
    source_type: str
    source_category: str
    source_stage: str
    detection_stage: str
    opportunity_type: str
    opportunity_category: str
    title: str
    summary: str
    trigger_reason: str
    suggested_next_step_type: str
    confidence: str
    evidence_refs: tuple[dict[str, object], ...]
    source_created_detection: bool
    telegram_send_allowed: bool
    followup_adapter_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    live_connector_allowed: bool
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
        if self.opportunity_type not in OPPORTUNITY_TYPES:
            raise ValueError("rejected_invalid_opportunity_type")
        if self.opportunity_category not in OPPORTUNITY_CATEGORIES:
            raise ValueError("rejected_invalid_opportunity_category")
        if self.suggested_next_step_type not in NEXT_STEP_TYPES:
            raise ValueError("rejected_invalid_next_step_type")
        if self.confidence not in CONFIDENCE_VALUES:
            raise ValueError("rejected_invalid_confidence")
        if self.source_created_detection is not False:
            raise ValueError("rejected_source_created_detection_must_be_false")
        if any(
            (
                self.telegram_send_allowed,
                self.followup_adapter_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.live_connector_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class ProactiveOpportunityDetectionRunRecord:
    run_id: str
    owner_id: str
    robot_id: str
    input_candidate_source_ids: tuple[str, ...]
    opportunity_ids: tuple[str, ...]
    detection_stage: str
    detection_mode: str
    live_connector_allowed: bool
    telegram_send_allowed: bool
    memory_write_allowed: bool
    created_at: str

    def __post_init__(self) -> None:
        if self.detection_stage != PROACTIVE_OPPORTUNITY_DETECTION_STAGE:
            raise ValueError("rejected_invalid_detection_stage")
        if self.detection_mode != DETECTION_MODE:
            raise ValueError("rejected_invalid_detection_mode")
        if any((self.live_connector_allowed, self.telegram_send_allowed, self.memory_write_allowed)):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ProactiveOpportunityRegistry:
    opportunities_by_id: dict[str, ProactiveOpportunityCandidateRecord] = field(default_factory=dict)
    opportunity_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    runs_by_id: dict[str, ProactiveOpportunityDetectionRunRecord] = field(default_factory=dict)

    def store_opportunity(self, record: ProactiveOpportunityCandidateRecord) -> ProactiveOpportunityCandidateRecord:
        self.opportunities_by_id[record.opportunity_id] = record
        self.opportunity_ids_by_dedupe_key[record.dedupe_key] = record.opportunity_id
        return record

    def get_opportunity(self, opportunity_id: str) -> ProactiveOpportunityCandidateRecord | None:
        return self.opportunities_by_id.get(opportunity_id)

    def get_opportunity_by_dedupe_key(self, dedupe_key: str) -> ProactiveOpportunityCandidateRecord | None:
        opportunity_id = self.opportunity_ids_by_dedupe_key.get(dedupe_key)
        if opportunity_id is None:
            return None
        return self.opportunities_by_id.get(opportunity_id)

    def list_opportunities(self) -> tuple[ProactiveOpportunityCandidateRecord, ...]:
        return tuple(self.opportunities_by_id[key] for key in sorted(self.opportunities_by_id))

    def store_run(self, record: ProactiveOpportunityDetectionRunRecord) -> ProactiveOpportunityDetectionRunRecord:
        self.runs_by_id[record.run_id] = record
        return record


def detect_proactive_opportunity_from_context_source(
    *,
    source_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    registry: ProactiveOpportunityRegistry,
    owner_id: str,
    robot_id: str,
    memory_items: tuple[MemoryCenterItem, ...] = (),
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveOpportunityCandidateRecord:
    validated_source = _validate_source(
        source_record=source_record,
        source_registry=source_registry,
        owner_id=owner_id,
        robot_id=robot_id,
    )
    memory_lineage = _matching_memory_items(memory_items=memory_items, owner_id=owner_id, robot_id=robot_id)
    lowered_text = _lowered_source_text(validated_source)
    if _contains_blocked_keywords(lowered_text, CREDENTIAL_KEYWORDS):
        raise ValueError("rejected_credential_like_payload")

    if _contains_blocked_keywords(lowered_text, SENSITIVE_KEYWORDS):
        opportunity_type = _blocked_sensitive_opportunity_type(validated_source, lowered_text)
        return _store_candidate(
            source_record=validated_source,
            source_registry=source_registry,
            registry=registry,
            opportunity_type=opportunity_type,
            trigger_reason="sensitive_data_blocked",
            created_at=created_at,
            memory_lineage=memory_lineage,
            sensitive_data_blocked=True,
        )

    opportunity_type, trigger_reason = _classify_opportunity_type(
        source_record=validated_source,
        lowered_text=lowered_text,
        created_at=created_at,
    )
    return _store_candidate(
        source_record=validated_source,
        source_registry=source_registry,
        registry=registry,
        opportunity_type=opportunity_type,
        trigger_reason=trigger_reason,
        created_at=created_at,
        memory_lineage=memory_lineage,
        sensitive_data_blocked=False,
    )


def run_local_proactive_opportunity_detection(
    *,
    candidate_sources: tuple[ContextScanCandidateSourceRecord, ...] | list[ContextScanCandidateSourceRecord],
    source_registry: ContextScanCandidateSourceRegistry,
    registry: ProactiveOpportunityRegistry,
    owner_id: str,
    robot_id: str,
    memory_items: tuple[MemoryCenterItem, ...] = (),
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ProactiveOpportunityDetectionRunRecord:
    input_ids: list[str] = []
    opportunity_ids: list[str] = []
    for source_record in candidate_sources:
        opportunity = detect_proactive_opportunity_from_context_source(
            source_record=source_record,
            source_registry=source_registry,
            registry=registry,
            owner_id=owner_id,
            robot_id=robot_id,
            memory_items=memory_items,
            created_at=created_at,
        )
        input_ids.append(opportunity.candidate_source_id)
        opportunity_ids.append(opportunity.opportunity_id)

    run_id = _stable_id(
        "proactive_opportunity_detection_run",
        owner_id,
        robot_id,
        ",".join(sorted(input_ids)),
        ",".join(sorted(opportunity_ids)),
        created_at,
    )
    existing = registry.runs_by_id.get(run_id)
    if existing is not None:
        return existing

    return registry.store_run(
        ProactiveOpportunityDetectionRunRecord(
            run_id=run_id,
            owner_id=owner_id,
            robot_id=robot_id,
            input_candidate_source_ids=tuple(sorted(input_ids)),
            opportunity_ids=tuple(sorted(opportunity_ids)),
            detection_stage=PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            detection_mode=DETECTION_MODE,
            live_connector_allowed=False,
            telegram_send_allowed=False,
            memory_write_allowed=False,
            created_at=created_at,
        )
    )


def get_proactive_opportunity_candidate(
    *,
    registry: ProactiveOpportunityRegistry,
    opportunity_id: str,
) -> ProactiveOpportunityCandidateRecord | None:
    return registry.get_opportunity(opportunity_id)


def list_proactive_opportunity_candidates(
    *,
    registry: ProactiveOpportunityRegistry,
) -> tuple[ProactiveOpportunityCandidateRecord, ...]:
    return registry.list_opportunities()


def _validate_source(
    *,
    source_record: object,
    source_registry: ContextScanCandidateSourceRegistry,
    owner_id: str,
    robot_id: str,
) -> ContextScanCandidateSourceRecord:
    if not isinstance(source_record, ContextScanCandidateSourceRecord):
        raise ValueError("rejected_unknown_source_record")
    if not source_record.owner_id:
        raise ValueError("rejected_unknown_owner")
    if not source_record.robot_id:
        raise ValueError("rejected_unknown_robot")
    if source_record.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if source_record.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if source_record.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
        raise ValueError("rejected_invalid_source_stage")
    if source_record.source_type in BLOCKED_SOURCE_TYPES:
        raise ValueError("rejected_live_connector_source_type")
    if source_record.source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("rejected_unsupported_source_type")
    if source_record.source_status in BLOCKED_SOURCE_STATUSES:
        raise ValueError("rejected_unauthorized_source")
    if source_record.source_status not in ALLOWED_SOURCE_STATUSES:
        raise ValueError("rejected_unauthorized_source")
    if source_record.scan_scope not in ALLOWED_SCAN_SCOPES:
        raise ValueError("rejected_invalid_scan_scope")
    if source_record.live_connector_allowed:
        raise ValueError("rejected_live_connector_access_not_allowed")
    if source_record.external_read_allowed:
        raise ValueError("rejected_external_read_not_allowed")
    if any(
        (
            source_record.external_write_allowed,
            source_record.memory_write_allowed,
            source_record.telegram_send_allowed,
            source_record.worker_dispatch_allowed,
        )
    ):
        raise ValueError("rejected_source_authority_expansion_not_allowed")

    authorization = source_registry.get_authorization(source_record.authorization_id)
    if authorization is None:
        raise ValueError("rejected_unknown_authorization")
    if authorization.owner_id != owner_id:
        raise ValueError("rejected_owner_mismatch")
    if authorization.robot_id != robot_id:
        raise ValueError("rejected_robot_mismatch")
    if authorization.authorization_status == "expired":
        raise ValueError("rejected_expired_authorization")
    if authorization.authorization_status == "revoked":
        raise ValueError("rejected_revoked_authorization")
    if authorization.authorization_status != "active":
        raise ValueError("rejected_unauthorized_source")
    if not authorization.granted_by_owner:
        raise ValueError("rejected_missing_owner_consent")
    if authorization.live_connector_allowed:
        raise ValueError("rejected_live_connector_access_not_allowed")
    if authorization.external_read_allowed:
        raise ValueError("rejected_external_read_not_allowed")
    if source_record.source_type not in authorization.allowed_source_types:
        raise ValueError("rejected_unauthorized_source_type_for_authorization")
    if source_record.scan_scope not in authorization.allowed_scan_scopes:
        raise ValueError("rejected_unauthorized_scan_scope_for_authorization")
    return source_record


def _classify_opportunity_type(
    *,
    source_record: ContextScanCandidateSourceRecord,
    lowered_text: str,
    created_at: str,
) -> tuple[str, str]:
    if source_record.source_type == "mock_calendar_event" and _is_upcoming(source_record.source_timestamp, created_at) and _mentions_any(
        lowered_text,
        ("missing brief", "no brief", "briefing missing", "needs brief", "missing agenda", "empty briefing"),
    ):
        return "meeting_brief_missing", "calendar_upcoming_missing_briefing_hint"
    if source_record.source_type in {"mock_document", "mock_crm_note"} and _mentions_any(
        lowered_text,
        ("proposal sent", "no response", "stale proposal", "waiting on reply", "follow up on proposal"),
    ):
        return "stale_proposal_followup", "stale_proposal_hint"
    if source_record.source_type == "mock_document" and _mentions_any(
        lowered_text,
        ("review", "contract", "nda", "proposal", "invoice"),
    ):
        return "document_review_needed", "document_review_hint"
    if source_record.source_type == "mock_crm_note" and _mentions_any(
        lowered_text,
        ("stale lead", "open lead", "follow-up", "follow up", "lead followup"),
    ):
        return "lead_followup_due", "crm_followup_hint"
    if source_record.source_type == "mock_invoice_record" and _mentions_any(
        lowered_text,
        ("due soon", "due date", "overdue", "payment due", "approaching due"),
    ):
        return "invoice_due_soon", "invoice_due_hint"
    if source_record.source_type == "mock_message_thread" and _mentions_any(
        lowered_text,
        ("complaint", "escalation", "refund", "support", "issue"),
    ):
        return "customer_issue_needs_attention", "customer_issue_hint"
    if source_record.source_type == "mock_task_item" and _mentions_any(
        lowered_text,
        ("deadline", "at risk", "blocker", "blocked", "due today", "due tomorrow"),
    ):
        return "task_deadline_risk", "task_deadline_risk_hint"
    if source_record.source_type in {"mock_email_thread", "mock_message_thread"} and _mentions_any(
        lowered_text,
        ("unread", "long thread", "needs summary", "summary needed"),
    ):
        return "unread_context_needs_summary", "unread_context_summary_hint"
    if source_record.source_type == "mock_memory_snapshot" and _mentions_any(
        lowered_text,
        ("conflicting boundary", "unsafe boundary", "boundary conflict", "robot limit unclear"),
    ):
        return "boundary_review_needed", "memory_boundary_review_hint"
    if source_record.source_type == "mock_memory_snapshot" and _mentions_any(
        lowered_text,
        ("missing preference", "missing context", "memory gap", "missing boundary"),
    ):
        return "memory_gap_detected", "memory_gap_hint"
    return "no_opportunity", "no_deterministic_trigger"


def _store_candidate(
    *,
    source_record: ContextScanCandidateSourceRecord,
    source_registry: ContextScanCandidateSourceRegistry,
    registry: ProactiveOpportunityRegistry,
    opportunity_type: str,
    trigger_reason: str,
    created_at: str,
    memory_lineage: tuple[MemoryCenterItem, ...],
    sensitive_data_blocked: bool,
) -> ProactiveOpportunityCandidateRecord:
    dedupe_key = _stable_id(
        "proactive_opportunity_candidate",
        source_record.owner_id,
        source_record.robot_id,
        source_record.candidate_source_id,
        opportunity_type,
    )
    existing = registry.get_opportunity_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    authorization = source_registry.get_authorization(source_record.authorization_id)
    assert authorization is not None
    title = _title_for(opportunity_type, source_record.source_title)
    summary = _summary_for(opportunity_type, source_record.source_title, sensitive_data_blocked)
    evidence_refs = _evidence_refs(
        source_record=source_record,
        trigger_reason=trigger_reason,
        memory_lineage=memory_lineage,
    )
    lineage_summary = {
        "candidate_source_id": source_record.candidate_source_id,
        "authorization_id": source_record.authorization_id,
        "source_stage": CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
        "detection_stage": PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
        "source_created_detection": False,
        "detection_stage_authorized": True,
        "proactive_detection_stage": PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
        "source_hint": source_record.lineage_summary.get("source_hint"),
        "retention_policy": source_record.retention_policy,
        "memory_lineage_ids": tuple(item.item_id for item in memory_lineage),
        "memory_lineage_stage": "117P" if memory_lineage else None,
        "authorization_scope": tuple(authorization.allowed_scan_scopes),
    }
    opportunity_id = _stable_id("proactive_opportunity_id", dedupe_key)
    return registry.store_opportunity(
        ProactiveOpportunityCandidateRecord(
            opportunity_id=opportunity_id,
            owner_id=source_record.owner_id,
            robot_id=source_record.robot_id,
            candidate_source_id=source_record.candidate_source_id,
            authorization_id=source_record.authorization_id,
            source_type=source_record.source_type,
            source_category=source_record.source_category,
            source_stage=CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            detection_stage=PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
            opportunity_type=opportunity_type,
            opportunity_category=CATEGORY_BY_OPPORTUNITY_TYPE[opportunity_type],
            title=title,
            summary=summary,
            trigger_reason=trigger_reason,
            suggested_next_step_type=NEXT_STEP_BY_OPPORTUNITY_TYPE[opportunity_type],
            confidence=CONFIDENCE_BY_OPPORTUNITY_TYPE[opportunity_type],
            evidence_refs=evidence_refs,
            source_created_detection=False,
            telegram_send_allowed=False,
            followup_adapter_allowed=False,
            async_delegation_allowed=False,
            execution_allowed=False,
            memory_write_allowed=False,
            live_connector_allowed=False,
            external_write_allowed=False,
            worker_dispatch_allowed=False,
            sensitive_data_blocked=sensitive_data_blocked,
            dedupe_key=dedupe_key,
            lineage_summary=lineage_summary,
            created_at=created_at,
        )
    )


def _evidence_refs(
    *,
    source_record: ContextScanCandidateSourceRecord,
    trigger_reason: str,
    memory_lineage: tuple[MemoryCenterItem, ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = [
        {
            "candidate_source_id": source_record.candidate_source_id,
            "source_type": source_record.source_type,
            "source_category": source_record.source_category,
            "fixture_id": source_record.fixture_id,
            "source_title": source_record.source_title,
            "timestamp": source_record.source_timestamp,
            "authorization_id": source_record.authorization_id,
            "scan_scope": source_record.scan_scope,
            "source_summary": source_record.source_summary,
            "source_hint": source_record.lineage_summary.get("source_hint"),
            "trigger_reason": trigger_reason,
        }
    ]
    for item in memory_lineage:
        refs.append(
            {
                "memory_item_id": item.item_id,
                "memory_kind": item.memory_kind,
                "memory_status": item.status,
                "memory_source": item.source,
            }
        )
    return tuple(refs)


def _matching_memory_items(
    *,
    memory_items: tuple[MemoryCenterItem, ...],
    owner_id: str,
    robot_id: str,
) -> tuple[MemoryCenterItem, ...]:
    return tuple(
        item
        for item in sorted(memory_items, key=lambda value: value.item_id)
        if item.owner_id == owner_id and item.robot_id == robot_id and item.status in {"active", "conflicted", "approved", "stale"}
    )


def _blocked_sensitive_opportunity_type(source_record: ContextScanCandidateSourceRecord, lowered_text: str) -> str:
    if source_record.source_type == "mock_memory_snapshot" and _mentions_any(
        lowered_text,
        ("boundary", "unsafe", "conflict", "limit"),
    ):
        return "boundary_review_needed"
    return "no_opportunity"


def _title_for(opportunity_type: str, source_title: str) -> str:
    prefix = {
        "meeting_brief_missing": "Possible missing meeting brief",
        "document_review_needed": "Document may need review",
        "lead_followup_due": "Lead may need follow-up",
        "invoice_due_soon": "Invoice may need attention",
        "customer_issue_needs_attention": "Customer issue may need attention",
        "stale_proposal_followup": "Proposal may need follow-up",
        "task_deadline_risk": "Task deadline may be at risk",
        "unread_context_needs_summary": "Context may need summary",
        "memory_gap_detected": "Memory gap may need review",
        "boundary_review_needed": "Boundary may need review",
        "no_opportunity": "No proactive opportunity detected",
    }[opportunity_type]
    return f"{prefix}: {source_title}" if opportunity_type != "no_opportunity" else prefix


def _summary_for(opportunity_type: str, source_title: str, sensitive_data_blocked: bool) -> str:
    if sensitive_data_blocked:
        return "Sensitive source content was blocked from proactive classification and no user-facing action is authorized."
    return {
        "meeting_brief_missing": f"Authorized local context suggests the upcoming event '{source_title}' may need a briefing.",
        "document_review_needed": f"Authorized local document context suggests '{source_title}' may need review.",
        "lead_followup_due": f"Authorized local CRM context suggests '{source_title}' may need follow-up.",
        "invoice_due_soon": f"Authorized local finance context suggests '{source_title}' may need review before its due window.",
        "customer_issue_needs_attention": f"Authorized local message context suggests '{source_title}' may need customer attention.",
        "stale_proposal_followup": f"Authorized local context suggests '{source_title}' may need a proposal follow-up.",
        "task_deadline_risk": f"Authorized local task context suggests '{source_title}' may be at deadline risk.",
        "unread_context_needs_summary": f"Authorized local thread context suggests '{source_title}' may need summarization.",
        "memory_gap_detected": f"Authorized local memory context suggests '{source_title}' may indicate a memory gap.",
        "boundary_review_needed": f"Authorized local memory context suggests '{source_title}' may need boundary review.",
        "no_opportunity": "The authorized local source did not provide a deterministic proactive opportunity trigger.",
    }[opportunity_type]


def _lowered_source_text(source_record: ContextScanCandidateSourceRecord) -> str:
    parts = [
        source_record.source_title,
        source_record.source_summary or "",
        str(source_record.lineage_summary.get("source_hint") or ""),
        str(source_record.lineage_summary.get("provenance_notes") or ""),
    ]
    return " ".join(parts).lower()


def _contains_blocked_keywords(text: str, keywords: frozenset[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _mentions_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _is_upcoming(source_timestamp: str | None, created_at: str) -> bool:
    if source_timestamp is None:
        return False
    try:
        return _parse_timestamp(source_timestamp) >= _parse_timestamp(created_at)
    except ValueError:
        return False


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
