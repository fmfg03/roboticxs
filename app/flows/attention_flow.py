from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import desc, select

from app.budget_policy import evaluate_budget_posture, get_budget_policy
from app.document_control import list_active_document_tasks
from app.file_intake_control import (
    list_active_file_intakes,
    list_pending_file_retrieval_attempts,
    list_pending_file_retrieval_enablement_requests,
)
from app.flow_runtime import build_flow_response, create_task_and_run, persist_route_and_token, persist_safety_decision
from app.memory_control import list_active_memories
from app.models import ProposedMemory, Task, TaskRun
from app.reply_composer import compose_attention_summary_reply
from app.safety import evaluate_safety
from app.usage_reporting import build_usage_summary


@dataclass(slots=True)
class AttentionFinding:
    rank: int
    sort_key: tuple[int | str, ...]
    text: str


def process_attention_summary(*, context) -> dict:
    task = create_task_and_run(
        context=context,
        kind="ATTENTION_STATUS",
        scope_decision="ANSWER",
        task_class="SIMPLE_CLASSIFICATION",
    )
    safety_result = evaluate_safety("prepare attention summary", "ANSWER")
    safety_decision = persist_safety_decision(context=context, task_id=task.id, safety_result=safety_result)

    findings = _build_attention_findings(context=context, current_task_id=task.id)
    route_record, token_event = persist_route_and_token(
        context=context,
        text=context.envelope.text,
        task_id=task.id,
        task_family="ATTENTION_STATUS",
        task_class="SIMPLE_CLASSIFICATION",
    )
    reply_text = compose_attention_summary_reply([finding.text for finding in findings])
    return build_flow_response(
        context=context,
        task_id=task.id,
        reply_text=reply_text,
        scope_decision="ANSWER",
        safety_decision=safety_decision,
        route_record=route_record,
        token_event=token_event,
    )


def _build_attention_findings(*, context, current_task_id: str) -> list[AttentionFinding]:
    findings: list[AttentionFinding] = []

    budget_finding = _build_budget_finding(context=context)
    if budget_finding is not None:
        findings.append(budget_finding)

    pending_enablement_requests = list_pending_file_retrieval_enablement_requests(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    if pending_enablement_requests:
        findings.append(
            AttentionFinding(
                rank=3,
                sort_key=(-len(pending_enablement_requests),),
                text=f"Tienes {len(pending_enablement_requests)} solicitudes de enablement de retrieval pendientes.",
            )
        )

    pending_retrievals = list_pending_file_retrieval_attempts(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    if pending_retrievals:
        findings.append(
            AttentionFinding(
                rank=4,
                sort_key=(-len(pending_retrievals),),
                text=f"Tienes {len(pending_retrievals)} solicitudes de retrieval pendientes.",
            )
        )

    active_file_intakes = list_active_file_intakes(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    if active_file_intakes:
        findings.append(
            AttentionFinding(
                rank=5,
                sort_key=(-len(active_file_intakes),),
                text=f"Hay {len(active_file_intakes)} archivos recibidos que todavía no tienen revisión registrada.",
            )
        )

    active_document_tasks = list_active_document_tasks(
        session=context.session,
        user_id=context.user.id,
        robot_id=context.robot.id,
    )
    if active_document_tasks:
        findings.append(
            AttentionFinding(
                rank=6,
                sort_key=(-len(active_document_tasks),),
                text=f"Hay {len(active_document_tasks)} documentos revisados recientemente que puedes conservar u olvidar.",
            )
        )

    unresolved_task_runs = context.session.execute(
        select(TaskRun, Task)
        .join(Task, Task.id == TaskRun.task_id)
        .where(
            Task.user_id == context.user.id,
            Task.robot_id == context.robot.id,
            Task.id != current_task_id,
            Task.kind != "ATTENTION_STATUS",
            TaskRun.status.in_(("pending", "failed", "blocked")),
        )
        .order_by(desc(TaskRun.created_at))
    ).all()
    if unresolved_task_runs:
        findings.append(
            AttentionFinding(
                rank=7,
                sort_key=(-len(unresolved_task_runs),),
                text=f"Hay {len(unresolved_task_runs)} tasks recientes que quedaron pendientes, bloqueados o fallidos.",
            )
        )

    pending_memories = context.session.scalars(
        select(ProposedMemory)
        .where(
            ProposedMemory.user_id == context.user.id,
            ProposedMemory.robot_id == context.robot.id,
            ProposedMemory.status == "PENDING",
        )
        .order_by(desc(ProposedMemory.created_at))
    ).all()
    if pending_memories:
        findings.append(
            AttentionFinding(
                rank=8,
                sort_key=(-len(pending_memories),),
                text=f"Tienes {len(pending_memories)} memorias pendientes de aprobación.",
            )
        )

    important_memories = [
        memory
        for memory in list_active_memories(
            session=context.session,
            user_id=context.user.id,
            robot_id=context.robot.id,
        )
        if (memory.importance or "normal").lower() != "normal"
    ]
    if important_memories:
        findings.append(
            AttentionFinding(
                rank=9,
                sort_key=(-len(important_memories),),
                text=f"Hay {len(important_memories)} memorias activas marcadas como importantes.",
            )
        )

    findings.sort(key=lambda item: (item.rank, item.sort_key, item.text))
    return findings[:7]


def _build_budget_finding(*, context) -> AttentionFinding | None:
    summary = build_usage_summary(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    policy = get_budget_policy(session=context.session, user_id=context.user.id, robot_id=context.robot.id)
    posture = evaluate_budget_posture(
        summary=summary,
        estimated_route_cost_usd=0.0,
        policy=policy,
    )
    if posture.status == "BLOCK":
        return AttentionFinding(
            rank=2,
            sort_key=(0, -posture.usage_percentage),
            text=f"Tu presupuesto está bloqueado localmente y va en {posture.usage_percentage:.0f}%.",
        )
    if posture.status == "WARN":
        return AttentionFinding(
            rank=2,
            sort_key=(1, -posture.usage_percentage),
            text=f"Tu presupuesto está al {posture.usage_percentage:.0f}%.",
        )
    return None
