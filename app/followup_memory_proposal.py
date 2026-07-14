from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.followup_completion_loop import FOLLOWUP_COMPLETION_LOOP_STAGE, FollowUpCompletionLoopRegistry, FollowUpCompletionLoopRouteRecord
from app.followup_result_acknowledgement import (
    FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
    FollowUpResultAcknowledgementRecord,
)
from app.telegram_async_result_delivery import TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE, TelegramAsyncResultDeliveryRecord


FOLLOWUP_MEMORY_PROPOSAL_STAGE = "115P"
PROPOSAL_TYPES = frozenset(
    {
        "user_preference_candidate",
        "work_preference_candidate",
        "business_context_candidate",
        "task_memory_candidate",
        "boundary_memory_candidate",
        "no_memory_candidate",
    }
)
PROPOSAL_STATUSES = frozenset(
    {
        "pending_user_review",
        "no_memory_recommended",
        "rejected_source",
    }
)
CONFIDENCE_LEVELS = frozenset({"high", "medium", "low", "not_applicable"})
SENSITIVE_KEYWORDS = (
    "health",
    "medical",
    "diagnosis",
    "political",
    "religion",
    "race",
    "ethnicity",
    "sexual orientation",
    "geolocation",
    "criminal",
    "bank account",
    "password",
    "secret",
    "credential",
)


@dataclass(frozen=True, slots=True)
class FollowUpMemoryProposalCandidateRecord:
    proposal_id: str
    owner_id: str
    robot_id: str
    acknowledgement_id: str
    route_id: str
    delivery_record_id: str
    surface_id: str
    inbox_record_id: str
    event_candidate_id: str
    attempt_id: str
    delegation_id: str
    packet_id: str
    handle_id: str
    source_stage: str
    proposal_stage: str
    proposal_type: str
    proposed_memory_text: str | None
    confidence: str
    review_reason: str
    status: str
    memory_write_allowed: bool
    telegram_approval_surface_allowed: bool
    user_approved: bool
    memory_center_mutated: bool
    live_send_allowed: bool
    sensitive_data_blocked: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.source_stage != FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE:
            raise ValueError("115P memory proposals must originate from 114P acknowledgement records.")
        if self.proposal_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
            raise ValueError("115P memory proposals must identify the 115P stage.")
        if self.proposal_type not in PROPOSAL_TYPES:
            raise ValueError("Unsupported 115P proposal type.")
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ValueError("Unsupported 115P confidence level.")
        if self.status not in PROPOSAL_STATUSES:
            raise ValueError("Unsupported 115P proposal status.")
        if self.memory_write_allowed is not False:
            raise ValueError("115P proposals must not authorize memory writes.")
        if self.telegram_approval_surface_allowed is not False:
            raise ValueError("115P proposals must not authorize Telegram approval surfaces.")
        if self.user_approved is not False:
            raise ValueError("115P proposals must not mark user approval.")
        if self.memory_center_mutated is not False:
            raise ValueError("115P proposals must not mutate Memory Center.")
        if self.live_send_allowed is not False:
            raise ValueError("115P proposals must not authorize live sends.")


@dataclass(slots=True)
class FollowUpMemoryProposalRegistry:
    proposals_by_id: dict[str, FollowUpMemoryProposalCandidateRecord] = field(default_factory=dict)

    def get_followup_memory_proposal_candidate(self, proposal_id: str) -> FollowUpMemoryProposalCandidateRecord | None:
        return self.proposals_by_id.get(proposal_id)

    def store(self, record: FollowUpMemoryProposalCandidateRecord) -> FollowUpMemoryProposalCandidateRecord:
        self.proposals_by_id[record.proposal_id] = record
        return record

    def list_followup_memory_proposal_candidates(self) -> tuple[FollowUpMemoryProposalCandidateRecord, ...]:
        return tuple(self.proposals_by_id[key] for key in sorted(self.proposals_by_id))


