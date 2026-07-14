from __future__ import annotations

from dataclasses import dataclass, field
import re
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
from app.demo_result_delivery_surface import DemoResultDeliverySurfaceRecord
from app.followup_delegation_authority import (
    FollowUpDelegationAuthorizationEvidence,
    FollowUpDelegationRegistry,
    FollowUpDelegationRequestRecord,
    create_followup_delegation_from_selection,
)
from app.followup_draft_planner import FollowUpDraftOption, FollowUpDraftPlanRecord, FollowUpDraftPlanRegistry
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
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionRecord, TelegramFollowUpChoiceSelectionRegistry
from app.telegram_followup_choice_surface import TelegramFollowUpChoiceSurfaceRecord, TelegramFollowUpChoiceSurfaceRegistry
from app.async_delegation_authority import serialize_async_delegation_authority_state


DOCUMENT_REVIEW_DEMO_STAGE = "128P"
DOCUMENT_REVIEW_DEMO_NAME = "document_review_from_context"
DOCUMENT_REVIEW_DEMO_MODE = "deterministic_local_demo"
DOCUMENT_REVIEW_ARTIFACT_TYPE = "local_document_review_demo"
EXECUTION_TASK_CLASS = "FOLLOWUP_HUMAN_REVIEW_CHECKLIST"
EXECUTION_OPTION_KIND = "human_review_checklist"
SKILL_PACK_ID = "documents_pack"
DEFAULT_CREATED_AT = "2026-06-21T00:00:00Z"
DEFAULT_BRIEF_DATE = "2026-06-21"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_WINDOW_START = "2026-06-21T00:00:00Z"
DEFAULT_WINDOW_END = "2026-06-21T23:59:59Z"
ALLOWED_DEMO_SOURCE_TYPES = frozenset({"mock_document"})
ALLOWED_DEMO_SOURCE_CATEGORIES = frozenset({"document_context"})
POSITIVE_OCR_PATTERNS = (
    re.compile(r"\bocr (?:was )?performed\b"),
    re.compile(r"\bperformed ocr\b"),
)
POSITIVE_LEGAL_ADVICE_PATTERNS = (
    re.compile(r"\bthis is legal advice\b"),
    re.compile(r"\blegal advice provided\b"),
    re.compile(r"\bprovided legal advice\b"),
    re.compile(r"\boffered legal advice\b"),
)
POSITIVE_SIGNATURE_PATTERNS = (
    re.compile(r"\bcertified signature created\b"),
    re.compile(r"\blegal signature created\b"),
    re.compile(r"\bdocument (?:was )?signed\b"),
    re.compile(r"\bsigned on your behalf\b"),
)
SAFE_REVIEW_CHECKLIST = (
    "Confirm the document type, owner context, and why review is being requested.",
    "Identify key sections, dates, obligations, and renewal or termination terms.",
    "List unclear clauses, negotiation points, and items to raise with the owner or advisor.",
    "Check whether supporting materials or prior versions should be reviewed before the meeting.",
    "Keep the output local and do not sign, annotate, or send any document from this demo.",
)
SAFE_POSSIBLE_RISK_NOTES = (
    "Undefined obligations or timing commitments may need clarification.",
    "Commercial or confidentiality terms may require owner review before discussion.",
    "Version-control or missing-context risks may require comparing against prior safe local notes.",
)
SAFE_OPEN_QUESTIONS = (
    "Which clauses matter most to the owner before the meeting?",
    "Is there a prior version or related note that should be compared locally?",
    "Which questions should be escalated to a professional advisor rather than answered by Hermes?",
)
SAFE_SUGGESTED_MATERIALS = (
    "Prior local draft or change summary fixture, if available.",
    "Local meeting notes tied to the vendor or agreement topic.",
    "Owner-provided checklist of negotiation points or concerns.",
)
SAFE_BOUNDARIES = (
    "No live document connector used.",
    "No OCR was performed.",
    "No legal advice provided.",
    "No certified signature or legal signature created.",
    "No model/tool calls used.",
    "No external file was written.",
    "No Memory Center mutation performed by 128P.",
)
NO_ACTION_TAKEN_NOTICE = (
    "No live document read, OCR, legal advice, signature creation, Telegram send, callback binding, approval, follow-up intent, delegation, execution, memory mutation, billing, or external action was created by 128P."
)


