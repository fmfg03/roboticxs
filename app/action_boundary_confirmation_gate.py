from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re


ACTION_BOUNDARY_CONFIRMATION_GATE_STAGE = "167P"
ACTION_BOUNDARY_DECISIONS = ("ALLOW", "DRAFT_ONLY", "ASK_CONFIRMATION", "ESCALATE", "BLOCK")
ALLOW_ACTION_TYPES = {
    "summarize",
    "prepare",
    "investigate",
    "classify",
    "list",
    "read_context",
    "review_local",
}
DRAFT_ONLY_ACTION_TYPES = {
    "draft",
    "draft_message",
    "draft_email",
    "draft_reply",
    "draft_document",
    "create_customer_facing_document",
    "prepare_proposal",
}
CONFIRMATION_ACTION_TYPES = {
    "send_message",
    "send_email",
    "schedule_event",
    "calendar_create",
    "calendar_update",
    "update_record",
    "publish_content",
    "external_write",
    "customer_facing_send",
}
ESCALATION_ACTION_TYPES = {
    "professional_review",
    "legal_review_request",
    "medical_review_request",
    "tax_review_request",
    "financial_review_request",
    "sensitive_review",
}
BLOCK_ACTION_TYPES = {
    "payment",
    "refund",
    "accept_terms",
    "sign_document",
    "legal_acceptance",
    "legal_decision",
    "medical_decision",
    "tax_decision",
    "financial_decision",
    "delete_data",
    "destructive_action",
    "deploy_production",
    "credential_change",
    "permission_change",
}
SENSITIVE_DECISION_PATTERN = re.compile(
    r"\b(legal|medical|tax|financial|investment|diagnos(?:e|is)|lawsuit|contract enforceable|"
    r"should i sign|pay|payment|refund|delete|destroy|deploy|credential|permission)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ActionBoundaryRequest:
    owner_id: str
    robot_id: str
    action_id: str
    action_type: str
    action_label: str
    target_surface: str = "telegram"
    risk_context: str = ""


@dataclass(frozen=True, slots=True)
class ActionBoundaryDecisionRecord:
    stage: str
    owner_id: str
    robot_id: str
    action_id: str
    action_type: str
    action_label: str
    target_surface: str
    decision: str
    reason_code: str
    safe_user_message: str
    allowed_next_step: str
    requires_confirmation: bool
    action_packet_required: bool
    draft_only: bool
    escalation_required: bool
    blocked: bool
    local_preparation_allowed: bool
    execution_authorized: bool
    external_write_allowed: bool
    connector_activation_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    memory_center_mutation_allowed: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    payment_allowed: bool
    destructive_action_allowed: bool
    professional_decision_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != ACTION_BOUNDARY_CONFIRMATION_GATE_STAGE:
            raise ValueError("167P action boundary decisions must identify the 167P stage.")
        if self.decision not in ACTION_BOUNDARY_DECISIONS:
            raise ValueError("167P action boundary decision is not recognized.")
        if any(
            (
                self.execution_authorized,
                self.external_write_allowed,
                self.connector_activation_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.memory_center_mutation_allowed,
                self.calendar_write_allowed,
                self.gmail_write_allowed,
                self.payment_allowed,
                self.destructive_action_allowed,
                self.professional_decision_allowed,
            )
        ):
            raise ValueError("167P action boundary decisions must not authorize execution or external authority.")
        if self.decision == "ASK_CONFIRMATION" and not self.action_packet_required:
            raise ValueError("167P confirmation decisions must require an action packet.")
        if self.decision == "DRAFT_ONLY" and not self.draft_only:
            raise ValueError("167P draft-only decisions must be marked draft-only.")
        if self.decision == "ESCALATE" and not self.escalation_required:
            raise ValueError("167P escalation decisions must require escalation.")
        if self.decision == "BLOCK" and not self.blocked:
            raise ValueError("167P blocked decisions must be marked blocked.")


def classify_action_boundary(
    *,
    owner_id: str,
    robot_id: str,
    action_id: str,
    action_type: str,
    action_label: str,
    target_surface: str = "telegram",
    risk_context: str = "",
) -> ActionBoundaryDecisionRecord:
    request = ActionBoundaryRequest(
        owner_id=owner_id,
        robot_id=robot_id,
        action_id=action_id,
        action_type=action_type,
        action_label=action_label,
        target_surface=target_surface,
        risk_context=risk_context,
    )
    return classify_action_boundary_request(request)


def classify_action_boundary_request(request: ActionBoundaryRequest) -> ActionBoundaryDecisionRecord:
    action_type = _normalize_action_type(request.action_type)
    searchable_text = " ".join((request.action_type, request.action_label, request.risk_context))
    if action_type in BLOCK_ACTION_TYPES or _looks_like_blocked_sensitive_decision(searchable_text):
        return _record(request, action_type, "BLOCK", "blocked_sensitive_or_destructive_action")
    if action_type in ESCALATION_ACTION_TYPES:
        return _record(request, action_type, "ESCALATE", "sensitive_review_requires_qualified_human")
    if action_type in CONFIRMATION_ACTION_TYPES:
        return _record(request, action_type, "ASK_CONFIRMATION", "external_change_requires_confirmation")
    if action_type in DRAFT_ONLY_ACTION_TYPES:
        return _record(request, action_type, "DRAFT_ONLY", "draft_output_only")
    if action_type in ALLOW_ACTION_TYPES:
        return _record(request, action_type, "ALLOW", "local_preparation_only")
    return _record(request, action_type, "ASK_CONFIRMATION", "unknown_action_requires_confirmation")


def render_action_boundary_decision(record: ActionBoundaryDecisionRecord) -> str:
    lines = [
        "Action Boundary",
        "",
        f"Stage: {record.stage}",
        f"Action: {record.action_label}",
        f"Action type: {record.action_type}",
        f"Decision: {record.decision}",
        f"Reason: {record.reason_code}",
        "",
        record.safe_user_message,
        f"Next step: {record.allowed_next_step}",
        "",
        "Decision labels: ALLOW, DRAFT_ONLY, ASK_CONFIRMATION, ESCALATE, BLOCK",
        "Action packet required: " + str(record.action_packet_required).lower(),
        "Confirmation required: " + str(record.requires_confirmation).lower(),
        "Draft only: " + str(record.draft_only).lower(),
        "Escalation required: " + str(record.escalation_required).lower(),
        "Blocked: " + str(record.blocked).lower(),
        "Execution authorized: false",
        "External writes: disabled",
        "Connector activation: disabled",
        "Model calls: disabled",
        "Tool calls: disabled",
        "Memory Center mutation: disabled",
        "Calendar writes: disabled",
        "Gmail writes: disabled",
        "Payments/destructive/professional decisions: disabled",
    ]
    return "\n".join(lines)


def _record(
    request: ActionBoundaryRequest,
    normalized_action_type: str,
    decision: str,
    reason_code: str,
) -> ActionBoundaryDecisionRecord:
    return ActionBoundaryDecisionRecord(
        stage=ACTION_BOUNDARY_CONFIRMATION_GATE_STAGE,
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        action_id=request.action_id,
        action_type=normalized_action_type,
        action_label=request.action_label,
        target_surface=request.target_surface,
        decision=decision,
        reason_code=reason_code,
        safe_user_message=_safe_user_message(decision),
        allowed_next_step=_allowed_next_step(decision),
        requires_confirmation=decision == "ASK_CONFIRMATION",
        action_packet_required=decision == "ASK_CONFIRMATION",
        draft_only=decision == "DRAFT_ONLY",
        escalation_required=decision == "ESCALATE",
        blocked=decision == "BLOCK",
        local_preparation_allowed=decision in {"ALLOW", "DRAFT_ONLY", "ASK_CONFIRMATION"},
        execution_authorized=False,
        external_write_allowed=False,
        connector_activation_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        memory_center_mutation_allowed=False,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        payment_allowed=False,
        destructive_action_allowed=False,
        professional_decision_allowed=False,
    )


def _safe_user_message(decision: str) -> str:
    if decision == "ALLOW":
        return "I can prepare this locally without taking external action."
    if decision == "DRAFT_ONLY":
        return "I can draft this for you, but I will not send, publish, sign, or accept it."
    if decision == "ASK_CONFIRMATION":
        return "I can prepare this, but I cannot send it or change anything without your confirmation."
    if decision == "ESCALATE":
        return "This needs a qualified human review before any decision or external action."
    return "I cannot do this action because it would cross a protected boundary."


def _allowed_next_step(decision: str) -> str:
    if decision == "ALLOW":
        return "Continue with local read-only preparation."
    if decision == "DRAFT_ONLY":
        return "Prepare a draft and ask the owner what to do next."
    if decision == "ASK_CONFIRMATION":
        return "Prepare an action packet for explicit owner confirmation."
    if decision == "ESCALATE":
        return "Escalate to a qualified human or ask the owner to narrow the request."
    return "Refuse the action and offer a safe draft or summary instead."


def _normalize_action_type(action_type: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", action_type.strip().lower()).strip("_") or "unknown"


def _looks_like_blocked_sensitive_decision(text: str) -> bool:
    lowered = text.lower()
    if "review" in lowered and any(word in lowered for word in ("legal", "medical", "tax", "financial")):
        return False
    return bool(SENSITIVE_DECISION_PATTERN.search(text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.action_boundary_confirmation_gate")
    parser.add_argument("action_type")
    parser.add_argument("action_label")
    parser.add_argument("--owner-id", default="local-owner")
    parser.add_argument("--robot-id", default="roboticxs-dev")
    parser.add_argument("--action-id", default="local-action")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = classify_action_boundary(
        owner_id=args.owner_id,
        robot_id=args.robot_id,
        action_id=args.action_id,
        action_type=args.action_type,
        action_label=args.action_label,
    )
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_action_boundary_decision(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
