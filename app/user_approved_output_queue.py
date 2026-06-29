from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5


USER_APPROVED_OUTPUT_QUEUE_STAGE = "RQF-027R"
APPROVAL_STATUS_PENDING = "pending_user_approval"
APPROVAL_DECISION_APPROVED = "approved_local_receipt"
APPROVAL_DECISION_REJECTED = "rejected_local_receipt"
APPROVAL_DECISION_MISSING_ID = "blocked_missing_approval_id"
APPROVAL_DECISION_NOT_FOUND = "blocked_approval_not_found"
SUPPORTED_APPROVAL_DECISIONS = frozenset({"approve", "reject"})


@dataclass(frozen=True, slots=True)
class UserApprovedOutputItem:
    stage: str
    owner_id: str
    robot_id: str
    approval_id: str
    output_type: str
    title: str
    body_preview: str
    status: str
    source: str
    local_only: bool
    requires_user_approval: bool
    email_sent: bool
    gmail_draft_created: bool
    calendar_event_created: bool
    external_action_performed: bool
    external_api_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != USER_APPROVED_OUTPUT_QUEUE_STAGE:
            raise ValueError("RQF-027R approval items must identify the RQF-027R stage.")
        if self.status != APPROVAL_STATUS_PENDING:
            raise ValueError("RQF-027R approval items must remain pending.")
        if not self.local_only or not self.requires_user_approval:
            raise ValueError("RQF-027R approval items must be local and require approval.")
        if any(
            (
                self.email_sent,
                self.gmail_draft_created,
                self.calendar_event_created,
                self.external_action_performed,
                self.external_api_write_allowed,
            )
        ):
            raise ValueError("RQF-027R approval items must not expand authority.")


@dataclass(frozen=True, slots=True)
class UserApprovedOutputQueue:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    items: tuple[UserApprovedOutputItem, ...]
    local_queue_created: bool
    no_external_action_taken: bool
    email_send_allowed: bool
    gmail_draft_creation_allowed: bool
    calendar_write_allowed: bool
    external_api_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != USER_APPROVED_OUTPUT_QUEUE_STAGE:
            raise ValueError("RQF-027R approval queues must identify the RQF-027R stage.")
        if self.status not in {"empty", "pending_approvals"}:
            raise ValueError("RQF-027R approval queues require a supported status.")
        if bool(self.items) != (self.status == "pending_approvals"):
            raise ValueError("RQF-027R approval queue status must match item count.")
        if not self.local_queue_created or not self.no_external_action_taken:
            raise ValueError("RQF-027R approval queues require local queue creation and no external action.")
        if any(
            (
                self.email_send_allowed,
                self.gmail_draft_creation_allowed,
                self.calendar_write_allowed,
                self.external_api_write_allowed,
            )
        ):
            raise ValueError("RQF-027R approval queues must not expand authority.")