@dataclass(frozen=True, slots=True)
class DocumentReviewDemoFixture:
    fixture_id: str
    source_type: str
    source_category: str
    source_status: str
    scan_scope: str
    document_title: str
    safe_summary: str
    source_hint: str
    provenance_notes: str
    retention_policy: str
    brief_date: str = DEFAULT_BRIEF_DATE
    timezone: str = DEFAULT_TIMEZONE
    window_start: str = DEFAULT_WINDOW_START
    window_end: str = DEFAULT_WINDOW_END
    live_document_read_used: bool = False
    ocr_performed: bool = False
    source_payload: object | None = None

    def __post_init__(self) -> None:
        if self.source_type not in ALLOWED_DEMO_SOURCE_TYPES:
            raise ValueError("rejected_live_document_source")
        if self.source_category not in ALLOWED_DEMO_SOURCE_CATEGORIES:
            raise ValueError("rejected_invalid_source_category")
        if not self.document_title:
            raise ValueError("rejected_missing_document_title")
        if self.live_document_read_used:
            raise ValueError("rejected_live_document_source")
        if self.ocr_performed:
            raise ValueError("rejected_ocr_dependency")
        if self.source_payload is not None:
            raise ValueError("rejected_raw_payload_not_allowed")
        for text in (self.document_title, self.safe_summary, self.source_hint):
            _reject_sensitive_text(text)
            _reject_prohibited_claim_text(text)


@dataclass(frozen=True, slots=True)
class DocumentReviewDemoArtifactRecord:
    demo_artifact_id: str
    owner_id: str
    robot_id: str
    document_demo_flow_id: str
    artifact_type: str
    title: str
    local_render_text: str
    demo_summary: str
    document_context_summary: str
    review_checklist: tuple[str, ...]
    possible_risk_notes: tuple[str, ...]
    open_questions: tuple[str, ...]
    suggested_materials: tuple[str, ...]
    documents_pack_summary: str
    daily_brief_summary: str
    safety_boundaries: tuple[str, ...]
    no_action_taken_notice: str
    lineage_summary: str
    live_connector_used: bool
    live_document_read_used: bool
    live_telegram_used: bool
    ocr_performed: bool
    model_called: bool
    tool_called: bool
    worker_dispatched: bool
    external_system_written: bool
    memory_mutated_by_128p: bool
    legal_advice_provided: bool
    certified_signature_created: bool
    created_at: str

    def __post_init__(self) -> None:
        if self.artifact_type != DOCUMENT_REVIEW_ARTIFACT_TYPE:
            raise ValueError("rejected_invalid_artifact_type")
        if any(
            (
                self.live_connector_used,
                self.live_document_read_used,
                self.live_telegram_used,
                self.ocr_performed,
                self.model_called,
                self.tool_called,
                self.worker_dispatched,
                self.external_system_written,
                self.memory_mutated_by_128p,
                self.legal_advice_provided,
                self.certified_signature_created,
            )
        ):
            raise ValueError("rejected_live_dependency")


@dataclass(frozen=True, slots=True)
class DocumentReviewDemoFlowRecord:
    document_demo_flow_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    demo_stage: str
    demo_name: str
    demo_mode: str
    document_fixture_id: str
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
    demo_result_surface_id: str | None
    demo_artifact_id: str
    normalized_intent_kind: str
    execution_task_class: str
    skill_pack_id: str
    demo_status: str
    live_connector_allowed: bool
    live_document_read_allowed: bool
    live_telegram_allowed: bool
    ocr_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    memory_write_allowed_by_128p: bool
    legal_advice_allowed: bool
    certified_signature_allowed: bool
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.demo_stage != DOCUMENT_REVIEW_DEMO_STAGE:
            raise ValueError("rejected_invalid_demo_stage")
        if self.demo_name != DOCUMENT_REVIEW_DEMO_NAME:
            raise ValueError("rejected_invalid_demo_name")
        if self.demo_mode != DOCUMENT_REVIEW_DEMO_MODE:
            raise ValueError("rejected_invalid_demo_mode")
        if self.demo_status not in {
            "completed_local_demo",
            "partial_local_demo",
            "rejected_invalid_lineage",
            "rejected_live_dependency",
            "rejected_sensitive_data",
            "rejected_legal_claim",
        }:
            raise ValueError("rejected_invalid_demo_status")
        if any(
            (
                self.live_connector_allowed,
                self.live_document_read_allowed,
                self.live_telegram_allowed,
                self.ocr_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.memory_write_allowed_by_128p,
                self.legal_advice_allowed,
                self.certified_signature_allowed,
                self.billing_allowed,
                self.entitlement_enforcement_allowed,
            )
        ):
            raise ValueError("rejected_live_dependency")


