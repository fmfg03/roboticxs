from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.followup_memory_proposal import (
    CONFIDENCE_LEVELS,
    FOLLOWUP_MEMORY_PROPOSAL_STAGE,
    PROPOSAL_TYPES,
    SENSITIVE_KEYWORDS,
    FollowUpMemoryProposalCandidateRecord,
)
from app.followup_result_acknowledgement import FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE


TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE = "116P"
ALLOWED_APPROVAL_ACTIONS = frozenset(
    {
        "approve_memory_proposal",
        "reject_memory_proposal",
        "edit_memory_proposal_text",
        "request_memory_proposal_lineage_summary",
    }
)
SURFACE_STATUSES = frozenset({"rendered", "blocked"})
DECISION_STATUSES = frozenset(
    {
        "approved_pending_writeback",
        "rejected_no_write",
        "edited_pending_writeback",
        "lineage_summary_requested",
        "rejected_sensitive_edit",
        "blocked",
    }
)
TERMINAL_DECISION_STATUSES = frozenset(
    {
        "approved_pending_writeback",
        "rejected_no_write",
        "edited_pending_writeback",
    }
)


@dataclass(frozen=True, slots=True)
class TelegramMemoryProposalApprovalSelectionPayload:
    owner_id: str
    robot_id: str
    chat_id: str
    proposal_id: str
    surface_id: str
    action: str
    revised_proposed_memory_text: str | None = None

    def __post_init__(self) -> None:
        if self.action not in ALLOWED_APPROVAL_ACTIONS:
            raise ValueError("Unsupported 116P memory proposal approval action.")


@dataclass(frozen=True, slots=True)
class TelegramMemoryProposalApprovalSurfaceRecord:
    surface_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    proposal_id: str
    proposal_type: str
    proposed_memory_text: str | None
    confidence: str
    review_reason: str
    source_stage: str
    surface_stage: str
    allowed_actions: tuple[str, ...]
    telegram_transport: str
    live_send_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str
    status: str
    text: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.proposal_type not in PROPOSAL_TYPES:
            raise ValueError("Unsupported 116P proposal type.")
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ValueError("Unsupported 116P confidence level.")
        if self.source_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
            raise ValueError("116P approval surfaces must originate from 115P proposals.")
        if self.surface_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
            raise ValueError("116P approval surfaces must identify the 116P stage.")
        if self.status not in SURFACE_STATUSES:
            raise ValueError("Unsupported 116P surface status.")
        if tuple(self.allowed_actions) != tuple(sorted(ALLOWED_APPROVAL_ACTIONS)):
            raise ValueError("116P approval surfaces must expose the supported action set.")
        if self.telegram_transport != "injected_local_only":
            raise ValueError("116P approval surfaces must remain injected and local only.")
        if self.live_send_allowed is not False:
            raise ValueError("116P approval surfaces must not authorize live sends.")
        if self.memory_write_allowed is not False:
            raise ValueError("116P approval surfaces must not authorize memory writes.")
        if self.memory_center_mutated is not False:
            raise ValueError("116P approval surfaces must not mutate Memory Center.")
        if self.external_write_allowed is not False:
            raise ValueError("116P approval surfaces must not authorize external writes.")


@dataclass(frozen=True, slots=True)
class TelegramMemoryProposalApprovalDecisionRecord:
    decision_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    surface_id: str
    proposal_id: str
    action: str
    decision_status: str
    original_proposed_memory_text: str | None
    revised_proposed_memory_text: str | None
    source_stage: str
    decision_stage: str
    writeback_stage_authorized: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    external_write_allowed: bool
    live_send_allowed: bool
    sensitive_data_blocked: bool
    dedupe_key: str
    lineage_summary: str | None
    created_at: str
    response_text: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.action not in ALLOWED_APPROVAL_ACTIONS:
            raise ValueError("Unsupported 116P approval action.")
        if self.decision_status not in DECISION_STATUSES:
            raise ValueError("Unsupported 116P decision status.")
        if self.source_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
            raise ValueError("116P decisions must originate from 115P proposals.")
        if self.decision_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
            raise ValueError("116P decisions must identify the 116P stage.")
        if self.writeback_stage_authorized is not False:
            raise ValueError("116P decisions must not authorize writeback.")
        if self.memory_write_allowed is not False:
            raise ValueError("116P decisions must not authorize memory writes.")
        if self.memory_center_mutated is not False:
            raise ValueError("116P decisions must not mutate Memory Center.")
        if self.external_write_allowed is not False:
            raise ValueError("116P decisions must not authorize external writes.")
        if self.live_send_allowed is not False:
            raise ValueError("116P decisions must not authorize live sends.")


