from __future__ import annotations

from app.flow_runtime import build_budgeted_route_estimate, build_flow_response, create_task_and_run, persist_safety_decision
from app.flow_runtime import persist_route_and_token_from_estimate
from app.memory_control import list_active_memories, summarize_active_memory_context
from app.model_router import classify_task
from app.reply_composer import compose_budget_block_reply, compose_budget_warn_prefix, compose_reply_text_with_memory
from app.safety import evaluate_safety
from app.scope_guard import decide_scope
from app.skills import get_active_skill_manifest


def process_general_task(*, context) -> dict:
    active_memories = list_active_memories(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    manifest = get_active_skill_manifest(context.session)
    scope_decision = decide_scope(context.envelope.text, manifest)
    task_class = classify_task(context.envelope.text, scope_decision, "GENERAL_TASK")

    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision=scope_decision,
        task_class=task_class,
    )
    route_estimate, budget_posture = build_budgeted_route_estimate(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="GENERAL_TASK",
        task_class=task_class,
    )
    if budget_posture.status == "BLOCK":
        safety_result = {
            "action_class": "BUDGET_GUARDRAIL",
            "decision": "BLOCK",
            "reason_code": "LOCAL_BUDGET_THRESHOLD_REACHED",
            "user_message": compose_budget_block_reply(posture=budget_posture),
        }
        safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
        route_record, token_event = persist_route_and_token_from_estimate(
            context=context,
            task_id=task.id,
            route_estimate=route_estimate,
        )
        return build_flow_response(
            context=context,
            task_id=task.id,
            reply_text=safety_result["user_message"],
            scope_decision="BLOCK",
            safety_decision=safety_decision,
            route_record=route_record,
            token_event=token_event,
        )

    safety_result = evaluate_safety(context.envelope.text, scope_decision)
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    route_record, token_event = persist_route_and_token_from_estimate(
        context=context,
        task_id=task.id,
        route_estimate=route_estimate,
    )

    reply_text = compose_reply_text_with_memory(
        scope_decision,
        safety_result,
        summarize_active_memory_context(active_memories),
    )
    if budget_posture.status == "WARN":
        reply_text = compose_budget_warn_prefix(posture=budget_posture) + reply_text
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision=scope_decision,
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )
