from __future__ import annotations

from app.file_retrieval_adapter import (
    build_file_retrieval_adapter_request,
    get_file_retrieval_adapter,
    get_file_retrieval_policy_status,
)
from app.file_intake_control import (
    cancel_pending_file_retrieval_attempt,
    forget_active_file_intake,
    get_active_file_intake,
    list_active_file_intakes,
    list_file_retrieval_enablement_requests,
    list_pending_file_retrieval_enablement_requests,
    list_pending_file_retrieval_attempts,
    resolve_file_retrieval_enablement_request,
)
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.models import FileIntakeAttempt, FileRetrievalAttempt, FileRetrievalEnablementRequest
from app.reply_composer import (
    compose_file_retrieval_control_report_reply,
    compose_file_retrieval_control_summary_reply,
    compose_file_retrieval_enablement_request_history_reply,
    compose_file_retrieval_enablement_request_reply,
    compose_file_retrieval_enablement_request_not_found_reply,
    compose_file_retrieval_enablement_request_resolved_reply,
    compose_file_retrieval_cancel_not_found_reply,
    compose_file_retrieval_cancelled_reply,
    compose_file_retrieval_not_found_reply,
    compose_file_retrieval_policy_status_reply,
    compose_file_retrieval_preflight_reply,
    compose_pending_file_retrieval_enablement_requests_reply,
    compose_pending_file_retrievals_reply,
)
from app.safety import evaluate_safety