@dataclass(frozen=True, slots=True)
class TelegramMemoryProposalApprovalResponseEnvelope:
    channel: str
    chat_id: str
    text: str
    live_send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("116P only supports Telegram-compatible response envelopes.")
        if self.live_send_allowed is not False:
            raise ValueError("116P response envelopes must keep live_send_allowed false.")


@dataclass(slots=True)
class TelegramMemoryProposalApprovalRegistry:
    surfaces_by_id: dict[str, TelegramMemoryProposalApprovalSurfaceRecord] = field(default_factory=dict)
    decisions_by_id: dict[str, TelegramMemoryProposalApprovalDecisionRecord] = field(default_factory=dict)

    def store_surface(
        self,
        record: TelegramMemoryProposalApprovalSurfaceRecord,
    ) -> TelegramMemoryProposalApprovalSurfaceRecord:
        self.surfaces_by_id[record.surface_id] = record
        return record

    def store_decision(
        self,
        record: TelegramMemoryProposalApprovalDecisionRecord,
    ) -> TelegramMemoryProposalApprovalDecisionRecord:
        self.decisions_by_id[record.decision_id] = record
        return record

    def get_memory_proposal_approval_surface(
        self,
        surface_id: str,
    ) -> TelegramMemoryProposalApprovalSurfaceRecord | None:
        return self.surfaces_by_id.get(surface_id)

    def get_memory_proposal_approval_decision(
        self,
        decision_id: str,
    ) -> TelegramMemoryProposalApprovalDecisionRecord | None:
        return self.decisions_by_id.get(decision_id)

    def list_memory_proposal_approval_surfaces(
        self,
    ) -> tuple[TelegramMemoryProposalApprovalSurfaceRecord, ...]:
        return tuple(self.surfaces_by_id[key] for key in sorted(self.surfaces_by_id))

    def list_memory_proposal_approval_decisions(
        self,
    ) -> tuple[TelegramMemoryProposalApprovalDecisionRecord, ...]:
        return tuple(self.decisions_by_id[key] for key in sorted(self.decisions_by_id))

    def get_terminal_decision_for_proposal(
        self,
        proposal_id: str,
    ) -> TelegramMemoryProposalApprovalDecisionRecord | None:
        for record in self.list_memory_proposal_approval_decisions():
            if record.proposal_id == proposal_id and record.decision_status in TERMINAL_DECISION_STATUSES:
                return record
        return None


def render_memory_proposal_approval_surface(
    *,
    proposal_record: object,
    registry: TelegramMemoryProposalApprovalRegistry,
    chat_id: str | None = None,
) -> TelegramMemoryProposalApprovalSurfaceRecord:
    if not isinstance(proposal_record, FollowUpMemoryProposalCandidateRecord):
        surface_id = _stable_id("telegram_memory_proposal_surface", "unknown")
        existing = registry.get_memory_proposal_approval_surface(surface_id)
        if existing is not None:
            return existing
        return registry.store_surface(
            _blocked_surface_record(
                surface_id=surface_id,
                proposal_record=None,
                chat_id=chat_id or "",
                rejection_reason="rejected_unknown_115p_memory_proposal_record",
            )
        )

    inferred_chat_id = _proposal_chat_id(proposal_record)
    target_chat_id = inferred_chat_id if chat_id is None else chat_id
    surface_id = _surface_id(proposal_record=proposal_record, chat_id=str(target_chat_id or ""))
    existing = registry.get_memory_proposal_approval_surface(surface_id)
    if existing is not None:
        return existing

    rejection_reason = _proposal_validation_error(
        proposal_record=proposal_record,
        chat_id=str(target_chat_id or ""),
    )
    if rejection_reason is not None:
        return registry.store_surface(
            _blocked_surface_record(
                surface_id=surface_id,
                proposal_record=proposal_record,
                chat_id=str(target_chat_id or ""),
                rejection_reason=rejection_reason,
            )
        )

    assert isinstance(target_chat_id, str)
    return registry.store_surface(
        TelegramMemoryProposalApprovalSurfaceRecord(
            surface_id=surface_id,
            owner_id=proposal_record.owner_id,
            robot_id=proposal_record.robot_id,
            chat_id=target_chat_id,
            proposal_id=proposal_record.proposal_id,
            proposal_type=proposal_record.proposal_type,
            proposed_memory_text=proposal_record.proposed_memory_text,
            confidence=proposal_record.confidence,
            review_reason=proposal_record.review_reason,
            source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
            surface_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
            allowed_actions=tuple(sorted(ALLOWED_APPROVAL_ACTIONS)),
            telegram_transport="injected_local_only",
            live_send_allowed=False,
            memory_write_allowed=False,
            memory_center_mutated=False,
            external_write_allowed=False,
            dedupe_key=_stable_id("telegram_memory_proposal_surface_dedupe", proposal_record.proposal_id, target_chat_id),
            lineage_summary=_surface_lineage_summary(proposal_record=proposal_record, chat_id=target_chat_id),
            created_at=f"surface_local_{len(registry.surfaces_by_id) + 1:04d}",
            status="rendered",
            text=_surface_text(proposal_record=proposal_record),
            rejection_reason=None,
        )
    )


