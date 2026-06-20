from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.followup_memory_proposal import (
    FOLLOWUP_MEMORY_PROPOSAL_STAGE,
    PROPOSAL_TYPES,
    SENSITIVE_KEYWORDS,
    FollowUpMemoryProposalCandidateRecord,
)
from app.memory_center_projection import MemoryCenterItem
from app.telegram_memory_proposal_approval import (
    TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
    TelegramMemoryProposalApprovalDecisionRecord,
    TelegramMemoryProposalApprovalSurfaceRecord,
)


MEMORY_CENTER_WRITEBACK_STAGE = "117P"
ALLOWED_DECISION_STATUSES = frozenset({"approved_pending_writeback", "edited_pending_writeback"})
WRITEBACK_STATUSES = frozenset(
    {
        "written",
        "duplicate_existing",
        "rejected_no_write",
        "rejected_sensitive_data",
        "rejected_invalid_lineage",
    }
)
MEMORY_KIND_BY_PROPOSAL_TYPE = {
    "user_preference_candidate": "USER_PROFILE_MEMORY",
    "work_preference_candidate": "WORK_PREFERENCE",
    "business_context_candidate": "BUSINESS_CONTEXT_MEMORY",
    "task_memory_candidate": "TASK_MEMORY",
    "boundary_memory_candidate": "BOUNDARY_MEMORY",
}
SCOPE_BY_MEMORY_KIND = {
    "USER_PROFILE_MEMORY": ("general", "telegram", "hermes_os"),
    "WORK_PREFERENCE": ("general", "telegram", "hermes_os"),
    "BUSINESS_CONTEXT_MEMORY": ("general", "telegram", "hermes_os"),
    "TASK_MEMORY": ("general", "telegram", "hermes_os"),
    "BOUNDARY_MEMORY": ("general", "telegram", "hermes_os", "caregiver", "routine"),
}
ALLOWED_USES_BY_MEMORY_KIND = {
    "USER_PROFILE_MEMORY": ("answer_personalization", "telegram_context", "hermes_os_context"),
    "WORK_PREFERENCE": ("answer_personalization", "telegram_context", "hermes_os_context"),
    "BUSINESS_CONTEXT_MEMORY": ("answer_personalization", "telegram_context", "hermes_os_context"),
    "TASK_MEMORY": ("telegram_context", "hermes_os_context"),
    "BOUNDARY_MEMORY": (
        "answer_personalization",
        "telegram_context",
        "hermes_os_context",
        "boundary_enforcement",
        "caregiver_context",
        "routine_context",
    ),
}


@dataclass(frozen=True, slots=True)
class MemoryCenterWritebackRecord:
    writeback_id: str
    owner_id: str
    robot_id: str
    decision_id: str
    surface_id: str
    proposal_id: str
    acknowledgement_id: str
    route_id: str
    delivery_record_id: str
    event_candidate_id: str
    attempt_id: str
    delegation_id: str
    packet_id: str
    handle_id: str
    source_stage: str
    writeback_stage: str
    proposal_type: str
    memory_section: str
    final_memory_text: str | None
    decision_status: str
    writeback_status: str
    memory_item_id: str | None
    memory_center_mutated: bool
    external_write_allowed: bool
    live_send_allowed: bool
    context_scan_allowed: bool
    proactive_detection_allowed: bool
    sensitive_data_blocked: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.source_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
            raise ValueError("117P writebacks must originate from 116P decisions.")
        if self.writeback_stage != MEMORY_CENTER_WRITEBACK_STAGE:
            raise ValueError("117P writebacks must identify the 117P stage.")
        if self.proposal_type not in PROPOSAL_TYPES:
            raise ValueError("Unsupported 117P proposal type.")
        if self.writeback_status not in WRITEBACK_STATUSES:
            raise ValueError("Unsupported 117P writeback status.")
        if self.external_write_allowed is not False:
            raise ValueError("117P writebacks must not authorize external writes.")
        if self.live_send_allowed is not False:
            raise ValueError("117P writebacks must not authorize live sends.")
        if self.context_scan_allowed is not False:
            raise ValueError("117P writebacks must not authorize context scans.")
        if self.proactive_detection_allowed is not False:
            raise ValueError("117P writebacks must not authorize proactive detection.")


