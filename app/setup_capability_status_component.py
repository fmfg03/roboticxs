from __future__ import annotations


SETUP_CAPABILITY_STATUS_COMPONENT_STAGE = "161P"

PRODUCT_APPROVAL_BOUNDARY_LINES = (
    "- I do not write Calendar or Gmail.",
    "- I do not remember new facts without approval.",
    "- I do not take external actions without approval.",
    "- Documents are metadata-only and draft-only right now.",
)

SETUP_ACTIVE_LINES = (
    "- Today and missed-item summaries",
    "- Meeting briefs and prep packs",
    "- Robot task inbox",
    "- Memory visibility and approval receipts",
    "- Draft-only document intake metadata",
)

SETUP_NEEDS_SETUP_LINES = (
    "- Calendar reads require read-only Google setup.",
    "- Calendar meeting suggestions need read-only Calendar setup.",
    "- Memory review uses local pending proposals only until writeback is approved.",
)

SETUP_UNAVAILABLE_LINES = (
    "- Gmail is not an inbox yet.",
    "- Document review remains draft-only; file contents are not downloaded or parsed.",
    "- Calendar and Gmail writes are not product capabilities.",
)

SETUP_INTENTIONALLY_DISABLED_LINES = (
    "- Calendar writes: disabled",
    "- Gmail writes: disabled",
    "- Model calls: disabled",
    "- Tool execution: disabled",
    "- Workers: disabled",
    "- Scheduler/proactive outbound: disabled",
    "- Automatic Memory Center mutation: disabled",
)

SETUP_COMPACT_LINES = (
    "- Calendar: not connected; read-only setup required.",
    "- Gmail: not connected to the robot task inbox.",
    "- Memory: approval mode active.",
    "- Documents: draft-only metadata intake.",
    "- External writes: disabled.",
)

TASK_INBOX_BOUNDARY_LINE = "- Task Inbox is your robot task inbox, not your Gmail inbox yet."


def render_setup_capability_status_sections(*, include_suggested_next_action: bool = True) -> tuple[str, ...]:
    lines: list[str] = [
        "Active now:",
        *SETUP_ACTIVE_LINES,
        "",
        "Needs setup:",
        *SETUP_NEEDS_SETUP_LINES,
        "",
        "Unavailable:",
        *SETUP_UNAVAILABLE_LINES,
        "",
        "Intentionally disabled:",
        *SETUP_INTENTIONALLY_DISABLED_LINES,
        "",
        "Approval boundaries:",
        *PRODUCT_APPROVAL_BOUNDARY_LINES,
        TASK_INBOX_BOUNDARY_LINE,
    ]
    if include_suggested_next_action:
        lines.extend(
            [
                "",
                "Suggested next action:",
                "- Use /today for the daily view, /brief for a meeting brief, or /prep <suggestion_id> for prep.",
            ]
        )
    return tuple(lines)


def render_compact_setup_capability_block() -> tuple[str, ...]:
    return (
        "Setup status:",
        *SETUP_COMPACT_LINES,
    )
