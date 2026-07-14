from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import (
    CREDENTIAL_KEYWORDS,
    SENSITIVE_KEYWORDS,
    ContextScanCandidateSourceRecord,
    ContextScanCandidateSourceRegistry,
    create_context_scan_candidate_source,
    create_local_context_scan_authorization,
)
from app.cost_governor import BudgetPolicy, CostPreflightResult, CostTraceRecord, ModelRouteDecision, TaskCostRequest, TokenUsageEstimate
from app.daily_brief_what_did_i_miss import (
    DailyBriefRegistry,
    DailyBriefSourceBundle,
    DailyBriefSnapshotRecord,
    create_daily_brief_snapshot,
    list_daily_brief_items,
)
from app.followup_delegation_authority import (
    FollowUpDelegationAuthorizationEvidence,
    FollowUpDelegationRegistry,
    FollowUpDelegationRequestRecord,
    create_followup_delegation_from_selection,
)
from app.followup_draft_planner import (
    FollowUpDraftOption,
    FollowUpDraftPlanRecord,
    FollowUpDraftPlanRegistry,
)
from app.followup_intent_review import FollowUpIntentReviewQueue, FollowUpIntentReviewRecord
from app.proactive_delegation_adapter import (
    PROACTIVE_DELEGATION_ADAPTER_STAGE,
    ProactiveDelegationAdapterRecord,
    ProactiveDelegationAdapterRegistry,
    ProactiveDelegationAuthorizationRecord,
    authorize_proactive_delegation_registration_local,
)
from app.proactive_execution_skeleton import (
    ProactiveExecutionAttemptRecord,
    ProactiveExecutionFixture,
    ProactiveExecutionRegistry,
    execute_proactive_delegation_skeleton,
)
from app.proactive_opportunity_detection import (
    ProactiveOpportunityCandidateRecord,
    ProactiveOpportunityRegistry,
    detect_proactive_opportunity_from_context_source,
)
from app.proactive_suggestion_adapter import (
    ProactiveSuggestionAdapterRegistry,
    ProactiveSuggestionFollowupAdapterRecord,
    adapt_proactive_suggestion_to_followup_intent,
    authorize_proactive_suggestion_adapter_local,
)
from app.proactive_telegram_suggestion import (
    ProactiveTelegramSuggestionDeliveryRecord,
    ProactiveTelegramSuggestionRegistry,
    ProactiveTelegramSuggestionSurfaceRecord,
    deliver_proactive_telegram_suggestion_local,
    render_proactive_telegram_suggestion,
)
from app.skill_pack_activation_surface import (
    SkillPackActivationRegistry,
    SkillPackActivationSurfaceRecord,
    SkillPackSourceBundle,
    create_skill_pack_activation_surface,
    list_skill_pack_classifications,
)
from app.telegram_async_result_delivery import TelegramAsyncResultTransport, TelegramOwnerBinding
from app.telegram_followup_choice_selection import (
    TelegramFollowUpChoiceSelectionRecord,
    TelegramFollowUpChoiceSelectionRegistry,
)
from app.telegram_followup_choice_surface import (
    TelegramFollowUpChoiceSurfaceRecord,
    TelegramFollowUpChoiceSurfaceRegistry,
)
from app.async_delegation_authority import serialize_async_delegation_authority_state


FIRST_DEMO_MEETING_BRIEF_STAGE = "126P"
FIRST_DEMO_MEETING_BRIEF_NAME = "meeting_brief_from_context"
FIRST_DEMO_MEETING_BRIEF_MODE = "deterministic_local_demo"
FIRST_DEMO_ARTIFACT_TYPE = "local_meeting_brief_demo"
EXECUTION_TASK_CLASS = "FOLLOWUP_HUMAN_REVIEW_CHECKLIST"
EXECUTION_OPTION_KIND = "human_review_checklist"
DEFAULT_CREATED_AT = "2026-06-20T00:00:00Z"
DEFAULT_WINDOW_START = "2026-06-20T00:00:00Z"
DEFAULT_WINDOW_END = "2026-06-20T23:59:59Z"
DEFAULT_BRIEF_DATE = "2026-06-20"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_MEETING_TIMESTAMP = "2026-06-21T09:00:00Z"
ALLOWED_DEMO_SOURCE_TYPES = frozenset({"mock_calendar_event", "mock_meeting_note"})
SAFE_CHECKLIST = (
    "Review the meeting objective and desired outcome.",
    "Confirm the latest safe local context for Victor / ASISINT follow-up.",
    "List open questions that must be answered during the meeting.",
    "Check which materials should be reviewed before the meeting starts.",
    "Keep the result local and do not trigger any live action from this demo.",
)
SAFE_OPEN_QUESTIONS = (
    "What changed since the last Victor / ASISINT follow-up?",
    "What decision or update is the owner trying to get from the meeting?",
    "What local notes or documents should be reviewed before the call?",
)
SAFE_SUGGESTED_MATERIALS = (
    "Prior local meeting note fixture, if present.",
    "Recent local summary fixture tied to the account or thread.",
    "Local list of pending questions or promised follow-ups.",
)
SAFE_BOUNDARIES = (
    "No live connectors used.",
    "No external messages sent.",
    "No model/tool calls used.",
    "No external systems written.",
    "No Memory Center mutation performed by 126P.",
)


@dataclass(frozen=True, slots=True)
class MeetingBriefDemoFixture:
    fixture_id: str
    source_type: str
    source_status: str
    scan_scope: str
    meeting_title: str
    meeting_timestamp: str
    safe_summary: str
    source_hint: str
    provenance_notes: str
    retention_policy: str
    brief_date: str = DEFAULT_BRIEF_DATE
    timezone: str = DEFAULT_TIMEZONE
    window_start: str = DEFAULT_WINDOW_START
    window_end: str = DEFAULT_WINDOW_END
    source_payload: object | None = None

    def __post_init__(self) -> None:
        if self.source_type not in ALLOWED_DEMO_SOURCE_TYPES:
            raise ValueError("rejected_live_connector_source_type")
        if not self.meeting_title:
            raise ValueError("rejected_missing_meeting_title")
        _reject_sensitive_text(self.meeting_title)
        _reject_sensitive_text(self.safe_summary)
        _reject_sensitive_text(self.source_hint)
        if self.source_payload is not None:
            raise ValueError("rejected_raw_payload_not_allowed")


@dataclass(frozen=True, slots=True)
class FirstDemoMeetingBriefArtifactRecord:
    demo_artifact_id: str
    owner_id: str
    robot_id: str
    demo_flow_id: str
    artifact_type: str
    title: str
    local_render_text: str
    demo_summary: str
    meeting_context_summary: str
    preparation_checklist: tuple[str, ...]
    open_questions: tuple[str, ...]
    suggested_materials: tuple[str, ...]
    safety_boundaries: tuple[str, ...]
    skill_pack_summary: str
    daily_brief_summary: str
    lineage_summary: str
    live_connector_used: bool
    live_telegram_used: bool
    model_called: bool
    tool_called: bool
    worker_dispatched: bool
    external_system_written: bool
    memory_mutated_by_126p: bool
    created_at: str

    def __post_init__(self) -> None:
        if self.artifact_type != FIRST_DEMO_ARTIFACT_TYPE:
            raise ValueError("rejected_invalid_artifact_type")
        if any(
            (
                self.live_connector_used,
                self.live_telegram_used,
                self.model_called,
                self.tool_called,
                self.worker_dispatched,
                self.external_system_written,
                self.memory_mutated_by_126p,
            )
        ):
            raise ValueError("rejected_live_dependency")


