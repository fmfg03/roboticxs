from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.async_delegation_authority import (
    AsyncDelegationAuthorityState,
    AsyncDelegationCompletionEvent,
    build_completion_event,
    serialize_async_delegation_authority_state,
)
from app.followup_delegation_authority import FollowUpDelegationRegistry, FollowUpDelegationRequestRecord
from app.proactive_delegation_adapter import (
    PROACTIVE_DELEGATION_ADAPTER_STAGE,
    ProactiveDelegationAdapterRecord,
)


PROACTIVE_EXECUTION_SKELETON_STAGE = "123P"
PROACTIVE_EXECUTION_MODE = "deterministic_local"
ALLOWED_TASK_CLASSES = frozenset(
    {
        "FOLLOWUP_DEEPER_SUMMARY",
        "FOLLOWUP_EXTRACT_QUESTIONS",
        "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        "FOLLOWUP_COMPARE_PRIOR_VERSION",
    }
)
REJECTED_ADAPTER_STATUSES = frozenset(
    {
        "rejected_invalid_lineage",
        "rejected_missing_owner_authorization",
        "rejected_unsupported_task_class",
        "rejected_sensitive_data",
        "rejected_cancelled_selection",
    }
)
ATTEMPT_STATUSES = frozenset(
    {
        "completed_candidate_created",
        "failure_candidate_created",
        "duplicate_existing",
        "rejected_invalid_lineage",
        "rejected_unsupported_task_class",
        "rejected_sensitive_data",
        "rejected_live_dependency",
    }
)
EVENT_TYPES_BY_STATUS = {
    "completed": "proactive_execution_completed",
    "failed": "proactive_execution_failed",
}
DEFAULT_QUESTIONS = (
    "What context is missing?",
    "What should the owner confirm before action?",
    "What source should be reviewed next?",
)
CHECKLIST_BY_INTENT = {
    "review_document": (
        "Review the source summary for key obligations and risks.",
        "Confirm whether any missing clauses require manual inspection.",
        "Decide whether a human reviewer should inspect the full source next.",
    ),
    "review_boundary": (
        "Verify the boundary concern described in the source summary.",
        "Confirm which authority limit applies before any later action.",
        "Escalate to explicit human review before any external effect.",
    ),
    "review_memory_gap": (
        "Identify the missing context referenced by the proactive signal.",
        "Confirm whether the gap is real or only a stale snapshot artifact.",
        "Decide what source should be reviewed before any memory action.",
    ),
    "prepare_checklist": (
        "Review the source summary for the next required administrative step.",
        "Confirm what deadline or dependency the owner must validate.",
        "Capture any missing context before any later execution stage.",
    ),
}


