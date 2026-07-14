from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.user_confirmation_runtime import (
    CONFIRMATION_STATUS_APPROVED,
    USER_CONFIRMATION_RUNTIME_STAGE,
    UserConfirmationReceipt,
)


APPROVED_OUTPUT_EXPORT_STAGE = "179P"
APPROVED_OUTPUT_EXPORT_FORMATS = frozenset({"text", "email_draft", "local_file"})
EXPORT_STATUS_CREATED = "local_export_payload_created"
EXPORT_STATUS_MISSING_CONFIRMATION_ID = "blocked_missing_confirmation_id"
EXPORT_STATUS_CONFIRMATION_NOT_FOUND = "blocked_confirmation_not_found"
EXPORT_STATUS_NOT_APPROVED = "blocked_confirmation_not_approved"


@dataclass(frozen=True, slots=True)
class ApprovedOutputExportRecord:
    stage: str
    owner_id: str
    robot_id: str
    export_id: str
    confirmation_id: str
    source_stage: str
    export_format: str
    export_status: str
    title: str
    payload_preview: str
    local_export_payload_created: bool
    owner_requested: bool
    gmail_draft_created: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    local_file_written: bool
    task_persisted: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != APPROVED_OUTPUT_EXPORT_STAGE:
            raise ValueError("179P approved output exports must identify the 179P stage.")
        if self.source_stage != USER_CONFIRMATION_RUNTIME_STAGE:
            raise ValueError("179P approved output exports must originate from 178P confirmations.")
        if self.export_format not in APPROVED_OUTPUT_EXPORT_FORMATS:
            raise ValueError("179P approved output exports require a supported format.")
        if self.export_status not in {
            EXPORT_STATUS_CREATED,
            EXPORT_STATUS_MISSING_CONFIRMATION_ID,
            EXPORT_STATUS_CONFIRMATION_NOT_FOUND,
            EXPORT_STATUS_NOT_APPROVED,
        }:
            raise ValueError("179P approved output export status must be supported.")
        if not self.owner_requested:
            raise ValueError("179P approved output exports require owner request.")
        if self.local_export_payload_created != (self.export_status == EXPORT_STATUS_CREATED):
            raise ValueError("179P approved output export payload flag must match status.")
        if any(
            (
                self.gmail_draft_created,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.local_file_written,
                self.task_persisted,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("179P approved output exports must not expand authority.")


def build_approved_output_export(
    *,
    owner_id: str,
    robot_id: str,
    confirmation_id: str,
    export_format: str,
    confirmations: tuple[UserConfirmationReceipt, ...] = (),
) -> ApprovedOutputExportRecord:
    normalized_confirmation_id = confirmation_id.strip()
    normalized_format = export_format.strip().lower()
    if normalized_format not in APPROVED_OUTPUT_EXPORT_FORMATS:
        raise ValueError("rejected_invalid_approved_output_export_format")
    for receipt in confirmations:
        if receipt.owner_id != owner_id or receipt.robot_id != robot_id:
            raise ValueError("rejected_approved_output_export_owner_robot_mismatch")
    if not normalized_confirmation_id:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id="",
            export_format=normalized_format,
            export_status=EXPORT_STATUS_MISSING_CONFIRMATION_ID,
            receipt=None,
        )
    receipt = next((item for item in confirmations if item.confirmation_id == normalized_confirmation_id), None)
    if receipt is None:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            export_format=normalized_format,
            export_status=EXPORT_STATUS_CONFIRMATION_NOT_FOUND,
            receipt=None,
        )
    if receipt.confirmation_status != CONFIRMATION_STATUS_APPROVED:
        return _record(
            owner_id=owner_id,
            robot_id=robot_id,
            confirmation_id=normalized_confirmation_id,
            export_format=normalized_format,
            export_status=EXPORT_STATUS_NOT_APPROVED,
            receipt=receipt,
        )
    return _record(
        owner_id=owner_id,
        robot_id=robot_id,
        confirmation_id=normalized_confirmation_id,
        export_format=normalized_format,
        export_status=EXPORT_STATUS_CREATED,
        receipt=receipt,
    )


