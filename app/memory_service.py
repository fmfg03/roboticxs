from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import MemoryItem, ProposedMemory


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_proposed_memory(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    task_id: str,
    memory_type: str,
    proposed_content: str,
    source_text: str,
    importance: str,
) -> ProposedMemory:
    expire_pending_proposals(session=session, user_id=user_id, robot_id=robot_id)
    proposal = ProposedMemory(
        user_id=user_id,
        robot_id=robot_id,
        task_id=task_id,
        memory_type=memory_type,
        proposed_content=proposed_content,
        source_text=source_text,
        status="PENDING",
    )
    session.add(proposal)
    session.flush()
    proposal.importance = importance  # transient convenience for reply composition
    return proposal


def expire_pending_proposals(*, session: Session, user_id: str, robot_id: str) -> None:
    pending = session.scalars(
        select(ProposedMemory).where(
            ProposedMemory.user_id == user_id,
            ProposedMemory.robot_id == robot_id,
            ProposedMemory.status == "PENDING",
        )
    ).all()
    for proposal in pending:
        proposal.status = "EXPIRED"
        proposal.decided_at = now_utc()


def get_latest_pending_proposal(*, session: Session, user_id: str, robot_id: str) -> ProposedMemory | None:
    return session.scalar(
        select(ProposedMemory)
        .where(
            ProposedMemory.user_id == user_id,
            ProposedMemory.robot_id == robot_id,
            ProposedMemory.status == "PENDING",
        )
        .order_by(desc(ProposedMemory.created_at))
        .limit(1)
    )


def list_pending_proposals(*, session: Session, user_id: str, robot_id: str) -> list[ProposedMemory]:
    return session.scalars(
        select(ProposedMemory)
        .where(
            ProposedMemory.user_id == user_id,
            ProposedMemory.robot_id == robot_id,
            ProposedMemory.status == "PENDING",
        )
        .order_by(desc(ProposedMemory.created_at))
    ).all()


def approve_proposal(*, session: Session, proposal: ProposedMemory) -> MemoryItem:
    proposal.status = "APPROVED"
    proposal.decided_at = now_utc()
    memory = MemoryItem(
        user_id=proposal.user_id,
        robot_id=proposal.robot_id,
        memory_type=proposal.memory_type,
        content=proposal.proposed_content,
        display_label=display_label_for_memory_type(proposal.memory_type),
        source="telegram_text",
        status="ACTIVE",
        importance="high" if proposal.memory_type == "BOUNDARY_MEMORY" else "normal",
    )
    session.add(memory)
    session.flush()
    return memory


def reject_proposal(*, session: Session, proposal: ProposedMemory) -> None:
    proposal.status = "REJECTED"
    proposal.decided_at = now_utc()


def display_label_for_memory_type(memory_type: str) -> str:
    return {
        "WORK_PREFERENCE": "Preference",
        "BOUNDARY_MEMORY": "Boundary",
        "USER_PROFILE": "Profile",
        "BUSINESS_CONTEXT": "Business context",
        "UPGRADE_INTEREST": "Interés local",
        "TASK_MEMORY": "Memory",
    }.get(memory_type, "Memory")


def pending_display_label_for_memory_type(memory_type: str) -> str:
    return {
        "WORK_PREFERENCE": "Preferencia de trabajo pendiente",
        "BOUNDARY_MEMORY": "Límite del robot pendiente",
        "USER_PROFILE": "Perfil pendiente",
        "BUSINESS_CONTEXT": "Contexto de negocio pendiente",
        "UPGRADE_INTEREST": "Interés local pendiente",
        "TASK_MEMORY": "Memoria pendiente",
    }.get(memory_type, "Memoria pendiente")