def bind_memory_proposal_approval_selection(
    *,
    proposal_record: object,
    surface_record: object,
    payload: TelegramMemoryProposalApprovalSelectionPayload,
    registry: TelegramMemoryProposalApprovalRegistry,
) -> TelegramMemoryProposalApprovalDecisionRecord:
    if not isinstance(payload, TelegramMemoryProposalApprovalSelectionPayload):
        raise TypeError("116P decision binding requires a TelegramMemoryProposalApprovalSelectionPayload.")

    decision_id = _decision_id(payload=payload)
    existing = registry.get_memory_proposal_approval_decision(decision_id)
    if existing is not None:
        return existing

    if not isinstance(proposal_record, FollowUpMemoryProposalCandidateRecord):
        return registry.store_decision(
            _blocked_decision_record(
                decision_id=decision_id,
                payload=payload,
                proposal_record=None,
                rejection_reason="rejected_unknown_115p_memory_proposal_record",
            )
        )

    if not isinstance(surface_record, TelegramMemoryProposalApprovalSurfaceRecord):
        return registry.store_decision(
            _blocked_decision_record(
                decision_id=decision_id,
                payload=payload,
                proposal_record=proposal_record,
                rejection_reason="rejected_unknown_surface_record",
            )
        )

    terminal = registry.get_terminal_decision_for_proposal(proposal_record.proposal_id)
    if terminal is not None and terminal.decision_id != decision_id:
        return registry.store_decision(
            _blocked_decision_record(
                decision_id=decision_id,
                payload=payload,
                proposal_record=proposal_record,
                rejection_reason="rejected_proposal_already_decided",
            )
        )

    validation_error = _decision_validation_error(
        proposal_record=proposal_record,
        surface_record=surface_record,
        payload=payload,
    )
    if validation_error is not None:
        return registry.store_decision(
            _blocked_decision_record(
                decision_id=decision_id,
                payload=payload,
                proposal_record=proposal_record,
                rejection_reason=validation_error,
            )
        )

    if payload.action == "request_memory_proposal_lineage_summary":
        summary = _lineage_summary_text(proposal_record=proposal_record, surface_record=surface_record)
        return registry.store_decision(
            TelegramMemoryProposalApprovalDecisionRecord(
                decision_id=decision_id,
                owner_id=proposal_record.owner_id,
                robot_id=proposal_record.robot_id,
                chat_id=surface_record.chat_id,
                surface_id=surface_record.surface_id,
                proposal_id=proposal_record.proposal_id,
                action=payload.action,
                decision_status="lineage_summary_requested",
                original_proposed_memory_text=proposal_record.proposed_memory_text,
                revised_proposed_memory_text=None,
                source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
                decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
                writeback_stage_authorized=False,
                memory_write_allowed=False,
                memory_center_mutated=False,
                external_write_allowed=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key=_decision_dedupe_key(payload=payload),
                lineage_summary=summary,
                created_at=f"decision_local_{len(registry.decisions_by_id) + 1:04d}",
                response_text=summary,
                rejection_reason=None,
            )
        )

    if payload.action == "edit_memory_proposal_text":
        revised_text = _normalize_text(payload.revised_proposed_memory_text)
        assert revised_text is not None
        if _contains_sensitive_data(revised_text):
            return registry.store_decision(
                TelegramMemoryProposalApprovalDecisionRecord(
                    decision_id=decision_id,
                    owner_id=proposal_record.owner_id,
                    robot_id=proposal_record.robot_id,
                    chat_id=surface_record.chat_id,
                    surface_id=surface_record.surface_id,
                    proposal_id=proposal_record.proposal_id,
                    action=payload.action,
                    decision_status="rejected_sensitive_edit",
                    original_proposed_memory_text=proposal_record.proposed_memory_text,
                    revised_proposed_memory_text=revised_text,
                    source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
                    decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
                    writeback_stage_authorized=False,
                    memory_write_allowed=False,
                    memory_center_mutated=False,
                    external_write_allowed=False,
                    live_send_allowed=False,
                    sensitive_data_blocked=True,
                    dedupe_key=_decision_dedupe_key(payload=payload),
                    lineage_summary=None,
                    created_at=f"decision_local_{len(registry.decisions_by_id) + 1:04d}",
                    response_text="I blocked that edited memory proposal locally because it contains sensitive data.",
                    rejection_reason="rejected_sensitive_edit",
                )
            )
        return registry.store_decision(
            TelegramMemoryProposalApprovalDecisionRecord(
                decision_id=decision_id,
                owner_id=proposal_record.owner_id,
                robot_id=proposal_record.robot_id,
                chat_id=surface_record.chat_id,
                surface_id=surface_record.surface_id,
                proposal_id=proposal_record.proposal_id,
                action=payload.action,
                decision_status="edited_pending_writeback",
                original_proposed_memory_text=proposal_record.proposed_memory_text,
                revised_proposed_memory_text=revised_text,
                source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
                decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
                writeback_stage_authorized=False,
                memory_write_allowed=False,
                memory_center_mutated=False,
                external_write_allowed=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key=_decision_dedupe_key(payload=payload),
                lineage_summary=None,
                created_at=f"decision_local_{len(registry.decisions_by_id) + 1:04d}",
                response_text="I recorded your revised memory proposal locally. It is still pending later writeback review.",
                rejection_reason=None,
            )
        )

    if payload.action == "reject_memory_proposal":
        return registry.store_decision(
            TelegramMemoryProposalApprovalDecisionRecord(
                decision_id=decision_id,
                owner_id=proposal_record.owner_id,
                robot_id=proposal_record.robot_id,
                chat_id=surface_record.chat_id,
                surface_id=surface_record.surface_id,
                proposal_id=proposal_record.proposal_id,
                action=payload.action,
                decision_status="rejected_no_write",
                original_proposed_memory_text=proposal_record.proposed_memory_text,
                revised_proposed_memory_text=None,
                source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
                decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
                writeback_stage_authorized=False,
                memory_write_allowed=False,
                memory_center_mutated=False,
                external_write_allowed=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key=_decision_dedupe_key(payload=payload),
                lineage_summary=None,
                created_at=f"decision_local_{len(registry.decisions_by_id) + 1:04d}",
                response_text="I recorded your rejection locally. No memory write was authorized.",
                rejection_reason=None,
            )
        )

    return registry.store_decision(
        TelegramMemoryProposalApprovalDecisionRecord(
            decision_id=decision_id,
            owner_id=proposal_record.owner_id,
            robot_id=proposal_record.robot_id,
            chat_id=surface_record.chat_id,
            surface_id=surface_record.surface_id,
            proposal_id=proposal_record.proposal_id,
            action=payload.action,
            decision_status="approved_pending_writeback",
            original_proposed_memory_text=proposal_record.proposed_memory_text,
            revised_proposed_memory_text=None,
            source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
            decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
            writeback_stage_authorized=False,
            memory_write_allowed=False,
            memory_center_mutated=False,
            external_write_allowed=False,
            live_send_allowed=False,
            sensitive_data_blocked=False,
            dedupe_key=_decision_dedupe_key(payload=payload),
            lineage_summary=None,
            created_at=f"decision_local_{len(registry.decisions_by_id) + 1:04d}",
            response_text="I recorded your approval locally. The proposal is pending later writeback review only.",
            rejection_reason=None,
        )
    )