def render_approved_output_export(record: ApprovedOutputExportRecord) -> str:
    lines = [
        "Approved Output Export",
        "",
        f"Stage: {record.stage}",
        f"Export id: {record.export_id}",
        f"Confirmation id: {record.confirmation_id or 'none'}",
        f"Format: {record.export_format}",
        f"Status: {record.export_status}",
        f"Title: {record.title or 'not available'}",
        "",
        "Payload:",
        f"- {record.payload_preview or 'No local export payload was created.'}",
        "",
        "Meaning:",
        *_meaning_lines(record),
        "",
        "Boundaries:",
        f"Local export payload created: {'true' if record.local_export_payload_created else 'false'}",
        "Gmail draft creation: disabled",
        "Gmail send: disabled",
        "Gmail modify/archive/label: disabled",
        "Calendar writes: disabled",
        "Local file write: disabled",
        "Task persistence: disabled",
        "Memory Center mutation: disabled",
        "Model calls: disabled",
        "Tools/workers: disabled",
        "External writes: disabled",
        "",
        "No external action was taken.",
    ]
    return "\n".join(lines)


def _meaning_lines(record: ApprovedOutputExportRecord) -> tuple[str, ...]:
    if record.export_status == EXPORT_STATUS_CREATED:
        return (
            "- Approved output is available as a local export payload.",
            "- You can copy it manually; nothing was sent or written.",
        )
    if record.export_status == EXPORT_STATUS_MISSING_CONFIRMATION_ID:
        return ("- No confirmation id was provided.", "- Use a locally approved confirmation receipt first.")
    if record.export_status == EXPORT_STATUS_NOT_APPROVED:
        return ("- That confirmation is not approved for export.", "- No payload was created.")
    return ("- That confirmation is not available in the current local context.", "- No payload was created.")


def _record(
    *,
    owner_id: str,
    robot_id: str,
    confirmation_id: str,
    export_format: str,
    export_status: str,
    receipt: UserConfirmationReceipt | None,
) -> ApprovedOutputExportRecord:
    title = "" if receipt is None else receipt.draft_title
    payload_preview = "" if export_status != EXPORT_STATUS_CREATED else _payload_preview(export_format, receipt)
    return ApprovedOutputExportRecord(
        stage=APPROVED_OUTPUT_EXPORT_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        export_id=_stable_export_id(owner_id, robot_id, confirmation_id, export_format, export_status),
        confirmation_id=confirmation_id,
        source_stage=USER_CONFIRMATION_RUNTIME_STAGE,
        export_format=export_format,
        export_status=export_status,
        title=title,
        payload_preview=payload_preview,
        local_export_payload_created=export_status == EXPORT_STATUS_CREATED,
        owner_requested=True,
        gmail_draft_created=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        local_file_written=False,
        task_persisted=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _payload_preview(export_format: str, receipt: UserConfirmationReceipt | None) -> str:
    if receipt is None:
        return ""
    if export_format == "email_draft":
        return f"Subject: {receipt.draft_title}; Body: Approved local draft output for manual review."
    if export_format == "local_file":
        return f"local-file-payload:{receipt.confirmation_id}.txt -> {receipt.draft_title}"
    return f"{receipt.draft_title}: Approved local draft output for manual copy."


def _stable_export_id(owner_id: str, robot_id: str, confirmation_id: str, export_format: str, export_status: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"roboticxs:approved-output-export:{owner_id}:{robot_id}:{confirmation_id}:{export_format}:{export_status}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.approved_output_export")
    parser.add_argument("export_format", choices=sorted(APPROVED_OUTPUT_EXPORT_FORMATS))
    parser.add_argument("confirmation_id", nargs="?", default="")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = build_approved_output_export(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        confirmation_id=args.confirmation_id,
        export_format=args.export_format,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_approved_output_export(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
