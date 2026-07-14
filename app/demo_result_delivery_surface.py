from __future__ import annotations

from dataclasses import dataclass, field
import json
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_candidate_source import CREDENTIAL_KEYWORDS, SENSITIVE_KEYWORDS
from app.meeting_brief_demo_flow import (
    FIRST_DEMO_MEETING_BRIEF_MODE,
    FIRST_DEMO_MEETING_BRIEF_STAGE,
    FirstDemoMeetingBriefArtifactRecord,
    FirstDemoMeetingBriefFlowRecord,
)


DEMO_RESULT_DELIVERY_SURFACE_STAGE = "127P"
DEMO_RESULT_DELIVERY_SURFACE_MODE = "deterministic_local_owner_facing"
DEFAULT_CREATED_AT = "2026-06-21T00:00:00Z"
NO_ACTION_TAKEN_NOTICE = (
    "No live delivery, callback binding, approval, follow-up intent, delegation, execution, memory mutation, billing, or external action was created by 127P."
)
REQUIRED_SAFETY_NOTICES = (
    "No live connectors were used.",
    "No real Telegram message was sent.",
    "No model or tool call was made.",
    "No external system was written.",
    "No Memory Center mutation was performed by 127P.",
    "No new task class or authority path was created.",
    "This is a deterministic local demo surface.",
)


@dataclass(frozen=True, slots=True)
class DemoResultDeliverySurfaceRecord:
    demo_result_surface_id: str
    owner_id: str
    robot_id: str
    chat_id: str
    source_stage: str
    surface_stage: str
    demo_flow_id: str
    demo_artifact_id: str
    daily_brief_id: str
    skill_pack_surface_id: str
    context_source_id: str
    opportunity_id: str
    suggestion_surface_id: str
    suggestion_delivery_record_id: str
    proactive_adapter_id: str
    proactive_delegation_adapter_id: str
    proactive_execution_attempt_id: str
    proactive_execution_event_candidate_id: str | None
    surface_mode: str
    result_title: str
    display_text: str
    what_hermes_noticed: str
    prepared_brief_summary: str
    preparation_checklist: tuple[str, ...]
    open_questions: tuple[str, ...]
    suggested_materials: tuple[str, ...]
    skill_pack_summary: str
    daily_brief_summary: str
    safety_boundaries: tuple[str, ...]
    no_action_taken_notice: str
    live_telegram_allowed: bool
    telegram_delivery_allowed: bool
    callback_binding_allowed: bool
    followup_intent_creation_allowed: bool
    async_delegation_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    live_connector_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool
    billing_allowed: bool
    entitlement_enforcement_allowed: bool
    sensitive_data_excluded: bool
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.source_stage != FIRST_DEMO_MEETING_BRIEF_STAGE:
            raise ValueError("rejected_missing_126p_demo_flow_lineage")
        if self.surface_stage != DEMO_RESULT_DELIVERY_SURFACE_STAGE:
            raise ValueError("rejected_invalid_surface_stage")
        if self.surface_mode != DEMO_RESULT_DELIVERY_SURFACE_MODE:
            raise ValueError("rejected_invalid_surface_mode")
        if any(
            (
                self.live_telegram_allowed,
                self.telegram_delivery_allowed,
                self.callback_binding_allowed,
                self.followup_intent_creation_allowed,
                self.async_delegation_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.live_connector_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
                self.billing_allowed,
                self.entitlement_enforcement_allowed,
            )
        ):
            raise ValueError("rejected_live_dependency")


@dataclass(slots=True)
class DemoResultDeliverySurfaceRegistry:
    surfaces_by_id: dict[str, DemoResultDeliverySurfaceRecord] = field(default_factory=dict)
    surface_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_surface(self, record: DemoResultDeliverySurfaceRecord) -> DemoResultDeliverySurfaceRecord:
        self.surfaces_by_id[record.demo_result_surface_id] = record
        self.surface_ids_by_dedupe_key[record.dedupe_key] = record.demo_result_surface_id
        return record

    def get_surface(self, demo_result_surface_id: str) -> DemoResultDeliverySurfaceRecord | None:
        return self.surfaces_by_id.get(demo_result_surface_id)

    def get_surface_by_dedupe_key(self, dedupe_key: str) -> DemoResultDeliverySurfaceRecord | None:
        surface_id = self.surface_ids_by_dedupe_key.get(dedupe_key)
        if surface_id is None:
            return None
        return self.surfaces_by_id.get(surface_id)

    def list_surfaces(self, *, owner_id: str | None = None, robot_id: str | None = None) -> tuple[DemoResultDeliverySurfaceRecord, ...]:
        records = tuple(self.surfaces_by_id[key] for key in sorted(self.surfaces_by_id))
        if owner_id is not None:
            records = tuple(record for record in records if record.owner_id == owner_id)
        if robot_id is not None:
            records = tuple(record for record in records if record.robot_id == robot_id)
        return records


