from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.personal_admin_inbox import PERSONAL_ADMIN_INBOX_STAGE


INBOX_ITEM_DECISION_STAGE = "147P"
INBOX_DECISION_CHOICES = frozenset({"done", "dismiss"})
DECISION_STATUS_BY_CHOICE = {
    "done": "marked_done_local_receipt",
    "dismiss": "dismissed_local_receipt",
}


@dataclass(frozen=True, slots=True)
class InboxItemDecisionRecord:
    stage: str
    owner_id: str
    robot_id: str
    item_id: str
    source_stage: str
    decision_id: str
    choice: str
    decision_status: str
    local_audit_created: bool
    owner_requested: bool
    evidence_deleted: bool
    persisted_state_written: bool
    memory_center_mutated: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != INBOX_ITEM_DECISION_STAGE:
            raise ValueError("147P inbox decisions must identify the 147P stage.")
        if self.source_stage != PERSONAL_ADMIN_INBOX_STAGE:
            raise ValueError("147P inbox decisions must originate from 146P inbox items.")
        if self.choice not in INBOX_DECISION_CHOICES:
            raise ValueError("147P inbox decisions require done or dismiss.")
        if self.decision_status != DECISION_STATUS_BY_CHOICE[self.choice]:
            raise ValueError("147P inbox decision status must match the owner choice.")
        if not self.local_audit_created or not self.owner_requested:
            raise ValueError("147P inbox decisions require explicit owner request and local audit.")
        if any(
            (
                self.evidence_deleted,
                self.persisted_state_written,
                self.memory_center_mutated,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("147P inbox decisions must not expand authority.")


def build_inbox_item_decision(
    *,
    owner_id: str,
    robot_id: str,
    item_id: str,
    choice: str,
) -> InboxItemDecisionRecord:
    normalized_item_id = item_id.strip()
    normalized_choice = choice.strip().lower()
    if not normalized_item_id:
        raise ValueError("rejected_missing_inbox_item_id")
    if normalized_choice not in INBOX_DECISION_CHOICES:
        raise ValueError("rejected_invalid_inbox_decision_choice")
    return InboxItemDecisionRecord(
        stage=INBOX_ITEM_DECISION_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        item_id=normalized_item_id,
        source_stage=PERSONAL_ADMIN_INBOX_STAGE,
        decision_id=_stable_decision_id(owner_id, robot_id, normalized_item_id, normalized_choice),
        choice=normalized_choice,
        decision_status=DECISION_STATUS_BY_CHOICE[normalized_choice],
        local_audit_created=True,
        owner_requested=True,
        evidence_deleted=False,
        persisted_state_written=False,
        memory_center_mutated=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_inbox_item_decision(record: InboxItemDecisionRecord) -> str:
    return "\n".join(
        [
            "Inbox Item Decision",
            "",
            f"Stage: {record.stage}",
            f"Decision id: {record.decision_id}",
            f"Item id: {record.item_id}",
            f"Choice: {record.choice}",
            f"Decision status: {record.decision_status}",
            f"Source stage: {record.source_stage}",
            "Owner requested: true",
            "Local audit created: true",
            "Evidence deleted: false",
            "Persisted state written: false",
            "Memory Center mutation: disabled",
            "Calendar writes: disabled",
            "LLM/model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No inbox evidence was deleted.",
        ]
    )


def _stable_decision_id(owner_id: str, robot_id: str, item_id: str, choice: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"roboticxs:inbox-item-decision:{owner_id}:{robot_id}:{item_id}:{choice}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.inbox_item_decision")
    parser.add_argument("choice", choices=sorted(INBOX_DECISION_CHOICES))
    parser.add_argument("item_id")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = build_inbox_item_decision(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        item_id=args.item_id,
        choice=args.choice,
    )
    print(render_inbox_item_decision(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
