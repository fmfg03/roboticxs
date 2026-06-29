from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.document_review_pack import (
    DOCUMENT_REVIEW_PACK_STAGE,
    DocumentReviewPackRecord,
    build_document_review_pack_from_intake,
    build_document_review_pack_record,
    render_document_review_pack,
)
from app.telegram_document_intake_stub import (
    TelegramDocumentIntakeMetadata,
    build_telegram_document_intake_stub_record,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DOCUMENT_REVIEW_PACK_166P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

DOCUMENT_TEXT = (
    "This NDA requires the recipient to keep confidential information private for five years. "
    "The receiving party must notify the sender within three business days of any disclosure issue. "
    "Materials must be returned on request and subcontractor sharing requires written approval. "
    "Termination clauses and penalties for breach should be reviewed before the meeting."
)


def intake_record():
    return build_telegram_document_intake_stub_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document=TelegramDocumentIntakeMetadata(
            file_id="telegram-file-166p",
            file_unique_id="unique-file-166p",
            file_name="vendor-nda.pdf",
            mime_type="application/pdf",
            file_size=12055,
        ),
    )


def test_166p_builds_document_review_pack_from_available_text_without_external_authority():
    record = build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="vendor-nda.pdf",
        extracted_text=DOCUMENT_TEXT,
        source_stage="owner_provided_text",
    )

    assert record.stage == DOCUMENT_REVIEW_PACK_STAGE
    assert record.status == "completed_draft_review"
    assert record.document_hash is not None
    assert record.summary
    assert len(record.key_sections) >= 1
    assert any("confidential" in section.lower() for section in record.key_sections)
    assert len(record.possible_risk_notes) >= 1
    assert len(record.suggested_questions) >= 1
    assert len(record.meeting_notes) >= 3
    assert record.draft_only is True
    assert record.file_downloaded is False
    assert record.content_parsed is True
    assert record.ocr_used is False
    assert record.persisted_state_written is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.calendar_write_allowed is False
    assert record.gmail_write_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.professional_advice_provided is False
    assert record.signature_or_acceptance_allowed is False


def test_166p_intake_metadata_without_text_fails_closed():
    record = build_document_review_pack_from_intake(intake_record=intake_record())

    assert record.status == "blocked_document_review_unavailable"
    assert record.error_code == "telegram_file_text_unavailable"
    assert record.document_title == "vendor-nda.pdf"
    assert record.content_parsed is False
    assert record.file_downloaded is False
    assert record.ocr_used is False
    assert record.external_write_allowed is False


def test_166p_intake_with_provided_text_creates_pdf_text_review_pack_without_live_extraction():
    record = build_document_review_pack_from_intake(
        intake_record=intake_record(),
        extracted_text=DOCUMENT_TEXT,
    )

    assert record.status == "completed_draft_review"
    assert record.source_stage == "158P"
    assert record.source_kind == "provided_pdf_text"
    assert record.pdf_text_extracted is True
    assert record.file_downloaded is False
    assert record.ocr_used is False


def test_166p_professional_authority_request_is_blocked_not_answered():
    record = build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="contract.txt",
        extracted_text="Tell me if this contract is legally enforceable and whether I should sign.",
    )

    assert record.status == "blocked_document_review_unavailable"
    assert record.error_code == "professional_authority_requested"
    assert record.professional_advice_provided is False
    assert record.signature_or_acceptance_allowed is False


def test_166p_rendered_pack_has_customer_facing_sections_and_boundaries():
    record = build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="vendor-nda.pdf",
        extracted_text=DOCUMENT_TEXT,
    )

    rendered = render_document_review_pack(record)

    assert "Document Review Pack" in rendered
    assert "Stage: 166P" in rendered
    assert "Summary:" in rendered
    assert "Key sections:" in rendered
    assert "Possible risk notes:" in rendered
    assert "Suggested questions:" in rendered
    assert "Meeting notes:" in rendered
    assert "Safe next step:" in rendered
    assert "Draft-only review. Not legal, tax, financial, medical, or professional advice." in rendered
    assert "File downloaded: false" in rendered
    assert "OCR used: false" in rendered
    assert "Model calls: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Signature or acceptance: disabled" in rendered


def test_166p_record_rejects_authority_expansion():
    valid = build_document_review_pack_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="vendor-nda.pdf",
        extracted_text=DOCUMENT_TEXT,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        DocumentReviewPackRecord(**{**asdict(valid), "external_write_allowed": True})


def test_166p_reference_and_roadmap_close_document_review_without_external_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "166P is Document Review Pack v0 only." in reference
    assert "does not authorize live file download" in reference
    assert "not legal, tax, financial, medical, or professional advice" in reference
    assert '"stage_id":"166P","stage_name":"Document Review Pack v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "197P and later remain unauthorized" in roadmap
