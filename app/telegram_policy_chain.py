from __future__ import annotations

from dataclasses import dataclass, field
import re
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.cost_governor import (
    CostPreflightResult,
    build_task_cost_request,
    default_budget_policy,
    evaluate_cost_preflight,
    serialize_cost_preflight_result,
)
from app.memory_control import list_active_memories
from app.memory_center_projection import (
    MemoryCenterItem,
    MemoryProjectionRequest,
    MemoryProjectionResult,
    project_memory,
)
from app.models import MemoryItem, Robot, User
from app.telegram_runtime import (
    TelegramRuntimeError,
    build_hermes_request_from_telegram,
    parse_telegram_text_update,
)


POLICY_CHAIN_STAGE = "95P"
POLICY_CHAIN_WEBHOOK_PATH = "/api/telegram/policy-chain/webhook"

EXPOSED_COMMANDS = {
    "help",
    "status",
    "usage",
    "routines list",
    "skills list",
    "memory review",
    "stop",
}
WRAPPED_COMMANDS = {
    "/cron": "Roboticxs Routines",
    "/skills": "Skill Packages",
    "/bundles": "Skill Packages",
    "/model": "Economy / Balanced / Premium",
    "/handoff": "Approved channel delivery",
    "/personality": "Approved modes",
    "/sessions": "Conversation history",
    "/resume": "Continue conversation",
}
OPERATOR_ONLY_COMMANDS = {
    "/config",
    "/reload",
    "/reload-mcp",
    "/plugins",
    "/toolsets",
    "/debug",
    "/profile",
    "/platforms",
    "/gateway",
    "/codex-runtime",
    "/branch",
    "/rollback",
}
BLOCKED_RAW_COMMANDS = {
    "/yolo",
}

APPROVE_PATTERN = re.compile(r"^/(?:approve|deny)\s+([a-zA-Z0-9_-]+)$")
BARE_APPROVAL_PATTERN = re.compile(r"^/(?:approve|deny)\s*$")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    policy: str
    decision: str
    reason: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryProjection:
    memory_id: str
    memory_type: str
    content: str
    source: str
    allowed_use: str


@dataclass(frozen=True, slots=True)
class MemoryContextBlock:
    packet_type: str
    status: str
    stage: str
    source_of_truth: str
    runtime_target: str
    projection_policy_id: str
    request_scope: str
    active_skill_id: str
    projections: tuple[MemoryProjection, ...]
    tool_action_authorization: bool
    permission_expansion_authorized: bool
    projection_result: MemoryProjectionResult | None = None


@dataclass(frozen=True, slots=True)
class LocalActionPacket:
    packet_id: str
    action_class: str
    decision: str
    requested_text: str
    final_user_visible_content: str
    confirmation_command: str
    external_effect_authorized: bool


@dataclass(frozen=True, slots=True)
class HermesGatewayAdapterStubResult:
    called: bool
    status: str
    response_text: str
    request_text: str | None
    memory_projection_count: int
    network_call: bool = False
    live_gateway_started: bool = False
    external_side_effect: bool = False


@dataclass(frozen=True, slots=True)
class TelegramPolicyChainResult:
    ok: bool
    stage: str
    chat_id: int | None
    user_id: int | None
    response_text: str
    command_policy: PolicyDecision
    skill_scope_policy: PolicyDecision
    tool_authority_policy: PolicyDecision
    memory_context: MemoryContextBlock
    cost_preflight: CostPreflightResult | None
    action_packet: LocalActionPacket | None
    hermes_adapter: HermesGatewayAdapterStubResult
    policy_trace: tuple[PolicyDecision, ...]
    local_response: dict[str, object]
    error_code: str | None = None


