from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.context_scan_candidate_source import ContextScanCandidateSourceRecord
from app.daily_brief_what_did_i_miss import DailyBriefItemRecord, DailyBriefSnapshotRecord
from app.followup_memory_proposal import FollowUpMemoryProposalCandidateRecord
from app.memory_center_writeback import MemoryCenterWritebackRecord
from app.proactive_opportunity_detection import ProactiveOpportunityCandidateRecord
from app.skill_pack_activation_surface import (
    SKILL_PACK_STAGE,
    SkillPackActivationRegistry,
    SkillPackSourceBundle,
    classify_record_for_skill_pack,
    create_skill_pack_activation_surface,
    get_skill_pack_activation_surface,
    get_skill_pack_classification,
    list_skill_pack_activation_surfaces,
    list_skill_pack_classifications,
)


OWNER_ID = "owner-125p"
ROBOT_ID = "robot-125p"


@dataclass(frozen=True, slots=True)
class UnknownRecord:
    owner_id: str
    robot_id: str
    title: str
    summary: str
    created_at: str = "2026-06-20T17:00:00Z"


def _daily_brief_item(*, summary: str, section_name: str = "headline_summary", source_stage: str = "124P", title: str = "What Did I Miss?") -> DailyBriefItemRecord:
    return DailyBriefItemRecord(
        item_id=f"item-{section_name}-{source_stage}-{title.replace(' ', '-').lower()}",
        brief_id="brief-125p",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        source_record_id=f"source-{section_name}-{source_stage}-{title.replace(' ', '-').lower()}",
        source_record_type="DailyBriefItemRecord",
        source_stage=source_stage,
        section_name=section_name,
        title=title,
        summary=summary,
        status="informational",
        severity="informational",
        safe_evidence_refs=(),
        suggested_review_type=None,
        action_allowed=False,
        telegram_delivery_allowed=False,
        callback_binding_allowed=False,
        delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        sensitive_data_excluded=True,
        lineage_summary={"source_stage": source_stage},
        created_at="2026-06-20T16:00:00Z",
    )


def _opportunity(opportunity_type: str, title: str, summary: str) -> ProactiveOpportunityCandidateRecord:
    category_by_type = {
        "document_review_needed": "document",
        "meeting_brief_missing": "meeting",
        "lead_followup_due": "sales",
        "stale_proposal_followup": "sales",
        "invoice_due_soon": "finance_admin",
        "customer_issue_needs_attention": "customer_success",
        "boundary_review_needed": "safety_boundary",
    }
    next_step_by_type = {
        "document_review_needed": "review_document",
        "meeting_brief_missing": "prepare_brief",
        "lead_followup_due": "draft_followup",
        "stale_proposal_followup": "draft_followup",
        "invoice_due_soon": "review_document",
        "customer_issue_needs_attention": "draft_followup",
        "boundary_review_needed": "review_boundary",
    }
    return ProactiveOpportunityCandidateRecord(
        opportunity_id=f"opportunity-{opportunity_type}",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        candidate_source_id=f"candidate-{opportunity_type}",
        authorization_id=f"auth-{opportunity_type}",
        source_type="mock_document" if "document" in opportunity_type or "proposal" in opportunity_type else "mock_calendar_event",
        source_category="document_context" if "document" in opportunity_type or "proposal" in opportunity_type else "calendar_context",
        source_stage="118P",
        detection_stage="119P",
        opportunity_type=opportunity_type,
        opportunity_category=category_by_type[opportunity_type],
        title=title,
        summary=summary,
        trigger_reason="deterministic_test_fixture",
        suggested_next_step_type=next_step_by_type[opportunity_type],
        confidence="high",
        evidence_refs=({"candidate_source_id": f"candidate-{opportunity_type}"},),
        source_created_detection=False,
        telegram_send_allowed=False,
        followup_adapter_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        live_connector_allowed=False,
        external_write_allowed=False,
        worker_dispatch_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key=f"dedupe-{opportunity_type}",
        lineage_summary={"detection_stage": "119P", "opportunity_type": opportunity_type},
        created_at="2026-06-20T12:00:00Z",
    )


def test_125p_classifies_records_into_expected_skill_packs():
    registry = SkillPackActivationRegistry()

    brief_item = _daily_brief_item(summary="What did I miss today?")
    assert classify_record_for_skill_pack(record=brief_item, owner_id=OWNER_ID, robot_id=ROBOT_ID, registry=registry).skill_pack_id == "basic_package"

    assert classify_record_for_skill_pack(
        record=_opportunity("document_review_needed", "NDA review", "Document review needed for NDA."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "documents_pack"
    assert classify_record_for_skill_pack(
        record=_opportunity("meeting_brief_missing", "Meeting brief missing", "Prepare meeting brief for tomorrow."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "basic_package"
    assert classify_record_for_skill_pack(
        record=_opportunity("lead_followup_due", "Lead follow-up", "Lead follow-up is due today."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "sales_pack"
    assert classify_record_for_skill_pack(
        record=_opportunity("stale_proposal_followup", "Stale proposal", "Proposal follow-up is overdue."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "sales_pack"
    assert classify_record_for_skill_pack(
        record=_opportunity("invoice_due_soon", "Invoice due", "Invoice payment is due soon."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "finance_admin_pack"
    assert classify_record_for_skill_pack(
        record=_opportunity("customer_issue_needs_attention", "Customer issue", "Customer issue needs attention."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "pro_package"
    assert classify_record_for_skill_pack(
        record=_opportunity("boundary_review_needed", "Boundary review", "Boundary review needed."),
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        registry=registry,
    ).skill_pack_id == "safety_boundary_core"

    proposal = FollowUpMemoryProposalCandidateRecord(
        proposal_id="proposal-125p",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        acknowledgement_id="ack-125p",
        route_id="route-125p",
        delivery_record_id="delivery-125p",
        surface_id="surface-125p",
        inbox_record_id="inbox-125p",
        event_candidate_id="event-125p",
        attempt_id="attempt-125p",
        delegation_id="delegation-125p",
        packet_id="packet-125p",
        handle_id="handle-125p",
        source_stage="114P",
        proposal_stage="115P",
        proposal_type="task_memory_candidate",
        proposed_memory_text="Remember ACME payment follow-up.",
        confidence="medium",
        review_reason="Potential memory candidate.",
        status="pending_user_review",
        memory_write_allowed=False,
        telegram_approval_surface_allowed=False,
        user_approved=False,
        memory_center_mutated=False,
        live_send_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key="proposal-dedupe-125p",
        lineage_summary={"proposal_stage": "115P"},
        created_at="2026-06-20T13:00:00Z",
        rejection_reason=None,
    )
    assert classify_record_for_skill_pack(record=proposal, owner_id=OWNER_ID, robot_id=ROBOT_ID, registry=registry).skill_pack_id == "memory_center_core"

    writeback = MemoryCenterWritebackRecord(
        writeback_id="writeback-125p",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        decision_id="decision-125p",
        surface_id="surface-memory-125p",
        proposal_id="proposal-125p",
        acknowledgement_id="ack-125p",
        route_id="route-125p",
        delivery_record_id="delivery-125p",
        event_candidate_id="event-125p",
        attempt_id="attempt-125p",
        delegation_id="delegation-125p",
        packet_id="packet-125p",
        handle_id="handle-125p",
        source_stage="116P",
        writeback_stage="117P",
        proposal_type="task_memory_candidate",
        memory_section="TASK_MEMORY",
        final_memory_text="Stored memory.",
        decision_status="approved_pending_writeback",
        writeback_status="written",
        memory_item_id="memory-item-125p",
        memory_center_mutated=True,
        external_write_allowed=False,
        live_send_allowed=False,
        context_scan_allowed=False,
        proactive_detection_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key="writeback-dedupe-125p",
        lineage_summary={"writeback_stage": "117P"},
        created_at="2026-06-20T13:10:00Z",
        rejection_reason=None,
    )
    assert classify_record_for_skill_pack(record=writeback, owner_id=OWNER_ID, robot_id=ROBOT_ID, registry=registry).skill_pack_id == "memory_center_core"

    context_source = ContextScanCandidateSourceRecord(
        candidate_source_id="context-source-125p",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        authorization_id="auth-context-125p",
        source_type="mock_calendar_event",
        source_category="calendar_context",
        source_status="authorized_local_fixture",
        scan_scope="metadata_only",
        fixture_id="fixture-context-125p",
        source_title="Generic context source",
        source_summary="General robot context source.",
        source_timestamp="2026-06-20T11:00:00Z",
        source_origin="local_fixture",
        source_stage="118P",
        live_connector_allowed=False,
        external_read_allowed=False,
        external_write_allowed=False,
        memory_write_allowed=False,
        proactive_detection_allowed=False,
        telegram_send_allowed=False,
        worker_dispatch_allowed=False,
        sensitive_data_blocked=False,
        retention_policy="test-only",
        dedupe_key="context-source-dedupe-125p",
        lineage_summary={"source_stage": "118P"},
        created_at="2026-06-20T11:00:00Z",
    )
    assert classify_record_for_skill_pack(record=context_source, owner_id=OWNER_ID, robot_id=ROBOT_ID, registry=registry).skill_pack_id == "robot_core"

    unknown = UnknownRecord(owner_id=OWNER_ID, robot_id=ROBOT_ID, title="Odd item", summary="No known mapping.")
    assert classify_record_for_skill_pack(record=unknown, owner_id=OWNER_ID, robot_id=ROBOT_ID, registry=registry).skill_pack_id == "unknown_unclassified"


def test_125p_surface_aggregates_counts_and_preserves_boundaries():
    registry = SkillPackActivationRegistry()
    snapshot = DailyBriefSnapshotRecord(
        brief_id="brief-125p",
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        brief_date="2026-06-20",
        timezone="UTC",
        window_start="2026-06-20T00:00:00Z",
        window_end="2026-06-20T23:59:59Z",
        source_stage_min="103P",
        source_stage_max="123P",
        brief_stage="124P",
        brief_mode="deterministic_local_read_only",
        headline_summary="1 pending result, 1 document review, and 1 memory writeback found.",
        section_ids=("section-1",),
        total_item_count=3,
        needs_attention_count=1,
        pending_review_count=1,
        blocked_or_rejected_count=0,
        completed_count=1,
        proactive_opportunity_count=1,
        memory_review_count=1,
        memory_written_count=1,
        local_render_text="Brief render",
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
        dedupe_key="brief-dedupe-125p",
        lineage_summary={"brief_stage": "124P"},
        created_at="2026-06-20T15:00:00Z",
    )
    brief_item = _daily_brief_item(summary="What did I miss today?")
    doc_opportunity = _opportunity("document_review_needed", "NDA review", "Document review needed for NDA.")
    lead_opportunity = _opportunity("lead_followup_due", "Lead follow-up", "Lead follow-up is due today.")
    invoice_opportunity = _opportunity("invoice_due_soon", "Invoice due", "Invoice payment is due soon.")
    boundary_item = _daily_brief_item(
        section_name="blocked_or_rejected_items",
        source_stage="119P",
        title="Boundary review item",
        summary="Boundary review needed before action.",
    )
    unknown = UnknownRecord(owner_id=OWNER_ID, robot_id=ROBOT_ID, title="Odd item", summary="No known mapping.")
    cross_owner = _opportunity("meeting_brief_missing", "Cross owner meeting", "Should be excluded.")
    cross_owner = ProactiveOpportunityCandidateRecord(
        opportunity_id=cross_owner.opportunity_id,
        owner_id="other-owner",
        robot_id=ROBOT_ID,
        candidate_source_id=cross_owner.candidate_source_id,
        authorization_id=cross_owner.authorization_id,
        source_type=cross_owner.source_type,
        source_category=cross_owner.source_category,
        source_stage=cross_owner.source_stage,
        detection_stage=cross_owner.detection_stage,
        opportunity_type=cross_owner.opportunity_type,
        opportunity_category=cross_owner.opportunity_category,
        title=cross_owner.title,
        summary=cross_owner.summary,
        trigger_reason=cross_owner.trigger_reason,
        suggested_next_step_type=cross_owner.suggested_next_step_type,
        confidence=cross_owner.confidence,
        evidence_refs=cross_owner.evidence_refs,
        source_created_detection=cross_owner.source_created_detection,
        telegram_send_allowed=False,
        followup_adapter_allowed=False,
        async_delegation_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        live_connector_allowed=False,
        external_write_allowed=False,
        worker_dispatch_allowed=False,
        sensitive_data_blocked=False,
        dedupe_key="cross-owner-dedupe",
        lineage_summary={"detection_stage": "119P"},
        created_at="2026-06-20T12:30:00Z",
    )

    surface = create_skill_pack_activation_surface(
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        source_records=SkillPackSourceBundle(
            daily_brief_snapshots_124p=(snapshot,),
            daily_brief_items_124p=(brief_item, boundary_item),
            proactive_opportunities_119p=(doc_opportunity, lead_opportunity, invoice_opportunity, cross_owner),
        ),
        registry=registry,
    )

    assert surface.surface_stage == SKILL_PACK_STAGE
    assert surface.basic_package_count >= 1
    assert surface.documents_pack_count == 1
    assert surface.sales_pack_count == 1
    assert surface.finance_admin_pack_count == 1
    assert surface.safety_boundary_core_count == 1
    assert surface.billing_allowed is False
    assert surface.entitlement_enforcement_allowed is False
    assert surface.package_activation_allowed is False
    assert surface.upgrade_prompt_allowed is False
    assert surface.telegram_delivery_allowed is False
    assert surface.callback_binding_allowed is False
    assert surface.followup_intent_creation_allowed is False
    assert surface.async_delegation_allowed is False
    assert surface.execution_allowed is False
    assert surface.memory_write_allowed is False
    assert surface.model_call_allowed is False
    assert surface.tool_call_allowed is False
    assert surface.live_connector_allowed is False
    assert surface.external_write_allowed is False
    assert surface.worker_dispatch_allowed is False
    assert "documents_pack: 1" in surface.local_render_text
    assert "sales_pack: 1" in surface.local_render_text
    assert "finance_admin_pack: 1" in surface.local_render_text
    assert get_skill_pack_activation_surface(registry=registry, surface_id=surface.surface_id) == surface
    assert list_skill_pack_activation_surfaces(registry=registry) == (surface,)

    classifications = list_skill_pack_classifications(registry=registry)
    assert all(classification.owner_id == OWNER_ID for classification in classifications)
    assert all(classification.robot_id == ROBOT_ID for classification in classifications)
    assert not any(classification.source_title == "Cross owner meeting" for classification in classifications)
    assert classifications[0] == get_skill_pack_classification(
        registry=registry,
        classification_id=classifications[0].classification_id,
    )

    duplicate_surface = create_skill_pack_activation_surface(
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        source_records=SkillPackSourceBundle(
            daily_brief_snapshots_124p=(snapshot,),
            daily_brief_items_124p=(brief_item, boundary_item),
            proactive_opportunities_119p=(doc_opportunity, lead_opportunity, invoice_opportunity, cross_owner),
        ),
        registry=registry,
    )
    assert duplicate_surface == surface


def test_125p_rejects_missing_owner_robot_cross_scope_and_credentials():
    registry = SkillPackActivationRegistry()
    unknown = UnknownRecord(owner_id=OWNER_ID, robot_id=ROBOT_ID, title="Odd item", summary="No known mapping.")

    with pytest.raises(ValueError, match="rejected_missing_owner_id"):
        classify_record_for_skill_pack(record=unknown, owner_id="", robot_id=ROBOT_ID, registry=registry)

    with pytest.raises(ValueError, match="rejected_missing_robot_id"):
        classify_record_for_skill_pack(record=unknown, owner_id=OWNER_ID, robot_id="", registry=registry)

    with pytest.raises(ValueError, match="rejected_cross_owner_record"):
        classify_record_for_skill_pack(
            record=UnknownRecord(owner_id="other-owner", robot_id=ROBOT_ID, title="Odd item", summary="No known mapping."),
            owner_id=OWNER_ID,
            robot_id=ROBOT_ID,
            registry=registry,
        )

    with pytest.raises(ValueError, match="rejected_raw_credential_payload"):
        classify_record_for_skill_pack(
            record=UnknownRecord(owner_id=OWNER_ID, robot_id=ROBOT_ID, title="API Key", summary="api_key: secret-value"),
            owner_id=OWNER_ID,
            robot_id=ROBOT_ID,
            registry=registry,
        )


def test_125p_empty_surface_is_valid():
    registry = SkillPackActivationRegistry()
    surface = create_skill_pack_activation_surface(
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        source_records=SkillPackSourceBundle(),
        registry=registry,
    )

    assert surface.total_classified_count == 0
    assert "No classified skill pack activity was found." in surface.local_render_text