@dataclass(slots=True)
class MemoryCenterWritebackRegistry:
    writebacks_by_id: dict[str, MemoryCenterWritebackRecord] = field(default_factory=dict)
    memory_items_by_id: dict[str, MemoryCenterItem] = field(default_factory=dict)
    writeback_to_memory_item_id: dict[str, str] = field(default_factory=dict)

    def store_writeback(self, record: MemoryCenterWritebackRecord) -> MemoryCenterWritebackRecord:
        self.writebacks_by_id[record.writeback_id] = record
        return record

    def store_memory_item(self, item: MemoryCenterItem, *, writeback_id: str) -> MemoryCenterItem:
        self.memory_items_by_id[item.item_id] = item
        self.writeback_to_memory_item_id[writeback_id] = item.item_id
        return item

    def get_memory_center_writeback_record(self, writeback_id: str) -> MemoryCenterWritebackRecord | None:
        return self.writebacks_by_id.get(writeback_id)

    def list_memory_center_writeback_records(self) -> tuple[MemoryCenterWritebackRecord, ...]:
        return tuple(self.writebacks_by_id[key] for key in sorted(self.writebacks_by_id))

    def get_memory_item_from_writeback(self, writeback_id: str) -> MemoryCenterItem | None:
        memory_item_id = self.writeback_to_memory_item_id.get(writeback_id)
        if memory_item_id is None:
            return None
        return self.memory_items_by_id.get(memory_item_id)


