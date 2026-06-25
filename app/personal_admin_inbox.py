from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.google_calendar_readonly_connector import GoogleCalendarHttpClientProtocol
from app.open_loops_command import OpenLoopsCommandRecord, run_open_loops_command
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


PERSONAL_ADMIN_INBOX_STAGE = "146P"


@dataclass(frozen=True, slots=True)
class PersonalAdminInboxRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    source_stages: tuple[str, ...]
    inbox_items: tuple[str, ...]
    next_steps: tuple[str, ...]
    read_only: bool
    item_resolution_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != PERSONAL_ADMIN_INBOX_STAGE:
            raise ValueError("146P inbox records must identify the 146P stage.")
        if not self.read_only:
            raise ValueError("146P inbox records must be read-only.")
        if any(
            (
                self.item_resolution_allowed,
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("146P inbox records must not expand authority.")


def build_personal_admin_inbox_record(
    *,
    owner_id: str,
    robot_id: str,
    open_loops_record: OpenLoopsCommandRecord,
) -> PersonalAdminInboxRecord:
    if open_loops_record.owner_id != owner_id or open_loops_record.robot_id != robot_id:
        raise ValueError("rejected_inbox_open_loops_owner_robot_mismatch")
    items = _items_from_open_loops(open_loops_record)
    return PersonalAdminInboxRecord(
        stage=PERSONAL_ADMIN_INBOX_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="completed_with_items" if items else "empty",
        source_stages=("142P", "144P", "145P"),
        inbox_items=items or ("No personal admin inbox items are visible right now.",),
        next_steps=(
            "Use /loops for the underlying open-loop details.",
            "Use /memory_approve or /memory_reject for brief-derived memory candidates.",
            "146P does not resolve, dismiss, write, or execute inbox items.",
        ),
        read_only=True,
        item_resolution_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def run_personal_admin_inbox(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> PersonalAdminInboxRecord:
    open_loops_record = run_open_loops_command(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_http_client=calendar_http_client,
        memory_source_bundle=memory_source_bundle,
    )
    return build_personal_admin_inbox_record(
        owner_id=owner_id,
        robot_id=robot_id,
        open_loops_record=open_loops_record,
    )


def render_personal_admin_inbox(record: PersonalAdminInboxRecord) -> str:
    has_items = record.status != "empty"
    return "\n".join(
        [
            "Task Inbox",
            "",
            f"Status: {record.status}",
            "Read-only: true",
            "",
            "Inbox type:",
            "- Robot task inbox, not Gmail.",
            "",
            "States:",
            "- pending: waiting in the local task inbox",
            "- needs approval: owner approval is required before memory or external action",
            "- blocked: source or setup is unavailable",
            "- done: local receipt only after /inbox_done <item_id>",
            "- dismissed: local receipt only after /inbox_dismiss <item_id>",
            "",
            "Items:",
            *(_render_inbox_item_lines(record.inbox_items) if has_items else ("- Empty: no robot task inbox items are visible right now.",)),
            "",
            "Suggested next action:",
            *(f"- {step}" for step in _product_next_steps(record)),
            "",
            "Boundaries:",
            "Memory writes: disabled",
            "Memory Center mutation: disabled",
            "Calendar writes: disabled",
            "Gmail inbox: unavailable",
            "Gmail writes: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "Underlying sources:",
            f"- {', '.join(record.source_stages)}",
            "",
            "Legacy next steps:",
            *(f"- {step}" for step in record.next_steps),
            "",
            "No inbox item was resolved or dismissed.",
        ]
    )


def _render_inbox_item_lines(items: tuple[str, ...]) -> tuple[str, ...]:
    rendered: list[str] = []
    for item in items:
        if item.startswith("pending-memory:"):
            rendered.append(f"- needs approval | {item}")
        elif item.startswith("meeting-suggestion:"):
            rendered.append(f"- pending | {item}")
        else:
            rendered.append(f"- blocked | {item}")
    return tuple(rendered)


def _product_next_steps(record: PersonalAdminInboxRecord) -> tuple[str, ...]:
    if record.status == "empty":
        return ("Use /today to see the current daily view.",)
    return (
        "Use /inbox_done <item_id> for a local done receipt.",
        "Use /inbox_dismiss <item_id> for a local dismissed receipt.",
        "Use /memory_approve or /memory_reject for memory proposals.",
    )


def _items_from_open_loops(record: OpenLoopsCommandRecord) -> tuple[str, ...]:
    items: list[str] = []
    for line in record.pending_memory_lines:
        if "No pending memory proposals" not in line:
            items.append(f"pending-memory: {line}")
    for line in record.meeting_suggestion_lines:
        if "No owner-requestable" not in line and "Calendar failed closed" not in line:
            items.append(f"meeting-suggestion: {line}")
    return tuple(items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.personal_admin_inbox")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    args = parser.parse_args(argv)
    record = run_personal_admin_inbox(owner_id=args.owner_id, robot_id=args.robot_id)
    print(render_personal_admin_inbox(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
