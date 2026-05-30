from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budget_policy import evaluate_budget_posture, get_budget_policy
from app.model_router import estimate_route
from app.models import ModelRouteDecision, Robot, SafetyDecision, Task, TaskRun, TokenUsageEvent, User
from app.token_usage import build_token_usage_event
from app.usage_reporting import build_usage_summary


@dataclass(slots=True)
class FlowContext:
    session: Session
    settings: object
    envelope: object
    user: User
    robot: Robot


def resolve_user_and_robot(*, session: Session, envelope) -> tuple[User, Robot]:
    user = session.scalar(select(User).where(User.telegram_user_id == envelope.telegram_user_id))
    if user is None:
        user = User(
            telegram_user_id=envelope.telegram_user_id,
            first_name=envelope.first_name,
            username=envelope.username,
        )
        session.add(user)
        session.flush()

    robot = session.scalar(select(Robot).where(Robot.user_id == user.id, Robot.active.is_(True)))
    if robot is None:
        robot = Robot(user_id=user.id, name=f"{user.first_name}'s Robot")
        session.add(robot)
        session.flush()

    return user, robot


def create_task_and_run(
    *,
    context: FlowContext,
    kind: str,
    scope_decision: str,
    task_class: str,
    input_text: str | None = None,
) -> Task:
    task = Task(
        user_id=context.user.id,
        robot_id=context.robot.id,
        kind=kind,
        input_text=input_text or context.envelope.text,
        scope_decision=scope_decision,
        task_class=task_class,
    )
    context.session.add(task)
    context.session.flush()
    context.session.add(TaskRun(task_id=task.id, status="completed"))
    return task


def persist_safety_decision(*, context: FlowContext, task_id: str, safety_result: dict[str, str]) -> SafetyDecision:
    safety_decision = SafetyDecision(task_id=task_id, **safety_result)
    context.session.add(safety_decision)
    context.session.flush()
    return safety_decision


def persist_route_and_token(*, context: FlowContext, text: str, task_id: str, task_family: str, task_class: str):
    route_estimate = estimate_route(
        text=text,
        task_id=task_id,
        task_family=task_family,
        task_class=task_class,
        settings=context.settings,
    )
    return persist_route_and_token_from_estimate(context=context, task_id=task_id, route_estimate=route_estimate)


def persist_route_and_token_from_estimate(*, context: FlowContext, task_id: str, route_estimate: dict[str, str | int | float]):
    route_record = ModelRouteDecision(**route_estimate)
    context.session.add(route_record)
    context.session.flush()

    token_event_payload = build_token_usage_event(
        user_id=context.user.id,
        robot_id=context.robot.id,
        task_id=task_id,
        provider=route_record.provider,
        model=route_record.model,
        input_tokens=route_record.estimated_input_tokens,
        output_tokens=route_record.estimated_output_tokens,
        estimated_cost_usd=route_record.estimated_cost_usd,
    )
    token_event = TokenUsageEvent(**token_event_payload)
    context.session.add(token_event)
    context.session.flush()
    return route_record, token_event


def build_budgeted_route_estimate(
    *,
    context: FlowContext,
    text: str,
    task_id: str,
    task_family: str,
    task_class: str,
):
    route_estimate = estimate_route(
        text=text,
        task_id=task_id,
        task_family=task_family,
        task_class=task_class,
        settings=context.settings,
    )
    summary = build_usage_summary(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    policy = get_budget_policy(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    budget_posture = evaluate_budget_posture(
        summary=summary,
        estimated_route_cost_usd=route_estimate["estimated_cost_usd"],
        policy=policy,
    )
    return route_estimate, budget_posture


def build_flow_response(
    *,
    context: FlowContext,
    task_id: str,
    reply_text: str,
    scope_decision: str,
    safety_decision: SafetyDecision,
    route_record: ModelRouteDecision,
    token_event: TokenUsageEvent,
) -> dict:
    return {
        "ok": True,
        "reply": {"chat_id": context.envelope.chat_id, "text": reply_text},
        "task_id": task_id,
        "scope_decision": scope_decision,
        "safety_decision": safety_decision.decision,
        "model_route_decision_id": route_record.id,
        "token_usage_event_id": token_event.id,
    }


def describe_file_metadata_input(document) -> str:
    file_name = document.file_name or "unnamed file"
    mime_type = document.mime_type or "unknown mime type"
    size = f"{document.file_size} bytes" if document.file_size is not None else "unknown size"
    return f"telegram_document_metadata: {file_name} ({mime_type}, {size})"
