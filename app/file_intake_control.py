from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import FileIntakeAttempt, FileRetrievalAttempt, FileRetrievalEnablementRequest


LIST_FILES_COMMAND = "what files did you receive"
LIST_PENDING_FILE_RETRIEVALS_COMMAND = "what file retrievals are pending"
FILE_RETRIEVAL_STATUS_COMMAND = "show file retrieval status"
FILE_RETRIEVAL_POLICY_COMMAND = "show retrieval policy"
FILE_RETRIEVAL_ENABLEMENT_REQUEST_COMMAND = "request file retrieval enablement"
RETRIEVAL_ENABLEMENT_REQUEST_COMMAND = "request retrieval enablement"
LIST_PENDING_FILE_RETRIEVAL_ENABLEMENT_REQUESTS_COMMAND = "what retrieval enablement requests are pending"
LIST_FILE_RETRIEVAL_ENABLEMENT_REQUEST_HISTORY_COMMAND = "what retrieval enablement requests do you have"
FILE_RETRIEVAL_ENABLEMENT_REQUEST_HISTORY_COMMAND = "show retrieval enablement request history"
FILE_RETRIEVAL_CONTROL_SUMMARY_COMMAND = "show retrieval control summary"
FILE_RETRIEVAL_CONTROLS_COMMAND = "show file retrieval controls"
FILE_RETRIEVAL_CONTROL_REPORT_COMMAND = "show retrieval control report"
FILE_RETRIEVAL_AUDIT_REPORT_COMMAND = "show file retrieval audit report"
APPROVE_FILE_RETRIEVAL_ENABLEMENT_REQUEST_PATTERN = re.compile(
    r"^approve retrieval enablement request ([a-f0-9-]+)$",
    re.IGNORECASE,
)
REJECT_FILE_RETRIEVAL_ENABLEMENT_REQUEST_PATTERN = re.compile(
    r"^reject retrieval enablement request ([a-f0-9-]+)$",
    re.IGNORECASE,
)
FORGET_FILE_PATTERN = re.compile(r"^forget file ([a-f0-9-]+)$", re.IGNORECASE)
RETRIEVE_FILE_PATTERN = re.compile(r"^retrieve file ([a-f0-9-]+)$", re.IGNORECASE)
PREPARE_FILE_PATTERN = re.compile(r"^prepare file ([a-f0-9-]+) for review$", re.IGNORECASE)
CANCEL_FILE_RETRIEVAL_PATTERN = re.compile(r"^cancel file retrieval ([a-f0-9-]+)$", re.IGNORECASE)
ACTIVE_FILE_STATUS = "METADATA_RECEIVED"
FORGOTTEN_FILE_STATUS = "FORGOTTEN"
PENDING_FILE_RETRIEVAL_STATUSES = (
    "REQUESTED_NOT_ENABLED",
    "READY_FOR_RETRIEVAL_WHEN_ENABLED",
    "BLOCKED_BY_POLICY",
    "DISABLED_BY_POLICY",
)
PENDING_FILE_RETRIEVAL_ENABLEMENT_REQUEST_STATUSES = ("REQUESTED_DISABLED",)


@dataclass(slots=True)
class ForgetFileRequest:
    file_id: str


@dataclass(slots=True)
class FileRetrievalRequest:
    file_id: str
    request_kind: str


@dataclass(slots=True)
class CancelFileRetrievalRequest:
    retrieval_id: str


@dataclass(slots=True)
class ResolveFileRetrievalEnablementRequest:
    request_id: str
    resolution: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_list_files_command(text: str) -> bool:
    return text.strip().lower() == LIST_FILES_COMMAND


def is_list_pending_file_retrievals_command(text: str) -> bool:
    return text.strip().lower() == LIST_PENDING_FILE_RETRIEVALS_COMMAND


def is_file_retrieval_status_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {FILE_RETRIEVAL_STATUS_COMMAND, FILE_RETRIEVAL_POLICY_COMMAND}


def is_file_retrieval_enablement_request_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        FILE_RETRIEVAL_ENABLEMENT_REQUEST_COMMAND,
        RETRIEVAL_ENABLEMENT_REQUEST_COMMAND,
    }


def is_list_pending_file_retrieval_enablement_requests_command(text: str) -> bool:
    return text.strip().lower() == LIST_PENDING_FILE_RETRIEVAL_ENABLEMENT_REQUESTS_COMMAND


def is_list_file_retrieval_enablement_request_history_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        LIST_FILE_RETRIEVAL_ENABLEMENT_REQUEST_HISTORY_COMMAND,
        FILE_RETRIEVAL_ENABLEMENT_REQUEST_HISTORY_COMMAND,
    }


def is_file_retrieval_control_summary_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        FILE_RETRIEVAL_CONTROL_SUMMARY_COMMAND,
        FILE_RETRIEVAL_CONTROLS_COMMAND,
    }


def is_file_retrieval_control_report_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        FILE_RETRIEVAL_CONTROL_REPORT_COMMAND,
        FILE_RETRIEVAL_AUDIT_REPORT_COMMAND,
    }


def parse_forget_file_command(text: str) -> ForgetFileRequest | None:
    match = FORGET_FILE_PATTERN.match(text.strip())
    if match is None:
        return None
    return ForgetFileRequest(file_id=match.group(1))


def parse_retrieve_file_command(text: str) -> FileRetrievalRequest | None:
    normalized = text.strip()
    retrieve_match = RETRIEVE_FILE_PATTERN.match(normalized)
    if retrieve_match is not None:
        return FileRetrievalRequest(file_id=retrieve_match.group(1), request_kind="RETRIEVE")
    prepare_match = PREPARE_FILE_PATTERN.match(normalized)
    if prepare_match is not None:
        return FileRetrievalRequest(file_id=prepare_match.group(1), request_kind="PREPARE_FOR_REVIEW")
    return None


