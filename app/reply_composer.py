from __future__ import annotations


def compose_reply_text(scope_decision: str, safety_result: dict[str, str]) -> str:
    if safety_result["decision"] in {"BLOCK", "ASK_CONFIRMATION", "ESCALATE"}:
        return safety_result["user_message"]
    if scope_decision == "CLARIFY":
        return "I can help with meeting prep, summaries, reminders, and drafting. Tell me the concrete task you want your robot to handle."
    return safety_result["user_message"]


def compose_reply_text_with_memory(scope_decision: str, safety_result: dict[str, str], memory_context_summary: str) -> str:
    base = compose_reply_text(scope_decision, safety_result)
    if not memory_context_summary or safety_result["decision"] in {"BLOCK", "ASK_CONFIRMATION", "ESCALATE"}:
        return base
    return f"{base} I used your saved {memory_context_summary} as context for this reply."


def compose_memory_proposal_reply(*, label: str, content: str) -> str:
    return f"I can remember this:\n\n{label}: {content}\n\nReply APPROVE to save it or REJECT to discard it."


def compose_memory_boundary_reply(content: str) -> str:
    return f"I can save this as a robot limit:\n\nBoundary: {content}\n\nReply APPROVE to save it or REJECT to discard it."


def compose_memory_approved_reply() -> str:
    return "Saved to your robot memory."


def compose_memory_rejected_reply() -> str:
    return "Discarded. I will not remember that."


def compose_no_pending_memory_reply() -> str:
    return "There is no pending memory to approve or reject right now."


def compose_memory_list_reply(memories: list[dict[str, str]]) -> str:
    if not memories:
        return "I do not have any approved memories for your robot yet."
    lines = ["Here is what I currently remember:", ""]
    for index, memory in enumerate(memories, start=1):
        lines.append(f"{index}. [{memory['id']}] {memory['label']}: {memory['content']}")
    lines.extend(["", f"To remove one, reply: forget memory {memories[0]['id']}"])
    return "\n".join(lines)


def compose_memory_forgotten_reply() -> str:
    return "Forgotten. I will no longer use that memory."


def compose_memory_not_found_reply() -> str:
    return "I could not find that active memory for your robot."


def compose_memory_needs_clearer_framing_reply() -> str:
    return "I cannot save that as memory in its current form. Rephrase it as a safe preference, profile fact, or robot limit."


def compose_document_refusal_reply() -> str:
    return (
        "I can provide a draft summary or flag items for your review, but I cannot tell you whether to sign, "
        "certify a signature, or provide legal, tax, financial, medical, or professional advice."
    )


def compose_document_list_reply(documents: list[dict[str, str]]) -> str:
    if not documents:
        return "I do not have any retained document-review records for your robot."
    lines = ["Here are the retained document-review records for your robot:", ""]
    for index, document in enumerate(documents, start=1):
        lines.append(
            f"{index}. [{document['id']}] {document['review_type']} | {document['status']} | "
            f"{document['created_at']} | {document['preview']}"
        )
    lines.extend(["", f"To remove one, reply: forget document {documents[0]['id']}"])
    return "\n".join(lines)


def compose_document_forgotten_reply() -> str:
    return "Forgotten. I will no longer retain that document-review record as active history."


def compose_document_not_found_reply() -> str:
    return "I could not find that active document-review record for your robot."


def compose_usage_empty_reply(kind: str) -> str:
    if kind == "spend":
        return "I do not have prior usage records for this robot yet. This report uses local estimated logs only, not live billing."
    return "I do not have prior token usage records for this robot yet. This report uses local estimated logs only."


def compose_spend_summary_reply(summary) -> str:
    lines = [
        "Local estimated spend summary:",
        f"- Total estimated cost (USD): ${summary.total_estimated_cost_usd:.6f}",
        f"- Total input tokens: {summary.total_input_tokens}",
        f"- Total output tokens: {summary.total_output_tokens}",
        f"- Total usage events: {summary.total_usage_events}",
    ]
    if summary.provider_model_breakdown:
        lines.extend(["", "Provider/model breakdown:"])
        for item in summary.provider_model_breakdown:
            lines.append(
                f"- {item['provider']} / {item['model']}: {item['events']} events | "
                f"in {item['input_tokens']} | out {item['output_tokens']} | est ${item['estimated_cost_usd']:.6f}"
            )
    if summary.highest_cost_routes:
        lines.extend(["", "Highest-cost local routes:"])
        for item in summary.highest_cost_routes:
            lines.append(
                f"- {item['task_family']} / {item['task_class']} | {item['provider']} / {item['model']} | "
                f"task {item['task_id']} | est ${item['estimated_cost_usd']:.6f}"
            )
    lines.extend(["", "This is a local estimate from robot logs only, not live billing or provider reconciliation."])
    return "\n".join(lines)


def compose_token_usage_summary_reply(summary) -> str:
    lines = [
        "Local token usage summary:",
        f"- Total input tokens: {summary.total_input_tokens}",
        f"- Total output tokens: {summary.total_output_tokens}",
        f"- Total tokens: {summary.total_tokens}",
        f"- Total usage events: {summary.total_usage_events}",
    ]
    if summary.provider_model_breakdown:
        lines.extend(["", "Provider/model breakdown:"])
        for item in summary.provider_model_breakdown:
            lines.append(
                f"- {item['provider']} / {item['model']}: {item['events']} events | "
                f"in {item['input_tokens']} | out {item['output_tokens']}"
            )
    if summary.task_family_breakdown:
        lines.extend(["", "Flow family breakdown:"])
        for item in summary.task_family_breakdown:
            lines.append(f"- {item['task_family']}: {item['events']} events")
    if summary.task_class_breakdown:
        lines.extend(["", "Task class breakdown:"])
        for item in summary.task_class_breakdown:
            lines.append(f"- {item['task_class']}: {item['events']} events")
    lines.extend(["", "This is local usage data only, derived from estimated robot logs."])
    return "\n".join(lines)


def compose_budget_status_reply(*, posture) -> str:
    return (
        f"Budget status: {posture.status}. "
        f"Local budget limit: ${posture.budget_limit_usd:.6f}. "
        f"Warn threshold: {posture.warn_threshold_percent}%. "
        f"Block threshold: {posture.block_threshold_percent}%. "
        f"Current local estimated spend: ${posture.current_estimated_spend_usd:.6f}. "
        f"Remaining local estimated budget: ${posture.remaining_estimated_budget_usd:.6f}. "
        f"Usage: {posture.usage_percentage:.2f}%. "
        "This is based on local estimates only, not live billing or provider reconciliation."
    )


def compose_budget_warn_prefix(*, posture) -> str:
    return (
        f"Budget warning: {posture.status}. "
        f"You have used about {posture.usage_percentage:.2f}% of your local estimated budget for this robot. "
        f"This task would project local estimated spend to ${posture.projected_estimated_spend_usd:.6f}. "
        "This is based on local estimates only, not live billing.\n\n"
    )


def compose_budget_block_reply(*, posture) -> str:
    return (
        "I cannot continue this task because your local estimated budget threshold has been reached. "
        f"Current local estimated spend is ${posture.current_estimated_spend_usd:.6f} "
        f"against a local budget limit of ${posture.budget_limit_usd:.6f}. "
        "You can still ask: show budget status or what did you spend. "
        "This is based on local estimates only, not live billing or provider reconciliation."
    )