def build_memory_proposal_approval_response_envelope(
    record: TelegramMemoryProposalApprovalDecisionRecord,
) -> TelegramMemoryProposalApprovalResponseEnvelope:
    return TelegramMemoryProposalApprovalResponseEnvelope(
        channel="telegram",
        chat_id=record.chat_id,
        text=record.response_text,
        live_send_allowed=False,
    )


def get_memory_proposal_approval_surface(
    *,
    registry: TelegramMemoryProposalApprovalRegistry,
    surface_id: str,
) -> TelegramMemoryProposalApprovalSurfaceRecord | None:
    return registry.get_memory_proposal_approval_surface(surface_id)


def get_memory_proposal_approval_decision(
    *,
    registry: TelegramMemoryProposalApprovalRegistry,
    decision_id: str,
) -> TelegramMemoryProposalApprovalDecisionRecord | None:
    return registry.get_memory_proposal_approval_decision(decision_id)


def list_memory_proposal_approval_surfaces(
    *,
    registry: TelegramMemoryProposalApprovalRegistry,
) -> tuple[TelegramMemoryProposalApprovalSurfaceRecord, ...]:
    return registry.list_memory_proposal_approval_surfaces()


def list_memory_proposal_approval_decisions(
    *,
    registry: TelegramMemoryProposalApprovalRegistry,
) -> tuple[TelegramMemoryProposalApprovalDecisionRecord, ...]:
    return registry.list_memory_proposal_approval_decisions()


