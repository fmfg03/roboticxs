from __future__ import annotations

from dataclasses import dataclass


PREMIUM_TELEGRAM_UX_SHELL_STAGE = "191P"
ALLOWED_TELEGRAM_UX_STATES = frozenset(
    {
        "ready",
        "needs setup",
        "blocked",
        "draft-only",
        "approval-required",
    }
)
PRODUCT_INTENTS = (
    "Today",
    "Prep",
    "Pilot",
    "Suggestions",
    "Approvals",
    "Drafts",
    "Memory",
    "Documents",
    "Usage",
    "Status",
)


@dataclass(frozen=True, slots=True)
class TelegramUxCard:
    title: str
    state: str
    primary_action: str
    summary: str
    limits: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in ALLOWED_TELEGRAM_UX_STATES:
            raise ValueError("rejected_unknown_telegram_ux_state")
        if not self.title.strip() or not self.primary_action.strip() or not self.summary.strip():
            raise ValueError("rejected_incomplete_telegram_ux_card")


@dataclass(frozen=True, slots=True)
class TelegramUxSection:
    title: str
    cards: tuple[TelegramUxCard, ...]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("rejected_missing_telegram_ux_section_title")
        if not self.cards:
            raise ValueError("rejected_empty_telegram_ux_section")


def render_telegram_ux_card(card: TelegramUxCard) -> str:
    lines = [
        f"{card.title}",
        f"State: {card.state}",
        f"Action: {card.primary_action}",
        f"Use: {card.summary}",
    ]
    if card.limits:
        lines.append("Limits:")
        lines.extend(f"- {limit}" for limit in card.limits)
    return "\n".join(lines)


def render_telegram_ux_section(section: TelegramUxSection) -> str:
    lines = [section.title]
    for card in section.cards:
        lines.extend(["", render_telegram_ux_card(card)])
    return "\n".join(lines)


def render_telegram_ux_sections(sections: tuple[TelegramUxSection, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    for index, section in enumerate(sections):
        if index:
            lines.append("")
        lines.append(render_telegram_ux_section(section))
    return tuple(lines)


def build_premium_telegram_home_sections() -> tuple[TelegramUxSection, ...]:
    return (
        TelegramUxSection(
            "Command Center",
            (
                _card("Today", "ready", "/today or /daily_brief", "See the daily view and read-only cross-source brief."),
                _card("Prep", "ready", "/prep <suggestion_id>", "Prepare a meeting from Calendar, Gmail context, and approved memory."),
                _card("Pilot", "ready", "/pilot", "Run the controlled customer pilot path end to end."),
            ),
        ),
        TelegramUxSection(
            "Work Queue",
            (
                _card("Suggestions", "ready", "/suggestions", "Review useful next actions before anything is executed."),
                _card("Approvals", "approval-required", "/approvals", "Review outputs waiting for local approve or reject receipts."),
                _card("Drafts", "approval-required", "/drafts", "Review local draft candidates and approve or reject them."),
            ),
        ),
        TelegramUxSection(
            "Controls",
            (
                _card("Memory", "approval-required", "/memory", "Review approved memory and pending memory decisions."),
                _card("Documents", "draft-only", "/document", "Use document intake and draft-only review when text is available."),
                _card("Usage", "ready", "/usage", "Review local estimated usage and cost receipts."),
                _card("Status", "needs setup", "/status or /checkup", "Check setup, connected sources, and blocked actions."),
            ),
        ),
    )


def build_premium_telegram_help_sections() -> tuple[TelegramUxSection, ...]:
    return (
        TelegramUxSection(
            "Daily Flow",
            (
                _card("Today", "ready", "/today, /miss, /daily_brief", "Daily view, missed items, and cross-source brief."),
                _card("Prep", "ready", "/prep <suggestion_id>, /brief, /suggest_brief", "Meeting prep and brief requests."),
                _card("Pilot", "ready", "/pilot", "Controlled pilot receipt with sources, approval, draft, and usage."),
            ),
        ),
        TelegramUxSection(
            "Review Flow",
            (
                _card("Suggestions", "ready", "/suggestions, /suggestion_draft <id>", "Review, dismiss, snooze, save memory, draft, or follow up."),
                _card("Approvals", "approval-required", "/approvals, /approve <id>, /reject <id>", "Record local approve or reject receipts without executing outputs."),
                _card("Drafts", "approval-required", "/drafts, /draft_approve <id>, /draft_reject <id>", "Approve, reject, edit, expire, or export approved drafts."),
            ),
        ),
        TelegramUxSection(
            "Control Flow",
            (
                _card("Memory", "approval-required", "/memory, /memory_review, /memory_approve <id>", "Approve, reject, edit, forget, and inspect memory."),
                _card("Documents", "draft-only", "send a document or /document", "Draft-only document intake and review."),
                _card("Usage", "ready", "/usage", "Local estimated usage and cost summary."),
                _card("Status", "needs setup", "/status, /checkup, /setup", "Setup status, source readiness, and safety boundaries."),
            ),
        ),
    )


def build_premium_telegram_status_sections(
    *,
    telegram_replies: str,
    dev_mode: str,
) -> tuple[TelegramUxSection, ...]:
    return (
        TelegramUxSection(
            "Runtime",
            (
                _card("Telegram replies", "ready" if telegram_replies == "enabled" else "blocked", telegram_replies, "Owner-gated Telegram command replies."),
                _card("Dev sandbox", "ready" if dev_mode == "enabled" else "blocked", dev_mode, "Local controlled runtime mode."),
            ),
        ),
        TelegramUxSection(
            "Sources",
            (
                _card("Calendar", "needs setup", "/checkup", "Read-only Calendar context when configured."),
                _card("Gmail", "needs setup", "/checkup", "Read-only Gmail context and approved draft creation when configured."),
                _card("Documents", "draft-only", "send a document", "Draft-only document review without professional advice."),
            ),
        ),
        TelegramUxSection(
            "Safety",
            (
                _card("External writes", "blocked", "approval gate", "No irreversible external action is allowed by the shell."),
                _card("Memory mutation", "approval-required", "/memory_review", "Memory remains owner-reviewed and receipt-driven."),
                _card("Pilot", "ready", "/pilot", "Controlled pilot receipt remains no-send and no-calendar-write."),
            ),
        ),
    )


def render_premium_shell_boundaries() -> tuple[str, ...]:
    return (
        "Premium Telegram UX Shell: active",
        "Gmail send: disabled",
        "Gmail modify/archive/label/delete: disabled",
        "Calendar writes: disabled",
        "Automatic Memory Center mutation: disabled",
        "External irreversible actions: disabled",
        "Model/tool calls: disabled",
        "Workers/scheduler: disabled",
    )


def _card(title: str, state: str, action: str, summary: str) -> TelegramUxCard:
    return TelegramUxCard(
        title=title,
        state=state,
        primary_action=action,
        summary=summary,
        limits=(
            "No external action without explicit approval.",
            "No secrets are shown.",
        ),
    )
