from __future__ import annotations

from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.reply_composer import compose_web_preflight_reply, compose_web_preflight_unknown_reply
from app.safety import evaluate_safety
from app.web_preflight_policy import classify_web_preflight, WEB_STATUS_UNKNOWN


def process_web_preflight(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="WEB_PREFLIGHT_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare web workflow preflight", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    result = classify_web_preflight(context.envelope.text)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="WEB_PREFLIGHT_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = (
        compose_web_preflight_unknown_reply()
        if result.status == WEB_STATUS_UNKNOWN
        else compose_web_preflight_reply(result=result)
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
