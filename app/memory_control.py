from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import MemoryItem


LIST_COMMAND = "what do you remember"
LIST_PENDING_PROPOSALS_COMMAND = "what memory proposals are pending"
MEMORY_CONTROL_HELP_COMMANDS = {
    "how do i control memory",
    "memory help",
    "what memory commands can i use",
    "cómo controlo tu memoria",
    "como controlo tu memoria",
    "cómo controlo lo que recuerdas",
    "como controlo lo que recuerdas",
}
FORGET_PATTERN = re.compile(r"^forget memory ([a-f0-9-]+)$", re.IGNORECASE)


@dataclass(slots=True)
class ForgetRequest:
    memory_id: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_list_memories_command(text: str) -> bool:
    return text.strip().lower() == LIST_COMMAND


def is_list_pending_memory_proposals_command(text: str) -> bool:
    return text.strip().lower() == LIST_PENDING_PROPOSALS_COMMAND


def is_memory_control_help_request(text: str) -> bool:
    normalized = text.strip().lower().lstrip("¿").rstrip("?").strip()
    return normalized in MEMORY_CONTROL_HELP_COMMANDS


def parse_forget_command(text: str) -> ForgetRequest | None:
    match = FORGET_PATTERN.match(text.strip())
    if match is None:
        return None
    return ForgetRequest(memory_id=match.group(1))


def list_active_memories(*, session: Session, user_id: str, robot_id: str) -> list[MemoryItem]:
    return session.scalars(
        select(MemoryItem)
        .where(
            MemoryItem.user_id == user_id,
            MemoryItem.robot_id == robot_id,
            MemoryItem.status == "ACTIVE",
        )
        .order_by(desc(MemoryItem.created_at))
    ).all()


def forget_active_memory(*, session: Session, user_id: str, robot_id: str, memory_id: str) -> MemoryItem | None:
    memory = session.scalar(
        select(MemoryItem).where(
            MemoryItem.id == memory_id,
            MemoryItem.user_id == user_id,
            MemoryItem.robot_id == robot_id,
            MemoryItem.status == "ACTIVE",
        )
    )
    if memory is None:
        return None
    memory.status = "FORGOTTEN"
    memory.updated_at = now_utc()
    return memory


def summarize_active_memory_context(memories: list[MemoryItem]) -> str:
    if not memories:
        return ""

    labels = []
    for memory in memories:
        if memory.memory_type == "BOUNDARY_MEMORY":
            labels.append("robot limits")
        elif memory.memory_type == "WORK_PREFERENCE":
            labels.append("preferences")
        elif memory.memory_type == "USER_PROFILE":
            labels.append("profile details")
        else:
            labels.append("saved context")

    unique_labels: list[str] = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)

    if len(unique_labels) == 1:
        return unique_labels[0]
    return ", ".join(unique_labels[:-1]) + f" and {unique_labels[-1]}"
