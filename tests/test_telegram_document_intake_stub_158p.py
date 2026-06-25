from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.runnable_telegram_robot_mvp import (
    handle_incoming_command,
    parse_telegram_incoming_command,
)
from app.telegram_document_intake_stub import (
    TELEGRAM_DOCUMENT_INTAKE_STUB_STAGE,
    TelegramDocumentIntakeStubRecord,
    build_telegram_document_intake_stub_record,
    render_telegram_document_intake_stub,
)
from tests.test_runnable_telegram_robot_mvp_130p import build_command_update, build_valid_config, FakeTelegramClient


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/TELEGRAM_DOCUMENT_INTAKE_STUB_158P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_document_update(*, user_id: int = 111111111) -> dict:
    update = build_command_update(telegram_user_id=user_id, text="")
    message = update["message"]
    message.pop("text", None)
    message["document"] = {
        "file_id": "telegram-file-158p",
        "file_unique_id": "unique-file-158p",
        "file_name": "vendor-agreement.pdf",
        "mime_type": "application/pdf",
        "file_size": 12055,
    }
    return update


def test_158p_parser_recognizes_document_metadata_as_internal_document_command():
    incoming = parse_telegram_incoming_command(build_document_update())

    assert incoming is not None
    assert incoming.command == "/document"
    assert incoming.raw_text == "[telegram document metadata]"
    assert incoming.document is not None
    assert incoming.document.file_id == "telegram-file-158p"
    assert incoming.document.file_name == "vendor-agreement.pdf"


def test_158p_document_stub_reply_is_draft_only_and_no_content_processing():
    incoming = parse_telegram_incoming_command(build_document_update())
    assert incoming is not None
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=build_valid_config(),
    )

    assert receipt.command == "/document"
    assert receipt.authorized is True
    assert "Document Intake" in receipt.reply_text
    assert "vendor-agreement.pdf" in receipt.reply_text
    assert "application/pdf" in receipt.reply_text
    assert "12055 bytes" in receipt.reply_text
    assert "summarize it" in receipt.reply_text
    assert "prepare meeting notes" in receipt.reply_text
    assert "flag risks for your review" in receipt.reply_text
    assert "Document review is currently draft-only." in receipt.reply_text
    assert "I received Telegram metadata only." in receipt.reply_text
    assert "File downloaded: false" in receipt.reply_text
    assert "Content parsed: false" in receipt.reply_text
    assert "OCR used: false" in receipt.reply_text
    assert "Persisted state written: false" in receipt.reply_text
    assert "Memory Center mutation: disabled" in receipt.reply_text
    assert "Model calls: disabled" in receipt.reply_text
    assert "External writes: disabled" in receipt.reply_text


def test_158p_unauthorized_document_update_does_not_render_document_intake():
    incoming = parse_telegram_incoming_command(build_document_update(user_id=999999999))
    assert incoming is not None
    client = FakeTelegramClient()

    receipt = handle_incoming_command(
        incoming_command=incoming,
        client=client,
        config=build_valid_config(),
    )

    assert receipt.authorized is False
    assert receipt.reply_text == "This Roboticxs bot is private. No action was taken."
    assert "Document Intake" not in receipt.reply_text


def test_158p_record_rejects_authority_expansion():
    incoming = parse_telegram_incoming_command(build_document_update())
    assert incoming is not None and incoming.document is not None
    valid = build_telegram_document_intake_stub_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document=incoming.document,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        TelegramDocumentIntakeStubRecord(**{**asdict(valid), "file_downloaded": True})


def test_158p_render_handles_missing_optional_metadata():
    incoming = parse_telegram_incoming_command(
        {
            "update_id": 15801,
            "message": {
                "message_id": 158,
                "chat": {"id": 4004, "type": "private"},
                "from": {"id": 111111111, "is_bot": False},
                "document": {"file_id": "telegram-file-minimal-158p"},
            },
        }
    )
    assert incoming is not None and incoming.document is not None
    record = build_telegram_document_intake_stub_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        document=incoming.document,
    )
    rendered = render_telegram_document_intake_stub(record)

    assert record.stage == TELEGRAM_DOCUMENT_INTAKE_STUB_STAGE
    assert "unnamed document" in rendered
    assert "unknown mime type" in rendered
    assert "unknown size" in rendered


def test_158p_reference_and_roadmap_close_document_stub_without_authority_expansion():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "recognize Telegram `message.document` metadata" in reference
    assert "does not download files" in reference
    assert "mutate Memory Center" in reference
    assert '"stage_id":"158P","stage_name":"Telegram Document Intake Stub v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "160P and later remain unauthorized" in roadmap
