from __future__ import annotations

from app.flow_runtime import (
    build_budgeted_route_estimate,
    build_flow_response,
    create_task_and_run,
    describe_file_metadata_input,
    persist_route_and_token_from_estimate,
    persist_safety_decision,
)
from app.models import FileIntakeAttempt
from app.reply_composer import compose_budget_block_reply, compose_budget_warn_prefix
from app.safety import evaluate_safety


def process_file_intake(*, context) -> dict:
    document = context.envelope.document
    input_text = describe_file_metadata_input(document)
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="EXTRACTION",
        input_text=input_text,
    )
    route_estimate, budget_posture = build_budgeted_route_estimate(
        context=context,
        text=input_text,
        task_id=task.id,
        task_family="FILE_INTAKE",
        task_class="EXTRACTION",
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

    safety_result = evaluate_safety("receive file metadata", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)

    file_intake_attempt = FileIntakeAttempt(
        user_id=context.user.id,
        robot_id=context.robot.id,
        task_id=task.id,
        source_channel="telegram",
        telegram_file_id=document.file_id,
        telegram_file_unique_id=document.file_unique_id,
        file_name=document.file_name,
        mime_type=document.mime_type,
        file_size=document.file_size,
        status="METADATA_RECEIVED",
    )
    context.session.add(file_intake_attempt)
    context.session.flush()

    route_record, token_event = persist_route_and_token_from_estimate(
        context=context,
        task_id=task.id,
        route_estimate=route_estimate,
    )

    file_name = document.file_name or "your file"
    reply_text = (
        f"I received the file metadata for {file_name}.\n\n"
        "File review is not enabled yet. I did not download, parse, OCR, review, or store the file contents.\n\n"
        "If you want a draft review now, paste the relevant text using:\n"
        "review document: <text>"
    )
    if budget_posture.status == "WARN":
        reply_text = compose_budget_warn_prefix(posture=budget_posture) + reply_text
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )
