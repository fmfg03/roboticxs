from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.async_delegation_authority import (
    AsyncDelegationAuthorityState,
    AsyncDelegationCompletionEvent,
    build_completion_event,
    serialize_async_delegation_authority_state,
)
from app.followup_delegation_authority import (
    FOLLOWUP_DELEGATION_AUTHORITY_STAGE,
    FOLLOWUP_PREPARATION_EFFECT_CLASS,
    FollowUpDelegationRegistry,
    FollowUpDelegationRequestRecord,
)


FOLLOWUP_EXECUTION_SKELETON_STAGE = "112P"
FOLLOWUP_EXECUTION_ATTEMPT_STATUSES = frozenset(
    {"completed_candidate", "failed_candidate", "duplicate", "blocked"}
)
ALLOWED_FOLLOWUP_TASK_CLASSES = frozenset(
    {
        "FOLLOWUP_DEEPER_SUMMARY",
        "FOLLOWUP_EXTRACT_QUESTIONS",
        "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        "FOLLOWUP_COMPARE_PRIOR_VERSION",
    }
)
FORBIDDEN_REQUEST_FLAGS = frozenset(
    {
        "authority_expansion_requested",
        "live_dispatch_requested",
        "requires_tool_call",
        "tool_call_requested",
        "requires_model_call",
        "model_call_requested",
        "requires_memory_mutation",
        "memory_mutation_requested",
        "requires_external_effect",
        "external_effect_requested",
        "requires_telegram_send",
        "telegram_send_requested",
    }
)
DEFAULT_SUCCESS_PAYLOADS = {
    "FOLLOWUP_DEEPER_SUMMARY": "Deeper summary prepared from the approved follow-up context.",
    "FOLLOWUP_EXTRACT_QUESTIONS": "Questions extracted from the approved follow-up context.",
    "FOLLOWUP_HUMAN_REVIEW_CHECKLIST": "Human review checklist prepared from the approved follow-up context.",
}
DEFAULT_FAILURE_PAYLOADS = {
    "FOLLOWUP_COMPARE_PRIOR_VERSION": "Prior version unavailable in local execution fixture.",
}


@dataclass(frozen=True, slots=True)
class FollowUpExecutionFixture:
    fixture_id: str
    owner_id: str
    robot_id: str
    allowed_task_classes: tuple[str, ...]
    deterministic_payloads: dict[str, str]
    force_failure_task_classes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FollowUpExecutionAttemptRecord:
    execution_attempt_id: str
    followup_delegation_id: str
    async_packet_id: str
    async_handle_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    followup_task_class: str
    status: str
    result_summary: str | None
    failure_reason: str | None
    completion_event_candidate: AsyncDelegationCompletionEvent | None
    failure_event_candidate: AsyncDelegationCompletionEvent | None
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in FOLLOWUP_EXECUTION_ATTEMPT_STATUSES:
            raise ValueError("Unsupported 112P follow-up execution status.")


@dataclass(frozen=True, slots=True)
class FollowUpExecutionSkeletonResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("112P only supports local Telegram-compatible response envelopes.")
        if self.send_allowed is not False:
            raise ValueError("112P response envelopes must keep send_allowed false.")


@dataclass(slots=True)
class FollowUpExecutionAttemptRegistry:
    records_by_id: dict[str, FollowUpExecutionAttemptRecord] = field(default_factory=dict)

    def get_record(self, execution_attempt_id: str) -> FollowUpExecutionAttemptRecord | None:
        return self.records_by_id.get(execution_attempt_id)

    def store(self, record: FollowUpExecutionAttemptRecord) -> FollowUpExecutionAttemptRecord:
        self.records_by_id[record.execution_attempt_id] = record
        return record

    def list_records(self) -> tuple[FollowUpExecutionAttemptRecord, ...]:
        return tuple(self.records_by_id[key] for key in sorted(self.records_by_id))