def parse_cancel_file_retrieval_command(text: str) -> CancelFileRetrievalRequest | None:
    match = CANCEL_FILE_RETRIEVAL_PATTERN.match(text.strip())
    if match is None:
        return None
    return CancelFileRetrievalRequest(retrieval_id=match.group(1))


def parse_resolve_file_retrieval_enablement_request_command(text: str) -> ResolveFileRetrievalEnablementRequest | None:
    normalized = text.strip()
    approve_match = APPROVE_FILE_RETRIEVAL_ENABLEMENT_REQUEST_PATTERN.match(normalized)
    if approve_match is not None:
        return ResolveFileRetrievalEnablementRequest(
            request_id=approve_match.group(1),
            resolution="APPROVED_PENDING_POLICY_CHANGE",
        )
    reject_match = REJECT_FILE_RETRIEVAL_ENABLEMENT_REQUEST_PATTERN.match(normalized)
    if reject_match is not None:
        return ResolveFileRetrievalEnablementRequest(
            request_id=reject_match.group(1),
            resolution="REJECTED",
        )
    return None


def list_active_file_intakes(*, session: Session, user_id: str, robot_id: str) -> list[FileIntakeAttempt]:
    return session.scalars(
        select(FileIntakeAttempt)
        .where(
            FileIntakeAttempt.user_id == user_id,
            FileIntakeAttempt.robot_id == robot_id,
            FileIntakeAttempt.status == ACTIVE_FILE_STATUS,
        )
        .order_by(desc(FileIntakeAttempt.created_at))
    ).all()


def forget_active_file_intake(*, session: Session, user_id: str, robot_id: str, file_id: str) -> FileIntakeAttempt | None:
    file_intake = session.scalar(
        select(FileIntakeAttempt).where(
            FileIntakeAttempt.id == file_id,
            FileIntakeAttempt.user_id == user_id,
            FileIntakeAttempt.robot_id == robot_id,
            FileIntakeAttempt.status == ACTIVE_FILE_STATUS,
        )
    )
    if file_intake is None:
        return None
    file_intake.status = FORGOTTEN_FILE_STATUS
    file_intake.updated_at = now_utc()
    return file_intake


def get_active_file_intake(*, session: Session, user_id: str, robot_id: str, file_id: str) -> FileIntakeAttempt | None:
    return session.scalar(
        select(FileIntakeAttempt).where(
            FileIntakeAttempt.id == file_id,
            FileIntakeAttempt.user_id == user_id,
            FileIntakeAttempt.robot_id == robot_id,
            FileIntakeAttempt.status == ACTIVE_FILE_STATUS,
        )
    )


def list_pending_file_retrieval_attempts(*, session: Session, user_id: str, robot_id: str) -> list[FileRetrievalAttempt]:
    return session.scalars(
        select(FileRetrievalAttempt)
        .where(
            FileRetrievalAttempt.user_id == user_id,
            FileRetrievalAttempt.robot_id == robot_id,
            FileRetrievalAttempt.status.in_(PENDING_FILE_RETRIEVAL_STATUSES),
        )
        .order_by(desc(FileRetrievalAttempt.created_at))
    ).all()


def cancel_pending_file_retrieval_attempt(*, session: Session, user_id: str, robot_id: str, retrieval_id: str) -> FileRetrievalAttempt | None:
    attempt = session.scalar(
        select(FileRetrievalAttempt).where(
            FileRetrievalAttempt.id == retrieval_id,
            FileRetrievalAttempt.user_id == user_id,
            FileRetrievalAttempt.robot_id == robot_id,
            FileRetrievalAttempt.status.in_(PENDING_FILE_RETRIEVAL_STATUSES),
        )
    )
    if attempt is None:
        return None
    attempt.status = "CANCELLED"
    attempt.updated_at = now_utc()
    session.flush()
    return attempt


def list_pending_file_retrieval_enablement_requests(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
) -> list[FileRetrievalEnablementRequest]:
    return session.scalars(
        select(FileRetrievalEnablementRequest)
        .where(
            FileRetrievalEnablementRequest.user_id == user_id,
            FileRetrievalEnablementRequest.robot_id == robot_id,
            FileRetrievalEnablementRequest.status.in_(PENDING_FILE_RETRIEVAL_ENABLEMENT_REQUEST_STATUSES),
        )
        .order_by(desc(FileRetrievalEnablementRequest.created_at))
    ).all()


def list_file_retrieval_enablement_requests(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
) -> list[FileRetrievalEnablementRequest]:
    return session.scalars(
        select(FileRetrievalEnablementRequest)
        .where(
            FileRetrievalEnablementRequest.user_id == user_id,
            FileRetrievalEnablementRequest.robot_id == robot_id,
        )
        .order_by(desc(FileRetrievalEnablementRequest.created_at))
    ).all()


def resolve_file_retrieval_enablement_request(
    *,
    session: Session,
    user_id: str,
    robot_id: str,
    request_id: str,
    resolution: str,
) -> FileRetrievalEnablementRequest | None:
    request = session.scalar(
        select(FileRetrievalEnablementRequest).where(
            FileRetrievalEnablementRequest.id == request_id,
            FileRetrievalEnablementRequest.user_id == user_id,
            FileRetrievalEnablementRequest.robot_id == robot_id,
            FileRetrievalEnablementRequest.status.in_(PENDING_FILE_RETRIEVAL_ENABLEMENT_REQUEST_STATUSES),
        )
    )
    if request is None:
        return None
    request.status = resolution
    request.updated_at = now_utc()
    session.flush()
    return request
