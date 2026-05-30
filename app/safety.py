from __future__ import annotations


def detect_action_class(text: str) -> str:
    normalized = text.lower()
    if any(term in normalized for term in ["pay", "payment", "refund"]):
        return "PAY"
    if any(term in normalized for term in ["delete account", "close account"]):
        return "DELETE_ACCOUNT"
    if any(term in normalized for term in ["change password", "reset password", "credential", "permission"]):
        return "CHANGE_CREDENTIAL"
    if any(term in normalized for term in ["accept contract", "sign legally", "legal acceptance"]):
        return "LEGAL_ACCEPTANCE"
    if any(term in normalized for term in ["schedule", "book meeting", "arrange with"]):
        return "SCHEDULE_WITH_THIRD_PARTY"
    if any(term in normalized for term in ["send ", "email ", "message ", "notify "]):
        return "SEND_NOTIFY"
    if any(term in normalized for term in ["update crm", "write record", "update record"]):
        return "WRITE_EXTERNAL_RECORD"
    if any(term in normalized for term in ["legal advice", "medical advice", "tax advice"]):
        return "PROFESSIONAL_DECISION"
    if any(term in normalized for term in ["draft", "write", "prepare"]):
        return "DRAFT"
    if any(term in normalized for term in ["summary", "summarize"]):
        return "SUMMARIZE"
    return "PREPARE"


def evaluate_safety(text: str, scope_decision: str) -> dict[str, str]:
    action_class = detect_action_class(text)
    if scope_decision == "BLOCK":
        return {
            "action_class": action_class,
            "decision": "BLOCK",
            "reason_code": "OUT_OF_SCOPE_BLOCKED_ACTION",
            "user_message": "This action is blocked by your robot limits. I can help prepare a checklist or draft, but I cannot execute this action.",
        }
    if scope_decision == "REFUSE_SCOPE":
        return {
            "action_class": action_class,
            "decision": "ESCALATE",
            "reason_code": "PROFESSIONAL_ADVICE_NOT_AVAILABLE",
            "user_message": "I can help summarize context or draft questions, but I cannot provide legal, medical, or tax advice.",
        }
    if action_class in {"PAY", "DELETE_ACCOUNT", "CHANGE_CREDENTIAL", "LEGAL_ACCEPTANCE", "PROFESSIONAL_DECISION"}:
        return {
            "action_class": action_class,
            "decision": "BLOCK",
            "reason_code": "BLOCKED_HIGH_RISK_ACTION",
            "user_message": "This action is blocked by your robot limits. I can help prepare a checklist or draft, but I cannot execute this action.",
        }
    if action_class in {"SEND_NOTIFY", "WRITE_EXTERNAL_RECORD", "SCHEDULE_WITH_THIRD_PARTY"}:
        return {
            "action_class": action_class,
            "decision": "ASK_CONFIRMATION",
            "reason_code": "EXTERNAL_ACTION_REQUIRES_CONFIRMATION",
            "user_message": "I can draft this, but I need your confirmation before sending or changing anything externally.",
        }
    if action_class in {"DRAFT", "SUMMARIZE"}:
        return {
            "action_class": action_class,
            "decision": "DRAFT_ONLY",
            "reason_code": "SAFE_INTERNAL_PREPARATION",
            "user_message": "I can help with that. I prepared this as an internal draft step in the Stage 1 loop.",
        }
    return {
        "action_class": action_class,
        "decision": "ALLOW",
        "reason_code": "LOW_RISK_PREPARATION",
        "user_message": "I can help with that. For this Stage 1 loop, I recorded the task, checked scope and safety, selected an estimated model route, and logged estimated token usage.",
    }