def _proposal_validation_error(
    *,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    chat_id: str,
) -> str | None:
    if proposal_record.source_stage != FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE:
        return "rejected_non_114p_acknowledgement_lineage"
    if proposal_record.proposal_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_non_115p_proposal_stage"
    if proposal_record.status == "no_memory_recommended":
        return "rejected_no_memory_recommended_proposal"
    if proposal_record.status == "rejected_source":
        return "rejected_rejected_source_proposal"
    if proposal_record.status != "pending_user_review":
        return f"rejected_non_pending_proposal_status_{proposal_record.status}"
    if proposal_record.proposal_type == "no_memory_candidate":
        return "rejected_no_memory_candidate_proposal"
    if proposal_record.sensitive_data_blocked:
        return "rejected_sensitive_proposal"
    if not chat_id:
        return "rejected_missing_chat_id"
    if proposal_record.proposed_memory_text is None:
        return "rejected_missing_proposed_memory_text"
    lineage = proposal_record.lineage_summary
    if lineage.get("proposal_stage") != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_proposal_stage_lineage_mismatch"
    if lineage.get("acknowledgement_stage") != FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE:
        return "rejected_non_114p_acknowledgement_lineage"
    if lineage.get("followup_completion_loop_stage") != "113P":
        return "rejected_non_113p_followup_completion_lineage"
    if lineage.get("followup_execution_stage") != "112P":
        return "rejected_non_112p_followup_execution_lineage"
    if lineage.get("followup_delegation_stage") != "111P":
        return "rejected_non_111p_followup_delegation_lineage"
    if lineage.get("acknowledgement_id") != proposal_record.acknowledgement_id:
        return "rejected_acknowledgement_lineage_mismatch"
    if lineage.get("route_id") != proposal_record.route_id:
        return "rejected_route_lineage_mismatch"
    if lineage.get("delivery_record_id") != proposal_record.delivery_record_id:
        return "rejected_delivery_lineage_mismatch"
    if lineage.get("surface_id") != proposal_record.surface_id:
        return "rejected_surface_lineage_mismatch"
    if lineage.get("inbox_record_id") != proposal_record.inbox_record_id:
        return "rejected_inbox_lineage_mismatch"
    if lineage.get("event_candidate_id") != proposal_record.event_candidate_id:
        return "rejected_event_candidate_lineage_mismatch"
    if lineage.get("attempt_id") != proposal_record.attempt_id:
        return "rejected_attempt_lineage_mismatch"
    if lineage.get("delegation_id") != proposal_record.delegation_id:
        return "rejected_delegation_lineage_mismatch"
    if lineage.get("packet_id") != proposal_record.packet_id:
        return "rejected_packet_lineage_mismatch"
    if lineage.get("handle_id") != proposal_record.handle_id:
        return "rejected_handle_lineage_mismatch"
    if lineage.get("owner_id") != proposal_record.owner_id:
        return "rejected_owner_mismatch"
    if lineage.get("robot_id") != proposal_record.robot_id:
        return "rejected_robot_mismatch"
    source_chat_id = _proposal_chat_id(proposal_record)
    if source_chat_id != chat_id:
        return "rejected_chat_mismatch"
    cost_summary = lineage.get("cost_preflight_summary")
    if not isinstance(cost_summary, dict):
        return "rejected_missing_100p_cost_lineage"
    route_decision = cost_summary.get("route_decision")
    if not isinstance(route_decision, dict) or not route_decision.get("selected_model_id"):
        return "rejected_missing_100p_cost_lineage"
    request_summary = lineage.get("task_cost_request_summary")
    if not isinstance(request_summary, dict) or not request_summary.get("request_id"):
        return "rejected_missing_100p_cost_lineage"
    return None


def _decision_validation_error(
    *,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    surface_record: TelegramMemoryProposalApprovalSurfaceRecord,
    payload: TelegramMemoryProposalApprovalSelectionPayload,
) -> str | None:
    proposal_error = _proposal_validation_error(proposal_record=proposal_record, chat_id=surface_record.chat_id)
    if proposal_error is not None:
        return proposal_error
    if surface_record.status != "rendered":
        return f"rejected_non_rendered_surface_status_{surface_record.status}"
    if surface_record.source_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_non_115p_surface_source"
    if surface_record.surface_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
        return "rejected_non_116p_surface_stage"
    if payload.proposal_id != proposal_record.proposal_id or payload.proposal_id != surface_record.proposal_id:
        return "rejected_proposal_surface_mismatch"
    if payload.surface_id != surface_record.surface_id:
        return "rejected_surface_mismatch"
    if payload.owner_id != proposal_record.owner_id or payload.owner_id != surface_record.owner_id:
        return "rejected_owner_mismatch"
    if payload.robot_id != proposal_record.robot_id or payload.robot_id != surface_record.robot_id:
        return "rejected_robot_mismatch"
    if payload.chat_id != surface_record.chat_id:
        return "rejected_chat_mismatch"
    if payload.action == "edit_memory_proposal_text" and _normalize_text(payload.revised_proposed_memory_text) is None:
        return "rejected_missing_revised_proposed_memory_text"
    return None


def _surface_text(*, proposal_record: FollowUpMemoryProposalCandidateRecord) -> str:
    return (
        "Memory proposal pending review.\n"
        f"Type: {proposal_record.proposal_type}\n"
        f"Confidence: {proposal_record.confidence}\n"
        f"Proposed memory: {proposal_record.proposed_memory_text}\n"
        f"Reason: {proposal_record.review_reason}"
    )


def _surface_lineage_summary(
    *,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    chat_id: str,
) -> dict[str, object]:
    return {
        "surface_stage": TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
        "proposal_stage": FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        "acknowledgement_stage": FOLLOWUP_RESULT_ACKNOWLEDGEMENT_STAGE,
        "followup_completion_loop_stage": proposal_record.lineage_summary.get("followup_completion_loop_stage"),
        "followup_execution_stage": proposal_record.lineage_summary.get("followup_execution_stage"),
        "followup_delegation_stage": proposal_record.lineage_summary.get("followup_delegation_stage"),
        "proposal_id": proposal_record.proposal_id,
        "acknowledgement_id": proposal_record.acknowledgement_id,
        "route_id": proposal_record.route_id,
        "delivery_record_id": proposal_record.delivery_record_id,
        "surface_id": proposal_record.surface_id,
        "inbox_record_id": proposal_record.inbox_record_id,
        "event_candidate_id": proposal_record.event_candidate_id,
        "attempt_id": proposal_record.attempt_id,
        "delegation_id": proposal_record.delegation_id,
        "packet_id": proposal_record.packet_id,
        "handle_id": proposal_record.handle_id,
        "owner_id": proposal_record.owner_id,
        "robot_id": proposal_record.robot_id,
        "telegram_chat_id": chat_id,
        "upstream_lineage": proposal_record.lineage_summary,
    }


def _lineage_summary_text(
    *,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    surface_record: TelegramMemoryProposalApprovalSurfaceRecord,
) -> str:
    return (
        "Memory proposal lineage summary:\n"
        f"- proposal_id={proposal_record.proposal_id}\n"
        f"- acknowledgement_id={proposal_record.acknowledgement_id}\n"
        f"- route_id={proposal_record.route_id}\n"
        f"- delivery_record_id={proposal_record.delivery_record_id}\n"
        f"- surface_id={surface_record.surface_id}\n"
        f"- attempt_id={proposal_record.attempt_id}\n"
        f"- delegation_id={proposal_record.delegation_id}\n"
        f"- packet_id={proposal_record.packet_id}\n"
        f"- handle_id={proposal_record.handle_id}\n"
        "- No Memory Center write, MemoryItem mutation, external write, or live send was authorized."
    )


def _blocked_surface_record(
    *,
    surface_id: str,
    proposal_record: FollowUpMemoryProposalCandidateRecord | None,
    chat_id: str,
    rejection_reason: str,
) -> TelegramMemoryProposalApprovalSurfaceRecord:
    return TelegramMemoryProposalApprovalSurfaceRecord(
        surface_id=surface_id,
        owner_id="" if proposal_record is None else proposal_record.owner_id,
        robot_id="" if proposal_record is None else proposal_record.robot_id,
        chat_id=chat_id,
        proposal_id="" if proposal_record is None else proposal_record.proposal_id,
        proposal_type="no_memory_candidate" if proposal_record is None else proposal_record.proposal_type,
        proposed_memory_text=None if proposal_record is None else proposal_record.proposed_memory_text,
        confidence="not_applicable" if proposal_record is None else proposal_record.confidence,
        review_reason="The source proposal did not meet 116P approval-surface requirements.",
        source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        surface_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
        allowed_actions=tuple(sorted(ALLOWED_APPROVAL_ACTIONS)),
        telegram_transport="injected_local_only",
        live_send_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        dedupe_key=surface_id,
        lineage_summary={
            "surface_stage": TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
            "proposal_id": None if proposal_record is None else proposal_record.proposal_id,
        },
        created_at="surface_rejected_local",
        status="blocked",
        text="No local Telegram memory approval surface was rendered.",
        rejection_reason=rejection_reason,
    )