def run_telegram_policy_chain(
    *,
    update: dict,
    settings: Settings,
    session: Session,
    memory_actor_role: str = "owner_admin",
    memory_target_scope: str = "telegram",
    memory_allowed_use: str = "telegram_context",
) -> TelegramPolicyChainResult:
    del settings  # 95P must not use credentials or production configuration.
    try:
        message = parse_telegram_text_update(update)
    except TelegramRuntimeError:
        empty_context = _empty_memory_context()
        blocked = PolicyDecision(
            policy="telegram_input",
            decision="BLOCK",
            reason="Malformed or unsupported Telegram input.",
        )
        adapter = _blocked_adapter_result("Input blocked before Hermes adapter.")
        return TelegramPolicyChainResult(
            ok=False,
            stage=POLICY_CHAIN_STAGE,
            chat_id=None,
            user_id=None,
            response_text="No pude procesar ese mensaje por ahora.",
            command_policy=blocked,
            skill_scope_policy=_skipped_policy("skill_scope_policy"),
            tool_authority_policy=_skipped_policy("tool_authority_policy"),
            memory_context=empty_context,
            cost_preflight=None,
            action_packet=None,
            hermes_adapter=adapter,
            policy_trace=(blocked,),
            local_response=_local_response(adapter=adapter, action_packet=None),
            error_code="telegram_input_blocked",
        )

    user, robot = _resolve_user_and_robot(session=session, message=message)
    command_policy = evaluate_command_policy(message.text)
    if command_policy.decision == "BLOCK_CONSUMER":
        memory_context = project_memory_context(
            session=session,
            user=user,
            robot=robot,
            request_scope="blocked",
            actor_role=memory_actor_role,
            target_scope=memory_target_scope,
            allowed_use=memory_allowed_use,
        )
        adapter = _blocked_adapter_result("Command policy blocked the request before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=_skipped_policy("skill_scope_policy"),
            tool_authority_policy=_skipped_policy("tool_authority_policy"),
            memory_context=memory_context,
            cost_preflight=None,
            action_packet=None,
            adapter=adapter,
            response_text="This raw Hermes command is not available in the Roboticxs Telegram surface.",
            ok=False,
            error_code="command_policy_blocked",
        )

    skill_scope_policy = evaluate_skill_scope_policy(message.text, command_policy=command_policy)
    if skill_scope_policy.decision == "BLOCK":
        memory_context = project_memory_context(
            session=session,
            user=user,
            robot=robot,
            request_scope="blocked",
            actor_role=memory_actor_role,
            target_scope=memory_target_scope,
            allowed_use=memory_allowed_use,
        )
        adapter = _blocked_adapter_result("Skill scope policy blocked the request before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=skill_scope_policy,
            tool_authority_policy=_skipped_policy("tool_authority_policy"),
            memory_context=memory_context,
            cost_preflight=None,
            action_packet=None,
            adapter=adapter,
            response_text="I cannot do that in Roboticxs v0. I can help prepare a safe local draft or checklist.",
            ok=False,
            error_code="skill_scope_blocked",
        )

    tool_authority_policy = evaluate_tool_authority_policy(message.text)
    memory_context = project_memory_context(
        session=session,
        user=user,
        robot=robot,
        request_scope=skill_scope_policy.decision.lower(),
        actor_role=memory_actor_role,
        target_scope=memory_target_scope,
        allowed_use=memory_allowed_use,
    )

    if tool_authority_policy.decision == "BLOCK":
        adapter = _blocked_adapter_result("Tool Authority Guard blocked the request before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=skill_scope_policy,
            tool_authority_policy=tool_authority_policy,
            memory_context=memory_context,
            cost_preflight=None,
            action_packet=None,
            adapter=adapter,
            response_text="That action is blocked in Roboticxs v0. Nothing was executed.",
            ok=False,
            error_code="tool_authority_blocked",
        )

    if tool_authority_policy.decision == "ASK_CONFIRMATION":
        action_packet = build_local_action_packet(
            message_text=message.text,
            action_class=str(tool_authority_policy.metadata["action_class"]),
        )
        adapter = _blocked_adapter_result("Approval-required action stopped before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=skill_scope_policy,
            tool_authority_policy=tool_authority_policy,
            memory_context=memory_context,
            cost_preflight=None,
            action_packet=action_packet,
            adapter=adapter,
            response_text=(
                "Approval required before any external effect. "
                f"Review Action Packet {action_packet.packet_id}."
            ),
            ok=False,
            error_code="action_packet_required",
        )

    cost_preflight = evaluate_cost_preflight(
        request=build_task_cost_request(
            request_id=f"100p:{user.id}:{robot.id}:{message.chat_id}:{message.user_id}",
            owner_id=str(user.id),
            robot_id=str(robot.id),
            text=message.text,
            memory_context_used=bool(memory_context.projections),
            context_item_count=len(memory_context.projections),
            active_skill_id=str(skill_scope_policy.metadata.get("active_skill_id", "basic_assistant")),
            routine_requested=memory_actor_role == "routine",
        ),
        budget_policy=default_budget_policy(owner_id=str(user.id), robot_id=str(robot.id)),
    )
    if cost_preflight.blocked:
        adapter = _blocked_adapter_result("100P cost preflight blocked the request before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=skill_scope_policy,
            tool_authority_policy=tool_authority_policy,
            memory_context=memory_context,
            cost_preflight=cost_preflight,
            action_packet=None,
            adapter=adapter,
            response_text="This request was blocked by the local cost governor before execution.",
            ok=False,
            error_code="cost_preflight_blocked",
        )
    if cost_preflight.confirmation_required:
        adapter = _blocked_adapter_result("100P cost preflight requires confirmation before Hermes adapter.")
        return _result(
            message=message,
            command_policy=command_policy,
            skill_scope_policy=skill_scope_policy,
            tool_authority_policy=tool_authority_policy,
            memory_context=memory_context,
            cost_preflight=cost_preflight,
            action_packet=None,
            adapter=adapter,
            response_text="This request needs explicit approval because the local cost governor flagged it as expensive.",
            ok=False,
            error_code="cost_confirmation_required",
        )

    hermes_request = build_hermes_request_from_telegram(message)
    adapter = dispatch_hermes_gateway_adapter_stub(
        request_text=hermes_request.text,
        memory_context=memory_context,
    )
    return _result(
        message=message,
        command_policy=command_policy,
        skill_scope_policy=skill_scope_policy,
        tool_authority_policy=tool_authority_policy,
        memory_context=memory_context,
        cost_preflight=cost_preflight,
        action_packet=None,
        adapter=adapter,
        response_text=adapter.response_text,
        ok=True,
    )


def evaluate_command_policy(text: str) -> PolicyDecision:
    normalized = text.strip().lower()
    first_token = normalized.split(maxsplit=1)[0] if normalized else ""

    if BARE_APPROVAL_PATTERN.match(normalized):
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="BLOCK_CONSUMER",
            reason="Approval or denial must reference one Action Packet.",
            metadata={"policy_class": "BLOCK_CONSUMER"},
        )
    approval_match = APPROVE_PATTERN.match(normalized)
    if approval_match is not None:
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="EXPOSE",
            reason="Approval command references a specific packet.",
            metadata={"policy_class": "EXPOSE", "action_packet_id": approval_match.group(1)},
        )
    if normalized in EXPOSED_COMMANDS:
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="EXPOSE",
            reason="Consumer-safe Roboticxs command.",
            metadata={"policy_class": "EXPOSE"},
        )
    if first_token in WRAPPED_COMMANDS:
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="WRAP",
            reason="Raw Hermes command is wrapped in Roboticxs product language.",
            metadata={"policy_class": "WRAP", "product_surface": WRAPPED_COMMANDS[first_token]},
        )
    if first_token in OPERATOR_ONLY_COMMANDS or first_token in BLOCKED_RAW_COMMANDS:
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="BLOCK_CONSUMER",
            reason="Raw Hermes operator or bypass command is not consumer-visible.",
            metadata={"policy_class": "BLOCK_CONSUMER", "raw_command": first_token},
        )
    if first_token.startswith("/"):
        return PolicyDecision(
            policy="command_surface_policy_90p",
            decision="BLOCK_CONSUMER",
            reason="Unknown raw Hermes command defaults to blocked consumer exposure.",
            metadata={"policy_class": "UNKNOWN_UNVERIFIED", "raw_command": first_token},
        )
    return PolicyDecision(
        policy="command_surface_policy_90p",
        decision="PRODUCT_INTENT",
        reason="Telegram text is treated as Roboticxs product intent.",
        metadata={"policy_class": "EXPOSE"},
    )


def evaluate_skill_scope_policy(text: str, *, command_policy: PolicyDecision) -> PolicyDecision:
    normalized = text.strip().lower()
    if "action_packet_id" in command_policy.metadata:
        return PolicyDecision(
            policy="skill_scope_policy_91p",
            decision="ANSWER",
            reason="Specific Action Packet reference may be handled locally without external execution.",
            metadata={"active_skill_id": "basic_assistant"},
        )
    if _contains_any(
        normalized,
        (
            "pay",
            "refund",
            "delete account",
            "change password",
            "change medication",
            "change medicine",
            "alter medication",
            "alter medicine",
            "which pill",
            "which medication",
            "which medicine",
            "medical decision",
            "diagnose",
            "diagnosis",
            "treatment advice",
            "missed dose",
            "double dose",
            "dose",
            "dosage",
            "credential",
            "accept legal",
            "deploy production",
            "yolo",
        ),
    ):
        return PolicyDecision(
            policy="skill_scope_policy_91p",
            decision="BLOCK",
            reason="Request asks for prohibited or sensitive action.",
            metadata={"active_skill_id": "basic_assistant"},
        )
    if command_policy.decision == "WRAP":
        return PolicyDecision(
            policy="skill_scope_policy_91p",
            decision="ANSWER",
            reason="Wrapped command remains inside Roboticxs product language.",
            metadata={"active_skill_id": "basic_assistant"},
        )
    if len(normalized.split()) <= 1 and normalized not in EXPOSED_COMMANDS:
        return PolicyDecision(
            policy="skill_scope_policy_91p",
            decision="CLARIFY",
            reason="Request is in scope but needs more detail.",
            metadata={"active_skill_id": "basic_assistant"},
        )
    return PolicyDecision(
        policy="skill_scope_policy_91p",
        decision="ANSWER",
        reason="Basic Assistant may answer safe local productivity requests.",
        metadata={"active_skill_id": "basic_assistant"},
    )


def evaluate_tool_authority_policy(text: str) -> PolicyDecision:
    normalized = text.strip().lower()
    if APPROVE_PATTERN.match(normalized):
        return PolicyDecision(
            policy="tool_authority_policy_92p",
            decision="DRAFT_ONLY",
            reason="95P binds the approval reference but executes no external effect.",
            metadata={"action_class": "ROUTE"},
        )
    if _contains_any(
        normalized,
        (
            "pay",
            "refund",
            "delete account",
            "delete all",
            "change password",
            "change medication",
            "change medicine",
            "alter medication",
            "alter medicine",
            "which pill",
            "which medication",
            "which medicine",
            "medical decision",
            "diagnose",
            "diagnosis",
            "treatment advice",
            "missed dose",
            "double dose",
            "dose",
            "dosage",
            "credential",
            "grant admin",
            "accept legal",
            "deploy production",
            "destructive",
        ),
    ):
        return PolicyDecision(
            policy="tool_authority_policy_92p",
            decision="BLOCK",
            reason="Prohibited action class defaults to BLOCK in v0.",
            metadata={"action_class": "BLOCKED_SENSITIVE_ACTION"},
        )
    if _contains_any(
        normalized,
        (
            "send email",
            "send message",
            "enviar correo",
            "enviar mensaje",
            "publish",
            "write external",
            "update crm",
            "book appointment",
            "schedule with",
            "external send",
        ),
    ):
        return PolicyDecision(
            policy="tool_authority_policy_92p",
            decision="ASK_CONFIRMATION",
            reason="External or user-visible action requires an Action Packet.",
            metadata={"action_class": "SEND_EXTERNAL_MESSAGE"},
        )
    if _contains_any(normalized, ("remind", "schedule myself", "local reminder", "recordatorio")):
        return PolicyDecision(
            policy="tool_authority_policy_92p",
            decision="DRAFT_ONLY",
            reason="Reminder or self-schedule remains local draft-only in 95P.",
            metadata={"action_class": "REMIND"},
        )
    return PolicyDecision(
        policy="tool_authority_policy_92p",
        decision="ALLOW",
        reason="Safe local read, draft, summarize, classify, or route action.",
        metadata={"action_class": "DRAFT"},
    )


def project_memory_context(
    *,
    session: Session,
    user: User,
    robot: Robot,
    request_scope: str,
    actor_role: str = "owner_admin",
    target_scope: str = "telegram",
    allowed_use: str = "telegram_context",
) -> MemoryContextBlock:
    memories = list_active_memories(session=session, user_id=user.id, robot_id=robot.id)
    projection_result = project_memory(
        request=MemoryProjectionRequest(
            request_id=f"95p:{user.id}:{robot.id}:{request_scope}:{target_scope}",
            actor_id=user.id,
            actor_role=actor_role,
            owner_id=user.id,
            robot_id=robot.id,
            target_scope=target_scope,
            allowed_use=allowed_use,
            max_items=3,
            max_summary_chars=160,
        ),
        items=tuple(_memory_center_item(memory) for memory in memories),
    )
    projections = tuple(
        MemoryProjection(
            memory_id=summary.item_id,
            memory_type=summary.memory_kind,
            content=summary.summary,
            source=summary.source,
            allowed_use=summary.allowed_use,
        )
        for summary in projection_result.summaries
    )
    return MemoryContextBlock(
        packet_type="MemoryContextBlock",
        status="NON_AUTHORITY_RUNTIME_CONTEXT",
        stage=POLICY_CHAIN_STAGE,
        source_of_truth="Roboticxs Memory Center",
        runtime_target="Hermes Gateway adapter stub",
        projection_policy_id="memory_center_projection_runtime_99p_v0",
        request_scope=request_scope,
        active_skill_id="basic_assistant",
        projections=projections,
        tool_action_authorization=False,
        permission_expansion_authorized=False,
        projection_result=projection_result,
    )


def build_local_action_packet(*, message_text: str, action_class: str) -> LocalActionPacket:
    packet_id = "ap_" + uuid5(NAMESPACE_URL, f"95p:{action_class}:{message_text}").hex[:12]
    return LocalActionPacket(
        packet_id=packet_id,
        action_class=action_class,
        decision="ASK_CONFIRMATION",
        requested_text=message_text,
        final_user_visible_content=message_text,
        confirmation_command=f"/approve {packet_id}",
        external_effect_authorized=False,
    )


def dispatch_hermes_gateway_adapter_stub(
    *,
    request_text: str,
    memory_context: MemoryContextBlock,
) -> HermesGatewayAdapterStubResult:
    return HermesGatewayAdapterStubResult(
        called=True,
        status="local_stub_ok",
        response_text="Roboticxs handled this through the local 95P Hermes Gateway adapter stub.",
        request_text=request_text,
        memory_projection_count=len(memory_context.projections),
    )


