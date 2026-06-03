from __future__ import annotations

from app.action_approval_control import build_action_approval_packet
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.reply_composer import compose_action_approval_packet_reply
from app.safety import evaluate_safety


def process_action_approval_packet(*, context, source_command: str, requested_task: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="ACTION_APPROVAL_PACKET",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare action approval packet", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    packet = build_action_approval_packet(
        packet_id=task.id,
        user_id=context.user.id,
        robot_id=context.robot.id,
        source_command=source_command,
        requested_task=requested_task,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="ACTION_APPROVAL_PACKET",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_action_approval_packet_reply(packet=packet)
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )
