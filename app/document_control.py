from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import DocumentTask


LIST_DOCUMENTS_COMMAND = "what documents did you review"
FORGET_DOCUMENT_PATTERN = re.compile(r"^forget document ([a-f0-9-]+)$", re.IGNORECASE)
ACTIVE_DOCUMENT_STATUS = "DRAFTED"
FORGOTTEN_DOCUMENT_STATUS = "FORGOTTEN"


@dataclass(slots=True)
class ForgetDocumentRequest:
    document_id: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_list_documents_command(text: str) -> bool:
    return text.strip().lower() == LIST_DOCUMENTS_COMMAND


def parse_forget_document_command(text: str) -> ForgetDocumentRequest | None:
    match = FORGET_DOCUMENT_PATTERN.match(text.strip())
    if match is None:
        return None
    return ForgetDocumentRequest(document_id=match.group(1))


def list_active_document_tasks(*, session: Session, user_id: str, robot_id: str) -> list[DocumentTask]:
    return session.scalars(
        select(DocumentTask)
        .where(
            DocumentTask.user_id == user_id,
            DocumentTask.robot_id == robot_id,
            DocumentTask.status == ACTIVE_DOCUMENT_STATUS,
        )
        .order_by(desc(DocumentTask.created_at))
    ).all()


def forget_active_document_task(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    document_id: str,
) -> DocumentTask | None:
    document_task = session.scalar(
        select(DocumentTask).where(
            DocumentTask.id == document_id,
            DocumentTask.user_id == user_id,
            DocumentTask.robot_id == robot_id,
            DocumentTask.status == ACTIVE_DOCUMENT_STATUS,
        )
    )
    if document_task is None:
        return None
    document_task.status = FORGOTTEN_DOCUMENT_STATUS
    document_task.updated_at = now_utc()
    return document_task
