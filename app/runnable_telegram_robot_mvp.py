from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.approved_output_export import (
    ApprovedOutputExportRecord,
    build_approved_output_export,
    render_approved_output_export,
)
from app.approved_gmail_draft_creation import (
    ApprovedGmailDraftCreationRecord,
    GmailDraftHttpClientProtocol,
    build_approved_gmail_draft_creation,
    render_approved_gmail_draft_creation,
)
from app.action_draft_queue import (
    ActionDraftQueue,
    build_action_draft_queue,
    render_action_draft_queue,
)
from app.brief_memory_proposal import (
    BriefMemoryProposalRecord,
    build_brief_memory_proposal_record,
    render_brief_memory_candidate_section,
)
from app.calendar_context_binding_v1 import (
    CalendarContextSourceTrace,
    append_calendar_source_trace,
    build_calendar_context_source_trace,
)
from app.calendar_context_scan import build_calendar_context_scan_record
from app.cross_source_daily_brief import (
    CrossSourceDailyBriefRecord,
    build_cross_source_daily_brief,
    render_cross_source_daily_brief,
)
from app.controlled_live_pilot_baseline import (
    ControlledLivePilotReceipt,
    build_controlled_live_pilot_baseline,
    render_controlled_live_pilot_receipt,
)
from app.customer_pilot_readiness_pack import (
    CustomerPilotReadinessPack,
    build_customer_pilot_readiness_pack,
    render_customer_pilot_readiness_pack,
)
from app.customer_pilot_audit_gate import (
    CustomerPilotAuditGateReport,
    build_customer_pilot_audit_gate,
    render_customer_pilot_audit_gate,
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
from app.gmail_readonly_context_scan import run_gmail_readonly_context_scan
from app.gmail_context_binding_v1 import (
    GmailContextSourceTrace,
    build_gmail_context_source_trace,
)
from app.gmail_readonly_context_scan import GmailReadonlyHttpClientProtocol
from app.gmail_thread_drilldown import (
    GmailThreadDrilldownRecord,
    render_gmail_thread_drilldown,
    run_gmail_thread_drilldown,
)
from app.founder_daily_use_loop import (
    FounderDailyUseLoop,
    build_founder_daily_use_loop,
    render_founder_daily_use_loop,
)
from app.founder_feedback_capture import (
    FounderFeedbackCaptureReceipt,
    build_founder_feedback_capture_receipt,
    parse_feedback_argument,
    render_feedback_usage,
    render_founder_feedback_capture_receipt,
)
from app.founder_to_friendly_pilot_baseline import (
    FounderToFriendlyPilotBaseline,
    build_founder_to_friendly_pilot_baseline,
    render_founder_to_friendly_pilot_baseline,
)
from app.friendly_user_onboarding_pack import (
    FriendlyUserOnboardingPack,
    build_friendly_user_onboarding_pack,
    render_friendly_user_onboarding_pack,
)
from app.friendly_pilot_operator_console import (
    FriendlyPilotOperatorConsole,
    FriendlyPilotUserStatus,
    build_friendly_pilot_operator_console,
    render_pilot_health,
    render_pilot_user,
    render_pilot_users,
)
from app.friendly_pilot_invite_consent import (
    FriendlyPilotInviteConsent,
    build_friendly_pilot_invite_consent,
    render_pilot_consent,
    render_pilot_invite,
)
from app.pilot_user_provisioning import (
    PilotUserProvisioningRecord,
    build_pilot_user_provisioning_record,
    parse_pilot_provision_argument,
    render_pilot_allowlist,
    render_pilot_user_provisioning,
)
from app.pilot_data_boundary import (
    PilotDataBoundaryItem,
    PilotDataBoundaryReport,
    build_pilot_data_boundary_report,
    render_pilot_data_boundary,
)
from app.pilot_onboarding_runbook import (
    PilotOnboardingRunbook,
    build_pilot_onboarding_runbook,
    render_pilot_onboarding_runbook,
)
from app.pilot_support_issue_capture import (
    PILOT_ISSUE_COMMANDS,
    PilotSupportIssueReceipt,
    build_pilot_support_issue_receipt,
    parse_pilot_issue_argument,
    render_pilot_issue_usage,
    render_pilot_support_issue_receipt,
)
from app.pilot_safety_incident_log import (
    PilotSafetyIncident,
    PilotSafetyIncidentLog,
    build_pilot_safety_incident_log,
    render_pilot_safety_incident_log,
)
from app.pilot_weekly_report import (
    PilotWeeklyReport,
    build_pilot_weekly_report,
    render_pilot_weekly_report,
)
from app.pilot_exit_data_removal import (
    PILOT_EXIT_COMMANDS,
    PilotExitDataRemovalReceipt,
    build_pilot_exit_data_removal_receipt,
    parse_pilot_exit_argument,
    render_pilot_exit_data_removal_receipt,
    render_pilot_exit_usage,
)
from app.friendly_pilot_launch_baseline import (
    FriendlyPilotLaunchBaseline,
    build_friendly_pilot_launch_baseline,
    render_friendly_pilot_launch_baseline,
)
from app.first_friendly_user_activation import (
    FirstFriendlyUserActivationReceipt,
    build_first_friendly_user_activation_receipt,
    parse_pilot_activation_argument,
    render_first_friendly_user_activation_receipt,
)
from app.pilot_review_session_pack import (
    PilotReviewSessionPack,
    build_pilot_review_session_pack,
    parse_pilot_review_argument,
    render_pilot_review_session_pack,
)
from app.pilot_learning_queue import (
    PilotLearningQueue,
    build_pilot_learning_queue,
    render_pilot_learning_queue,
)
from app.feedback_ledger_tags import (
    FeedbackLedger,
    FeedbackLedgerEntry,
    build_feedback_ledger,
    render_feedback_ledger,
)
from app.daily_loop_outcome_tracker import (
    DailyLoopOutcomeRecord,
    build_daily_loop_outcome_record,
    parse_daily_loop_outcome_argument,
    render_daily_loop_outcome_record,
    render_daily_loop_outcome_usage,
)
from app.suggestion_quality_tuning import (
    SuggestionQualityTuningReport,
    build_suggestion_quality_tuning_report,
    render_suggestion_quality_tuning_report,
)
from app.prep_quality_tuning import (
    PrepQualityTuningReport,
    build_prep_quality_tuning_report,
    render_prep_quality_tuning_report,
)
from app.draft_revision_loop import (
    DraftRevisionReceipt,
    build_draft_revision_receipt,
    parse_draft_revision_argument,
    render_draft_revision_receipt,
    render_draft_revision_usage,
)
from app.inbox_item_decision import (
    InboxItemDecisionRecord,
    build_inbox_item_decision,
    render_inbox_item_decision,
)
from app.document_review_pack_v1 import (
    DocumentReviewPackV1Record,
    build_document_review_pack_v1_from_intake,
    render_document_review_pack_v1,
)
from app.fast_path_cache import (
    FastPathCacheEntry,
    find_fast_path_cache_entry,
    render_fast_path_cached_reply,
)
from app.live_connector_readiness_check import (
    LiveConnectorReadinessReport,
    build_live_connector_readiness_report,
    render_compact_live_connector_readiness_block,
    render_live_connector_readiness_report,
)
from app.live_smoke_script import (
    LiveSmokeScript,
    build_live_smoke_script,
    render_live_smoke_script,
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
    build_meeting_prep_pack,
    render_meeting_prep_pack,
)
from app.meeting_prep_pack_v1 import (
    MeetingPrepPackV1Record,
    build_meeting_prep_pack_v1,
    render_meeting_prep_pack_v1,
)
from app.memory_approval_telegram_flow import (
    MemoryApprovalTelegramReceipt,
    MemoryReviewInbox,
    build_memory_approval_telegram_receipt,
    build_memory_review_inbox,
    render_memory_approval_telegram_receipt,
    render_memory_review_inbox,
)
from app.memory_intelligence import build_memory_intelligence_report, render_memory_intelligence_report
from app.memory_correction_loop import (
    MEMORY_CORRECTION_COMMANDS,
    MemoryCorrectionReceipt,
    build_memory_correction_receipt,
    correction_type_from_command,
    parse_memory_correction_argument,
    render_memory_correction_receipt,
    render_memory_correction_usage,
)
from app.memory_source_forget_receipts import (
    MemoryEditReceipt,
    MemoryForgetReceipt,
    build_memory_edit_receipt,
    build_memory_forget_receipt,
    build_memory_source_receipts,
    memory_id_matches_visible_approved_memory,
    render_memory_edit_receipt,
    render_memory_forget_receipt,
    render_memory_source_receipts,
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
from app.pilot_metrics_snapshot import (
    PilotMetricsSnapshot,
    build_pilot_metrics_snapshot,
    render_pilot_metrics_snapshot,
)
from app.proactive_meeting_suggestion import (
    ProactiveMeetingSuggestionScanRecord,
    build_proactive_meeting_suggestion_scan,
    render_proactive_meeting_suggestion_scan,
    run_proactive_meeting_suggestion_scan,
)
from app.premium_telegram_ux_shell import (
    build_premium_telegram_help_sections,
    build_premium_telegram_home_sections,
    build_premium_telegram_status_sections,
    render_premium_shell_boundaries,
    render_telegram_ux_sections,
)
from app.suggested_meeting_brief_request import (
    SuggestedMeetingBriefRequestRecord,
    render_suggested_meeting_brief_request,
    run_suggested_meeting_brief_request,
)
from app.setup_capability_status_component import (
    PRODUCT_APPROVAL_BOUNDARY_LINES,
    render_compact_setup_capability_block,
    render_setup_capability_status_sections,
)
from app.smart_context_ranking import (
    SmartContextRankingRecord,
    build_smart_context_ranking,
    render_smart_context_ranking,
)
from app.skill_manifest_runtime_gates import (
    classify_command_for_skill_gate,
    render_skill_runtime_boundary_lines,
    render_skill_runtime_gate_decision,
    render_skill_runtime_manifest_summary,
)
from app.source_trace_receipts import (
    SourceTraceReceipt,
    append_source_trace_receipt,
    build_source_trace_receipt,
)
from app.suggestion_inbox import (
    SuggestionInbox,
    build_suggestion_inbox,
    render_suggestion_inbox,
)
from app.suggestion_decision_flow import (
    SuggestionDecisionReceipt,
    build_suggestion_decision_receipt,
    render_suggestion_decision_receipt,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSnapshot,
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
    render_memory_center_command_reply,
    render_memory_limits_command_reply,
    render_memory_pending_command_reply,
)
from app.telegram_document_intake_stub import (
    TelegramDocumentIntakeMetadata,
    TelegramDocumentIntakeStubRecord,
    build_telegram_document_intake_stub_record,
    render_telegram_document_intake_stub,
)
from app.today_command import (
    TodayCommandRecord,
    build_today_command_record,
    render_today_command,
)
from app.user_confirmation_runtime import (
    UserConfirmationReceipt,
    build_user_confirmation_receipt,
    render_user_confirmation_receipt,
)
from app.user_approved_output_queue import (
    UserApprovedOutputDecisionReceipt,
    UserApprovedOutputItem,
    UserApprovedOutputQueue,
    build_user_approved_output_decision_receipt,
    build_user_approved_output_queue,
    render_user_approved_output_decision_receipt,
    render_user_approved_output_queue,
)
from app.usage_cost_ledger import (
    UsageCostLedgerEntry,
    render_usage_cost_ledger_summary,
    summarize_usage_cost_ledger,
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
    "/menu",
    "/status",
    "/checkup",
    "/setup",
    "/miss",
    "/today",
    "/daily_brief",
    "/demo",
    "/pilot",
    "/pilot_pack",
    "/pilot_audit",
    "/live_smoke",
    "/pilot_metrics",
    "/friendly_onboarding",
    "/friendly_pilot",
    "/pilot_users",
    "/pilot_user",
    "/pilot_health",
    "/pilot_invite",
    "/pilot_consent",
    "/pilot_provision",
    "/pilot_allowlist",
    "/pilot_boundary",
    "/pilot_runbook",
    "/report_issue",
    "/report_bug",
    "/report_confusing",
    "/report_wrong",
    "/report_missing",
    "/report_slow",
    "/pilot_safety",
    "/pilot_weekly_report",
    "/end_pilot",
    "/export_pilot_data",
    "/delete_pilot_memory",
    "/disable_pilot_connectors",
    "/pilot_launch",
    "/pilot_activate",
    "/pilot_review",
    "/pilot_learnings",
    "/founder_loop",
    "/feedback",
    "/feedback_ledger",
    "/founder_outcome",
    "/suggestion_quality",
    "/prep_quality",
    "/gmail_thread",
    "/loops",
    "/inbox",
    "/inbox_done",
    "/inbox_dismiss",
    "/prep",
    "/brief",
    "/suggest_brief",
    "/suggestions",
    "/suggestion_dismiss",
    "/suggestion_snooze",
    "/suggestion_memory",
    "/suggestion_draft",
    "/suggestion_followup",
    "/approvals",
    "/approve",
    "/reject",
    "/drafts",
    "/draft_approve",
    "/draft_reject",
    "/draft_edit",
    "/draft_revise",
    "/draft_expire",
    "/export_text",
    "/export_email",
    "/export_file",
    "/usage",
    "/memory_review",
    "/memory_approve",
    "/memory_reject",
    "/memory_edit",
    "/memory_forget",
    "/memory_wrong",
    "/memory_stale",
    "/memory_duplicate",
    "/memory_merge",
    "/memory_never_use",
    "/memory",
    "/memory_limits",
    "/memory_pending",
    "/document",
)
PRODUCT_MENU_LINES = (
    "Today: /today, /miss, /daily_brief, /demo, /pilot, /pilot_pack, /pilot_audit, /live_smoke, /pilot_metrics, /pilot_weekly_report, /pilot_launch, /pilot_activate <alias>, /pilot_review <pilot_user>, /pilot_learnings, /friendly_onboarding, /friendly_pilot, /pilot_users, /pilot_user <id>, /pilot_health, /pilot_invite <alias>, /pilot_consent <alias>, /pilot_provision <telegram_id> <alias>, /pilot_allowlist, /pilot_boundary, /pilot_runbook, /founder_loop",
    "Pilot Support: /report_issue, /report_bug, /report_confusing, /report_wrong, /report_missing, /report_slow",
    "Pilot Safety: /pilot_safety, /pilot_weekly_report",
    "Pilot Exit: /end_pilot, /export_pilot_data, /delete_pilot_memory, /disable_pilot_connectors",
    "Feedback: /feedback <useful|wrong|noisy|stale|missing_source|bad_draft|too_verbose> <item_id> [comment]",
    "Feedback Ledger: /feedback_ledger",
    "Daily Loop Outcome: /founder_outcome <loop_id> <outcome> [note]",
    "Suggestion Quality: /suggestion_quality",
    "Prep Quality: /prep_quality",
    "Brief: /brief, /suggest_brief, /gmail_thread <thread_id>",
    "Prep: /prep, /prep <suggestion_id>",
    "Suggestions: /suggestions, /suggestion_dismiss <suggestion_id>, /suggestion_snooze <suggestion_id>, /suggestion_memory <suggestion_id>, /suggestion_draft <suggestion_id>, /suggestion_followup <suggestion_id>",
    "Approvals: /approvals, /approve <approval_id>, /reject <approval_id>",
    "Drafts: /drafts, /draft_approve <draft_id>, /draft_reject <draft_id>, /draft_edit <draft_id> <text>, /draft_revise <draft_id> <revision>, /draft_expire <draft_id>, /export_text <confirmation_id>, /export_email <confirmation_id>, /export_file <confirmation_id>",
    "Usage: /usage",
    "Tasks: /inbox, /inbox_done <item_id>, /inbox_dismiss <item_id>",
    "Memory: /memory, /memory_review, /memory_pending, /memory_limits, /memory_approve <candidate_id>, /memory_reject <candidate_id>, /memory_edit <candidate_or_memory_id> <text>, /memory_forget <memory_id>, /memory_wrong <memory_id>, /memory_stale <memory_id>, /memory_duplicate <memory_id>, /memory_merge <memory_id> <target_memory_id>, /memory_never_use <memory_id>",
    "Documents: send a file for draft-only intake",
    "Setup Check: /status, /checkup, /setup",
)
NO_ACTION_TAKEN_LINE = "No external action was taken."
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
    document: TelegramDocumentIntakeMetadata | None = None


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
        reply_markup: dict[str, Any] | None = None,
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
        reply_markup: dict[str, Any] | None = None,
    ) -> dict:
        payload: dict[str, int | str] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup, sort_keys=True)
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
    document = _normalize_telegram_document_metadata(message.get("document"))
    if not isinstance(chat, dict) or not isinstance(sender, dict):
        return None
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")
    if not isinstance(chat_id, int) or not isinstance(telegram_user_id, int):
        return None
    update_id = update.get("update_id")
    message_id = message.get("message_id")
    if document is not None:
        raw_document_text = "[telegram document metadata]"
        return TelegramIncomingCommand(
            update_id=update_id if isinstance(update_id, int) else None,
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            message_id=message_id if isinstance(message_id, int) else None,
            command="/document",
            raw_text=raw_document_text,
            document=document,
        )
    if not isinstance(raw_text, str):
        return None
    stripped_text = raw_text.strip()
    if not stripped_text:
        return None
    command = normalize_telegram_command(stripped_text)
    if command is None:
        return None
    return TelegramIncomingCommand(
        update_id=update_id if isinstance(update_id, int) else None,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        message_id=message_id if isinstance(message_id, int) else None,
        command=command,
        raw_text=stripped_text,
        document=None,
    )


def _normalize_telegram_document_metadata(payload: object) -> TelegramDocumentIntakeMetadata | None:
    if not isinstance(payload, dict):
        return None
    file_id = payload.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        return None
    file_unique_id = payload.get("file_unique_id")
    file_name = payload.get("file_name")
    mime_type = payload.get("mime_type")
    file_size = payload.get("file_size")
    return TelegramDocumentIntakeMetadata(
        file_id=file_id.strip(),
        file_unique_id=file_unique_id.strip() if isinstance(file_unique_id, str) and file_unique_id.strip() else None,
        file_name=file_name.strip() if isinstance(file_name, str) and file_name.strip() else None,
        mime_type=mime_type.strip() if isinstance(mime_type, str) and mime_type.strip() else None,
        file_size=file_size if isinstance(file_size, int) else None,
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


def _suggestion_decision_choice_from_command(command: str) -> str:
    return {
        "/suggestion_dismiss": "dismiss",
        "/suggestion_snooze": "snooze",
        "/suggestion_memory": "save_memory",
        "/suggestion_draft": "create_draft",
        "/suggestion_followup": "ask_followup",
    }[command]


def _split_memory_edit_argument(argument: str) -> tuple[str, str]:
    parts = argument.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1].strip()


def _user_confirmation_choice_from_command(command: str) -> str:
    return {
        "/draft_approve": "approve",
        "/draft_reject": "reject",
        "/draft_edit": "edit",
        "/draft_expire": "expire",
    }[command]


def _approved_output_export_format_from_command(command: str) -> str:
    return {
        "/export_text": "text",
        "/export_email": "email_draft",
        "/export_file": "local_file",
    }[command]


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
            "Premium control shell",
            f"Robot: {config.robot_id}",
            "Access: owner-gated",
            "",
            *render_telegram_ux_sections(build_premium_telegram_home_sections()),
            "",
            "What needs setup:",
            "- Calendar reads need read-only Google setup.",
            "- Gmail is not connected to the task inbox yet.",
            "- Documents are draft-only until document intake is approved.",
            "",
            *render_compact_setup_capability_block(),
            "",
            "Approval boundaries:",
            *PRODUCT_APPROVAL_BOUNDARY_LINES,
            "",
            "Choose first useful action:",
            "- /today for your daily view",
            "- /prep for the next available meeting prep",
            "- /prep <suggestion_id> for a specific meeting prep",
            "- /pilot for the controlled customer pilot flow",
            "- /status for setup and capability status",
            "",
            NO_ACTION_TAKEN_LINE,
        ]
    )


def render_help_command_reply() -> str:
    return "\n".join(
        [
            "Roboticxs Command Center",
            "",
            *render_telegram_ux_sections(build_premium_telegram_help_sections()),
            "",
            "Skill gates:",
            *render_skill_runtime_manifest_summary(),
            "",
            "Notes:",
            "- Tasks is your robot task inbox, not your Gmail inbox yet.",
            "- Setup Check shows what is active, unavailable, blocked, or intentionally disabled.",
            "- Memory changes require approval.",
            "- Documents are metadata-only and draft-only right now.",
            "",
            "Approval boundaries:",
            *PRODUCT_APPROVAL_BOUNDARY_LINES,
            "",
            NO_ACTION_TAKEN_LINE,
        ]
    )


def render_menu_command_reply() -> str:
    return "\n".join(
        [
            "Roboticxs Menu",
            "",
            "Daily",
            "- /today - daily context",
            "- /prep - next meeting prep",
            "",
            "Work",
            "- /suggestions - pending suggestions",
            "- /approvals - outputs waiting for approval",
            "- /drafts - approval queue",
            "- /inbox - task inbox",
            "",
            "Memory",
            "- /memory - approved memory",
            "- /memory_review - pending memory decisions",
            "",
            "Documents",
            "- Send a document for draft-only intake",
            "",
            "Usage & setup",
            "- /usage - estimated usage",
            "- /status - setup and capabilities",
            "",
            "Boundaries",
            "- No sends.",
            "- No Calendar writes.",
            "- No Gmail writes.",
            "- Drafts and memory changes require approval.",
            "",
            "Use /help for the full command reference.",
            NO_ACTION_TAKEN_LINE,
        ]
    )


