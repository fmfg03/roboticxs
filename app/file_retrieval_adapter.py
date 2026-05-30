from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.config import Settings
from app.models import FileIntakeAttempt


@dataclass(slots=True, frozen=True)
class FileRetrievalAdapterRequest:
    request_kind: str
    user_id: str
    robot_id: str
    file_intake_id: str
    telegram_file_id: str
    telegram_file_unique_id: str | None
    file_name: str | None
    mime_type: str | None
    file_size: int | None


@dataclass(slots=True, frozen=True)
class FileRetrievalAdapterResult:
    adapter_kind: str
    live_retrieval_enabled: bool
    status: str
    reason_code: str


class FileRetrievalAdapter(Protocol):
    def plan_retrieval(self, *, request: FileRetrievalAdapterRequest) -> FileRetrievalAdapterResult:
        ...


class MockOnlyFileRetrievalAdapter:
    def __init__(self, *, retrieval_enabled: bool):
        self._retrieval_enabled = retrieval_enabled

    def plan_retrieval(self, *, request: FileRetrievalAdapterRequest) -> FileRetrievalAdapterResult:
        return describe_file_retrieval_policy(retrieval_enabled=self._retrieval_enabled)


def describe_file_retrieval_policy(*, retrieval_enabled: bool) -> FileRetrievalAdapterResult:
    if retrieval_enabled:
        return FileRetrievalAdapterResult(
            adapter_kind="mock_disabled",
            live_retrieval_enabled=True,
            status="ENABLED_BY_POLICY",
            reason_code="LIVE_RETRIEVAL_IMPLEMENTATION_NOT_AVAILABLE",
        )
    return FileRetrievalAdapterResult(
        adapter_kind="mock_disabled",
        live_retrieval_enabled=False,
        status="DISABLED_BY_POLICY",
        reason_code="FILE_RETRIEVAL_DISABLED_BY_POLICY",
    )


def build_file_retrieval_adapter_request(
    *,
    file_intake: FileIntakeAttempt,
    request_kind: str,
    user_id: str,
    robot_id: str,
) -> FileRetrievalAdapterRequest:
    return FileRetrievalAdapterRequest(
        request_kind=request_kind,
        user_id=user_id,
        robot_id=robot_id,
        file_intake_id=file_intake.id,
        telegram_file_id=file_intake.telegram_file_id,
        telegram_file_unique_id=file_intake.telegram_file_unique_id,
        file_name=file_intake.file_name,
        mime_type=file_intake.mime_type,
        file_size=file_intake.file_size,
    )


def get_file_retrieval_adapter(*, settings: Settings) -> FileRetrievalAdapter:
    return MockOnlyFileRetrievalAdapter(retrieval_enabled=settings.file_retrieval_enabled)


def is_live_file_retrieval_enabled(*, settings: Settings) -> bool:
    return settings.file_retrieval_enabled


def get_file_retrieval_policy_status(*, settings: Settings) -> FileRetrievalAdapterResult:
    return describe_file_retrieval_policy(retrieval_enabled=settings.file_retrieval_enabled)