@dataclass(frozen=True, slots=True)
class FirstDemoMeetingBriefFlowRecord:
    demo_flow_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    demo_stage: str
    demo_name: str
    demo_mode: str
    context_source_id: str
    opportunity_id: str
    suggestion_surface_id: str
    suggestion_delivery_record_id: str
    proactive_adapter_id: str
    followup_intent_review_record_id: str
    followup_plan_id: str
    followup_choice_surface_id: str
    followup_selection_id: str
    proactive_delegation_adapter_id: str
    delegation_packet_id: str | None
    delegation_handle_id: str | None
    proactive_execution_attempt_id: str
    proactive_execution_event_candidate_id: str | None
    daily_brief_id: str
    skill_pack_surface_id: str
    demo_artifact_id: str
    demo_status: str
    live_connector_allowed: bool
    live_telegram_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    memory_write_allowed_by_126p: bool
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.demo_stage != FIRST_DEMO_MEETING_BRIEF_STAGE:
            raise ValueError("rejected_invalid_demo_stage")
        if self.demo_name != FIRST_DEMO_MEETING_BRIEF_NAME:
            raise ValueError("rejected_invalid_demo_name")
        if self.demo_mode != FIRST_DEMO_MEETING_BRIEF_MODE:
            raise ValueError("rejected_invalid_demo_mode")
        if self.demo_status not in {
            "completed_local_demo",
            "partial_local_demo",
            "rejected_invalid_lineage",
            "rejected_live_dependency",
            "rejected_sensitive_data",
        }:
            raise ValueError("rejected_invalid_demo_status")
        if any(
            (
                self.live_connector_allowed,
                self.live_telegram_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.memory_write_allowed_by_126p,
                self.billing_allowed,
                self.entitlement_enforcement_allowed,
            )
        ):
            raise ValueError("rejected_live_dependency")


@dataclass(slots=True)
class MeetingBriefDemoFlowRegistry:
    flows_by_id: dict[str, FirstDemoMeetingBriefFlowRecord] = field(default_factory=dict)
    flow_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    artifacts_by_id: dict[str, FirstDemoMeetingBriefArtifactRecord] = field(default_factory=dict)

    def store_flow(self, flow: FirstDemoMeetingBriefFlowRecord) -> FirstDemoMeetingBriefFlowRecord:
        self.flows_by_id[flow.demo_flow_id] = flow
        self.flow_ids_by_dedupe_key[flow.dedupe_key] = flow.demo_flow_id
        return flow

    def get_flow(self, demo_flow_id: str) -> FirstDemoMeetingBriefFlowRecord | None:
        return self.flows_by_id.get(demo_flow_id)

    def get_flow_by_dedupe_key(self, dedupe_key: str) -> FirstDemoMeetingBriefFlowRecord | None:
        flow_id = self.flow_ids_by_dedupe_key.get(dedupe_key)
        if flow_id is None:
            return None
        return self.flows_by_id.get(flow_id)

    def list_flows(self, *, owner_id: str | None = None, robot_id: str | None = None) -> tuple[FirstDemoMeetingBriefFlowRecord, ...]:
        records = tuple(self.flows_by_id[key] for key in sorted(self.flows_by_id))
        if owner_id is not None:
            records = tuple(record for record in records if record.owner_id == owner_id)
        if robot_id is not None:
            records = tuple(record for record in records if record.robot_id == robot_id)
        return records

    def store_artifact(self, artifact: FirstDemoMeetingBriefArtifactRecord) -> FirstDemoMeetingBriefArtifactRecord:
        self.artifacts_by_id[artifact.demo_artifact_id] = artifact
        return artifact

    def get_artifact(self, demo_artifact_id: str) -> FirstDemoMeetingBriefArtifactRecord | None:
        return self.artifacts_by_id.get(demo_artifact_id)


@dataclass(slots=True)
class MeetingBriefDemoDependencyBundle:
    context_registry: ContextScanCandidateSourceRegistry = field(default_factory=ContextScanCandidateSourceRegistry)
    opportunity_registry: ProactiveOpportunityRegistry = field(default_factory=ProactiveOpportunityRegistry)
    suggestion_registry: ProactiveTelegramSuggestionRegistry = field(default_factory=ProactiveTelegramSuggestionRegistry)
    suggestion_adapter_registry: ProactiveSuggestionAdapterRegistry = field(default_factory=ProactiveSuggestionAdapterRegistry)
    followup_queue: FollowUpIntentReviewQueue = field(default_factory=FollowUpIntentReviewQueue)
    draft_plan_registry: FollowUpDraftPlanRegistry = field(default_factory=FollowUpDraftPlanRegistry)
    choice_surface_registry: TelegramFollowUpChoiceSurfaceRegistry = field(default_factory=TelegramFollowUpChoiceSurfaceRegistry)
    choice_selection_registry: TelegramFollowUpChoiceSelectionRegistry = field(default_factory=TelegramFollowUpChoiceSelectionRegistry)
    followup_delegation_registry: FollowUpDelegationRegistry = field(default_factory=FollowUpDelegationRegistry)
    proactive_delegation_registry: ProactiveDelegationAdapterRegistry = field(default_factory=ProactiveDelegationAdapterRegistry)
    execution_registry: ProactiveExecutionRegistry = field(default_factory=ProactiveExecutionRegistry)
    daily_brief_registry: DailyBriefRegistry = field(default_factory=DailyBriefRegistry)
    skill_pack_registry: SkillPackActivationRegistry = field(default_factory=SkillPackActivationRegistry)
    demo_registry: MeetingBriefDemoFlowRegistry = field(default_factory=MeetingBriefDemoFlowRegistry)


class _LocalOnlyTelegramTransport(TelegramAsyncResultTransport):
    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict[str, object]:
        return {
            "transport": "deterministic_local_demo",
            "chat_id": chat_id,
            "button_count": len(buttons),
            "text_fingerprint": f"{len(text)}:{len(buttons)}",
        }


def build_default_meeting_brief_demo_fixture() -> MeetingBriefDemoFixture:
    return MeetingBriefDemoFixture(
        fixture_id="fixture-126p-meeting-brief-demo",
        source_type="mock_calendar_event",
        source_status="authorized_local_fixture",
        scan_scope="summary_fixture",
        meeting_title="Victor / ASISINT follow-up",
        meeting_timestamp=DEFAULT_MEETING_TIMESTAMP,
        safe_summary="Upcoming meeting has a missing brief based on authorized local context.",
        source_hint="missing brief and empty briefing note",
        provenance_notes="deterministic_local_demo_fixture",
        retention_policy="keep_until_fixture_rotation",
    )


def run_local_meeting_brief_demo_flow(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    dependencies: MeetingBriefDemoDependencyBundle | None = None,
    fixture: MeetingBriefDemoFixture | None = None,
    created_at: str = DEFAULT_CREATED_AT,
) -> FirstDemoMeetingBriefFlowRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not chat_id:
        raise ValueError("rejected_missing_chat_id")
    bundle = MeetingBriefDemoDependencyBundle() if dependencies is None else dependencies
    scenario = build_default_meeting_brief_demo_fixture() if fixture is None else fixture
    _reject_sensitive_text(chat_id)

    dedupe_key = _stable_id(
        "meeting_brief_demo_flow",
        owner_id,
        robot_id,
        chat_id,
        scenario.fixture_id,
        scenario.source_type,
        scenario.meeting_timestamp,
    )
    existing = bundle.demo_registry.get_flow_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    context_authorization = create_local_context_scan_authorization(
        owner_id=owner_id,
        robot_id=robot_id,
        allowed_source_types=tuple(sorted(ALLOWED_DEMO_SOURCE_TYPES)),
        allowed_scan_scopes=("metadata_only", "summary_fixture", "selected_fields_fixture", "local_test_snapshot"),
        registry=bundle.context_registry,
        created_at=created_at,
    )
    context_source = create_context_scan_candidate_source(
        owner_id=owner_id,
        robot_id=robot_id,
        authorization_id=context_authorization.authorization_id,
        source_type=scenario.source_type,
        source_status=scenario.source_status,
        scan_scope=scenario.scan_scope,
        fixture_id=scenario.fixture_id,
        source_title=scenario.meeting_title,
        source_summary=scenario.safe_summary,
        source_timestamp=scenario.meeting_timestamp,
        source_hint=scenario.source_hint,
        retention_policy=scenario.retention_policy,
        provenance_notes=scenario.provenance_notes,
        source_payload=scenario.source_payload,
        registry=bundle.context_registry,
        created_at=created_at,
    )
    opportunity = detect_proactive_opportunity_from_context_source(
        source_record=context_source,
        source_registry=bundle.context_registry,
        registry=bundle.opportunity_registry,
        owner_id=owner_id,
        robot_id=robot_id,
        created_at=created_at,
    )
    suggestion_surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=bundle.context_registry,
        registry=bundle.suggestion_registry,
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        created_at=created_at,
    )
    suggestion_delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=suggestion_surface,
        owner_binding=TelegramOwnerBinding(owner_id=owner_id, robot_id=robot_id, telegram_chat_id=chat_id),
        transport=_LocalOnlyTelegramTransport(),
        registry=bundle.suggestion_registry,
        created_at=created_at,
    )
    suggestion_authorization = authorize_proactive_suggestion_adapter_local(
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        delivery_record_id=suggestion_delivery.delivery_record_id,
        suggestion_surface_id=suggestion_surface.suggestion_surface_id,
        opportunity_id=opportunity.opportunity_id,
        registry=bundle.suggestion_adapter_registry,
        created_at=created_at,
    )
    proactive_adapter = adapt_proactive_suggestion_to_followup_intent(
        delivery_record=suggestion_delivery,
        suggestion_registry=bundle.suggestion_registry,
        opportunity_record=opportunity,
        source_registry=bundle.context_registry,
        queue=bundle.followup_queue,
        adapter_registry=bundle.suggestion_adapter_registry,
        authorization_record=suggestion_authorization,
        owner_id=owner_id,
        robot_id=robot_id,
        created_at=created_at,
    )
    followup_intent = bundle.followup_queue.get_record(proactive_adapter.followup_intent_review_record_id)
    if followup_intent is None:
        raise ValueError("rejected_missing_121p_adapter_lineage")

    followup_plan = _assemble_followup_draft_plan(
        proactive_adapter=proactive_adapter,
        followup_intent=followup_intent,
        registry=bundle.draft_plan_registry,
    )
    choice_surface = _assemble_followup_choice_surface(
        proactive_adapter=proactive_adapter,
        followup_plan=followup_plan,
        registry=bundle.choice_surface_registry,
    )
    selection = _assemble_followup_choice_selection(
        choice_surface=choice_surface,
        registry=bundle.choice_selection_registry,
    )

    task_request = _build_demo_task_cost_request(owner_id=owner_id, robot_id=robot_id, created_at=created_at)
    cost_preflight = _build_demo_cost_preflight(request=task_request)
    budget_policy = _build_demo_budget_policy(owner_id=owner_id, robot_id=robot_id)
    followup_authorization = FollowUpDelegationAuthorizationEvidence(
        authorization_id=_stable_id("meeting_brief_demo_followup_authorization", selection.selection_id, task_request.request_id),
        authorization_kind="followup_delegation_authorization",
        selection_id=selection.selection_id,
        owner_id=owner_id,
        robot_id=robot_id,
        selected_option_id=selection.selected_option_id,
        selected_option_kind=selection.selected_option_kind,
        cost_preflight_request_id=task_request.request_id,
        approval_evidence_id=None,
        explicit_user_authorized=True,
    )
    followup_delegation = create_followup_delegation_from_selection(
        selection_record=selection,
        authorization_evidence=followup_authorization,
        cost_preflight_evidence=cost_preflight,
        task_cost_request=task_request,
        budget_policy=budget_policy,
        approval_evidence=None,
        followup_registry=bundle.followup_delegation_registry,
        occurred_at=created_at,
    )
    proactive_delegation_authorization = authorize_proactive_delegation_registration_local(
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        proactive_adapter_id=proactive_adapter.adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=task_request.request_id,
        registry=bundle.proactive_delegation_registry,
        created_at=created_at,
    )
    proactive_delegation = _assemble_meeting_brief_proactive_delegation_record(
        proactive_adapter=proactive_adapter,
        followup_plan=followup_plan,
        choice_surface=choice_surface,
        selection=selection,
        followup_delegation=followup_delegation,
        authorization=proactive_delegation_authorization,
        followup_registry=bundle.followup_delegation_registry,
        registry=bundle.proactive_delegation_registry,
        created_at=created_at,
    )
    execution_attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=proactive_delegation,
        followup_registry=bundle.followup_delegation_registry,
        fixture=ProactiveExecutionFixture(
            fixture_id="fixture-126p-deterministic-local-execution",
            owner_id=owner_id,
            robot_id=robot_id,
            allowed_task_classes=(EXECUTION_TASK_CLASS,),
            deterministic_payloads={
                EXECUTION_TASK_CLASS: "Prepared deterministic local meeting brief checklist for Victor / ASISINT follow-up."
            },
        ),
        execution_registry=bundle.execution_registry,
        created_at=created_at,
    )
    daily_brief = create_daily_brief_snapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        brief_date=scenario.brief_date,
        timezone=scenario.timezone,
        window_start=scenario.window_start,
        window_end=scenario.window_end,
        source_records=DailyBriefSourceBundle(
            context_sources_118p=(context_source,),
            proactive_opportunities_119p=(opportunity,),
            proactive_deliveries_120p=(suggestion_delivery,),
            proactive_adapters_121p=(proactive_adapter,),
            proactive_delegations_122p=(proactive_delegation,),
            proactive_executions_123p=(execution_attempt,),
        ),
        registry=bundle.daily_brief_registry,
        created_at=created_at,
    )
    skill_pack_surface = create_skill_pack_activation_surface(
        owner_id=owner_id,
        robot_id=robot_id,
        source_records=SkillPackSourceBundle(
            daily_brief_snapshots_124p=(daily_brief,),
            daily_brief_items_124p=list_daily_brief_items(registry=bundle.daily_brief_registry, brief_id=daily_brief.brief_id),
            proactive_executions_123p=(execution_attempt,),
            proactive_delegations_122p=(proactive_delegation,),
            proactive_adapters_121p=(proactive_adapter,),
            proactive_deliveries_120p=(suggestion_delivery,),
            proactive_opportunities_119p=(opportunity,),
            context_sources_118p=(context_source,),
        ),
        registry=bundle.skill_pack_registry,
        created_at=created_at,
    )
    return assemble_meeting_brief_demo_flow(
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        context_source_record=context_source,
        opportunity_record=opportunity,
        suggestion_surface_record=suggestion_surface,
        suggestion_delivery_record=suggestion_delivery,
        proactive_adapter_record=proactive_adapter,
        followup_intent_review_record=followup_intent,
        followup_plan_record=followup_plan,
        followup_choice_surface_record=choice_surface,
        followup_selection_record=selection,
        proactive_delegation_authorization_record=proactive_delegation_authorization,
        followup_delegation_record=followup_delegation,
        proactive_delegation_adapter_record=proactive_delegation,
        proactive_execution_attempt_record=execution_attempt,
        daily_brief_snapshot_record=daily_brief,
        skill_pack_surface_record=skill_pack_surface,
        registry=bundle.demo_registry,
        skill_pack_registry=bundle.skill_pack_registry,
        created_at=created_at,
    )


def assemble_meeting_brief_demo_flow(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    context_source_record: object,
    opportunity_record: object,
    suggestion_surface_record: object,
    suggestion_delivery_record: object,
    proactive_adapter_record: object,
    followup_intent_review_record: object,
    followup_plan_record: object,
    followup_choice_surface_record: object,
    followup_selection_record: object,
    proactive_delegation_authorization_record: object,
    followup_delegation_record: object,
    proactive_delegation_adapter_record: object,
    proactive_execution_attempt_record: object,
    daily_brief_snapshot_record: object,
    skill_pack_surface_record: object,
    registry: MeetingBriefDemoFlowRegistry,
    skill_pack_registry: SkillPackActivationRegistry,
    created_at: str = DEFAULT_CREATED_AT,
) -> FirstDemoMeetingBriefFlowRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not chat_id:
        raise ValueError("rejected_missing_chat_id")
    context_source = _require_record(context_source_record, ContextScanCandidateSourceRecord, "rejected_missing_118p_context_source_lineage")
    opportunity = _require_record(opportunity_record, ProactiveOpportunityCandidateRecord, "rejected_missing_119p_opportunity_lineage")
    suggestion_surface = _require_record(suggestion_surface_record, ProactiveTelegramSuggestionSurfaceRecord, "rejected_missing_120p_suggestion_lineage")
    suggestion_delivery = _require_record(suggestion_delivery_record, ProactiveTelegramSuggestionDeliveryRecord, "rejected_missing_120p_suggestion_lineage")
    proactive_adapter = _require_record(proactive_adapter_record, ProactiveSuggestionFollowupAdapterRecord, "rejected_missing_121p_adapter_lineage")
    followup_intent = _require_record(followup_intent_review_record, FollowUpIntentReviewRecord, "rejected_missing_121p_adapter_lineage")
    followup_plan = _require_record(followup_plan_record, FollowUpDraftPlanRecord, "rejected_missing_followup_plan_lineage")
    choice_surface = _require_record(followup_choice_surface_record, TelegramFollowUpChoiceSurfaceRecord, "rejected_missing_followup_choice_surface_lineage")
    selection = _require_record(followup_selection_record, TelegramFollowUpChoiceSelectionRecord, "rejected_missing_followup_selection_lineage")
    proactive_delegation_authorization = _require_record(
        proactive_delegation_authorization_record,
        ProactiveDelegationAuthorizationRecord,
        "rejected_missing_122p_delegation_lineage",
    )
    followup_delegation = _require_record(followup_delegation_record, FollowUpDelegationRequestRecord, "rejected_missing_followup_delegation_lineage")
    proactive_delegation = _require_record(
        proactive_delegation_adapter_record,
        ProactiveDelegationAdapterRecord,
        "rejected_missing_122p_delegation_lineage",
    )
    execution_attempt = _require_record(
        proactive_execution_attempt_record,
        ProactiveExecutionAttemptRecord,
        "rejected_missing_123p_execution_lineage",
    )
    daily_brief = _require_record(daily_brief_snapshot_record, DailyBriefSnapshotRecord, "rejected_missing_124p_daily_brief_lineage")
    skill_pack_surface = _require_record(
        skill_pack_surface_record,
        SkillPackActivationSurfaceRecord,
        "rejected_missing_125p_skill_pack_lineage",
    )

    for record in (
        context_source,
        opportunity,
        suggestion_surface,
        suggestion_delivery,
        proactive_adapter,
        followup_intent,
        followup_plan,
        choice_surface,
        selection,
        proactive_delegation_authorization,
        followup_delegation,
        proactive_delegation,
        execution_attempt,
        daily_brief,
        skill_pack_surface,
    ):
        _validate_identity(record=record, owner_id=owner_id, robot_id=robot_id)
        _reject_live_flags(record)

    if suggestion_surface.chat_id != chat_id or suggestion_delivery.chat_id != chat_id:
        raise ValueError("rejected_chat_mismatch")
    if proactive_adapter.chat_id != chat_id or proactive_delegation.chat_id != chat_id or execution_attempt.chat_id != chat_id:
        raise ValueError("rejected_chat_mismatch")
    if opportunity.candidate_source_id != context_source.candidate_source_id:
        raise ValueError("rejected_missing_118p_context_source_lineage")
    if suggestion_surface.opportunity_id != opportunity.opportunity_id:
        raise ValueError("rejected_missing_119p_opportunity_lineage")
    if suggestion_delivery.suggestion_surface_id != suggestion_surface.suggestion_surface_id:
        raise ValueError("rejected_missing_120p_suggestion_lineage")
    if proactive_adapter.followup_intent_review_record_id != followup_intent.followup_intent_id:
        raise ValueError("rejected_missing_121p_adapter_lineage")
    if proactive_delegation.followup_plan_id != followup_plan.draft_plan_id:
        raise ValueError("rejected_missing_followup_plan_lineage")
    if proactive_delegation.followup_choice_surface_id != choice_surface.choice_surface_id:
        raise ValueError("rejected_missing_followup_choice_surface_lineage")
    if proactive_delegation.followup_selection_id != selection.selection_id:
        raise ValueError("rejected_missing_followup_selection_lineage")
    if proactive_delegation.explicit_owner_delegation_authorization_id != proactive_delegation_authorization.authorization_id:
        raise ValueError("rejected_missing_122p_delegation_lineage")
    if proactive_delegation.delegation_packet_id != followup_delegation.async_packet_id:
        raise ValueError("rejected_missing_followup_delegation_lineage")
    if execution_attempt.proactive_delegation_adapter_id != proactive_delegation.proactive_delegation_adapter_id:
        raise ValueError("rejected_missing_123p_execution_lineage")
    if daily_brief.brief_stage != "124P":
        raise ValueError("rejected_missing_124p_daily_brief_lineage")
    if skill_pack_surface.surface_stage != "125P":
        raise ValueError("rejected_missing_125p_skill_pack_lineage")
    if proactive_adapter.normalized_intent_kind != "prepare_meeting_brief":
        raise ValueError("rejected_invalid_demo_intent_lineage")
    if proactive_delegation.normalized_intent_kind != "prepare_meeting_brief":
        raise ValueError("rejected_invalid_demo_intent_lineage")
    if proactive_delegation.selected_option_id != selection.selected_option_id:
        raise ValueError("rejected_missing_followup_selection_lineage")
    if proactive_delegation.mapped_task_class != EXECUTION_TASK_CLASS:
        raise ValueError("rejected_unsupported_task_class")

    demo_dedupe_key = _stable_id(
        "meeting_brief_demo_flow",
        owner_id,
        robot_id,
        chat_id,
        context_source.candidate_source_id,
        opportunity.opportunity_id,
        proactive_delegation.proactive_delegation_adapter_id,
        execution_attempt.proactive_execution_attempt_id,
    )
    existing = registry.get_flow_by_dedupe_key(demo_dedupe_key)
    if existing is not None:
        return existing

    artifact = render_meeting_brief_demo_artifact(
        owner_id=owner_id,
        robot_id=robot_id,
        demo_flow_id=_stable_id("meeting_brief_demo_flow_id", demo_dedupe_key),
        context_source_record=context_source,
        opportunity_record=opportunity,
        suggestion_surface_record=suggestion_surface,
        suggestion_delivery_record=suggestion_delivery,
        proactive_adapter_record=proactive_adapter,
        followup_plan_record=followup_plan,
        followup_selection_record=selection,
        followup_delegation_record=followup_delegation,
        proactive_delegation_adapter_record=proactive_delegation,
        proactive_execution_attempt_record=execution_attempt,
        daily_brief_snapshot_record=daily_brief,
        skill_pack_surface_record=skill_pack_surface,
        skill_pack_registry=skill_pack_registry,
        created_at=created_at,
    )
    registry.store_artifact(artifact)

    event_candidate_id = execution_attempt.completion_event_candidate_id or execution_attempt.failure_event_candidate_id
    flow = FirstDemoMeetingBriefFlowRecord(
        demo_flow_id=artifact.demo_flow_id,
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        demo_stage=FIRST_DEMO_MEETING_BRIEF_STAGE,
        demo_name=FIRST_DEMO_MEETING_BRIEF_NAME,
        demo_mode=FIRST_DEMO_MEETING_BRIEF_MODE,
        context_source_id=context_source.candidate_source_id,
        opportunity_id=opportunity.opportunity_id,
        suggestion_surface_id=suggestion_surface.suggestion_surface_id,
        suggestion_delivery_record_id=suggestion_delivery.delivery_record_id,
        proactive_adapter_id=proactive_adapter.adapter_id,
        followup_intent_review_record_id=followup_intent.followup_intent_id,
        followup_plan_id=followup_plan.draft_plan_id,
        followup_choice_surface_id=choice_surface.choice_surface_id,
        followup_selection_id=selection.selection_id,
        proactive_delegation_adapter_id=proactive_delegation.proactive_delegation_adapter_id,
        delegation_packet_id=proactive_delegation.delegation_packet_id,
        delegation_handle_id=proactive_delegation.delegation_handle_id,
        proactive_execution_attempt_id=execution_attempt.proactive_execution_attempt_id,
        proactive_execution_event_candidate_id=event_candidate_id,
        daily_brief_id=daily_brief.brief_id,
        skill_pack_surface_id=skill_pack_surface.surface_id,
        demo_artifact_id=artifact.demo_artifact_id,
        demo_status="completed_local_demo",
        live_connector_allowed=False,
        live_telegram_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        memory_write_allowed_by_126p=False,
        billing_allowed=False,
        entitlement_enforcement_allowed=False,
        dedupe_key=demo_dedupe_key,
        lineage_summary={
            "product_intent_kind": "prepare_meeting_brief",
            "delegated_option_kind": EXECUTION_OPTION_KIND,
            "delegated_task_class": proactive_delegation.mapped_task_class,
            "delegated_task_class_source": "existing_governed_human_review_checklist",
            "context_source_id": context_source.candidate_source_id,
            "opportunity_id": opportunity.opportunity_id,
            "suggestion_surface_id": suggestion_surface.suggestion_surface_id,
            "suggestion_delivery_record_id": suggestion_delivery.delivery_record_id,
            "proactive_adapter_id": proactive_adapter.adapter_id,
            "followup_intent_review_record_id": followup_intent.followup_intent_id,
            "followup_plan_id": followup_plan.draft_plan_id,
            "followup_choice_surface_id": choice_surface.choice_surface_id,
            "followup_selection_id": selection.selection_id,
            "followup_delegation_id": followup_delegation.followup_delegation_id,
            "proactive_delegation_adapter_id": proactive_delegation.proactive_delegation_adapter_id,
            "proactive_execution_attempt_id": execution_attempt.proactive_execution_attempt_id,
            "daily_brief_id": daily_brief.brief_id,
            "skill_pack_surface_id": skill_pack_surface.surface_id,
            "safety_boundaries": list(SAFE_BOUNDARIES),
        },
        created_at=created_at,
    )
    return registry.store_flow(flow)


def render_meeting_brief_demo_artifact(
    *,
    owner_id: str,
    robot_id: str,
    demo_flow_id: str,
    context_source_record: ContextScanCandidateSourceRecord,
    opportunity_record: ProactiveOpportunityCandidateRecord,
    suggestion_surface_record: ProactiveTelegramSuggestionSurfaceRecord,
    suggestion_delivery_record: ProactiveTelegramSuggestionDeliveryRecord,
    proactive_adapter_record: ProactiveSuggestionFollowupAdapterRecord,
    followup_plan_record: FollowUpDraftPlanRecord,
    followup_selection_record: TelegramFollowUpChoiceSelectionRecord,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    proactive_delegation_adapter_record: ProactiveDelegationAdapterRecord,
    proactive_execution_attempt_record: ProactiveExecutionAttemptRecord,
    daily_brief_snapshot_record: DailyBriefSnapshotRecord,
    skill_pack_surface_record: SkillPackActivationSurfaceRecord,
    skill_pack_registry: SkillPackActivationRegistry,
    created_at: str = DEFAULT_CREATED_AT,
) -> FirstDemoMeetingBriefArtifactRecord:
    _validate_identity(record=context_source_record, owner_id=owner_id, robot_id=robot_id)
    _validate_identity(record=skill_pack_surface_record, owner_id=owner_id, robot_id=robot_id)
    classifications = list_skill_pack_classifications(registry=skill_pack_registry)
    meeting_classifications = [
        record
        for record in classifications
        if record.owner_id == owner_id
        and record.robot_id == robot_id
        and record.skill_pack_id in {"basic_package", "pro_package"}
        and record.source_record_id
        in {
            opportunity_record.opportunity_id,
            daily_brief_snapshot_record.brief_id,
            proactive_execution_attempt_record.proactive_execution_attempt_id,
        }
    ]
    skill_pack_summary = _skill_pack_summary(meeting_classifications, skill_pack_surface_record)
    daily_brief_summary = (
        f"Daily brief {daily_brief_snapshot_record.brief_id} includes the proactive meeting-brief demo in local-only read-only form."
    )
    lineage_summary = (
        f"118P {context_source_record.candidate_source_id} -> 119P {opportunity_record.opportunity_id} -> "
        f"120P {suggestion_surface_record.suggestion_surface_id}/{suggestion_delivery_record.delivery_record_id} -> "
        f"121P {proactive_adapter_record.adapter_id} -> 108P {followup_plan_record.draft_plan_id} -> "
        f"110P {followup_selection_record.selection_id} -> 111P {followup_delegation_record.followup_delegation_id} -> "
        f"122P {proactive_delegation_adapter_record.proactive_delegation_adapter_id} -> "
        f"123P {proactive_execution_attempt_record.proactive_execution_attempt_id} -> "
        f"124P {daily_brief_snapshot_record.brief_id} -> 125P {skill_pack_surface_record.surface_id} -> 126P {demo_flow_id}."
    )
    demo_summary = (
        "Hermes noticed an upcoming meeting from authorized local context, suggested a brief, routed the selected work through the existing governed follow-up path, and rendered a deterministic local meeting-brief-style checklist artifact."
    )
    local_render_text = _render_artifact_text(
        title=context_source_record.source_title,
        meeting_context_summary=context_source_record.source_summary or opportunity_record.summary,
        demo_summary=demo_summary,
        skill_pack_summary=skill_pack_summary,
        daily_brief_summary=daily_brief_summary,
        lineage_summary=lineage_summary,
    )
    return FirstDemoMeetingBriefArtifactRecord(
        demo_artifact_id=_stable_id("meeting_brief_demo_artifact_id", demo_flow_id),
        owner_id=owner_id,
        robot_id=robot_id,
        demo_flow_id=demo_flow_id,
        artifact_type=FIRST_DEMO_ARTIFACT_TYPE,
        title=f"Meeting Brief Demo: {context_source_record.source_title}",
        local_render_text=local_render_text,
        demo_summary=demo_summary,
        meeting_context_summary=context_source_record.source_summary or opportunity_record.summary,
        preparation_checklist=SAFE_CHECKLIST,
        open_questions=SAFE_OPEN_QUESTIONS,
        suggested_materials=SAFE_SUGGESTED_MATERIALS,
        safety_boundaries=SAFE_BOUNDARIES,
        skill_pack_summary=skill_pack_summary,
        daily_brief_summary=daily_brief_summary,
        lineage_summary=lineage_summary,
        live_connector_used=False,
        live_telegram_used=False,
        model_called=False,
        tool_called=False,
        worker_dispatched=False,
        external_system_written=False,
        memory_mutated_by_126p=False,
        created_at=created_at,
    )


