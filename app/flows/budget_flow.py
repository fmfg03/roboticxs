from __future__ import annotations

from app.budget_policy import (
    evaluate_budget_posture,
    get_budget_policy,
    parse_budget_amount,
    parse_budget_threshold_percent,
    parse_set_budget_block_threshold_command,
    parse_set_budget_limit_command,
    parse_set_budget_warn_threshold_command,
    reset_budget_policy,
    upsert_budget_block_threshold_policy,
    upsert_budget_limit_policy,
    upsert_budget_warn_threshold_policy,
)
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.reply_composer import (
    compose_budget_block_threshold_invalid_reply,
    compose_budget_block_threshold_updated_reply,
    compose_budget_limit_invalid_reply,
    compose_budget_limit_updated_reply,
    compose_budget_policy_reset_reply,
    compose_budget_status_reply,
    compose_budget_warn_threshold_invalid_reply,
    compose_budget_warn_threshold_updated_reply,
)
from app.safety import evaluate_safety
from app.usage_reporting import build_usage_summary


def process_budget_status(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare budget status", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    summary = build_usage_summary(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    policy = get_budget_policy(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    posture = evaluate_budget_posture(summary=summary, estimated_route_cost_usd=0.0, policy=policy)
    reply_text = compose_budget_status_reply(posture=posture)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="BUDGET_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_budget_policy_reset(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("reset local budget policy", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    reset_budget_policy(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="BUDGET_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_budget_policy_reset_reply(),
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_budget_limit_update(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("update local budget limit", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    raw_amount = parse_set_budget_limit_command(context.envelope.text)
    amount = parse_budget_amount(raw_amount or "")
    if amount is None:
        reply_text = compose_budget_limit_invalid_reply()
        scope_decision = "CLARIFY"
    else:
        upsert_budget_limit_policy(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
            limit_amount=amount,
        )
        reply_text = compose_budget_limit_updated_reply(amount=float(amount))
        scope_decision = "ANSWER"
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="BUDGET_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision=scope_decision,
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_budget_warn_threshold_update(*, context) -> dict:
    return _process_budget_threshold_update(context=context, threshold_kind="warn")


def process_budget_block_threshold_update(*, context) -> dict:
    return _process_budget_threshold_update(context=context, threshold_kind="block")


def _process_budget_threshold_update(*, context, threshold_kind: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("update local budget threshold", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    if threshold_kind == "warn":
        raw_threshold = parse_set_budget_warn_threshold_command(context.envelope.text)
        threshold_percent = parse_budget_threshold_percent(raw_threshold or "")
        if threshold_percent is None:
            reply_text = compose_budget_warn_threshold_invalid_reply()
            scope_decision = "CLARIFY"
        else:
            policy = upsert_budget_warn_threshold_policy(
                session=context.session,
                user_id=context.user.id,
                robot_id=context.robot.id,
                warn_threshold_percent=threshold_percent,
            )
            if policy is None:
                reply_text = compose_budget_warn_threshold_invalid_reply()
                scope_decision = "CLARIFY"
            else:
                reply_text = compose_budget_warn_threshold_updated_reply(threshold_percent=threshold_percent)
                scope_decision = "ANSWER"
    else:
        raw_threshold = parse_set_budget_block_threshold_command(context.envelope.text)
        threshold_percent = parse_budget_threshold_percent(raw_threshold or "")
        if threshold_percent is None:
            reply_text = compose_budget_block_threshold_invalid_reply()
            scope_decision = "CLARIFY"
        else:
            policy = upsert_budget_block_threshold_policy(
                session=context.session,
                user_id=context.user.id,
                robot_id=context.robot.id,
                block_threshold_percent=threshold_percent,
            )
            if policy is None:
                reply_text = compose_budget_block_threshold_invalid_reply()
                scope_decision = "CLARIFY"
            else:
                reply_text = compose_budget_block_threshold_updated_reply(threshold_percent=threshold_percent)
                scope_decision = "ANSWER"
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="BUDGET_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision=scope_decision,
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )
