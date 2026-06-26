from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5

from app.suggestion_inbox import SUGGESTION_INBOX_STAGE, SuggestionInbox, SuggestionInboxItem


SUGGESTION_DECISION_FLOW_STAGE = "172P"
SUGGESTION_DECISION_CHOICES = frozenset(
    {"dismiss", "snooze", "save_memory", "create_draft", "ask_followup"}
)
DECISION_STATUS_RECORDED = "recorded_local_receipt"
DECISION_STATUS_MISSING_SUGGESTION_ID = "blocked_missing_suggestion_id"
DECISION_STATUS_SUGGESTION_NOT_FOUND = "blocked_suggestion_not_found"


@dataclass(frozen=True, slots=True)
class SuggestionDecisionReceipt:
    stage: str
    owner_id: str
    robot_id: str
    suggestion_id: str
    source_stage: str
    decision_id: str
    choice: str
    decision_status: str
    suggestion_title: str
    local_receipt_created: bool
    owner_requested: bool
    no_action_taken: bool
    draft_created: bool
    memory_written: bool
    snooze_scheduled: bool
    followup_question_sent: bool
    callback_bound: bool
    live_send_allowed: bool
    execution_allowed: bool
    connector_activation_allowed: bool
    model_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SUGGESTION_DECISION_FLOW_STAGE:
            raise ValueError("172P suggestion decisions must identify the 172P stage.")
        if self.source_stage != SUGGESTION_INBOX_STAGE:
            raise ValueError("172P suggestion decisions must originate from 171P suggestion inbox.")
        if self.choice not in SUGGESTION_DECISION_CHOICES:
            raise ValueError("172P suggestion decisions require a supported choice.")
        if self.decision_status not in {
            DECISION_STATUS_RECORDED,
            DECISION_STATUS_MISSING_SUGGESTION_ID,
            DECISION_STATUS_SUGGESTION_NOT_FOUND,
        }:
            raise ValueError("172P suggestion decision status must be supported.")
        if not self.local_receipt_created or not self.owner_requested or not self.no_action_taken:
            raise ValueError("172P suggestion decisions require owner request, local receipt, and no action taken.")
        if any(
            (
                self.draft_created,
                self.memory_written,
                self.snooze_scheduled,
                self.followup_question_sent,
                self.callback_bound,
                self.live_send_allowed,
                self.execution_allowed,
                self.connector_activation_allowed,
                self.model_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("172P suggestion decisions must not expand authority.")


def build_suggestion_decision_receipt(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    choice: str,
    inbox: SuggestionInbox,
) -> SuggestionDecisionReceipt:
    normalized_suggestion_id = suggestion_id.strip()
    normalized_choice = choice.strip().lower()
    if normalized_choice not in SUGGESTION_DECISION_CHOICES:
        raise ValueError("rejected_invalid_suggestion_decision_choice")
    if inbox.owner_id != owner_id or inbox.robot_id != robot_id:
        raise ValueError("rejected_suggestion_inbox_owner_robot_mismatch")
    if not normalized_suggestion_id:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id="",
            choice=normalized_choice,
            decision_status=DECISION_STATUS_MISSING_SUGGESTION_ID,
            suggestion=None,
        )
    suggestion = next(
        (item for item in inbox.items if item.suggestion_id == normalized_suggestion_id),
        None,
    )
    if suggestion is None:
        return _receipt(
            owner_id=owner_id,
            robot_id=robot_id,
            suggestion_id=normalized_suggestion_id,
            choice=normalized_choice,
            decision_status=DECISION_STATUS_SUGGESTION_NOT_FOUND,
            suggestion=None,
        )
    return _receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=normalized_suggestion_id,
        choice=normalized_choice,
        decision_status=DECISION_STATUS_RECORDED,
        suggestion=suggestion,
    )


def render_suggestion_decision_receipt(record: SuggestionDecisionReceipt) -> str:
    lines = [
        "Suggestion Decision",
        "",
        f"Stage: {record.stage}",
        f"Decision id: {record.decision_id}",
        f"Suggestion id: {record.suggestion_id or 'none'}",
        f"Choice: {record.choice}",
        f"Status: {record.decision_status}",
        f"Suggestion: {record.suggestion_title or 'not available'}",
        "Owner requested: true",
        "Local receipt created: true",
        "",
    ]
    if record.decision_status == DECISION_STATUS_RECORDED:
        lines.extend(
            [
                "Meaning:",
                "- Your decision intent was recorded locally.",
                "- Nothing has been executed.",
            ]
        )
    elif record.decision_status == DECISION_STATUS_MISSING_SUGGESTION_ID:
        lines.extend(
            [
                "Meaning:",
                "- No suggestion id was provided.",
                "- Use /suggestions to review pending local suggestions first.",
            ]
        )
    else:
        lines.extend(
            [
                "Meaning:",
                "- That suggestion is not available in the current local inbox.",
                "- No decision was applied to a suggestion.",
            ]
        )
    lines.extend(
        [
            "",
            "No action has been taken.",
            "Draft created: false",
            "Memory written: false",
            "Snooze scheduled: false",
            "Follow-up question sent: false",
            "Callbacks: disabled",
            "Live send: disabled",
            "Execution: disabled",
            "Connector activation: disabled",
            "Model calls: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
        ]
    )
    return "\n".join(lines)


def _receipt(
    *,
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    choice: str,
    decision_status: str,
    suggestion: SuggestionInboxItem | None,
) -> SuggestionDecisionReceipt:
    suggestion_title = "" if suggestion is None else suggestion.title
    return SuggestionDecisionReceipt(
        stage=SUGGESTION_DECISION_FLOW_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        source_stage=SUGGESTION_INBOX_STAGE,
        decision_id=_stable_decision_id(owner_id, robot_id, suggestion_id, choice, decision_status),
        choice=choice,
        decision_status=decision_status,
        suggestion_title=suggestion_title,
        local_receipt_created=True,
        owner_requested=True,
        no_action_taken=True,
        draft_created=False,
        memory_written=False,
        snooze_scheduled=False,
        followup_question_sent=False,
        callback_bound=False,
        live_send_allowed=False,
        execution_allowed=False,
        connector_activation_allowed=False,
        model_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _stable_decision_id(
    owner_id: str,
    robot_id: str,
    suggestion_id: str,
    choice: str,
    decision_status: str,
) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"roboticxs:suggestion-decision:{owner_id}:{robot_id}:{suggestion_id}:{choice}:{decision_status}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.suggestion_decision_flow")
    parser.add_argument("choice", choices=sorted(SUGGESTION_DECISION_CHOICES))
    parser.add_argument("suggestion_id", nargs="?", default="")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    inbox = SuggestionInbox(
        stage=SUGGESTION_INBOX_STAGE,
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        items=(),
        local_read_only=True,
        no_action_taken=True,
        decision_flow_allowed=False,
        draft_creation_allowed=False,
        memory_write_allowed=False,
        external_write_allowed=False,
    )
    record = build_suggestion_decision_receipt(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        suggestion_id=args.suggestion_id,
        choice=args.choice,
        inbox=inbox,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_suggestion_decision_receipt(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
