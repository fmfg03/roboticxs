from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import time
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.brief_memory_proposal import (
    BriefMemoryProposalRecord,
    build_brief_memory_proposal_record,
    render_brief_memory_candidate_section,
)
from app.brief_memory_approval import (
    BriefMemoryApprovalDecisionRecord,
    build_brief_memory_approval_decision,
    render_brief_memory_approval_decision,
)
from app.daily_brief_what_did_i_miss import (
    DailyBriefRegistry,
    DailyBriefSourceBundle,
    NO_UPDATES_SUMMARY,
    create_daily_brief_snapshot,
)
from app.google_calendar_readonly_connector import (
    CalendarReadResult,
    GoogleCalendarHttpClientProtocol,
    run_google_calendar_readonly_connector,
)
from app.inbox_item_decision import (
    InboxItemDecisionRecord,
    build_inbox_item_decision,
    render_inbox_item_decision,
)
from app.meeting_brief_demo_flow import (
    MeetingBriefDemoDependencyBundle,
    MeetingBriefDemoFixture,
    build_default_meeting_brief_demo_fixture,
    get_meeting_brief_demo_artifact,
    run_local_meeting_brief_demo_flow,
)
from app.meeting_prep_pack import (
    MeetingPrepPackRecord,
    render_meeting_prep_pack,
    run_meeting_prep_pack,
)
from app.open_loops_command import (
    OpenLoopsCommandRecord,
    render_open_loops_command,
    run_open_loops_command,
)
from app.personal_admin_inbox import (
    PersonalAdminInboxRecord,
    render_personal_admin_inbox,
    run_personal_admin_inbox,
)
from app.proactive_meeting_suggestion import (
    ProactiveMeetingSuggestionScanRecord,
    render_proactive_meeting_suggestion_scan,
    run_proactive_meeting_suggestion_scan,
)
from app.suggested_meeting_brief_request import (
    SuggestedMeetingBriefRequestRecord,
    render_suggested_meeting_brief_request,
    run_suggested_meeting_brief_request,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
    render_memory_center_command_reply,
    render_memory_limits_command_reply,
    render_memory_pending_command_reply,
)
from app.today_command import (
    TodayCommandRecord,
    render_today_command,
    run_today_command,
)

RUNNABLE_TELEGRAM_ROBOT_STAGE = "150P"
DEFAULT_ROBOT_ID = "roboticxs-dev"
DEFAULT_OWNER_ID = "local-owner"
DEFAULT_POLL_TIMEOUT_SECONDS = 30
DEFAULT_POLL_LIMIT = 10
DEFAULT_DEV_MODE = True
DEFAULT_DRY_RUN = False
SUPPORTED_COMMANDS = (
    "/start",
    "/help",
    "/status",
    "/miss",
    "/today",
    "/loops",
    "/inbox",
    "/inbox_done",
    "/inbox_dismiss",
    "/prep",
    "/brief",
    "/suggest_brief",
    "/memory_approve",
    "/memory_reject",
    "/memory",
    "/memory_limits",
    "/memory_pending",
)
PRODUCT_MENU_LINES = (
    "Today: /today, /miss",
    "Brief: /brief, /suggest_brief",
    "Prep: /prep <suggestion_id>",
    "Tasks: /inbox, /inbox_done <item_id>, /inbox_dismiss <item_id>",
    "Memory: /memory, /memory_pending, /memory_limits, /memory_approve <candidate_id>, /memory_reject <candidate_id>",
    "Setup Check: /status",
)
DAILY_BRIEF_DATE = "2026-06-20"
DAILY_BRIEF_TIMEZONE = "UTC"
DAILY_BRIEF_WINDOW_START = "2026-06-20T00:00:00+00:00"
DAILY_BRIEF_WINDOW_END = "2026-06-20T23:59:59+00:00"
MEETING_BRIEF_CHAT_ID = "telegram-brief-command"
MEETING_BRIEF_CREATED_AT = "2026-06-21T08:00:00Z"
CALENDAR_BRIEF_MAX_EVENTS = 3


class TelegramRobotConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TelegramRobotConfig:
    bot_token: str
    owner_ids: frozenset[int]
    robot_id: str
    owner_id: str
    poll_timeout_seconds: int
    poll_limit: int
    dry_run: bool
    dev_mode: bool


@dataclass(frozen=True, slots=True)
class TelegramIncomingCommand:
    update_id: int | None
    chat_id: int
    telegram_user_id: int
    message_id: int | None
    command: str
    raw_text: str


@dataclass(frozen=True, slots=True)
class TelegramSendReceipt:
    chat_id: int
    telegram_user_id: int
    command: str
    authorized: bool
    reply_text: str
    message_id: int | None
    api_receipt: dict | None


@dataclass(frozen=True, slots=True)
class TelegramPollingCycleResult:
    next_offset: int | None
    processed_update_ids: tuple[int, ...]
    ignored_update_ids: tuple[int, ...]
    receipts: tuple[TelegramSendReceipt, ...]


class TelegramClientProtocol(Protocol):
    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
        ...

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict:
        ...


class TelegramBotApiClient:
    def __init__(self, *, bot_token: str) -> None:
        self._bot_token = bot_token
        self._base_url = f"https://api.telegram.org/bot{bot_token}/"

    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
        payload: dict[str, int] = {
            "timeout": timeout,
            "limit": limit,
        }
        if offset is not None:
            payload["offset"] = offset
        body = self._post("getUpdates", payload)
        result = body.get("result")
        if not isinstance(result, list):
            raise TelegramRobotConfigError("rejected_invalid_get_updates_result")
        return [item for item in result if isinstance(item, dict)]

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict:
        payload: dict[str, int | str] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._post("sendMessage", payload)

    def _post(self, method: str, payload: dict[str, int | str]) -> dict:
        data = urlencode(payload).encode("utf-8")
        request = Request(
            self._base_url + method,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("ok") is not True:
            raise TelegramRobotConfigError(f"telegram_api_error:{method}")
        return body


def _env_bool(name: str, default: bool = False, env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_owner_ids(raw: str | None) -> frozenset[int]:
    if raw is None or not raw.strip():
        return frozenset()
    owner_ids: set[int] = set()
    for part in raw.split(","):
        candidate = part.strip()
        if not candidate:
            continue
        if not candidate.isdigit():
            raise TelegramRobotConfigError("rejected_invalid_owner_allowlist")
        owner_ids.add(int(candidate))
    return frozenset(owner_ids)


def load_telegram_robot_config_from_env(env: dict[str, str] | None = None) -> TelegramRobotConfig:
    source = os.environ if env is None else env
    poll_timeout_raw = source.get(
        "ROBOTICXS_TELEGRAM_POLL_TIMEOUT_SECONDS",
        str(DEFAULT_POLL_TIMEOUT_SECONDS),
    )
    poll_limit_raw = source.get("ROBOTICXS_TELEGRAM_POLL_LIMIT", str(DEFAULT_POLL_LIMIT))
    try:
        poll_timeout_seconds = int(poll_timeout_raw)
        poll_limit = int(poll_limit_raw)
    except ValueError as exc:
        raise TelegramRobotConfigError("rejected_invalid_polling_configuration") from exc
    return TelegramRobotConfig(
        bot_token=source.get("ROBOTICXS_TELEGRAM_BOT_TOKEN", "").strip(),
        owner_ids=_parse_owner_ids(source.get("ROBOTICXS_TELEGRAM_OWNER_IDS")),
        robot_id=source.get("ROBOTICXS_ROBOT_ID", DEFAULT_ROBOT_ID).strip(),
        owner_id=source.get("ROBOTICXS_OWNER_ID", DEFAULT_OWNER_ID).strip(),
        poll_timeout_seconds=poll_timeout_seconds,
        poll_limit=poll_limit,
        dry_run=_env_bool("ROBOTICXS_TELEGRAM_DRY_RUN", DEFAULT_DRY_RUN, env=source),
        dev_mode=_env_bool("ROBOTICXS_TELEGRAM_DEV_MODE", DEFAULT_DEV_MODE, env=source),
    )


def validate_telegram_robot_config(config: TelegramRobotConfig) -> TelegramRobotConfig:
    if not config.robot_id:
        raise TelegramRobotConfigError("rejected_missing_robot_id")
    if not config.owner_id:
        raise TelegramRobotConfigError("rejected_missing_owner_id")
    if not config.owner_ids:
        raise TelegramRobotConfigError("rejected_missing_owner_allowlist")
    if not config.dry_run and not config.bot_token:
        raise TelegramRobotConfigError("rejected_missing_bot_token")
    if config.poll_timeout_seconds <= 0:
        raise TelegramRobotConfigError("rejected_invalid_poll_timeout")
    if config.poll_limit <= 0:
        raise TelegramRobotConfigError("rejected_invalid_poll_limit")
    return config


def parse_telegram_incoming_command(update: dict) -> TelegramIncomingCommand | None:
    if not isinstance(update, dict):
        return None
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    sender = message.get("from")
    raw_text = message.get("text")
    if not isinstance(chat, dict) or not isinstance(sender, dict) or not isinstance(raw_text, str):
        return None
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")
    if not isinstance(chat_id, int) or not isinstance(telegram_user_id, int):
        return None
    stripped_text = raw_text.strip()
    if not stripped_text:
        return None
    command = normalize_telegram_command(stripped_text)
    if command is None:
        return None
    update_id = update.get("update_id")
    message_id = message.get("message_id")
    return TelegramIncomingCommand(
        update_id=update_id if isinstance(update_id, int) else None,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        message_id=message_id if isinstance(message_id, int) else None,
        command=command,
        raw_text=stripped_text,
    )


def normalize_telegram_command(raw_text: str) -> str | None:
    stripped = raw_text.strip()
    if not stripped:
        return None
    first_token = stripped.split()[0].lower()
    if first_token.startswith("/"):
        base = first_token.split("@", 1)[0]
        return base
    return first_token


def extract_telegram_command_argument(raw_text: str, *, command: str) -> str | None:
    parts = raw_text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return None
    if normalize_telegram_command(parts[0]) != command:
        return None
    argument = parts[1].strip()
    return argument or None


def is_owner_authorized(
    *,
    telegram_user_id: int,
    config: TelegramRobotConfig,
) -> bool:
    return telegram_user_id in config.owner_ids


def render_start_command_reply(config: TelegramRobotConfig) -> str:
    return "\n".join(
        [
            "Roboticxs",
            "",
            "Your private robot is online.",
            f"Robot: {config.robot_id}",
            "Access: owner-gated",
            "",
            "What I can help with:",
            *PRODUCT_MENU_LINES,
            "",
            "Start here:",
            "- /today for your daily view",
            "- /brief for a meeting brief",
            "- /status for setup and capability status",
            "",
            "Safety:",
            "- I do not write Calendar or Gmail.",
            "- I do not remember new facts without approval.",
            "- I do not take external actions without approval.",
            "No action was taken.",
        ]
    )


def render_help_command_reply() -> str:
    return "\n".join(
        [
            "Roboticxs Menu",
            "",
            *PRODUCT_MENU_LINES,
            "",
            "Notes:",
            "- Tasks is your robot task inbox, not your Gmail inbox yet.",
            "- Setup Check shows what is active, unavailable, blocked, or intentionally disabled.",
            "- Memory changes require approval.",
            "",
            "No action was taken.",
        ]
    )


def render_status_command_reply(config: TelegramRobotConfig) -> str:
    live_telegram_state = "disabled" if config.dry_run else "enabled"
    dev_mode_state = "enabled" if config.dev_mode else "disabled"
    return "\n".join(
        [
            "Setup Check",
            "",
            f"Robot: {config.robot_id}",
            "Access: owner-gated",
            f"Telegram replies: {live_telegram_state}",
            f"Dev/sandbox mode: {dev_mode_state}",
            "",
            "Active now:",
            "- Today and missed-item summaries",
            "- Meeting briefs and prep packs",
            "- Robot task inbox",
            "- Memory visibility and approval receipts",
            "",
            "Needs setup:",
            "- Calendar reads require read-only Google setup.",
            "- Calendar meeting suggestions need read-only Calendar setup.",
            "- Memory review uses local pending proposals only until writeback is approved.",
            "",
            "Unavailable:",
            "- Gmail is not an inbox yet.",
            "- Document review is draft-only until a document intake stage is approved.",
            "- Calendar and Gmail writes are not product capabilities.",
            "",
            "Intentionally disabled:",
            "- Calendar writes: disabled",
            "- Gmail writes: disabled",
            "- Model calls: disabled",
            "- Tool execution: disabled",
            "- Workers: disabled",
            "- Scheduler/proactive outbound: disabled",
            "- Automatic Memory Center mutation: disabled",
            "",
            "Approval boundaries:",
            "- I do not remember new facts without approval.",
            "- I do not take external actions without approval.",
            "- Task Inbox is your robot task inbox, not your Gmail inbox yet.",
            "",
            "Suggested next action:",
            "- Use /today for the daily view, /brief for a meeting brief, or /prep <suggestion_id> for prep.",
            "",
            "Roadmap: 95P-153P closed, Setup & Capability Status active",
        ]
    )


def render_unknown_command_reply() -> str:
    return "\n".join(
        [
            "I do not know that command yet.",
            "",
            "Use /help to see the Roboticxs menu.",
            "",
            "Available areas:",
            *PRODUCT_MENU_LINES,
            "",
            "No action was taken.",
        ]
    )


def render_unauthorized_reply() -> str:
    return "This Roboticxs bot is private. No action was taken."


def render_miss_command_reply(config: TelegramRobotConfig) -> str:
    snapshot = create_daily_brief_snapshot(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        brief_date=DAILY_BRIEF_DATE,
        timezone=DAILY_BRIEF_TIMEZONE,
        window_start=DAILY_BRIEF_WINDOW_START,
        window_end=DAILY_BRIEF_WINDOW_END,
        source_records=DailyBriefSourceBundle(),
        registry=DailyBriefRegistry(),
    )
    highlight = "No missed items found in the local snapshot."
    suggested_next_step = "No action required."
    if snapshot.headline_summary != NO_UPDATES_SUMMARY:
        highlight = snapshot.headline_summary
        suggested_next_step = "Review the local snapshot sections before taking any external action."
    return "\n".join(
        [
            "What Did I Miss?",
            "",
            "Status: local read-only brief",
            "Source: Hermes local state snapshot",
            "External connectors: disabled",
            "LLM/model calls: disabled",
            "Memory mutation: disabled",
            "",
            "Highlights:",
            f"- {highlight}",
            f"- Brief summary: {snapshot.headline_summary}",
            "",
            "Suggested next step:",
            f"- {suggested_next_step}",
            "",
            "No external action was taken.",
        ]
    )


def render_calendar_events_for_brief(result: CalendarReadResult) -> list[str]:
    if not result.ok:
        return [
            "Blocked / unavailable sources:",
            f"- Read-only Calendar connector unavailable: {result.error_code or 'unknown_error'}.",
            "- Falling back to local deterministic meeting context.",
        ]
    if not result.events:
        return [
            "Calendar:",
            "- No upcoming Calendar events found in the configured read-only window.",
        ]

    lines = ["Calendar:"]
    for event in result.events[:CALENDAR_BRIEF_MAX_EVENTS]:
        label = event.start
        if event.all_day:
            label = f"{event.start} (all day)"
        lines.append(f"- {label} - {event.summary}")
    if len(result.events) > CALENDAR_BRIEF_MAX_EVENTS:
        remaining = len(result.events) - CALENDAR_BRIEF_MAX_EVENTS
        lines.append(f"- Plus {remaining} more event(s) in the read-only window.")
    return lines


def render_brief_command_reply(
    config: TelegramRobotConfig,
    *,
    meeting_context_available: bool = True,
    fixture: MeetingBriefDemoFixture | None = None,
    created_at: str = MEETING_BRIEF_CREATED_AT,
    calendar_result: CalendarReadResult | None = None,
) -> str:
    if not meeting_context_available:
        return "\n".join(
            [
                "Meeting Brief",
                "",
                "No local meeting context is available in the deterministic snapshot.",
                "Google Calendar read-only connector was not used.",
                "No external action was taken.",
            ]
        )

    dependencies = MeetingBriefDemoDependencyBundle()
    flow = run_local_meeting_brief_demo_flow(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        chat_id=MEETING_BRIEF_CHAT_ID,
        dependencies=dependencies,
        fixture=build_default_meeting_brief_demo_fixture() if fixture is None else fixture,
        created_at=created_at,
    )
    artifact = get_meeting_brief_demo_artifact(
        registry=dependencies.demo_registry,
        demo_artifact_id=flow.demo_artifact_id,
    )
    if artifact is None:
        raise TelegramRobotConfigError("rejected_missing_meeting_brief_artifact")

    meeting_title = artifact.title.removeprefix("Meeting Brief Demo: ").strip() or artifact.title
    agenda_items = artifact.preparation_checklist[:2]
    risk_item = (
        artifact.open_questions[0]
        if artifact.open_questions
        else "No local risks found."
    )
    suggested_prep = (
        artifact.suggested_materials[0]
        if artifact.suggested_materials
        else "Review the deterministic local context before the meeting."
    )
    calendar_lines = (
        render_calendar_events_for_brief(calendar_result)
        if calendar_result is not None
        else [
            "Calendar:",
            "- Google Calendar read-only connector was not configured for this reply.",
        ]
    )

    return "\n".join(
        [
            "Meeting Brief",
            "",
            "Status: local read-only meeting brief",
            "Source: local meeting context + optional read-only Calendar snapshot",
            "",
            *calendar_lines,
            "",
            "Meeting context:",
            f"- {meeting_title}",
            f"- {artifact.meeting_context_summary}",
            "",
            "Agenda:",
            *(f"- {item}" for item in agenda_items),
            "",
            "Watchpoints:",
            f"- {risk_item}",
            "",
            "Suggested prep:",
            f"- {suggested_prep}",
            "",
            "Safe next step:",
            "- Review the brief and take any external action yourself unless a later approved command explicitly supports it.",
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Memory mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )


def render_suggest_brief_command_reply(record: ProactiveMeetingSuggestionScanRecord) -> str:
    return "\n".join(
        [
            render_proactive_meeting_suggestion_scan(record),
            "",
            "Telegram delivery: owner-requested reply only.",
            "Automatic proactive send: disabled.",
        ]
    )


def render_requested_suggested_brief_reply(record: SuggestedMeetingBriefRequestRecord) -> str:
    return "\n".join(
        [
            render_suggested_meeting_brief_request(record),
            "",
            "Telegram delivery: owner-requested reply only.",
            "Automatic proactive send: disabled.",
        ]
    )


def render_command_reply(
    command: str,
    config: TelegramRobotConfig,
    *,
    suggested_meeting_brief: SuggestedMeetingBriefRequestRecord | None = None,
    calendar_result: CalendarReadResult | None = None,
    proactive_meeting_suggestion: ProactiveMeetingSuggestionScanRecord | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
    today_record: TodayCommandRecord | None = None,
    open_loops_record: OpenLoopsCommandRecord | None = None,
    personal_admin_inbox: PersonalAdminInboxRecord | None = None,
    inbox_item_decision: InboxItemDecisionRecord | None = None,
    meeting_prep_pack: MeetingPrepPackRecord | None = None,
    brief_memory_proposal: BriefMemoryProposalRecord | None = None,
    brief_memory_decision: BriefMemoryApprovalDecisionRecord | None = None,
) -> str:
    if command == "/start":
        return render_start_command_reply(config)
    if command == "/help":
        return render_help_command_reply()
    if command == "/status":
        return render_status_command_reply(config)
    if command == "/miss":
        return render_miss_command_reply(config)
    if command == "/today":
        if today_record is None:
            raise TelegramRobotConfigError("rejected_missing_today_command_record")
        return render_today_command(today_record)
    if command == "/loops":
        if open_loops_record is None:
            raise TelegramRobotConfigError("rejected_missing_open_loops_command_record")
        return render_open_loops_command(open_loops_record)
    if command == "/inbox":
        if personal_admin_inbox is None:
            raise TelegramRobotConfigError("rejected_missing_personal_admin_inbox")
        return render_personal_admin_inbox(personal_admin_inbox)
    if command in {"/inbox_done", "/inbox_dismiss"}:
        if inbox_item_decision is None:
            raise TelegramRobotConfigError("rejected_missing_inbox_item_decision")
        return render_inbox_item_decision(inbox_item_decision)
    if command == "/prep":
        if meeting_prep_pack is None:
            raise TelegramRobotConfigError("rejected_missing_meeting_prep_pack")
        reply = render_meeting_prep_pack(meeting_prep_pack)
        if brief_memory_proposal is None:
            return reply
        return "\n".join(
            [
                reply,
                "",
                *render_brief_memory_candidate_section(brief_memory_proposal),
            ]
        )
    if command == "/brief":
        if suggested_meeting_brief is not None:
            return render_requested_suggested_brief_reply(suggested_meeting_brief)
        return render_brief_command_reply(config, calendar_result=calendar_result)
    if command == "/suggest_brief":
        if proactive_meeting_suggestion is None:
            raise TelegramRobotConfigError("rejected_missing_proactive_meeting_suggestion")
        return render_suggest_brief_command_reply(proactive_meeting_suggestion)
    if command in {"/memory_approve", "/memory_reject"}:
        if brief_memory_decision is None:
            raise TelegramRobotConfigError("rejected_missing_brief_memory_decision")
        return render_brief_memory_approval_decision(brief_memory_decision)
    if command == "/memory":
        return render_memory_command_reply(config, source_bundle=memory_source_bundle)
    if command == "/memory_limits":
        return render_memory_limits_reply(config, source_bundle=memory_source_bundle)
    if command == "/memory_pending":
        return render_memory_pending_reply(config, source_bundle=memory_source_bundle)
    return render_unknown_command_reply()


def render_memory_command_reply(
    config: TelegramRobotConfig,
    *,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> str:
    snapshot = build_memory_center_telegram_snapshot(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        source_bundle=source_bundle,
    )
    return render_memory_center_command_reply(snapshot)


def render_memory_limits_reply(
    config: TelegramRobotConfig,
    *,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> str:
    snapshot = build_memory_center_telegram_snapshot(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        source_bundle=source_bundle,
    )
    return render_memory_limits_command_reply(snapshot)


def render_memory_pending_reply(
    config: TelegramRobotConfig,
    *,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> str:
    snapshot = build_memory_center_telegram_snapshot(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        source_bundle=source_bundle,
    )
    return render_memory_pending_command_reply(snapshot)


def handle_incoming_command(
    *,
    incoming_command: TelegramIncomingCommand,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
    calendar_http_client: GoogleCalendarHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> TelegramSendReceipt:
    authorized = is_owner_authorized(
        telegram_user_id=incoming_command.telegram_user_id,
        config=config,
    )
    brief_suggestion_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/brief",
    )
    prep_suggestion_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/prep",
    )
    memory_approve_candidate_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_approve",
    )
    memory_reject_candidate_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_reject",
    )
    inbox_done_item_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/inbox_done",
    )
    inbox_dismiss_item_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/inbox_dismiss",
    )
    suggested_meeting_brief = None
    calendar_result = None
    proactive_meeting_suggestion = None
    today_record = None
    open_loops_record = None
    personal_admin_inbox = None
    inbox_item_decision = None
    meeting_prep_pack = None
    brief_memory_proposal = None
    brief_memory_decision = None
    if authorized and incoming_command.command == "/brief" and brief_suggestion_id:
        suggested_meeting_brief = run_suggested_meeting_brief_request(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestion_id=brief_suggestion_id,
            calendar_http_client=calendar_http_client,
        )
    elif authorized and incoming_command.command == "/brief":
        calendar_result = run_google_calendar_readonly_connector(
            http_client=calendar_http_client,
        )
    if authorized and incoming_command.command == "/suggest_brief":
        proactive_meeting_suggestion = run_proactive_meeting_suggestion_scan(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_http_client=calendar_http_client,
        )
    if authorized and incoming_command.command == "/today":
        today_record = run_today_command(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_http_client=calendar_http_client,
            memory_source_bundle=memory_source_bundle,
        )
    if authorized and incoming_command.command == "/loops":
        open_loops_record = run_open_loops_command(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_http_client=calendar_http_client,
            memory_source_bundle=memory_source_bundle,
        )
    if authorized and incoming_command.command == "/inbox":
        personal_admin_inbox = run_personal_admin_inbox(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_http_client=calendar_http_client,
            memory_source_bundle=memory_source_bundle,
        )
    if authorized and incoming_command.command == "/inbox_done":
        inbox_item_decision = build_inbox_item_decision(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            item_id=inbox_done_item_id or "",
            choice="done",
        )
    if authorized and incoming_command.command == "/inbox_dismiss":
        inbox_item_decision = build_inbox_item_decision(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            item_id=inbox_dismiss_item_id or "",
            choice="dismiss",
        )
    if authorized and incoming_command.command == "/prep":
        meeting_prep_pack = run_meeting_prep_pack(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestion_id=prep_suggestion_id or "",
            calendar_http_client=calendar_http_client,
            memory_source_bundle=memory_source_bundle,
        )
        brief_memory_proposal = build_brief_memory_proposal_record(prep_pack=meeting_prep_pack)
    if authorized and incoming_command.command == "/memory_approve":
        brief_memory_decision = build_brief_memory_approval_decision(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            candidate_id=memory_approve_candidate_id or "",
            choice="approve",
        )
    if authorized and incoming_command.command == "/memory_reject":
        brief_memory_decision = build_brief_memory_approval_decision(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            candidate_id=memory_reject_candidate_id or "",
            choice="reject",
        )
    if authorized:
        reply_text = render_command_reply(
            incoming_command.command,
            config,
            suggested_meeting_brief=suggested_meeting_brief,
            calendar_result=calendar_result,
            proactive_meeting_suggestion=proactive_meeting_suggestion,
            memory_source_bundle=memory_source_bundle,
            today_record=today_record,
            open_loops_record=open_loops_record,
            personal_admin_inbox=personal_admin_inbox,
            inbox_item_decision=inbox_item_decision,
            meeting_prep_pack=meeting_prep_pack,
            brief_memory_proposal=brief_memory_proposal,
            brief_memory_decision=brief_memory_decision,
        )
    else:
        reply_text = render_unauthorized_reply()
    receipt = client.send_message(
        incoming_command.chat_id,
        reply_text,
        reply_to_message_id=incoming_command.message_id,
    )
    return TelegramSendReceipt(
        chat_id=incoming_command.chat_id,
        telegram_user_id=incoming_command.telegram_user_id,
        command=incoming_command.command,
        authorized=authorized,
        reply_text=reply_text,
        message_id=incoming_command.message_id,
        api_receipt=receipt,
    )


def run_polling_once(
    *,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
    offset: int | None = None,
) -> TelegramPollingCycleResult:
    validated = validate_telegram_robot_config(config)
    updates = client.get_updates(
        offset=offset,
        timeout=validated.poll_timeout_seconds,
        limit=validated.poll_limit,
    )
    next_offset = offset
    processed_update_ids: list[int] = []
    ignored_update_ids: list[int] = []
    receipts: list[TelegramSendReceipt] = []
    for update in updates:
        update_id = update.get("update_id")
        incoming_command = parse_telegram_incoming_command(update)
        if incoming_command is None:
            if isinstance(update_id, int):
                ignored_update_ids.append(update_id)
                next_offset = update_id + 1
            continue
        receipts.append(
            handle_incoming_command(
                incoming_command=incoming_command,
                client=client,
                config=validated,
            )
        )
        if incoming_command.update_id is not None:
            processed_update_ids.append(incoming_command.update_id)
            next_offset = incoming_command.update_id + 1
    return TelegramPollingCycleResult(
        next_offset=next_offset,
        processed_update_ids=tuple(processed_update_ids),
        ignored_update_ids=tuple(ignored_update_ids),
        receipts=tuple(receipts),
    )


def run_polling_loop(
    *,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
    offset: int | None = None,
    max_cycles: int | None = None,
    idle_sleep_seconds: float = 0.0,
) -> TelegramPollingCycleResult:
    validated = validate_telegram_robot_config(config)
    if max_cycles is not None and max_cycles < 0:
        raise TelegramRobotConfigError("rejected_invalid_max_cycles")
    cycle_count = 0
    current_offset = offset
    all_processed: list[int] = []
    all_ignored: list[int] = []
    all_receipts: list[TelegramSendReceipt] = []
    while max_cycles is None or cycle_count < max_cycles:
        result = run_polling_once(client=client, config=validated, offset=current_offset)
        current_offset = result.next_offset
        all_processed.extend(result.processed_update_ids)
        all_ignored.extend(result.ignored_update_ids)
        all_receipts.extend(result.receipts)
        cycle_count += 1
        if max_cycles is not None and cycle_count >= max_cycles:
            break
        if idle_sleep_seconds > 0:
            time.sleep(idle_sleep_seconds)
    return TelegramPollingCycleResult(
        next_offset=current_offset,
        processed_update_ids=tuple(all_processed),
        ignored_update_ids=tuple(all_ignored),
        receipts=tuple(all_receipts),
    )


def build_telegram_robot_startup_report(config: TelegramRobotConfig) -> str:
    validated = validate_telegram_robot_config(config)
    return "\n".join(
        [
            "Roboticxs Telegram Robot: online",
            f"Stage: {RUNNABLE_TELEGRAM_ROBOT_STAGE}",
            f"Robot: {validated.robot_id}",
            f"Owner gate: enabled ({len(validated.owner_ids)} allowed Telegram user id(s))",
            f"Dev mode: {'enabled' if validated.dev_mode else 'disabled'}",
            f"Dry run: {'enabled' if validated.dry_run else 'disabled'}",
            "Product menu: Today, Brief, Prep, Tasks, Memory, Setup Check",
            "Available commands: /start, /help, /status, /miss, /today, /loops, /inbox, /inbox_done, /inbox_dismiss, /prep, /brief, /suggest_brief, /memory_approve, /memory_reject, /memory, /memory_limits, /memory_pending",
            "External connectors: Google Calendar read-only optional",
            "Calendar writes: disabled",
            "LLM/model calls: disabled",
            "Tools: disabled",
            "Memory Center commands: /memory, /memory_limits, /memory_pending",
            "Memory Center mutation: disabled",
            "Today command: /today owner-requested read-only summary only",
            "Open Loops command: /loops owner-requested read-only unresolved loops only",
            "Personal Admin Inbox: /inbox owner-requested read-only pending items only",
            "Inbox Item Decisions: /inbox_done and /inbox_dismiss create local decision receipts only",
            "Meeting Prep Pack: /prep <suggestion_id> owner-requested read-only prep only",
            "Brief Memory Proposals: shown in /prep as pending owner review only",
            "Brief Memory Decisions: /memory_approve and /memory_reject create local decision receipts only",
            "Proactive meeting suggestions: /suggest_brief owner-requested replies only",
            "Suggested meeting brief requests: /brief <suggestion_id> owner-requested replies only",
            "Proactive outbound: disabled",
        ]
    )


def create_telegram_client(config: TelegramRobotConfig) -> TelegramClientProtocol:
    return TelegramBotApiClient(bot_token=config.bot_token)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.runnable_telegram_robot_mvp")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-cycles", type=int, default=None)
    args = parser.parse_args(argv)
    try:
        config = validate_telegram_robot_config(load_telegram_robot_config_from_env())
        client = create_telegram_client(config)
    except TelegramRobotConfigError as exc:
        print(f"Roboticxs Telegram Robot: offline\nReason: {exc}")
        return 1
    print(build_telegram_robot_startup_report(config))
    try:
        if args.once:
            run_polling_once(client=client, config=config)
        else:
            run_polling_loop(client=client, config=config, max_cycles=args.max_cycles)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
