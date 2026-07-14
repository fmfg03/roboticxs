from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import ContextScanCandidateSourceRecord
from app.daily_brief_what_did_i_miss import DailyBriefItemRecord, DailyBriefSnapshotRecord
from app.followup_delegation_authority import FollowUpDelegationRequestRecord
from app.followup_draft_planner import FollowUpDraftPlanRecord
from app.followup_intent_review import FollowUpIntentReviewRecord
from app.followup_memory_proposal import FollowUpMemoryProposalCandidateRecord
from app.followup_result_acknowledgement import FollowUpResultAcknowledgementRecord
from app.memory_center_writeback import MemoryCenterWritebackRecord
from app.proactive_delegation_adapter import ProactiveDelegationAdapterRecord
from app.proactive_execution_skeleton import ProactiveExecutionAttemptRecord
from app.proactive_opportunity_detection import ProactiveOpportunityCandidateRecord
from app.proactive_suggestion_adapter import ProactiveSuggestionFollowupAdapterRecord
from app.proactive_telegram_suggestion import ProactiveTelegramSuggestionDeliveryRecord
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionRecord
from app.telegram_followup_choice_surface import TelegramFollowUpChoiceSurfaceRecord
from app.telegram_memory_proposal_approval import (
    TelegramMemoryProposalApprovalDecisionRecord,
    TelegramMemoryProposalApprovalSurfaceRecord,
)
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord
from app.async_delegation_inbox import AsyncDelegationInboxRecord


SKILL_PACK_STAGE = "125P"
SKILL_PACK_MODE = "deterministic_local_read_only"
SOURCE_STAGE_MIN = "103P"
SOURCE_STAGE_MAX = "124P"
NO_UPDATES_TEXT = "No classified skill pack activity was found."
SKILL_PACK_IDS = (
    "robot_core",
    "basic_package",
    "pro_package",
    "documents_pack",
    "sales_pack",
    "marketing_pack",
    "finance_admin_pack",
    "hr_pack",
    "memory_center_core",
    "safety_boundary_core",
    "future_specialty_pack",
    "unknown_unclassified",
)
PACKAGE_DISPLAY_STATES = {
    "robot_core": "included_core",
    "memory_center_core": "included_core",
    "safety_boundary_core": "included_core",
    "basic_package": "available_in_basic",
    "pro_package": "available_in_pro",
    "documents_pack": "available_as_specialty_pack",
    "sales_pack": "available_as_specialty_pack",
    "marketing_pack": "available_as_specialty_pack",
    "finance_admin_pack": "available_as_specialty_pack",
    "hr_pack": "available_as_specialty_pack",
    "future_specialty_pack": "future_pack_candidate",
    "unknown_unclassified": "unclassified",
}
CATALOG_TIER_BY_ID = {
    "robot_core": "core",
    "memory_center_core": "core",
    "safety_boundary_core": "core",
    "basic_package": "basic",
    "pro_package": "pro",
    "documents_pack": "specialty",
    "sales_pack": "specialty",
    "marketing_pack": "specialty",
    "finance_admin_pack": "specialty",
    "hr_pack": "specialty",
    "future_specialty_pack": "future",
    "unknown_unclassified": "future",
}
CONFIDENCE_VALUES = {"high", "medium", "low", "not_applicable"}
SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "api_key",
    "api key",
    "secret",
    "credential",
    "token",
    "bearer",
    "private key",
    "private_key",
    "medical record",
    "diagnosis",
    "passport",
    "driver license",
)
SOURCE_STAGE_ORDER = {f"{number}P": number for number in range(103, 126)}
SAFE_LINEAGE_KEYS = {
    "source_stage",
    "delivery_stage",
    "acknowledgement_stage",
    "proposal_stage",
    "decision_stage",
    "writeback_stage",
    "detection_stage",
    "suggestion_stage",
    "adapter_stage",
    "delegation_adapter_stage",
    "execution_stage",
    "followup_stage",
    "source_record_id",
    "delivery_id",
    "surface_id",
    "inbox_record_id",
    "acknowledgement_id",
    "proposal_id",
    "decision_id",
    "writeback_id",
    "candidate_source_id",
    "opportunity_id",
    "suggestion_surface_id",
    "authorization_id",
    "followup_intent_id",
    "draft_plan_id",
    "choice_surface_id",
    "selection_id",
    "delegation_id",
    "attempt_id",
    "packet_id",
    "route_id",
    "handle_id",
    "source_type",
    "source_category",
    "opportunity_type",
    "opportunity_category",
    "selected_option_kind",
    "followup_task_class",
    "memory_item_id",
    "memory_kind",
    "review_type",
    "count",
}


