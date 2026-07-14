from __future__ import annotations

from dataclasses import dataclass


TELEGRAM_DOCUMENT_INTAKE_STUB_STAGE = "158P"


@dataclass(frozen=True, slots=True)
class TelegramDocumentIntakeMetadata:
    file_id: str
    file_unique_id: str | None
    file_name: str | None
    mime_type: str | None
    file_size: int | None

    def __post_init__(self) -> None:
        if not self.file_id.strip():
            raise ValueError("158P document intake requires Telegram file_id metadata.")


@dataclass(frozen=True, slots=True)
class TelegramDocumentIntakeStubRecord:
    stage: str
    owner_id: str
    robot_id: str
    file_id_seen: bool
    file_unique_id_seen: bool
    file_name: str
    mime_type: str
    file_size_label: str
    status: str
    draft_only: bool
    file_downloaded: bool
    content_parsed: bool
    ocr_used: bool
    summary_created: bool
    risk_review_created: bool
    persisted_state_written: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != TELEGRAM_DOCUMENT_INTAKE_STUB_STAGE:
            raise ValueError("158P document intake records must identify the 158P stage.")
        if not self.draft_only:
            raise ValueError("158P document intake must remain draft-only.")
        if any(
            (
                self.file_downloaded,
                self.content_parsed,
                self.ocr_used,
                self.summary_created,
                self.risk_review_created,
                self.persisted_state_written,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("158P document intake stub must not expand authority.")


def build_telegram_document_intake_stub_record(
    *,
    owner_id: str,
    robot_id: str,
    document: TelegramDocumentIntakeMetadata,
) -> TelegramDocumentIntakeStubRecord:
    file_size_label = "unknown size"
    if document.file_size is not None:
        file_size_label = f"{document.file_size} bytes"
    return TelegramDocumentIntakeStubRecord(
        stage=TELEGRAM_DOCUMENT_INTAKE_STUB_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        file_id_seen=True,
        file_unique_id_seen=bool(document.file_unique_id),
        file_name=document.file_name or "unnamed document",
        mime_type=document.mime_type or "unknown mime type",
        file_size_label=file_size_label,
        status="metadata_received_draft_only",
        draft_only=True,
        file_downloaded=False,
        content_parsed=False,
        ocr_used=False,
        summary_created=False,
        risk_review_created=False,
        persisted_state_written=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_telegram_document_intake_stub(record: TelegramDocumentIntakeStubRecord) -> str:
    return "\n".join(
        [
            "Document Intake",
            "",
            f"Status: {record.status}",
            "Draft-only: true",
            "",
            "Received:",
            f"- File name: {record.file_name}",
            f"- MIME type: {record.mime_type}",
            f"- Size: {record.file_size_label}",
            "",
            "What I can do later:",
            "- summarize it",
            "- prepare meeting notes",
            "- flag risks for your review",
            "",
            "Current limit:",
            "- Document review is currently draft-only.",
            "- I received Telegram metadata only.",
            "",
            "Boundaries:",
            "File downloaded: false",
            "Content parsed: false",
            "OCR used: false",
            "Summary created: false",
            "Risk review created: false",
            "Persisted state written: false",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
