from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.cost_governor import CostPreflightResult
from app.telegram_policy_chain import (
    LocalActionPacket,
    MemoryContextBlock,
    PolicyDecision,
    TelegramPolicyChainResult,
)


HERMES_OS_STAGE = "96P"
HERMES_OS_RUNTIME_ROLE = "persistent_runtime_substrate"
AUTHORITY_LAYER = "Roboticxs policy chain"

BLOCKED_TOOL_CLASSES = frozenset(
    {
        "PAY",
        "REFUND",
        "DELETE",
        "CHANGE_CREDENTIALS",
        "CHANGE_PERMISSIONS",
        "LEGAL_ACCEPT",
        "PRODUCTION_DEPLOY",
        "DESTRUCTIVE_ACTION",
        "CONNECTOR_EXECUTION",
        "LIVE_RETRIEVAL",
        "BROWSER_EXECUTION",
        "EMAIL_EXECUTION",
        "WHATSAPP_EXECUTION",
        "PUBLISH",
        "EXTERNAL_WRITE",
    }
)
CONFIRMATION_TOOL_CLASSES = frozenset(
    {
        "SEND_EXTERNAL_MESSAGE",
        "WRITE_EXTERNAL_RECORD",
        "SCHEDULE_WITH_THIRD_PARTY",
        "MODIFY_CRM",
        "PLACE_VISUAL_SIGNATURE",
    }
)


@dataclass(frozen=True, slots=True)
class PolicyTrace:
    packet_type: str
    stage: str
    complete: bool
    decisions: tuple[PolicyDecision, ...]
    entrypoint: str
    downstream_authority_required: tuple[str, ...]

    def __post_init__(self) -> None:
        required = {
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        }
        observed = {decision.policy for decision in self.decisions}
        if self.complete and not required.issubset(observed):
            raise ValueError("96P PolicyTrace must include 90P, 91P, and 92P decisions.")


@dataclass(frozen=True, slots=True)
class RobotConstitution:
    packet_type: str
    stage: str
    robot_id: str
    identity: str
    runtime_role: str
    authority_layer: str
    hermes_is_authority: bool
    blocked_capabilities: tuple[str, ...]
    required_policy_order: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.hermes_is_authority:
            raise ValueError("Hermes must not be represented as the authority layer.")


@dataclass(frozen=True, slots=True)
class GoalPacket:
    packet_type: str
    stage: str
    goal_id: str
    robot_id: str
    user_intent: str
    requested_tool_classes: tuple[str, ...]
    policy_trace: PolicyTrace
    blocked: bool
    blocked_reason: str | None

    def __post_init__(self) -> None:
        blocked = BLOCKED_TOOL_CLASSES.intersection(self.requested_tool_classes)
        if blocked and not self.blocked:
            raise ValueError(f"GoalPacket requesting blocked tools must be blocked: {sorted(blocked)}")


@dataclass(frozen=True, slots=True)
class RoutinePacket:
    packet_type: str
    stage: str
    routine_id: str
    goal_id: str
    wake_preflight_required: bool
    budget_preflight_required: bool
    live_cron_authorized: bool
    model_router_allowed_before_budget: bool
    delivery_authorized: bool

    def __post_init__(self) -> None:
        if not self.wake_preflight_required or not self.budget_preflight_required:
            raise ValueError("RoutinePacket requires wake and budget preflight placeholders in 96P.")
        if self.live_cron_authorized or self.model_router_allowed_before_budget or self.delivery_authorized:
            raise ValueError("96P RoutinePacket cannot authorize cron, model routing before budget, or delivery.")


@dataclass(frozen=True, slots=True)
class SkillActivationPacket:
    packet_type: str
    stage: str
    skill_id: str
    scope_decision: str
    manifest_authority: str
    activation_allowed: bool
    hermes_activation_grants_permission: bool

    def __post_init__(self) -> None:
        if self.hermes_activation_grants_permission:
            raise ValueError("Hermes skill activation cannot grant product permission.")
        if self.activation_allowed and self.scope_decision not in {"ANSWER", "CLARIFY"}:
            raise ValueError("Skill activation is allowed only for ANSWER or CLARIFY scope decisions in 96P.")


@dataclass(frozen=True, slots=True)
class MemoryProjectionPacket:
    packet_type: str
    stage: str
    source_of_truth: str
    runtime_target: str
    projection_count: int
    bounded: bool
    scoped: bool
    tool_action_authorization: bool
    permission_expansion_authorized: bool
    context: MemoryContextBlock

    def __post_init__(self) -> None:
        if self.source_of_truth != "Roboticxs Memory Center":
            raise ValueError("MemoryProjectionPacket must use Roboticxs Memory Center as source of truth.")
        if not self.bounded or not self.scoped:
            raise ValueError("MemoryProjectionPacket must be bounded and scoped.")
        if self.tool_action_authorization or self.permission_expansion_authorized:
            raise ValueError("MemoryProjectionPacket must not authorize tools or expand permissions.")


