from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re
from uuid import NAMESPACE_URL, uuid5

from app.document_review import (
    build_document_hash,
    build_document_preview,
    build_follow_up_questions,
    build_notes,
    build_risk_notes,
    build_summary,
    is_prohibited_document_authority_request,
)
from app.telegram_document_intake_stub import TelegramDocumentIntakeStubRecord


DOCUMENT_REVIEW_PACK_STAGE = "166P"
MAX_SECTION_COUNT = 5
MAX_NOTE_COUNT = 5
MAX_TEXT_CHARS = 12000
PROFESSIONAL_BOUNDARY = "Draft-only review. Not legal, tax, financial, medical, or professional advice."
KEY_SECTION_MARKERS = (
    "must",
    "shall",
    "required",
    "deadline",
    "termination",
    "confidential",
    "payment",
    "fee",
    "penalty",
    "approval",
    "notice",
)


@dataclass(frozen=True, slots=True)
class DocumentReviewPackRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    document_title: str
    source_stage: str
    source_kind: str
    document_hash: str | None
    source_preview: str
    summary: str
    key_sections: tuple[str, ...]
    possible_risk_notes: tuple[str, ...]
    suggested_questions: tuple[str, ...]
    meeting_notes: tuple[str, ...]
    safe_next_step: str
    boundary: str
    draft_only: bool
    file_downloaded: bool
    content_parsed: bool
    pdf_text_extracted: bool
    ocr_used: bool
    persisted_state_written: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    professional_advice_provided: bool
    signature_or_acceptance_allowed: bool
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.stage != DOCUMENT_REVIEW_PACK_STAGE:
            raise ValueError("166P document review packs must identify the 166P stage.")
        if not self.draft_only:
            raise ValueError("166P document review packs must remain draft-only.")
        if any(
            (
                self.file_downloaded,
                self.ocr_used,
                self.persisted_state_written,
                self.memory_center_mutated,
                self.proposed_memory_written,
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
            raise ValueError("166P document review packs must not expand authority.")


def build_document_review_pack_record(
    *,
    owner_id: str,
    robot_id: str,
    document_title: str,
    extracted_text: str,
    source_stage: str = "owner_provided_text",
    source_kind: str = "text",
) -> DocumentReviewPackRecord:
    text = _bounded_text(extracted_text)
    if not text:
        return _blocked_record(
            owner_id=owner_id,
            robot_id=robot_id,
            document_title=document_title,
            source_stage=source_stage,
            source_kind=source_kind,
            error_code="missing_extracted_text",
        )
    if is_prohibited_document_authority_request(text):
        return _blocked_record(
            owner_id=owner_id,
            robot_id=robot_id,
            document_title=document_title,
            source_stage=source_stage,
            source_kind=source_kind,
            error_code="professional_authority_requested",
        )
    return DocumentReviewPackRecord(
        stage=DOCUMENT_REVIEW_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="completed_draft_review",
        document_title=document_title or "Untitled document",
        source_stage=source_stage,
        source_kind=source_kind,
        document_hash=build_document_hash(text),
        source_preview=build_document_preview(text),
        summary=build_summary(text),
        key_sections=_key_sections(text),
        possible_risk_notes=_split_notes(build_risk_notes(text)),
        suggested_questions=_split_notes(build_follow_up_questions(text)),
        meeting_notes=_meeting_notes(text),
        safe_next_step="Review this pack, confirm missing context, and decide whether a qualified advisor should review it.",
        boundary=PROFESSIONAL_BOUNDARY,
        draft_only=True,
        file_downloaded=False,
        content_parsed=True,
        pdf_text_extracted=source_kind in {"provided_pdf_text", "extracted_text"},
        ocr_used=False,
        persisted_state_written=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        professional_advice_provided=False,
        signature_or_acceptance_allowed=False,
    )


def build_document_review_pack_from_intake(
    *,
    intake_record: TelegramDocumentIntakeStubRecord,
    extracted_text: str | None = None,
) -> DocumentReviewPackRecord:
    if extracted_text is None or not extracted_text.strip():
        return _blocked_record(
            owner_id=intake_record.owner_id,
            robot_id=intake_record.robot_id,
            document_title=intake_record.file_name,
            source_stage=intake_record.stage,
            source_kind="telegram_document_metadata",
            error_code="telegram_file_text_unavailable",
        )
    return build_document_review_pack_record(
        owner_id=intake_record.owner_id,
        robot_id=intake_record.robot_id,
        document_title=intake_record.file_name,
        extracted_text=extracted_text,
        source_stage=intake_record.stage,
        source_kind="provided_pdf_text" if intake_record.mime_type == "application/pdf" else "provided_document_text",
    )


def render_document_review_pack(record: DocumentReviewPackRecord) -> str:
    lines = [
        "Document Review Pack",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Document: {record.document_title}",
        f"Source: {record.source_stage} / {record.source_kind}",
        "",
        "Summary:",
        f"- {record.summary}",
        "",
        "Key sections:",
        *_render_items(record.key_sections, "No key sections were identified."),
        "",
        "Possible risk notes:",
        *_render_items(record.possible_risk_notes, "No risk notes were identified."),
        "",
        "Suggested questions:",
        *_render_items(record.suggested_questions, "No suggested questions were identified."),
        "",
        "Meeting notes:",
        *_render_items(record.meeting_notes, "No meeting notes were generated."),
        "",
        f"Safe next step: {record.safe_next_step}",
        "",
        "Boundaries:",
        record.boundary,
        f"File downloaded: {str(record.file_downloaded).lower()}",
        f"Content parsed: {str(record.content_parsed).lower()}",
        f"PDF text extracted from live file: {str(record.pdf_text_extracted and record.source_stage != '158P').lower()}",
        f"OCR used: {str(record.ocr_used).lower()}",
        "Memory Center mutation: disabled",
        "ProposedMemory writes: disabled",
        "Model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "Signature or acceptance: disabled",
    ]
    if record.error_code is not None:
        lines.extend(["", f"Blocked reason: {record.error_code}"])
    return "\n".join(lines)


def _blocked_record(
    *,
    owner_id: str,
    robot_id: str,
    document_title: str,
    source_stage: str,
    source_kind: str,
    error_code: str,
) -> DocumentReviewPackRecord:
    return DocumentReviewPackRecord(
        stage=DOCUMENT_REVIEW_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="blocked_document_review_unavailable",
        document_title=document_title or "Untitled document",
        source_stage=source_stage,
        source_kind=source_kind,
        document_hash=None,
        source_preview="",
        summary="Document text is not available for local review.",
        key_sections=(),
        possible_risk_notes=(),
        suggested_questions=(),
        meeting_notes=(),
        safe_next_step="Provide extracted text or a supported local text source before requesting review.",
        boundary=PROFESSIONAL_BOUNDARY,
        draft_only=True,
        file_downloaded=False,
        content_parsed=False,
        pdf_text_extracted=False,
        ocr_used=False,
        persisted_state_written=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        professional_advice_provided=False,
        signature_or_acceptance_allowed=False,
        error_code=error_code,
    )


def _key_sections(text: str) -> tuple[str, ...]:
    sentences = _sentences(text)
    matches = [
        sentence
        for sentence in sentences
        if any(marker in sentence.lower() for marker in KEY_SECTION_MARKERS)
    ]
    return tuple((matches or sentences[:MAX_SECTION_COUNT])[:MAX_SECTION_COUNT])


def _meeting_notes(text: str) -> tuple[str, ...]:
    notes = [
        "Confirm document purpose, parties, dates, and current version.",
        "Review obligations, deadlines, approvals, and termination language.",
        "Prepare owner questions for unclear or high-impact sections.",
    ]
    lowered = text.lower()
    if "confidential" in lowered or "nda" in lowered:
        notes.append("Ask what information is covered and who is allowed to receive it.")
    if "payment" in lowered or "fee" in lowered:
        notes.append("Confirm payment timing, amounts, dependencies, and exceptions.")
    return tuple(notes[:MAX_NOTE_COUNT])


def _sentences(text: str) -> list[str]:
    compact = " ".join(text.split())
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]


def _split_notes(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"(?<=[.!?])\s+", value) if part.strip())[:MAX_NOTE_COUNT]


def _render_items(items: tuple[str, ...], empty: str) -> tuple[str, ...]:
    if not items:
        return (f"- {empty}",)
    return tuple(f"- {item}" for item in items)


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_TEXT_CHARS:
        return stripped
    return stripped[: MAX_TEXT_CHARS - 3].rstrip() + "..."


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:document-review-pack:" + ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.document_review_pack")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("text", nargs="?", default="This agreement requires notice within three business days.")
    args = parser.parse_args(argv)
    record = build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="local-text-document",
        extracted_text=args.text,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_document_review_pack(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
