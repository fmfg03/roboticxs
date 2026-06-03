from __future__ import annotations

from collections.abc import Callable

from app.action_approval_control import is_action_approval_command
from app.attention_control import is_attention_summary_command
from app.capability_control import is_capability_catalog_command, is_capability_query
from app.budget_policy import is_budget_policy_reset_command, is_budget_status_command
from app.file_intake_control import (
    is_file_retrieval_control_report_command,
    is_file_retrieval_control_summary_command,
    is_file_retrieval_enablement_request_command,
    is_file_retrieval_status_command,
    is_list_file_retrieval_enablement_request_history_command,
    is_list_files_command,
    is_list_pending_file_retrieval_enablement_requests_command,
    is_list_pending_file_retrievals_command,
)
from app.flows import (
    process_action_approval_packet,
    process_attention_summary,
    process_capability_catalog,
    process_capability_query,
    process_budget_policy_reset,
    process_budget_status,
    process_file_listing,
    process_file_retrieval_control_report,
    process_file_retrieval_control_summary,
    process_file_retrieval_enablement_request,
    process_file_retrieval_enablement_request_history,
    process_file_retrieval_policy_status,
    process_pending_file_retrieval_enablement_request_listing,
    process_pending_file_retrieval_listing,
    process_robot_folder,
    process_super_familiar,
    process_usage_spend,
    process_usage_tokens,
    process_web_preflight,
)
from app.robot_folder_control import is_robot_folder_command
from app.super_familiar_control import is_super_familiar_command
from app.usage_reporting import is_spend_command, is_token_usage_command
from app.web_preflight_control import is_web_preflight_command


FlowHandler = Callable[..., dict]


REGISTERED_COMMAND_ROUTES: tuple[tuple[Callable[[str], bool], FlowHandler], ...] = (
    (is_action_approval_command, process_action_approval_packet),
    (is_web_preflight_command, process_web_preflight),
    (is_capability_catalog_command, process_capability_catalog),
    (is_capability_query, process_capability_query),
    (is_attention_summary_command, process_attention_summary),
    (is_robot_folder_command, process_robot_folder),
    (is_super_familiar_command, process_super_familiar),
    (is_spend_command, process_usage_spend),
    (is_token_usage_command, process_usage_tokens),
    (is_budget_status_command, process_budget_status),
    (is_budget_policy_reset_command, process_budget_policy_reset),
    (is_list_files_command, process_file_listing),
    (is_list_pending_file_retrievals_command, process_pending_file_retrieval_listing),
    (is_list_pending_file_retrieval_enablement_requests_command, process_pending_file_retrieval_enablement_request_listing),
    (is_list_file_retrieval_enablement_request_history_command, process_file_retrieval_enablement_request_history),
    (is_file_retrieval_control_summary_command, process_file_retrieval_control_summary),
    (is_file_retrieval_control_report_command, process_file_retrieval_control_report),
    (is_file_retrieval_status_command, process_file_retrieval_policy_status),
    (is_file_retrieval_enablement_request_command, process_file_retrieval_enablement_request),
)


def dispatch_registered_flow(*, context):
    text = context.envelope.text
    for detector, handler in REGISTERED_COMMAND_ROUTES:
        if detector(text):
            if handler is process_action_approval_packet:
                return handler(context=context, source_command=text.strip(), requested_task="")
            return handler(context=context)
    return None