def execute_followup_delegation_skeleton(
    *,
    followup_delegation_record: object,
    followup_registry: FollowUpDelegationRegistry,
    fixture: FollowUpExecutionFixture,
    attempt_registry: FollowUpExecutionAttemptRegistry,
) -> FollowUpExecutionAttemptRecord:
    if not isinstance(followup_delegation_record, FollowUpDelegationRequestRecord):
        attempt_id = _stable_id("followup_execution_attempt", "unknown", fixture.fixture_id)
        existing = attempt_registry.get_record(attempt_id)
        if existing is not None:
            return existing
        return attempt_registry.store(
            _blocked_attempt(
                attempt_id=attempt_id,
                record=None,
                fixture=fixture,
                rejection_reason="blocked_unknown_followup_delegation_record",
            )
        )

    attempt_id = _attempt_id(followup_delegation_record=followup_delegation_record, fixture=fixture)
    existing = attempt_registry.get_record(attempt_id)
    if existing is not None:
        return existing

    rejection_reason = _delegation_block_reason(
        followup_delegation_record=followup_delegation_record,
        followup_registry=followup_registry,
        fixture=fixture,
    )
    if rejection_reason is not None:
        return attempt_registry.store(
            _blocked_attempt(
                attempt_id=attempt_id,
                record=followup_delegation_record,
                fixture=fixture,
                rejection_reason=rejection_reason,
            )
        )

    authority_state = followup_registry.get_authority_state(
        followup_delegation_record.followup_delegation_id
    )
    assert authority_state is not None

    completion_status, payload_text, reason_code = _deterministic_execution_result(
        followup_delegation_record=followup_delegation_record,
        fixture=fixture,
    )
    event = build_completion_event(
        authority_state=authority_state,
        completion_status=completion_status,
        source_stage=FOLLOWUP_EXECUTION_SKELETON_STAGE,
        completion_payload_summary={
            "result_summary": payload_text,
            "followup_lineage": _safe_followup_lineage_summary(followup_delegation_record),
            "fixture_id": fixture.fixture_id,
        },
        reason_code=reason_code,
    )
    if completion_status == "completed":
        record = FollowUpExecutionAttemptRecord(
            execution_attempt_id=attempt_id,
            followup_delegation_id=followup_delegation_record.followup_delegation_id,
            async_packet_id=followup_delegation_record.async_packet_id or "",
            async_handle_id=followup_delegation_record.async_handle_id or "",
            owner_id=followup_delegation_record.owner_id,
            robot_id=followup_delegation_record.robot_id,
            telegram_chat_id=followup_delegation_record.telegram_chat_id,
            followup_task_class=followup_delegation_record.followup_task_class,
            status="completed_candidate",
            result_summary=payload_text,
            failure_reason=None,
            completion_event_candidate=event,
            failure_event_candidate=None,
            lineage_summary=_execution_lineage_summary(
                followup_delegation_record=followup_delegation_record,
                authority_state=authority_state,
                fixture=fixture,
                status="completed_candidate",
            ),
            rejection_reason=None,
        )
        return attempt_registry.store(record)

    record = FollowUpExecutionAttemptRecord(
        execution_attempt_id=attempt_id,
        followup_delegation_id=followup_delegation_record.followup_delegation_id,
        async_packet_id=followup_delegation_record.async_packet_id or "",
        async_handle_id=followup_delegation_record.async_handle_id or "",
        owner_id=followup_delegation_record.owner_id,
        robot_id=followup_delegation_record.robot_id,
        telegram_chat_id=followup_delegation_record.telegram_chat_id,
        followup_task_class=followup_delegation_record.followup_task_class,
        status="failed_candidate",
        result_summary=None,
        failure_reason=payload_text,
        completion_event_candidate=None,
        failure_event_candidate=event,
        lineage_summary=_execution_lineage_summary(
            followup_delegation_record=followup_delegation_record,
            authority_state=authority_state,
            fixture=fixture,
            status="failed_candidate",
        ),
        rejection_reason=None,
    )
    return attempt_registry.store(record)


def build_followup_execution_skeleton_response_envelope(
    record: FollowUpExecutionAttemptRecord,
) -> FollowUpExecutionSkeletonResponseEnvelope:
    if record.status == "completed_candidate":
        text = record.result_summary or "Local follow-up result candidate prepared."
    elif record.status == "failed_candidate":
        text = record.failure_reason or "Local follow-up result candidate failed."
    else:
        text = "No pude ejecutar ese seguimiento en este esqueleto local."
    return FollowUpExecutionSkeletonResponseEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=text,
        send_allowed=False,
    )


