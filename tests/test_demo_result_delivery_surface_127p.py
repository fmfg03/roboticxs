from __future__ import annotations

import pytest

from app.demo_result_delivery_surface import (
    DEMO_RESULT_DELIVERY_SURFACE_MODE,
    DEMO_RESULT_DELIVERY_SURFACE_STAGE,
    DemoResultDeliverySurfaceRegistry,
    get_demo_result_delivery_surface,
    list_demo_result_delivery_surfaces,
    render_demo_result_delivery_surface,
    render_demo_result_delivery_surface_text,
)
from app.meeting_brief_demo_flow import (
    MeetingBriefDemoDependencyBundle,
    build_default_meeting_brief_demo_fixture,
    get_meeting_brief_demo_artifact,
    run_local_meeting_brief_demo_flow,
)


def unsafe_replace_record(record, **overrides):
    values = {field_name: getattr(record, field_name) for field_name in record.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(record.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


def build_demo_surface_state():
    dependencies = MeetingBriefDemoDependencyBundle()
    flow = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-21T08:00:00Z",
    )
    artifact = get_meeting_brief_demo_artifact(
        registry=dependencies.demo_registry,
        demo_artifact_id=flow.demo_artifact_id,
    )
    assert artifact is not None
    surface_registry = DemoResultDeliverySurfaceRegistry()
    surface = render_demo_result_delivery_surface(
        owner_id="demo_owner",
        robot_id="demo_robot",
        demo_flow_record=flow,
        demo_artifact_record=artifact,
        registry=surface_registry,
        created_at="2026-06-21T08:10:00Z",
    )
    return {
        "flow": flow,
        "artifact": artifact,
        "surface": surface,
        "registry": surface_registry,
    }


def test_127p_renders_owner_facing_demo_result_surface_from_126p_records():
    state = build_demo_surface_state()
    flow = state["flow"]
    artifact = state["artifact"]
    surface = state["surface"]

    assert surface.source_stage == "126P"
    assert surface.surface_stage == DEMO_RESULT_DELIVERY_SURFACE_STAGE
    assert surface.surface_mode == DEMO_RESULT_DELIVERY_SURFACE_MODE
    assert surface.owner_id == flow.owner_id
    assert surface.robot_id == flow.robot_id
    assert surface.chat_id == flow.chat_id
    assert surface.demo_flow_id == flow.demo_flow_id
    assert surface.demo_artifact_id == artifact.demo_artifact_id
    assert surface.daily_brief_id == flow.daily_brief_id
    assert surface.skill_pack_surface_id == flow.skill_pack_surface_id
    assert surface.context_source_id == flow.context_source_id
    assert surface.opportunity_id == flow.opportunity_id
    assert surface.suggestion_surface_id == flow.suggestion_surface_id
    assert surface.suggestion_delivery_record_id == flow.suggestion_delivery_record_id
    assert surface.proactive_adapter_id == flow.proactive_adapter_id
    assert surface.proactive_delegation_adapter_id == flow.proactive_delegation_adapter_id
    assert surface.proactive_execution_attempt_id == flow.proactive_execution_attempt_id
    assert surface.proactive_execution_event_candidate_id == flow.proactive_execution_event_candidate_id
    assert surface.result_title == artifact.title
    assert surface.what_hermes_noticed == artifact.meeting_context_summary
    assert surface.prepared_brief_summary == artifact.demo_summary
    assert surface.preparation_checklist == artifact.preparation_checklist
    assert surface.open_questions == artifact.open_questions
    assert surface.suggested_materials == artifact.suggested_materials
    assert surface.skill_pack_summary == artifact.skill_pack_summary
    assert surface.daily_brief_summary == artifact.daily_brief_summary
    assert "No live connectors were used." in surface.safety_boundaries
    assert "No real Telegram message was sent." in surface.safety_boundaries
    assert "No model or tool call was made." in surface.safety_boundaries
    assert "No external system was written." in surface.safety_boundaries
    assert "No Memory Center mutation was performed by 127P." in surface.safety_boundaries
    assert "No new task class or authority path was created." in surface.safety_boundaries
    assert "This is a deterministic local demo surface." in surface.safety_boundaries
    assert "No live delivery, callback binding" in surface.no_action_taken_notice
    assert surface.display_text
    assert "Result Title" in surface.display_text
    assert "What Hermes Noticed" in surface.display_text
    assert "Prepared Brief" in surface.display_text
    assert "Skill Pack Summary" in surface.display_text
    assert "Daily Brief Summary" in surface.display_text
    assert "Safety Boundaries" in surface.display_text
    assert "No Action Taken Notice" in surface.display_text
    assert surface.live_telegram_allowed is False
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
    assert surface.billing_allowed is False
    assert surface.entitlement_enforcement_allowed is False
    assert surface.sensitive_data_excluded is True


def test_127p_duplicate_rendering_is_duplicate_safe():
    dependencies = MeetingBriefDemoDependencyBundle()
    flow = run_local_meeting_brief_demo_flow(
        owner_id="demo_owner",
        robot_id="demo_robot",
        chat_id="demo_chat",
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture(),
        created_at="2026-06-21T08:00:00Z",
    )
    artifact = get_meeting_brief_demo_artifact(
        registry=dependencies.demo_registry,
        demo_artifact_id=flow.demo_artifact_id,
    )
    assert artifact is not None
    registry = DemoResultDeliverySurfaceRegistry()
    first = render_demo_result_delivery_surface(
        owner_id="demo_owner",
        robot_id="demo_robot",
        demo_flow_record=flow,
        demo_artifact_record=artifact,
        registry=registry,
        created_at="2026-06-21T08:10:00Z",
    )
    second = render_demo_result_delivery_surface(
        owner_id="demo_owner",
        robot_id="demo_robot",
        demo_flow_record=flow,
        demo_artifact_record=artifact,
        registry=registry,
        created_at="2026-06-21T08:11:00Z",
    )

    assert first.demo_result_surface_id == second.demo_result_surface_id
    assert len(list_demo_result_delivery_surfaces(registry=registry)) == 1
    assert get_demo_result_delivery_surface(registry=registry, demo_result_surface_id=first.demo_result_surface_id) == first


def test_127p_rejects_missing_owner_id():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_missing_owner_id"):
        render_demo_result_delivery_surface(
            owner_id="",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_cross_owner_records():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_cross_owner_record"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=unsafe_replace_record(state["flow"], owner_id="other_owner"),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_missing_robot_id():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_missing_robot_id"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="",
            demo_flow_record=state["flow"],
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_cross_robot_records():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_cross_robot_record"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=unsafe_replace_record(state["artifact"], robot_id="other_robot"),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_unknown_demo_flow_record():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_unknown_demo_flow_record"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=object(),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_unknown_demo_artifact_record():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_unknown_demo_artifact_record"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=object(),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_mismatched_flow_artifact_lineage():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_mismatched_flow_artifact_lineage"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=unsafe_replace_record(state["artifact"], demo_flow_id="other-flow-id"),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_live_connector_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_live_connector_usage"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=unsafe_replace_record(state["flow"], live_connector_allowed=True),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_live_telegram_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_live_telegram_delivery"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=unsafe_replace_record(state["flow"], live_telegram_allowed=True),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_memory_write_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_memory_write_dependency"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=unsafe_replace_record(state["artifact"], memory_mutated_by_126p=True),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_model_or_tool_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_model_tool_dependency"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=unsafe_replace_record(state["flow"], model_call_allowed=True),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_external_write_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_external_write_dependency"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=unsafe_replace_record(state["artifact"], external_system_written=True),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_worker_dispatch_dependency():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_worker_dispatch_dependency"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=unsafe_replace_record(state["flow"], worker_dispatch_allowed=True),
            demo_artifact_record=state["artifact"],
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_rejects_sensitive_payload_or_credentials():
    state = build_demo_surface_state()
    with pytest.raises(ValueError, match="rejected_raw_credentials"):
        render_demo_result_delivery_surface(
            owner_id="demo_owner",
            robot_id="demo_robot",
            demo_flow_record=state["flow"],
            demo_artifact_record=unsafe_replace_record(state["artifact"], title="Meeting Brief Demo: password token"),
            registry=DemoResultDeliverySurfaceRegistry(),
        )


def test_127p_render_text_helper_is_deterministic():
    text_one = render_demo_result_delivery_surface_text(
        result_title="Meeting Brief Demo: Victor / ASISINT follow-up",
        what_hermes_noticed="Upcoming meeting has a missing brief based on authorized local context.",
        prepared_brief_summary="Hermes prepared a deterministic local meeting-brief-style checklist.",
        meeting_context="Upcoming meeting has a missing brief based on authorized local context.",
        preparation_checklist=("Step 1", "Step 2"),
        open_questions=("Question 1",),
        suggested_materials=("Material 1",),
        skill_pack_summary="Classified under basic_package.",
        daily_brief_summary="Included in daily brief.",
        safety_boundaries=("No live connectors were used.",),
        lineage_summary="118P -> 119P -> 120P -> 126P",
        no_action_taken_notice="No actions were taken.",
    )
    text_two = render_demo_result_delivery_surface_text(
        result_title="Meeting Brief Demo: Victor / ASISINT follow-up",
        what_hermes_noticed="Upcoming meeting has a missing brief based on authorized local context.",
        prepared_brief_summary="Hermes prepared a deterministic local meeting-brief-style checklist.",
        meeting_context="Upcoming meeting has a missing brief based on authorized local context.",
        preparation_checklist=("Step 1", "Step 2"),
        open_questions=("Question 1",),
        suggested_materials=("Material 1",),
        skill_pack_summary="Classified under basic_package.",
        daily_brief_summary="Included in daily brief.",
        safety_boundaries=("No live connectors were used.",),
        lineage_summary="118P -> 119P -> 120P -> 126P",
        no_action_taken_notice="No actions were taken.",
    )

    assert text_one == text_two