@dataclass(frozen=True, slots=True)
class UserApprovedOutputDecisionReceipt:
    stage: str
    owner_id: str
    robot_id: str
    approval_id: str
    decision_id: str
    decision: str
    status: str
    output_title: str
    owner_requested: bool
    local_receipt_recorded: bool
    queue_state_updated_locally: bool
    email_sent: bool
    gmail_draft_created: bool
    calendar_event_created: bool
    external_action_performed: bool
    external_api_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != USER_APPROVED_OUTPUT_QUEUE_STAGE:
            raise ValueError("RQF-027R approval decisions must identify the RQF-027R stage.")
        if self.decision not in SUPPORTED_APPROVAL_DECISIONS:
            raise ValueError("RQF-027R approval decisions require a supported decision.")
        if self.status not in {
            APPROVAL_DECISION_APPROVED,
            APPROVAL_DECISION_REJECTED,
            APPROVAL_DECISION_MISSING_ID,
            APPROVAL_DECISION_NOT_FOUND,
        }:
            raise ValueError("RQF-027R approval decision status must be supported.")
        if not self.owner_requested or not self.local_receipt_recorded:
            raise ValueError("RQF-027R approval decisions require owner request and local receipt.")
        if any(
            (
                self.email_sent,
                self.gmail_draft_created,
                self.calendar_event_created,
                self.external_action_performed,
                self.external_api_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("RQF-027R approval decisions must not expand authority.")


def build_user_approved_output_queue(
    *,
    owner_id: str,
    robot_id: str,
    items: tuple[UserApprovedOutputItem, ...] = (),
) -> UserApprovedOutputQueue:
    for item in items:
        if item.owner_id != owner_id or item.robot_id != robot_id:
            raise ValueError("rejected_approval_queue_owner_robot_mismatch")
    return UserApprovedOutputQueue(
        stage=USER_APPROVED_OUTPUT_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="pending_approvals" if items else "empty",
        items=items,
        local_queue_created=True,
        no_external_action_taken=True,
        email_send_allowed=False,
        gmail_draft_creation_allowed=False,
        calendar_write_allowed=False,
        external_api_write_allowed=False,
    )


def build_user_approved_output_item(
    *,
    owner_id: str,
    robot_id: str,
    output_type: str,
    title: str,
    body_preview: str,
    source: str = "local_fixture",
    approval_id: str | None = None,
) -> UserApprovedOutputItem:
    normalized_title = " ".join(title.split()) or "Untitled approval output"
    normalized_preview = " ".join(body_preview.split()) or "No local preview is available."
    normalized_type = " ".join(output_type.split()) or "local_output"
    normalized_source = " ".join(source.split()) or "local_fixture"
    return UserApprovedOutputItem(
        stage=USER_APPROVED_OUTPUT_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        approval_id=approval_id
        or _stable_id("approval-item", owner_id, robot_id, normalized_type, normalized_title, normalized_source),
        output_type=normalized_type,
        title=normalized_title,
        body_preview=normalized_preview,
        status=APPROVAL_STATUS_PENDING,
        source=normalized_source,
        local_only=True,
        requires_user_approval=True,
        email_sent=False,
        gmail_draft_created=False,
        calendar_event_created=False,
        external_action_performed=False,
        external_api_write_allowed=False,
    )


def build_user_approved_output_decision_receipt(
    *,
    owner_id: str,
    robot_id: str,
    approval_id: str,
    decision: str,
    queue: UserApprovedOutputQueue,
) -> UserApprovedOutputDecisionReceipt:
    normalized_approval_id = approval_id.strip()
    normalized_decision = decision.strip().lower()
    if normalized_decision not in SUPPORTED_APPROVAL_DECISIONS:
        raise ValueError("rejected_invalid_user_approved_output_decision")
    if queue.owner_id != owner_id or queue.robot_id != robot_id:
        raise ValueError("rejected_approval_decision_queue_owner_robot_mismatch")
    if not normalized_approval_id:
        return _decision_receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            approval_id="",
            decision=normalized_decision,
            status=APPROVAL_DECISION_MISSING_ID,
            item=None,
        )
    item = next((candidate for candidate in queue.items if candidate.approval_id == normalized_approval_id), None)
    if item is None:
        return _decision_receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            approval_id=normalized_approval_id,
            decision=normalized_decision,
            status=APPROVAL_DECISION_NOT_FOUND,
            item=None,
        )
    status = APPROVAL_DECISION_APPROVED if normalized_decision == "approve" else APPROVAL_DECISION_REJECTED
    return _decision_receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        approval_id=normalized_approval_id,
        decision=normalized_decision,
        status=status,
        item=item,
    )


def render_user_approved_output_queue(queue: UserApprovedOutputQueue) -> str:
    lines = [
        "Approvals",
        "",
        f"Stage: {queue.stage}",
        f"Status: {queue.status}",
        f"Pending approvals: {len(queue.items)}",
        "Local queue: true",
        "",
        "Items:",
    ]
    if queue.items:
        for item in queue.items:
            lines.extend(
                [
                    f"- {item.approval_id} | {item.output_type} | {item.status}",
                    f"  Title: {item.title}",
                    f"  Preview: {item.body_preview}",
                    f"  Source: {item.source}",
                ]
            )
    else:
        lines.append("- No pending approvals.")
        lines.append("- Use /suggestions, /drafts, or /prep to create reviewable work first.")
    lines.extend(_boundary_lines())
    return "\n".join(lines)


def render_user_approved_output_decision_receipt(record: UserApprovedOutputDecisionReceipt) -> str:
    lines = [
        "Approval Receipt",
        "",
        f"Stage: {record.stage}",
        f"Decision id: {record.decision_id}",
        f"Approval id: {record.approval_id or 'none'}",
        f"Decision: {record.decision}",
        f"Status: {record.status}",
        f"Output: {record.output_title or 'not available'}",
        "Owner requested: true",
        "Receipt recorded: true",
        "",
        *_decision_meaning_lines(record),
        "",
        "Approved locally." if record.status == APPROVAL_DECISION_APPROVED else "Decision recorded locally.",
        "No email sent.",
        "No Gmail draft created.",
        "No calendar event created.",
        "No external action performed.",
        "Receipt recorded.",
        "",
        "Authority:",
        "Email send: disabled",
        "Gmail draft creation: disabled",
        "Calendar writes: disabled",
        "External API writes: disabled",
        "Model calls: disabled",
        "Tools/workers: disabled",
    ]
    return "\n".join(lines)


def _decision_receipt(
    *,
    owner_id: str,
    robot_id: str,
    approval_id: str,
    decision: str,
    status: str,
    item: UserApprovedOutputItem | None,
) -> UserApprovedOutputDecisionReceipt:
    return UserApprovedOutputDecisionReceipt(
        stage=USER_APPROVED_OUTPUT_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        approval_id=approval_id,
        decision_id=_stable_id("approval-decision", owner_id, robot_id, approval_id, decision, status),
        decision=decision,
        status=status,
        output_title="" if item is None else item.title,
        owner_requested=True,
        local_receipt_recorded=True,
        queue_state_updated_locally=status in {APPROVAL_DECISION_APPROVED, APPROVAL_DECISION_REJECTED},
        email_sent=False,
        gmail_draft_created=False,
        calendar_event_created=False,
        external_action_performed=False,
        external_api_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def _decision_meaning_lines(record: UserApprovedOutputDecisionReceipt) -> tuple[str, ...]:
    if record.status == APPROVAL_DECISION_APPROVED:
        return (
            "Meaning:",
            "- Your approval was recorded locally.",
            "- Approval does not execute the output.",
        )
    if record.status == APPROVAL_DECISION_REJECTED:
        return (
            "Meaning:",
            "- Your rejection was recorded locally.",
            "- No output was changed or executed.",
        )
    if record.status == APPROVAL_DECISION_MISSING_ID:
        return (
            "Meaning:",
            "- No approval id was provided.",
            "- Use /approvals to review pending local approvals first.",
        )
    return (
        "Meaning:",
        "- That approval is not available in the current local queue.",
        "- No approval decision was applied.",
    )


def _boundary_lines() -> list[str]:
    return [
        "",
        "Meaning:",
        "- These are local review candidates only.",
        "- Approve means record local approval; it does not execute.",
        "",
        "Authority:",
        "Email send: disabled",
        "Gmail draft creation: disabled",
        "Calendar writes: disabled",
        "External API writes: disabled",
        "External actions: disabled",
        "",
        "No external action was taken.",
    ]


def _stable_id(kind: str, *parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, ":".join(("roboticxs", kind, *parts))))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.user_approved_output_queue")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    queue = build_user_approved_output_queue(owner_id=args.owner_id, robot_id=args.robot_id)
    if args.as_json:
        print(json.dumps(asdict(queue), sort_keys=True, indent=2))
    else:
        print(render_user_approved_output_queue(queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