@dataclass(frozen=True, slots=True)
class ToolRequestPacket:
    packet_type: str
    stage: str
    request_id: str
    action_class: str
    decision: str
    requires_action_packet: bool
    blocked: bool
    reaches_hermes_adapter: bool
    external_side_effect_authorized: bool

    def __post_init__(self) -> None:
        if self.action_class in BLOCKED_TOOL_CLASSES and not self.blocked:
            raise ValueError("Blocked action classes must remain blocked in 96P.")
        if self.blocked and self.reaches_hermes_adapter:
            raise ValueError("Blocked tool requests must not reach the Hermes adapter.")
        if self.requires_action_packet and self.reaches_hermes_adapter:
            raise ValueError("Approval-required tool requests must stop before the Hermes adapter in 96P.")
        if self.external_side_effect_authorized:
            raise ValueError("96P cannot authorize external side effects.")


@dataclass(frozen=True, slots=True)
class ActionPacketBinding:
    packet_type: str
    stage: str
    action_packet: LocalActionPacket | None
    required: bool
    bound: bool
    external_effect_authorized: bool

    def __post_init__(self) -> None:
        if self.required and self.action_packet is None:
            raise ValueError("ActionPacketBinding requires an ActionPacket when required=True.")
        if self.external_effect_authorized:
            raise ValueError("ActionPacketBinding cannot authorize external effects in 96P.")


@dataclass(frozen=True, slots=True)
class TaskRunRecord:
    packet_type: str
    stage: str
    task_run_id: str
    goal_id: str
    policy_trace: PolicyTrace
    status: str
    hermes_adapter_called: bool
    cost_preflight_decision: str | None
    selected_model_id: str | None
    live_hermes_started: bool
    network_call: bool
    external_side_effect: bool

    def __post_init__(self) -> None:
        if self.live_hermes_started or self.network_call or self.external_side_effect:
            raise ValueError("TaskRunRecord cannot record live Hermes, network, or external effects in 96P.")


@dataclass(frozen=True, slots=True)
class HermesOSRuntimeContract:
    packet_type: str
    stage: str
    robot_constitution: RobotConstitution
    goal_packet: GoalPacket
    routine_packet: RoutinePacket
    skill_activation_packet: SkillActivationPacket
    memory_projection_packet: MemoryProjectionPacket
    tool_request_packet: ToolRequestPacket
    action_packet_binding: ActionPacketBinding
    cost_preflight_result: CostPreflightResult | None
    policy_trace: PolicyTrace
    task_run_record: TaskRunRecord
    live_hermes_start_authorized: bool
    live_cron_authorized: bool
    live_telegram_send_authorized: bool
    connector_activation_authorized: bool
    external_side_effect_authorized: bool

    def __post_init__(self) -> None:
        if any(
            (
                self.live_hermes_start_authorized,
                self.live_cron_authorized,
                self.live_telegram_send_authorized,
                self.connector_activation_authorized,
                self.external_side_effect_authorized,
            )
        ):
            raise ValueError("96P Hermes OS contract cannot authorize live runtime or external effects.")