def build_menu_reply_markup() -> dict[str, object]:
    return {
        "keyboard": [
            [{"text": "/today"}, {"text": "/prep"}],
            [{"text": "/suggestions"}, {"text": "/approvals"}],
            [{"text": "/drafts"}, {"text": "/inbox"}],
            [{"text": "/memory"}, {"text": "Send a document"}],
            [{"text": "/usage"}, {"text": "/status"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "is_persistent": True,
        "input_field_placeholder": "Choose a Roboticxs action",
    }


def render_status_command_reply(config: TelegramRobotConfig) -> str:
    live_telegram_state = "disabled" if config.dry_run else "enabled"
    dev_mode_state = "enabled" if config.dev_mode else "disabled"
    readiness = build_live_connector_readiness_report(owner_id=config.owner_id, robot_id=config.robot_id)
    return "\n".join(
        [
            "Setup Check",
            "",
            f"Robot: {config.robot_id}",
            "Access: owner-gated",
            f"Telegram replies: {live_telegram_state}",
            f"Dev/sandbox mode: {dev_mode_state}",
            "",
            *render_telegram_ux_sections(
                build_premium_telegram_status_sections(
                    telegram_replies=live_telegram_state,
                    dev_mode=dev_mode_state,
                )
            ),
            "",
            *render_setup_capability_status_sections(),
            "",
            *render_compact_live_connector_readiness_block(readiness),
            "",
            *render_premium_shell_boundaries(),
            "",
            *render_skill_runtime_boundary_lines(),
            "",
            "Roadmap: 95P-191P closed, Premium Telegram UX Shell v0 active",
        ]
    )


def render_unknown_command_reply(skill_gate_decision_text: str | None = None) -> str:
    skill_gate_lines = [skill_gate_decision_text, ""] if skill_gate_decision_text else []
    return "\n".join(
        [
            "I do not know that command yet.",
            "",
            *skill_gate_lines,
            "Use /help to see the Roboticxs menu.",
            "",
            "Available areas:",
            *PRODUCT_MENU_LINES,
            "",
            NO_ACTION_TAKEN_LINE,
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
            NO_ACTION_TAKEN_LINE,
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


def resolve_prep_suggestion_id(
    *,
    requested_suggestion_id: str | None,
    suggestion_scan: ProactiveMeetingSuggestionScanRecord,
) -> str:
    normalized = (requested_suggestion_id or "").strip()
    if normalized:
        return normalized
    if suggestion_scan.status == "blocked_calendar_unavailable":
        return "calendar-unavailable"
    if suggestion_scan.suggestions:
        return suggestion_scan.suggestions[0].suggestion_id
    return ""


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
    meeting_prep_pack_v1: MeetingPrepPackV1Record | None = None,
    brief_memory_proposal: BriefMemoryProposalRecord | None = None,
    brief_memory_decision: BriefMemoryApprovalDecisionRecord | None = None,
    memory_review_inbox: MemoryReviewInbox | None = None,
    memory_approval_decision: MemoryApprovalTelegramReceipt | None = None,
    memory_edit_receipt: MemoryEditReceipt | None = None,
    memory_forget_receipt: MemoryForgetReceipt | None = None,
    memory_correction_receipt: MemoryCorrectionReceipt | None = None,
    document_intake: TelegramDocumentIntakeStubRecord | None = None,
    document_review_pack_v1: DocumentReviewPackV1Record | None = None,
    suggestion_inbox: SuggestionInbox | None = None,
    suggestion_decision: SuggestionDecisionReceipt | None = None,
    user_approved_output_queue: UserApprovedOutputQueue | None = None,
    user_approved_output_decision: UserApprovedOutputDecisionReceipt | None = None,
    action_draft_queue: ActionDraftQueue | None = None,
    user_confirmation: UserConfirmationReceipt | None = None,
    approved_output_export: ApprovedOutputExportRecord | None = None,
    approved_gmail_draft_creation: ApprovedGmailDraftCreationRecord | None = None,
    customer_mvp_demo_pack: object | None = None,
    controlled_live_pilot: ControlledLivePilotReceipt | None = None,
    customer_pilot_readiness_pack: CustomerPilotReadinessPack | None = None,
    customer_pilot_audit_gate: CustomerPilotAuditGateReport | None = None,
    live_smoke_script: LiveSmokeScript | None = None,
    pilot_metrics_snapshot: PilotMetricsSnapshot | None = None,
    friendly_user_onboarding_pack: FriendlyUserOnboardingPack | None = None,
    founder_to_friendly_pilot_baseline: FounderToFriendlyPilotBaseline | None = None,
    friendly_pilot_operator_console: FriendlyPilotOperatorConsole | None = None,
    friendly_pilot_invite_consent: FriendlyPilotInviteConsent | None = None,
    pilot_user_provisioning: PilotUserProvisioningRecord | None = None,
    pilot_user_allowlist: tuple[PilotUserProvisioningRecord, ...] = (),
    pilot_data_boundary: PilotDataBoundaryReport | None = None,
    pilot_onboarding_runbook: PilotOnboardingRunbook | None = None,
    pilot_support_issue: PilotSupportIssueReceipt | None = None,
    pilot_safety_incident_log: PilotSafetyIncidentLog | None = None,
    pilot_weekly_report: PilotWeeklyReport | None = None,
    pilot_exit_data_removal: PilotExitDataRemovalReceipt | None = None,
    friendly_pilot_launch_baseline: FriendlyPilotLaunchBaseline | None = None,
    first_friendly_user_activation: FirstFriendlyUserActivationReceipt | None = None,
    pilot_review_session_pack: PilotReviewSessionPack | None = None,
    pilot_learning_queue: PilotLearningQueue | None = None,
    founder_daily_use_loop: FounderDailyUseLoop | None = None,
    founder_feedback_capture: FounderFeedbackCaptureReceipt | None = None,
    feedback_ledger: FeedbackLedger | None = None,
    daily_loop_outcome: DailyLoopOutcomeRecord | None = None,
    suggestion_quality_tuning: SuggestionQualityTuningReport | None = None,
    prep_quality_tuning: PrepQualityTuningReport | None = None,
    draft_revision: DraftRevisionReceipt | None = None,
    live_connector_readiness: LiveConnectorReadinessReport | None = None,
    calendar_source_trace: CalendarContextSourceTrace | None = None,
    gmail_source_trace: GmailContextSourceTrace | None = None,
    source_trace_receipt: SourceTraceReceipt | None = None,
    smart_context_ranking: SmartContextRankingRecord | None = None,
    cross_source_daily_brief: CrossSourceDailyBriefRecord | None = None,
    gmail_thread_drilldown: GmailThreadDrilldownRecord | None = None,
    usage_ledger_entries: tuple[UsageCostLedgerEntry, ...] = (),
    fast_path_cache_entry: FastPathCacheEntry | None = None,
    fast_path_now_epoch_seconds: int | None = None,
) -> str:
    if fast_path_cache_entry is not None:
        return render_fast_path_cached_reply(
            fast_path_cache_entry,
            now_epoch_seconds=fast_path_now_epoch_seconds or int(time.time()),
        )
    if command == "/start":
        return render_start_command_reply(config)
    if command == "/help":
        return render_help_command_reply()
    if command == "/menu":
        return render_menu_command_reply()
    if command == "/status":
        return render_status_command_reply(config)
    if command in {"/checkup", "/setup"}:
        if live_connector_readiness is None:
            raise TelegramRobotConfigError("rejected_missing_live_connector_readiness")
        return render_live_connector_readiness_report(live_connector_readiness)
    if command == "/miss":
        return render_miss_command_reply(config)
    if command == "/today":
        if today_record is None:
            raise TelegramRobotConfigError("rejected_missing_today_command_record")
        reply = render_today_command(today_record)
        return append_calendar_source_trace(reply, calendar_source_trace) if calendar_source_trace else reply
    if command == "/daily_brief":
        if cross_source_daily_brief is None:
            raise TelegramRobotConfigError("rejected_missing_cross_source_daily_brief")
        reply = render_cross_source_daily_brief(cross_source_daily_brief)
        if smart_context_ranking is not None:
            reply = "\n\n".join([reply, render_smart_context_ranking(smart_context_ranking)])
        return append_source_trace_receipt(reply, source_trace_receipt) if source_trace_receipt else reply
    if command == "/demo":
        if customer_mvp_demo_pack is None:
            raise TelegramRobotConfigError("rejected_missing_customer_mvp_demo_pack")
        from app.customer_mvp_demo_pack_v1 import render_customer_mvp_demo_pack_v1

        return render_customer_mvp_demo_pack_v1(customer_mvp_demo_pack)
    if command == "/pilot":
        if controlled_live_pilot is None:
            raise TelegramRobotConfigError("rejected_missing_controlled_live_pilot")
        return render_controlled_live_pilot_receipt(controlled_live_pilot)
    if command == "/pilot_pack":
        if customer_pilot_readiness_pack is None:
            raise TelegramRobotConfigError("rejected_missing_customer_pilot_readiness_pack")
        return render_customer_pilot_readiness_pack(customer_pilot_readiness_pack)
    if command == "/pilot_audit":
        if customer_pilot_audit_gate is None:
            raise TelegramRobotConfigError("rejected_missing_customer_pilot_audit_gate")
        return render_customer_pilot_audit_gate(customer_pilot_audit_gate)
    if command == "/live_smoke":
        if live_smoke_script is None:
            raise TelegramRobotConfigError("rejected_missing_live_smoke_script")
        return render_live_smoke_script(live_smoke_script)
    if command == "/pilot_metrics":
        if pilot_metrics_snapshot is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_metrics_snapshot")
        return render_pilot_metrics_snapshot(pilot_metrics_snapshot)
    if command == "/friendly_onboarding":
        if friendly_user_onboarding_pack is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_user_onboarding_pack")
        return render_friendly_user_onboarding_pack(friendly_user_onboarding_pack)
    if command == "/friendly_pilot":
        if founder_to_friendly_pilot_baseline is None:
            raise TelegramRobotConfigError("rejected_missing_founder_to_friendly_pilot_baseline")
        return render_founder_to_friendly_pilot_baseline(founder_to_friendly_pilot_baseline)
    if command == "/pilot_users":
        if friendly_pilot_operator_console is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_operator_console")
        return render_pilot_users(friendly_pilot_operator_console)
    if command == "/pilot_user":
        if friendly_pilot_operator_console is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_operator_console")
        return render_pilot_user(friendly_pilot_operator_console)
    if command == "/pilot_health":
        if friendly_pilot_operator_console is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_operator_console")
        return render_pilot_health(friendly_pilot_operator_console)
    if command == "/pilot_invite":
        if friendly_pilot_invite_consent is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_invite_consent")
        return render_pilot_invite(friendly_pilot_invite_consent)
    if command == "/pilot_consent":
        if friendly_pilot_invite_consent is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_invite_consent")
        return render_pilot_consent(friendly_pilot_invite_consent)
    if command == "/pilot_provision":
        if pilot_user_provisioning is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_user_provisioning")
        return render_pilot_user_provisioning(pilot_user_provisioning)
    if command == "/pilot_allowlist":
        return render_pilot_allowlist(pilot_user_allowlist)
    if command == "/pilot_boundary":
        if pilot_data_boundary is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_data_boundary")
        return render_pilot_data_boundary(pilot_data_boundary)
    if command == "/pilot_runbook":
        if pilot_onboarding_runbook is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_onboarding_runbook")
        return render_pilot_onboarding_runbook(pilot_onboarding_runbook)
    if command in PILOT_ISSUE_COMMANDS:
        if pilot_support_issue is None:
            return render_pilot_issue_usage()
        return render_pilot_support_issue_receipt(pilot_support_issue)
    if command == "/pilot_safety":
        if pilot_safety_incident_log is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_safety_incident_log")
        return render_pilot_safety_incident_log(pilot_safety_incident_log)
    if command == "/pilot_weekly_report":
        if pilot_weekly_report is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_weekly_report")
        return render_pilot_weekly_report(pilot_weekly_report)
    if command in PILOT_EXIT_COMMANDS:
        if pilot_exit_data_removal is None:
            return render_pilot_exit_usage()
        return render_pilot_exit_data_removal_receipt(pilot_exit_data_removal)
    if command == "/pilot_launch":
        if friendly_pilot_launch_baseline is None:
            raise TelegramRobotConfigError("rejected_missing_friendly_pilot_launch_baseline")
        return render_friendly_pilot_launch_baseline(friendly_pilot_launch_baseline)
    if command == "/pilot_activate":
        if first_friendly_user_activation is None:
            raise TelegramRobotConfigError("rejected_missing_first_friendly_user_activation")
        return render_first_friendly_user_activation_receipt(first_friendly_user_activation)
    if command == "/pilot_review":
        if pilot_review_session_pack is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_review_session_pack")
        return render_pilot_review_session_pack(pilot_review_session_pack)
    if command == "/pilot_learnings":
        if pilot_learning_queue is None:
            raise TelegramRobotConfigError("rejected_missing_pilot_learning_queue")
        return render_pilot_learning_queue(pilot_learning_queue)
    if command == "/founder_loop":
        if founder_daily_use_loop is None:
            raise TelegramRobotConfigError("rejected_missing_founder_daily_use_loop")
        return render_founder_daily_use_loop(founder_daily_use_loop)
    if command == "/feedback":
        if founder_feedback_capture is None:
            return render_feedback_usage()
        return render_founder_feedback_capture_receipt(founder_feedback_capture)
    if command == "/feedback_ledger":
        if feedback_ledger is None:
            raise TelegramRobotConfigError("rejected_missing_feedback_ledger")
        return render_feedback_ledger(feedback_ledger)
    if command == "/founder_outcome":
        if daily_loop_outcome is None:
            return render_daily_loop_outcome_usage()
        return render_daily_loop_outcome_record(daily_loop_outcome)
    if command == "/suggestion_quality":
        if suggestion_quality_tuning is None:
            raise TelegramRobotConfigError("rejected_missing_suggestion_quality_tuning")
        return render_suggestion_quality_tuning_report(suggestion_quality_tuning)
    if command == "/prep_quality":
        if prep_quality_tuning is None:
            raise TelegramRobotConfigError("rejected_missing_prep_quality_tuning")
        return render_prep_quality_tuning_report(prep_quality_tuning)
    if command == "/draft_revise":
        if draft_revision is None:
            return render_draft_revision_usage()
        return render_draft_revision_receipt(draft_revision)
    if command == "/gmail_thread":
        if gmail_thread_drilldown is None:
            raise TelegramRobotConfigError("rejected_missing_gmail_thread_drilldown")
        return render_gmail_thread_drilldown(gmail_thread_drilldown)
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
        reply = (
            render_meeting_prep_pack_v1(meeting_prep_pack_v1)
            if meeting_prep_pack_v1 is not None
            else render_meeting_prep_pack(meeting_prep_pack)
        )
        if brief_memory_proposal is None:
            if smart_context_ranking is not None:
                reply = "\n\n".join([reply, render_smart_context_ranking(smart_context_ranking)])
            return append_source_trace_receipt(reply, source_trace_receipt) if source_trace_receipt else reply
        reply = "\n".join(
            [
                reply,
                "",
                *render_brief_memory_candidate_section(brief_memory_proposal),
            ]
        )
        if smart_context_ranking is not None:
            reply = "\n\n".join([reply, render_smart_context_ranking(smart_context_ranking)])
        return append_source_trace_receipt(reply, source_trace_receipt) if source_trace_receipt else reply
    if command == "/brief":
        if suggested_meeting_brief is not None:
            return render_requested_suggested_brief_reply(suggested_meeting_brief)
        return render_brief_command_reply(config, calendar_result=calendar_result)
    if command == "/suggest_brief":
        if proactive_meeting_suggestion is None:
            raise TelegramRobotConfigError("rejected_missing_proactive_meeting_suggestion")
        return render_suggest_brief_command_reply(proactive_meeting_suggestion)
    if command == "/suggestions":
        if suggestion_inbox is None:
            raise TelegramRobotConfigError("rejected_missing_suggestion_inbox")
        return render_suggestion_inbox(suggestion_inbox)
    if command in {
        "/suggestion_dismiss",
        "/suggestion_snooze",
        "/suggestion_memory",
        "/suggestion_draft",
        "/suggestion_followup",
    }:
        if suggestion_decision is None:
            raise TelegramRobotConfigError("rejected_missing_suggestion_decision")
        return render_suggestion_decision_receipt(suggestion_decision)
    if command == "/approvals":
        if user_approved_output_queue is None:
            raise TelegramRobotConfigError("rejected_missing_user_approved_output_queue")
        return render_user_approved_output_queue(user_approved_output_queue)
    if command in {"/approve", "/reject"}:
        if user_approved_output_decision is None:
            raise TelegramRobotConfigError("rejected_missing_user_approved_output_decision")
        return render_user_approved_output_decision_receipt(user_approved_output_decision)
    if command == "/drafts":
        if action_draft_queue is None:
            raise TelegramRobotConfigError("rejected_missing_action_draft_queue")
        return render_action_draft_queue(action_draft_queue)
    if command in {"/draft_approve", "/draft_reject", "/draft_edit", "/draft_expire"}:
        if user_confirmation is None:
            raise TelegramRobotConfigError("rejected_missing_user_confirmation")
        return render_user_confirmation_receipt(user_confirmation)
    if command == "/export_email":
        if approved_gmail_draft_creation is not None:
            return render_approved_gmail_draft_creation(approved_gmail_draft_creation)
        if approved_output_export is None:
            raise TelegramRobotConfigError("rejected_missing_approved_output_export")
        return render_approved_output_export(approved_output_export)
    if command in {"/export_text", "/export_email", "/export_file"}:
        if approved_output_export is None:
            raise TelegramRobotConfigError("rejected_missing_approved_output_export")
        return render_approved_output_export(approved_output_export)
    if command == "/usage":
        return render_usage_cost_ledger_summary(
            summarize_usage_cost_ledger(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                entries=usage_ledger_entries,
            )
        )
    if command == "/memory_review":
        if memory_review_inbox is None:
            raise TelegramRobotConfigError("rejected_missing_memory_review_inbox")
        return render_memory_review_inbox(memory_review_inbox)
    if command in {"/memory_approve", "/memory_reject"}:
        if memory_approval_decision is None:
            raise TelegramRobotConfigError("rejected_missing_memory_approval_decision")
        return render_memory_approval_telegram_receipt(memory_approval_decision)
    if command == "/memory_edit":
        if memory_edit_receipt is not None:
            return render_memory_edit_receipt(memory_edit_receipt)
        if memory_approval_decision is None:
            raise TelegramRobotConfigError("rejected_missing_memory_approval_decision")
        return render_memory_approval_telegram_receipt(memory_approval_decision)
    if command == "/memory_forget":
        if memory_forget_receipt is None:
            raise TelegramRobotConfigError("rejected_missing_memory_forget_receipt")
        return render_memory_forget_receipt(memory_forget_receipt)
    if command in MEMORY_CORRECTION_COMMANDS:
        if memory_correction_receipt is None:
            return render_memory_correction_usage()
        return render_memory_correction_receipt(memory_correction_receipt)
    if command == "/memory":
        return render_memory_command_reply(config, source_bundle=memory_source_bundle)
    if command == "/memory_limits":
        return render_memory_limits_reply(config, source_bundle=memory_source_bundle)
    if command == "/memory_pending":
        return render_memory_pending_reply(config, source_bundle=memory_source_bundle)
    if command == "/document":
        if document_review_pack_v1 is not None:
            return render_document_review_pack_v1(document_review_pack_v1)
        if document_intake is None:
            raise TelegramRobotConfigError("rejected_missing_document_intake")
        return render_telegram_document_intake_stub(document_intake)
    skill_gate_decision = classify_command_for_skill_gate(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        command=command,
        raw_text=command,
    )
    return render_unknown_command_reply(render_skill_runtime_gate_decision(skill_gate_decision))


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
    source_receipts = build_memory_source_receipts(
        owner_id=config.owner_id,
        robot_id=config.robot_id,
        source_bundle=source_bundle,
    )
    intelligence = build_memory_intelligence_report(snapshot)
    return "\n".join(
        [
            render_memory_center_command_reply(snapshot),
            "",
            render_memory_source_receipts(source_receipts),
            "",
            render_memory_intelligence_report(intelligence),
        ]
    )


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
    gmail_http_client: GmailReadonlyHttpClientProtocol | None = None,
    gmail_draft_http_client: GmailDraftHttpClientProtocol | None = None,
    memory_source_bundle: TelegramMemoryCenterSourceBundle | None = None,
    confirmation_receipts: tuple[UserConfirmationReceipt, ...] = (),
    document_extracted_text_by_file_id: dict[str, str] | None = None,
    usage_ledger_entries: tuple[UsageCostLedgerEntry, ...] = (),
    feedback_ledger_entries: tuple[FeedbackLedgerEntry, ...] = (),
    daily_loop_outcome_records: tuple[DailyLoopOutcomeRecord, ...] = (),
    friendly_pilot_users: tuple[FriendlyPilotUserStatus, ...] = (),
    pilot_boundary_items: tuple[PilotDataBoundaryItem, ...] = (),
    pilot_support_issues: tuple[PilotSupportIssueReceipt, ...] = (),
    pilot_safety_incidents: tuple[PilotSafetyIncident, ...] = (),
    draft_revision_receipts: tuple[DraftRevisionReceipt, ...] = (),
    memory_correction_receipts: tuple[MemoryCorrectionReceipt, ...] = (),
    approval_items: tuple[UserApprovedOutputItem, ...] = (),
    fast_path_cache_entries: tuple[FastPathCacheEntry, ...] = (),
    fast_path_now_epoch_seconds: int | None = None,
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
    gmail_thread_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/gmail_thread",
    )
    pilot_user_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/pilot_user",
    )
    pilot_consent_alias = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command if incoming_command.command in {"/pilot_invite", "/pilot_consent"} else "/pilot_invite",
    )
    pilot_provision_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/pilot_provision",
    )
    pilot_issue_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command if incoming_command.command in PILOT_ISSUE_COMMANDS else "/report_issue",
    )
    pilot_exit_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command if incoming_command.command in PILOT_EXIT_COMMANDS else "/end_pilot",
    )
    pilot_activation_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/pilot_activate",
    )
    pilot_review_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/pilot_review",
    )
    memory_approve_candidate_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_approve",
    )
    memory_reject_candidate_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_reject",
    )
    memory_edit_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_edit",
    )
    memory_forget_memory_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/memory_forget",
    )
    memory_correction_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command if incoming_command.command in MEMORY_CORRECTION_COMMANDS else "/memory_wrong",
    )
    inbox_done_item_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/inbox_done",
    )
    inbox_dismiss_item_id = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/inbox_dismiss",
    )
    suggestion_decision_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command,
    )
    approval_decision_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command,
    )
    user_confirmation_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command,
    )
    approved_output_export_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command=incoming_command.command,
    )
    feedback_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/feedback",
    )
    daily_loop_outcome_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/founder_outcome",
    )
    draft_revision_argument = extract_telegram_command_argument(
        incoming_command.raw_text,
        command="/draft_revise",
    )
    suggested_meeting_brief = None
    calendar_result = None
    proactive_meeting_suggestion = None
    cross_source_daily_brief = None
    gmail_thread_drilldown = None
    today_record = None
    open_loops_record = None
    personal_admin_inbox = None
    inbox_item_decision = None
    meeting_prep_pack = None
    meeting_prep_pack_v1 = None
    brief_memory_proposal = None
    brief_memory_decision = None
    memory_review_inbox = None
    memory_approval_decision = None
    memory_edit_receipt = None
    memory_forget_receipt = None
    memory_correction_receipt = None
    document_intake = None
    document_review_pack_v1 = None
    suggestion_inbox = None
    suggestion_decision = None
    user_approved_output_queue = None
    user_approved_output_decision = None
    action_draft_queue = None
    user_confirmation = None
    approved_output_export = None
    approved_gmail_draft_creation = None
    customer_mvp_demo_pack = None
    controlled_live_pilot = None
    customer_pilot_readiness_pack = None
    customer_pilot_audit_gate = None
    live_smoke_script = None
    pilot_metrics_snapshot = None
    friendly_user_onboarding_pack = None
    founder_to_friendly_pilot_baseline = None
    friendly_pilot_operator_console = None
    friendly_pilot_invite_consent = None
    pilot_user_provisioning = None
    pilot_user_allowlist: tuple[PilotUserProvisioningRecord, ...] = ()
    pilot_data_boundary = None
    pilot_onboarding_runbook = None
    pilot_support_issue = None
    pilot_safety_incident_log = None
    pilot_weekly_report = None
    pilot_exit_data_removal = None
    friendly_pilot_launch_baseline = None
    first_friendly_user_activation = None
    pilot_review_session_pack = None
    pilot_learning_queue = None
    founder_daily_use_loop = None
    founder_feedback_capture = None
    feedback_ledger = None
    daily_loop_outcome = None
    suggestion_quality_tuning = None
    prep_quality_tuning = None
    draft_revision = None
    live_connector_readiness = None
    calendar_source_trace = None
    gmail_source_trace = None
    source_trace_receipt = None
    smart_context_ranking = None
    memory_snapshot: TelegramMemoryCenterSnapshot | None = None
    cache_now = fast_path_now_epoch_seconds or int(time.time())
    fast_path_cache_entry = (
        find_fast_path_cache_entry(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            command=incoming_command.command,
            entries=fast_path_cache_entries,
            now_epoch_seconds=cache_now,
        )
        if authorized
        else None
    )
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
    if authorized and incoming_command.command == "/today" and fast_path_cache_entry is None:
        calendar_result = run_google_calendar_readonly_connector(
            http_client=calendar_http_client,
        )
        calendar_source_trace = build_calendar_context_source_trace(calendar_result=calendar_result)
        context_scan = build_calendar_context_scan_record(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_result=calendar_result,
        )
        suggestion_scan = build_proactive_meeting_suggestion_scan(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            context_scan=context_scan,
        )
        today_record = build_today_command_record(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestion_scan=suggestion_scan,
            memory_snapshot=build_memory_center_telegram_snapshot(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                source_bundle=memory_source_bundle,
            ),
        )
    if authorized and incoming_command.command == "/daily_brief":
        calendar_result = run_google_calendar_readonly_connector(
            http_client=calendar_http_client,
        )
        calendar_source_trace = build_calendar_context_source_trace(calendar_result=calendar_result)
        gmail_scan = run_gmail_readonly_context_scan(http_client=gmail_http_client)
        gmail_source_trace = build_gmail_context_source_trace(gmail_scan=gmail_scan)
        memory_snapshot = build_memory_center_telegram_snapshot(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            source_bundle=memory_source_bundle,
        )
        cross_source_daily_brief = build_cross_source_daily_brief(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_result=calendar_result,
            gmail_scan=gmail_scan,
            memory_snapshot=memory_snapshot,
            document_reviews=(),
        )
        source_trace_receipt = build_source_trace_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_trace=calendar_source_trace,
            gmail_trace=gmail_source_trace,
            memory_snapshot=memory_snapshot,
            document_reviews=(),
        )
        smart_context_ranking = build_smart_context_ranking(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_result=calendar_result,
            gmail_scan=gmail_scan,
            memory_snapshot=memory_snapshot,
            document_reviews=(),
        )
    if authorized and incoming_command.command == "/demo":
        from app.customer_mvp_demo_pack_v1 import build_customer_mvp_demo_pack_v1

        customer_mvp_demo_pack = build_customer_mvp_demo_pack_v1(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/pilot":
        controlled_live_pilot = build_controlled_live_pilot_baseline(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            gmail_draft_http_client=gmail_draft_http_client,
            usage_entries=usage_ledger_entries,
        )
    if authorized and incoming_command.command == "/pilot_pack":
        customer_pilot_readiness_pack = build_customer_pilot_readiness_pack(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/pilot_audit":
        customer_pilot_audit_gate = build_customer_pilot_audit_gate(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/live_smoke":
        live_smoke_script = build_live_smoke_script(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/pilot_metrics":
        pilot_metrics_snapshot = build_pilot_metrics_snapshot(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            feedback_entries=feedback_ledger_entries,
            outcome_records=daily_loop_outcome_records,
            usage_entries=usage_ledger_entries,
        )
    if authorized and incoming_command.command == "/friendly_onboarding":
        friendly_user_onboarding_pack = build_friendly_user_onboarding_pack(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/friendly_pilot":
        founder_to_friendly_pilot_baseline = build_founder_to_friendly_pilot_baseline(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command in {"/pilot_users", "/pilot_user", "/pilot_health"}:
        friendly_pilot_operator_console = build_friendly_pilot_operator_console(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            users=friendly_pilot_users,
            selected_user_id=pilot_user_id,
        )
    if authorized and incoming_command.command in {"/pilot_invite", "/pilot_consent"}:
        friendly_pilot_invite_consent = build_friendly_pilot_invite_consent(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            pilot_alias=pilot_consent_alias or "Friendly pilot",
        )
    if authorized and incoming_command.command in {"/pilot_provision", "/pilot_allowlist"}:
        allowed_telegram_user_id, pilot_alias = parse_pilot_provision_argument(
            pilot_provision_argument,
            fallback_telegram_user_id=incoming_command.telegram_user_id,
        )
        pilot_user_provisioning = build_pilot_user_provisioning_record(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            allowed_telegram_user_id=allowed_telegram_user_id,
            user_alias=pilot_alias,
            role="owner_founder" if allowed_telegram_user_id == incoming_command.telegram_user_id else "friendly_user",
            pilot_status="active_local" if allowed_telegram_user_id == incoming_command.telegram_user_id else "pending_consent",
        )
        pilot_user_allowlist = (pilot_user_provisioning,)
    if authorized and incoming_command.command == "/pilot_boundary":
        pilot_data_boundary = build_pilot_data_boundary_report(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            items=pilot_boundary_items,
        )
    if authorized and incoming_command.command == "/pilot_runbook":
        pilot_onboarding_runbook = build_pilot_onboarding_runbook(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command in PILOT_ISSUE_COMMANDS:
        issue_severity, issue_item_id, issue_comment = parse_pilot_issue_argument(pilot_issue_argument)
        try:
            pilot_support_issue = build_pilot_support_issue_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                pilot_user_id=str(incoming_command.telegram_user_id),
                command=incoming_command.command,
                severity=issue_severity,
                item_id=issue_item_id,
                comment=issue_comment,
            )
        except ValueError:
            pilot_support_issue = None
    if authorized and incoming_command.command == "/pilot_safety":
        pilot_safety_incident_log = build_pilot_safety_incident_log(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            incidents=pilot_safety_incidents,
        )
    if authorized and incoming_command.command == "/pilot_weekly_report":
        pilot_weekly_report = build_pilot_weekly_report(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            feedback_entries=feedback_ledger_entries,
            outcome_records=daily_loop_outcome_records,
            usage_entries=usage_ledger_entries,
            issue_receipts=pilot_support_issues,
            safety_incidents=pilot_safety_incidents,
            draft_revisions=draft_revision_receipts,
            memory_corrections=memory_correction_receipts,
        )
    if authorized and incoming_command.command in PILOT_EXIT_COMMANDS:
        exit_pilot_user_id, exit_scope = parse_pilot_exit_argument(
            pilot_exit_argument,
            fallback_pilot_user_id=str(incoming_command.telegram_user_id),
        )
        try:
            pilot_exit_data_removal = build_pilot_exit_data_removal_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                command=incoming_command.command,
                pilot_user_id=exit_pilot_user_id,
                requested_scope=exit_scope,
                pilot_users=friendly_pilot_users,
            )
        except ValueError:
            pilot_exit_data_removal = None
    if authorized and incoming_command.command == "/pilot_launch":
        friendly_pilot_launch_baseline = build_friendly_pilot_launch_baseline(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/pilot_activate":
        activation_pilot_user_id, activation_alias = parse_pilot_activation_argument(
            pilot_activation_argument,
            fallback_pilot_user_id=str(incoming_command.telegram_user_id),
        )
        first_friendly_user_activation = build_first_friendly_user_activation_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            pilot_alias=activation_alias,
            pilot_user_id=activation_pilot_user_id,
        )
    if authorized and incoming_command.command == "/pilot_review":
        review_pilot_user_id, review_alias = parse_pilot_review_argument(
            pilot_review_argument,
            fallback_pilot_user_id=str(incoming_command.telegram_user_id),
        )
        pilot_review_session_pack = build_pilot_review_session_pack(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            pilot_user_id=review_pilot_user_id,
            pilot_alias=review_alias,
            activation_receipts=(),
            feedback_entries=feedback_ledger_entries,
            outcome_records=daily_loop_outcome_records,
            issue_receipts=pilot_support_issues,
            safety_incidents=pilot_safety_incidents,
            usage_entries=usage_ledger_entries,
            draft_revisions=draft_revision_receipts,
            memory_corrections=memory_correction_receipts,
        )
    if authorized and incoming_command.command == "/pilot_learnings":
        pilot_learning_queue = build_pilot_learning_queue(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            feedback_entries=feedback_ledger_entries,
            issue_receipts=pilot_support_issues,
            safety_incidents=pilot_safety_incidents,
            usage_entries=usage_ledger_entries,
            review_packs=(),
        )
    if authorized and incoming_command.command == "/founder_loop":
        founder_daily_use_loop = build_founder_daily_use_loop(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/feedback":
        feedback_tag, feedback_item_id, feedback_comment = parse_feedback_argument(feedback_argument)
        try:
            founder_feedback_capture = build_founder_feedback_capture_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                tag=feedback_tag,
                item_id=feedback_item_id,
                comment=feedback_comment,
            )
        except ValueError:
            founder_feedback_capture = None
    if authorized and incoming_command.command == "/feedback_ledger":
        feedback_ledger = build_feedback_ledger(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            entries=feedback_ledger_entries,
        )
    if authorized and incoming_command.command == "/founder_outcome":
        loop_id, outcome, outcome_note = parse_daily_loop_outcome_argument(daily_loop_outcome_argument)
        try:
            daily_loop_outcome = build_daily_loop_outcome_record(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                loop_id=loop_id,
                outcome=outcome,
                note=outcome_note,
            )
        except ValueError:
            daily_loop_outcome = None
    if authorized and incoming_command.command == "/suggestion_quality":
        suggestion_quality_tuning = build_suggestion_quality_tuning_report(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            feedback_entries=feedback_ledger_entries,
            outcome_records=daily_loop_outcome_records,
        )
    if authorized and incoming_command.command == "/prep_quality":
        prep_quality_tuning = build_prep_quality_tuning_report(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            feedback_entries=feedback_ledger_entries,
        )
    if authorized and incoming_command.command == "/draft_revise":
        draft_id, revision_request = parse_draft_revision_argument(draft_revision_argument)
        try:
            draft_revision = build_draft_revision_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                draft_id=draft_id,
                revision_request=revision_request,
            )
        except ValueError:
            draft_revision = None
    if authorized and incoming_command.command in {"/checkup", "/setup"}:
        live_connector_readiness = build_live_connector_readiness_report(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
        )
    if authorized and incoming_command.command == "/gmail_thread":
        gmail_thread_drilldown = run_gmail_thread_drilldown(thread_id=gmail_thread_id or "")
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
        calendar_result = run_google_calendar_readonly_connector(
            http_client=calendar_http_client,
        )
        calendar_source_trace = build_calendar_context_source_trace(calendar_result=calendar_result)
        context_scan = build_calendar_context_scan_record(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_result=calendar_result,
        )
        suggestion_scan = build_proactive_meeting_suggestion_scan(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            context_scan=context_scan,
        )
        memory_snapshot = build_memory_center_telegram_snapshot(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            source_bundle=memory_source_bundle,
        )
        meeting_prep_pack = build_meeting_prep_pack(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestion_id=resolve_prep_suggestion_id(
                requested_suggestion_id=prep_suggestion_id,
                suggestion_scan=suggestion_scan,
            ),
            suggestion_scan=suggestion_scan,
            memory_snapshot=memory_snapshot,
        )
        meeting_prep_pack_v1 = build_meeting_prep_pack_v1(
            base_pack=meeting_prep_pack,
            gmail_scan=(gmail_scan := run_gmail_readonly_context_scan(http_client=gmail_http_client)),
            document_reviews=(),
        )
        gmail_source_trace = build_gmail_context_source_trace(gmail_scan=gmail_scan)
        source_trace_receipt = build_source_trace_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_trace=calendar_source_trace,
            gmail_trace=gmail_source_trace,
            memory_snapshot=memory_snapshot,
            document_reviews=(),
        )
        smart_context_ranking = build_smart_context_ranking(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            calendar_result=calendar_result,
            gmail_scan=gmail_scan,
            memory_snapshot=memory_snapshot,
            document_reviews=(),
        )
        brief_memory_proposal = build_brief_memory_proposal_record(prep_pack=meeting_prep_pack)
    if authorized and incoming_command.command in {"/memory_review", "/memory_approve", "/memory_reject", "/memory_edit"}:
        memory_review_inbox = build_memory_review_inbox(
            snapshot=build_memory_center_telegram_snapshot(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                source_bundle=memory_source_bundle,
            )
        )
    if authorized and incoming_command.command == "/memory_approve":
        memory_approval_decision = build_memory_approval_telegram_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            candidate_id=memory_approve_candidate_id or "",
            choice="approve",
            inbox=memory_review_inbox,
        )
    if authorized and incoming_command.command == "/memory_reject":
        memory_approval_decision = build_memory_approval_telegram_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            candidate_id=memory_reject_candidate_id or "",
            choice="reject",
            inbox=memory_review_inbox,
        )
    if authorized and incoming_command.command == "/memory_edit":
        edit_candidate_id, edit_text = _split_memory_edit_argument(memory_edit_argument or "")
        if memory_id_matches_visible_approved_memory(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            memory_id=edit_candidate_id,
            source_bundle=memory_source_bundle,
        ):
            memory_edit_receipt = build_memory_edit_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                memory_id=edit_candidate_id,
                proposed_text=edit_text,
                source_bundle=memory_source_bundle,
            )
        else:
            memory_approval_decision = build_memory_approval_telegram_receipt(
                owner_id=config.owner_id,
                robot_id=config.robot_id,
                candidate_id=edit_candidate_id,
                choice="edit",
                inbox=memory_review_inbox,
                edited_memory_text=edit_text,
            )
    if authorized and incoming_command.command == "/memory_forget":
        memory_forget_receipt = build_memory_forget_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            memory_id=memory_forget_memory_id or "",
            source_bundle=memory_source_bundle,
        )
    if authorized and incoming_command.command in MEMORY_CORRECTION_COMMANDS:
        correction_type = correction_type_from_command(incoming_command.command)
        memory_id, merge_target_memory_id = parse_memory_correction_argument(correction_type, memory_correction_argument)
        memory_correction_receipt = build_memory_correction_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            correction_type=correction_type,
            memory_id=memory_id,
            merge_target_memory_id=merge_target_memory_id,
            source_bundle=memory_source_bundle,
        )
    if authorized and incoming_command.command == "/document":
        if incoming_command.document is None:
            raise TelegramRobotConfigError("rejected_missing_document_metadata")
        document_intake = build_telegram_document_intake_stub_record(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            document=incoming_command.document,
        )
        extracted_text = (document_extracted_text_by_file_id or {}).get(incoming_command.document.file_id)
        if extracted_text is not None:
            document_review_pack_v1 = build_document_review_pack_v1_from_intake(
                intake_record=document_intake,
                extracted_text=extracted_text,
            )
    if authorized and incoming_command.command == "/suggestions":
        suggestion_inbox = build_suggestion_inbox(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestions=(),
        )
    if authorized and incoming_command.command in {
        "/suggestion_dismiss",
        "/suggestion_snooze",
        "/suggestion_memory",
        "/suggestion_draft",
        "/suggestion_followup",
    }:
        suggestion_inbox = build_suggestion_inbox(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestions=(),
        )
        suggestion_decision = build_suggestion_decision_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            suggestion_id=suggestion_decision_argument or "",
            choice=_suggestion_decision_choice_from_command(incoming_command.command),
            inbox=suggestion_inbox,
        )
    if authorized and incoming_command.command in {"/approvals", "/approve", "/reject"}:
        user_approved_output_queue = build_user_approved_output_queue(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            items=approval_items,
        )
    if authorized and incoming_command.command in {"/approve", "/reject"}:
        user_approved_output_decision = build_user_approved_output_decision_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            approval_id=approval_decision_argument or "",
            decision="approve" if incoming_command.command == "/approve" else "reject",
            queue=user_approved_output_queue,
        )
    if authorized and incoming_command.command == "/drafts":
        action_draft_queue = build_action_draft_queue(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            decisions=(),
        )
    if authorized and incoming_command.command in {"/draft_approve", "/draft_reject", "/draft_edit", "/draft_expire"}:
        action_draft_queue = build_action_draft_queue(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            decisions=(),
        )
        draft_id, edit_text = (
            _split_memory_edit_argument(user_confirmation_argument or "")
            if incoming_command.command == "/draft_edit"
            else (user_confirmation_argument or "", "")
        )
        user_confirmation = build_user_confirmation_receipt(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            draft_id=draft_id,
            choice=_user_confirmation_choice_from_command(incoming_command.command),
            queue=action_draft_queue,
            edited_text=edit_text,
        )
    if authorized and incoming_command.command == "/export_email":
        approved_gmail_draft_creation = build_approved_gmail_draft_creation(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            confirmation_id=approved_output_export_argument or "",
            confirmations=confirmation_receipts,
            http_client=gmail_draft_http_client,
        )
    if authorized and incoming_command.command in {"/export_text", "/export_file"}:
        approved_output_export = build_approved_output_export(
            owner_id=config.owner_id,
            robot_id=config.robot_id,
            confirmation_id=approved_output_export_argument or "",
            export_format=_approved_output_export_format_from_command(incoming_command.command),
            confirmations=confirmation_receipts,
        )
    if authorized:
        reply_text = render_command_reply(
            incoming_command.command,
            config,
            suggested_meeting_brief=suggested_meeting_brief,
            calendar_result=calendar_result,
            proactive_meeting_suggestion=proactive_meeting_suggestion,
            memory_source_bundle=memory_source_bundle,
            cross_source_daily_brief=cross_source_daily_brief,
            gmail_thread_drilldown=gmail_thread_drilldown,
            today_record=today_record,
            open_loops_record=open_loops_record,
            personal_admin_inbox=personal_admin_inbox,
            inbox_item_decision=inbox_item_decision,
            meeting_prep_pack=meeting_prep_pack,
            meeting_prep_pack_v1=meeting_prep_pack_v1,
            brief_memory_proposal=brief_memory_proposal,
            brief_memory_decision=brief_memory_decision,
            memory_review_inbox=memory_review_inbox,
            memory_approval_decision=memory_approval_decision,
            memory_edit_receipt=memory_edit_receipt,
            memory_forget_receipt=memory_forget_receipt,
            memory_correction_receipt=memory_correction_receipt,
            document_intake=document_intake,
            document_review_pack_v1=document_review_pack_v1,
            suggestion_inbox=suggestion_inbox,
            suggestion_decision=suggestion_decision,
            user_approved_output_queue=user_approved_output_queue,
            user_approved_output_decision=user_approved_output_decision,
            action_draft_queue=action_draft_queue,
            user_confirmation=user_confirmation,
            approved_output_export=approved_output_export,
            approved_gmail_draft_creation=approved_gmail_draft_creation,
            customer_mvp_demo_pack=customer_mvp_demo_pack,
            controlled_live_pilot=controlled_live_pilot,
            customer_pilot_readiness_pack=customer_pilot_readiness_pack,
            customer_pilot_audit_gate=customer_pilot_audit_gate,
            live_smoke_script=live_smoke_script,
            pilot_metrics_snapshot=pilot_metrics_snapshot,
            friendly_user_onboarding_pack=friendly_user_onboarding_pack,
            founder_to_friendly_pilot_baseline=founder_to_friendly_pilot_baseline,
            friendly_pilot_operator_console=friendly_pilot_operator_console,
            friendly_pilot_invite_consent=friendly_pilot_invite_consent,
            pilot_user_provisioning=pilot_user_provisioning,
            pilot_user_allowlist=pilot_user_allowlist,
            pilot_data_boundary=pilot_data_boundary,
            pilot_onboarding_runbook=pilot_onboarding_runbook,
            pilot_support_issue=pilot_support_issue,
            pilot_safety_incident_log=pilot_safety_incident_log,
            pilot_weekly_report=pilot_weekly_report,
            pilot_exit_data_removal=pilot_exit_data_removal,
            friendly_pilot_launch_baseline=friendly_pilot_launch_baseline,
            first_friendly_user_activation=first_friendly_user_activation,
            pilot_review_session_pack=pilot_review_session_pack,
            pilot_learning_queue=pilot_learning_queue,
            founder_daily_use_loop=founder_daily_use_loop,
            founder_feedback_capture=founder_feedback_capture,
            feedback_ledger=feedback_ledger,
            daily_loop_outcome=daily_loop_outcome,
            suggestion_quality_tuning=suggestion_quality_tuning,
            prep_quality_tuning=prep_quality_tuning,
            draft_revision=draft_revision,
            live_connector_readiness=live_connector_readiness,
            calendar_source_trace=calendar_source_trace,
            gmail_source_trace=gmail_source_trace,
            source_trace_receipt=source_trace_receipt,
            smart_context_ranking=smart_context_ranking,
            usage_ledger_entries=usage_ledger_entries,
            fast_path_cache_entry=fast_path_cache_entry,
            fast_path_now_epoch_seconds=cache_now,
        )
    else:
        reply_text = render_unauthorized_reply()
    reply_markup = (
        build_menu_reply_markup()
        if authorized and incoming_command.command == "/menu"
        else None
    )
    receipt = _send_telegram_reply(
        client=client,
        chat_id=incoming_command.chat_id,
        text=reply_text,
        reply_to_message_id=incoming_command.message_id,
        reply_markup=reply_markup,
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


def _send_telegram_reply(
    *,
    client: TelegramClientProtocol,
    chat_id: int,
    text: str,
    reply_to_message_id: int | None,
    reply_markup: dict[str, Any] | None = None,
) -> dict:
    if reply_markup is None:
        return client.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
    try:
        return client.send_message(
            chat_id,
            text,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
    except TypeError:
        return client.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)


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
            "Product menu: Today, Prep, Pilot, Suggestions, Approvals, Drafts, Memory, Documents, Usage, Status",
            "Available commands: /start, /help, /menu, /status, /checkup, /setup, /miss, /today, /daily_brief, /demo, /pilot, /pilot_pack, /pilot_audit, /live_smoke, /pilot_metrics, /pilot_weekly_report, /pilot_launch, /pilot_activate, /pilot_review, /pilot_learnings, /friendly_onboarding, /friendly_pilot, /pilot_users, /pilot_user, /pilot_health, /pilot_invite, /pilot_consent, /pilot_provision, /pilot_allowlist, /pilot_boundary, /pilot_runbook, /report_issue, /report_bug, /report_confusing, /report_wrong, /report_missing, /report_slow, /pilot_safety, /end_pilot, /export_pilot_data, /delete_pilot_memory, /disable_pilot_connectors, /founder_loop, /feedback, /feedback_ledger, /founder_outcome, /suggestion_quality, /prep_quality, /gmail_thread, /loops, /inbox, /inbox_done, /inbox_dismiss, /prep, /brief, /suggest_brief, /suggestions, /suggestion_dismiss, /suggestion_snooze, /suggestion_memory, /suggestion_draft, /suggestion_followup, /approvals, /approve, /reject, /drafts, /draft_approve, /draft_reject, /draft_edit, /draft_revise, /draft_expire, /export_text, /export_email, /export_file, /usage, /memory_review, /memory_approve, /memory_reject, /memory_edit, /memory_forget, /memory_wrong, /memory_stale, /memory_duplicate, /memory_merge, /memory_never_use, /memory, /memory_limits, /memory_pending, document upload",
            "External connectors: Google Calendar read-only optional",
            "Calendar writes: disabled",
            "LLM/model calls: disabled",
            "Tools: disabled",
            "Memory Center commands: /memory, /memory_review, /memory_limits, /memory_pending, /memory_forget",
            "Memory Center mutation: disabled",
            "Today command: /today owner-requested read-only summary only",
            "Cross-Source Daily Brief: /daily_brief owner-requested read-only brief only",
            "Customer MVP Demo Pack v1: /demo owner-requested local demo only",
            "Controlled Live Pilot Baseline: /pilot owner-requested controlled pilot receipt only",
            "Customer Pilot Readiness Pack: /pilot_pack owner-requested pilot setup pack only",
            "Customer Pilot Audit Gate: /pilot_audit owner-requested pilot audit report only",
            "Live Smoke Script: /live_smoke owner-requested manual smoke guide only",
            "Pilot Metrics Snapshot: /pilot_metrics shows local pilot metrics only",
            "Pilot Weekly Report: /pilot_weekly_report summarizes local weekly usage, feedback, issues, cost, safety, and product learnings only",
            "Friendly User Onboarding Pack: /friendly_onboarding shows 1-3 user pilot setup only",
            "Founder-to-Friendly Pilot Baseline: /friendly_pilot shows the controlled pilot baseline only",
            "Friendly Pilot Operator Console: /pilot_users, /pilot_user, and /pilot_health show local pilot status only",
            "Friendly Pilot Invite & Consent: /pilot_invite and /pilot_consent show local consent text without sending invites",
            "Pilot User Provisioning: /pilot_provision and /pilot_allowlist show strict local allowlist receipts only",
            "Pilot Data Boundary: /pilot_boundary shows local owner/robot scope checks only",
            "Pilot Onboarding Runbook: /pilot_runbook shows the local Day 0-Day 7 pilot execution guide only",
            "Pilot Support Issue Capture: /report_* creates local pilot issue receipts only",
            "Pilot Safety Incident Log: /pilot_safety shows local safety incidents only",
            "Pilot Exit / Data Removal: /end_pilot, /export_pilot_data, /delete_pilot_memory, and /disable_pilot_connectors create local exit receipts only",
            "Friendly Pilot Launch Baseline: /pilot_launch shows the controlled launch checklist only",
            "First Friendly User Activation: /pilot_activate creates a local activation receipt only",
            "Pilot Review Session Pack: /pilot_review summarizes local pilot session learnings only",
            "Pilot Learning Queue: /pilot_learnings shows prioritized local product learnings only",
            "Founder Daily Use Loop: /founder_loop owner-requested morning operating card only",
            "Founder Feedback Capture: /feedback creates local non-persistent feedback receipts only",
            "Feedback Ledger & Tags: /feedback_ledger shows local structured feedback entries only",
            "Daily Loop Outcome Tracker: /founder_outcome creates local outcome receipts only",
            "Suggestion Quality Tuning: /suggestion_quality shows local feedback-based ranking decisions only",
            "Prep Quality Tuning: /prep_quality shows local prep feedback tuning decisions only",
            "Premium Telegram UX Shell: grouped customer-facing control shell only",
            "Live Connector Readiness Check: /checkup owner-requested read-only readiness only",
            "Gmail Thread Drilldown: /gmail_thread <thread_id> owner-requested read-only metadata only",
            "Open Loops command: /loops owner-requested read-only unresolved loops only",
            "Personal Admin Inbox: /inbox owner-requested read-only pending items only",
            "Inbox Item Decisions: /inbox_done and /inbox_dismiss create local decision receipts only",
            "Meeting Prep Pack: /prep or /prep <suggestion_id> owner-requested read-only prep only",
            "Meeting Prep Pack v1: /prep includes read-only email/document context when locally available",
            "Brief Memory Proposals: shown in /prep as pending owner review only",
            "Memory Review Decisions: /memory_approve, /memory_reject, and /memory_edit create local decision receipts only",
            "Memory Source & Forget Receipts: /memory shows provenance and /memory_forget creates local receipts only",
            "Memory Correction Loop: /memory_wrong, /memory_stale, /memory_duplicate, /memory_merge, and /memory_never_use create local receipts only",
            "Document Intake: Telegram document metadata receives draft-only local replies only",
            "Proactive meeting suggestions: /suggest_brief owner-requested replies only",
            "Suggestion Inbox: /suggestions owner-requested local pending suggestions only",
            "Suggestion Decisions: /suggestion_* owner-requested local receipts only",
            "User-Approved Output Queue: /approvals, /approve, and /reject create local receipts only",
            "Action Draft Queue: /drafts owner-requested local approval candidates only",
            "User Confirmation Runtime: /draft_* creates local confirmation receipts only",
            "Draft Revision Loop: /draft_revise creates local revision candidates only",
            "Approved Output Export: /export_* creates local export payloads only",
            "Usage & Cost Ledger: /usage shows local estimated usage only",
            "Skill Manifest Runtime Gates: available for local command skill boundaries only",
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