def render_demo_result_delivery_surface(
    *,
    owner_id: str,
    robot_id: str,
    demo_flow_record: object,
    demo_artifact_record: object,
    registry: DemoResultDeliverySurfaceRegistry,
    created_at: str = DEFAULT_CREATED_AT,
) -> DemoResultDeliverySurfaceRecord:
    if not owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not robot_id:
        raise ValueError("rejected_missing_robot_id")
    flow = _require_flow_record(demo_flow_record)
    artifact = _require_artifact_record(demo_artifact_record)
    _validate_identity(record=flow, owner_id=owner_id, robot_id=robot_id)
    _validate_identity(record=artifact, owner_id=owner_id, robot_id=robot_id)
    _validate_flow_artifact_lineage(flow=flow, artifact=artifact)
    _reject_live_flags(flow)
    _reject_live_flags(artifact)
    _reject_sensitive_text(flow.chat_id)
    dedupe_key = _stable_id(
        "demo_result_delivery_surface",
        owner_id,
        robot_id,
        flow.demo_flow_id,
        artifact.demo_artifact_id,
    )
    existing = registry.get_surface_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    what_hermes_noticed = _what_hermes_noticed(artifact=artifact)
    prepared_brief_summary = _prepared_brief_summary(artifact=artifact)
    safety_boundaries = _surface_safety_boundaries(artifact=artifact)
    display_text = render_demo_result_delivery_surface_text(
        result_title=artifact.title,
        what_hermes_noticed=what_hermes_noticed,
        prepared_brief_summary=prepared_brief_summary,
        meeting_context=artifact.meeting_context_summary,
        preparation_checklist=artifact.preparation_checklist,
        open_questions=artifact.open_questions,
        suggested_materials=artifact.suggested_materials,
        skill_pack_summary=artifact.skill_pack_summary,
        daily_brief_summary=artifact.daily_brief_summary,
        safety_boundaries=safety_boundaries,
        lineage_summary=_render_lineage_summary_text(
            {
                "source_stage": FIRST_DEMO_MEETING_BRIEF_STAGE,
                "surface_stage": DEMO_RESULT_DELIVERY_SURFACE_STAGE,
                "demo_flow_id": flow.demo_flow_id,
                "demo_artifact_id": artifact.demo_artifact_id,
                "context_source_id": flow.context_source_id,
                "opportunity_id": flow.opportunity_id,
                "skill_pack_surface_id": flow.skill_pack_surface_id,
                "daily_brief_id": flow.daily_brief_id,
            }
        ),
        no_action_taken_notice=NO_ACTION_TAKEN_NOTICE,
    )
    record = DemoResultDeliverySurfaceRecord(
        demo_result_surface_id=_stable_id("demo_result_delivery_surface_id", dedupe_key),
        owner_id=owner_id,
        robot_id=robot_id,
        chat_id=flow.chat_id,
        source_stage=FIRST_DEMO_MEETING_BRIEF_STAGE,
        surface_stage=DEMO_RESULT_DELIVERY_SURFACE_STAGE,
        demo_flow_id=flow.demo_flow_id,
        demo_artifact_id=artifact.demo_artifact_id,
        daily_brief_id=flow.daily_brief_id,
        skill_pack_surface_id=flow.skill_pack_surface_id,
        context_source_id=flow.context_source_id,
        opportunity_id=flow.opportunity_id,
        suggestion_surface_id=flow.suggestion_surface_id,
        suggestion_delivery_record_id=flow.suggestion_delivery_record_id,
        proactive_adapter_id=flow.proactive_adapter_id,
        proactive_delegation_adapter_id=flow.proactive_delegation_adapter_id,
        proactive_execution_attempt_id=flow.proactive_execution_attempt_id,
        proactive_execution_event_candidate_id=flow.proactive_execution_event_candidate_id,
        surface_mode=DEMO_RESULT_DELIVERY_SURFACE_MODE,
        result_title=artifact.title,
        display_text=display_text,
        what_hermes_noticed=what_hermes_noticed,
        prepared_brief_summary=prepared_brief_summary,
        preparation_checklist=artifact.preparation_checklist,
        open_questions=artifact.open_questions,
        suggested_materials=artifact.suggested_materials,
        skill_pack_summary=artifact.skill_pack_summary,
        daily_brief_summary=artifact.daily_brief_summary,
        safety_boundaries=safety_boundaries,
        no_action_taken_notice=NO_ACTION_TAKEN_NOTICE,
        live_telegram_allowed=False,
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
        billing_allowed=False,
        entitlement_enforcement_allowed=False,
        sensitive_data_excluded=True,
        dedupe_key=dedupe_key,
        lineage_summary={
            "source_stage": FIRST_DEMO_MEETING_BRIEF_STAGE,
            "surface_stage": DEMO_RESULT_DELIVERY_SURFACE_STAGE,
            "demo_mode": flow.demo_mode,
            "surface_mode": DEMO_RESULT_DELIVERY_SURFACE_MODE,
            "demo_flow_id": flow.demo_flow_id,
            "demo_artifact_id": artifact.demo_artifact_id,
            "daily_brief_id": flow.daily_brief_id,
            "skill_pack_surface_id": flow.skill_pack_surface_id,
            "context_source_id": flow.context_source_id,
            "opportunity_id": flow.opportunity_id,
            "suggestion_surface_id": flow.suggestion_surface_id,
            "suggestion_delivery_record_id": flow.suggestion_delivery_record_id,
            "proactive_adapter_id": flow.proactive_adapter_id,
            "proactive_delegation_adapter_id": flow.proactive_delegation_adapter_id,
            "proactive_execution_attempt_id": flow.proactive_execution_attempt_id,
            "proactive_execution_event_candidate_id": flow.proactive_execution_event_candidate_id,
            "product_intent_kind": flow.lineage_summary.get("product_intent_kind"),
            "delegated_task_class": flow.lineage_summary.get("delegated_task_class"),
            "safety_boundaries": list(safety_boundaries),
            "artifact_lineage_summary": artifact.lineage_summary,
            "upstream_lineage": flow.lineage_summary,
        },
        created_at=created_at,
    )
    return registry.store_surface(record)