def write_approved_memory_proposal_to_memory_center(
    *,
    decision_record: object,
    surface_record: object,
    proposal_record: object,
    registry: MemoryCenterWritebackRegistry,
) -> MemoryCenterWritebackRecord:
    if not isinstance(decision_record, TelegramMemoryProposalApprovalDecisionRecord):
        writeback_id = _stable_id("memory_center_writeback", "unknown")
        existing = registry.get_memory_center_writeback_record(writeback_id)
        if existing is not None:
            return existing
        return registry.store_writeback(
            _rejected_writeback_record(
                writeback_id=writeback_id,
                decision_record=None,
                proposal_record=None,
                rejection_reason="rejected_unknown_116p_decision_record",
            )
        )

    writeback_id = _writeback_id(decision_record=decision_record)
    existing = registry.get_memory_center_writeback_record(writeback_id)
    if existing is not None:
        return existing

    if not isinstance(proposal_record, FollowUpMemoryProposalCandidateRecord):
        return registry.store_writeback(
            _rejected_writeback_record(
                writeback_id=writeback_id,
                decision_record=decision_record,
                proposal_record=None,
                rejection_reason="rejected_unknown_115p_proposal_record",
            )
        )

    if not isinstance(surface_record, TelegramMemoryProposalApprovalSurfaceRecord):
        return registry.store_writeback(
            _rejected_writeback_record(
                writeback_id=writeback_id,
                decision_record=decision_record,
                proposal_record=proposal_record,
                rejection_reason="rejected_unknown_116p_surface_record",
            )
        )

    final_memory_text = _final_memory_text(decision_record=decision_record)
    rejection_reason = _validation_error(
        decision_record=decision_record,
        surface_record=surface_record,
        proposal_record=proposal_record,
        final_memory_text=final_memory_text,
    )
    if rejection_reason is not None:
        return registry.store_writeback(
            _rejected_writeback_record(
                writeback_id=writeback_id,
                decision_record=decision_record,
                proposal_record=proposal_record,
                rejection_reason=rejection_reason,
                final_memory_text=final_memory_text,
            )
        )

    assert final_memory_text is not None
    memory_kind = MEMORY_KIND_BY_PROPOSAL_TYPE[proposal_record.proposal_type]
    memory_item_id = _memory_item_id(decision_record=decision_record, proposal_record=proposal_record, final_memory_text=final_memory_text)
    memory_item = MemoryCenterItem(
        item_id=memory_item_id,
        owner_id=proposal_record.owner_id,
        robot_id=proposal_record.robot_id,
        memory_kind=memory_kind,
        status="active",
        scopes=SCOPE_BY_MEMORY_KIND[memory_kind],
        sensitivity="ordinary",
        allowed_uses=ALLOWED_USES_BY_MEMORY_KIND[memory_kind],
        skill_ids=(),
        content=final_memory_text,
        bounded_summary=final_memory_text,
        source="followup_result_approved_memory",
        actor_visibility="owner_private",
        conflict_group="followup_boundary" if memory_kind == "BOUNDARY_MEMORY" else None,
        is_boundary=memory_kind == "BOUNDARY_MEMORY",
        is_preference=memory_kind in {"USER_PROFILE_MEMORY", "WORK_PREFERENCE"},
    )
    registry.store_memory_item(memory_item, writeback_id=writeback_id)
    return registry.store_writeback(
        MemoryCenterWritebackRecord(
            writeback_id=writeback_id,
            owner_id=proposal_record.owner_id,
            robot_id=proposal_record.robot_id,
            decision_id=decision_record.decision_id,
            surface_id=surface_record.surface_id,
            proposal_id=proposal_record.proposal_id,
            acknowledgement_id=proposal_record.acknowledgement_id,
            route_id=proposal_record.route_id,
            delivery_record_id=proposal_record.delivery_record_id,
            event_candidate_id=proposal_record.event_candidate_id,
            attempt_id=proposal_record.attempt_id,
            delegation_id=proposal_record.delegation_id,
            packet_id=proposal_record.packet_id,
            handle_id=proposal_record.handle_id,
            source_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
            writeback_stage=MEMORY_CENTER_WRITEBACK_STAGE,
            proposal_type=proposal_record.proposal_type,
            memory_section=memory_kind,
            final_memory_text=final_memory_text,
            decision_status=decision_record.decision_status,
            writeback_status="written",
            memory_item_id=memory_item_id,
            memory_center_mutated=True,
            external_write_allowed=False,
            live_send_allowed=False,
            context_scan_allowed=False,
            proactive_detection_allowed=False,
            sensitive_data_blocked=False,
            dedupe_key=_dedupe_key(decision_record=decision_record, proposal_record=proposal_record, final_memory_text=final_memory_text),
            lineage_summary=_lineage_summary(
                decision_record=decision_record,
                surface_record=surface_record,
                proposal_record=proposal_record,
                memory_item=memory_item,
            ),
            created_at=f"writeback_local_{len(registry.writebacks_by_id) + 1:04d}",
            rejection_reason=None,
        )
    )


def get_memory_center_writeback_record(
    *,
    registry: MemoryCenterWritebackRegistry,
    writeback_id: str,
) -> MemoryCenterWritebackRecord | None:
    return registry.get_memory_center_writeback_record(writeback_id)


def list_memory_center_writeback_records(
    *,
    registry: MemoryCenterWritebackRegistry,
) -> tuple[MemoryCenterWritebackRecord, ...]:
    return registry.list_memory_center_writeback_records()


def get_memory_item_from_writeback(
    *,
    registry: MemoryCenterWritebackRegistry,
    writeback_id: str,
) -> MemoryCenterItem | None:
    return registry.get_memory_item_from_writeback(writeback_id)


def _validation_error(
    *,
    decision_record: TelegramMemoryProposalApprovalDecisionRecord,
    surface_record: TelegramMemoryProposalApprovalSurfaceRecord,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    final_memory_text: str | None,
) -> str | None:
    if decision_record.source_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_missing_115p_proposal_lineage"
    if decision_record.decision_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
        return "rejected_missing_116p_approval_lineage"
    if surface_record.source_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_missing_115p_proposal_lineage"
    if surface_record.surface_stage != TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE:
        return "rejected_missing_116p_approval_lineage"
    if proposal_record.proposal_stage != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_missing_115p_proposal_lineage"
    if decision_record.decision_status == "rejected_no_write":
        return "rejected_no_write"
    if decision_record.decision_status == "rejected_sensitive_edit":
        return "rejected_sensitive_edit"
    if decision_record.decision_status == "lineage_summary_requested":
        return "rejected_lineage_summary_requested"
    if decision_record.decision_status not in ALLOWED_DECISION_STATUSES:
        return f"rejected_invalid_decision_status_{decision_record.decision_status}"
    if proposal_record.status == "rejected_source":
        return "rejected_source_proposal"
    if proposal_record.status == "no_memory_recommended":
        return "rejected_no_memory_candidate_proposal"
    if proposal_record.proposal_type == "no_memory_candidate":
        return "rejected_no_memory_candidate_proposal"
    if proposal_record.sensitive_data_blocked:
        return "rejected_sensitive_proposal"
    if proposal_record.proposal_type not in MEMORY_KIND_BY_PROPOSAL_TYPE:
        return "rejected_unsupported_proposal_type"
    if decision_record.owner_id != proposal_record.owner_id or decision_record.owner_id != surface_record.owner_id:
        return "rejected_owner_mismatch"
    if decision_record.robot_id != proposal_record.robot_id or decision_record.robot_id != surface_record.robot_id:
        return "rejected_robot_mismatch"
    if decision_record.surface_id != surface_record.surface_id:
        return "rejected_surface_lineage_mismatch"
    if decision_record.proposal_id != proposal_record.proposal_id or decision_record.proposal_id != surface_record.proposal_id:
        return "rejected_proposal_lineage_mismatch"
    if surface_record.owner_id != proposal_record.owner_id:
        return "rejected_owner_mismatch"
    if surface_record.robot_id != proposal_record.robot_id:
        return "rejected_robot_mismatch"
    surface_lineage = surface_record.lineage_summary
    if surface_lineage.get("proposal_id") != proposal_record.proposal_id:
        return "rejected_proposal_lineage_mismatch"
    if surface_lineage.get("acknowledgement_id") != proposal_record.acknowledgement_id:
        return "rejected_acknowledgement_lineage_mismatch"
    if surface_lineage.get("route_id") != proposal_record.route_id:
        return "rejected_route_lineage_mismatch"
    if surface_lineage.get("delivery_record_id") != proposal_record.delivery_record_id:
        return "rejected_delivery_lineage_mismatch"
    if surface_lineage.get("event_candidate_id") != proposal_record.event_candidate_id:
        return "rejected_event_candidate_lineage_mismatch"
    if surface_lineage.get("attempt_id") != proposal_record.attempt_id:
        return "rejected_attempt_lineage_mismatch"
    if surface_lineage.get("delegation_id") != proposal_record.delegation_id:
        return "rejected_delegation_lineage_mismatch"
    if surface_lineage.get("packet_id") != proposal_record.packet_id:
        return "rejected_packet_lineage_mismatch"
    if surface_lineage.get("handle_id") != proposal_record.handle_id:
        return "rejected_handle_lineage_mismatch"
    proposal_lineage = proposal_record.lineage_summary
    if proposal_lineage.get("proposal_stage") != FOLLOWUP_MEMORY_PROPOSAL_STAGE:
        return "rejected_missing_115p_proposal_lineage"
    if proposal_lineage.get("acknowledgement_stage") != "114P":
        return "rejected_acknowledgement_lineage_mismatch"
    if proposal_lineage.get("followup_completion_loop_stage") != "113P":
        return "rejected_route_lineage_mismatch"
    if proposal_lineage.get("followup_execution_stage") != "112P":
        return "rejected_attempt_lineage_mismatch"
    if proposal_lineage.get("followup_delegation_stage") != "111P":
        return "rejected_delegation_lineage_mismatch"
    if proposal_lineage.get("route_id") != proposal_record.route_id:
        return "rejected_route_lineage_mismatch"
    if proposal_lineage.get("delivery_record_id") != proposal_record.delivery_record_id:
        return "rejected_delivery_lineage_mismatch"
    if proposal_lineage.get("event_candidate_id") != proposal_record.event_candidate_id:
        return "rejected_event_candidate_lineage_mismatch"
    if final_memory_text is None:
        return "rejected_empty_final_memory_text"
    if _contains_sensitive_data(final_memory_text):
        return "rejected_sensitive_final_memory_text"
    return None


def _final_memory_text(*, decision_record: TelegramMemoryProposalApprovalDecisionRecord) -> str | None:
    if decision_record.decision_status == "approved_pending_writeback":
        return _normalize_text(decision_record.original_proposed_memory_text)
    if decision_record.decision_status == "edited_pending_writeback":
        return _normalize_text(decision_record.revised_proposed_memory_text)
    return None


def _lineage_summary(
    *,
    decision_record: TelegramMemoryProposalApprovalDecisionRecord,
    surface_record: TelegramMemoryProposalApprovalSurfaceRecord,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    memory_item: MemoryCenterItem,
) -> dict[str, object]:
    return {
        "writeback_stage": MEMORY_CENTER_WRITEBACK_STAGE,
        "decision_stage": TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
        "proposal_stage": FOLLOWUP_MEMORY_PROPOSAL_STAGE,
        "acknowledgement_stage": proposal_record.lineage_summary.get("acknowledgement_stage"),
        "followup_completion_loop_stage": proposal_record.lineage_summary.get("followup_completion_loop_stage"),
        "followup_execution_stage": proposal_record.lineage_summary.get("followup_execution_stage"),
        "followup_delegation_stage": proposal_record.lineage_summary.get("followup_delegation_stage"),
        "decision_id": decision_record.decision_id,
        "decision_status": decision_record.decision_status,
        "decision_action": decision_record.action,
        "surface_id": surface_record.surface_id,
        "proposal_id": proposal_record.proposal_id,
        "acknowledgement_id": proposal_record.acknowledgement_id,
        "route_id": proposal_record.route_id,
        "delivery_record_id": proposal_record.delivery_record_id,
        "event_candidate_id": proposal_record.event_candidate_id,
        "attempt_id": proposal_record.attempt_id,
        "delegation_id": proposal_record.delegation_id,
        "packet_id": proposal_record.packet_id,
        "handle_id": proposal_record.handle_id,
        "owner_id": proposal_record.owner_id,
        "robot_id": proposal_record.robot_id,
        "memory_item_id": memory_item.item_id,
        "memory_kind": memory_item.memory_kind,
        "cost_preflight_summary": proposal_record.lineage_summary.get("cost_preflight_summary"),
        "task_cost_request_summary": proposal_record.lineage_summary.get("task_cost_request_summary"),
        "budget_policy_summary": proposal_record.lineage_summary.get("budget_policy_summary"),
        "approval_packet_id": proposal_record.lineage_summary.get("approval_packet_id"),
        "async_authority_state": proposal_record.lineage_summary.get("async_authority_state"),
        "proposal_lineage": proposal_record.lineage_summary,
        "surface_lineage": surface_record.lineage_summary,
    }


