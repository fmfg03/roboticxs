from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.proactive_suggestion_loop import ProactiveSuggestionLoopRecord


SUGGESTION_INBOX_STAGE = "171P"
SUGGESTION_INBOX_STATUS_PENDING = "pending"


@dataclass(frozen=True, slots=True)
class SuggestionInboxItem:
    stage: str
    owner_id: str
    robot_id: str
    suggestion_id: str
    status: str
    trigger_type: str
    title: str
    summary: str
    suggested_next_step: str
    source_refs: tuple[str, ...]
    no_action_taken: bool
    live_send_allowed: bool
    callback_binding_allowed: bool
    execution_allowed: bool
    memory_write_allowed: bool
    draft_creation_allowed: bool
    external_write_allowed: bool
    connector_activation_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SUGGESTION_INBOX_STAGE:
            raise ValueError("171P suggestion inbox items must identify the 171P stage.")
        if self.status != SUGGESTION_INBOX_STATUS_PENDING:
            raise ValueError("171P suggestion inbox only supports pending suggestions.")
        if not self.no_action_taken:
            raise ValueError("171P suggestion inbox items must declare that no action was taken.")
        if any(
            (
                self.live_send_allowed,
                self.callback_binding_allowed,
                self.execution_allowed,
                self.memory_write_allowed,
                self.draft_creation_allowed,
                self.external_write_allowed,
                self.connector_activation_allowed,
            )
        ):
            raise ValueError("171P suggestion inbox must not expand authority.")


@dataclass(frozen=True, slots=True)
class SuggestionInbox:
    stage: str
    owner_id: str
    robot_id: str
    items: tuple[SuggestionInboxItem, ...]
    local_read_only: bool
    no_action_taken: bool
    decision_flow_allowed: bool
    draft_creation_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SUGGESTION_INBOX_STAGE:
            raise ValueError("171P suggestion inbox must identify the 171P stage.")
        if not self.local_read_only:
            raise ValueError("171P suggestion inbox must remain local read-only.")
        if not self.no_action_taken:
            raise ValueError("171P suggestion inbox must declare that no action was taken.")
        if any(
            (
                self.decision_flow_allowed,
                self.draft_creation_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("171P suggestion inbox must not authorize decisions, drafts, memory writes, or external writes.")


def build_suggestion_inbox(
    *,
    owner_id: str,
    robot_id: str,
    suggestions: tuple[ProactiveSuggestionLoopRecord, ...],
) -> SuggestionInbox:
    items = tuple(
        _item_from_suggestion(suggestion)
        for suggestion in suggestions
        if suggestion.owner_id == owner_id and suggestion.robot_id == robot_id
    )
    return SuggestionInbox(
        stage=SUGGESTION_INBOX_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        items=items,
        local_read_only=True,
        no_action_taken=True,
        decision_flow_allowed=False,
        draft_creation_allowed=False,
        memory_write_allowed=False,
        external_write_allowed=False,
    )


def render_suggestion_inbox(inbox: SuggestionInbox) -> str:
    lines = [
        "Suggestion Inbox",
        "",
        f"Stage: {inbox.stage}",
        f"Robot: {inbox.robot_id}",
        f"Status: {len(inbox.items)} pending suggestion(s)",
        "",
    ]
    if not inbox.items:
        lines.extend(
            [
                "Pending suggestions:",
                "- No pending suggestions in the local inbox.",
            ]
        )
    else:
        lines.append("Pending suggestions:")
        for item in inbox.items:
            lines.extend(
                [
                    f"- {item.title}",
                    f"  id: {item.suggestion_id}",
                    f"  trigger: {item.trigger_type}",
                    f"  status: {item.status}",
                    f"  summary: {item.summary}",
                    f"  suggested next step: {item.suggested_next_step}",
                    f"  sources: {_render_source_refs(item.source_refs)}",
                ]
            )
    lines.extend(
        [
            "",
            "No action has been taken.",
            "Decision flow: disabled",
            "Draft creation: disabled",
            "Memory writes: disabled",
            "Live send: disabled",
            "Callbacks: disabled",
            "Execution: disabled",
            "Connector activation: disabled",
            "External writes: disabled",
        ]
    )
    return "\n".join(lines)


def _item_from_suggestion(suggestion: ProactiveSuggestionLoopRecord) -> SuggestionInboxItem:
    if any(
        (
            suggestion.live_send_allowed,
            suggestion.callback_binding_allowed,
            suggestion.execution_allowed,
            suggestion.connector_activation_allowed,
            suggestion.memory_write_allowed,
            suggestion.external_write_allowed,
            suggestion.worker_dispatch_allowed,
        )
    ):
        raise ValueError("171P suggestion inbox accepts non-authority 170P suggestions only.")
    return SuggestionInboxItem(
        stage=SUGGESTION_INBOX_STAGE,
        owner_id=suggestion.owner_id,
        robot_id=suggestion.robot_id,
        suggestion_id=suggestion.suggestion_id,
        status=SUGGESTION_INBOX_STATUS_PENDING,
        trigger_type=suggestion.trigger_type,
        title=suggestion.title,
        summary=suggestion.suggestion_text,
        suggested_next_step=suggestion.suggested_next_step,
        source_refs=suggestion.source_refs,
        no_action_taken=True,
        live_send_allowed=False,
        callback_binding_allowed=False,
        execution_allowed=False,
        memory_write_allowed=False,
        draft_creation_allowed=False,
        external_write_allowed=False,
        connector_activation_allowed=False,
    )


def _render_source_refs(source_refs: tuple[str, ...]) -> str:
    if not source_refs:
        return "none"
    return ", ".join(source_refs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.suggestion_inbox")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    inbox = build_suggestion_inbox(owner_id="local-owner", robot_id="roboticxs-dev", suggestions=())
    if args.as_json:
        print(json.dumps(asdict(inbox), sort_keys=True, indent=2))
    else:
        print(render_suggestion_inbox(inbox))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