def process_file_listing(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file metadata listing", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    file_intakes = list_active_file_intakes(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = _compose_file_list_reply(file_intakes)
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_file_forget(*, context, file_id: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file metadata forget", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    file_intake = forget_active_file_intake(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        file_id=file_id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=_compose_file_forgotten_reply() if file_intake is not None else _compose_file_not_found_reply(),
        scope_decision="ANSWER" if file_intake is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_file_retrieval_preflight(*, context, file_id: str, request_kind: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file retrieval preflight", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    file_intake = get_active_file_intake(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        file_id=file_id,
    )
    if file_intake is not None:
        adapter = get_file_retrieval_adapter(settings=context.settings)
        adapter_request = build_file_retrieval_adapter_request(
            file_intake=file_intake,
            request_kind=request_kind,
            user_id=context.user.id,
            robot_id=context.robot.id,
        )
        adapter_result = adapter.plan_retrieval(request=adapter_request)
        retrieval_attempt = FileRetrievalAttempt(
            user_id=context.user.id,
            robot_id=context.robot.id,
            task_id=task.id,
            file_intake_id=file_intake.id,
            request_kind=request_kind,
            status=adapter_result.status,
        )
        context.session.add(retrieval_attempt)
        context.session.flush()
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_PREFLIGHT",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_file_retrieval_preflight_reply(
            request_kind=request_kind,
            file_name=file_intake.file_name or "your file",
        ) if file_intake is not None else compose_file_retrieval_not_found_reply(),
        scope_decision="ANSWER" if file_intake is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_pending_file_retrieval_listing(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare pending file retrieval listing", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    retrievals = list_pending_file_retrieval_attempts(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_pending_file_retrievals_reply(
        [
            {
                "id": retrieval.id,
                "request_kind": retrieval.request_kind,
                "status": retrieval.status,
                "file_name": _lookup_file_name(context=context, file_intake_id=retrieval.file_intake_id),
                "created_at": retrieval.created_at.isoformat(),
            }
            for retrieval in retrievals
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


def process_file_retrieval_cancel(*, context, retrieval_id: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file retrieval cancellation", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    retrieval = cancel_pending_file_retrieval_attempt(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        retrieval_id=retrieval_id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_file_retrieval_cancelled_reply() if retrieval is not None else compose_file_retrieval_cancel_not_found_reply(),
        scope_decision="ANSWER" if retrieval is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_file_retrieval_policy_status(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file retrieval policy status", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    policy_status = get_file_retrieval_policy_status(settings=context.settings)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_file_retrieval_policy_status_reply(
            status=policy_status.status,
            reason_code=policy_status.reason_code,
        ),
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_file_retrieval_enablement_request(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare file retrieval enablement request", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    policy_status = get_file_retrieval_policy_status(settings=context.settings)
    request = FileRetrievalEnablementRequest(
        user_id=context.user.id,
        robot_id=context.robot.id,
        task_id=task.id,
        status="REQUESTED_DISABLED",
        reason_code=policy_status.reason_code,
    )
    context.session.add(request)
    context.session.flush()
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_file_retrieval_enablement_request_reply(reason_code=policy_status.reason_code),
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_pending_file_retrieval_enablement_request_listing(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare retrieval enablement request listing", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    requests = list_pending_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_pending_file_retrieval_enablement_requests_reply(
        [
            {
                "id": request.id,
                "status": request.status,
                "reason_code": request.reason_code,
                "created_at": request.created_at.isoformat(),
            }
            for request in requests
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


def process_file_retrieval_enablement_request_history(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare retrieval enablement request history", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    requests = list_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_file_retrieval_enablement_request_history_reply(
        [
            {
                "id": request.id,
                "status": request.status,
                "reason_code": request.reason_code,
                "created_at": request.created_at.isoformat(),
                "updated_at": request.updated_at.isoformat(),
            }
            for request in requests
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


def process_file_retrieval_control_summary(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare retrieval control summary", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    policy_status = get_file_retrieval_policy_status(settings=context.settings)
    pending_retrievals = list_pending_file_retrieval_attempts(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    pending_enablement_requests = list_pending_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    enablement_request_history = list_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_file_retrieval_control_summary_reply(
        policy_status=policy_status.status,
        reason_code=policy_status.reason_code,
        pending_retrieval_intents_count=len(pending_retrievals),
        pending_enablement_requests_count=len(pending_enablement_requests),
        recent_enablement_request_outcomes=[
            {
                "id": request.id,
                "status": request.status,
                "reason_code": request.reason_code,
                "updated_at": request.updated_at.isoformat(),
            }
            for request in enablement_request_history[:5]
        ],
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


def process_file_retrieval_control_report(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare retrieval control report", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    policy_status = get_file_retrieval_policy_status(settings=context.settings)
    pending_retrievals = list_pending_file_retrieval_attempts(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    pending_enablement_requests = list_pending_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    enablement_request_history = list_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_file_retrieval_control_report_reply(
        policy_status=policy_status.status,
        reason_code=policy_status.reason_code,
        pending_retrieval_intents_count=len(pending_retrievals),
        pending_enablement_requests_count=len(pending_enablement_requests),
        recent_enablement_request_outcomes=[
            {
                "id": request.id,
                "status": request.status,
                "reason_code": request.reason_code,
                "updated_at": request.updated_at.isoformat(),
            }
            for request in enablement_request_history[:5]
        ],
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


def process_file_retrieval_enablement_request_resolution(*, context, request_id: str, resolution: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare retrieval enablement request resolution", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    request = resolve_file_retrieval_enablement_request(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        request_id=request_id,
        resolution=resolution,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_file_retrieval_enablement_request_resolved_reply(resolution=resolution)
        if request is not None
        else compose_file_retrieval_enablement_request_not_found_reply(),
        scope_decision="ANSWER" if request is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def _lookup_file_name(*, context, file_intake_id: str) -> str:
    file_intake = context.session.get(FileIntakeAttempt, file_intake_id)
    if file_intake is not None and file_intake.file_name:
        return file_intake.file_name
    return "unknown file"


def _compose_file_list_reply(file_intakes: list) -> str:
    if not file_intakes:
        return "I do not have any active retained file metadata records for this robot."

    lines = ["Here are the file metadata records I currently retain for this robot:", ""]
    for index, file_intake in enumerate(file_intakes, start=1):
        file_name = file_intake.file_name or "unnamed file"
        mime_type = file_intake.mime_type or "unknown mime type"
        file_size = f"{file_intake.file_size} bytes" if file_intake.file_size is not None else "unknown size"
        lines.append(
            f"{index}. [{file_intake.id}] {file_name} — {mime_type} — {file_size} — "
            f"{file_intake.status} — {file_intake.created_at.isoformat()}"
        )
    lines.extend(
        [
            "",
            "I have not downloaded, parsed, OCRed, reviewed, or stored the file contents.",
            f"To remove one, reply: forget file {file_intakes[0].id}",
        ]
    )
    return "\n".join(lines)


def _compose_file_forgotten_reply() -> str:
    return "Forgotten. I will no longer retain that file metadata record as active."


def _compose_file_not_found_reply() -> str:
    return "I could not find an active file metadata record with that ID for this robot."
