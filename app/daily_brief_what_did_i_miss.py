from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date, datetime
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from app.async_delegation_inbox import AsyncDelegationInboxRecord
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
from app.context_scan_candidate_source import ContextScanCandidateSourceRecord


DAILY_BRIEF_STAGE = "124P"
DAILY_BRIEF_MODE = "deterministic_local_read_only"
SOURCE_STAGE_MIN = "103P"
SOURCE_STAGE_MAX = "123P"
NO_UPDATES_SUMMARY = "No updates were recorded in the selected window."
SECTION_ORDER = (
    "headline_summary",
    "needs_attention",
    "pending_results",
    "pending_followups",
    "pending_memory_reviews",
    "memory_written_today",
    "proactive_opportunities",
    "proactive_suggestions_sent_local",
    "proactive_execution_candidates",
    "blocked_or_rejected_items",
    "completed_today",
    "suggested_next_reviews",
    "lineage_and_safety_summary",
)
SECTION_TITLES = {
    "headline_summary": "Headline Summary",
    "needs_attention": "Needs Attention",
    "pending_results": "Pending Results",
    "pending_followups": "Pending Follow-ups",
    "pending_memory_reviews": "Pending Memory Reviews",
    "memory_written_today": "Memory Written Today",
    "proactive_opportunities": "Proactive Opportunities",
    "proactive_suggestions_sent_local": "Proactive Suggestions Sent Local",
    "proactive_execution_candidates": "Proactive Execution Candidates",
    "blocked_or_rejected_items": "Blocked Or Rejected Items",
    "completed_today": "Completed Today",
    "suggested_next_reviews": "Suggested Next Reviews",
    "lineage_and_safety_summary": "Lineage And Safety Summary",
}
SECTION_DISPLAY_ORDER = {name: index for index, name in enumerate(SECTION_ORDER, start=1)}
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "informational": 4,
}
STAGE_ORDER = {f"{number}P": number for number in range(103, 125)}
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
    "diagnosis",
    "medical record",
    "passport",
    "driver license",
)
BLOCKED_REVIEW_TYPES = (
    "review_blocked_items",
    "review_pending_results",
    "review_pending_followups",
    "review_pending_memory",
    "review_proactive_candidates",
    "review_context_sources",
)
SAFE_LINEAGE_KEYS = {
    "event_id",
    "handle_id",
    "request_id",
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
    "source_stage",
    "delivery_stage",
    "acknowledgement_stage",
    "proposal_stage",
    "surface_stage",
    "decision_stage",
    "writeback_stage",
    "detection_stage",
    "suggestion_stage",
    "adapter_stage",
    "delegation_adapter_stage",
    "execution_stage",
    "followup_stage",
    "status",
    "event_status",
    "opportunity_type",
    "opportunity_category",
    "selected_option_kind",
    "followup_task_class",
    "memory_item_id",
    "memory_kind",
}


@dataclass(frozen=True, slots=True)
class DailyBriefGenerationInputRecord:
    generation_input_id: str
    owner_id: str
    robot_id: str
    brief_date: str
    timezone: str
    window_start: str
    window_end: str
    included_stage_range: tuple[str, str]
    created_at: str