def _delegation_block_reason(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    followup_registry: FollowUpDelegationRegistry,
    fixture: FollowUpExecutionFixture,
) -> str | None:
    if followup_delegation_record.status != "registered":
        return f"blocked_followup_delegation_status_{followup_delegation_record.status}"
    if (
        not followup_delegation_record.async_packet_id
        or not followup_delegation_record.async_handle_id
    ):
        return "blocked_missing_async_packet_or_handle"
    if followup_delegation_record.followup_task_class not in ALLOWED_FOLLOWUP_TASK_CLASSES:
        return "blocked_unsupported_followup_task_class"
    if followup_delegation_record.owner_id != fixture.owner_id:
        return "blocked_owner_mismatch"
    if followup_delegation_record.robot_id != fixture.robot_id:
        return "blocked_robot_mismatch"
    if followup_delegation_record.followup_task_class not in fixture.allowed_task_classes:
        return "blocked_fixture_disallowed_task_class"
    if followup_delegation_record.lineage_summary.get("followup_delegation_stage") != FOLLOWUP_DELEGATION_AUTHORITY_STAGE:
        return "blocked_missing_111p_followup_lineage"

    authority_state = followup_registry.get_authority_state(
        followup_delegation_record.followup_delegation_id
    )
    if authority_state is None or authority_state.stage != "102P":
        return "blocked_missing_102p_async_lineage"
    handle = authority_state.handle
    packet = authority_state.packet
    if handle is None:
        return "blocked_missing_async_packet_or_handle"
    if followup_delegation_record.async_handle_id != handle.handle_id:
        return "blocked_missing_async_packet_or_handle"
    if followup_delegation_record.async_packet_id != f"{packet.delegation_id}:v{packet.packet_version}":
        return "blocked_missing_async_packet_or_handle"
    if packet.state != "registered" or handle.status != "registered":
        return "blocked_async_handle_not_registered"
    if packet.owner_id != followup_delegation_record.owner_id or handle.owner_id != followup_delegation_record.owner_id:
        return "blocked_owner_mismatch"
    if packet.robot_id != followup_delegation_record.robot_id or handle.robot_id != followup_delegation_record.robot_id:
        return "blocked_robot_mismatch"
    if packet.task_class != "async_delegation" or handle.task_class != "async_delegation":
        return "blocked_task_class_mismatch"
    if packet.source_stage != FOLLOWUP_DELEGATION_AUTHORITY_STAGE:
        return "blocked_missing_111p_followup_lineage"
    if packet.execution_authorized or handle.execution_authorized:
        return "blocked_execution_authority_expansion"
    if packet.provider_call_authorized or handle.provider_call_authorized:
        return "blocked_live_model_or_tool_request"
    if packet.external_effect_authorized or handle.external_effect_authorized:
        return "blocked_external_effect_request"
    if packet.live_dispatch_authorized or handle.live_dispatch_authorized or handle.dispatch_authorized:
        return "blocked_live_dispatch_request"
    if packet.authority_expanded or handle.authority_expanded:
        return "blocked_execution_authority_expansion"

    request_evidence = handle.original_request_evidence
    if not request_evidence:
        return "blocked_missing_111p_followup_lineage"
    request_payload = request_evidence.get("request_payload")
    if not isinstance(request_payload, dict):
        return "blocked_missing_111p_followup_lineage"
    if request_payload.get("followup_task_class") != followup_delegation_record.followup_task_class:
        return "blocked_task_class_mismatch"
    if request_payload.get("selection_id") != followup_delegation_record.selection_id:
        return "blocked_missing_111p_followup_lineage"
    if request_payload.get("effect_class") != FOLLOWUP_PREPARATION_EFFECT_CLASS:
        return "blocked_external_effect_request"
    if request_payload.get("send_allowed") is not False:
        return "blocked_external_effect_request"
    for flag in FORBIDDEN_REQUEST_FLAGS:
        if bool(request_payload.get(flag)) or bool(request_evidence.get(flag)):
            if "model_call" in flag or "tool_call" in flag:
                return "blocked_live_model_or_tool_request"
            if "memory_mutation" in flag:
                return "blocked_memory_mutation_request"
            if "telegram_send" in flag:
                return "blocked_external_effect_request"
            if "external_effect" in flag:
                return "blocked_external_effect_request"
            return "blocked_execution_authority_expansion"

    cost_lineage = _cost_lineage_block_reason(
        followup_delegation_record=followup_delegation_record,
        authority_state=authority_state,
    )
    if cost_lineage is not None:
        return cost_lineage
    approval_lineage = _approval_lineage_block_reason(
        followup_delegation_record=followup_delegation_record,
        authority_state=authority_state,
    )
    if approval_lineage is not None:
        return approval_lineage
    return None