def _blocked_decision_record(
    *,
    decision_id: str,
    payload: TelegramMemoryProposalApprovalSelectionPayload,
    proposal_record: FollowUpMemoryProposalCandidateRecord | None,
    rejection_reason: str,
) -> TelegramMemoryProposalApprovalDecisionRecord:
    return TelegramMemoryProposalApprovalDecisionRecord(
        decision_id=decision_id,
        owner_id=payload.owner_id,
        robot_id=payload.robot_id,
        chat_id=payload.chat_id,
        surface_id=payload.surface_id,
        proposal_id=payload.proposal_id,
        action=payload.action,
        decision_status="blocked",
        original_proposed_memory_text=None if proposal_record is None else proposal_record.proposed_memory_text,
        revised_proposed_memory_text=_normalize_text(payload.revised_proposed_memory_text),
        source_stage=FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        decision_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
        writeback_stage_authorized=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        external_write_allowed=False,
        live_send_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key=_decision_dedupe_key(payload=payload),
        lineage_summary=None,
        created_at="decision_rejected_local",
        response_text="I could not record that memory proposal decision in this version.",
        rejection_reason=rejection_reason,
    )


def _surface_id(*, proposal_record: FollowUpMemoryProposalCandidateRecord, chat_id: str) -> str:
    return _stable_id(
        "telegram_memory_proposal_surface",
        proposal_record.proposal_id,
        proposal_record.owner_id,
        proposal_record.robot_id,
        chat_id,
    )


def _decision_id(*, payload: TelegramMemoryProposalApprovalSelectionPayload) -> str:
    return _stable_id(
        "telegram_memory_proposal_decision",
        payload.proposal_id,
        payload.surface_id,
        payload.action,
        _normalize_text(payload.revised_proposed_memory_text) or "",
    )


def _decision_dedupe_key(*, payload: TelegramMemoryProposalApprovalSelectionPayload) -> str:
    return _stable_id(
        "telegram_memory_proposal_decision_dedupe",
        payload.proposal_id,
        payload.surface_id,
        payload.action,
        _normalize_text(payload.revised_proposed_memory_text) or "",
    )


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split()).strip()
    return text or None


def _contains_sensitive_data(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def _proposal_chat_id(proposal_record: FollowUpMemoryProposalCandidateRecord) -> str | None:
    lineage = proposal_record.lineage_summary
    direct = lineage.get("telegram_chat_id")
    if isinstance(direct, str) and direct:
        return direct
    acknowledgement_lineage = lineage.get("acknowledgement_lineage")
    if isinstance(acknowledgement_lineage, dict):
        chat_id = acknowledgement_lineage.get("chat_id")
        if isinstance(chat_id, str) and chat_id:
            return chat_id
    route_lineage = lineage.get("route_lineage")
    if isinstance(route_lineage, dict):
        delivery_summary = route_lineage.get("delivery_summary")
        if isinstance(delivery_summary, dict):
            chat_id = delivery_summary.get("telegram_chat_id")
            if isinstance(chat_id, str) and chat_id:
                return chat_id
        upstream_lineage = route_lineage.get("upstream_lineage")
        if isinstance(upstream_lineage, dict):
            chat_id = upstream_lineage.get("telegram_chat_id")
            if isinstance(chat_id, str) and chat_id:
                return chat_id
    return None


def _stable_id(prefix: str, *parts: object) -> str:
    material = "::".join(str(part) for part in parts)
    return f"{prefix}_{uuid5(NAMESPACE_URL, material)}"
