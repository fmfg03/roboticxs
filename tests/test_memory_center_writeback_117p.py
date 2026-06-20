from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.memory_center_writeback import (
    MEMORY_CENTER_WRITEBACK_STAGE,
    MemoryCenterWritebackRegistry,
    get_memory_center_writeback_record,
    get_memory_item_from_writeback,
    list_memory_center_writeback_records,
    write_approved_memory_proposal_to_memory_center,
)
from app.telegram_memory_proposal_approval import TelegramMemoryProposalApprovalRegistry
from tests.test_telegram_memory_proposal_approval_116p import pending_proposal, payload, render_surface
from app.telegram_memory_proposal_approval import bind_memory_proposal_approval_selection


REPO_ROOT = Path(__file__).resolve().parents[1]
WRITEBACK_PATH = REPO_ROOT / "app/memory_center_writeback.py"


def approved_decision(*, delivery_text: str = "Checklist for NDA review next step.", action: str = "approve_memory_proposal", revised_text: str | None = None):
    proposal = pending_proposal(delivery_text=delivery_text)
    registry = TelegramMemoryProposalApprovalRegistry()
    surface = render_surface(proposal=proposal, registry=registry)[2]
    decision = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(
            surface,
            action=action,
            revised_proposed_memory_text=revised_text,
        ),
        registry=registry,
    )
    return proposal, surface, decision


def test_117p_approved_pending_writeback_writes_original_memory_text_to_local_memory_center():
    proposal, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )
    memory_item = get_memory_item_from_writeback(registry=registry, writeback_id=record.writeback_id)

    assert record.writeback_stage == MEMORY_CENTER_WRITEBACK_STAGE
    assert record.writeback_status == "written"
    assert record.final_memory_text == proposal.proposed_memory_text
    assert record.memory_center_mutated is True
    assert memory_item is not None
    assert memory_item.content == proposal.proposed_memory_text


def test_117p_edited_pending_writeback_writes_revised_memory_text_to_local_memory_center():
    proposal, surface, decision = approved_decision(
        action="edit_memory_proposal_text",
        revised_text="Use checklist format for NDA review follow-ups.",
    )
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )
    memory_item = get_memory_item_from_writeback(registry=registry, writeback_id=record.writeback_id)

    assert record.decision_status == "edited_pending_writeback"
    assert record.final_memory_text == "Use checklist format for NDA review follow-ups."
    assert memory_item is not None
    assert memory_item.content == "Use checklist format for NDA review follow-ups."


def test_117p_rejected_no_write_decision_does_not_write_memory():
    proposal, surface, decision = approved_decision(action="reject_memory_proposal")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_no_write"
    assert record.memory_center_mutated is False
    assert get_memory_item_from_writeback(registry=registry, writeback_id=record.writeback_id) is None


def test_117p_rejected_sensitive_edit_does_not_write_memory():
    proposal, surface, decision = approved_decision(
        action="edit_memory_proposal_text",
        revised_text="Remember the owner's health diagnosis.",
    )
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_no_write"
    assert record.rejection_reason == "rejected_sensitive_edit"


def test_117p_lineage_summary_requested_does_not_write_memory():
    proposal, surface, decision = approved_decision(action="request_memory_proposal_lineage_summary")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_no_write"
    assert record.rejection_reason == "rejected_lineage_summary_requested"


def test_117p_no_memory_candidate_proposal_does_not_write_memory():
    proposal, surface, decision = approved_decision()
    proposal = replace(
        proposal,
        proposal_type="no_memory_candidate",
        status="no_memory_recommended",
        proposed_memory_text=None,
    )
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_invalid_lineage"
    assert record.rejection_reason == "rejected_no_memory_candidate_proposal"


def test_117p_rejected_source_proposal_does_not_write_memory():
    proposal, surface, decision = approved_decision()
    proposal = replace(proposal, status="rejected_source", rejection_reason="fixture")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.rejection_reason == "rejected_source_proposal"


