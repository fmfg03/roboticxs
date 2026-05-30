from __future__ import annotations


def decide_scope(text: str, manifest: dict) -> str:
    normalized = text.lower().strip()
    if not normalized:
        return "CLARIFY"

    blocked_action_terms = [
        "pay",
        "payment",
        "refund",
        "delete my account",
        "delete account",
        "close account",
        "change password",
        "reset password",
        "credential",
        "permission",
        "vendor bank",
    ]
    if any(term in normalized for term in blocked_action_terms):
        return "BLOCK"

    refused_topics = ["legal advice", "medical advice", "tax advice", "lawsuit", "diagnose", "prescription"]
    if any(term in normalized for term in refused_topics):
        return "REFUSE_SCOPE"

    answer_terms = [
        "meeting",
        "prepare",
        "summary",
        "summarize",
        "draft",
        "write",
        "remind",
        "follow up",
        "todo",
        "task",
    ]
    if any(term in normalized for term in answer_terms):
        return "ANSWER"

    if len(normalized.split()) <= 2:
        return "CLARIFY"

    allowed_topics = " ".join(manifest.get("allowed_topics", [])).lower()
    if any(term in allowed_topics for term in normalized.split()):
        return "ANSWER"

    return "CLARIFY"