def _rejected_writeback_record(
    *,
    writeback_id: str,
    decision_record: TelegramMemoryProposalApprovalDecisionRecord | None,
    proposal_record: FollowUpMemoryProposalCandidateRecord | None,
    rejection_reason: str,
    final_memory_text: str | None = None,
) -> MemoryCenterWritebackRecord:
    proposal_type = "no_memory_candidate" if proposal_record is None else proposal_record.proposal_type
    return MemoryCenterWritebackRecord(
        writeback_id=writeback_id,
        owner_id="" if decision_record is None else decision_record.owner_id,
        robot_id="" if decision_record is None else decision_record.robot_id,
        decision_id="" if decision_record is None else decision_record.decision_id,
        surface_id="" if decision_record is None else decision_record.surface_id,
        proposal_id="" if decision_record is None else decision_record.proposal_id,
        acknowledgement_id="" if proposal_record is None else proposal_record.acknowledgement_id,
        route_id="" if proposal_record is None else proposal_record.route_id,
        delivery_record_id="" if proposal_record is None else proposal_record.delivery_record_id,
        event_candidate_id="" if proposal_record is None else proposal_record.event_candidate_id,
        attempt_id="" if proposal_record is None else proposal_record.attempt_id,
        delegation_id="" if proposal_record is None else proposal_record.delegation_id,
        packet_id="" if proposal_record is None else proposal_record.packet_id,
        handle_id="" if proposal_record is None else proposal_record.handle_id,
        source_stage=TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
        writeback_stage=MEMORY_CENTER_WRITEBACK_STAGE,
        proposal_type=proposal_type,
        memory_section="" if proposal_type not in MEMORY_KIND_BY_PROPOSAL_TYPE else MEMORY_KIND_BY_PROPOSAL_TYPE[proposal_type],
        final_memory_text=final_memory_text,
        decision_status="" if decision_record is None else decision_record.decision_status,
        writeback_status=(
            "rejected_no_write"
            if rejection_reason in {"rejected_no_write", "rejected_sensitive_edit", "rejected_lineage_summary_requested"}
            else "rejected_sensitive_data"
            if "sensitive" in rejection_reason
            else "rejected_invalid_lineage"
        ),
        memory_item_id=None,
        memory_center_mutated=False,
        external_write_allowed=False,
        live_send_allowed=False,
        context_scan_allowed=False,
        proactive_detection_allowed=False,
        sensitive_data_blocked="sensitive" in rejection_reason,
        dedupe_key=writeback_id,
        lineage_summary={
            "writeback_stage": MEMORY_CENTER_WRITEBACK_STAGE,
            "decision_id": None if decision_record is None else decision_record.decision_id,
            "proposal_id": None if proposal_record is None else proposal_record.proposal_id,
        },
        created_at="writeback_rejected_local",
        rejection_reason=rejection_reason,
    )


def _writeback_id(*, decision_record: TelegramMemoryProposalApprovalDecisionRecord) -> str:
    return _stable_id(
        "memory_center_writeback",
        decision_record.decision_id,
        decision_record.proposal_id,
        decision_record.decision_status,
        _normalize_text(decision_record.original_proposed_memory_text) or "",
        _normalize_text(decision_record.revised_proposed_memory_text) or "",
    )


def _memory_item_id(
    *,
    decision_record: TelegramMemoryProposalApprovalDecisionRecord,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    final_memory_text: str,
) -> str:
    return _stable_id(
        "memory_center_item",
        decision_record.decision_id,
        proposal_record.proposal_id,
        proposal_record.proposal_type,
        final_memory_text,
    )


def _dedupe_key(
    *,
    decision_record: TelegramMemoryProposalApprovalDecisionRecord,
    proposal_record: FollowUpMemoryProposalCandidateRecord,
    final_memory_text: str,
) -> str:
    return _stable_id(
        "memory_center_writeback_dedupe",
        decision_record.decision_id,
        proposal_record.proposal_id,
        final_memory_text,
    )


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split()).strip()
    return text or None


def _contains_sensitive_data(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "::".join(str(part) for part in parts)
    return f"{prefix}_{uuid5(NAMESPACE_URL, material)}"