def get_demo_result_delivery_surface(
    *,
    registry: DemoResultDeliverySurfaceRegistry,
    demo_result_surface_id: str,
) -> DemoResultDeliverySurfaceRecord | None:
    return registry.get_surface(demo_result_surface_id)


def list_demo_result_delivery_surfaces(
    *,
    registry: DemoResultDeliverySurfaceRegistry,
    owner_id: str | None = None,
    robot_id: str | None = None,
) -> tuple[DemoResultDeliverySurfaceRecord, ...]:
    return registry.list_surfaces(owner_id=owner_id, robot_id=robot_id)


def render_demo_result_delivery_surface_text(
    *,
    result_title: str,
    what_hermes_noticed: str,
    prepared_brief_summary: str,
    meeting_context: str,
    preparation_checklist: tuple[str, ...],
    open_questions: tuple[str, ...],
    suggested_materials: tuple[str, ...],
    skill_pack_summary: str,
    daily_brief_summary: str,
    safety_boundaries: tuple[str, ...],
    lineage_summary: str,
    no_action_taken_notice: str,
) -> str:
    sections = [
        "Result Title",
        result_title,
        "",
        "What Hermes Noticed",
        what_hermes_noticed,
        "",
        "Prepared Brief",
        prepared_brief_summary,
        "",
        "Meeting Context",
        meeting_context,
        "",
        "Preparation Checklist",
    ]
    sections.extend(f"- {item}" for item in preparation_checklist)
    sections.extend(["", "Open Questions"])
    sections.extend(f"- {item}" for item in open_questions)
    sections.extend(["", "Suggested Materials"])
    sections.extend(f"- {item}" for item in suggested_materials)
    sections.extend(
        [
            "",
            "Skill Pack Summary",
            skill_pack_summary,
            "",
            "Daily Brief Summary",
            daily_brief_summary,
            "",
            "Safety Boundaries",
        ]
    )
    sections.extend(f"- {item}" for item in safety_boundaries)
    sections.extend(
        [
            "",
            "Lineage Summary",
            lineage_summary,
            "",
            "No Action Taken Notice",
            no_action_taken_notice,
        ]
    )
    return "\n".join(sections)


def _require_flow_record(record: object) -> FirstDemoMeetingBriefFlowRecord:
    if not isinstance(record, FirstDemoMeetingBriefFlowRecord):
        raise ValueError("rejected_unknown_demo_flow_record")
    return record


def _require_artifact_record(record: object) -> FirstDemoMeetingBriefArtifactRecord:
    if not isinstance(record, FirstDemoMeetingBriefArtifactRecord):
        raise ValueError("rejected_unknown_demo_artifact_record")
    return record