def create_followup_memory_proposal_candidate(
    *,
    acknowledgement_record: object,
    route_registry: FollowUpCompletionLoopRegistry,
    proposal_registry: FollowUpMemoryProposalRegistry,
) -> FollowUpMemoryProposalCandidateRecord:
    if not isinstance(acknowledgement_record, FollowUpResultAcknowledgementRecord):
        proposal_id = _stable_id("followup_memory_proposal", "unknown")
        existing = proposal_registry.get_followup_memory_proposal_candidate(proposal_id)
        if existing is not None:
            return existing
        return proposal_registry.store(
            _rejected_record(
                proposal_id=proposal_id,
                acknowledgement_record=None,
                rejection_reason="rejected_unknown_114p_acknowledgement_record",
            )
        )

    proposal_id = _proposal_id(acknowledgement_record=acknowledgement_record)
    existing = proposal_registry.get_followup_memory_proposal_candidate(proposal_id)
    if existing is not None:
        return existing

    route = route_registry.get_followup_completion_route(acknowledgement_record.route_id)
    if route is None:
        return proposal_registry.store(
            _rejected_record(
                proposal_id=proposal_id,
                acknowledgement_record=acknowledgement_record,
                rejection_reason="rejected_unknown_113p_route",
            )
        )

    delivery = route_registry.delivery_registry.get_delivery(acknowledgement_record.delivery_record_id)
    if delivery is None:
        return proposal_registry.store(
            _rejected_record(
                proposal_id=proposal_id,
                acknowledgement_record=acknowledgement_record,
                rejection_reason="rejected_unknown_delivery_record",
            )
        )

    rejection_reason = _validation_error(
        acknowledgement_record=acknowledgement_record,
        route=route,
        delivery=delivery,
        route_registry=route_registry,
    )
    if rejection_reason is not None:
        return proposal_registry.store(
            _rejected_record(
                proposal_id=proposal_id,
                acknowledgement_record=acknowledgement_record,
                rejection_reason=rejection_reason,
            )
        )

    proposal_type, proposed_memory_text, confidence, review_reason, status, sensitive_data_blocked = _classify_proposal(
        delivery_text=delivery.text,
        route=route,
    )
    return proposal_registry.store(
        FollowUpMemoryProposalCandidateRecord(
            proposal_id=proposal_id,
            owner_id=acknowledgement_record.owner_id,
            robot_id=acknowledgement_record.robot_id,
            acknowledgement_id=acknowledgement_record.acknowledgement_id,
            route_id=acknowledgement_record.route_id,
            delivery_record_id=acknowledgement_record.delivery_record_id,
            surface_id=acknowledgement_record.surface_id,
            inbox_record_id=acknowledgement_record.inbox_record_id,
            event_candidate_id=acknowledgement_record.event_candidate_id,
            attempt_id=acknowledgement_record.attempt_id,
            delegation_id=acknowledgement_record.delegation_id,
            packet_id=acknowledgement_record.packet_id,
            handle_id=acknowledgement_record.handle_id,
            source_stage=FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
            proposal_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
            proposal_type=proposal_type,
            proposed_memory_text=proposed_memory_text,
            confidence=confidence,
            review_reason=review_reason,
            status=status,
            memory_write_allowed=False,
            telegram_approval_surface_allowed=False,
            user_approved=False,
            memory_center_mutated=False,
            live_send_allowed=False,
            sensitive_data_blocked=sensitive_data_blocked,
            dedupe_key=_dedupe_key(acknowledgement_record=acknowledgement_record),
            lineage_summary=_lineage_summary(
                acknowledgement_record=acknowledgement_record,
                route=route,
                delivery=delivery,
            ),
            created_at=_created_at(proposal_registry=proposal_registry),
            rejection_reason=None,
        )
    )


def get_followup_memory_proposal_candidate(
    *,
    proposal_registry: FollowUpMemoryProposalRegistry,
    proposal_id: str,
) -> FollowUpMemoryProposalCandidateRecord | None:
    return proposal_registry.get_followup_memory_proposal_candidate(proposal_id)


def list_followup_memory_proposal_candidates(
    *,
    proposal_registry: FollowUpMemoryProposalRegistry,
) -> tuple[FollowUpMemoryProposalCandidateRecord, ...]:
    return proposal_registry.list_followup_memory_proposal_candidates()


