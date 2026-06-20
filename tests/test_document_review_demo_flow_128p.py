from __future__ import annotations

import pytest

from app.demo_result_delivery_surface import DemoResultDeliverySurfaceRegistry, render_demo_result_delivery_surface
from app.document_review_demo_flow import (
    EXECUTION_OPTION_KIND,
    EXECUTION_TASK_CLASS,
    DocumentReviewDemoDependencyBundle,
    assemble_document_review_demo_flow,
    build_default_document_review_demo_fixture,
    get_document_review_demo_artifact,
    list_document_review_demo_flows,
    run_local_document_review_demo_flow,
)
from app.meeting_brief_demo_flow import (
    MeetingBriefDemoDependencyBundle,
    build_default_meeting_brief_demo_fixture,
    get_meeting_brief_demo_artifact,
    run_local_meeting_brief_demo_flow,
)
from app.skill_pack_activation_surface import list_skill_pack_classifications


def unsafe_replace_record(record, **overrides):
    values = {field_name: getattr(record, field_name) for field_name in record.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(record.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


def build_demo_state():
    dependencies = DocumentReviewDemoDependencyBundle()
    flow = run_local_document_review_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_document_review_demo_fixture(),
        created_at="2026-06-21T10:00:00Z",
    )
    artifact = get_document_review_demo_artifact(
        registry=dependencies.demo_registry,
        demo_artifact_id=flow.demo_artifact_id,
    )
    assert artifact is not None
    return {
        "dependencies": dependencies,
        "flow": flow,
        "artifact": artifact,
        "context_source": next(iter(dependencies.context_registry.candidates_by_id.values())),
        "opportunity": next(iter(dependencies.opportunity_registry.opportunities_by_id.values())),
        "suggestion_surface": next(iter(dependencies.suggestion_registry.surfaces_by_id.values())),
        "suggestion_delivery": next(iter(dependencies.suggestion_registry.deliveries_by_id.values())),
        "proactive_adapter": next(iter(dependencies.suggestion_adapter_registry.adapters_by_id.values())),
        "followup_intent": next(iter(dependencies.followup_queue.records_by_id.values())),
        "followup_plan": next(iter(dependencies.draft_plan_registry.plans_by_id.values())),
        "choice_surface": next(iter(dependencies.choice_surface_registry.records_by_id.values())),
        "selection": next(iter(dependencies.choice_selection_registry.selections_by_id.values())),
        "followup_delegation": next(iter(dependencies.followup_delegation_registry.records_by_id.values())),
        "proactive_delegation_authorization": next(iter(dependencies.proactive_delegation_registry.authorizations_by_id.values())),
        "proactive_delegation": next(iter(dependencies.proactive_delegation_registry.records_by_id.values())),
        "execution_attempt": next(iter(dependencies.execution_registry.attempts_by_id.values())),
        "daily_brief": next(iter(dependencies.daily_brief_registry.snapshots_by_id.values())),
        "skill_pack_surface": next(iter(dependencies.skill_pack_registry.surfaces_by_id.values())),
    }


def build_valid_127p_surface():
    dependencies = MeetingBriefDemoDependencyBundle()
    flow = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-21T09:00:00Z",
    )
    artifact = get_meeting_brief_demo_artifact(
        registry=dependencies.demo_registry,
        demo_artifact_id=flow.demo_artifact_id,
    )
    assert artifact is not None
    return render_demo_result_delivery_surface(
        owner_id="demo_owner",
        robot_id="demo_robot",
        demo_flow_record=flow,
        demo_artifact_record=artifact,
        registry=DemoResultDeliverySurfaceRegistry(),
        created_at="2026-06-21T09:10:00Z",
    )


def test_128p_happy_path_preserves_review_document_but_reuses_existing_governed_task_class():
    state = build_demo_state()
    flow = state["flow"]
    artifact = state["artifact"]
    proactive_delegation = state["proactive_delegation"]
    selection = state["selection"]
    followup_delegation = state["followup_delegation"]
    execution_attempt = state["execution_attempt"]

    assert flow.demo_status == "completed_local_demo"
    assert flow.normalized_intent_kind == "review_document"
    assert flow.execution_task_class == EXECUTION_TASK_CLASS
    assert flow.skill_pack_id == "documents_pack"
    assert flow.demo_result_surface_id is None
    assert proactive_delegation.normalized_intent_kind == "review_document"
    assert selection.selected_option_kind == EXECUTION_OPTION_KIND
    assert proactive_delegation.mapped_task_class == EXECUTION_TASK_CLASS
    assert followup_delegation.followup_task_class == EXECUTION_TASK_CLASS
    assert execution_attempt.mapped_task_class == EXECUTION_TASK_CLASS
    assert proactive_delegation.uses_existing_delegation_authority is True
    assert artifact.local_render_text
    assert "Normalized intent kind remained review_document." in artifact.local_render_text
    assert f"Delegated executable class reused existing {EXECUTION_OPTION_KIND} / {EXECUTION_TASK_CLASS}." in artifact.local_render_text
    assert "No new document-specific executable task class was created." in artifact.local_render_text
    assert "No live document connector used." in artifact.local_render_text
    assert "No OCR was performed." in artifact.local_render_text
    assert "No legal advice provided." in artifact.local_render_text
    assert "No certified signature or legal signature created." in artifact.local_render_text
    assert "No model/tool calls used." in artifact.local_render_text
    assert "No external file was written." in artifact.local_render_text
    assert "No Memory Center mutation performed by 128P." in artifact.local_render_text
    assert artifact.review_checklist
    assert artifact.possible_risk_notes
    assert artifact.open_questions
    assert artifact.suggested_materials


def test_128p_daily_brief_and_skill_pack_surfaces_include_documents_pack_demo_records():
    state = build_demo_state()
    skill_pack_surface = state["skill_pack_surface"]
    classifications = list_skill_pack_classifications(registry=state["dependencies"].skill_pack_registry)

    assert state["daily_brief"].brief_stage == "124P"
    assert skill_pack_surface.surface_stage == "125P"
    assert skill_pack_surface.documents_pack_count >= 1
    assert any(record.skill_pack_id == "documents_pack" for record in classifications)


def test_128p_duplicate_demo_run_is_duplicate_safe():
    dependencies = DocumentReviewDemoDependencyBundle()
    first = run_local_document_review_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_document_review_demo_fixture(),
        created_at="2026-06-21T10:00:00Z",
    )
    second = run_local_document_review_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_document_review_demo_fixture(),
        created_at="2026-06-21T10:00:00Z",
    )

    assert first.document_demo_flow_id == second.document_demo_flow_id
    assert first.demo_artifact_id == second.demo_artifact_id
    assert len(list_document_review_demo_flows(registry=dependencies.demo_registry)) == 1


def test_128p_can_preserve_optional_127p_surface_lineage_when_provided():
    state = build_demo_state()
    result_surface = build_valid_127p_surface()

    assembled = assemble_document_review_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        fixture=build_default_document_review_demo_fixture(),
        context_source_record=state["context_source"],
        opportunity_record=state["opportunity"],
        suggestion_surface_record=state["suggestion_surface"],
        suggestion_delivery_record=state["suggestion_delivery"],
        proactive_adapter_record=state["proactive_adapter"],
        followup_intent_review_record=state["followup_intent"],
        followup_plan_record=state["followup_plan"],
        followup_choice_surface_record=state["choice_surface"],
        followup_selection_record=state["selection"],
        proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
        followup_delegation_record=state["followup_delegation"],
        proactive_delegation_adapter_record=state["proactive_delegation"],
        proactive_execution_attempt_record=state["execution_attempt"],
        daily_brief_snapshot_record=state["daily_brief"],
        skill_pack_surface_record=state["skill_pack_surface"],
        demo_result_surface_record=result_surface,
        registry=DocumentReviewDemoDependencyBundle().demo_registry,
        skill_pack_registry=state["dependencies"].skill_pack_registry,
        require_demo_result_surface=True,
    )

    assert assembled.demo_result_surface_id == result_surface.demo_result_surface_id