def _cost_lineage_block_reason(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
) -> str | None:
    lineage = followup_delegation_record.lineage_summary
    cost_preflight_summary = lineage.get("cost_preflight_summary")
    task_cost_request_summary = lineage.get("task_cost_request_summary")
    budget_policy_summary = lineage.get("budget_policy_summary")
    if not isinstance(cost_preflight_summary, dict) or not isinstance(task_cost_request_summary, dict):
        return "blocked_missing_100p_cost_lineage"
    if not isinstance(budget_policy_summary, dict):
        return "blocked_missing_100p_cost_lineage"
    handle = authority_state.handle
    packet = authority_state.packet
    if handle is None:
        return "blocked_missing_async_packet_or_handle"
    if not handle.cost_preflight_evidence or not packet.cost_preflight_request_id:
        return "blocked_missing_100p_cost_lineage"
    if lineage.get("cost_preflight_request_id") != packet.cost_preflight_request_id:
        return "blocked_cost_preflight_request_mismatch"
    if cost_preflight_summary.get("request_id") != packet.cost_preflight_request_id:
        return "blocked_cost_preflight_request_mismatch"
    if task_cost_request_summary.get("request_id") != packet.cost_preflight_request_id:
        return "blocked_cost_preflight_request_mismatch"
    if handle.cost_preflight_request_id != packet.cost_preflight_request_id:
        return "blocked_cost_preflight_request_mismatch"
    if task_cost_request_summary.get("task_class") != "async_delegation":
        return "blocked_missing_100p_cost_lineage"
    if task_cost_request_summary.get("owner_id") != followup_delegation_record.owner_id:
        return "blocked_owner_mismatch"
    if task_cost_request_summary.get("robot_id") != followup_delegation_record.robot_id:
        return "blocked_robot_mismatch"
    if budget_policy_summary.get("owner_id") != followup_delegation_record.owner_id:
        return "blocked_owner_mismatch"
    if budget_policy_summary.get("robot_id") != followup_delegation_record.robot_id:
        return "blocked_robot_mismatch"
    request_route_mode = task_cost_request_summary.get("routing_mode")
    route_decision = cost_preflight_summary.get("route_decision")
    if not isinstance(route_decision, dict):
        return "blocked_route_model_mismatch"
    if request_route_mode != packet.request_snapshot.get("requested_route_mode"):
        return "blocked_route_model_mismatch"
    if route_decision.get("selected_model_id") != packet.selected_model_id:
        return "blocked_route_model_mismatch"
    if route_decision.get("selected_provider_id") != packet.selected_provider_id:
        return "blocked_route_model_mismatch"
    if handle.cost_preflight_evidence.get("estimated_cost_usd") in {None, 0, 0.0}:
        return "blocked_missing_100p_cost_lineage"
    return None


def _approval_lineage_block_reason(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
) -> str | None:
    lineage = followup_delegation_record.lineage_summary
    cost_preflight_summary = lineage.get("cost_preflight_summary")
    if not isinstance(cost_preflight_summary, dict):
        return "blocked_missing_100p_cost_lineage"
    requires_approval = cost_preflight_summary.get("decision") == "require_confirmation"
    handle = authority_state.handle
    if handle is None:
        return "blocked_missing_async_packet_or_handle"
    if not requires_approval:
        return None
    approval_packet_id = lineage.get("approval_packet_id")
    if not approval_packet_id:
        return "blocked_missing_required_101p_approval_lineage"
    approval = handle.approval_evidence
    if not isinstance(approval, dict):
        return "blocked_missing_required_101p_approval_lineage"
    if approval.get("action_type") != "async_delegation":
        return "blocked_generic_approval_evidence_does_not_authorize_execution"
    if approval.get("packet_id", approval.get("action_packet_id")) != approval_packet_id:
        return "blocked_missing_required_101p_approval_lineage"
    return None


def _deterministic_execution_result(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    fixture: FollowUpExecutionFixture,
) -> tuple[str, str, str]:
    task_class = followup_delegation_record.followup_task_class
    if task_class in fixture.force_failure_task_classes:
        return (
            "failed",
            fixture.deterministic_payloads.get(task_class)
            or DEFAULT_FAILURE_PAYLOADS.get(task_class)
            or "Deterministic local follow-up execution failed.",
            "failed_local_followup_execution",
        )
    if task_class == "FOLLOWUP_COMPARE_PRIOR_VERSION" and task_class not in fixture.deterministic_payloads:
        return (
            "failed",
            DEFAULT_FAILURE_PAYLOADS[task_class],
            "failed_local_prior_version_unavailable",
        )
    return (
        "completed",
        fixture.deterministic_payloads.get(task_class)
        or DEFAULT_SUCCESS_PAYLOADS.get(task_class)
        or "Deterministic local follow-up execution completed.",
        "completed_local_followup_execution",
    )


