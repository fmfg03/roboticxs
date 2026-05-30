from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


COMMAND_PREFIXES = {
    "review document:": "REVIEW",
    "summarize document:": "SUMMARY",
    "mark risks in document:": "RISKS",
    "prepare notes from document:": "NOTES",
}

PROHIBITED_AUTHORITY_PHRASES = [
    "legally enforceable",
    "should i sign",
    "tax settlement",
    "certify this signature",
    "sign this document",
    "legal advice",
    "tax advice",
    "financial advice",
    "medical advice",
    "employment decision",
]

PREVIEW_LIMIT = 160


@dataclass(slots=True)
class DocumentReviewRequest:
    review_type: str
    source_text: str


def detect_document_review_command(text: str) -> DocumentReviewRequest | None:
    stripped = text.strip()
    lowered = stripped.lower()
    for prefix, review_type in COMMAND_PREFIXES.items():
        if lowered.startswith(prefix):
            source_text = stripped[len(prefix) :].strip()
            if source_text:
                return DocumentReviewRequest(review_type=review_type, source_text=source_text)
    return None


def is_prohibited_document_authority_request(source_text: str) -> bool:
    lowered = source_text.lower()
    return any(phrase in lowered for phrase in PROHIBITED_AUTHORITY_PHRASES)


def build_document_preview(source_text: str) -> str:
    compact = " ".join(source_text.split())
    if len(compact) <= PREVIEW_LIMIT:
        return compact
    return compact[: PREVIEW_LIMIT - 3].rstrip() + "..."


def build_document_hash(source_text: str) -> str:
    return sha256(source_text.encode("utf-8")).hexdigest()


def build_document_review_reply(*, review_type: str, source_text: str) -> str:
    summary = build_summary(source_text)
    risks = build_risk_notes(source_text)
    follow_ups = build_follow_up_questions(source_text)
    notes = build_notes(review_type, source_text)
    boundary = (
        "This is a draft document review, not legal, tax, financial, medical, or professional advice. "
        "I can help summarize and flag items for your review, but you must decide what to do next."
    )
    return (
        f"Summary: {summary}\n\n"
        f"Possible risk notes: {risks}\n\n"
        f"Suggested follow-up questions: {follow_ups}\n\n"
        f"Draft notes: {notes}\n\n"
        f"{boundary}"
    )


def build_document_refusal_reply() -> str:
    return (
        "I can provide a draft summary or flag items for your review, but I cannot tell you whether to sign, "
        "certify a signature, or provide legal, tax, financial, medical, or professional advice."
    )


def build_summary(source_text: str) -> str:
    text = " ".join(source_text.split())
    if len(text) <= 140:
        return text
    return text[:137].rstrip() + "..."


def build_risk_notes(source_text: str) -> str:
    lowered = source_text.lower()
    notes = []
    if any(term in lowered for term in ["must", "required", "obligation", "liable", "penalty", "termination"]):
        notes.append("Look closely at obligations, penalties, or termination language.")
    if any(term in lowered for term in ["confidential", "nda", "non-disclosure", "exclusive"]):
        notes.append("Check confidentiality or exclusivity terms carefully.")
    if any(term in lowered for term in ["deadline", "due date", "within", "days"]):
        notes.append("Confirm deadlines, notice periods, and response windows.")
    if not notes:
        notes.append("Review key obligations, dates, approvals, and any ambiguous language.")
    return " ".join(notes)


def build_follow_up_questions(source_text: str) -> str:
    lowered = source_text.lower()
    questions = [
        "Which obligations, deadlines, or approvals matter most here?",
        "Is any term unclear enough that it should be confirmed before action?",
    ]
    if any(term in lowered for term in ["payment", "fee", "price", "cost"]):
        questions.append("Are payment amounts, timing, and conditions explicit?")
    return " ".join(questions[:3])


def build_notes(review_type: str, source_text: str) -> str:
    if review_type == "SUMMARY":
        return "Use this as a meeting-ready summary and confirm the most important obligations and dates."
    if review_type == "RISKS":
        return "Focus first on clauses that create obligations, deadlines, penalties, approval dependencies, or ambiguity."
    if review_type == "NOTES":
        return "Prepare a checklist of obligations, dates, open questions, and any items that need confirmation."
    return "Review the summary, risk notes, and follow-up questions before deciding what to do next."
