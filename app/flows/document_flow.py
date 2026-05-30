from __future__ import annotations

from app.flow_runtime import build_budgeted_route_estimate
from app.document_control import forget_active_document_task, list_active_document_tasks
from app.document_review import (
    build_document_hash,
    build_document_preview,
    build_document_refusal_reply,
    build_document_review_reply,
    is_prohibited_document_authority_request,
)
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_route_and_token_from_estimate, persist_safety_decision
from app.models import DocumentTask
from app.reply_composer import (
    compose_budget_block_reply,
    compose_budget_warn_prefix,
    compose_document_forgotten_reply,
    compose_document_list_reply,
    compose_document_not_found_reply,
)
from app.safety import evaluate_safety


def process_document_review(*, context, review_type: str, source_text: str) -> dict:
    prohibited = is_prohibited_document_authority_request(source_text)
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SENSITIVE_REVIEW" if prohibited else "EXTRACTION",
    )
    route_estimate, budget_posture = build_budgeted_route_estimate(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="DOCUMENT_REVIEW",
        task_class="SENSITIVE_REVIEW" if prohibited else "EXTRACTION",
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

    if prohibited:
        safety_result = {
            "action_class": "PROFESSIONAL_DECISION",
            "decision": "ESCALATE",
            "reason_code": "DOCUMENT_AUTHORITY_REQUEST_BLOCKED",
            "user_message": build_document_refusal_reply(),
        }
    else:
        safety_result = evaluate_safety("draft document review", "ANSWER")

    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    document_task = DocumentTask(
        user_id=context.user.id,
        robot_id=context.robot.id,
        task_id=task.id,
        review_type=review_type,
        source_kind="TEXT_SIMULATED",
        source_text_preview=build_document_preview(source_text),
        source_text_hash=build_document_hash(source_text),
        status="DRAFTED",
    )
    context.session.add(document_task)
    context.session.flush()
    route_record, token_event = persist_route_and_token_from_estimate(
        context=context,
        task_id=task.id,
        route_estimate=route_estimate,
    )
    reply_text = build_document_refusal_reply() if safety_decision.decision == "ESCALATE" else build_document_review_reply(
        review_type=review_type,
        source_text=source_text,
    )
    if budget_posture.status == "WARN":
        reply_text = compose_budget_warn_prefix(posture=budget_posture) + reply_text
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="REFUSE_SCOPE" if safety_decision.decision == "ESCALATE" else "ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_document_listing(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare document listing", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    documents = list_active_document_tasks(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="DOCUMENT_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_document_list_reply(
        [
            {
                "id": document.id,
                "review_type": document.review_type,
                "status": document.status,
                "preview": document.source_text_preview,
                "created_at": document.created_at.isoformat(),
            }
            for document in documents
        ]
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


def process_document_forget(*, context, document_id: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare document forget", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    document_task = forget_active_document_task(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        document_id=document_id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="DOCUMENT_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_document_forgotten_reply() if document_task is not None else compose_document_not_found_reply(),
        scope_decision="ANSWER" if document_task is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )
