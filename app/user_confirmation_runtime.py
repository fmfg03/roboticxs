from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.action_draft_queue import ACTION_DRAFT_QUEUE_STAGE, ActionDraftQueue, ActionDraftRecord


USER_CONFIRMATION_RUNTIME_STAGE = "178P"
USER_CONFIRMATION_CHOICES = frozenset({"approve", "reject", "edit", "expire"})
CONFIRMATION_STATUS_APPROVED = "approved_pending_export_local_receipt"
CONFIRMATION_STATUS_REJECTED = "rejected_local_receipt"
CONFIRMATION_STATUS_EDIT_PENDING = "edit_pending_local_receipt"
CONFIRMATION_STATUS_EXPIRED = "expired_local_receipt"
CONFIRMATION_STATUS_MISSING_DRAFT_ID = "blocked_missing_draft_id"
CONFIRMATION_STATUS_DRAFT_NOT_FOUND = "blocked_draft_not_found"
CONFIRMATION_STATUS_MISSING_EDIT_TEXT = "blocked_missing_edit_text"


@dataclass(frozen=True, slots=True)
class UserConfirmationReceipt:
    stage: str
    owner_id: str
    robot_id: str
    draft_id: str
    source_stage: str
    confirmation_id: str
    choice: str
    confirmation_status: str
    draft_title: str
    edited_text: str
    local_receipt_created: bool
    owner_requested: bool
    action_executed: bool
    approved_output_exported: bool
    gmail_draft_created: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    task_persisted: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != USER_CONFIRMATION_RUNTIME_STAGE:
            raise ValueError("178P user confirmations must identify the 178P stage.")
        if self.source_stage != ACTION_DRAFT_QUEUE_STAGE:
            raise ValueError("178P user confirmations must originate from 177P action draft queues.")
        if self.choice not in USER_CONFIRMATION_CHOICES:
            raise ValueError("178P user confirmations require a supported choice.")
        if self.confirmation_status not in {
            CONFIRMATION_STATUS_APPROVED,
            CONFIRMATION_STATUS_REJECTED,
            CONFIRMATION_STATUS_EDIT_PENDING,
            CONFIRMATION_STATUS_EXPIRED,
            CONFIRMATION_STATUS_MISSING_DRAFT_ID,
            CONFIRMATION_STATUS_DRAFT_NOT_FOUND,
            CONFIRMATION_STATUS_MISSING_EDIT_TEXT,
        }:
            raise ValueError("178P user confirmation status must be supported.")
        if not self.local_receipt_created or not self.owner_requested:
            raise ValueError("178P user confirmations require owner request and local receipt.")
        if any(
            (
                self.action_executed,
                self.approved_output_exported,
                self.gmail_draft_created,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.task_persisted,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("178P user confirmations must not expand authority.")


def build_user_confirmation_receipt(
    *,
    owner_id: str,
    robot_id: str,
    draft_id: str,
    choice: str,
    queue: ActionDraftQueue,
    edited_text: str = "",
) -> UserConfirmationReceipt:
    normalized_draft_id = draft_id.strip()
    normalized_choice = choice.strip().lower()
    normalized_edit_text = " ".join(edited_text.split())
    if normalized_choice not in USER_CONFIRMATION_CHOICES:
        raise ValueError("rejected_invalid_user_confirmation_choice")
    if queue.owner_id != owner_id or queue.robot_id != robot_id:
        raise ValueError("rejected_user_confirmation_queue_owner_robot_mismatch")
    if not normalized_draft_id:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            draft_id="",
            choice=normalized_choice,
            confirmation_status=CONFIRMATION_STATUS_MISSING_DRAFT_ID,
            draft=None,
            edited_text="",
        )
    draft = next((item for item in queue.drafts if item.draft_id == normalized_draft_id), None)
    if draft is None:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            draft_id=normalized_draft_id,
            choice=normalized_choice,
            confirmation_status=CONFIRMATION_STATUS_DRAFT_NOT_FOUND,
            draft=None,
            edited_text="",
        )
    if normalized_choice == "edit" and not normalized_edit_text:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            draft_id=normalized_draft_id,
            choice=normalized_choice,
            confirmation_status=CONFIRMATION_STATUS_MISSING_EDIT_TEXT,
            draft=draft,
            edited_text="",
        )
    status_by_choice = {
        "approve": CONFIRMATION_STATUS_APPROVED,
        "reject": CONFIRMATION_STATUS_REJECTED,
        "edit": CONFIRMATION_STATUS_EDIT_PENDING,
        "expire": CONFIRMATION_STATUS_EXPIRED,
    }
    return _receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        draft_id=normalized_draft_id,
        choice=normalized_choice,
        confirmation_status=status_by_choice[normalized_choice],
        draft=draft,
        edited_text=normalized_edit_text if normalized_choice == "edit" else "",
    )


def render_user_confirmation_receipt(record: UserConfirmationReceipt) -> str:
    lines = [
        "User Confirmation Receipt",
        "",
        f"Stage: {record.stage}",
        f"Confirmation id: {record.confirmation_id}",
        f"Draft id: {record.draft_id or 'none'}",
        f"Choice: {record.choice}",
        f"Status: {record.confirmation_status}",
        f"Draft: {record.draft_title or 'not available'}",
    ]
    if record.edited_text:
        lines.append(f"Edited text: {record.edited_text}")
    lines.extend(
        [
            "Owner requested: true",
            "Local receipt created: true",
            "",
            *_meaning_lines(record),
            "",
            "Action executed: false",
            "Approved output export: disabled",
            "Gmail draft creation: disabled",
            "Gmail send: disabled",
            "Gmail modify/archive/label: disabled",
            "Calendar writes: disabled",
            "Task persistence: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _meaning_lines(record: UserConfirmationReceipt) -> tuple[str, ...]:
    if record.confirmation_status == CONFIRMATION_STATUS_APPROVED:
        return (
            "Meaning:",
            "- Your approval intent was recorded locally.",
            "- Nothing was exported or executed.",
        )
    if record.confirmation_status == CONFIRMATION_STATUS_REJECTED:
        return (
            "Meaning:",
            "- Your rejection intent was recorded locally.",
            "- The source draft was not changed.",
        )
    if record.confirmation_status == CONFIRMATION_STATUS_EDIT_PENDING:
        return (
            "Meaning:",
            "- Your edit intent was recorded locally.",
            "- No rewritten draft was persisted or exported.",
        )
    if record.confirmation_status == CONFIRMATION_STATUS_EXPIRED:
        return (
            "Meaning:",
            "- Your expire intent was recorded locally.",
            "- No queue state was persisted.",
        )
    if record.confirmation_status == CONFIRMATION_STATUS_MISSING_DRAFT_ID:
        return (
            "Meaning:",
            "- No draft id was provided.",
            "- Use /drafts to review pending local drafts first.",
        )
    if record.confirmation_status == CONFIRMATION_STATUS_MISSING_EDIT_TEXT:
        return (
            "Meaning:",
            "- No edit text was provided.",
            "- Use /draft_edit <draft_id> <text>.",
        )
    return (
        "Meaning:",
        "- That draft is not available in the current local queue.",
        "- No confirmation was applied to a draft.",
    )


def _receipt(
    *,
    owner_id: str,
    robot_id: str,
    draft_id: str,
    choice: str,
    confirmation_status: str,
    draft: ActionDraftRecord | None,
    edited_text: str,
) -> UserConfirmationReceipt:
    draft_title = "" if draft is None else draft.title
    return UserConfirmationReceipt(
        stage=USER_CONFIRMATION_RUNTIME_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        draft_id=draft_id,
        source_stage=ACTION_DRAFT_QUEUE_STAGE,
        confirmation_id=_stable_confirmation_id(owner_id, robot_id, draft_id, choice, confirmation_status, edited_text),
        choice=choice,
        confirmation_status=confirmation_status,
        draft_title=draft_title,
        edited_text=edited_text,
        local_receipt_created=True,
        owner_requested=True,
        action_executed=False,
        approved_output_exported=False,
        gmail_draft_created=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        task_persisted=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _stable_confirmation_id(
    owner_id: str,
    robot_id: str,
    draft_id: str,
    choice: str,
    confirmation_status: str,
    edited_text: str,
) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"roboticxs:user-confirmation:{owner_id}:{robot_id}:{draft_id}:{choice}:{confirmation_status}:{edited_text}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.user_confirmation_runtime")
    parser.add_argument("choice", choices=sorted(USER_CONFIRMATION_CHOICES))
    parser.add_argument("draft_id", nargs="?", default="")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--edit-text", default="")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    queue = ActionDraftQueue(
        stage=ACTION_DRAFT_QUEUE_STAGE,
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        status="empty",
        drafts=(),
        skipped_decision_ids=(),
        local_queue_created=True,
        no_external_action_taken=True,
        gmail_draft_creation_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        task_persistence_allowed=False,
        memory_center_mutation_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )
    record = build_user_confirmation_receipt(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        draft_id=args.draft_id,
        choice=args.choice,
        queue=queue,
        edited_text=args.edit_text,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_user_confirmation_receipt(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