def test_117p_unknown_decision_is_rejected():
    proposal, surface, _ = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=object(),
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_invalid_lineage"
    assert record.rejection_reason == "rejected_unknown_116p_decision_record"


def test_117p_unknown_proposal_is_rejected():
    _, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=object(),
        registry=registry,
    )

    assert record.rejection_reason == "rejected_unknown_115p_proposal_record"


def test_117p_wrong_owner_is_rejected():
    proposal, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=replace(decision, owner_id="other-owner"),
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.rejection_reason == "rejected_owner_mismatch"


def test_117p_wrong_robot_is_rejected():
    proposal, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=replace(decision, robot_id="other-robot"),
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.rejection_reason == "rejected_robot_mismatch"


def test_117p_mismatched_decision_surface_proposal_lineage_is_rejected():
    proposal, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=replace(decision, surface_id="other-surface"),
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.rejection_reason == "rejected_surface_lineage_mismatch"


def test_117p_empty_final_memory_text_is_rejected():
    proposal, surface, decision = approved_decision(action="edit_memory_proposal_text", revised_text="   ")
    decision = replace(decision, decision_status="edited_pending_writeback", revised_proposed_memory_text="   ")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.rejection_reason == "rejected_empty_final_memory_text"


def test_117p_sensitive_final_memory_text_is_rejected():
    proposal, surface, decision = approved_decision()
    decision = replace(decision, original_proposed_memory_text="Remember the owner's health diagnosis.")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.writeback_status == "rejected_sensitive_data"
    assert record.rejection_reason == "rejected_sensitive_final_memory_text"


def test_117p_duplicate_writeback_returns_existing_record_without_duplicate_memory_item():
    proposal, surface, decision = approved_decision()
    registry = MemoryCenterWritebackRegistry()

    first = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )
    second = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert first == second
    assert len(list_memory_center_writeback_records(registry=registry)) == 1
    assert get_memory_center_writeback_record(registry=registry, writeback_id=first.writeback_id) == first
    assert len(registry.memory_items_by_id) == 1


def test_117p_writeback_record_preserves_100p_through_116p_lineage():
    proposal, surface, decision = approved_decision(delivery_text="Ask before sending external messages.")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )

    assert record.lineage_summary["cost_preflight_summary"]["route_decision"]["selected_model_id"] == "balanced_standard_v1"
    assert record.lineage_summary["task_cost_request_summary"]["request_id"] == "cost-request-112p"
    assert record.lineage_summary["followup_delegation_stage"] == "111P"
    assert record.lineage_summary["followup_execution_stage"] == "112P"
    assert record.lineage_summary["followup_completion_loop_stage"] == "113P"
    assert record.lineage_summary["acknowledgement_stage"] == "114P"
    assert record.lineage_summary["proposal_stage"] == "115P"
    assert record.lineage_summary["decision_stage"] == "116P"


def test_117p_boundary_memory_maps_to_boundary_memory_section():
    proposal, surface, decision = approved_decision(delivery_text="Ask before sending external messages.")
    registry = MemoryCenterWritebackRegistry()

    record = write_approved_memory_proposal_to_memory_center(
        decision_record=decision,
        surface_record=surface,
        proposal_record=proposal,
        registry=registry,
    )
    memory_item = get_memory_item_from_writeback(registry=registry, writeback_id=record.writeback_id)

    assert record.memory_section == "BOUNDARY_MEMORY"
    assert memory_item is not None
    assert memory_item.memory_kind == "BOUNDARY_MEMORY"
    assert memory_item.is_boundary is True


def test_117p_stage_stays_local_without_external_side_effects():
    text = WRITEBACK_PATH.read_text()

    for forbidden in [
        "send_message",
        "telegram.Bot",
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "delegate_task",
        "register_async_delegation_handle",
    ]:
        assert forbidden not in text


def test_117p_118p_plus_remains_unauthorized():
    roadmap = (REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md").read_text()

    assert "118P and later remain unauthorized" in roadmap or "118P+ remains unauthorized" in roadmap