@dataclass(slots=True)
class DocumentReviewDemoFlowRegistry:
    flows_by_id: dict[str, DocumentReviewDemoFlowRecord] = field(default_factory=dict)
    flow_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    artifacts_by_id: dict[str, DocumentReviewDemoArtifactRecord] = field(default_factory=dict)

    def store_flow(self, flow: DocumentReviewDemoFlowRecord) -> DocumentReviewDemoFlowRecord:
        self.flows_by_id[flow.document_demo_flow_id] = flow
        self.flow_ids_by_dedupe_key[flow.dedupe_key] = flow.document_demo_flow_id
        return flow

    def get_flow(self, document_demo_flow_id: str) -> DocumentReviewDemoFlowRecord | None:
        return self.flows_by_id.get(document_demo_flow_id)

    def get_flow_by_dedupe_key(self, dedupe_key: str) -> DocumentReviewDemoFlowRecord | None:
        flow_id = self.flow_ids_by_dedupe_key.get(dedupe_key)
        if flow_id is None:
            return None
        return self.flows_by_id.get(flow_id)

    def list_flows(self, *, owner_id: str | None = None, robot_id: str | None = None) -> tuple[DocumentReviewDemoFlowRecord, ...]:
        records = tuple(self.flows_by_id[key] for key in sorted(self.flows_by_id))
        if owner_id is not None:
            records = tuple(record for record in records if record.owner_id == owner_id)
        if robot_id is not None:
            records = tuple(record for record in records if record.robot_id == robot_id)
        return records

    def store_artifact(self, artifact: DocumentReviewDemoArtifactRecord) -> DocumentReviewDemoArtifactRecord:
        self.artifacts_by_id[artifact.demo_artifact_id] = artifact
        return artifact

    def get_artifact(self, demo_artifact_id: str) -> DocumentReviewDemoArtifactRecord | None:
        return self.artifacts_by_id.get(demo_artifact_id)


@dataclass(slots=True)
class DocumentReviewDemoDependencyBundle:
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
    demo_registry: DocumentReviewDemoFlowRegistry = field(default_factory=DocumentReviewDemoFlowRegistry)


class _LocalOnlyTelegramTransport(TelegramAsyncResultTransport):
    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict[str, object]:
        return {
            "transport": "deterministic_local_demo",
            "chat_id": chat_id,
            "button_count": len(buttons),
            "text_fingerprint": f"{len(text)}:{len(buttons)}",
        }


def build_default_document_review_demo_fixture() -> DocumentReviewDemoFixture:
    return DocumentReviewDemoFixture(
        fixture_id="fixture-128p-document-review-demo",
        source_type="mock_document",
        source_category="document_context",
        source_status="authorized_local_fixture",
        scan_scope="summary_fixture",
        document_title="Sample NDA / Vendor Agreement",
        safe_summary="Local fixture document appears to need review before a meeting.",
        source_hint="review requested and contract-like document with key terms needing checklist",
        provenance_notes="deterministic_local_demo_fixture",
        retention_policy="keep_until_fixture_rotation",
    )


def run_local_document_review_demo_flow(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    dependencies: DocumentReviewDemoDependencyBundle | None = None,
    fixture: DocumentReviewDemoFixture | None = None,
    created_at: str = DEFAULT_CREATED_AT,
) -> DocumentReviewDemoFlowRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not chat_id:
        raise ValueError("rejected_missing_chat_id")
    bundle = DocumentReviewDemoDependencyBundle() if dependencies is None else dependencies
    scenario = build_default_document_review_demo_fixture() if fixture is None else fixture
    _validate_fixture(scenario)
    _reject_sensitive_text(chat_id)

    dedupe_key = _stable_id(
        "document_review_demo_flow",
        owner_id,
        robot_id,
        chat_id,
        scenario.fixture_id,
        scenario.source_type,
        scenario.document_title,
    )
    existing = bundle.demo_registry.get_flow_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    context_authorization = create_local_context_scan_authorization(
        owner_id=owner_id,
        robot_id=robot_id,
        allowed_source_types=("mock_document",),
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
        source_title=scenario.document_title,
        source_summary=scenario.safe_summary,
        source_timestamp=created_at,
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
    if opportunity.opportunity_type != "document_review_needed":
        raise ValueError("rejected_missing_119p_opportunity_lineage")
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
    selection = _assemble_followup_choice_selection(choice_surface=choice_surface, registry=bundle.choice_selection_registry)
    task_request = _build_demo_task_cost_request(owner_id=owner_id, robot_id=robot_id, created_at=created_at)
    cost_preflight = _build_demo_cost_preflight(request=task_request)
    budget_policy = _build_demo_budget_policy(owner_id=owner_id, robot_id=robot_id)
    followup_authorization = FollowUpDelegationAuthorizationEvidence(
        authorization_id=_stable_id("document_review_demo_followup_authorization", selection.selection_id, task_request.request_id),
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
    proactive_delegation = _assemble_document_review_proactive_delegation_record(
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
            fixture_id="fixture-128p-deterministic-local-document-review",
            owner_id=owner_id,
            robot_id=robot_id,
            allowed_task_classes=(EXECUTION_TASK_CLASS,),
            deterministic_payloads={
                EXECUTION_TASK_CLASS: "Prepared deterministic local document review checklist for Sample NDA / Vendor Agreement."
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
    return assemble_document_review_demo_flow(
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        fixture=scenario,
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


def assemble_document_review_demo_flow(
    *,
    owner_id: str,
    robot_id: str,
    chat_id: str,
    fixture: DocumentReviewDemoFixture,
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
    registry: DocumentReviewDemoFlowRegistry,
    skill_pack_registry: SkillPackActivationRegistry,
    demo_result_surface_record: object | None = None,
    require_demo_result_surface: bool = False,
    created_at: str = DEFAULT_CREATED_AT,
) -> DocumentReviewDemoFlowRecord:
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
    proactive_delegation = _require_record(proactive_delegation_adapter_record, ProactiveDelegationAdapterRecord, "rejected_missing_122p_delegation_lineage")
    execution_attempt = _require_record(proactive_execution_attempt_record, ProactiveExecutionAttemptRecord, "rejected_missing_123p_execution_lineage")
    daily_brief = _require_record(daily_brief_snapshot_record, DailyBriefSnapshotRecord, "rejected_missing_124p_daily_brief_lineage")
    skill_pack_surface = _require_record(skill_pack_surface_record, SkillPackActivationSurfaceRecord, "rejected_missing_125p_skill_pack_lineage")

    demo_result_surface = None
    if demo_result_surface_record is not None:
        demo_result_surface = _require_record(
            demo_result_surface_record,
            DemoResultDeliverySurfaceRecord,
            "rejected_missing_127p_presentational_surface_lineage",
        )
    if require_demo_result_surface and demo_result_surface is None:
        raise ValueError("rejected_missing_127p_presentational_surface_lineage")

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
        _reject_record_texts(record)
    if demo_result_surface is not None:
        _validate_identity(record=demo_result_surface, owner_id=owner_id, robot_id=robot_id)
        _reject_live_flags(demo_result_surface)

    if suggestion_surface.chat_id != chat_id or suggestion_delivery.chat_id != chat_id:
        raise ValueError("rejected_chat_mismatch")
    if proactive_adapter.chat_id != chat_id or proactive_delegation.chat_id != chat_id or execution_attempt.chat_id != chat_id:
        raise ValueError("rejected_chat_mismatch")
    if context_source.source_type != "mock_document":
        raise ValueError("rejected_missing_118p_mock_document_context_source_lineage")
    if opportunity.candidate_source_id != context_source.candidate_source_id:
        raise ValueError("rejected_missing_118p_context_source_lineage")
    if opportunity.opportunity_type != "document_review_needed":
        raise ValueError("rejected_missing_119p_opportunity_lineage")
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
    if proactive_adapter.normalized_intent_kind != "review_document":
        raise ValueError("rejected_invalid_demo_intent_lineage")
    if proactive_delegation.normalized_intent_kind != "review_document":
        raise ValueError("rejected_invalid_demo_intent_lineage")
    if proactive_delegation.mapped_task_class != EXECUTION_TASK_CLASS:
        raise ValueError("rejected_unsupported_task_class")
    if proactive_delegation.selected_option_id != selection.selected_option_id:
        raise ValueError("rejected_missing_followup_selection_lineage")

    demo_dedupe_key = _stable_id(
        "document_review_demo_flow",
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

    artifact = render_document_review_demo_artifact(
        owner_id=owner_id,
        robot_id=robot_id,
        document_demo_flow_id=_stable_id("document_review_demo_flow_id", demo_dedupe_key),
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
        demo_result_surface_record=demo_result_surface,
        created_at=created_at,
    )
    registry.store_artifact(artifact)

    event_candidate_id = execution_attempt.completion_event_candidate_id or execution_attempt.failure_event_candidate_id
    flow = DocumentReviewDemoFlowRecord(
        document_demo_flow_id=artifact.document_demo_flow_id,
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=chat_id,
        demo_stage=DOCUMENT_REVIEW_DEMO_STAGE,
        demo_name=DOCUMENT_REVIEW_DEMO_NAME,
        demo_mode=DOCUMENT_REVIEW_DEMO_MODE,
        document_fixture_id=fixture.fixture_id,
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
        demo_result_surface_id=None if demo_result_surface is None else demo_result_surface.demo_result_surface_id,
        demo_artifact_id=artifact.demo_artifact_id,
        normalized_intent_kind="review_document",
        execution_task_class=EXECUTION_TASK_CLASS,
        skill_pack_id=SKILL_PACK_ID,
        demo_status="completed_local_demo",
        live_connector_allowed=False,
        live_document_read_allowed=False,
        live_telegram_allowed=False,
        ocr_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        memory_write_allowed_by_128p=False,
        legal_advice_allowed=False,
        certified_signature_allowed=False,
        billing_allowed=False,
        entitlement_enforcement_allowed=False,
        dedupe_key=demo_dedupe_key,
        lineage_summary={
            "product_intent_kind": "review_document",
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
            "demo_result_surface_id": None if demo_result_surface is None else demo_result_surface.demo_result_surface_id,
            "safety_boundaries": list(SAFE_BOUNDARIES),
        },
        created_at=created_at,
    )
    return registry.store_flow(flow)


def render_document_review_demo_artifact(
    *,
    owner_id: str,
    robot_id: str,
    document_demo_flow_id: str,
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
    demo_result_surface_record: DemoResultDeliverySurfaceRecord | None = None,
    created_at: str = DEFAULT_CREATED_AT,
) -> DocumentReviewDemoArtifactRecord:
    for record in (
        context_source_record,
        opportunity_record,
        suggestion_surface_record,
        suggestion_delivery_record,
        proactive_adapter_record,
        followup_plan_record,
        followup_selection_record,
        followup_delegation_record,
        proactive_delegation_adapter_record,
        proactive_execution_attempt_record,
        daily_brief_snapshot_record,
        skill_pack_surface_record,
    ):
        _validate_identity(record=record, owner_id=owner_id, robot_id=robot_id)
        _reject_live_flags(record)
        _reject_record_texts(record)
    if demo_result_surface_record is not None:
        _validate_identity(record=demo_result_surface_record, owner_id=owner_id, robot_id=robot_id)
        _reject_live_flags(demo_result_surface_record)

    classifications = list_skill_pack_classifications(registry=skill_pack_registry)
    document_classifications = [
        record
        for record in classifications
        if record.owner_id == owner_id
        and record.robot_id == robot_id
        and record.skill_pack_id == SKILL_PACK_ID
        and record.source_record_id
        in {
            opportunity_record.opportunity_id,
            daily_brief_snapshot_record.brief_id,
            proactive_execution_attempt_record.proactive_execution_attempt_id,
            context_source_record.candidate_source_id,
        }
    ]
    if not document_classifications:
        raise ValueError("rejected_missing_125p_documents_pack_classification")
    document_pack_summary = _documents_pack_summary(document_classifications, skill_pack_surface_record)
    daily_brief_summary = (
        f"Daily brief {daily_brief_snapshot_record.brief_id} includes the proactive document-review demo in local-only read-only form."
    )
    lineage_summary = (
        f"118P {context_source_record.candidate_source_id} -> 119P {opportunity_record.opportunity_id} -> "
        f"120P {suggestion_surface_record.suggestion_surface_id}/{suggestion_delivery_record.delivery_record_id} -> "
        f"121P {proactive_adapter_record.adapter_id} -> 108P {followup_plan_record.draft_plan_id} -> "
        f"110P {followup_selection_record.selection_id} -> 111P {followup_delegation_record.followup_delegation_id} -> "
        f"122P {proactive_delegation_adapter_record.proactive_delegation_adapter_id} -> "
        f"123P {proactive_execution_attempt_record.proactive_execution_attempt_id} -> "
        f"124P {daily_brief_snapshot_record.brief_id} -> 125P {skill_pack_surface_record.surface_id}"
        f"{'' if demo_result_surface_record is None else f' -> 127P {demo_result_surface_record.demo_result_surface_id}'} -> "
        f"128P {document_demo_flow_id}."
    )
    demo_summary = (
        "Hermes noticed a document review need from authorized local context, suggested a safe review, routed the selected work through the existing governed follow-up path, and rendered a deterministic local document-review checklist artifact."
    )
    local_render_text = _render_document_review_artifact_text(
        title=context_source_record.source_title,
        document_context_summary=context_source_record.source_summary or opportunity_record.summary,
        demo_summary=demo_summary,
        document_pack_summary=document_pack_summary,
        daily_brief_summary=daily_brief_summary,
        lineage_summary=lineage_summary,
    )
    return DocumentReviewDemoArtifactRecord(
        demo_artifact_id=_stable_id("document_review_demo_artifact_id", document_demo_flow_id),
        owner_id=owner_id,
        robot_id=robot_id,
        document_demo_flow_id=document_demo_flow_id,
        artifact_type=DOCUMENT_REVIEW_ARTIFACT_TYPE,
        title=f"Document Review Demo: {context_source_record.source_title}",
        local_render_text=local_render_text,
        demo_summary=demo_summary,
        document_context_summary=context_source_record.source_summary or opportunity_record.summary,
        review_checklist=SAFE_REVIEW_CHECKLIST,
        possible_risk_notes=SAFE_POSSIBLE_RISK_NOTES,
        open_questions=SAFE_OPEN_QUESTIONS,
        suggested_materials=SAFE_SUGGESTED_MATERIALS,
        documents_pack_summary=document_pack_summary,
        daily_brief_summary=daily_brief_summary,
        safety_boundaries=SAFE_BOUNDARIES,
        no_action_taken_notice=NO_ACTION_TAKEN_NOTICE,
        lineage_summary=lineage_summary,
        live_connector_used=False,
        live_document_read_used=False,
        live_telegram_used=False,
        ocr_performed=False,
        model_called=False,
        tool_called=False,
        worker_dispatched=False,
        external_system_written=False,
        memory_mutated_by_128p=False,
        legal_advice_provided=False,
        certified_signature_created=False,
        created_at=created_at,
    )


def get_document_review_demo_flow(
    *,
    registry: DocumentReviewDemoFlowRegistry,
    document_demo_flow_id: str,
) -> DocumentReviewDemoFlowRecord | None:
    return registry.get_flow(document_demo_flow_id)


def get_document_review_demo_artifact(
    *,
    registry: DocumentReviewDemoFlowRegistry,
    demo_artifact_id: str,
) -> DocumentReviewDemoArtifactRecord | None:
    return registry.get_artifact(demo_artifact_id)


def list_document_review_demo_flows(
    *,
    registry: DocumentReviewDemoFlowRegistry,
    owner_id: str | None = None,
    robot_id: str | None = None,
) -> tuple[DocumentReviewDemoFlowRecord, ...]:
    return registry.list_flows(owner_id=owner_id, robot_id=robot_id)


def _assemble_document_review_proactive_delegation_record(
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
        "document_review_demo_proactive_delegation",
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
        proactive_delegation_adapter_id=_stable_id("document_review_demo_proactive_delegation_id", dedupe_key),
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
        normalized_intent_kind="review_document",
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
            "product_intent_kind": "review_document",
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
    draft_plan_id = _stable_id("document_review_demo_followup_plan", followup_intent.followup_intent_id, proactive_adapter.adapter_id)
    existing = registry.get_plan(draft_plan_id)
    if existing is not None:
        return existing
    checklist_option_id = _stable_id("document_review_demo_option", followup_intent.followup_intent_id, EXECUTION_OPTION_KIND)
    cancel_option_id = _stable_id("document_review_demo_option", followup_intent.followup_intent_id, "cancel_followup")
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
        title="Proactive document review follow-up options",
        summary="Choose a local-only governed option for the document review demo.",
        options=(
            FollowUpDraftOption(
                option_id=checklist_option_id,
                label="Checklist de revision documental",
                description="Reuse the existing human review checklist class for a local document review demo.",
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
    choice_surface_id = _stable_id("document_review_demo_choice_surface", followup_plan.draft_plan_id, proactive_adapter.adapter_id)
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
        text="Rendered proactive document review choice surface locally.",
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
    selection_id = _stable_id("document_review_demo_selection", choice_surface.choice_surface_id, selected_option_id)
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
        response_text="Registered local proactive document review selection only.",
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
        policy_id=_stable_id("document_review_demo_budget_policy", owner_id, robot_id),
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
        request_id=_stable_id("document_review_demo_cost_request", owner_id, robot_id, created_at),
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
        active_skill_id="documents_pack_demo",
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
        budget_policy_id="document_review_demo_policy",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def _documents_pack_summary(classifications: list[object], skill_pack_surface: SkillPackActivationSurfaceRecord) -> str:
    return (
        f"Skill pack surface {skill_pack_surface.surface_id} classifies this document-review demo under {SKILL_PACK_ID} "
        f"with {len(classifications)} matching local-safe classification record(s)."
    )


def _render_document_review_artifact_text(
    *,
    title: str,
    document_context_summary: str,
    demo_summary: str,
    document_pack_summary: str,
    daily_brief_summary: str,
    lineage_summary: str,
) -> str:
    sections = [
        f"Document title: {title}",
        f"Document context: {document_context_summary}",
        "",
        demo_summary,
        "",
        f"Normalized intent kind remained review_document.",
        f"Delegated executable class reused existing {EXECUTION_OPTION_KIND} / {EXECUTION_TASK_CLASS}.",
        "No new document-specific executable task class was created.",
        "",
        "Review checklist:",
    ]
    sections.extend(f"- {item}" for item in SAFE_REVIEW_CHECKLIST)
    sections.extend(["", "Possible risk notes:"])
    sections.extend(f"- {item}" for item in SAFE_POSSIBLE_RISK_NOTES)
    sections.extend(["", "Open questions:"])
    sections.extend(f"- {item}" for item in SAFE_OPEN_QUESTIONS)
    sections.extend(["", "Suggested materials:"])
    sections.extend(f"- {item}" for item in SAFE_SUGGESTED_MATERIALS)
    sections.extend(
        [
            "",
            f"Documents Pack classification: {document_pack_summary}",
            f"Daily brief inclusion: {daily_brief_summary}",
            "",
            "Safety boundaries:",
        ]
    )
    sections.extend(f"- {item}" for item in SAFE_BOUNDARIES)
    sections.extend(
        [
            "",
            f"No action taken: {NO_ACTION_TAKEN_NOTICE}",
            "",
            f"Lineage summary: {lineage_summary}",
        ]
    )
    return "\n".join(sections)


def _require_record(record: object, record_type: type[object], error_code: str):
    if not isinstance(record, record_type):
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
        "live_connector_used",
        "live_document_read_allowed",
        "live_document_read_used",
        "live_send_allowed",
        "live_telegram_allowed",
        "live_telegram_used",
        "telegram_delivery_allowed",
        "callback_binding_allowed",
        "followup_intent_creation_allowed",
        "async_delegation_allowed",
        "execution_allowed",
        "memory_write_allowed",
        "memory_mutated_by_128p",
        "memory_mutated_by_127p",
        "memory_mutated_by_126p",
        "model_call_allowed",
        "model_called",
        "tool_call_allowed",
        "tool_called",
        "external_write_allowed",
        "external_system_written",
        "external_written",
        "worker_dispatch_allowed",
        "worker_dispatched",
        "billing_allowed",
        "entitlement_enforcement_allowed",
        "ocr_allowed",
        "ocr_performed",
        "legal_advice_allowed",
        "legal_advice_provided",
        "certified_signature_allowed",
        "certified_signature_created",
    )
    for field_name in blocked_truthy:
        if bool(getattr(record, field_name, False)):
            if field_name in {"live_document_read_allowed", "live_document_read_used"}:
                raise ValueError("rejected_live_document_source")
            if field_name in {"live_send_allowed", "live_telegram_allowed", "live_telegram_used", "telegram_delivery_allowed"}:
                raise ValueError("rejected_live_telegram_delivery")
            if field_name in {"model_call_allowed", "model_called", "tool_call_allowed", "tool_called"}:
                raise ValueError("rejected_model_tool_dependency")
            if field_name in {"external_write_allowed", "external_system_written", "external_written"}:
                raise ValueError("rejected_external_write_dependency")
            if field_name in {"worker_dispatch_allowed", "worker_dispatched"}:
                raise ValueError("rejected_worker_dispatch_dependency")
            if field_name in {"memory_write_allowed", "memory_mutated_by_128p", "memory_mutated_by_127p", "memory_mutated_by_126p"}:
                raise ValueError("rejected_memory_write_dependency")
            if field_name in {"live_connector_allowed", "live_connector_used"}:
                raise ValueError("rejected_live_connector_usage")
            if field_name in {"ocr_allowed", "ocr_performed"}:
                raise ValueError("rejected_ocr_dependency")
            if field_name in {"legal_advice_allowed", "legal_advice_provided"}:
                raise ValueError("rejected_legal_claim")
            if field_name in {"certified_signature_allowed", "certified_signature_created"}:
                raise ValueError("rejected_certified_signature_claim")
            raise ValueError("rejected_live_dependency")


def _reject_record_texts(record: object) -> None:
    for field_name in (
        "title",
        "summary",
        "source_title",
        "source_summary",
        "source_hint",
        "local_render_text",
        "demo_summary",
        "document_context_summary",
        "lineage_summary",
        "display_text",
    ):
        value = getattr(record, field_name, None)
        if isinstance(value, str):
            _reject_sensitive_text(value)
            _reject_prohibited_claim_text(value)


def _reject_sensitive_text(text: str) -> None:
    lowered = text.lower()
    if any(keyword in lowered for keyword in CREDENTIAL_KEYWORDS):
        raise ValueError("rejected_raw_credentials")
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        raise ValueError("rejected_sensitive_raw_payload")


def _reject_prohibited_claim_text(text: str) -> None:
    lowered = text.lower()
    if (
        any(pattern.search(lowered) for pattern in POSITIVE_OCR_PATTERNS)
        and "no ocr was performed" not in lowered
        and "no ocr performed" not in lowered
        and "ocr was not performed" not in lowered
    ):
        raise ValueError("rejected_ocr_dependency")
    if (
        any(pattern.search(lowered) for pattern in POSITIVE_LEGAL_ADVICE_PATTERNS)
        and "no legal advice" not in lowered
        and "not legal advice" not in lowered
    ):
        raise ValueError("rejected_legal_claim")
    if (
        any(pattern.search(lowered) for pattern in POSITIVE_SIGNATURE_PATTERNS)
        and "no certified signature" not in lowered
        and "no legal signature" not in lowered
        and "not a legal signature" not in lowered
    ):
        raise ValueError("rejected_certified_signature_claim")


def _validate_fixture(fixture: DocumentReviewDemoFixture) -> None:
    if fixture.source_type not in ALLOWED_DEMO_SOURCE_TYPES:
        raise ValueError("rejected_live_document_source")
    if fixture.source_category not in ALLOWED_DEMO_SOURCE_CATEGORIES:
        raise ValueError("rejected_invalid_source_category")
    if fixture.live_document_read_used:
        raise ValueError("rejected_live_document_source")
    if fixture.ocr_performed:
        raise ValueError("rejected_ocr_dependency")
    if fixture.source_payload is not None:
        raise ValueError("rejected_raw_payload_not_allowed")
    for text in (fixture.document_title, fixture.safe_summary, fixture.source_hint):
        _reject_sensitive_text(text)
        _reject_prohibited_claim_text(text)


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