@dataclass(frozen=True, slots=True)
class DailyBriefItemRecord:
    item_id: str
    brief_id: str
    owner_id: str
    robot_id: str
    source_record_id: str
    source_record_type: str
    source_stage: str
    section_name: str
    title: str
    summary: str
    status: str
    severity: str
    safe_evidence_refs: tuple[dict[str, object], ...]
    suggested_review_type: str | None
    action_allowed: bool
    telegram_delivery_allowed: bool
    callback_binding_allowed: bool
    delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    sensitive_data_excluded: bool
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.section_name not in SECTION_TITLES:
            raise ValueError("rejected_invalid_section_name")
        if self.severity not in SEVERITY_ORDER:
            raise ValueError("rejected_invalid_severity")
        if any(
            (
                self.action_allowed,
                self.telegram_delivery_allowed,
                self.callback_binding_allowed,
                self.delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class DailyBriefSectionRecord:
    section_id: str
    brief_id: str
    owner_id: str
    robot_id: str
    section_name: str
    section_title: str
    item_ids: tuple[str, ...]
    item_count: int
    display_order: int
    created_at: str

    def __post_init__(self) -> None:
        if self.section_name not in SECTION_TITLES:
            raise ValueError("rejected_invalid_section_name")
        if self.section_title != SECTION_TITLES[self.section_name]:
            raise ValueError("rejected_invalid_section_title")
        if self.display_order != SECTION_DISPLAY_ORDER[self.section_name]:
            raise ValueError("rejected_invalid_display_order")


@dataclass(frozen=True, slots=True)
class DailyBriefSnapshotRecord:
    brief_id: str
    owner_id: str
    robot_id: str
    brief_date: str
    timezone: str
    window_start: str
    window_end: str
    source_stage_min: str
    source_stage_max: str
    brief_stage: str
    brief_mode: str
    headline_summary: str
    section_ids: tuple[str, ...]
    total_item_count: int
    needs_attention_count: int
    pending_review_count: int
    blocked_or_rejected_count: int
    completed_count: int
    proactive_opportunity_count: int
    memory_review_count: int
    memory_written_count: int
    local_render_text: str
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
        if self.brief_stage != DAILY_BRIEF_STAGE:
            raise ValueError("rejected_invalid_brief_stage")
        if self.brief_mode != DAILY_BRIEF_MODE:
            raise ValueError("rejected_invalid_brief_mode")
        if any(
            (
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
class DailyBriefSourceBundle:
    inbox_records_103p: tuple[AsyncDelegationInboxRecord, ...] = ()
    delivery_records_105p: tuple[TelegramAsyncResultDeliveryRecord, ...] = ()
    result_acknowledgements_106p: tuple[TelegramResultAcknowledgementRecord, ...] = ()
    followup_intents_107p: tuple[FollowUpIntentReviewRecord, ...] = ()
    followup_plans_108p: tuple[FollowUpDraftPlanRecord, ...] = ()
    followup_choice_surfaces_109p: tuple[TelegramFollowUpChoiceSurfaceRecord, ...] = ()
    followup_selections_110p: tuple[TelegramFollowUpChoiceSelectionRecord, ...] = ()
    followup_delegations_111p: tuple[FollowUpDelegationRequestRecord, ...] = ()
    followup_acknowledgements_114p: tuple[FollowUpResultAcknowledgementRecord, ...] = ()
    memory_proposals_115p: tuple[FollowUpMemoryProposalCandidateRecord, ...] = ()
    memory_approval_surfaces_116p: tuple[TelegramMemoryProposalApprovalSurfaceRecord, ...] = ()
    memory_approval_decisions_116p: tuple[TelegramMemoryProposalApprovalDecisionRecord, ...] = ()
    memory_writebacks_117p: tuple[MemoryCenterWritebackRecord, ...] = ()
    context_sources_118p: tuple[ContextScanCandidateSourceRecord, ...] = ()
    proactive_opportunities_119p: tuple[ProactiveOpportunityCandidateRecord, ...] = ()
    proactive_deliveries_120p: tuple[ProactiveTelegramSuggestionDeliveryRecord, ...] = ()
    proactive_adapters_121p: tuple[ProactiveSuggestionFollowupAdapterRecord, ...] = ()
    proactive_delegations_122p: tuple[ProactiveDelegationAdapterRecord, ...] = ()
    proactive_executions_123p: tuple[ProactiveExecutionAttemptRecord, ...] = ()


@dataclass(slots=True)
class DailyBriefRegistry:
    generation_inputs_by_id: dict[str, DailyBriefGenerationInputRecord] = field(default_factory=dict)
    snapshots_by_id: dict[str, DailyBriefSnapshotRecord] = field(default_factory=dict)
    snapshot_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    sections_by_id: dict[str, DailyBriefSectionRecord] = field(default_factory=dict)
    items_by_id: dict[str, DailyBriefItemRecord] = field(default_factory=dict)
    item_ids_by_brief_id: dict[str, tuple[str, ...]] = field(default_factory=dict)
    section_ids_by_brief_id: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def store_generation_input(self, record: DailyBriefGenerationInputRecord) -> DailyBriefGenerationInputRecord:
        self.generation_inputs_by_id[record.generation_input_id] = record
        return record

    def store_snapshot(
        self,
        *,
        snapshot: DailyBriefSnapshotRecord,
        sections: tuple[DailyBriefSectionRecord, ...],
        items: tuple[DailyBriefItemRecord, ...],
    ) -> DailyBriefSnapshotRecord:
        self.snapshots_by_id[snapshot.brief_id] = snapshot
        self.snapshot_ids_by_dedupe_key[snapshot.dedupe_key] = snapshot.brief_id
        self.item_ids_by_brief_id[snapshot.brief_id] = tuple(item.item_id for item in items)
        self.section_ids_by_brief_id[snapshot.brief_id] = tuple(section.section_id for section in sections)
        for section in sections:
            self.sections_by_id[section.section_id] = section
        for item in items:
            self.items_by_id[item.item_id] = item
        return snapshot

    def get_snapshot(self, brief_id: str) -> DailyBriefSnapshotRecord | None:
        return self.snapshots_by_id.get(brief_id)

    def get_snapshot_by_dedupe_key(self, dedupe_key: str) -> DailyBriefSnapshotRecord | None:
        brief_id = self.snapshot_ids_by_dedupe_key.get(dedupe_key)
        if brief_id is None:
            return None
        return self.snapshots_by_id.get(brief_id)

    def list_snapshots(self) -> tuple[DailyBriefSnapshotRecord, ...]:
        return tuple(self.snapshots_by_id[key] for key in sorted(self.snapshots_by_id))

    def list_items(self, *, brief_id: str | None = None) -> tuple[DailyBriefItemRecord, ...]:
        if brief_id is None:
            return tuple(self.items_by_id[key] for key in sorted(self.items_by_id))
        item_ids = self.item_ids_by_brief_id.get(brief_id, ())
        return tuple(self.items_by_id[item_id] for item_id in item_ids if item_id in self.items_by_id)

    def list_sections(self, *, brief_id: str | None = None) -> tuple[DailyBriefSectionRecord, ...]:
        if brief_id is None:
            return tuple(self.sections_by_id[key] for key in sorted(self.sections_by_id))
        section_ids = self.section_ids_by_brief_id.get(brief_id, ())
        return tuple(self.sections_by_id[section_id] for section_id in section_ids if section_id in self.sections_by_id)


def create_daily_brief_snapshot(
    *,
    owner_id: str,
    robot_id: str,
    brief_date: str,
    timezone: str,
    window_start: str,
    window_end: str,
    source_records: DailyBriefSourceBundle,
    registry: DailyBriefRegistry,
    created_at: str | None = None,
) -> DailyBriefSnapshotRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not isinstance(source_records, DailyBriefSourceBundle):
        raise TypeError("rejected_invalid_source_records")

    resolved_date, resolved_tz, resolved_window_start, resolved_window_end = _validate_window(
        brief_date=brief_date,
        timezone_name=timezone,
        window_start=window_start,
        window_end=window_end,
    )
    created_marker = created_at or resolved_window_end.isoformat().replace("+00:00", "Z")
    dedupe_key = _stable_id(
        "daily_brief_snapshot",
        owner_id,
        robot_id,
        resolved_date.isoformat(),
        resolved_tz.key,
        resolved_window_start.isoformat(),
        resolved_window_end.isoformat(),
    )
    existing = registry.get_snapshot_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    generation_input = DailyBriefGenerationInputRecord(
        generation_input_id=_stable_id("daily_brief_generation_input", dedupe_key),
        owner_id=owner_id,
        robot_id=robot_id,
        brief_date=resolved_date.isoformat(),
        timezone=resolved_tz.key,
        window_start=_to_zulu(resolved_window_start),
        window_end=_to_zulu(resolved_window_end),
        included_stage_range=(SOURCE_STAGE_MIN, SOURCE_STAGE_MAX),
        created_at=created_marker,
    )
    registry.store_generation_input(generation_input)

    brief_id = _stable_id("daily_brief_snapshot_id", dedupe_key)
    section_buckets: dict[str, list[DailyBriefItemRecord]] = {name: [] for name in SECTION_ORDER}
    input_record_counts = _input_record_counts(source_records=source_records)
    filtered = _filtered_records(
        source_records=source_records,
        owner_id=owner_id,
        robot_id=robot_id,
        window_start=resolved_window_start,
        window_end=resolved_window_end,
    )

    pending_result_delivery_ids = {
        record.delivery_id
        for record in filtered["delivery_records_105p"]
        if record.status == "delivered" and not _has_result_ack(record=record, acknowledgements=filtered["result_acknowledgements_106p"])
    }
    written_proposal_ids = {
        record.proposal_id
        for record in filtered["memory_writebacks_117p"]
        if record.writeback_status in {"written", "duplicate_existing"}
    }
    proactive_delivery_ids = {record.delivery_record_id for record in filtered["proactive_deliveries_120p"]}
    proactive_adapter_opportunity_ids = {record.opportunity_id for record in filtered["proactive_adapters_121p"]}

    seen_source_keys: set[tuple[str, str, str]] = set()
    for record in filtered["delivery_records_105p"]:
        if record.status == "delivered" and not _has_result_ack(record=record, acknowledgements=filtered["result_acknowledgements_106p"]):
            _add_item(
                bucket=section_buckets["pending_results"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.delivery_id,
                    source_record_type=type(record).__name__,
                    source_stage="105P",
                    section_name="pending_results",
                    title="Async result awaiting acknowledgement",
                    summary=_safe_summary(
                        f"Telegram async result delivery {record.delivery_id} is delivered locally and still awaiting owner acknowledgement."
                    ),
                    status="pending_acknowledgement",
                    severity="high",
                    safe_evidence_refs=(
                        {"delivery_id": record.delivery_id, "surface_id": record.surface_id, "inbox_record_id": record.inbox_record_id},
                    ),
                    suggested_review_type="review_pending_results",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )
        if _is_blocked_delivery(record):
            _add_item(
                bucket=section_buckets["blocked_or_rejected_items"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.delivery_id,
                    source_record_type=type(record).__name__,
                    source_stage="105P",
                    section_name="blocked_or_rejected_items",
                    title="Async result delivery blocked",
                    summary=_safe_summary(record.rejection_reason or "Local Telegram delivery did not complete."),
                    status="blocked",
                    severity="critical",
                    safe_evidence_refs=({"delivery_id": record.delivery_id, "surface_id": record.surface_id},),
                    suggested_review_type="review_blocked_items",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    for record in filtered["result_acknowledgements_106p"]:
        if record.status == "blocked":
            section_name = "blocked_or_rejected_items"
            title = "Result acknowledgement blocked"
            severity = "high"
            status = "blocked"
            review_type = "review_blocked_items"
        else:
            section_name = "completed_today"
            title = "Result acknowledgement recorded"
            severity = "low"
            status = "completed"
            review_type = None
        _add_item(
            bucket=section_buckets[section_name],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.acknowledgement_id,
                source_record_type=type(record).__name__,
                source_stage="106P",
                section_name=section_name,
                title=title,
                summary=_safe_summary(record.response_text),
                status=status,
                severity=severity,
                safe_evidence_refs=(
                    {
                        "acknowledgement_id": record.acknowledgement_id,
                        "delivery_id": record.delivery_id,
                        "surface_id": record.surface_id,
                    },
                ),
                suggested_review_type=review_type,
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_intents_107p"]:
        target_section = "pending_followups" if record.status in {"pending_review", "dismissed", "resolved_no_action"} else "blocked_or_rejected_items"
        severity = "high" if record.status == "pending_review" else "medium"
        status = record.status if record.status != "pending_review" else "pending_review"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.followup_intent_id,
                source_record_type=type(record).__name__,
                source_stage="107P",
                section_name=target_section,
                title="Follow-up intent review",
                summary=_safe_summary(record.review_summary),
                status=status,
                severity=severity,
                safe_evidence_refs=({"followup_intent_id": record.followup_intent_id, "acknowledgement_id": record.acknowledgement_id},),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_plans_108p"]:
        target_section = "pending_followups" if record.status == "drafted" else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.draft_plan_id,
                source_record_type=type(record).__name__,
                source_stage="108P",
                section_name=target_section,
                title="Follow-up draft plan",
                summary=_safe_summary(record.summary),
                status="pending_review" if target_section == "pending_followups" else "blocked",
                severity="medium" if target_section == "pending_followups" else "high",
                safe_evidence_refs=({"draft_plan_id": record.draft_plan_id, "followup_intent_id": record.followup_intent_id},),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_choice_surfaces_109p"]:
        target_section = "pending_followups" if record.status in {"rendered", "delivered"} else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.choice_surface_id,
                source_record_type=type(record).__name__,
                source_stage="109P",
                section_name=target_section,
                title="Follow-up choice surface",
                summary=_safe_summary(record.text),
                status="delivered_local" if record.status == "delivered" else ("pending_review" if target_section == "pending_followups" else "blocked"),
                severity="medium" if target_section == "pending_followups" else "high",
                safe_evidence_refs=({"choice_surface_id": record.choice_surface_id, "draft_plan_id": record.draft_plan_id},),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_selections_110p"]:
        if record.status == "blocked":
            section_name = "blocked_or_rejected_items"
            severity = "high"
            review_type = "review_blocked_items"
        elif record.status == "cancelled_no_action":
            section_name = "blocked_or_rejected_items"
            severity = "low"
            review_type = "review_pending_followups"
        else:
            section_name = "pending_followups"
            severity = "high"
            review_type = "review_pending_followups"
        _add_item(
            bucket=section_buckets[section_name],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.selection_id,
                source_record_type=type(record).__name__,
                source_stage="110P",
                section_name=section_name,
                title="Follow-up choice selection",
                summary=_safe_summary(record.response_text),
                status="pending_review" if section_name == "pending_followups" else ("blocked" if record.status == "blocked" else "rejected"),
                severity=severity,
                safe_evidence_refs=(
                    {
                        "selection_id": record.selection_id,
                        "choice_surface_id": record.choice_surface_id,
                        "selected_option_kind": record.selected_option_kind,
                    },
                ),
                suggested_review_type=review_type,
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_delegations_111p"]:
        target_section = "pending_followups" if record.status == "registered" else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.followup_delegation_id,
                source_record_type=type(record).__name__,
                source_stage="111P",
                section_name=target_section,
                title="Follow-up delegation record",
                summary=_safe_summary(
                    f"Follow-up delegation for {record.followup_task_class or 'unknown_task'} is {record.status}."
                ),
                status="pending_review" if target_section == "pending_followups" else ("blocked" if record.status == "blocked" else "rejected"),
                severity="high" if target_section == "pending_followups" else "medium",
                safe_evidence_refs=(
                    {
                        "delegation_id": record.followup_delegation_id,
                        "selection_id": record.selection_id,
                        "packet_id": record.async_packet_id or "",
                        "handle_id": record.async_handle_id or "",
                    },
                ),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["followup_acknowledgements_114p"]:
        target_section = "completed_today" if record.status in {"acknowledged", "dismissed", "lineage_summary_requested"} else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.acknowledgement_id,
                source_record_type=type(record).__name__,
                source_stage="114P",
                section_name=target_section,
                title="Follow-up result acknowledgement",
                summary=_safe_summary(record.response_text),
                status="completed" if target_section == "completed_today" else "blocked",
                severity="low" if target_section == "completed_today" else "high",
                safe_evidence_refs=({"acknowledgement_id": record.acknowledgement_id, "route_id": record.route_id},),
                suggested_review_type=None if target_section == "completed_today" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_metadata),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["memory_proposals_115p"]:
        if record.proposal_id not in written_proposal_ids and record.status in {"pending_user_review", "no_memory_recommended"}:
            _add_item(
                bucket=section_buckets["pending_memory_reviews"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.proposal_id,
                    source_record_type=type(record).__name__,
                    source_stage="115P",
                    section_name="pending_memory_reviews",
                    title="Memory proposal awaiting review",
                    summary=_safe_summary(record.review_reason),
                    status="pending_review",
                    severity="medium",
                    safe_evidence_refs=({"proposal_id": record.proposal_id, "acknowledgement_id": record.acknowledgement_id},),
                    suggested_review_type="review_pending_memory",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )
        if record.status == "rejected_source" or record.rejection_reason:
            _add_item(
                bucket=section_buckets["blocked_or_rejected_items"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.proposal_id,
                    source_record_type=type(record).__name__,
                    source_stage="115P",
                    section_name="blocked_or_rejected_items",
                    title="Memory proposal rejected",
                    summary=_safe_summary(record.rejection_reason or record.review_reason),
                    status="rejected",
                    severity="medium",
                    safe_evidence_refs=({"proposal_id": record.proposal_id, "delivery_record_id": record.delivery_record_id},),
                    suggested_review_type="review_blocked_items",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    for record in filtered["memory_approval_decisions_116p"]:
        if record.decision_status in {"approved_pending_writeback", "edited_pending_writeback"} and record.proposal_id not in written_proposal_ids:
            _add_item(
                bucket=section_buckets["pending_memory_reviews"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.decision_id,
                    source_record_type=type(record).__name__,
                    source_stage="116P",
                    section_name="pending_memory_reviews",
                    title="Approved memory awaiting writeback",
                    summary=_safe_summary(record.response_text),
                    status="pending_writeback",
                    severity="high",
                    safe_evidence_refs=({"decision_id": record.decision_id, "proposal_id": record.proposal_id},),
                    suggested_review_type="review_pending_memory",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )
        if record.decision_status in {"blocked", "rejected_no_write", "rejected_sensitive_edit"}:
            _add_item(
                bucket=section_buckets["blocked_or_rejected_items"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.decision_id,
                    source_record_type=type(record).__name__,
                    source_stage="116P",
                    section_name="blocked_or_rejected_items",
                    title="Memory approval decision blocked or rejected",
                    summary=_safe_summary(record.response_text),
                    status="blocked" if record.decision_status == "blocked" else "rejected",
                    severity="high" if record.decision_status == "blocked" else "medium",
                    safe_evidence_refs=({"decision_id": record.decision_id, "proposal_id": record.proposal_id},),
                    suggested_review_type="review_blocked_items",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    for record in filtered["memory_writebacks_117p"]:
        if record.writeback_status == "written":
            target_section = "memory_written_today"
            status = "completed"
            severity = "low"
            review_type = None
        elif record.writeback_status == "duplicate_existing":
            target_section = "completed_today"
            status = "duplicate_existing"
            severity = "low"
            review_type = None
        else:
            target_section = "blocked_or_rejected_items"
            status = "blocked" if record.writeback_status.startswith("rejected") else "rejected"
            severity = "high"
            review_type = "review_blocked_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.writeback_id,
                source_record_type=type(record).__name__,
                source_stage="117P",
                section_name=target_section,
                title="Memory Center writeback",
                summary=_safe_summary(record.final_memory_text or record.rejection_reason or record.writeback_status),
                status=status,
                severity=severity,
                safe_evidence_refs=({"writeback_id": record.writeback_id, "proposal_id": record.proposal_id, "memory_item_id": record.memory_item_id or ""},),
                suggested_review_type=review_type,
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["context_sources_118p"]:
        if _valid_lineage(record.lineage_summary):
            _add_item(
                bucket=section_buckets["completed_today"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.candidate_source_id,
                    source_record_type=type(record).__name__,
                    source_stage="118P",
                    section_name="completed_today",
                    title="Context source registered",
                    summary=_safe_summary(record.source_title),
                    status="informational",
                    severity="informational",
                    safe_evidence_refs=(
                        {
                            "candidate_source_id": record.candidate_source_id,
                            "source_type": record.source_type,
                            "source_category": record.source_category,
                        },
                    ),
                    suggested_review_type="review_context_sources",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    for record in filtered["proactive_opportunities_119p"]:
        if record.opportunity_type == "no_opportunity":
            continue
        surfaced = any(delivery.opportunity_id == record.opportunity_id for delivery in filtered["proactive_deliveries_120p"])
        adapted = record.opportunity_id in proactive_adapter_opportunity_ids
        if not surfaced or not adapted:
            _add_item(
                bucket=section_buckets["proactive_opportunities"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.opportunity_id,
                    source_record_type=type(record).__name__,
                    source_stage="119P",
                    section_name="proactive_opportunities",
                    title="Proactive opportunity candidate",
                    summary=_safe_summary(record.summary),
                    status="candidate_created",
                    severity=_proactive_severity(record.opportunity_type),
                    safe_evidence_refs=(
                        {
                            "opportunity_id": record.opportunity_id,
                            "candidate_source_id": record.candidate_source_id,
                            "opportunity_type": record.opportunity_type,
                        },
                    ),
                    suggested_review_type="review_proactive_candidates",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    for record in filtered["proactive_deliveries_120p"]:
        if record.delivery_status == "delivered_local":
            target_section = "proactive_suggestions_sent_local"
            status = "delivered_local"
            severity = "low"
            review_type = "review_proactive_candidates"
        else:
            target_section = "blocked_or_rejected_items"
            status = "blocked" if record.delivery_status.startswith("rejected") else "rejected"
            severity = "high"
            review_type = "review_blocked_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.delivery_record_id,
                source_record_type=type(record).__name__,
                source_stage="120P",
                section_name=target_section,
                title="Proactive suggestion delivery",
                summary=_safe_summary(f"Proactive suggestion delivery status: {record.delivery_status}."),
                status=status,
                severity=severity,
                safe_evidence_refs=({"delivery_record_id": record.delivery_record_id, "opportunity_id": record.opportunity_id},),
                suggested_review_type=review_type,
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["proactive_adapters_121p"]:
        target_section = "pending_followups" if record.adapter_status == "adapted_to_followup_intent" else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.adapter_id,
                source_record_type=type(record).__name__,
                source_stage="121P",
                section_name=target_section,
                title="Proactive suggestion adapter",
                summary=_safe_summary(
                    f"Proactive suggestion was normalized into follow-up intent {record.normalized_intent_kind}."
                ),
                status="pending_review" if target_section == "pending_followups" else "blocked",
                severity="medium" if target_section == "pending_followups" else "high",
                safe_evidence_refs=({"adapter_id": record.adapter_id, "opportunity_id": record.opportunity_id},),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["proactive_delegations_122p"]:
        target_section = "pending_followups" if record.adapter_status == "delegated_registered" else "blocked_or_rejected_items"
        _add_item(
            bucket=section_buckets[target_section],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.proactive_delegation_adapter_id,
                source_record_type=type(record).__name__,
                source_stage="122P",
                section_name=target_section,
                title="Proactive delegation adapter",
                summary=_safe_summary(
                    f"Proactive delegation adapter is {record.adapter_status} for task class {record.mapped_task_class}."
                ),
                status="pending_review" if target_section == "pending_followups" else "blocked",
                severity="high" if target_section == "pending_followups" else "high",
                safe_evidence_refs=(
                    {
                        "delegation_id": record.delegation_handle_id,
                        "packet_id": record.delegation_packet_id,
                        "opportunity_id": record.opportunity_id,
                    },
                ),
                suggested_review_type="review_pending_followups" if target_section == "pending_followups" else "review_blocked_items",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )

    for record in filtered["proactive_executions_123p"]:
        section_name = "proactive_execution_candidates"
        status = "candidate_created" if record.attempt_status == "completed_candidate_created" else ("failed" if record.attempt_status == "failure_candidate_created" else "blocked")
        severity = "high" if status == "failed" else ("medium" if status == "candidate_created" else "high")
        _add_item(
            bucket=section_buckets[section_name],
            seen_source_keys=seen_source_keys,
            item=_make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=record.proactive_execution_attempt_id,
                source_record_type=type(record).__name__,
                source_stage="123P",
                section_name=section_name,
                title="Proactive execution candidate",
                summary=_safe_summary(record.result_summary or record.failure_reason or record.attempt_status),
                status=status,
                severity=severity,
                safe_evidence_refs=(
                    {
                        "attempt_id": record.proactive_execution_attempt_id,
                        "packet_id": record.delegation_packet_id,
                        "handle_id": record.delegation_handle_id,
                    },
                ),
                suggested_review_type="review_proactive_candidates",
                lineage_summary=_safe_lineage_dict(record.lineage_summary),
                created_at=_record_created_at(record),
            ),
        )
        if status in {"failed", "blocked"}:
            _add_item(
                bucket=section_buckets["blocked_or_rejected_items"],
                seen_source_keys=seen_source_keys,
                item=_make_item(
                    brief_id=brief_id,
                    owner_id=owner_id,
                    robot_id=robot_id,
                    source_record_id=record.proactive_execution_attempt_id,
                    source_record_type=type(record).__name__,
                    source_stage="123P",
                    section_name="blocked_or_rejected_items",
                    title="Proactive execution failure candidate",
                    summary=_safe_summary(record.failure_reason or record.attempt_status),
                    status=status,
                    severity="high",
                    safe_evidence_refs=({"attempt_id": record.proactive_execution_attempt_id, "packet_id": record.delegation_packet_id},),
                    suggested_review_type="review_blocked_items",
                    lineage_summary=_safe_lineage_dict(record.lineage_summary),
                    created_at=_record_created_at(record),
                ),
            )

    attention_items = _derive_attention_items(
        brief_id=brief_id,
        owner_id=owner_id,
        robot_id=robot_id,
        candidate_items=(
            *section_buckets["blocked_or_rejected_items"],
            *section_buckets["pending_memory_reviews"],
            *section_buckets["pending_results"],
            *section_buckets["pending_followups"],
            *section_buckets["proactive_execution_candidates"],
            *section_buckets["proactive_opportunities"],
        ),
    )
    section_buckets["needs_attention"].extend(attention_items)
    section_buckets["headline_summary"].append(
        _make_item(
            brief_id=brief_id,
            owner_id=owner_id,
            robot_id=robot_id,
            source_record_id=brief_id,
            source_record_type="DailyBriefHeadline",
            source_stage=DAILY_BRIEF_STAGE,
            section_name="headline_summary",
            title="Daily brief summary",
            summary=_headline_summary(section_buckets=section_buckets),
            status="informational",
            severity="informational",
            safe_evidence_refs=(),
            suggested_review_type=None,
            lineage_summary={
                "brief_stage": DAILY_BRIEF_STAGE,
                "source_stage_min": SOURCE_STAGE_MIN,
                "source_stage_max": SOURCE_STAGE_MAX,
            },
            created_at=created_marker,
        )
    )
    section_buckets["suggested_next_reviews"].extend(
        _build_suggested_review_items(
            brief_id=brief_id,
            owner_id=owner_id,
            robot_id=robot_id,
            section_buckets=section_buckets,
            created_at=created_marker,
        )
    )
    section_buckets["lineage_and_safety_summary"].append(
        _make_item(
            brief_id=brief_id,
            owner_id=owner_id,
            robot_id=robot_id,
            source_record_id=f"{brief_id}:lineage",
            source_record_type="DailyBriefSafetySummary",
            source_stage=DAILY_BRIEF_STAGE,
            section_name="lineage_and_safety_summary",
            title="Lineage and safety summary",
            summary=_lineage_and_safety_summary(input_record_counts=input_record_counts, filtered=filtered),
            status="informational",
            severity="informational",
            safe_evidence_refs=(),
            suggested_review_type=None,
            lineage_summary={
                "brief_stage": DAILY_BRIEF_STAGE,
                "source_counts": input_record_counts,
                "live_connector_allowed": False,
                "model_call_allowed": False,
                "tool_call_allowed": False,
                "execution_allowed": False,
            },
            created_at=created_marker,
        )
    )

    sorted_sections: list[DailyBriefSectionRecord] = []
    sorted_items: list[DailyBriefItemRecord] = []
    for section_name in SECTION_ORDER:
        section_items = tuple(_sort_items(section_buckets[section_name]))
        sorted_items.extend(section_items)
        section_id = _stable_id("daily_brief_section", brief_id, section_name)
        sorted_sections.append(
            DailyBriefSectionRecord(
                section_id=section_id,
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                section_name=section_name,
                section_title=SECTION_TITLES[section_name],
                item_ids=tuple(item.item_id for item in section_items),
                item_count=len(section_items),
                display_order=SECTION_DISPLAY_ORDER[section_name],
                created_at=created_marker,
            )
        )

    local_render_text = render_daily_brief_text(
        sections=tuple(sorted_sections),
        items=tuple(sorted_items),
    )
    snapshot = DailyBriefSnapshotRecord(
        brief_id=brief_id,
        owner_id=owner_id,
        robot_id=robot_id,
        brief_date=resolved_date.isoformat(),
        timezone=resolved_tz.key,
        window_start=_to_zulu(resolved_window_start),
        window_end=_to_zulu(resolved_window_end),
        source_stage_min=SOURCE_STAGE_MIN,
        source_stage_max=SOURCE_STAGE_MAX,
        brief_stage=DAILY_BRIEF_STAGE,
        brief_mode=DAILY_BRIEF_MODE,
        headline_summary=_headline_summary(section_buckets=section_buckets),
        section_ids=tuple(section.section_id for section in sorted_sections),
        total_item_count=len(sorted_items),
        needs_attention_count=len(section_buckets["needs_attention"]),
        pending_review_count=len(section_buckets["pending_followups"]) + len(section_buckets["pending_memory_reviews"]),
        blocked_or_rejected_count=len(section_buckets["blocked_or_rejected_items"]),
        completed_count=len(section_buckets["completed_today"]) + len(section_buckets["memory_written_today"]),
        proactive_opportunity_count=len(section_buckets["proactive_opportunities"]),
        memory_review_count=len(section_buckets["pending_memory_reviews"]),
        memory_written_count=len(section_buckets["memory_written_today"]),
        local_render_text=local_render_text,
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
            "brief_stage": DAILY_BRIEF_STAGE,
            "source_stage_min": SOURCE_STAGE_MIN,
            "source_stage_max": SOURCE_STAGE_MAX,
            "input_record_counts": input_record_counts,
            "filtered_record_counts": {key: len(value) for key, value in filtered.items()},
        },
        created_at=created_marker,
    )
    return registry.store_snapshot(
        snapshot=snapshot,
        sections=tuple(sorted_sections),
        items=tuple(sorted_items),
    )


def render_daily_brief_text(
    *,
    sections: tuple[DailyBriefSectionRecord, ...],
    items: tuple[DailyBriefItemRecord, ...],
) -> str:
    items_by_section: dict[str, list[DailyBriefItemRecord]] = {section.section_name: [] for section in sections}
    for item in items:
        items_by_section.setdefault(item.section_name, []).append(item)

    lines: list[str] = ["What Did I Miss?"]
    for section in sorted(sections, key=lambda section: section.display_order):
        lines.extend(("", f"{section.section_title}:"))
        section_items = items_by_section.get(section.section_name, [])
        if not section_items:
            lines.append("- none")
            continue
        for item in section_items:
            lines.append(f"- [{item.severity}] {item.title}: {item.summary}")
    return "\n".join(lines)


def get_daily_brief_snapshot(
    *,
    registry: DailyBriefRegistry,
    brief_id: str,
) -> DailyBriefSnapshotRecord | None:
    return registry.get_snapshot(brief_id)


def list_daily_brief_snapshots(
    *,
    registry: DailyBriefRegistry,
) -> tuple[DailyBriefSnapshotRecord, ...]:
    return registry.list_snapshots()


def list_daily_brief_items(
    *,
    registry: DailyBriefRegistry,
    brief_id: str | None = None,
) -> tuple[DailyBriefItemRecord, ...]:
    return registry.list_items(brief_id=brief_id)


def _validate_window(
    *,
    brief_date: str,
    timezone_name: str,
    window_start: str,
    window_end: str,
) -> tuple[date, ZoneInfo, datetime, datetime]:
    try:
        resolved_date = date.fromisoformat(brief_date)
    except ValueError as exc:
        raise ValueError("rejected_invalid_brief_date") from exc
    try:
        resolved_tz = ZoneInfo(timezone_name)
    except Exception as exc:
        raise ValueError("rejected_invalid_timezone") from exc
    start = _parse_datetime(window_start, reason="rejected_invalid_window_start")
    end = _parse_datetime(window_end, reason="rejected_invalid_window_end")
    if start >= end:
        raise ValueError("rejected_invalid_window_range")
    if start.astimezone(resolved_tz).date() > resolved_date or end.astimezone(resolved_tz).date() < resolved_date:
        raise ValueError("rejected_window_date_mismatch")
    return resolved_date, resolved_tz, start, end


def _parse_datetime(value: str, *, reason: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(reason) from exc
    if parsed.tzinfo is None:
        raise ValueError(reason)
    return parsed


def _to_zulu(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _record_created_at(record: object) -> str:
    created_at = getattr(record, "created_at", None)
    if isinstance(created_at, str):
        return created_at
    return "2026-06-20T00:00:00Z"


def _filtered_records(
    *,
    source_records: DailyBriefSourceBundle,
    owner_id: str,
    robot_id: str,
    window_start: datetime,
    window_end: datetime,
) -> dict[str, tuple[object, ...]]:
    filtered: dict[str, tuple[object, ...]] = {}
    for bundle_field in fields(source_records):
        key = bundle_field.name
        value = getattr(source_records, key)
        scoped: list[object] = []
        for record in value:
            if getattr(record, "owner_id", None) != owner_id:
                continue
            if getattr(record, "robot_id", None) != robot_id:
                continue
            if not _in_window(_record_created_at(record), window_start=window_start, window_end=window_end):
                continue
            lineage = getattr(record, "lineage_summary", None)
            if not isinstance(lineage, dict):
                lineage = getattr(record, "lineage_metadata", {})
            if not _valid_lineage(lineage):
                continue
            scoped.append(record)
        filtered[key] = tuple(scoped)
    return filtered


def _input_record_counts(source_records: DailyBriefSourceBundle) -> dict[str, int]:
    return {bundle_field.name: len(getattr(source_records, bundle_field.name)) for bundle_field in fields(source_records)}


def _in_window(created_at: str, *, window_start: datetime, window_end: datetime) -> bool:
    parsed = _parse_datetime(created_at, reason="rejected_invalid_record_created_at")
    return window_start <= parsed <= window_end


def _valid_lineage(lineage: object) -> bool:
    return isinstance(lineage, dict) and bool(lineage)


def _has_result_ack(
    *,
    record: TelegramAsyncResultDeliveryRecord,
    acknowledgements: tuple[TelegramResultAcknowledgementRecord, ...],
) -> bool:
    for acknowledgement in acknowledgements:
        if acknowledgement.delivery_id == record.delivery_id and acknowledgement.status == "recorded":
            return True
    return False


def _is_blocked_delivery(record: TelegramAsyncResultDeliveryRecord) -> bool:
    return record.status in {"blocked", "failed"} or bool(record.rejection_reason)


def _proactive_severity(opportunity_type: str) -> str:
    if opportunity_type in {
        "meeting_brief_missing",
        "invoice_due_soon",
        "customer_issue_needs_attention",
        "lead_followup_due",
        "task_deadline_risk",
    }:
        return "high"
    return "medium"


def _headline_summary(*, section_buckets: dict[str, list[DailyBriefItemRecord]]) -> str:
    pending_results = len(section_buckets["pending_results"])
    pending_followups = len(section_buckets["pending_followups"])
    pending_memory = len(section_buckets["pending_memory_reviews"])
    blocked = len(section_buckets["blocked_or_rejected_items"])
    completed = len(section_buckets["completed_today"]) + len(section_buckets["memory_written_today"])
    proactive = len(section_buckets["proactive_opportunities"]) + len(section_buckets["proactive_execution_candidates"])
    if pending_results + pending_followups + pending_memory + blocked + completed + proactive == 0:
        return NO_UPDATES_SUMMARY
    return (
        f"{pending_results} pending results, {pending_followups} pending follow-ups, "
        f"{pending_memory} pending memory reviews, {blocked} blocked or rejected items, "
        f"{completed} completed items, and {proactive} proactive items were found."
    )


def _lineage_and_safety_summary(
    *,
    input_record_counts: dict[str, int],
    filtered: dict[str, tuple[object, ...]],
) -> str:
    return (
        f"Read-only brief built from {sum(input_record_counts.values())} provided records and "
        f"{sum(len(records) for records in filtered.values())} in-scope records. "
        "No live connectors, models, tools, delivery, execution, memory writes, or worker dispatch were allowed."
    )


def _derive_attention_items(
    *,
    brief_id: str,
    owner_id: str,
    robot_id: str,
    candidate_items: tuple[DailyBriefItemRecord, ...],
) -> list[DailyBriefItemRecord]:
    ranked = sorted(candidate_items, key=_attention_sort_key)
    attention: list[DailyBriefItemRecord] = []
    seen_sources: set[tuple[str, str]] = set()
    for item in ranked:
        source_key = (item.source_stage, item.source_record_id)
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        attention.append(
            _make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=f"attention:{item.source_record_id}",
                source_record_type="DailyBriefAttentionItem",
                source_stage=item.source_stage,
                section_name="needs_attention",
                title=item.title,
                summary=item.summary,
                status=item.status,
                severity=item.severity,
                safe_evidence_refs=item.safe_evidence_refs,
                suggested_review_type=item.suggested_review_type,
                lineage_summary=item.lineage_summary,
                created_at=item.created_at,
            )
        )
        if len(attention) >= 5:
            break
    return attention


def _attention_sort_key(item: DailyBriefItemRecord) -> tuple[int, int, int, str]:
    priority = 7
    if item.section_name == "blocked_or_rejected_items":
        priority = 1
    elif item.section_name == "pending_memory_reviews":
        priority = 6
    elif item.section_name == "pending_results":
        priority = 3
    elif item.section_name == "pending_followups":
        priority = 2
    elif item.section_name == "proactive_execution_candidates" and item.status == "failed":
        priority = 4
    elif item.section_name == "proactive_opportunities":
        priority = 5
    elif item.section_name == "completed_today":
        priority = 7
    return (priority, SEVERITY_ORDER[item.severity], STAGE_ORDER.get(item.source_stage, 999), item.item_id)


def _build_suggested_review_items(
    *,
    brief_id: str,
    owner_id: str,
    robot_id: str,
    section_buckets: dict[str, list[DailyBriefItemRecord]],
    created_at: str,
) -> list[DailyBriefItemRecord]:
    counts = {
        "review_blocked_items": len(section_buckets["blocked_or_rejected_items"]),
        "review_pending_results": len(section_buckets["pending_results"]),
        "review_pending_followups": len(section_buckets["pending_followups"]),
        "review_pending_memory": len(section_buckets["pending_memory_reviews"]),
        "review_proactive_candidates": len(section_buckets["proactive_opportunities"]) + len(section_buckets["proactive_execution_candidates"]),
        "review_context_sources": len(section_buckets["completed_today"]),
    }
    items: list[DailyBriefItemRecord] = []
    for review_type in BLOCKED_REVIEW_TYPES:
        count = counts[review_type]
        if count == 0:
            continue
        items.append(
            _make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id=f"suggested-review:{review_type}",
                source_record_type="DailyBriefSuggestedReview",
                source_stage=DAILY_BRIEF_STAGE,
                section_name="suggested_next_reviews",
                title=review_type.replace("_", " "),
                summary=_safe_summary(f"{count} item(s) are available for {review_type.replace('_', ' ')}."),
                status="informational",
                severity="informational",
                safe_evidence_refs=(),
                suggested_review_type=review_type,
                lineage_summary={"brief_stage": DAILY_BRIEF_STAGE, "review_type": review_type, "count": count},
                created_at=created_at,
            )
        )
    if not items:
        items.append(
            _make_item(
                brief_id=brief_id,
                owner_id=owner_id,
                robot_id=robot_id,
                source_record_id="suggested-review:none",
                source_record_type="DailyBriefSuggestedReview",
                source_stage=DAILY_BRIEF_STAGE,
                section_name="suggested_next_reviews",
                title="no_updates",
                summary=NO_UPDATES_SUMMARY,
                status="informational",
                severity="informational",
                safe_evidence_refs=(),
                suggested_review_type=None,
                lineage_summary={"brief_stage": DAILY_BRIEF_STAGE},
                created_at=created_at,
            )
        )
    return items


def _make_item(
    *,
    brief_id: str,
    owner_id: str,
    robot_id: str,
    source_record_id: str,
    source_record_type: str,
    source_stage: str,
    section_name: str,
    title: str,
    summary: str,
    status: str,
    severity: str,
    safe_evidence_refs: tuple[dict[str, object], ...],
    suggested_review_type: str | None,
    lineage_summary: dict[str, object],
    created_at: str,
) -> DailyBriefItemRecord:
    item_id = _stable_id("daily_brief_item", brief_id, section_name, source_stage, source_record_id, source_record_type)
    return DailyBriefItemRecord(
        item_id=item_id,
        brief_id=brief_id,
        owner_id=owner_id,
        robot_id=robot_id,
        source_record_id=source_record_id,
        source_record_type=source_record_type,
        source_stage=source_stage,
        section_name=section_name,
        title=title,
        summary=summary,
        status=status,
        severity=severity,
        safe_evidence_refs=tuple(_safe_lineage_dict(ref) for ref in safe_evidence_refs),
        suggested_review_type=suggested_review_type,
        action_allowed=False,
        telegram_delivery_allowed=False,
        callback_binding_allowed=False,
        delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        sensitive_data_excluded=True,
        lineage_summary=_safe_lineage_dict(lineage_summary),
        created_at=created_at,
    )


def _add_item(
    *,
    bucket: list[DailyBriefItemRecord],
    seen_source_keys: set[tuple[str, str, str]],
    item: DailyBriefItemRecord,
) -> None:
    dedupe_key = (item.section_name, item.source_stage, item.source_record_id)
    if dedupe_key in seen_source_keys:
        return
    seen_source_keys.add(dedupe_key)
    bucket.append(item)


def _sort_items(items: list[DailyBriefItemRecord]) -> list[DailyBriefItemRecord]:
    return sorted(
        items,
        key=lambda item: (
            SEVERITY_ORDER[item.severity],
            STAGE_ORDER.get(item.source_stage, 999),
            item.created_at,
            item.title,
            item.source_record_id,
        ),
    )


def _safe_summary(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return "No additional safe summary was available."
    lowered = text.lower()
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        return "Sensitive details were excluded from this brief item."
    return text


def _safe_lineage_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
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
            lowered = raw_value.lower()
            if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
                continue
            safe[key] = raw_value
            continue
        if isinstance(raw_value, (int, float, bool)) or raw_value is None:
            safe[key] = raw_value
    return safe


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(parts)))
