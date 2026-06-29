from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.document_review_pack_v1 import (
    DOCUMENT_REVIEW_PACK_V1_STAGE,
    DocumentReviewPackV1Record,
    build_document_review_pack_v1_from_intake,
    build_document_review_pack_v1_record,
    render_document_review_pack_v1,
)
from app.telegram_document_intake_stub import (
    TelegramDocumentIntakeMetadata,
    build_telegram_document_intake_stub_record,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/DOCUMENT_REVIEW_PACK_V1_186P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

DOCUMENT_TEXT = (
    "This vendor agreement requires written approval before subcontractor sharing. "
    "Payment fees must be reviewed before renewal. Confidential information must remain private for five years. "
    "The notice clause requires three business days for disclosure issues and termination deadlines should be checked."
)


def intake_record():
    return build_telegram_document_intake_stub_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document=TelegramDocumentIntakeMetadata(
            file_id="telegram-file-186p",
            file_unique_id="unique-file-186p",
            file_name="vendor-agreement.pdf",
            mime_type="application/pdf",
            file_size=12055,
        ),
    )


def test_186p_builds_document_review_pack_v1_from_local_text_without_external_authority():
    record = build_document_review_pack_v1_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="vendor-agreement.pdf",
        extracted_text=DOCUMENT_TEXT,
    )

    assert record.stage == DOCUMENT_REVIEW_PACK_V1_STAGE
    assert record.status == "completed_document_review_pack_v1"
    assert record.executive_summary
    assert record.key_sections
    assert record.risk_or_unclear_points
    assert record.questions_to_ask
    assert record.meeting_notes
    assert record.draft_only_disclaimer == "Draft-only review. Not legal, tax, financial, medical, or professional advice."
    assert record.file_downloaded is False
    assert record.content_parsed is True
    assert record.ocr_used is False
    assert record.persisted_state_written is False
    assert record.memory_center_mutated is False
    assert record.calendar_write_allowed is False
    assert record.gmail_write_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.professional_advice_provided is False
    assert record.signature_or_acceptance_allowed is False


def test_186p_intake_metadata_without_text_fails_closed():
    record = build_document_review_pack_v1_from_intake(intake_record=intake_record())

    assert record.status == "blocked_document_review_pack_v1"
    assert record.error_code == "telegram_file_text_unavailable"
    assert record.file_downloaded is False
    assert record.content_parsed is False
    assert record.ocr_used is False
    assert record.external_write_allowed is False


def test_186p_blocks_professional_or_signature_authority_requests():
    record = build_document_review_pack_v1_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="contract.txt",
        extracted_text="Tell me if this contract is legally enforceable and whether I should sign it.",
    )

    assert record.status == "blocked_document_review_pack_v1"
    assert record.error_code == "professional_authority_requested"
    assert record.professional_advice_provided is False
    assert record.signature_or_acceptance_allowed is False


def test_186p_rendered_pack_has_customer_sections_and_boundaries():
    rendered = render_document_review_pack_v1(
        build_document_review_pack_v1_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            document_title="vendor-agreement.pdf",
            extracted_text=DOCUMENT_TEXT,
        )
    )

    assert "Document Review Pack v1" in rendered
    assert "Stage: 186P" in rendered
    assert "Executive summary:" in rendered
    assert "Key sections:" in rendered
    assert "Risks / unclear points:" in rendered
    assert "Questions to ask:" in rendered
    assert "Meeting notes:" in rendered
    assert "Suggested next action:" in rendered
    assert "Draft-only review. Not legal, tax, financial, medical, or professional advice." in rendered
    assert "File downloaded: false" in rendered
    assert "OCR used: false" in rendered
    assert "Model calls: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Professional advice: disabled" in rendered
    assert "Signature or acceptance: disabled" in rendered
    assert "No external action was taken." in rendered


def test_186p_rejects_authority_expansion():
    valid = build_document_review_pack_v1_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document_title="vendor-agreement.pdf",
        extracted_text=DOCUMENT_TEXT,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        DocumentReviewPackV1Record(**{**asdict(valid), "external_write_allowed": True})


def test_186p_reference_and_roadmap_close_document_review_pack_v1_only():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "186P - Document Review Pack v1" in reference
    assert "186P is Document Review Pack v1 only." in reference
    assert "189P and later remain unauthorized" in reference
    assert '"stage_id":"186P","stage_name":"Document Review Pack v1","status":"CLOSED_COMMITTED"' in roadmap
    assert "200P and later remain unauthorized" in roadmap