def serialize_policy_chain_result(result: TelegramPolicyChainResult) -> dict[str, object]:
    return {
        "ok": result.ok,
        "stage": result.stage,
        "chat_id": result.chat_id,
        "user_id": result.user_id,
        "response_text": result.response_text,
        "error_code": result.error_code,
        "command_policy": _policy_to_dict(result.command_policy),
        "skill_scope_policy": _policy_to_dict(result.skill_scope_policy),
        "tool_authority_policy": _policy_to_dict(result.tool_authority_policy),
        "memory_context": {
            "packet_type": result.memory_context.packet_type,
            "status": result.memory_context.status,
            "stage": result.memory_context.stage,
            "source_of_truth": result.memory_context.source_of_truth,
            "runtime_target": result.memory_context.runtime_target,
            "projection_policy_id": result.memory_context.projection_policy_id,
            "request_scope": result.memory_context.request_scope,
            "active_skill_id": result.memory_context.active_skill_id,
            "tool_action_authorization": result.memory_context.tool_action_authorization,
            "permission_expansion_authorized": result.memory_context.permission_expansion_authorized,
            "projection_trace": []
            if result.memory_context.projection_result is None
            else [
                {
                    "item_id": trace.item_id,
                    "decision": trace.decision,
                    "reason_code": trace.reason_code,
                    "decisional": trace.decisional,
                }
                for trace in result.memory_context.projection_result.trace
            ],
            "projections": [
                {
                    "memory_id": projection.memory_id,
                    "memory_type": projection.memory_type,
                    "content": projection.content,
                    "source": projection.source,
                    "allowed_use": projection.allowed_use,
                }
                for projection in result.memory_context.projections
            ],
        },
        "action_packet": None
        if result.action_packet is None
        else {
            "packet_id": result.action_packet.packet_id,
            "action_class": result.action_packet.action_class,
            "decision": result.action_packet.decision,
            "requested_text": result.action_packet.requested_text,
            "final_user_visible_content": result.action_packet.final_user_visible_content,
            "confirmation_command": result.action_packet.confirmation_command,
            "external_effect_authorized": result.action_packet.external_effect_authorized,
        },
        "cost_preflight": serialize_cost_preflight_result(result.cost_preflight),
        "hermes_adapter": {
            "called": result.hermes_adapter.called,
            "status": result.hermes_adapter.status,
            "response_text": result.hermes_adapter.response_text,
            "request_text": result.hermes_adapter.request_text,
            "memory_projection_count": result.hermes_adapter.memory_projection_count,
            "network_call": result.hermes_adapter.network_call,
            "live_gateway_started": result.hermes_adapter.live_gateway_started,
            "external_side_effect": result.hermes_adapter.external_side_effect,
        },
        "policy_trace": [_policy_to_dict(policy) for policy in result.policy_trace],
        "local_response": result.local_response,
    }


def _result(
    *,
    message,
    command_policy: PolicyDecision,
    skill_scope_policy: PolicyDecision,
    tool_authority_policy: PolicyDecision,
    memory_context: MemoryContextBlock,
    cost_preflight: CostPreflightResult | None,
    action_packet: LocalActionPacket | None,
    adapter: HermesGatewayAdapterStubResult,
    response_text: str,
    ok: bool,
    error_code: str | None = None,
) -> TelegramPolicyChainResult:
    trace = tuple(
        policy
        for policy in (command_policy, skill_scope_policy, tool_authority_policy)
        if policy.decision != "SKIPPED"
    )
    return TelegramPolicyChainResult(
        ok=ok,
        stage=POLICY_CHAIN_STAGE,
        chat_id=message.chat_id,
        user_id=message.user_id,
        response_text=response_text,
        command_policy=command_policy,
        skill_scope_policy=skill_scope_policy,
        tool_authority_policy=tool_authority_policy,
        memory_context=memory_context,
        cost_preflight=cost_preflight,
        action_packet=action_packet,
        hermes_adapter=adapter,
        policy_trace=trace,
        local_response=_local_response(adapter=adapter, action_packet=action_packet),
        error_code=error_code,
    )


