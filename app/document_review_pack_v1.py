from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from app.document_review_pack import (
    DocumentReviewPackRecord,
    build_document_review_pack_from_intake,
    build_document_review_pack_record,
)
from app.telegram_document_intake_stub import TelegramDocumentIntakeStubRecord


DOCUMENT_REVIEW_PACK_V1_STAGE = "186P"
DOCUMENT_REVIEW_PACK_V1_STATUS_COMPLETED = "completed_document_review_pack_v1"
DOCUMENT_REVIEW_PACK_V1_STATUS_BLOCKED = "blocked_document_review_pack_v1"
DOCUMENT_REVIEW_PACK_V1_DISCLAIMER = "Draft-only review. Not legal, tax, financial, medical, or professional advice."


@dataclass(frozen=True, slots=True)
class DocumentReviewPackV1Record:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    document_title: str
    source_stage: str
    source_kind: str
    executive_summary: str
    key_sections: tuple[str, ...]
    risk_or_unclear_points: tuple[str, ...]
    questions_to_ask: tuple[str, ...]
    meeting_notes: tuple[str, ...]
    suggested_next_action: str
    draft_only_disclaimer: str
    source_review_status: str
    error_code: str | None
    file_downloaded: bool
    content_parsed: bool
    ocr_used: bool
    persisted_state_written: bool
    memory_center_mutated: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    professional_advice_provided: bool
    signature_or_acceptance_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != DOCUMENT_REVIEW_PACK_V1_STAGE:
            raise ValueError("186P document review packs must identify the 186P stage.")
        if self.status not in {DOCUMENT_REVIEW_PACK_V1_STATUS_COMPLETED, DOCUMENT_REVIEW_PACK_V1_STATUS_BLOCKED}:
            raise ValueError("186P document review packs require a supported status.")
        if self.draft_only_disclaimer != DOCUMENT_REVIEW_PACK_V1_DISCLAIMER:
            raise ValueError("186P document review packs require the draft-only disclaimer.")
        if any(
            (
                self.file_downloaded,
                self.ocr_used,
                self.persisted_state_written,
                self.memory_center_mutated,
                self.calendar_write_allowed,
                self.gmail_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
                self.professional_advice_provided,
                self.signature_or_acceptance_allowed,
            )
        ):
            raise ValueError("186P document review packs must not expand authority.")


def build_document_review_pack_v1_record(
    *,
    owner_id: str,
    robot_id: str,
    document_title: str,
    extracted_text: str,
    source_stage: str = "owner_provided_text",
    source_kind: str = "text",
) -> DocumentReviewPackV1Record:
    source = build_document_review_pack_record(
        owner_id=owner_id,
        robot_id=robot_id,
        document_title=document_title,
        extracted_text=extracted_text,
        source_stage=source_stage,
        source_kind=source_kind,
    )
    return build_document_review_pack_v1_from_source(source)


def build_document_review_pack_v1_from_intake(
    *,
    intake_record: TelegramDocumentIntakeStubRecord,
    extracted_text: str | None = None,
) -> DocumentReviewPackV1Record:
    source = build_document_review_pack_from_intake(
        intake_record=intake_record,
        extracted_text=extracted_text,
    )
    return build_document_review_pack_v1_from_source(source)


def build_document_review_pack_v1_from_source(source: DocumentReviewPackRecord) -> DocumentReviewPackV1Record:
    completed = source.status == "completed_draft_review"
    return DocumentReviewPackV1Record(
        stage=DOCUMENT_REVIEW_PACK_V1_STAGE,
        owner_id=source.owner_id,
        robot_id=source.robot_id,
        status=DOCUMENT_REVIEW_PACK_V1_STATUS_COMPLETED if completed else DOCUMENT_REVIEW_PACK_V1_STATUS_BLOCKED,
        document_title=source.document_title,
        source_stage=source.source_stage,
        source_kind=source.source_kind,
        executive_summary=source.summary,
        key_sections=source.key_sections,
        risk_or_unclear_points=source.possible_risk_notes,
        questions_to_ask=source.suggested_questions,
        meeting_notes=source.meeting_notes,
        suggested_next_action=source.safe_next_step,
        draft_only_disclaimer=DOCUMENT_REVIEW_PACK_V1_DISCLAIMER,
        source_review_status=source.status,
        error_code=source.error_code,
        file_downloaded=source.file_downloaded,
        content_parsed=source.content_parsed,
        ocr_used=source.ocr_used,
        persisted_state_written=source.persisted_state_written,
        memory_center_mutated=source.memory_center_mutated,
        calendar_write_allowed=source.calendar_write_allowed,
        gmail_write_allowed=source.gmail_write_allowed,
        model_call_allowed=source.model_call_allowed,
        tool_call_allowed=source.tool_call_allowed,
        worker_dispatch_allowed=source.worker_dispatch_allowed,
        external_write_allowed=source.external_write_allowed,
        professional_advice_provided=source.professional_advice_provided,
        signature_or_acceptance_allowed=source.signature_or_acceptance_allowed,
    )


def render_document_review_pack_v1(record: DocumentReviewPackV1Record) -> str:
    lines = [
        "Document Review Pack v1",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Document: {record.document_title}",
        f"Source: {record.source_stage} / {record.source_kind}",
        "",
        "Executive summary:",
        f"- {record.executive_summary}",
        "",
        "Key sections:",
        *_render_items(record.key_sections, "No key sections were identified."),
        "",
        "Risks / unclear points:",
        *_render_items(record.risk_or_unclear_points, "No risks or unclear points were identified."),
        "",
        "Questions to ask:",
        *_render_items(record.questions_to_ask, "No questions were generated."),
        "",
        "Meeting notes:",
        *_render_items(record.meeting_notes, "No meeting notes were generated."),
        "",
        f"Suggested next action: {record.suggested_next_action}",
        "",
        "Draft-only disclaimer:",
        record.draft_only_disclaimer,
        "",
        "Boundaries:",
        f"File downloaded: {str(record.file_downloaded).lower()}",
        f"Content parsed: {str(record.content_parsed).lower()}",
        f"OCR used: {str(record.ocr_used).lower()}",
        "Persisted state written: false",
        "Memory Center mutation: disabled",
        "Calendar writes: disabled",
        "Gmail writes: disabled",
        "Model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "Professional advice: disabled",
        "Signature or acceptance: disabled",
    ]
    if record.error_code:
        lines.extend(["", f"Blocked reason: {record.error_code}"])
    lines.append("")
    lines.append("No external action was taken.")
    return "\n".join(lines)


def _render_items(items: tuple[str, ...], empty_text: str) -> tuple[str, ...]:
    if not items:
        return (f"- {empty_text}",)
    return tuple(f"- {item}" for item in items)


def main() -> int:
    record = build_document_review_pack_v1_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="local-text-document",
        extracted_text="This document requires review before a meeting and includes notice, approval, and deadline terms.",
    )
    print(json.dumps(asdict(record), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