@dataclass(frozen=True, slots=True)
class SkillPackCatalogEntryRecord:
    skill_pack_id: str
    display_name: str
    category: str
    package_tier: str
    allowed_source_types: tuple[str, ...]
    allowed_opportunity_types: tuple[str, ...]
    allowed_task_classes: tuple[str, ...]
    allowed_memory_types: tuple[str, ...]
    safe_display_description: str
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    created_at: str

    def __post_init__(self) -> None:
        if self.skill_pack_id not in SKILL_PACK_IDS:
            raise ValueError("rejected_invalid_skill_pack_id")
        if self.package_tier not in {"core", "basic", "pro", "specialty", "future"}:
            raise ValueError("rejected_invalid_package_tier")
        if self.billing_allowed or self.entitlement_enforcement_allowed:
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class SkillPackClassificationRecord:
    classification_id: str
    owner_id: str
    robot_id: str
    source_record_id: str
    source_record_type: str
    source_stage: str
    skill_pack_id: str
    skill_pack_category: str
    package_display_state: str
    classification_reason: str
    confidence: str
    source_title: str
    source_summary: str
    safe_evidence_refs: tuple[dict[str, object], ...]
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    package_activation_allowed: bool
    upgrade_prompt_allowed: bool
    telegram_delivery_allowed: bool
    callback_binding_allowed: bool
    followup_intent_creation_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    live_connector_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.skill_pack_id not in SKILL_PACK_IDS:
            raise ValueError("rejected_invalid_skill_pack_id")
        if self.package_display_state not in {
            "included_core",
            "available_in_basic",
            "available_in_pro",
            "available_as_specialty_pack",
            "future_pack_candidate",
            "unclassified",
        }:
            raise ValueError("rejected_invalid_package_display_state")
        if self.confidence not in CONFIDENCE_VALUES:
            raise ValueError("rejected_invalid_confidence")
        if any(
            (
                self.billing_allowed,
                self.entitlement_enforcement_allowed,
                self.package_activation_allowed,
                self.upgrade_prompt_allowed,
                self.telegram_delivery_allowed,
                self.callback_binding_allowed,
                self.followup_intent_creation_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.live_connector_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class SkillPackActivationSurfaceRecord:
    surface_id: str
    owner_id: str
    robot_id: str
    source_stage_min: str
    source_stage_max: str
    surface_stage: str
    surface_mode: str
    classification_ids: tuple[str, ...]
    total_classified_count: int
    robot_core_count: int
    basic_package_count: int
    pro_package_count: int
    documents_pack_count: int
    sales_pack_count: int
    marketing_pack_count: int
    finance_admin_pack_count: int
    hr_pack_count: int
    memory_center_core_count: int
    safety_boundary_core_count: int
    unknown_unclassified_count: int
    local_render_text: str
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    package_activation_allowed: bool
    upgrade_prompt_allowed: bool
    telegram_delivery_allowed: bool
    callback_binding_allowed: bool
    followup_intent_creation_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    live_connector_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    sensitive_data_excluded: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.source_stage_min != SOURCE_STAGE_MIN:
            raise ValueError("rejected_invalid_source_stage_min")
        if self.source_stage_max != SOURCE_STAGE_MAX:
            raise ValueError("rejected_invalid_source_stage_max")
        if self.surface_stage != SKILL_PACK_STAGE:
            raise ValueError("rejected_invalid_surface_stage")
        if self.surface_mode != SKILL_PACK_MODE:
            raise ValueError("rejected_invalid_surface_mode")
        if any(
            (
                self.billing_allowed,
                self.entitlement_enforcement_allowed,
                self.package_activation_allowed,
                self.upgrade_prompt_allowed,
                self.telegram_delivery_allowed,
                self.callback_binding_allowed,
                self.followup_intent_creation_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.live_connector_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class SkillPackSourceBundle:
    daily_brief_snapshots_124p: tuple[DailyBriefSnapshotRecord, ...] = ()
    daily_brief_items_124p: tuple[DailyBriefItemRecord, ...] = ()
    proactive_executions_123p: tuple[ProactiveExecutionAttemptRecord, ...] = ()
    proactive_delegations_122p: tuple[ProactiveDelegationAdapterRecord, ...] = ()
    proactive_adapters_121p: tuple[ProactiveSuggestionFollowupAdapterRecord, ...] = ()
    proactive_deliveries_120p: tuple[ProactiveTelegramSuggestionDeliveryRecord, ...] = ()
    proactive_opportunities_119p: tuple[ProactiveOpportunityCandidateRecord, ...] = ()
    context_sources_118p: tuple[ContextScanCandidateSourceRecord, ...] = ()
    memory_writebacks_117p: tuple[MemoryCenterWritebackRecord, ...] = ()
    memory_approval_surfaces_116p: tuple[TelegramMemoryProposalApprovalSurfaceRecord, ...] = ()
    memory_approval_decisions_116p: tuple[TelegramMemoryProposalApprovalDecisionRecord, ...] = ()
    memory_proposals_115p: tuple[FollowUpMemoryProposalCandidateRecord, ...] = ()
    followup_acknowledgements_114p: tuple[FollowUpResultAcknowledgementRecord, ...] = ()
    followup_delegations_111p: tuple[FollowUpDelegationRequestRecord, ...] = ()
    followup_selections_110p: tuple[TelegramFollowUpChoiceSelectionRecord, ...] = ()
    followup_choice_surfaces_109p: tuple[TelegramFollowUpChoiceSurfaceRecord, ...] = ()
    followup_plans_108p: tuple[FollowUpDraftPlanRecord, ...] = ()
    followup_intents_107p: tuple[FollowUpIntentReviewRecord, ...] = ()
    result_acknowledgements_106p: tuple[TelegramResultAcknowledgementRecord, ...] = ()
    result_deliveries_105p: tuple[TelegramAsyncResultDeliveryRecord, ...] = ()
    inbox_records_103p: tuple[AsyncDelegationInboxRecord, ...] = ()


@dataclass(slots=True)
class SkillPackActivationRegistry:
    catalog_by_id: dict[str, SkillPackCatalogEntryRecord] = field(default_factory=dict)
    classifications_by_id: dict[str, SkillPackClassificationRecord] = field(default_factory=dict)
    classification_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    surfaces_by_id: dict[str, SkillPackActivationSurfaceRecord] = field(default_factory=dict)
    surface_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    classification_ids_by_surface_id: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def store_catalog_entry(self, entry: SkillPackCatalogEntryRecord) -> SkillPackCatalogEntryRecord:
        self.catalog_by_id[entry.skill_pack_id] = entry
        return entry

    def store_classification(self, record: SkillPackClassificationRecord) -> SkillPackClassificationRecord:
        self.classifications_by_id[record.classification_id] = record
        self.classification_ids_by_dedupe_key[record.dedupe_key] = record.classification_id
        return record

    def get_classification(self, classification_id: str) -> SkillPackClassificationRecord | None:
        return self.classifications_by_id.get(classification_id)

    def get_classification_by_dedupe_key(self, dedupe_key: str) -> SkillPackClassificationRecord | None:
        classification_id = self.classification_ids_by_dedupe_key.get(dedupe_key)
        if classification_id is None:
            return None
        return self.classifications_by_id.get(classification_id)

    def list_classifications(self) -> tuple[SkillPackClassificationRecord, ...]:
        return tuple(self.classifications_by_id[key] for key in sorted(self.classifications_by_id))

    def store_surface(
        self,
        *,
        surface: SkillPackActivationSurfaceRecord,
        classifications: tuple[SkillPackClassificationRecord, ...],
    ) -> SkillPackActivationSurfaceRecord:
        self.surfaces_by_id[surface.surface_id] = surface
        self.surface_ids_by_dedupe_key[surface.dedupe_key] = surface.surface_id
        self.classification_ids_by_surface_id[surface.surface_id] = tuple(
            classification.classification_id for classification in classifications
        )
        return surface

    def get_surface(self, surface_id: str) -> SkillPackActivationSurfaceRecord | None:
        return self.surfaces_by_id.get(surface_id)

    def get_surface_by_dedupe_key(self, dedupe_key: str) -> SkillPackActivationSurfaceRecord | None:
        surface_id = self.surface_ids_by_dedupe_key.get(dedupe_key)
        if surface_id is None:
            return None
        return self.surfaces_by_id.get(surface_id)

    def list_surfaces(self) -> tuple[SkillPackActivationSurfaceRecord, ...]:
        return tuple(self.surfaces_by_id[key] for key in sorted(self.surfaces_by_id))


def build_default_skill_pack_catalog(
    *,
    created_at: str = "2026-06-20T00:00:00Z",
) -> tuple[SkillPackCatalogEntryRecord, ...]:
    entries = (
        ("robot_core", "Robot Core", "robot_core", ("mock_calendar_event", "mock_memory_snapshot"), (), (), (), "Core robot status and context surfaces."),
        ("basic_package", "Basic Package", "basic_package", ("mock_calendar_event", "mock_task_item", "mock_message_thread"), ("meeting_brief_missing",), (), (), "Daily summaries and simple operator help."),
        ("pro_package", "Pro Package", "pro_package", ("mock_task_item", "mock_message_thread"), ("customer_issue_needs_attention", "task_deadline_risk", "unread_context_needs_summary"), ("FOLLOWUP_DEEPER_SUMMARY",), (), "Deeper recurring operator workflows."),
        ("documents_pack", "Documents Pack", "documents_pack", ("mock_document",), ("document_review_needed",), ("FOLLOWUP_HUMAN_REVIEW_CHECKLIST", "FOLLOWUP_COMPARE_PRIOR_VERSION"), (), "Document review and checklist workflows."),
        ("sales_pack", "Sales Pack", "sales_pack", ("mock_crm_note", "mock_document"), ("lead_followup_due", "stale_proposal_followup"), ("FOLLOWUP_EXTRACT_QUESTIONS",), (), "Lead follow-up and proposal workflow support."),
        ("marketing_pack", "Marketing Pack", "marketing_pack", ("mock_document", "mock_message_thread"), (), (), (), "Campaign and content-oriented work."),
        ("finance_admin_pack", "Finance/Admin Pack", "finance_admin_pack", ("mock_invoice_record",), ("invoice_due_soon",), (), (), "Invoice and admin reminders."),
        ("hr_pack", "HR Pack", "hr_pack", ("mock_document", "mock_message_thread"), (), (), (), "Candidate, interview, and onboarding workflows."),
        ("memory_center_core", "Memory Center Core", "memory_center_core", ("mock_memory_snapshot",), (), (), ("TASK_MEMORY", "BUSINESS_CONTEXT_MEMORY", "WORK_PREFERENCE", "USER_PROFILE_MEMORY", "BOUNDARY_MEMORY"), "Memory proposals and writebacks."),
        ("safety_boundary_core", "Safety Boundary Core", "safety_boundary_core", (), ("boundary_review_needed", "memory_gap_detected"), (), ("BOUNDARY_MEMORY",), "Safety and boundary review surfaces."),
        ("future_specialty_pack", "Future Specialty Pack", "future_specialty_pack", (), (), (), (), "Reserved future specialty workflows."),
        ("unknown_unclassified", "Unknown / Unclassified", "unknown_unclassified", (), (), (), (), "Fallback for records that do not map cleanly."),
    )
    return tuple(
        SkillPackCatalogEntryRecord(
            skill_pack_id=skill_pack_id,
            display_name=display_name,
            category=category,
            package_tier=CATALOG_TIER_BY_ID[skill_pack_id],
            allowed_source_types=source_types,
            allowed_opportunity_types=opportunity_types,
            allowed_task_classes=task_classes,
            allowed_memory_types=memory_types,
            safe_display_description=description,
            billing_allowed=False,
            entitlement_enforcement_allowed=False,
            created_at=created_at,
        )
        for skill_pack_id, display_name, category, source_types, opportunity_types, task_classes, memory_types, description in entries
    )


def classify_record_for_skill_pack(
    *,
    record: object,
    owner_id: str,
    robot_id: str,
    registry: SkillPackActivationRegistry,
    catalog: tuple[SkillPackCatalogEntryRecord, ...] | None = None,
) -> SkillPackClassificationRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if getattr(record, "owner_id", owner_id) != owner_id:
        raise ValueError("rejected_cross_owner_record")
    if getattr(record, "robot_id", robot_id) != robot_id:
        raise ValueError("rejected_cross_robot_record")

    catalog_entries = build_default_skill_pack_catalog() if catalog is None else catalog
    for entry in catalog_entries:
        registry.store_catalog_entry(entry)

    source_stage = _source_stage(record)
    source_record_id = _source_record_id(record)
    source_title = _source_title(record)
    source_summary = _source_summary(record)
    _reject_sensitive_text(source_title)
    _reject_sensitive_text(source_summary)

    dedupe_key = _stable_id(
        "skill_pack_classification",
        owner_id,
        robot_id,
        source_stage,
        source_record_id,
        type(record).__name__,
    )
    existing = registry.get_classification_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    skill_pack_id, classification_reason, confidence = _classify_skill_pack(record)
    classification = SkillPackClassificationRecord(
        classification_id=_stable_id("skill_pack_classification_id", dedupe_key),
        owner_id=owner_id,
        robot_id=robot_id,
        source_record_id=source_record_id,
        source_record_type=type(record).__name__,
        source_stage=source_stage,
        skill_pack_id=skill_pack_id,
        skill_pack_category=skill_pack_id,
        package_display_state=PACKAGE_DISPLAY_STATES[skill_pack_id],
        classification_reason=classification_reason,
        confidence=confidence,
        source_title=source_title,
        source_summary=source_summary,
        safe_evidence_refs=_safe_evidence_refs(record),
        billing_allowed=False,
        entitlement_enforcement_allowed=False,
        package_activation_allowed=False,
        upgrade_prompt_allowed=False,
        telegram_delivery_allowed=False,
        callback_binding_allowed=False,
        followup_intent_creation_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        live_connector_allowed=False,
        external_write_allowed=False,
        worker_dispatch_allowed=False,
        dedupe_key=dedupe_key,
        lineage_summary=_safe_lineage(record),
        created_at=_created_at(record),
    )
    return registry.store_classification(classification)


def create_skill_pack_activation_surface(
    *,
    owner_id: str,
    robot_id: str,
    source_records: SkillPackSourceBundle,
    registry: SkillPackActivationRegistry,
    catalog: tuple[SkillPackCatalogEntryRecord, ...] | None = None,
    created_at: str = "2026-06-20T00:00:00Z",
) -> SkillPackActivationSurfaceRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not isinstance(source_records, SkillPackSourceBundle):
        raise TypeError("rejected_invalid_source_records")

    catalog_entries = build_default_skill_pack_catalog(created_at=created_at) if catalog is None else catalog
    for entry in catalog_entries:
        registry.store_catalog_entry(entry)

    dedupe_key = _stable_id("skill_pack_surface", owner_id, robot_id, SOURCE_STAGE_MIN, SOURCE_STAGE_MAX)
    existing = registry.get_surface_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    classifications: list[SkillPackClassificationRecord] = []
    seen: set[tuple[str, str]] = set()
    for collection in (
        source_records.daily_brief_snapshots_124p,
        source_records.daily_brief_items_124p,
        source_records.proactive_executions_123p,
        source_records.proactive_delegations_122p,
        source_records.proactive_adapters_121p,
        source_records.proactive_deliveries_120p,
        source_records.proactive_opportunities_119p,
        source_records.context_sources_118p,
        source_records.memory_writebacks_117p,
        source_records.memory_approval_surfaces_116p,
        source_records.memory_approval_decisions_116p,
        source_records.memory_proposals_115p,
        source_records.followup_acknowledgements_114p,
        source_records.followup_delegations_111p,
        source_records.followup_selections_110p,
        source_records.followup_choice_surfaces_109p,
        source_records.followup_plans_108p,
        source_records.followup_intents_107p,
        source_records.result_acknowledgements_106p,
        source_records.result_deliveries_105p,
        source_records.inbox_records_103p,
    ):
        for record in collection:
            if getattr(record, "owner_id", owner_id) != owner_id:
                continue
            if getattr(record, "robot_id", robot_id) != robot_id:
                continue
            key = (_source_stage(record), _source_record_id(record))
            if key in seen:
                continue
            try:
                classification = classify_record_for_skill_pack(
                    record=record,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    registry=registry,
                    catalog=catalog_entries,
                )
            except ValueError as exc:
                if str(exc) in {"rejected_raw_sensitive_payload", "rejected_raw_credential_payload"}:
                    continue
                raise
            seen.add(key)
            classifications.append(classification)

    classifications_tuple = tuple(sorted(classifications, key=_classification_sort_key))
    local_render_text = render_skill_pack_activation_surface_text(
        classifications=classifications_tuple,
        catalog=catalog_entries,
    )
    counts = {skill_pack_id: 0 for skill_pack_id in SKILL_PACK_IDS}
    for classification in classifications_tuple:
        counts[classification.skill_pack_id] += 1

    surface = SkillPackActivationSurfaceRecord(
        surface_id=_stable_id("skill_pack_surface_id", dedupe_key),
        owner_id=owner_id,
        robot_id=robot_id,
        source_stage_min=SOURCE_STAGE_MIN,
        source_stage_max=SOURCE_STAGE_MAX,
        surface_stage=SKILL_PACK_STAGE,
        surface_mode=SKILL_PACK_MODE,
        classification_ids=tuple(classification.classification_id for classification in classifications_tuple),
        total_classified_count=len(classifications_tuple),
        robot_core_count=counts["robot_core"],
        basic_package_count=counts["basic_package"],
        pro_package_count=counts["pro_package"],
        documents_pack_count=counts["documents_pack"],
        sales_pack_count=counts["sales_pack"],
        marketing_pack_count=counts["marketing_pack"],
        finance_admin_pack_count=counts["finance_admin_pack"],
        hr_pack_count=counts["hr_pack"],
        memory_center_core_count=counts["memory_center_core"],
        safety_boundary_core_count=counts["safety_boundary_core"],
        unknown_unclassified_count=counts["unknown_unclassified"],
        local_render_text=local_render_text,
        billing_allowed=False,
        entitlement_enforcement_allowed=False,
        package_activation_allowed=False,
        upgrade_prompt_allowed=False,
        telegram_delivery_allowed=False,
        callback_binding_allowed=False,
        followup_intent_creation_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        live_connector_allowed=False,
        external_write_allowed=False,
        worker_dispatch_allowed=False,
        sensitive_data_excluded=True,
        dedupe_key=dedupe_key,
        lineage_summary={
            "surface_stage": SKILL_PACK_STAGE,
            "source_stage_min": SOURCE_STAGE_MIN,
            "source_stage_max": SOURCE_STAGE_MAX,
            "total_classified_count": len(classifications_tuple),
        },
        created_at=created_at,
    )
    return registry.store_surface(surface=surface, classifications=classifications_tuple)


def render_skill_pack_activation_surface_text(
    *,
    classifications: tuple[SkillPackClassificationRecord, ...],
    catalog: tuple[SkillPackCatalogEntryRecord, ...],
) -> str:
    if not classifications:
        return f"Skill Pack Activation Surface\n\n{NO_UPDATES_TEXT}"
    counts = {entry.skill_pack_id: 0 for entry in catalog}
    for classification in classifications:
        counts[classification.skill_pack_id] = counts.get(classification.skill_pack_id, 0) + 1
    lines = ["Skill Pack Activation Surface", "", "Pack counts:"]
    for skill_pack_id in SKILL_PACK_IDS:
        count = counts.get(skill_pack_id, 0)
        if count == 0:
            continue
        lines.append(f"- {skill_pack_id}: {count}")
    lines.extend(("", "Classified items:"))
    for classification in classifications:
        lines.append(
            f"- [{classification.skill_pack_id}] {classification.source_stage} {classification.source_title}: "
            f"{classification.classification_reason}"
        )
    return "\n".join(lines)


def get_skill_pack_classification(
    *,
    registry: SkillPackActivationRegistry,
    classification_id: str,
) -> SkillPackClassificationRecord | None:
    return registry.get_classification(classification_id)


def list_skill_pack_classifications(
    *,
    registry: SkillPackActivationRegistry,
) -> tuple[SkillPackClassificationRecord, ...]:
    return registry.list_classifications()


def get_skill_pack_activation_surface(
    *,
    registry: SkillPackActivationRegistry,
    surface_id: str,
) -> SkillPackActivationSurfaceRecord | None:
    return registry.get_surface(surface_id)


def list_skill_pack_activation_surfaces(
    *,
    registry: SkillPackActivationRegistry,
) -> tuple[SkillPackActivationSurfaceRecord, ...]:
    return registry.list_surfaces()


def _classify_skill_pack(record: object) -> tuple[str, str, str]:
    if isinstance(record, DailyBriefSnapshotRecord):
        return ("basic_package", "Daily brief snapshot demonstrates the What Did I Miss basic summary surface.", "high")
    if isinstance(record, DailyBriefItemRecord):
        return _classify_daily_brief_item(record)
    if isinstance(record, ProactiveOpportunityCandidateRecord):
        return _classify_opportunity(record.opportunity_type)
    if isinstance(record, ContextScanCandidateSourceRecord):
        return ("robot_core", "Generic local context source belongs to robot core state awareness.", "medium")
    if isinstance(record, FollowUpMemoryProposalCandidateRecord):
        return ("memory_center_core", "Memory proposal records belong to Memory Center Core.", "high")
    if isinstance(record, MemoryCenterWritebackRecord):
        return ("memory_center_core", "Memory writeback records belong to Memory Center Core.", "high")
    if isinstance(record, TelegramMemoryProposalApprovalDecisionRecord | TelegramMemoryProposalApprovalSurfaceRecord):
        return ("memory_center_core", "Memory approval records belong to Memory Center Core.", "high")
    if isinstance(record, ProactiveExecutionAttemptRecord):
        if "boundary" in _combined_text(record):
            return ("safety_boundary_core", "Boundary-oriented execution candidate belongs to Safety Boundary Core.", "medium")
        return ("pro_package", "Proactive execution candidates demonstrate pro-level operator workflow support.", "medium")
    if isinstance(record, ProactiveDelegationAdapterRecord | ProactiveSuggestionFollowupAdapterRecord):
        combined = _combined_text(record)
        if "document" in combined or "checklist" in combined:
            return ("documents_pack", "Document-oriented proactive adapter maps to the Documents Pack.", "medium")
        if "meeting" in combined:
            return ("basic_package", "Meeting brief work maps to the Basic Package.", "medium")
        return ("pro_package", "Adapter records demonstrate pro-level workflow orchestration.", "low")
    if isinstance(record, ProactiveTelegramSuggestionDeliveryRecord):
        return ("basic_package", "Proactive suggestion delivery is a basic daily assistance surface.", "medium")
    if isinstance(record, FollowUpDelegationRequestRecord | TelegramFollowUpChoiceSelectionRecord | TelegramFollowUpChoiceSurfaceRecord | FollowUpDraftPlanRecord | FollowUpIntentReviewRecord | FollowUpResultAcknowledgementRecord):
        combined = _combined_text(record)
        if "document" in combined or "checklist" in combined or "nda" in combined or "proposal" in combined:
            return ("documents_pack", "Document-oriented follow-up flow maps to the Documents Pack.", "medium")
        if "lead" in combined or "sales" in combined or "followup" in combined:
            return ("sales_pack", "Sales-style follow-up flow maps to the Sales Pack.", "low")
        return ("pro_package", "Follow-up workflow records demonstrate pro-level operator workflows.", "low")
    if isinstance(record, TelegramResultAcknowledgementRecord | TelegramAsyncResultDeliveryRecord | AsyncDelegationInboxRecord):
        return ("robot_core", "Async result plumbing belongs to Robot Core runtime behavior.", "medium")
    return ("unknown_unclassified", "No deterministic skill pack mapping rule matched this record.", "not_applicable")


def _classify_daily_brief_item(record: DailyBriefItemRecord) -> tuple[str, str, str]:
    combined = f"{record.section_name} {record.title} {record.summary}".lower()
    if record.source_stage == "124P":
        return ("basic_package", "Daily brief summary and review items belong to the Basic Package.", "high")
    if record.source_stage in {"115P", "116P", "117P"}:
        return ("memory_center_core", "Memory-related brief items belong to Memory Center Core.", "high")
    if "boundary" in combined or "blocked" in combined:
        return ("safety_boundary_core", "Boundary and blocked brief items belong to Safety Boundary Core.", "medium")
    if "document" in combined or "nda" in combined or "proposal" in combined or "pdf" in combined or "checklist" in combined:
        return ("documents_pack", "Document-oriented brief items map to the Documents Pack.", "high")
    if "lead" in combined or "crm" in combined or "stale proposal" in combined or "sales" in combined:
        return ("sales_pack", "Sales-oriented brief items map to the Sales Pack.", "high")
    if "invoice" in combined or "payment" in combined or "expense" in combined or "finance" in combined:
        return ("finance_admin_pack", "Finance and admin brief items map to the Finance/Admin Pack.", "high")
    if "candidate" in combined or "interview" in combined or "onboarding" in combined or "hr" in combined:
        return ("hr_pack", "HR-oriented brief items map to the HR Pack.", "high")
    if "campaign" in combined or "newsletter" in combined or "competitor" in combined or "marketing" in combined or "post" in combined:
        return ("marketing_pack", "Marketing-oriented brief items map to the Marketing Pack.", "high")
    if "customer issue" in combined:
        return ("pro_package", "Customer issue review is classified as a Pro Package workflow in this catalog.", "medium")
    if "meeting brief" in combined or "what did i miss" in combined or "headline summary" in combined:
        return ("basic_package", "Meeting brief and summary items map to the Basic Package.", "high")
    if record.section_name in {"completed_today", "lineage_and_safety_summary"}:
        return ("robot_core", "Generic status and context items belong to Robot Core.", "medium")
    return ("unknown_unclassified", "No deterministic brief-item skill pack rule matched this item.", "low")


def _classify_opportunity(opportunity_type: str) -> tuple[str, str, str]:
    mapping = {
        "document_review_needed": ("documents_pack", "Document review opportunity maps to the Documents Pack.", "high"),
        "meeting_brief_missing": ("basic_package", "Meeting brief opportunity maps to the Basic Package.", "high"),
        "lead_followup_due": ("sales_pack", "Lead follow-up opportunity maps to the Sales Pack.", "high"),
        "stale_proposal_followup": ("sales_pack", "Stale proposal follow-up maps to the Sales Pack.", "high"),
        "invoice_due_soon": ("finance_admin_pack", "Invoice due opportunity maps to the Finance/Admin Pack.", "high"),
        "customer_issue_needs_attention": ("pro_package", "Customer issue review is classified as a Pro Package workflow in this catalog.", "medium"),
        "boundary_review_needed": ("safety_boundary_core", "Boundary review opportunity maps to Safety Boundary Core.", "high"),
        "memory_gap_detected": ("safety_boundary_core", "Memory gap boundary review maps to Safety Boundary Core.", "medium"),
        "task_deadline_risk": ("pro_package", "Deadline-risk orchestration maps to the Pro Package.", "medium"),
        "unread_context_needs_summary": ("basic_package", "Unread context summaries map to the Basic Package.", "medium"),
        "no_opportunity": ("robot_core", "No-opportunity detection belongs to Robot Core telemetry.", "not_applicable"),
    }
    return mapping.get(opportunity_type, ("unknown_unclassified", "No deterministic opportunity skill pack rule matched this type.", "low"))


def _source_stage(record: object) -> str:
    if isinstance(record, DailyBriefSnapshotRecord | DailyBriefItemRecord):
        return "124P"
    if isinstance(record, ProactiveExecutionAttemptRecord):
        return "123P"
    if isinstance(record, ProactiveDelegationAdapterRecord):
        return "122P"
    if isinstance(record, ProactiveSuggestionFollowupAdapterRecord):
        return "121P"
    if isinstance(record, ProactiveTelegramSuggestionDeliveryRecord):
        return "120P"
    if isinstance(record, ProactiveOpportunityCandidateRecord):
        return "119P"
    if isinstance(record, ContextScanCandidateSourceRecord):
        return "118P"
    if isinstance(record, MemoryCenterWritebackRecord):
        return "117P"
    if isinstance(record, TelegramMemoryProposalApprovalDecisionRecord | TelegramMemoryProposalApprovalSurfaceRecord):
        return "116P"
    if isinstance(record, FollowUpMemoryProposalCandidateRecord):
        return "115P"
    if isinstance(record, FollowUpResultAcknowledgementRecord):
        return "114P"
    if isinstance(record, FollowUpDelegationRequestRecord):
        return "111P"
    if isinstance(record, TelegramFollowUpChoiceSelectionRecord):
        return "110P"
    if isinstance(record, TelegramFollowUpChoiceSurfaceRecord):
        return "109P"
    if isinstance(record, FollowUpDraftPlanRecord):
        return "108P"
    if isinstance(record, FollowUpIntentReviewRecord):
        return "107P"
    if isinstance(record, TelegramResultAcknowledgementRecord):
        return "106P"
    if isinstance(record, TelegramAsyncResultDeliveryRecord):
        return "105P"
    if isinstance(record, AsyncDelegationInboxRecord):
        return "103P"
    return "unknown"


def _source_record_id(record: object) -> str:
    for attr in (
        "item_id",
        "brief_id",
        "proactive_execution_attempt_id",
        "proactive_delegation_adapter_id",
        "adapter_id",
        "delivery_record_id",
        "opportunity_id",
        "candidate_source_id",
        "writeback_id",
        "decision_id",
        "surface_id",
        "proposal_id",
        "acknowledgement_id",
        "followup_delegation_id",
        "selection_id",
        "choice_surface_id",
        "draft_plan_id",
        "followup_intent_id",
        "delivery_id",
        "inbox_record_id",
    ):
        value = getattr(record, attr, None)
        if isinstance(value, str) and value:
            return value
    return type(record).__name__.lower()


def _source_title(record: object) -> str:
    for attr in ("title", "source_title", "section_name", "skill_pack_id"):
        value = getattr(record, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return type(record).__name__


def _source_summary(record: object) -> str:
    for attr in ("summary", "source_summary", "review_summary", "response_text", "result_summary", "failure_reason", "headline_summary", "local_render_text", "review_reason", "classification_reason"):
        value = getattr(record, attr, None)
        if isinstance(value, str) and value.strip():
            return _safe_text(value)
    return "No additional safe summary was available."


def _combined_text(record: object) -> str:
    values = [
        _source_title(record),
        _source_summary(record),
        str(getattr(record, "opportunity_type", "")),
        str(getattr(record, "normalized_intent_kind", "")),
        str(getattr(record, "mapped_task_class", "")),
        str(getattr(record, "followup_task_class", "")),
        str(getattr(record, "proposal_type", "")),
        str(getattr(record, "memory_section", "")),
    ]
    return " ".join(values).lower()


def _reject_sensitive_text(value: str) -> None:
    lowered = value.lower()
    if any(keyword in lowered for keyword in {"password", "passwd", "api_key", "api key", "secret", "credential", "private key", "private_key"}):
        raise ValueError("rejected_raw_credential_payload")
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        raise ValueError("rejected_raw_sensitive_payload")


def _safe_text(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        return "Sensitive details were excluded from this classification."
    return text


def _safe_evidence_refs(record: object) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    ref: dict[str, object] = {
        "source_record_id": _source_record_id(record),
        "source_stage": _source_stage(record),
    }
    for attr in (
        "source_type",
        "source_category",
        "opportunity_type",
        "opportunity_category",
        "mapped_task_class",
        "followup_task_class",
        "proposal_type",
        "memory_section",
        "section_name",
    ):
        value = getattr(record, attr, None)
        if isinstance(value, str) and value:
            ref[attr] = value
    refs.append(ref)
    return tuple(refs)


def _safe_lineage(record: object) -> dict[str, object]:
    lineage = getattr(record, "lineage_summary", None)
    if not isinstance(lineage, dict):
        lineage = getattr(record, "lineage_metadata", {})
    return _safe_lineage_dict(lineage if isinstance(lineage, dict) else {})


def _safe_lineage_dict(value: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, raw_value in value.items():
        if key not in SAFE_LINEAGE_KEYS and key != "upstream_lineage":
            continue
        if isinstance(raw_value, dict):
            nested = _safe_lineage_dict(raw_value)
            if nested:
                safe[key] = nested
            continue
        if isinstance(raw_value, str):
            if any(keyword in raw_value.lower() for keyword in SENSITIVE_KEYWORDS):
                continue
            safe[key] = raw_value
            continue
        if isinstance(raw_value, (int, float, bool)) or raw_value is None:
            safe[key] = raw_value
    return safe


def _created_at(record: object) -> str:
    value = getattr(record, "created_at", None)
    if isinstance(value, str) and value:
        return value
    return "2026-06-20T00:00:00Z"


def _classification_sort_key(record: SkillPackClassificationRecord) -> tuple[int, str, str, str]:
    return (
        SOURCE_STAGE_ORDER.get(record.source_stage, 999),
        record.skill_pack_id,
        record.source_title,
        record.source_record_id,
    )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(parts)))