def _resolve_user_and_robot(*, session: Session, message) -> tuple[User, Robot]:
    user = session.scalar(select(User).where(User.telegram_user_id == message.user_id))
    if user is None:
        user = User(
            telegram_user_id=message.user_id,
            first_name=message.first_name or "Telegram",
            username=message.username,
        )
        session.add(user)
        session.flush()

    robot = session.scalar(select(Robot).where(Robot.user_id == user.id, Robot.active.is_(True)))
    if robot is None:
        robot = Robot(user_id=user.id, name=f"{user.first_name}'s Robot")
        session.add(robot)
        session.flush()
    return user, robot


def _memory_center_item(memory: MemoryItem) -> MemoryCenterItem:
    sensitive_types = {"CREDENTIAL", "SECRET", "MEDICAL_DECISION", "OWNER_PRIVATE", "UNRELATED_OWNER_MEMORY"}
    status = "active" if memory.status == "ACTIVE" else "revoked"
    sensitivity = "credential_like" if memory.memory_type in {"CREDENTIAL", "SECRET"} else (
        "medical" if memory.memory_type == "MEDICAL_DECISION" else (
            "personal" if memory.memory_type in {"OWNER_PRIVATE", "UNRELATED_OWNER_MEMORY"} else "ordinary"
        )
    )
    scopes, allowed_uses = _legacy_projection_policy(memory.memory_type)
    return MemoryCenterItem(
        item_id=memory.id,
        owner_id=memory.user_id,
        robot_id=memory.robot_id,
        memory_kind=memory.memory_type,
        status=status,
        scopes=scopes,
        sensitivity=sensitivity,
        allowed_uses=allowed_uses,
        skill_ids=(),
        content=memory.content,
        bounded_summary=None,
        source=memory.source,
        is_boundary=memory.memory_type == "BOUNDARY_MEMORY",
        is_preference="PREFERENCE" in memory.memory_type,
    )


def _legacy_projection_policy(memory_type: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    scopes = ["general", "telegram", "hermes_os"]
    allowed_uses = ["answer_personalization", "telegram_context", "hermes_os_context"]
    if memory_type == "BOUNDARY_MEMORY":
        scopes.extend(("caregiver", "routine"))
        allowed_uses.extend(("boundary_enforcement", "caregiver_context", "routine_context"))
    elif memory_type == "WORK_PREFERENCE":
        scopes.append("routine")
        allowed_uses.append("routine_context")
    return tuple(scopes), tuple(allowed_uses)


def _empty_memory_context() -> MemoryContextBlock:
    return MemoryContextBlock(
        packet_type="MemoryContextBlock",
        status="NON_AUTHORITY_RUNTIME_CONTEXT",
        stage=POLICY_CHAIN_STAGE,
        source_of_truth="Roboticxs Memory Center",
        runtime_target="Hermes Gateway adapter stub",
        projection_policy_id="memory_projection_policy_v0_1",
        request_scope="none",
        active_skill_id="basic_assistant",
        projections=(),
        tool_action_authorization=False,
        permission_expansion_authorized=False,
    )


def _blocked_adapter_result(reason: str) -> HermesGatewayAdapterStubResult:
    return HermesGatewayAdapterStubResult(
        called=False,
        status="not_called",
        response_text=reason,
        request_text=None,
        memory_projection_count=0,
    )


def _skipped_policy(policy: str) -> PolicyDecision:
    return PolicyDecision(policy=policy, decision="SKIPPED", reason="Prior policy stopped the chain.")


def _local_response(
    *,
    adapter: HermesGatewayAdapterStubResult,
    action_packet: LocalActionPacket | None,
) -> dict[str, object]:
    return {
        "network_call": False,
        "telegram_send": False,
        "live_hermes_gateway_started": False,
        "external_side_effect": False,
        "hermes_adapter_called": adapter.called,
        "action_packet_required": action_packet is not None,
    }


def _policy_to_dict(policy: PolicyDecision) -> dict[str, object]:
    return {
        "policy": policy.policy,
        "decision": policy.decision,
        "reason": policy.reason,
        "metadata": policy.metadata,
    }


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
