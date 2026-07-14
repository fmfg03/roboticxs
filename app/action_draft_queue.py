from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.draft_quality_engine import build_draft_quality_review, render_draft_quality_review
from app.suggestion_decision_flow import (
    DECISION_STATUS_RECORDED,
    SUGGESTION_DECISION_FLOW_STAGE,
    SuggestionDecisionReceipt,
)


ACTION_DRAFT_QUEUE_STAGE = "177P"
ACTION_DRAFT_STATUS_PENDING = "pending_user_confirmation"
SUPPORTED_ACTION_DRAFT_TYPES = frozenset({"email_reply", "follow_up", "meeting_note", "task_note"})


@dataclass(frozen=True, slots=True)
class ActionDraftRecord:
    stage: str
    owner_id: str
    robot_id: str
    draft_id: str
    draft_type: str
    title: str
    body_preview: str
    status: str
    source_stage: str
    source_decision_id: str
    source_suggestion_id: str
    source_suggestion_title: str
    local_draft_record_created: bool
    requires_user_confirmation: bool
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
        if self.stage != ACTION_DRAFT_QUEUE_STAGE:
            raise ValueError("177P action drafts must identify the 177P stage.")
        if self.draft_type not in SUPPORTED_ACTION_DRAFT_TYPES:
            raise ValueError("177P action drafts require a supported draft type.")
        if self.status != ACTION_DRAFT_STATUS_PENDING:
            raise ValueError("177P action drafts must remain pending user confirmation.")
        if self.source_stage != SUGGESTION_DECISION_FLOW_STAGE:
            raise ValueError("177P action drafts must originate from 172P suggestion decision receipts.")
        if not self.local_draft_record_created or not self.requires_user_confirmation:
            raise ValueError("177P action drafts require local record creation and user confirmation.")
        if any(
            (
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
            raise ValueError("177P action drafts must not expand authority.")


@dataclass(frozen=True, slots=True)
class ActionDraftQueue:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    drafts: tuple[ActionDraftRecord, ...]
    skipped_decision_ids: tuple[str, ...]
    local_queue_created: bool
    no_external_action_taken: bool
    gmail_draft_creation_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    task_persistence_allowed: bool
    memory_center_mutation_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != ACTION_DRAFT_QUEUE_STAGE:
            raise ValueError("177P action draft queues must identify the 177P stage.")
        if self.status not in {"empty", "pending_drafts"}:
            raise ValueError("177P action draft queues require a supported status.")
        if bool(self.drafts) != (self.status == "pending_drafts"):
            raise ValueError("177P action draft queue status must match draft count.")
        if not self.local_queue_created or not self.no_external_action_taken:
            raise ValueError("177P action draft queues require local queue creation and no external action.")
        if any(
            (
                self.gmail_draft_creation_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.task_persistence_allowed,
                self.memory_center_mutation_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("177P action draft queues must not expand authority.")


def build_action_draft_queue(
    *,
    owner_id: str,
    robot_id: str,
    decisions: tuple[SuggestionDecisionReceipt, ...] = (),
) -> ActionDraftQueue:
    drafts: list[ActionDraftRecord] = []
    skipped: list[str] = []
    for decision in decisions:
        if decision.owner_id != owner_id or decision.robot_id != robot_id:
            raise ValueError("rejected_action_draft_queue_owner_robot_mismatch")
        if decision.choice != "create_draft" or decision.decision_status != DECISION_STATUS_RECORDED:
            skipped.append(decision.decision_id)
            continue
        drafts.append(_draft_from_decision(owner_id=owner_id, robot_id=robot_id, decision=decision))
    return ActionDraftQueue(
        stage=ACTION_DRAFT_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="pending_drafts" if drafts else "empty",
        drafts=tuple(drafts),
        skipped_decision_ids=tuple(skipped),
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


def render_action_draft_queue(queue: ActionDraftQueue) -> str:
    lines = [
        "Action Draft Queue",
        "",
        f"Stage: {queue.stage}",
        f"Status: {queue.status}",
        f"Pending drafts: {len(queue.drafts)}",
        f"Skipped decisions: {len(queue.skipped_decision_ids)}",
        "Local queue created: true",
        "",
        "Drafts:",
    ]
    if queue.drafts:
        for draft in queue.drafts:
            lines.extend(
                [
                    f"- {draft.draft_id} | {draft.draft_type} | {draft.status}",
                    f"  Title: {draft.title}",
                    f"  Source suggestion: {draft.source_suggestion_id}",
                    f"  Preview: {draft.body_preview}",
                    *render_draft_quality_review(build_draft_quality_review(draft)),
                ]
            )
    else:
        lines.append("- No pending local drafts.")
    lines.extend(
        [
            "",
            "Meaning:",
            "- Drafts in this queue are local approval candidates.",
            "- They are not Gmail drafts, sent emails, scheduled events, or persisted tasks.",
            "",
            "Boundaries:",
            "Local draft records: enabled",
            "User confirmation required: true",
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


def _draft_from_decision(*, owner_id: str, robot_id: str, decision: SuggestionDecisionReceipt) -> ActionDraftRecord:
    title = f"Draft for: {decision.suggestion_title}"
    return ActionDraftRecord(
        stage=ACTION_DRAFT_QUEUE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        draft_id=_stable_draft_id(owner_id, robot_id, decision.decision_id),
        draft_type="follow_up",
        title=title,
        body_preview="Local draft placeholder from approved draft intent; final content requires confirmation runtime.",
        status=ACTION_DRAFT_STATUS_PENDING,
        source_stage=decision.stage,
        source_decision_id=decision.decision_id,
        source_suggestion_id=decision.suggestion_id,
        source_suggestion_title=decision.suggestion_title,
        local_draft_record_created=True,
        requires_user_confirmation=True,
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


def _stable_draft_id(owner_id: str, robot_id: str, decision_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"roboticxs:action-draft:{owner_id}:{robot_id}:{decision_id}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.action_draft_queue")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    queue = build_action_draft_queue(owner_id=args.owner_id, robot_id=args.robot_id)
    if args.as_json:
        print(json.dumps(asdict(queue), sort_keys=True, indent=2))
    else:
        print(render_action_draft_queue(queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
