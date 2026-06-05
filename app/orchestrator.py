from __future__ import annotations

from app.action_approval_control import parse_action_approval_command
from app.attention_control import is_attention_summary_command
from app.capability_control import is_capability_catalog_command, is_capability_query
from app.document_control import is_list_documents_command, parse_forget_document_command
from app.document_review import detect_document_review_command
from app.command_registry import dispatch_registered_flow
from app.file_intake_control import (
    is_file_retrieval_enablement_request_command,
    parse_cancel_file_retrieval_command,
    parse_forget_file_command,
    parse_resolve_file_retrieval_enablement_request_command,
    parse_retrieve_file_command,
)
from app.flow_runtime import FlowContext, resolve_user_and_robot
from app.flows import (
    process_action_approval_packet,
    process_budget_block_threshold_update,
    process_budget_limit_update,
    process_budget_warn_threshold_update,
    process_document_forget,
    process_document_listing,
    process_document_review,
    process_file_forget,
    process_file_intake,
    process_file_retrieval_enablement_request,
    process_file_retrieval_enablement_request_resolution,
    process_file_retrieval_cancel,
    process_file_retrieval_preflight,
    process_general_task,
    process_memory_decision,
    process_memory_forget,
    process_memory_listing,
    process_memory_proposal,
    process_pending_memory_review,
)
from app.budget_policy import (
    parse_set_budget_block_threshold_command,
    parse_set_budget_limit_command,
    parse_set_budget_warn_threshold_command,
)
from app.memory_control import is_list_memories_command, is_list_pending_memory_proposals_command, parse_forget_command
from app.memory_extraction import detect_memory_intent, extract_proposed_memory, is_memory_approval_command
from app.skills import get_active_skill_manifest


def process_telegram_message(*, session, settings, envelope) -> dict:
    user, robot = resolve_user_and_robot(session=session, envelope=envelope)
    context = FlowContext(session=session, settings=settings, envelope=envelope, user=user, robot=robot)

    get_active_skill_manifest(session)

    routed = dispatch_registered_flow(context=context)
    if routed is not None:
        return routed

    approval_request = parse_action_approval_command(envelope.text)
    if approval_request is not None:
        return process_action_approval_packet(
            context=context,
            source_command=approval_request.source_command,
            requested_task=approval_request.requested_task,
        )

    if parse_set_budget_limit_command(envelope.text) is not None:
        return process_budget_limit_update(context=context)

    if parse_set_budget_warn_threshold_command(envelope.text) is not None:
        return process_budget_warn_threshold_update(context=context)

    if parse_set_budget_block_threshold_command(envelope.text) is not None:
        return process_budget_block_threshold_update(context=context)

    if is_file_retrieval_enablement_request_command(envelope.text):
        return process_file_retrieval_enablement_request(context=context)

    resolve_retrieval_enablement_request = parse_resolve_file_retrieval_enablement_request_command(envelope.text)
    if resolve_retrieval_enablement_request is not None:
        return process_file_retrieval_enablement_request_resolution(
            context=context,
            request_id=resolve_retrieval_enablement_request.request_id,
            resolution=resolve_retrieval_enablement_request.resolution,
        )

    forget_file_request = parse_forget_file_command(envelope.text)
    if forget_file_request is not None:
        return process_file_forget(context=context, file_id=forget_file_request.file_id)

    cancel_file_retrieval_request = parse_cancel_file_retrieval_command(envelope.text)
    if cancel_file_retrieval_request is not None:
        return process_file_retrieval_cancel(context=context, retrieval_id=cancel_file_retrieval_request.retrieval_id)

    retrieve_file_request = parse_retrieve_file_command(envelope.text)
    if retrieve_file_request is not None:
        return process_file_retrieval_preflight(
            context=context,
            file_id=retrieve_file_request.file_id,
            request_kind=retrieve_file_request.request_kind,
        )

    if envelope.document is not None:
        return process_file_intake(context=context)

    if is_list_documents_command(envelope.text):
        return process_document_listing(context=context)

    forget_document_request = parse_forget_document_command(envelope.text)
    if forget_document_request is not None:
        return process_document_forget(context=context, document_id=forget_document_request.document_id)

    document_request = detect_document_review_command(envelope.text)
    if document_request is not None:
        return process_document_review(
            context=context,
            review_type=document_request.review_type,
            source_text=document_request.source_text,
        )

    if is_list_memories_command(envelope.text):
        return process_memory_listing(context=context)

    if is_list_pending_memory_proposals_command(envelope.text):
        return process_pending_memory_review(context=context)

    forget_request = parse_forget_command(envelope.text)
    if forget_request is not None:
        return process_memory_forget(context=context, memory_id=forget_request.memory_id)

    if is_memory_approval_command(envelope.text):
        return process_memory_decision(context=context, command=envelope.text.strip().upper())

    if detect_memory_intent(envelope.text):
        proposal_payload = extract_proposed_memory(envelope.text)
        if proposal_payload is not None:
            return process_memory_proposal(context=context, proposal_payload=proposal_payload)

    return process_general_task(context=context)
