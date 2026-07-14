from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.action_approval_control import parse_action_approval_command
from app.attention_control import is_attention_summary_command
from app.capability_control import is_capability_catalog_command, is_capability_query
from app.budget_policy import (
    is_budget_policy_reset_command,
    is_budget_status_command,
    parse_set_budget_block_threshold_command,
    parse_set_budget_limit_command,
    parse_set_budget_warn_threshold_command,
)
from app.document_control import is_list_documents_command, parse_forget_document_command
from app.document_review import detect_document_review_command
from app.file_intake_control import (
    is_file_retrieval_control_report_command,
    is_file_retrieval_control_summary_command,
    is_file_retrieval_enablement_request_command,
    is_file_retrieval_status_command,
    is_list_file_retrieval_enablement_request_history_command,
    is_list_files_command,
    is_list_pending_file_retrieval_enablement_requests_command,
    is_list_pending_file_retrievals_command,
    parse_cancel_file_retrieval_command,
    parse_forget_file_command,
    parse_resolve_file_retrieval_enablement_request_command,
    parse_retrieve_file_command,
)
from app.flows import (
    process_action_approval_packet,
    process_attention_summary,
    process_budget_block_threshold_update,
    process_budget_limit_update,
    process_capability_catalog,
    process_capability_query,
    process_budget_policy_reset,
    process_budget_status,
    process_budget_warn_threshold_update,
    process_document_forget,
    process_document_listing,
    process_document_review,
    process_file_forget,
    process_file_listing,
    process_file_retrieval_cancel,
    process_file_retrieval_control_report,
    process_file_retrieval_control_summary,
    process_file_retrieval_enablement_request,
    process_file_retrieval_enablement_request_history,
    process_file_retrieval_enablement_request_resolution,
    process_file_retrieval_policy_status,
    process_file_retrieval_preflight,
    process_memory_control_help,
    process_memory_decision,
    process_memory_forget,
    process_memory_listing,
    process_pending_file_retrieval_enablement_request_listing,
    process_pending_file_retrieval_listing,
    process_pending_memory_review,
    process_robot_folder,
    process_super_familiar,
    process_usage_spend,
    process_usage_tokens,
    process_web_preflight,
)
from app.memory_control import (
    is_list_memories_command,
    is_list_pending_memory_proposals_command,
    is_memory_control_help_request,
    parse_forget_command,
)
from app.memory_extraction import is_memory_approval_command
from app.robot_folder_control import is_robot_folder_command
from app.super_familiar_control import is_super_familiar_command
from app.usage_reporting import is_spend_command, is_token_usage_command
from app.web_preflight_control import is_web_preflight_command


FlowHandler = Callable[..., dict]
RouteMatcher = Callable[[str], dict | None]

@dataclass(frozen=True, slots=True)
class CommandRoute:
    name: str
    matcher: RouteMatcher
    handler: FlowHandler


def _match_flag(detector: Callable[[str], bool]) -> RouteMatcher:
    def matcher(text: str) -> dict | None:
        return {} if detector(text) else None

    return matcher


def _match_when(parser: Callable[[str], object | None]) -> RouteMatcher:
    def matcher(text: str) -> dict | None:
        return {} if parser(text) is not None else None

    return matcher


def _match_action_approval_command(text: str) -> dict | None:
    parsed = parse_action_approval_command(text)
    if parsed is None:
        return None
    return {
        "source_command": parsed.source_command,
        "requested_task": parsed.requested_task,
    }


def _match_file_retrieval_enablement_resolution(text: str) -> dict | None:
    parsed = parse_resolve_file_retrieval_enablement_request_command(text)
    if parsed is None:
        return None
    return {
        "request_id": parsed.request_id,
        "resolution": parsed.resolution,
    }


def _match_forget_file(text: str) -> dict | None:
    parsed = parse_forget_file_command(text)
    if parsed is None:
        return None
    return {"file_id": parsed.file_id}


def _match_cancel_file_retrieval(text: str) -> dict | None:
    parsed = parse_cancel_file_retrieval_command(text)
    if parsed is None:
        return None
    return {"retrieval_id": parsed.retrieval_id}


def _match_retrieve_file(text: str) -> dict | None:
    parsed = parse_retrieve_file_command(text)
    if parsed is None:
        return None
    return {
        "file_id": parsed.file_id,
        "request_kind": parsed.request_kind,
    }


def _match_forget_document(text: str) -> dict | None:
    parsed = parse_forget_document_command(text)
    if parsed is None:
        return None
    return {"document_id": parsed.document_id}


def _match_document_review(text: str) -> dict | None:
    parsed = detect_document_review_command(text)
    if parsed is None:
        return None
    return {
        "review_type": parsed.review_type,
        "source_text": parsed.source_text,
    }