def _validate_identity(*, record: object, owner_id: str, robot_id: str) -> None:
    if getattr(record, "owner_id", None) != owner_id:
        raise ValueError("rejected_cross_owner_record")
    if getattr(record, "robot_id", None) != robot_id:
        raise ValueError("rejected_cross_robot_record")


def _validate_flow_artifact_lineage(
    *,
    flow: FirstDemoMeetingBriefFlowRecord,
    artifact: FirstDemoMeetingBriefArtifactRecord,
) -> None:
    if flow.demo_stage != FIRST_DEMO_MEETING_BRIEF_STAGE:
        raise ValueError("rejected_missing_126p_demo_flow_lineage")
    if flow.demo_mode != FIRST_DEMO_MEETING_BRIEF_MODE:
        raise ValueError("rejected_missing_126p_demo_flow_lineage")
    if flow.demo_artifact_id != artifact.demo_artifact_id:
        raise ValueError("rejected_mismatched_flow_artifact_lineage")
    if artifact.demo_flow_id != flow.demo_flow_id:
        raise ValueError("rejected_mismatched_flow_artifact_lineage")
    if artifact.artifact_type != "local_meeting_brief_demo":
        raise ValueError("rejected_missing_126p_artifact_lineage")


def _reject_live_flags(record: object) -> None:
    blocked_truthy = (
        "live_connector_allowed",
        "live_connector_used",
        "live_send_allowed",
        "live_telegram_allowed",
        "live_telegram_used",
        "telegram_delivery_allowed",
        "callback_binding_allowed",
        "followup_intent_creation_allowed",
        "async_delegation_allowed",
        "execution_allowed",
        "memory_write_allowed",
        "memory_mutated",
        "memory_mutated_by_126p",
        "memory_mutated_by_127p",
        "model_call_allowed",
        "model_called",
        "tool_call_allowed",
        "tool_called",
        "external_write_allowed",
        "external_system_written",
        "external_written",
        "worker_dispatch_allowed",
        "worker_dispatched",
        "billing_allowed",
        "entitlement_enforcement_allowed",
    )
    for field_name in blocked_truthy:
        if bool(getattr(record, field_name, False)):
            if field_name in {"live_send_allowed", "live_telegram_allowed", "live_telegram_used", "telegram_delivery_allowed"}:
                raise ValueError("rejected_live_telegram_delivery")
            if field_name in {"model_call_allowed", "model_called", "tool_call_allowed", "tool_called"}:
                raise ValueError("rejected_model_tool_dependency")
            if field_name in {"external_write_allowed", "external_system_written", "external_written"}:
                raise ValueError("rejected_external_write_dependency")
            if field_name in {"worker_dispatch_allowed", "worker_dispatched"}:
                raise ValueError("rejected_worker_dispatch_dependency")
            if field_name in {"memory_write_allowed", "memory_mutated", "memory_mutated_by_126p", "memory_mutated_by_127p"}:
                raise ValueError("rejected_memory_write_dependency")
            if field_name in {"live_connector_allowed", "live_connector_used"}:
                raise ValueError("rejected_live_connector_usage")
            raise ValueError("rejected_live_dependency")
    for field_name in ("title", "local_render_text", "demo_summary", "meeting_context_summary", "lineage_summary", "display_text"):
        value = getattr(record, field_name, None)
        if isinstance(value, str):
            _reject_sensitive_text(value)


def _reject_sensitive_text(text: str) -> None:
    lowered = text.lower()
    if any(keyword in lowered for keyword in CREDENTIAL_KEYWORDS):
        raise ValueError("rejected_raw_credentials")
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        raise ValueError("rejected_sensitive_raw_payload")


def _what_hermes_noticed(*, artifact: FirstDemoMeetingBriefArtifactRecord) -> str:
    return artifact.meeting_context_summary


def _prepared_brief_summary(*, artifact: FirstDemoMeetingBriefArtifactRecord) -> str:
    return artifact.demo_summary


def _surface_safety_boundaries(*, artifact: FirstDemoMeetingBriefArtifactRecord) -> tuple[str, ...]:
    merged = list(artifact.safety_boundaries)
    for notice in REQUIRED_SAFETY_NOTICES:
        if notice not in merged:
            merged.append(notice)
    return tuple(merged)


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))


def _render_lineage_summary_text(lineage_summary: dict[str, object]) -> str:
    return json.dumps(lineage_summary, sort_keys=True, separators=(",", ":"))
