from __future__ import annotations

import pytest

from app.meeting_brief_demo_flow import (
    EXECUTION_OPTION_KIND,
    EXECUTION_TASK_CLASS,
    MeetingBriefDemoDependencyBundle,
    build_default_meeting_brief_demo_fixture,
    get_meeting_brief_demo_artifact,
    list_meeting_brief_demo_flows,
    run_local_meeting_brief_demo_flow,
    assemble_meeting_brief_demo_flow,
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
    dependencies = MeetingBriefDemoDependencyBundle()
    flow = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-20T18:00:00Z",
    )
    artifact = get_meeting_brief_demo_artifact(
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


def test_126p_happy_path_preserves_prepare_meeting_brief_but_reuses_existing_governed_task_class():
    state = build_demo_state()
    flow = state["flow"]
    artifact = state["artifact"]
    proactive_delegation = state["proactive_delegation"]
    selection = state["selection"]
    followup_delegation = state["followup_delegation"]
    execution_attempt = state["execution_attempt"]

    assert flow.demo_status == "completed_local_demo"
    assert proactive_delegation.normalized_intent_kind == "prepare_meeting_brief"
    assert selection.selected_option_kind == EXECUTION_OPTION_KIND
    assert proactive_delegation.mapped_task_class == EXECUTION_TASK_CLASS
    assert followup_delegation.followup_task_class == EXECUTION_TASK_CLASS
    assert execution_attempt.mapped_task_class == EXECUTION_TASK_CLASS
    assert proactive_delegation.uses_existing_delegation_authority is True
    assert execution_attempt.model_call_allowed is False
    assert execution_attempt.tool_call_allowed is False
    assert execution_attempt.live_connector_allowed is False
    assert execution_attempt.external_write_allowed is False
    assert artifact.local_render_text
    assert "normalized_intent_kind remained prepare_meeting_brief" in artifact.local_render_text
    assert f"Delegated executable class reused existing {EXECUTION_OPTION_KIND} / {EXECUTION_TASK_CLASS}." in artifact.local_render_text
    assert "Preparation checklist:" in artifact.local_render_text
    assert "No live connectors used." in artifact.local_render_text
    assert "No external messages sent." in artifact.local_render_text
    assert "No model/tool calls used." in artifact.local_render_text
    assert "No Memory Center mutation performed by 126P." in artifact.local_render_text


def test_126p_daily_brief_and_skill_pack_surfaces_include_demo_records():
    state = build_demo_state()
    daily_brief = state["daily_brief"]
    skill_pack_surface = state["skill_pack_surface"]
    classifications = list_skill_pack_classifications(registry=state["dependencies"].skill_pack_registry)

    assert daily_brief.brief_stage == "124P"
    assert "proactive" in daily_brief.local_render_text.lower()
    assert skill_pack_surface.surface_stage == "125P"
    assert skill_pack_surface.basic_package_count >= 1
    assert any(record.skill_pack_id == "basic_package" for record in classifications)


def test_126p_duplicate_demo_run_is_duplicate_safe():
    dependencies = MeetingBriefDemoDependencyBundle()
    first = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-20T18:00:00Z",
    )
    second = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-20T18:00:00Z",
    )

    assert first.demo_flow_id == second.demo_flow_id
    assert first.demo_artifact_id == second.demo_artifact_id
    assert len(list_meeting_brief_demo_flows(registry=dependencies.demo_registry)) == 1


def test_126p_rejects_missing_owner_id():
    with pytest.raises(ValueError, match="rejected_missing_owner_id"):
        run_local_meeting_brief_demo_flow(
            owner_id="",
            robot_id="demo_robot",
            chat_id="demo_chat",
            dependencies=MeetingBriefDemoDependencyBundle(),
        )


def test_126p_rejects_live_connector_source_fixture():
    with pytest.raises(ValueError, match="rejected_live_connector_source_type"):
        run_local_meeting_brief_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
            dependencies=MeetingBriefDemoDependencyBundle(),
            fixture=unsafe_replace_record(
                build_default_meeting_brief_demo_fixture(),
                source_type="live_google_calendar",
            ),
        )


def test_126p_rejects_cross_owner_records_on_assembly():
    state = build_demo_state()
    with pytest.raises(ValueError, match="rejected_cross_owner_record"):
        assemble_meeting_brief_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
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
            registry=MeetingBriefDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_126p_rejects_missing_119p_lineage_on_assembly():
    state = build_demo_state()
    broken_opportunity = unsafe_replace_record(state["opportunity"], candidate_source_id="other-source")
    with pytest.raises(ValueError, match="rejected_missing_118p_context_source_lineage"):
        assemble_meeting_brief_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
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
            registry=MeetingBriefDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_126p_rejects_live_telegram_dependency_on_assembly():
    state = build_demo_state()
    broken_delivery = unsafe_replace_record(state["suggestion_delivery"], live_send_allowed=True)
    with pytest.raises(ValueError, match="rejected_live_telegram_delivery"):
        assemble_meeting_brief_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
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
            registry=MeetingBriefDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )


def test_126p_rejects_model_or_tool_dependency_on_assembly():
    state = build_demo_state()
    broken_execution = unsafe_replace_record(state["execution_attempt"], model_call_allowed=True)
    with pytest.raises(ValueError, match="rejected_model_tool_dependency"):
        assemble_meeting_brief_demo_flow(
            owner_id="demo_owner",
            robot_id="demo_robot",
            chat_id="demo_chat",
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
            proactive_execution_attempt_record=broken_execution,
            daily_brief_snapshot_record=state["daily_brief"],
            skill_pack_surface_record=state["skill_pack_surface"],
            registry=MeetingBriefDemoDependencyBundle().demo_registry,
            skill_pack_registry=state["dependencies"].skill_pack_registry,
        )