@dataclass(frozen=True, slots=True)
class ProactiveExecutionFixture:
    fixture_id: str
    owner_id: str
    robot_id: str
    allowed_task_classes: tuple[str, ...]
    deterministic_payloads: dict[str, str] = field(default_factory=dict)
    compare_prior_version_fixture_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProactiveExecutionEventCandidateRecord:
    event_candidate_id: str
    owner_id: str
    robot_id: str
    proactive_execution_attempt_id: str
    proactive_delegation_adapter_id: str
    delegation_packet_id: str
    delegation_handle_id: str
    event_type: str
    event_status: str
    result_payload: dict[str, object]
    failure_reason: str | None
    retry_allowed: bool
    source_stage: str
    execution_stage: str
    compatible_with_async_completion_event_shape: bool
    inbox_inserted: bool
    result_surface_created: bool
    telegram_delivered: bool
    memory_mutated: bool
    external_written: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.event_type not in {"proactive_execution_completed", "proactive_execution_failed"}:
            raise ValueError("rejected_invalid_event_type")
        if self.event_status not in {"completed", "failed"}:
            raise ValueError("rejected_invalid_event_status")
        if self.source_stage != PROACTIVE_DELEGATION_ADAPTER_STAGE:
            raise ValueError("rejected_invalid_source_stage")
        if self.execution_stage != PROACTIVE_EXECUTION_SKELETON_STAGE:
            raise ValueError("rejected_invalid_execution_stage")
        if self.compatible_with_async_completion_event_shape is not True:
            raise ValueError("rejected_incompatible_async_completion_shape")
        if any(
            (
                self.inbox_inserted,
                self.result_surface_created,
                self.telegram_delivered,
                self.memory_mutated,
                self.external_written,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(frozen=True, slots=True)
class ProactiveExecutionAttemptRecord:
    proactive_execution_attempt_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    proactive_delegation_adapter_id: str
    delegation_packet_id: str
    delegation_handle_id: str
    proactive_adapter_id: str
    delivery_record_id: str
    suggestion_surface_id: str
    opportunity_id: str
    candidate_source_id: str
    source_authorization_id: str
    followup_intent_review_record_id: str
    followup_plan_id: str
    followup_choice_surface_id: str
    followup_selection_id: str
    explicit_owner_delegation_authorization_id: str
    source_stage: str
    detection_stage: str
    suggestion_stage: str
    adapter_stage: str
    delegation_adapter_stage: str
    execution_stage: str
    mapped_task_class: str
    execution_mode: str
    attempt_status: str
    completion_event_candidate_id: str | None
    failure_event_candidate_id: str | None
    result_summary: str | None
    failure_reason: str | None
    inbox_insert_allowed: bool
    result_surface_allowed: bool
    telegram_delivery_allowed: bool
    worker_dispatch_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    live_connector_allowed: bool
    external_write_allowed: bool
    memory_write_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.source_stage != "118P":
            raise ValueError("rejected_invalid_source_stage")
        if self.detection_stage != "119P":
            raise ValueError("rejected_invalid_detection_stage")
        if self.suggestion_stage != "120P":
            raise ValueError("rejected_invalid_suggestion_stage")
        if self.adapter_stage != "121P":
            raise ValueError("rejected_invalid_adapter_stage")
        if self.delegation_adapter_stage != "122P":
            raise ValueError("rejected_invalid_delegation_adapter_stage")
        if self.execution_stage != PROACTIVE_EXECUTION_SKELETON_STAGE:
            raise ValueError("rejected_invalid_execution_stage")
        if self.execution_mode != PROACTIVE_EXECUTION_MODE:
            raise ValueError("rejected_invalid_execution_mode")
        if self.attempt_status not in ATTEMPT_STATUSES:
            raise ValueError("rejected_invalid_attempt_status")
        if any(
            (
                self.inbox_insert_allowed,
                self.result_surface_allowed,
                self.telegram_delivery_allowed,
                self.worker_dispatch_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.live_connector_allowed,
                self.external_write_allowed,
                self.memory_write_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ProactiveExecutionRegistry:
    attempts_by_id: dict[str, ProactiveExecutionAttemptRecord] = field(default_factory=dict)
    attempt_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)
    events_by_id: dict[str, ProactiveExecutionEventCandidateRecord] = field(default_factory=dict)
    event_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_attempt(self, record: ProactiveExecutionAttemptRecord) -> ProactiveExecutionAttemptRecord:
        self.attempts_by_id[record.proactive_execution_attempt_id] = record
        self.attempt_ids_by_dedupe_key[record.dedupe_key] = record.proactive_execution_attempt_id
        return record

    def get_attempt(self, proactive_execution_attempt_id: str) -> ProactiveExecutionAttemptRecord | None:
        return self.attempts_by_id.get(proactive_execution_attempt_id)

    def get_attempt_by_dedupe_key(self, dedupe_key: str) -> ProactiveExecutionAttemptRecord | None:
        record_id = self.attempt_ids_by_dedupe_key.get(dedupe_key)
        if record_id is None:
            return None
        return self.attempts_by_id.get(record_id)

    def list_attempts(self) -> tuple[ProactiveExecutionAttemptRecord, ...]:
        return tuple(self.attempts_by_id[key] for key in sorted(self.attempts_by_id))

    def store_event(self, record: ProactiveExecutionEventCandidateRecord) -> ProactiveExecutionEventCandidateRecord:
        self.events_by_id[record.event_candidate_id] = record
        self.event_ids_by_dedupe_key[record.dedupe_key] = record.event_candidate_id
        return record

    def get_event(self, event_candidate_id: str) -> ProactiveExecutionEventCandidateRecord | None:
        return self.events_by_id.get(event_candidate_id)

    def list_events(self) -> tuple[ProactiveExecutionEventCandidateRecord, ...]:
        return tuple(self.events_by_id[key] for key in sorted(self.events_by_id))


def execute_proactive_delegation_skeleton(
    *,
    proactive_delegation_adapter_record: object,
    followup_registry: FollowUpDelegationRegistry,
    fixture: ProactiveExecutionFixture,
    execution_registry: ProactiveExecutionRegistry,
    created_at: str,
) -> ProactiveExecutionAttemptRecord:
    adapter = _coerce_adapter_record(proactive_delegation_adapter_record, fixture)
    dedupe_key = _attempt_dedupe_key(adapter=adapter, fixture=fixture)
    existing = execution_registry.get_attempt_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    attempt_id = _stable_id("proactive_execution_attempt", dedupe_key)
    rejection_status = _adapter_rejection_status(adapter=adapter, fixture=fixture)
    if rejection_status is not None:
        return execution_registry.store_attempt(
            _rejected_attempt(
                attempt_id=attempt_id,
                adapter=adapter,
                attempt_status=rejection_status,
                failure_reason=_failure_reason_for_attempt_status(rejection_status),
                dedupe_key=dedupe_key,
                created_at=created_at,
            )
        )

    followup_record, authority_state = _resolve_registered_followup_delegation(
        adapter=adapter,
        followup_registry=followup_registry,
    )
    if followup_record is None or authority_state is None:
        return execution_registry.store_attempt(
            _rejected_attempt(
                attempt_id=attempt_id,
                adapter=adapter,
                attempt_status="rejected_invalid_lineage",
                failure_reason="missing_registered_followup_delegation",
                dedupe_key=dedupe_key,
                created_at=created_at,
            )
        )

    completion_status, result_payload, failure_reason, reason_code = _deterministic_result(
        adapter=adapter,
        followup_record=followup_record,
        fixture=fixture,
    )
    completion_event = build_completion_event(
        authority_state=authority_state,
        completion_status=completion_status,
        source_stage=PROACTIVE_EXECUTION_SKELETON_STAGE,
        completion_payload_summary=result_payload,
        reason_code=reason_code,
    )
    event_record = execution_registry.store_event(
        _event_candidate_record(
            adapter=adapter,
            attempt_id=attempt_id,
            completion_event=completion_event,
            completion_status=completion_status,
            result_payload=result_payload,
            failure_reason=failure_reason,
            created_at=created_at,
        )
    )
    attempt_status = (
        "completed_candidate_created"
        if completion_status == "completed"
        else "failure_candidate_created"
    )
    return execution_registry.store_attempt(
        ProactiveExecutionAttemptRecord(
            proactive_execution_attempt_id=attempt_id,
            owner_id=adapter.owner_id,
            robot_id=adapter.robot_id,
            chat_id=adapter.chat_id,
            proactive_delegation_adapter_id=adapter.proactive_delegation_adapter_id,
            delegation_packet_id=adapter.delegation_packet_id or "",
            delegation_handle_id=adapter.delegation_handle_id or "",
            proactive_adapter_id=adapter.proactive_adapter_id,
            delivery_record_id=adapter.delivery_record_id,
            suggestion_surface_id=adapter.suggestion_surface_id,
            opportunity_id=adapter.opportunity_id,
            candidate_source_id=adapter.candidate_source_id,
            source_authorization_id=adapter.source_authorization_id,
            followup_intent_review_record_id=adapter.followup_intent_review_record_id,
            followup_plan_id=adapter.followup_plan_id,
            followup_choice_surface_id=adapter.followup_choice_surface_id,
            followup_selection_id=adapter.followup_selection_id,
            explicit_owner_delegation_authorization_id=adapter.explicit_owner_delegation_authorization_id,
            source_stage=adapter.source_stage,
            detection_stage=adapter.detection_stage,
            suggestion_stage=adapter.suggestion_stage,
            adapter_stage=adapter.adapter_stage,
            delegation_adapter_stage=adapter.delegation_adapter_stage,
            execution_stage=PROACTIVE_EXECUTION_SKELETON_STAGE,
            mapped_task_class=adapter.mapped_task_class,
            execution_mode=PROACTIVE_EXECUTION_MODE,
            attempt_status=attempt_status,
            completion_event_candidate_id=event_record.event_candidate_id if completion_status == "completed" else None,
            failure_event_candidate_id=event_record.event_candidate_id if completion_status == "failed" else None,
            result_summary=None if completion_status == "failed" else str(result_payload.get("result_summary")),
            failure_reason=failure_reason,
            inbox_insert_allowed=False,
            result_surface_allowed=False,
            telegram_delivery_allowed=False,
            worker_dispatch_allowed=False,
            model_call_allowed=False,
            tool_call_allowed=False,
            live_connector_allowed=False,
            external_write_allowed=False,
            memory_write_allowed=False,
            dedupe_key=dedupe_key,
            lineage_summary=_attempt_lineage_summary(
                adapter=adapter,
                followup_record=followup_record,
                authority_state=authority_state,
                event_record=event_record,
                fixture=fixture,
                attempt_status=attempt_status,
            ),
            created_at=created_at,
        )
    )


def get_proactive_execution_attempt(
    *,
    execution_registry: ProactiveExecutionRegistry,
    proactive_execution_attempt_id: str,
) -> ProactiveExecutionAttemptRecord | None:
    return execution_registry.get_attempt(proactive_execution_attempt_id)


def get_proactive_execution_event_candidate(
    *,
    execution_registry: ProactiveExecutionRegistry,
    event_candidate_id: str,
) -> ProactiveExecutionEventCandidateRecord | None:
    return execution_registry.get_event(event_candidate_id)


def list_proactive_execution_attempts(
    *,
    execution_registry: ProactiveExecutionRegistry,
) -> tuple[ProactiveExecutionAttemptRecord, ...]:
    return execution_registry.list_attempts()


def list_proactive_execution_event_candidates(
    *,
    execution_registry: ProactiveExecutionRegistry,
) -> tuple[ProactiveExecutionEventCandidateRecord, ...]:
    return execution_registry.list_events()


def _coerce_adapter_record(
    proactive_delegation_adapter_record: object,
    fixture: ProactiveExecutionFixture,
) -> ProactiveDelegationAdapterRecord:
    if isinstance(proactive_delegation_adapter_record, ProactiveDelegationAdapterRecord):
        return proactive_delegation_adapter_record
    return ProactiveDelegationAdapterRecord(
        proactive_delegation_adapter_id=_stable_id("proactive_delegation_adapter", "unknown"),
        owner_id=fixture.owner_id,
        robot_id=fixture.robot_id,
        chat_id="",
        proactive_adapter_id="",
        delivery_record_id="",
        suggestion_surface_id="",
        opportunity_id="",
        candidate_source_id="",
        source_authorization_id="",
        source_stage="118P",
        detection_stage="119P",
        suggestion_stage="120P",
        adapter_stage="121P",
        delegation_adapter_stage="122P",
        followup_intent_review_record_id="",
        followup_plan_id="",
        followup_choice_surface_id="",
        followup_selection_id="",
        explicit_owner_delegation_authorization_id="",
        normalized_intent_kind="summarize_context",
        selected_option_id="",
        mapped_task_class="",
        delegation_packet_id=None,
        delegation_handle_id=None,
        adapter_status="rejected_invalid_lineage",
        uses_existing_delegation_authority=True,
        execution_allowed=False,
        worker_dispatch_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        live_connector_allowed=False,
        telegram_send_allowed=False,
        memory_write_allowed=False,
        external_write_allowed=False,
        dedupe_key=_stable_id("proactive_delegation_adapter", "unknown-dedupe"),
        lineage_summary={},
        created_at="",
    )


def _adapter_rejection_status(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    fixture: ProactiveExecutionFixture,
) -> str | None:
    if adapter.delegation_adapter_stage != PROACTIVE_DELEGATION_ADAPTER_STAGE:
        return "rejected_invalid_lineage"
    if adapter.adapter_status in REJECTED_ADAPTER_STATUSES:
        if adapter.adapter_status == "rejected_unsupported_task_class":
            return "rejected_unsupported_task_class"
        if adapter.adapter_status == "rejected_sensitive_data":
            return "rejected_sensitive_data"
        return "rejected_invalid_lineage"
    if adapter.adapter_status != "delegated_registered":
        return "rejected_invalid_lineage"
    if not adapter.delegation_packet_id or not adapter.delegation_handle_id:
        return "rejected_invalid_lineage"
    if not adapter.explicit_owner_delegation_authorization_id:
        return "rejected_invalid_lineage"
    if adapter.owner_id != fixture.owner_id or adapter.robot_id != fixture.robot_id:
        return "rejected_invalid_lineage"
    if adapter.mapped_task_class not in ALLOWED_TASK_CLASSES:
        return "rejected_unsupported_task_class"
    if adapter.mapped_task_class not in fixture.allowed_task_classes:
        return "rejected_unsupported_task_class"
    if any(
        (
            adapter.execution_allowed,
            adapter.worker_dispatch_allowed,
            adapter.model_call_allowed,
            adapter.tool_call_allowed,
            adapter.live_connector_allowed,
            adapter.telegram_send_allowed,
            adapter.memory_write_allowed,
            adapter.external_write_allowed,
        )
    ):
        return "rejected_live_dependency"
    proactive_lineage = adapter.lineage_summary.get("upstream_lineage")
    if not isinstance(proactive_lineage, dict):
        return "rejected_invalid_lineage"
    proactive_adapter_lineage = proactive_lineage.get("proactive_adapter")
    followup_lineage = proactive_lineage.get("followup_delegation")
    if not isinstance(proactive_adapter_lineage, dict) or not isinstance(followup_lineage, dict):
        return "rejected_invalid_lineage"
    if proactive_adapter_lineage.get("adapter_stage") != "121P":
        return "rejected_invalid_lineage"
    if followup_lineage.get("followup_delegation_stage") != "111P":
        return "rejected_invalid_lineage"
    if followup_lineage.get("async_delegation_stage") != "102P":
        return "rejected_invalid_lineage"
    source_upstream = proactive_adapter_lineage.get("upstream_lineage")
    if not isinstance(source_upstream, dict):
        return "rejected_invalid_lineage"
    opportunity_lineage = source_upstream.get("opportunity")
    source_lineage = source_upstream.get("source")
    if not isinstance(opportunity_lineage, dict) or not isinstance(source_lineage, dict):
        return "rejected_invalid_lineage"
    if bool(opportunity_lineage.get("sensitive_data_blocked")):
        return "rejected_sensitive_data"
    if bool(source_lineage.get("live_connector_allowed")) or bool(source_lineage.get("external_read_allowed")):
        return "rejected_live_dependency"
    if bool(opportunity_lineage.get("live_connector_allowed")):
        return "rejected_live_dependency"
    if bool(opportunity_lineage.get("model_calls_required")) or bool(opportunity_lineage.get("tool_calls_required")):
        return "rejected_live_dependency"
    return None


def _resolve_registered_followup_delegation(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    followup_registry: FollowUpDelegationRegistry,
) -> tuple[FollowUpDelegationRequestRecord | None, AsyncDelegationAuthorityState | None]:
    for record in followup_registry.list_records():
        if (
            record.async_packet_id == adapter.delegation_packet_id
            and record.async_handle_id == adapter.delegation_handle_id
            and record.selection_id == adapter.followup_selection_id
        ):
            authority_state = followup_registry.get_authority_state(record.followup_delegation_id)
            if authority_state is None:
                return None, None
            if _followup_authority_block_reason(record=record, authority_state=authority_state, adapter=adapter) is not None:
                return None, None
            return record, authority_state
    return None, None


def _followup_authority_block_reason(
    *,
    record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
    adapter: ProactiveDelegationAdapterRecord,
) -> str | None:
    if record.status != "registered":
        return "invalid_followup_delegation_status"
    if record.owner_id != adapter.owner_id or record.robot_id != adapter.robot_id:
        return "invalid_followup_owner_or_robot"
    if record.telegram_chat_id != adapter.chat_id:
        return "invalid_followup_chat"
    if record.followup_task_class != adapter.mapped_task_class:
        return "invalid_followup_task_class"
    packet = authority_state.packet
    handle = authority_state.handle
    if authority_state.stage != "102P" or handle is None:
        return "missing_async_authority_lineage"
    if packet.state != "registered" or handle.status != "registered":
        return "async_authority_not_registered"
    if packet.source_stage != "111P":
        return "invalid_async_source_stage"
    if packet.task_class != "async_delegation" or handle.task_class != "async_delegation":
        return "invalid_async_task_class"
    if packet.execution_authorized or handle.execution_authorized:
        return "execution_authority_expanded"
    if packet.provider_call_authorized or handle.provider_call_authorized:
        return "live_model_or_tool_requested"
    if packet.external_effect_authorized or handle.external_effect_authorized:
        return "external_effect_requested"
    if packet.live_dispatch_authorized or handle.live_dispatch_authorized or handle.dispatch_authorized:
        return "live_dispatch_requested"
    if packet.authority_expanded or handle.authority_expanded:
        return "authority_expanded"
    return None


def _deterministic_result(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    followup_record: FollowUpDelegationRequestRecord,
    fixture: ProactiveExecutionFixture,
) -> tuple[str, dict[str, object], str | None, str]:
    payload_text = fixture.deterministic_payloads.get(adapter.mapped_task_class)
    source_summary = _source_summary(adapter)
    source_title = _source_title(adapter)
    trigger_reason = _trigger_reason(adapter)
    if adapter.mapped_task_class == "FOLLOWUP_COMPARE_PRIOR_VERSION":
        prior_fixture_id = _prior_version_fixture_id(adapter)
        if prior_fixture_id and prior_fixture_id in set(fixture.compare_prior_version_fixture_ids):
            result_payload = {
                "result_summary": payload_text
                or f"Compared local prior version fixture {prior_fixture_id} against {source_title}.",
                "comparison_fixture_id": prior_fixture_id,
                "source_summary": source_summary,
                "trigger_reason": trigger_reason,
                "followup_selection_id": adapter.followup_selection_id,
            }
            return "completed", result_payload, None, "completed_local_proactive_compare_prior_version"
        result_payload = {
            "result_summary": "Prior version fixture is unavailable for deterministic local comparison.",
            "comparison_fixture_id": prior_fixture_id,
            "source_summary": source_summary,
            "trigger_reason": trigger_reason,
            "followup_selection_id": adapter.followup_selection_id,
        }
        return "failed", result_payload, "missing_local_prior_version_fixture", "failed_local_prior_version_unavailable"

    if adapter.mapped_task_class == "FOLLOWUP_DEEPER_SUMMARY":
        result_payload = {
            "result_summary": payload_text
            or f"Summary: {source_summary} Trigger: {trigger_reason}. Intent: {adapter.normalized_intent_kind}.",
            "source_title": source_title,
            "source_summary": source_summary,
            "trigger_reason": trigger_reason,
            "followup_selection_id": adapter.followup_selection_id,
        }
        return "completed", result_payload, None, "completed_local_proactive_summary"

    if adapter.mapped_task_class == "FOLLOWUP_EXTRACT_QUESTIONS":
        result_payload = {
            "result_summary": payload_text or "Prepared deterministic follow-up questions from the proactive lineage.",
            "questions": list(DEFAULT_QUESTIONS),
            "source_title": source_title,
            "source_summary": source_summary,
            "trigger_reason": trigger_reason,
            "followup_selection_id": adapter.followup_selection_id,
        }
        return "completed", result_payload, None, "completed_local_proactive_questions"

    checklist = CHECKLIST_BY_INTENT.get(
        adapter.normalized_intent_kind,
        (
            "Review the proactive source summary.",
            "Confirm what the owner must validate next.",
            "Keep the result local until a later authorized routing stage.",
        ),
    )
    result_payload = {
        "result_summary": payload_text or "Prepared deterministic human review checklist from the proactive lineage.",
        "checklist": list(checklist),
        "source_title": source_title,
        "source_summary": source_summary,
        "trigger_reason": trigger_reason,
        "followup_selection_id": adapter.followup_selection_id,
    }
    return "completed", result_payload, None, "completed_local_proactive_checklist"


def _event_candidate_record(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    attempt_id: str,
    completion_event: AsyncDelegationCompletionEvent,
    completion_status: str,
    result_payload: dict[str, object],
    failure_reason: str | None,
    created_at: str,
) -> ProactiveExecutionEventCandidateRecord:
    dedupe_key = _stable_id(
        "proactive_execution_event_candidate",
        adapter.proactive_delegation_adapter_id,
        completion_event.handle_id,
        completion_status,
    )
    return ProactiveExecutionEventCandidateRecord(
        event_candidate_id=_stable_id("proactive_execution_event_candidate_id", dedupe_key),
        owner_id=adapter.owner_id,
        robot_id=adapter.robot_id,
        proactive_execution_attempt_id=attempt_id,
        proactive_delegation_adapter_id=adapter.proactive_delegation_adapter_id,
        delegation_packet_id=adapter.delegation_packet_id or "",
        delegation_handle_id=adapter.delegation_handle_id or "",
        event_type=EVENT_TYPES_BY_STATUS[completion_status],
        event_status=completion_status,
        result_payload={
            "async_completion_event": completion_event,
            "result_payload": result_payload,
        },
        failure_reason=failure_reason,
        retry_allowed=False,
        source_stage=PROACTIVE_DELEGATION_ADAPTER_STAGE,
        execution_stage=PROACTIVE_EXECUTION_SKELETON_STAGE,
        compatible_with_async_completion_event_shape=True,
        inbox_inserted=False,
        result_surface_created=False,
        telegram_delivered=False,
        memory_mutated=False,
        external_written=False,
        dedupe_key=dedupe_key,
        lineage_summary={
            "delegation_adapter_stage": "122P",
            "execution_stage": PROACTIVE_EXECUTION_SKELETON_STAGE,
            "async_completion_event_id": completion_event.event_id,
            "handle_id": completion_event.handle_id,
            "delegation_id": completion_event.delegation_id,
            "completion_status": completion_event.completion_status,
            "reason_code": completion_event.reason_code,
            "owner_id": adapter.owner_id,
            "robot_id": adapter.robot_id,
            "upstream_lineage": adapter.lineage_summary,
        },
        created_at=created_at,
    )


def _attempt_lineage_summary(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    followup_record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
    event_record: ProactiveExecutionEventCandidateRecord,
    fixture: ProactiveExecutionFixture,
    attempt_status: str,
) -> dict[str, object]:
    serialized_state = serialize_async_delegation_authority_state(authority_state)
    return {
        "execution_stage": PROACTIVE_EXECUTION_SKELETON_STAGE,
        "execution_mode": PROACTIVE_EXECUTION_MODE,
        "attempt_status": attempt_status,
        "fixture_id": fixture.fixture_id,
        "owner_id": adapter.owner_id,
        "robot_id": adapter.robot_id,
        "chat_id": adapter.chat_id,
        "delegation_packet_id": adapter.delegation_packet_id,
        "delegation_handle_id": adapter.delegation_handle_id,
        "event_candidate_id": event_record.event_candidate_id,
        "async_authority_stage": authority_state.stage,
        "async_packet_summary": serialized_state.get("packet"),
        "async_handle_summary": serialized_state.get("handle"),
        "followup_delegation_id": followup_record.followup_delegation_id,
        "followup_delegation_stage": followup_record.lineage_summary.get("followup_delegation_stage"),
        "cost_preflight_request_id": followup_record.lineage_summary.get("cost_preflight_request_id"),
        "approval_packet_id": followup_record.lineage_summary.get("approval_packet_id"),
        "approval_resume_token_id": followup_record.lineage_summary.get("approval_resume_token_id"),
        "upstream_lineage": {
            "proactive_delegation_adapter": adapter.lineage_summary,
            "followup_delegation": followup_record.lineage_summary,
            "event_candidate": event_record.lineage_summary,
        },
    }


def _rejected_attempt(
    *,
    attempt_id: str,
    adapter: ProactiveDelegationAdapterRecord,
    attempt_status: str,
    failure_reason: str,
    dedupe_key: str,
    created_at: str,
) -> ProactiveExecutionAttemptRecord:
    return ProactiveExecutionAttemptRecord(
        proactive_execution_attempt_id=attempt_id,
        owner_id=adapter.owner_id,
        robot_id=adapter.robot_id,
        chat_id=adapter.chat_id,
        proactive_delegation_adapter_id=adapter.proactive_delegation_adapter_id,
        delegation_packet_id=adapter.delegation_packet_id or "",
        delegation_handle_id=adapter.delegation_handle_id or "",
        proactive_adapter_id=adapter.proactive_adapter_id,
        delivery_record_id=adapter.delivery_record_id,
        suggestion_surface_id=adapter.suggestion_surface_id,
        opportunity_id=adapter.opportunity_id,
        candidate_source_id=adapter.candidate_source_id,
        source_authorization_id=adapter.source_authorization_id,
        followup_intent_review_record_id=adapter.followup_intent_review_record_id,
        followup_plan_id=adapter.followup_plan_id,
        followup_choice_surface_id=adapter.followup_choice_surface_id,
        followup_selection_id=adapter.followup_selection_id,
        explicit_owner_delegation_authorization_id=adapter.explicit_owner_delegation_authorization_id,
        source_stage=adapter.source_stage,
        detection_stage=adapter.detection_stage,
        suggestion_stage=adapter.suggestion_stage,
        adapter_stage=adapter.adapter_stage,
        delegation_adapter_stage=PROACTIVE_DELEGATION_ADAPTER_STAGE,
        execution_stage=PROACTIVE_EXECUTION_SKELETON_STAGE,
        mapped_task_class=adapter.mapped_task_class,
        execution_mode=PROACTIVE_EXECUTION_MODE,
        attempt_status=attempt_status,
        completion_event_candidate_id=None,
        failure_event_candidate_id=None,
        result_summary=None,
        failure_reason=failure_reason,
        inbox_insert_allowed=False,
        result_surface_allowed=False,
        telegram_delivery_allowed=False,
        worker_dispatch_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        live_connector_allowed=False,
        external_write_allowed=False,
        memory_write_allowed=False,
        dedupe_key=dedupe_key,
        lineage_summary={
            "execution_stage": PROACTIVE_EXECUTION_SKELETON_STAGE,
            "execution_mode": PROACTIVE_EXECUTION_MODE,
            "attempt_status": attempt_status,
            "upstream_lineage": adapter.lineage_summary,
        },
        created_at=created_at,
    )


def _failure_reason_for_attempt_status(attempt_status: str) -> str:
    mapping = {
        "rejected_invalid_lineage": "invalid_proactive_delegation_lineage",
        "rejected_unsupported_task_class": "unsupported_proactive_task_class",
        "rejected_sensitive_data": "sensitive_data_blocked",
        "rejected_live_dependency": "live_dependency_not_allowed",
    }
    return mapping[attempt_status]


def _attempt_dedupe_key(
    *,
    adapter: ProactiveDelegationAdapterRecord,
    fixture: ProactiveExecutionFixture,
) -> str:
    return _stable_id(
        "proactive_execution_attempt",
        adapter.proactive_delegation_adapter_id,
        adapter.delegation_packet_id,
        adapter.delegation_handle_id,
        adapter.explicit_owner_delegation_authorization_id,
        adapter.mapped_task_class,
        fixture.fixture_id,
    )


def _source_title(adapter: ProactiveDelegationAdapterRecord) -> str:
    proactive_lineage = adapter.lineage_summary.get("upstream_lineage", {}).get("proactive_adapter", {})
    opportunity_lineage = proactive_lineage.get("upstream_lineage", {}).get("opportunity", {})
    return str(opportunity_lineage.get("title") or "proactive source")


def _source_summary(adapter: ProactiveDelegationAdapterRecord) -> str:
    proactive_lineage = adapter.lineage_summary.get("upstream_lineage", {}).get("proactive_adapter", {})
    opportunity_lineage = proactive_lineage.get("upstream_lineage", {}).get("opportunity", {})
    if opportunity_lineage.get("summary"):
        return str(opportunity_lineage["summary"])
    source_lineage = proactive_lineage.get("upstream_lineage", {}).get("source", {})
    return str(source_lineage.get("source_summary") or "No additional safe summary is available.")


def _trigger_reason(adapter: ProactiveDelegationAdapterRecord) -> str:
    proactive_lineage = adapter.lineage_summary.get("upstream_lineage", {}).get("proactive_adapter", {})
    opportunity_lineage = proactive_lineage.get("upstream_lineage", {}).get("opportunity", {})
    return str(opportunity_lineage.get("trigger_reason") or "deterministic_local_execution")


def _prior_version_fixture_id(adapter: ProactiveDelegationAdapterRecord) -> str | None:
    selection_lineage = adapter.lineage_summary.get("upstream_lineage", {}).get("selection", {})
    choice_surface_lineage = selection_lineage.get("upstream_lineage", {})
    metadata_by_ref = choice_surface_lineage.get("option_metadata_by_ref")
    if not isinstance(metadata_by_ref, dict):
        return None
    selected = metadata_by_ref.get(adapter.selected_option_id)
    if not isinstance(selected, dict):
        return None
    prior_fixture_id = selected.get("prior_version_fixture_id")
    if isinstance(prior_fixture_id, str) and prior_fixture_id:
        return prior_fixture_id
    return None


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