def _execution_lineage_summary(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    authority_state: AsyncDelegationAuthorityState,
    fixture: FollowUpExecutionFixture,
    status: str,
) -> dict[str, object]:
    serialized_state = serialize_async_delegation_authority_state(authority_state)
    packet = serialized_state["packet"]
    handle = serialized_state["handle"]
    return {
        "followup_execution_stage": FOLLOWUP_EXECUTION_SKELETON_STAGE,
        "followup_execution_status": status,
        "fixture_id": fixture.fixture_id,
        "owner_id": followup_delegation_record.owner_id,
        "robot_id": followup_delegation_record.robot_id,
        "telegram_chat_id": followup_delegation_record.telegram_chat_id,
        "followup_delegation_id": followup_delegation_record.followup_delegation_id,
        "followup_delegation_stage": followup_delegation_record.lineage_summary.get(
            "followup_delegation_stage"
        ),
        "async_delegation_stage": authority_state.stage,
        "async_packet_id": followup_delegation_record.async_packet_id,
        "async_handle_id": followup_delegation_record.async_handle_id,
        "async_packet_summary": packet,
        "async_handle_summary": handle,
        "upstream_lineage": followup_delegation_record.lineage_summary,
    }


def _safe_followup_lineage_summary(
    followup_delegation_record: FollowUpDelegationRequestRecord,
) -> dict[str, object]:
    lineage = followup_delegation_record.lineage_summary
    return {
        "followup_delegation_id": followup_delegation_record.followup_delegation_id,
        "followup_delegation_stage": lineage.get("followup_delegation_stage"),
        "selection_id": followup_delegation_record.selection_id,
        "choice_surface_id": followup_delegation_record.choice_surface_id,
        "draft_plan_id": followup_delegation_record.draft_plan_id,
        "followup_intent_id": lineage.get("followup_intent_id"),
        "acknowledgement_id": followup_delegation_record.acknowledgement_id,
        "delivery_id": followup_delegation_record.delivery_id,
        "source_surface_id": followup_delegation_record.source_surface_id,
        "inbox_record_id": followup_delegation_record.inbox_record_id,
        "owner_id": followup_delegation_record.owner_id,
        "robot_id": followup_delegation_record.robot_id,
        "cost_preflight_request_id": lineage.get("cost_preflight_request_id"),
        "approval_packet_id": lineage.get("approval_packet_id"),
        "approval_resume_token_id": lineage.get("approval_resume_token_id"),
        "async_packet_id": lineage.get("async_packet_id"),
        "async_handle_id": lineage.get("async_handle_id"),
    }


def _blocked_attempt(
    *,
    attempt_id: str,
    record: FollowUpDelegationRequestRecord | None,
    fixture: FollowUpExecutionFixture,
    rejection_reason: str,
) -> FollowUpExecutionAttemptRecord:
    return FollowUpExecutionAttemptRecord(
        execution_attempt_id=attempt_id,
        followup_delegation_id="" if record is None else record.followup_delegation_id,
        async_packet_id="" if record is None or record.async_packet_id is None else record.async_packet_id,
        async_handle_id="" if record is None or record.async_handle_id is None else record.async_handle_id,
        owner_id=fixture.owner_id if record is None else record.owner_id,
        robot_id=fixture.robot_id if record is None else record.robot_id,
        telegram_chat_id="" if record is None else record.telegram_chat_id,
        followup_task_class="" if record is None else record.followup_task_class,
        status="blocked",
        result_summary=None,
        failure_reason=None,
        completion_event_candidate=None,
        failure_event_candidate=None,
        lineage_summary={
            "followup_execution_stage": FOLLOWUP_EXECUTION_SKELETON_STAGE,
            "fixture_id": fixture.fixture_id,
            "upstream_lineage": None if record is None else record.lineage_summary,
        },
        rejection_reason=rejection_reason,
    )


def _attempt_id(
    *,
    followup_delegation_record: FollowUpDelegationRequestRecord,
    fixture: FollowUpExecutionFixture,
) -> str:
    return _stable_id(
        "followup_execution_attempt",
        followup_delegation_record.followup_delegation_id,
        followup_delegation_record.async_packet_id,
        followup_delegation_record.async_handle_id,
        followup_delegation_record.owner_id,
        followup_delegation_record.robot_id,
        followup_delegation_record.followup_task_class,
        fixture.fixture_id,
    )


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