def build_hermes_os_runtime_contract(
    *,
    policy_result: TelegramPolicyChainResult,
    robot_id: str = "local_robot",
    routine_requested: bool = False,
) -> HermesOSRuntimeContract:
    policy_trace = PolicyTrace(
        packet_type="PolicyTrace",
        stage=HERMES_OS_STAGE,
        complete=_trace_is_complete(policy_result),
        decisions=policy_result.policy_trace,
        entrypoint="/api/telegram/policy-chain/webhook",
        downstream_authority_required=(
            "command_policy",
            "skill_scope_policy",
            "tool_authority_policy",
            "memory_projection_policy",
            "budget_authority_where_applicable",
            "action_packet_confirmation",
            "blocked_action_policy",
        ),
    )
    action_class = str(policy_result.tool_authority_policy.metadata.get("action_class", "ROUTE"))
    requires_action_packet = policy_result.action_packet is not None
    blocked = policy_result.tool_authority_policy.decision == "BLOCK" or action_class in BLOCKED_TOOL_CLASSES
    reaches_adapter = bool(policy_result.hermes_adapter.called)
    goal_id = _stable_id("goal", policy_result.user_id, policy_result.response_text, action_class)

    robot_constitution = RobotConstitution(
        packet_type="RobotConstitution",
        stage=HERMES_OS_STAGE,
        robot_id=robot_id,
        identity="Roboticxs personal robot running on Hermes as substrate",
        runtime_role=HERMES_OS_RUNTIME_ROLE,
        authority_layer=AUTHORITY_LAYER,
        hermes_is_authority=False,
        blocked_capabilities=tuple(sorted(BLOCKED_TOOL_CLASSES)),
        required_policy_order=(
            "command_policy",
            "skill_scope_policy",
            "tool_authority_policy",
            "memory_projection_policy",
            "budget_authority_where_applicable",
            "action_packet_confirmation",
        ),
    )
    goal_packet = GoalPacket(
        packet_type="GoalPacket",
        stage=HERMES_OS_STAGE,
        goal_id=goal_id,
        robot_id=robot_id,
        user_intent=policy_result.response_text,
        requested_tool_classes=(action_class,),
        policy_trace=policy_trace,
        blocked=blocked,
        blocked_reason="blocked_by_policy_chain" if blocked else None,
    )
    routine_packet = RoutinePacket(
        packet_type="RoutinePacket",
        stage=HERMES_OS_STAGE,
        routine_id=_stable_id("routine", goal_id, routine_requested),
        goal_id=goal_id,
        wake_preflight_required=True,
        budget_preflight_required=True,
        live_cron_authorized=False,
        model_router_allowed_before_budget=False,
        delivery_authorized=False,
    )
    skill_activation_packet = SkillActivationPacket(
        packet_type="SkillActivationPacket",
        stage=HERMES_OS_STAGE,
        skill_id=str(policy_result.skill_scope_policy.metadata.get("active_skill_id", "basic_assistant")),
        scope_decision=policy_result.skill_scope_policy.decision,
        manifest_authority="Roboticxs SkillManifest",
        activation_allowed=policy_result.skill_scope_policy.decision in {"ANSWER", "CLARIFY"},
        hermes_activation_grants_permission=False,
    )
    memory_projection_packet = MemoryProjectionPacket(
        packet_type="MemoryProjectionPacket",
        stage=HERMES_OS_STAGE,
        source_of_truth=policy_result.memory_context.source_of_truth,
        runtime_target="Hermes OS context",
        projection_count=len(policy_result.memory_context.projections),
        bounded=True,
        scoped=True,
        tool_action_authorization=policy_result.memory_context.tool_action_authorization,
        permission_expansion_authorized=policy_result.memory_context.permission_expansion_authorized,
        context=policy_result.memory_context,
    )
    tool_request_packet = ToolRequestPacket(
        packet_type="ToolRequestPacket",
        stage=HERMES_OS_STAGE,
        request_id=_stable_id("tool", goal_id, action_class),
        action_class=action_class,
        decision=policy_result.tool_authority_policy.decision,
        requires_action_packet=requires_action_packet,
        blocked=blocked,
        reaches_hermes_adapter=reaches_adapter,
        external_side_effect_authorized=False,
    )
    action_packet_binding = ActionPacketBinding(
        packet_type="ActionPacket",
        stage=HERMES_OS_STAGE,
        action_packet=policy_result.action_packet,
        required=requires_action_packet,
        bound=requires_action_packet,
        external_effect_authorized=False,
    )
    task_run_record = TaskRunRecord(
        packet_type="TaskRunRecord",
        stage=HERMES_OS_STAGE,
        task_run_id=_stable_id("task_run", goal_id, reaches_adapter),
        goal_id=goal_id,
        policy_trace=policy_trace,
        status=_task_run_status(policy_result),
        hermes_adapter_called=reaches_adapter,
        cost_preflight_decision=None if policy_result.cost_preflight is None else policy_result.cost_preflight.decision,
        selected_model_id=None
        if policy_result.cost_preflight is None or policy_result.cost_preflight.route_decision is None
        else policy_result.cost_preflight.route_decision.selected_model_id,
        live_hermes_started=False,
        network_call=False,
        external_side_effect=False,
    )
    return HermesOSRuntimeContract(
        packet_type="HermesOSRuntimeContract",
        stage=HERMES_OS_STAGE,
        robot_constitution=robot_constitution,
        goal_packet=goal_packet,
        routine_packet=routine_packet,
        skill_activation_packet=skill_activation_packet,
        memory_projection_packet=memory_projection_packet,
        tool_request_packet=tool_request_packet,
        action_packet_binding=action_packet_binding,
        cost_preflight_result=policy_result.cost_preflight,
        policy_trace=policy_trace,
        task_run_record=task_run_record,
        live_hermes_start_authorized=False,
        live_cron_authorized=False,
        live_telegram_send_authorized=False,
        connector_activation_authorized=False,
        external_side_effect_authorized=False,
    )


def _trace_is_complete(policy_result: TelegramPolicyChainResult) -> bool:
    return policy_result.tool_authority_policy.decision != "SKIPPED"


def _task_run_status(policy_result: TelegramPolicyChainResult) -> str:
    if policy_result.tool_authority_policy.decision == "BLOCK":
        return "BLOCKED_BEFORE_HERMES"
    if policy_result.action_packet is not None:
        return "WAITING_FOR_ACTION_PACKET_CONFIRMATION"
    if policy_result.hermes_adapter.called:
        return "LOCAL_HERMES_OS_STUB_COMPLETED"
    return "STOPPED_BEFORE_HERMES"


def _stable_id(prefix: str, *parts: object) -> str:
    raw = ":".join(str(part) for part in parts)
    return f"{prefix}_{uuid5(NAMESPACE_URL, raw).hex[:12]}"