def _match_forget_memory(text: str) -> dict | None:
    parsed = parse_forget_command(text)
    if parsed is None:
        return None
    return {"memory_id": parsed.memory_id}


def _match_memory_decision(text: str) -> dict | None:
    if not is_memory_approval_command(text):
        return None
    return {"command": text.strip().upper()}


REGISTERED_COMMAND_ROUTES: tuple[CommandRoute, ...] = (
    CommandRoute("action_approval_packet", _match_action_approval_command, process_action_approval_packet),
    CommandRoute("web_preflight", _match_flag(is_web_preflight_command), process_web_preflight),
    CommandRoute("capability_catalog", _match_flag(is_capability_catalog_command), process_capability_catalog),
    CommandRoute("capability_query", _match_flag(is_capability_query), process_capability_query),
    CommandRoute("attention_summary", _match_flag(is_attention_summary_command), process_attention_summary),
    CommandRoute("robot_folder", _match_flag(is_robot_folder_command), process_robot_folder),
    CommandRoute("super_familiar", _match_flag(is_super_familiar_command), process_super_familiar),
    CommandRoute("usage_spend", _match_flag(is_spend_command), process_usage_spend),
    CommandRoute("usage_tokens", _match_flag(is_token_usage_command), process_usage_tokens),
    CommandRoute("budget_status", _match_flag(is_budget_status_command), process_budget_status),
    CommandRoute("budget_policy_reset", _match_flag(is_budget_policy_reset_command), process_budget_policy_reset),
    CommandRoute("file_listing", _match_flag(is_list_files_command), process_file_listing),
    CommandRoute(
        "pending_file_retrievals",
        _match_flag(is_list_pending_file_retrievals_command),
        process_pending_file_retrieval_listing,
    ),
    CommandRoute(
        "pending_file_retrieval_enablement_requests",
        _match_flag(is_list_pending_file_retrieval_enablement_requests_command),
        process_pending_file_retrieval_enablement_request_listing,
    ),
    CommandRoute(
        "file_retrieval_enablement_request_history",
        _match_flag(is_list_file_retrieval_enablement_request_history_command),
        process_file_retrieval_enablement_request_history,
    ),
    CommandRoute(
        "file_retrieval_control_summary",
        _match_flag(is_file_retrieval_control_summary_command),
        process_file_retrieval_control_summary,
    ),
    CommandRoute(
        "file_retrieval_control_report",
        _match_flag(is_file_retrieval_control_report_command),
        process_file_retrieval_control_report,
    ),
    CommandRoute(
        "file_retrieval_policy_status",
        _match_flag(is_file_retrieval_status_command),
        process_file_retrieval_policy_status,
    ),
    CommandRoute(
        "file_retrieval_enablement_request",
        _match_flag(is_file_retrieval_enablement_request_command),
        process_file_retrieval_enablement_request,
    ),
    CommandRoute("budget_limit_update", _match_when(parse_set_budget_limit_command), process_budget_limit_update),
    CommandRoute(
        "budget_warn_threshold_update",
        _match_when(parse_set_budget_warn_threshold_command),
        process_budget_warn_threshold_update,
    ),
    CommandRoute(
        "budget_block_threshold_update",
        _match_when(parse_set_budget_block_threshold_command),
        process_budget_block_threshold_update,
    ),
    CommandRoute(
        "file_retrieval_enablement_resolution",
        _match_file_retrieval_enablement_resolution,
        process_file_retrieval_enablement_request_resolution,
    ),
    CommandRoute("file_forget", _match_forget_file, process_file_forget),
    CommandRoute("file_retrieval_cancel", _match_cancel_file_retrieval, process_file_retrieval_cancel),
    CommandRoute("file_retrieval_preflight", _match_retrieve_file, process_file_retrieval_preflight),
    CommandRoute("document_listing", _match_flag(is_list_documents_command), process_document_listing),
    CommandRoute("document_forget", _match_forget_document, process_document_forget),
    CommandRoute("document_review", _match_document_review, process_document_review),
    CommandRoute("memory_listing", _match_flag(is_list_memories_command), process_memory_listing),
    CommandRoute("memory_control_help", _match_flag(is_memory_control_help_request), process_memory_control_help),
    CommandRoute(
        "pending_memory_review",
        _match_flag(is_list_pending_memory_proposals_command),
        process_pending_memory_review,
    ),
    CommandRoute("memory_forget", _match_forget_memory, process_memory_forget),
    CommandRoute("memory_decision", _match_memory_decision, process_memory_decision),
)


def dispatch_registered_flow(*, context):
    text = context.envelope.text
    for route in REGISTERED_COMMAND_ROUTES:
        payload = route.matcher(text)
        if payload is not None:
            return route.handler(context=context, **payload)
    return None
