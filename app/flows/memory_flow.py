from __future__ import annotations

from app.flow_runtime import build_budgeted_route_estimate, build_flow_response, create_task_and_run, persist_route_and_token, persist_route_and_token_from_estimate, persist_safety_decision
from app.memory_control import forget_active_memory, list_active_memories
from app.memory_service import (
    approve_proposal,
    create_proposed_memory,
    get_latest_pending_proposal,
    list_pending_proposals,
    pending_display_label_for_memory_type,
    reject_proposal,
)
from app.reply_composer import (
    compose_budget_block_reply,
    compose_budget_warn_prefix,
    compose_memory_control_help_reply,
    compose_memory_approved_reply,
    compose_memory_boundary_reply,
    compose_memory_forgotten_reply,
    compose_memory_list_reply,
    compose_memory_needs_clearer_framing_reply,
    compose_memory_not_found_reply,
    compose_memory_proposal_reply,
    compose_memory_rejected_reply,
    compose_no_pending_memory_reply,
    compose_pending_memory_review_reply,
    compose_upgrade_interest_approved_reply,
    compose_upgrade_interest_proposal_reply,
)
from app.safety import evaluate_safety


def process_memory_proposal(*, context, proposal_payload: dict) -> dict:
    task = create_task_and_run(
        context=context,
        kind="MEMORY_PROPOSAL",
        scope_decision="ANSWER",
        task_class="EXTRACTION",
    )
    route_estimate, budget_posture = build_budgeted_route_estimate(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_PROPOSAL",
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

    safety_result = evaluate_safety(context.envelope.text, "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    route_record, token_event = persist_route_and_token_from_estimate(
        context=context,
        task_id=task.id,
        route_estimate=route_estimate,
    )

    if safety_decision.decision != "ALLOW" and proposal_payload["memory_type"] != "BOUNDARY_MEMORY":
        scope_decision = "CLARIFY" if safety_decision.decision == "ASK_CONFIRMATION" else "REFUSE_SCOPE"
        reply_text = compose_memory_needs_clearer_framing_reply()
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

    proposal = create_proposed_memory(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        task_id=task.id,
        memory_type=proposal_payload["memory_type"],
        proposed_content=proposal_payload["content"],
        source_text=context.envelope.text,
        importance=proposal_payload["importance"],
    )
    if proposal.memory_type == "BOUNDARY_MEMORY":
        reply_text = compose_memory_boundary_reply(proposal.proposed_content)
    elif proposal.memory_type == "UPGRADE_INTEREST":
        reply_text = compose_upgrade_interest_proposal_reply(proposal.proposed_content)
    else:
        reply_text = compose_memory_proposal_reply(label=proposal_payload["label"], content=proposal.proposed_content)
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


def process_memory_control_help(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare memory control help", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_memory_control_help_reply(),
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_memory_listing(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare memory listing", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    memories = list_active_memories(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_memory_list_reply(
        [{"id": memory.id, "label": memory.display_label, "content": memory.content} for memory in memories]
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


def process_pending_memory_review(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare pending memory review", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    proposals = list_pending_proposals(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_pending_memory_review_reply(
        [
            {
                "id": proposal.id,
                "label": pending_display_label_for_memory_type(proposal.memory_type),
                "content": proposal.proposed_content,
                "memory_type": proposal.memory_type,
            }
            for proposal in proposals
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


def process_memory_forget(*, context, memory_id: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="GENERAL_TASK",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare memory forget", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    memory = forget_active_memory(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
        memory_id=memory_id,
    )
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
    )
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=compose_memory_forgotten_reply() if memory is not None else compose_memory_not_found_reply(),
        scope_decision="ANSWER" if memory is not None else "CLARIFY",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def process_memory_decision(*, context, command: str) -> dict:
    task = create_task_and_run(
        context=context,
        kind="MEMORY_DECISION",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    pending = get_latest_pending_proposal(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    if pending is None:
        safety_result = {
            "action_class": "PREPARE",
            "decision": "ALLOW",
            "reason_code": "NO_PENDING_MEMORY",
            "user_message": compose_no_pending_memory_reply(),
        }
        safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
        route_record, token_event = persist_route_and_token(
            context=context,
            text=context.envelope.text,
            task_id=task.id,
            task_family="MEMORY_DECISION",
            task_class="SIMPLE_CLASSIFICATION",
        )
        return build_flow_response(
            context=context,
            task_id=task.id,
            reply_text=compose_no_pending_memory_reply(),
            scope_decision="CLARIFY",
            safety_decision=safety_decision,
            route_record=route_record,
            token_event=token_event,
        )

    route_estimate, budget_posture = build_budgeted_route_estimate(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="MEMORY_DECISION",
        task_class="SIMPLE_CLASSIFICATION",
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

    safety_result = evaluate_safety("prepare memory decision", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)
    if command == "APPROVE":
        approve_proposal(session=context.session, proposal=pending)
        if pending.memory_type == "UPGRADE_INTEREST":
            reply_text = compose_upgrade_interest_approved_reply()
        else:
            reply_text = compose_memory_approved_reply()
    else:
        reject_proposal(session=context.session, proposal=pending)
        reply_text = compose_memory_rejected_reply()

    route_record, token_event = persist_route_and_token_from_estimate(
        context=context,
        task_id=task.id,
        route_estimate=route_estimate,
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