def get_meeting_brief_demo_flow(
    *,
    registry: MeetingBriefDemoFlowRegistry,
    demo_flow_id: str,
) -> FirstDemoMeetingBriefFlowRecord | None:
    return registry.get_flow(demo_flow_id)


def get_meeting_brief_demo_artifact(
    *,
    registry: MeetingBriefDemoFlowRegistry,
    demo_artifact_id: str,
) -> FirstDemoMeetingBriefArtifactRecord | None:
    return registry.get_artifact(demo_artifact_id)


def list_meeting_brief_demo_flows(
    *,
    registry: MeetingBriefDemoFlowRegistry,
    owner_id: str | None = None,
    robot_id: str | None = None,
) -> tuple[FirstDemoMeetingBriefFlowRecord, ...]:
    return registry.list_flows(owner_id=owner_id, robot_id=robot_id)


def _assemble_meeting_brief_proactive_delegation_record(
    *,
    proactive_adapter: ProactiveSuggestionFollowupAdapterRecord,
    followup_plan: FollowUpDraftPlanRecord,
    choice_surface: TelegramFollowUpChoiceSurfaceRecord,
    selection: TelegramFollowUpChoiceSelectionRecord,
    followup_delegation: FollowUpDelegationRequestRecord,
    authorization: ProactiveDelegationAuthorizationRecord,
    followup_registry: FollowUpDelegationRegistry,
    registry: ProactiveDelegationAdapterRegistry,
    created_at: str,
) -> ProactiveDelegationAdapterRecord:
    dedupe_key = _stable_id(
        "meeting_brief_demo_proactive_delegation",
        proactive_adapter.adapter_id,
        selection.selection_id,
        authorization.authorization_id,
        followup_delegation.followup_delegation_id,
    )
    existing = registry.get_record_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing
    authority_state = followup_registry.get_authority_state(followup_delegation.followup_delegation_id)
    if authority_state is None or followup_delegation.async_packet_id is None or followup_delegation.async_handle_id is None:
        raise ValueError("rejected_missing_followup_delegation_lineage")
    serialized_state = serialize_async_delegation_authority_state(authority_state)
    record = ProactiveDelegationAdapterRecord(
        proactive_delegation_adapter_id=_stable_id("meeting_brief_demo_proactive_delegation_id", dedupe_key),
        owner_id=proactive_adapter.owner_id,
        robot_id=proactive_adapter.robot_id,
        chat_id=proactive_adapter.chat_id,
        proactive_adapter_id=proactive_adapter.adapter_id,
        delivery_record_id=proactive_adapter.delivery_record_id,
        suggestion_surface_id=proactive_adapter.suggestion_surface_id,
        opportunity_id=proactive_adapter.opportunity_id,
        candidate_source_id=proactive_adapter.candidate_source_id,
        source_authorization_id=proactive_adapter.authorization_id,
        source_stage="118P",
        detection_stage="119P",
        suggestion_stage="120P",
        adapter_stage="121P",
        delegation_adapter_stage=PROACTIVE_DELEGATION_ADAPTER_STAGE,
        followup_intent_review_record_id=proactive_adapter.followup_intent_review_record_id,
        followup_plan_id=followup_plan.draft_plan_id,
        followup_choice_surface_id=choice_surface.choice_surface_id,
        followup_selection_id=selection.selection_id,
        explicit_owner_delegation_authorization_id=authorization.authorization_id,
        normalized_intent_kind="prepare_meeting_brief",
        selected_option_id=selection.selected_option_id,
        mapped_task_class=followup_delegation.followup_task_class,
        delegation_packet_id=followup_delegation.async_packet_id,
        delegation_handle_id=followup_delegation.async_handle_id,
        adapter_status="delegated_registered",
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
            "delegation_adapter_stage": "122P",
            "product_intent_kind": "prepare_meeting_brief",
            "delegated_option_kind": EXECUTION_OPTION_KIND,
            "delegated_task_class": followup_delegation.followup_task_class,
            "delegated_task_class_source": "existing_governed_human_review_checklist",
            "cost_lineage_id": authorization.cost_lineage_id,
            "authorization_id": authorization.authorization_id,
            "upstream_lineage": {
                "proactive_adapter": proactive_adapter.lineage_summary,
                "followup_plan": followup_plan.lineage_summary,
                "choice_surface": choice_surface.lineage_summary,
                "selection": selection.lineage_summary,
                "followup_delegation": followup_delegation.lineage_summary,
                "async_authority": serialized_state,
            },
        },
        created_at=created_at,
    )
    return registry.store_record(record)


def _assemble_followup_draft_plan(
    *,
    proactive_adapter: ProactiveSuggestionFollowupAdapterRecord,
    followup_intent: FollowUpIntentReviewRecord,
    registry: FollowUpDraftPlanRegistry,
) -> FollowUpDraftPlanRecord:
    draft_plan_id = _stable_id("meeting_brief_demo_followup_plan", followup_intent.followup_intent_id, proactive_adapter.adapter_id)
    existing = registry.get_plan(draft_plan_id)
    if existing is not None:
        return existing
    checklist_option_id = _stable_id("meeting_brief_demo_option", followup_intent.followup_intent_id, EXECUTION_OPTION_KIND)
    cancel_option_id = _stable_id("meeting_brief_demo_option", followup_intent.followup_intent_id, "cancel_followup")
    record = FollowUpDraftPlanRecord(
        draft_plan_id=draft_plan_id,
        followup_intent_id=followup_intent.followup_intent_id,
        acknowledgement_id=followup_intent.acknowledgement_id,
        delivery_id=followup_intent.delivery_id,
        surface_id=followup_intent.surface_id,
        inbox_record_id=followup_intent.inbox_record_id,
        owner_id=followup_intent.owner_id,
        robot_id=followup_intent.robot_id,
        telegram_chat_id=followup_intent.telegram_chat_id,
        status="drafted",
        title="Proactive meeting brief follow-up options",
        summary="Choose a local-only governed option for the meeting brief demo.",
        options=(
            FollowUpDraftOption(
                option_id=checklist_option_id,
                label="Checklist de revision",
                description="Reuse the existing human review checklist class for a local meeting brief demo.",
                option_kind=EXECUTION_OPTION_KIND,
                local_only=True,
                creates_authority=False,
            ),
            FollowUpDraftOption(
                option_id=cancel_option_id,
                label="Cancelar",
                description="Cancel the demo follow-up without creating any new authority.",
                option_kind="cancel_followup",
                local_only=True,
                creates_authority=False,
            ),
        ),
        lineage_summary={
            "planner_stage": "108P",
            "followup_stage": "107P",
            "followup_intent_id": followup_intent.followup_intent_id,
            "acknowledgement_stage": "120P",
            "acknowledgement_id": followup_intent.acknowledgement_id,
            "delivery_stage": "120P",
            "delivery_id": followup_intent.delivery_id,
            "surface_id": followup_intent.surface_id,
            "inbox_record_id": followup_intent.inbox_record_id,
            "owner_id": followup_intent.owner_id,
            "robot_id": followup_intent.robot_id,
            "telegram_chat_id": followup_intent.telegram_chat_id,
            "source_action": "request_followup_pending",
            "upstream_lineage": proactive_adapter.lineage_summary,
        },
        rejection_reason=None,
    )
    return registry.store(record)


def _assemble_followup_choice_surface(
    *,
    proactive_adapter: ProactiveSuggestionFollowupAdapterRecord,
    followup_plan: FollowUpDraftPlanRecord,
    registry: TelegramFollowUpChoiceSurfaceRegistry,
) -> TelegramFollowUpChoiceSurfaceRecord:
    choice_surface_id = _stable_id("meeting_brief_demo_choice_surface", followup_plan.draft_plan_id, proactive_adapter.adapter_id)
    existing = registry.get_record(choice_surface_id)
    if existing is not None:
        return existing
    option_metadata_by_ref = {
        option.option_id: {
            "option_id": option.option_id,
            "option_kind": option.option_kind,
            "label": option.label,
            "local_only": option.local_only,
            "creates_authority": option.creates_authority,
            "implies_execution": False,
            "implies_memory_mutation": False,
            "implies_external_send": False,
            "implies_model_call": False,
            "implies_tool_call": False,
            "implies_delegation_creation": False,
            "implies_action_packet_creation": False,
            "implies_approval_creation": False,
        }
        for option in followup_plan.options
    }
    record = TelegramFollowUpChoiceSurfaceRecord(
        choice_surface_id=choice_surface_id,
        draft_plan_id=followup_plan.draft_plan_id,
        followup_intent_id=followup_plan.followup_intent_id,
        acknowledgement_id=followup_plan.acknowledgement_id,
        delivery_id=followup_plan.delivery_id,
        source_surface_id=followup_plan.surface_id,
        inbox_record_id=followup_plan.inbox_record_id,
        owner_id=followup_plan.owner_id,
        robot_id=followup_plan.robot_id,
        telegram_chat_id=followup_plan.telegram_chat_id,
        status="delivered",
        text="Rendered proactive meeting brief choice surface locally.",
        button_labels=tuple(option.label for option in followup_plan.options),
        option_refs=tuple(option.option_id for option in followup_plan.options),
        lineage_summary={
            "choice_surface_stage": "109P",
            "draft_planner_stage": "108P",
            "followup_stage": "107P",
            "followup_intent_id": followup_plan.followup_intent_id,
            "acknowledgement_stage": "120P",
            "acknowledgement_id": followup_plan.acknowledgement_id,
            "delivery_stage": "120P",
            "delivery_id": followup_plan.delivery_id,
            "source_surface_stage": "120P",
            "source_surface_id": followup_plan.surface_id,
            "inbox_stage": "121P",
            "inbox_record_id": followup_plan.inbox_record_id,
            "telegram_policy_boundary_stage": "95P",
            "owner_id": followup_plan.owner_id,
            "robot_id": followup_plan.robot_id,
            "telegram_chat_id": followup_plan.telegram_chat_id,
            "option_refs": tuple(option.option_id for option in followup_plan.options),
            "option_metadata_by_ref": option_metadata_by_ref,
            "upstream_lineage": proactive_adapter.lineage_summary,
        },
        transport_receipt={"transport": "deterministic_local_demo"},
        rejection_reason=None,
    )
    return registry.store(record)


def _assemble_followup_choice_selection(
    *,
    choice_surface: TelegramFollowUpChoiceSurfaceRecord,
    registry: TelegramFollowUpChoiceSelectionRegistry,
) -> TelegramFollowUpChoiceSelectionRecord:
    selected_option_id = ""
    for option_id, metadata in choice_surface.lineage_summary.get("option_metadata_by_ref", {}).items():
        if metadata.get("option_kind") == EXECUTION_OPTION_KIND:
            selected_option_id = option_id
            break
    if not selected_option_id:
        raise ValueError("rejected_missing_followup_selection_lineage")
    selection_id = _stable_id("meeting_brief_demo_selection", choice_surface.choice_surface_id, selected_option_id)
    existing = registry.get_selection(selection_id)
    if existing is not None:
        return existing
    record = TelegramFollowUpChoiceSelectionRecord(
        selection_id=selection_id,
        choice_surface_id=choice_surface.choice_surface_id,
        draft_plan_id=choice_surface.draft_plan_id,
        selected_option_id=selected_option_id,
        selected_option_kind=EXECUTION_OPTION_KIND,
        followup_intent_id=choice_surface.followup_intent_id,
        acknowledgement_id=choice_surface.acknowledgement_id,
        delivery_id=choice_surface.delivery_id,
        source_surface_id=choice_surface.source_surface_id,
        inbox_record_id=choice_surface.inbox_record_id,
        owner_id=choice_surface.owner_id,
        robot_id=choice_surface.robot_id,
        telegram_chat_id=choice_surface.telegram_chat_id,
        status="selected_pending_authorization",
        response_text="Registered local proactive meeting brief selection only.",
        lineage_summary={
            "selection_stage": "110P",
            "selection_status": "selected_pending_authorization",
            "choice_surface_stage": "109P",
            "choice_surface_id": choice_surface.choice_surface_id,
            "draft_planner_stage": "108P",
            "draft_plan_id": choice_surface.draft_plan_id,
            "followup_stage": "107P",
            "followup_intent_id": choice_surface.followup_intent_id,
            "acknowledgement_stage": "120P",
            "acknowledgement_id": choice_surface.acknowledgement_id,
            "delivery_stage": "120P",
            "delivery_id": choice_surface.delivery_id,
            "source_surface_stage": "120P",
            "source_surface_id": choice_surface.source_surface_id,
            "inbox_stage": "121P",
            "inbox_record_id": choice_surface.inbox_record_id,
            "telegram_policy_boundary_stage": "95P",
            "owner_id": choice_surface.owner_id,
            "robot_id": choice_surface.robot_id,
            "telegram_chat_id": choice_surface.telegram_chat_id,
            "selected_option_id": selected_option_id,
            "selected_option_kind": EXECUTION_OPTION_KIND,
            "upstream_lineage": choice_surface.lineage_summary,
        },
        rejection_reason=None,
    )
    return registry.store(record)


def _build_demo_budget_policy(*, owner_id: str, robot_id: str) -> BudgetPolicy:
    return BudgetPolicy(
        policy_id=_stable_id("meeting_brief_demo_budget_policy", owner_id, robot_id),
        owner_id=owner_id,
        robot_id=robot_id,
        routing_mode_allowlist=("economy", "balanced", "premium", "byok"),
        default_routing_mode="balanced",
        max_estimated_cost_usd=0.08,
        confirmation_cost_usd=0.02,
        max_input_tokens=4000,
        max_output_tokens=1800,
        long_context_confirmation_tokens=2400,
        byok_allowed=False,
        async_delegation_allowed=True,
        premium_allowed_without_confirmation=False,
        allowed_task_classes=(
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
        sensitive_task_min_tier="advanced",
        unsafe_model_block=True,
        untrusted_model_block=True,
        requires_trace=True,
    )


def _build_demo_task_cost_request(*, owner_id: str, robot_id: str, created_at: str) -> TaskCostRequest:
    return TaskCostRequest(
        request_id=_stable_id("meeting_brief_demo_cost_request", owner_id, robot_id, created_at),
        owner_id=owner_id,
        robot_id=robot_id,
        task_class="async_delegation",
        routing_mode="balanced",
        sensitivity="ordinary",
        requires_tools=False,
        requires_long_context=False,
        input_chars_estimate=1200,
        expected_output_chars=800,
        context_item_count=2,
        active_skill_id="basic_assistant",
        memory_context_used=False,
        routine_requested=True,
        async_delegation_requested=True,
        authority_expansion_requested=False,
    )


def _build_demo_cost_preflight(*, request: TaskCostRequest) -> CostPreflightResult:
    token_estimate = TokenUsageEstimate(
        estimated_input_tokens=300,
        estimated_output_tokens=220,
        estimated_total_tokens=520,
        estimation_basis="deterministic_local_demo",
        long_context_applied=False,
    )
    route = ModelRouteDecision(
        selected_provider_id="local_fixture",
        selected_model_id="balanced_standard_v1",
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=("balanced_standard_v1",),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id="balanced_standard_v1",
        candidate_model_ids=("balanced_standard_v1",),
        decision="allow",
        reason_code="allow_selected_eligible_route",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.03,
        budget_state="within_budget",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision="allow",
        budget_policy_id="meeting_brief_demo_policy",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def _require_record(record: object, expected_type: type[object], error_code: str):
    if not isinstance(record, expected_type):
        raise ValueError(error_code)
    return record


def _validate_identity(*, record: object, owner_id: str, robot_id: str) -> None:
    if getattr(record, "owner_id", None) != owner_id:
        raise ValueError("rejected_cross_owner_record")
    if getattr(record, "robot_id", None) != robot_id:
        raise ValueError("rejected_cross_robot_record")


def _reject_live_flags(record: object) -> None:
    blocked_truthy = (
        "live_connector_allowed",
        "live_send_allowed",
        "live_telegram_allowed",
        "live_telegram_used",
        "model_call_allowed",
        "model_called",
        "tool_call_allowed",
        "tool_called",
        "external_write_allowed",
        "external_written",
        "external_system_written",
        "worker_dispatch_allowed",
        "worker_dispatched",
        "memory_write_allowed",
        "memory_mutated",
        "memory_mutated_by_126p",
        "billing_allowed",
        "entitlement_enforcement_allowed",
    )
    for field_name in blocked_truthy:
        if bool(getattr(record, field_name, False)):
            if field_name in {"live_send_allowed", "live_telegram_allowed", "live_telegram_used"}:
                raise ValueError("rejected_live_telegram_delivery")
            if field_name in {"model_call_allowed", "model_called", "tool_call_allowed", "tool_called"}:
                raise ValueError("rejected_model_tool_dependency")
            if field_name in {"external_write_allowed", "external_written", "external_system_written"}:
                raise ValueError("rejected_external_write_dependency")
            if field_name in {"worker_dispatch_allowed", "worker_dispatched"}:
                raise ValueError("rejected_worker_dispatch_dependency")
            if field_name in {"memory_write_allowed", "memory_mutated", "memory_mutated_by_126p"}:
                raise ValueError("rejected_memory_write_dependency")
            raise ValueError("rejected_live_dependency")
    for field_name in ("source_type", "telegram_transport", "delivery_mode"):
        value = getattr(record, field_name, None)
        if isinstance(value, str) and value.startswith("live_"):
            if field_name == "source_type":
                raise ValueError("rejected_live_connector_source_type")
            raise ValueError("rejected_live_telegram_delivery")
    for field_name in ("source_summary", "summary", "display_text", "local_render_text", "source_hint", "title", "text"):
        value = getattr(record, field_name, None)
        if isinstance(value, str):
            _reject_sensitive_text(value)


def _reject_sensitive_text(text: str) -> None:
    lowered = text.lower()
    if any(keyword in lowered for keyword in CREDENTIAL_KEYWORDS):
        raise ValueError("rejected_raw_credentials")
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        raise ValueError("rejected_sensitive_raw_payload")


def _skill_pack_summary(classifications: list[object], surface: SkillPackActivationSurfaceRecord) -> str:
    pack_ids = sorted({getattr(record, "skill_pack_id", "unknown_unclassified") for record in classifications})
    pack_text = ", ".join(pack_ids) if pack_ids else "basic_package"
    return (
        f"Skill pack surface {surface.surface_id} classifies the demo under {pack_text}. "
        f"basic_package_count={surface.basic_package_count}, pro_package_count={surface.pro_package_count}."
    )


def _render_artifact_text(
    *,
    title: str,
    meeting_context_summary: str,
    demo_summary: str,
    skill_pack_summary: str,
    daily_brief_summary: str,
    lineage_summary: str,
) -> str:
    sections = [
        "Demo Summary",
        demo_summary,
        "",
        "Context Source",
        f"Meeting title: {title}",
        f"Safe context summary: {meeting_context_summary}",
        "",
        "Opportunity Detected",
        "Opportunity type: meeting_brief_missing",
        "Suggested next step: prepare_brief",
        "",
        "Suggestion Surface",
        "A local-only proactive Telegram suggestion was rendered and delivered through injected_local_only transport.",
        "",
        "Authorization Path",
        "normalized_intent_kind remained prepare_meeting_brief.",
        f"Delegated executable class reused existing {EXECUTION_OPTION_KIND} / {EXECUTION_TASK_CLASS}.",
        "",
        "Delegation Registered",
        "The demo reused the existing governed follow-up delegation path without creating a new authority path.",
        "",
        "Local Execution Candidate",
        "Artifact type: local_meeting_brief_demo",
        "Preparation checklist:",
    ]
    sections.extend(f"- {line}" for line in SAFE_CHECKLIST)
    sections.extend(
        [
            "",
            "Open Questions",
            *[f"- {line}" for line in SAFE_OPEN_QUESTIONS],
            "",
            "Suggested Materials",
            *[f"- {line}" for line in SAFE_SUGGESTED_MATERIALS],
            "",
            "Daily Brief Inclusion",
            daily_brief_summary,
            "",
            "Skill Pack Classification",
            skill_pack_summary,
            "",
            "Safety Boundaries",
            *[f"- {line}" for line in SAFE_BOUNDARIES],
            "",
            "Lineage Summary",
            lineage_summary,
        ]
    )
    return "\n".join(sections)
def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