def compose_budget_limit_updated_reply(*, amount: float) -> str:
    return (
        f"Budget limit updated for this robot: ${amount:.6f} local estimated spend.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_limit_invalid_reply() -> str:
    return "I could not set the budget limit. Use a positive amount such as: set budget limit 0.01 or set budget limit $0.01."


def compose_budget_warn_threshold_updated_reply(*, threshold_percent: int) -> str:
    return (
        f"Budget warn threshold updated for this robot: {threshold_percent}%.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_warn_threshold_invalid_reply() -> str:
    return (
        "I could not set the budget warn threshold. Use a whole percent above 0 and below the current block threshold, "
        "such as: set budget warn threshold 70 or set budget warn threshold 70%."
    )


def compose_budget_block_threshold_updated_reply(*, threshold_percent: int) -> str:
    return (
        f"Budget block threshold updated for this robot: {threshold_percent}%.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_block_threshold_invalid_reply() -> str:
    return (
        "I could not set the budget block threshold. Use a whole percent above 0, at most 100, and above the current warn "
        "threshold, such as: set budget block threshold 95 or set budget block threshold 95%."
    )


def compose_budget_policy_reset_reply() -> str:
    return (
        "Budget policy reset for this robot. It is now using the default local budget limit and default warn/block thresholds.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_file_retrieval_preflight_reply(*, request_kind: str, file_name: str) -> str:
    action = "retrieve" if request_kind == "RETRIEVE" else "prepare for review"
    return (
        f"I recorded your request to {action} {file_name}.\n\n"
        "File retrieval and content review are not enabled yet. I did not call Telegram getFile, did not download the file, parse it, OCR it, "
        "did not review it, or store file contents.\n\n"
        "This step only stored request/status metadata so your robot can track the preflight request."
    )


def compose_file_retrieval_not_found_reply() -> str:
    return "I could not find an active file metadata record with that ID for this robot."


def compose_pending_file_retrievals_reply(retrievals: list[dict[str, str]]) -> str:
    if not retrievals:
        return "I do not have any pending file retrieval requests for this robot."
    lines = ["Here are the pending file retrieval requests for this robot:", ""]
    for index, retrieval in enumerate(retrievals, start=1):
        lines.append(
            f"{index}. [{retrieval['id']}] {retrieval['request_kind']} | {retrieval['status']} | "
            f"{retrieval['file_name']} | {retrieval['created_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval is still not enabled. I have not called Telegram getFile, downloaded the file, parsed it, OCRed it, reviewed it, or stored file contents.",
            f"To cancel one, reply: cancel file retrieval {retrievals[0]['id']}",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_cancelled_reply() -> str:
    return "Cancelled. I will no longer keep that file retrieval request pending."


def compose_file_retrieval_cancel_not_found_reply() -> str:
    return "I could not find a pending file retrieval request with that ID for this robot."


def compose_file_retrieval_policy_status_reply(*, status: str, reason_code: str) -> str:
    return (
        f"File retrieval status: {status.lower()}.\n"
        f"Reason: {reason_code}.\n\n"
        "Live retrieval is not active. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, "
        "store raw bytes, store extracted text, or claim the file was reviewed."
    )


def compose_file_retrieval_enablement_request_reply(*, reason_code: str) -> str:
    return (
        "I recorded your request for file retrieval enablement.\n"
        "Retrieval remains disabled.\n"
        f"Reason: {reason_code}.\n\n"
        "Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, "
        "store extracted text, or claim the file was reviewed."
    )


def compose_pending_file_retrieval_enablement_requests_reply(requests: list[dict[str, str]]) -> str:
    if not requests:
        return "I do not have any pending retrieval enablement requests for this robot."
    lines = ["Here are the pending retrieval enablement requests for this robot:", ""]
    for index, request in enumerate(requests, start=1):
        lines.append(
            f"{index}. [{request['id']}] {request['status']} | {request['reason_code']} | {request['created_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
            f"To approve one, reply: approve retrieval enablement request {requests[0]['id']}",
            f"To reject one, reply: reject retrieval enablement request {requests[0]['id']}",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_enablement_request_history_reply(requests: list[dict[str, str]]) -> str:
    if not requests:
        return "I do not have any retrieval enablement request history for this robot."
    lines = ["Here is the retrieval enablement request history for this robot:", ""]
    for index, request in enumerate(requests, start=1):
        lines.append(
            f"{index}. [{request['id']}] {request['status']} | {request['reason_code']} | "
            f"created {request['created_at']} | updated {request['updated_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_control_summary_reply(
    *,
    policy_status: str,
    reason_code: str,
    pending_retrieval_intents_count: int,
    pending_enablement_requests_count: int,
    recent_enablement_request_outcomes: list[dict[str, str]],
) -> str:
    lines = [
        "Retrieval control summary:",
        f"- Retrieval policy: {policy_status}",
        f"- Reason: {reason_code}",
        f"- Pending file retrieval intents: {pending_retrieval_intents_count}",
        f"- Pending retrieval enablement requests: {pending_enablement_requests_count}",
    ]
    if recent_enablement_request_outcomes:
        lines.extend(["", "Recent retrieval enablement request outcomes:"])
        for item in recent_enablement_request_outcomes:
            lines.append(
                f"- [{item['id']}] {item['status']} | {item['reason_code']} | {item['updated_at']}"
            )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_control_report_reply(
    *,
    policy_status: str,
    reason_code: str,
    pending_retrieval_intents_count: int,
    pending_enablement_requests_count: int,
    recent_enablement_request_outcomes: list[dict[str, str]],
) -> str:
    lines = [
        "Retrieval control report:",
        f"- Retrieval policy: {policy_status}",
        f"- Reason: {reason_code}",
        f"- Pending file retrieval intents: {pending_retrieval_intents_count}",
        f"- Pending retrieval enablement requests: {pending_enablement_requests_count}",
    ]
    if recent_enablement_request_outcomes:
        lines.extend(["", "Recent retrieval enablement request outcomes:"])
        for item in recent_enablement_request_outcomes:
            lines.append(
                f"- [{item['id']}] {item['status']} | {item['reason_code']} | {item['updated_at']}"
            )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_enablement_request_resolved_reply(*, resolution: str) -> str:
    action = "approved" if resolution == "APPROVED_PENDING_POLICY_CHANGE" else "rejected"
    return (
        f"Retrieval enablement request {action}.\n"
        "Retrieval remains disabled.\n\n"
        "Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, "
        "store extracted text, or claim the file was reviewed."
    )


def compose_file_retrieval_enablement_request_not_found_reply() -> str:
    return "I could not find a pending retrieval enablement request with that ID for this robot."