def _validation_error(
    *,
    acknowledgement_record: FollowUpResultAcknowledgementRecord,
    route: FollowUpCompletionLoopRouteRecord,
    delivery: TelegramAsyncResultDeliveryRecord,
    route_registry: FollowUpCompletionLoopRegistry,
) -> str | None:
    if acknowledgement_record.source_stage != FOLLOWUP_COMPLETION_LOOP_STAGE:
        return "rejected_non_113p_followup_completion_route"
    if acknowledgement_record.acknowledged_stage != FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE:
        return "rejected_non_114p_acknowledgement_lineage"
    if acknowledgement_record.status != "acknowledged":
        if acknowledgement_record.status == "dismissed":
            return "rejected_dismissed_acknowledgement_source"
        if acknowledgement_record.status == "lineage_summary_requested":
            return "rejected_lineage_summary_only_acknowledgement_source"
        return f"rejected_invalid_acknowledgement_status_{acknowledgement_record.status}"
    if acknowledgement_record.action != "acknowledge_followup_result":
        if acknowledgement_record.action == "dismiss_followup_result":
            return "rejected_dismissed_acknowledgement_source"
        if acknowledgement_record.action == "request_followup_result_lineage_summary":
            return "rejected_lineage_summary_only_acknowledgement_source"
        return "rejected_invalid_acknowledgement_action"
    if route.status != "routed" or route.routed_stage != FOLLOWUP_COMPLETION_LOOP_STAGE:
        return "rejected_non_113p_followup_completion_route"
    if acknowledgement_record.owner_id != route.owner_id or acknowledgement_record.owner_id != delivery.owner_id:
        return "rejected_owner_mismatch"
    if acknowledgement_record.robot_id != route.robot_id or acknowledgement_record.robot_id != delivery.robot_id:
        return "rejected_robot_mismatch"
    if acknowledgement_record.chat_id != delivery.telegram_chat_id:
        return "rejected_chat_mismatch"
    if acknowledgement_record.route_id != route.route_id:
        return "rejected_route_lineage_mismatch"
    if acknowledgement_record.delivery_record_id != delivery.delivery_id or route.delivery_record_id != delivery.delivery_id:
        return "rejected_delivery_lineage_mismatch"
    if acknowledgement_record.surface_id != route.surface_id or acknowledgement_record.surface_id != delivery.surface_id:
        return "rejected_surface_lineage_mismatch"
    if acknowledgement_record.inbox_record_id != route.inbox_record_id:
        return "rejected_inbox_lineage_mismatch"
    if acknowledgement_record.event_candidate_id != route.event_candidate_id:
        return "rejected_event_candidate_lineage_mismatch"
    if acknowledgement_record.attempt_id != route.attempt_id:
        return "rejected_attempt_lineage_mismatch"
    if acknowledgement_record.delegation_id != route.delegation_id:
        return "rejected_delegation_lineage_mismatch"
    if acknowledgement_record.packet_id != route.packet_id:
        return "rejected_packet_lineage_mismatch"
    if acknowledgement_record.handle_id != route.handle_id:
        return "rejected_handle_lineage_mismatch"
    if delivery.lineage_summary.get("delivery_stage") != TELEGRAM_ASYNC_RESULT_DELIVERY_STAGE:
        return "rejected_non_105p_delivery_record"
    upstream = route.lineage_summary.get("upstream_lineage")
    if not isinstance(upstream, dict):
        return "rejected_missing_100p_114p_lineage"
    if route_registry.get_surface(route.surface_id or "") is None:
        return "rejected_surface_lineage_mismatch"
    if route_registry.get_inbox_record(route.inbox_record_id or "") is None:
        return "rejected_inbox_lineage_mismatch"
    return None