def test_128p_rejects_missing_required_127p_surface_lineage():
    state = build_demo_state()
    with pytest.raises(ValueError, match="rejected_missing_127p_presentational_surface_lineage"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
            require_demo_result_surface=True,
        )


def test_128p_rejects_live_document_source_fixture():
    with pytest.raises(ValueError, match="rejected_live_document_source"):
        run_local_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            dependencies=DocumentReviewDemoDependencyBundle(),
            fixture=unsafe_replace_record(build_default_document_review_demo_fixture(), source_type="live_google_drive_document"),
        )


def test_128p_rejects_ocr_dependency_fixture():
    with pytest.raises(ValueError, match="rejected_ocr_dependency"):
        run_local_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            dependencies=DocumentReviewDemoDependencyBundle(),
            fixture=unsafe_replace_record(build_default_document_review_demo_fixture(), ocr_performed=True),
        )


def test_128p_rejects_cross_owner_records_on_assembly():
    state = build_demo_state()
    with pytest.raises(ValueError, match="rejected_cross_owner_record"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=unsafe_replace_record(state["context_source"], owner_id="other_owner"),
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_128p_rejects_missing_119p_lineage_on_assembly():
    state = build_demo_state()
    broken_opportunity = unsafe_replace_record(state["opportunity"], candidate_source_id="other-source")
    with pytest.raises(ValueError, match="rejected_missing_118p_context_source_lineage"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=broken_opportunity,
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_128p_rejects_live_telegram_dependency_on_assembly():
    state = build_demo_state()
    broken_delivery = unsafe_replace_record(state["suggestion_delivery"], live_send_allowed=True)
    with pytest.raises(ValueError, match="rejected_live_telegram_delivery"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=broken_delivery,
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_128p_rejects_ocr_model_tool_external_write_worker_legal_and_signature_dependencies_on_assembly():
    state = build_demo_state()
    bad_context_for_ocr = unsafe_replace_record(state["context_source"], source_summary="OCR performed on uploaded PDF")
    with pytest.raises(ValueError, match="rejected_ocr_dependency"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=bad_context_for_ocr,
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )

    with pytest.raises(ValueError, match="rejected_model_tool_dependency"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=unsafe_replace_record(state["execution_attempt"], model_call_allowed=True),
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )

    with pytest.raises(ValueError, match="rejected_external_write_dependency"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=unsafe_replace_record(state["execution_attempt"], external_write_allowed=True),
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )

    with pytest.raises(ValueError, match="rejected_worker_dispatch_dependency"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=state["context_source"],
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=unsafe_replace_record(state["execution_attempt"], worker_dispatch_allowed=True),
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )

    with pytest.raises(ValueError, match="rejected_legal_claim"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=unsafe_replace_record(state["context_source"], source_summary="This is legal advice for the contract."),
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )

    with pytest.raises(ValueError, match="rejected_certified_signature_claim"):
        assemble_document_review_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            fixture=build_default_document_review_demo_fixture(),
            context_source_record=unsafe_replace_record(state["context_source"], source_summary="Certified signature created for this document."),
            opportunity_record=state["opportunity"],
            suggestion_surface_record=state["suggestion_surface"],
            suggestion_delivery_record=state["suggestion_delivery"],
            proactive_adapter_record=state["proactive_adapter"],
            followup_intent_review_record=state["followup_intent"],
            followup_plan_record=state["followup_plan"],
            followup_choice_surface_record=state["choice_surface"],
            followup_selection_record=state["selection"],
            proactive_delegation_authorization_record=state["proactive_delegation_authorization"],
            followup_delegation_record=state["followup_delegation"],
            proactive_delegation_adapter_record=state["proactive_delegation"],
            proactive_execution_attempt_record=state["execution_attempt"],
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=DocumentReviewDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )
