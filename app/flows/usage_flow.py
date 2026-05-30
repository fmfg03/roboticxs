from __future__ import annotations

from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.reply_composer import compose_spend_summary_reply, compose_token_usage_summary_reply, compose_usage_empty_reply
from app.safety import evaluate_safety
from app.usage_reporting import build_usage_summary


def process_usage_spend(*, context) -> dict:
    return _process_usage_report(context=context, report_kind="spend")


def process_usage_tokens(*, context) -> dict:
    return _process_usage_report(context=context, report_kind="tokens")


def _process_usage_report(*, context, report_kind: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare usage report", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    summary = build_usage_summary(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    reply_text = _compose_usage_reply(report_kind=report_kind, summary=summary)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="USAGE_REPORT",
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


def _compose_usage_reply(*, report_kind: str, summary) -> str:
    if summary.is_empty:
        return compose_usage_empty_reply("spend" if report_kind == "spend" else "tokens")
    if report_kind == "spend":
        return compose_spend_summary_reply(summary)
    return compose_token_usage_summary_reply(summary)