def _classify_proposal(
    *,
    delivery_text: str,
    route: FollowUpCompletionLoopRouteRecord,
) -> tuple[str, str | None, str, str, str, bool]:
    text = " ".join(delivery_text.split())
    lowered = text.lower()
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        return (
            "no_memory_candidate",
            None,
            "not_applicable",
            "Sensitive personal attribute content is not eligible for a memory proposal at 115P.",
            "no_memory_recommended",
            True,
        )
    if lowered in {
        "fixture deeper summary.",
        "fixture deeper summary",
        "fixture review questions.",
        "fixture review questions",
        "fixture review checklist.",
        "fixture review checklist",
        "prior version unavailable in local execution fixture.",
        "prior version unavailable in local execution fixture",
    }:
        return (
            "no_memory_candidate",
            None,
            "not_applicable",
            "The acknowledged result is too generic to justify a durable memory proposal.",
            "no_memory_recommended",
            False,
        )
    if _is_boundary_candidate(lowered):
        memory_text = _boundary_memory_text(text)
        return (
            "boundary_memory_candidate",
            memory_text,
            "high",
            "The acknowledged result states a reusable robot boundary or operating limit.",
            "pending_user_review",
            False,
        )
    if "prefer" in lowered or "preference" in lowered:
        if "work" in lowered or "review" in lowered or "format" in lowered:
            return (
                "work_preference_candidate",
                _sentence_or_text(text),
                "medium",
                "The acknowledged result states a reusable work preference.",
                "pending_user_review",
                False,
            )
        return (
            "user_preference_candidate",
            _sentence_or_text(text),
            "medium",
            "The acknowledged result states a reusable user preference.",
            "pending_user_review",
            False,
        )
    if any(token in lowered for token in ("checklist", "question", "summary", "next step", "follow-up task", "action item")):
        concise = _task_memory_text(text, route)
        return (
            "task_memory_candidate",
            concise,
            "low" if concise == text else "medium",
            "The acknowledged result contains reusable task context from the completed follow-up.",
            "pending_user_review",
            False,
        )
    if any(token in lowered for token in ("client", "contract", "vendor", "nda", "project", "business", "company")):
        return (
            "business_context_candidate",
            _sentence_or_text(text),
            "medium",
            "The acknowledged result contains durable business context worth later review.",
            "pending_user_review",
            False,
        )
    return (
        "no_memory_candidate",
        None,
        "not_applicable",
        "The acknowledged result does not contain durable, safe memory material for later approval.",
        "no_memory_recommended",
        False,
    )


def _lineage_summary(
    *,
    acknowledgement_record: FollowUpResultAcknowledgementRecord,
    route: FollowUpCompletionLoopRouteRecord,
    delivery: TelegramAsyncResultDeliveryRecord,
) -> dict[str, object]:
    route_upstream = route.lineage_summary.get("upstream_lineage")
    return {
        "proposal_stage": FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        "acknowledgement_stage": FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
        "followup_completion_loop_stage": FOLLOWUP_COMPLETION_LOOP_STAGE,
        "delivery_stage": delivery.lineage_summary.get("delivery_stage"),
        "acknowledgement_id": acknowledgement_record.acknowledgement_id,
        "acknowledgement_action": acknowledgement_record.action,
        "callback_action": acknowledgement_record.action,
        "route_id": route.route_id,
        "delivery_record_id": delivery.delivery_id,
        "surface_id": route.surface_id,
        "inbox_record_id": route.inbox_record_id,
        "event_candidate_id": route.event_candidate_id,
        "attempt_id": route.attempt_id,
        "delegation_id": route.delegation_id,
        "packet_id": route.packet_id,
        "handle_id": route.handle_id,
        "owner_id": route.owner_id,
        "robot_id": route.robot_id,
        "acknowledgement_lineage": {
            **acknowledgement_record.lineage_metadata,
            "callback_action": acknowledgement_record.action,
        },
        "route_lineage": route.lineage_summary,
        "cost_preflight_summary": _nested_dict(route_upstream, "upstream_lineage", "cost_preflight_summary"),
        "task_cost_request_summary": _nested_dict(route_upstream, "upstream_lineage", "task_cost_request_summary"),
        "budget_policy_summary": _nested_dict(route_upstream, "upstream_lineage", "budget_policy_summary"),
        "approval_packet_id": _nested_value(route_upstream, "upstream_lineage", "approval_packet_id"),
        "followup_delegation_stage": _nested_value(route_upstream, "upstream_lineage", "followup_delegation_stage"),
        "followup_execution_stage": _nested_value(route_upstream, "followup_execution_stage"),
        "async_authority_state": route.lineage_summary.get("async_authority_state"),
    }


def _rejected_record(
    *,
    proposal_id: str,
    acknowledgement_record: FollowUpResultAcknowledgementRecord | None,
    rejection_reason: str,
) -> FollowUpMemoryProposalCandidateRecord:
    return FollowUpMemoryProposalCandidateRecord(
        proposal_id=proposal_id,
        owner_id="" if acknowledgement_record is None else acknowledgement_record.owner_id,
        robot_id="" if acknowledgement_record is None else acknowledgement_record.robot_id,
        acknowledgement_id="" if acknowledgement_record is None else acknowledgement_record.acknowledgement_id,
        route_id="" if acknowledgement_record is None else acknowledgement_record.route_id,
        delivery_record_id="" if acknowledgement_record is None else acknowledgement_record.delivery_record_id,
        surface_id="" if acknowledgement_record is None else acknowledgement_record.surface_id,
        inbox_record_id="" if acknowledgement_record is None else acknowledgement_record.inbox_record_id,
        event_candidate_id="" if acknowledgement_record is None else acknowledgement_record.event_candidate_id,
        attempt_id="" if acknowledgement_record is None else acknowledgement_record.attempt_id,
        delegation_id="" if acknowledgement_record is None else acknowledgement_record.delegation_id,
        packet_id="" if acknowledgement_record is None else acknowledgement_record.packet_id,
        handle_id="" if acknowledgement_record is None else acknowledgement_record.handle_id,
        source_stage=FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
        proposal_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        proposal_type="no_memory_candidate",
        proposed_memory_text=None,
        confidence="not_applicable",
        review_reason="The source acknowledgement did not meet 115P eligibility requirements.",
        status="rejected_source",
        memory_write_allowed=False,
        telegram_approval_surface_allowed=False,
        user_approved=False,
        memory_center_mutated=False,
        live_send_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key=proposal_id,
        lineage_summary={
            "proposal_stage": FOLLOWUP_MEMORY_PROPOSAL_STAGE,
            "acknowledgement_id": None if acknowledgement_record is None else acknowledgement_record.acknowledgement_id,
        },
        created_at="proposal_rejected_local",
        rejection_reason=rejection_reason,
    )


def _proposal_id(*, acknowledgement_record: FollowUpResultAcknowledgementRecord) -> str:
    return _stable_id(
        "followup_memory_proposal",
        acknowledgement_record.acknowledgement_id,
        acknowledgement_record.route_id,
        acknowledgement_record.delivery_record_id,
        acknowledgement_record.action,
    )


def _dedupe_key(*, acknowledgement_record: FollowUpResultAcknowledgementRecord) -> str:
    return _stable_id(
        "followup_memory_proposal_dedupe",
        acknowledgement_record.acknowledgement_id,
        acknowledgement_record.route_id,
        acknowledgement_record.delivery_record_id,
    )


def _created_at(*, proposal_registry: FollowUpMemoryProposalRegistry) -> str:
    return f"proposal_local_{len(proposal_registry.proposals_by_id) + 1:04d}"


def _nested_value(data: object, *keys: str) -> object:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _nested_dict(data: object, *keys: str) -> dict[str, object] | None:
    current = _nested_value(data, *keys)
    return current if isinstance(current, dict) else None


def _is_boundary_candidate(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in (
            "ask before",
            "never execute",
            "never send",
            "do not use this source",
            "must not",
            "do not send",
            "do not use",
        )
    )


def _boundary_memory_text(text: str) -> str:
    return _sentence_or_text(text)


def _sentence_or_text(text: str) -> str:
    first_sentence = text.split(".")[0].strip()
    if first_sentence:
        return first_sentence + ("." if not first_sentence.endswith(".") else "")
    return text


def _task_memory_text(text: str, route: FollowUpCompletionLoopRouteRecord) -> str:
    summary = route.lineage_summary.get("surface_summary")
    if isinstance(summary, dict):
        title = summary.get("title")
        if isinstance(title, str) and title:
            return f"{title}: {_sentence_or_text(text)}"
    return _sentence_or_text(text)


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(
        NAMESPACE_URL,
        "|".join("" if part is None else str(part) for part in parts),
    ).hex[:12]
