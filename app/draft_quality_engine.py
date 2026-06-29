from __future__ import annotations

from dataclasses import dataclass


DRAFT_QUALITY_ENGINE_STAGE = "195P"


@dataclass(frozen=True, slots=True)
class DraftQualityReview:
    stage: str
    draft_id: str
    intent: str
    audience: str
    tone: str
    source_basis: tuple[str, ...]
    risk_note: str
    approval_state: str
    expires_after: str
    editable_body: str
    no_external_action_taken: bool
    gmail_draft_created: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    model_call_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != DRAFT_QUALITY_ENGINE_STAGE:
            raise ValueError("195P draft quality reviews must identify the 195P stage.")
        if not self.draft_id or not self.intent or not self.audience or not self.tone:
            raise ValueError("195P draft quality reviews require intent, audience, and tone.")
        if not self.source_basis:
            raise ValueError("195P draft quality reviews require source basis.")
        if not self.no_external_action_taken:
            raise ValueError("195P draft quality reviews must not take action.")
        if any(
            (
                self.gmail_draft_created,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("195P draft quality reviews must not expand authority.")


def build_draft_quality_review(draft: object) -> DraftQualityReview:
    draft_type = str(getattr(draft, "draft_type", "draft"))
    title = str(getattr(draft, "title", "Draft"))
    preview = str(getattr(draft, "body_preview", ""))
    source_refs = tuple(
        value
        for value in (
            f"stage:{getattr(draft, 'source_stage', 'unknown')}",
            f"suggestion:{getattr(draft, 'source_suggestion_id', 'unknown')}",
            f"decision:{getattr(draft, 'source_decision_id', 'unknown')}",
        )
        if value
    )
    return DraftQualityReview(
        stage=DRAFT_QUALITY_ENGINE_STAGE,
        draft_id=str(getattr(draft, "draft_id", "")),
        intent=_intent(draft_type=draft_type, title=title),
        audience=_audience(title=title, preview=preview),
        tone=_tone(draft_type=draft_type),
        source_basis=source_refs,
        risk_note=_risk_note(preview=preview),
        approval_state=str(getattr(draft, "status", "pending_user_confirmation")),
        expires_after="current_review_session",
        editable_body=preview or "Editable draft body is pending owner review.",
        no_external_action_taken=True,
        gmail_draft_created=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        model_call_allowed=False,
        external_write_allowed=False,
    )


def render_draft_quality_review(review: DraftQualityReview) -> tuple[str, ...]:
    return (
        "  Quality:",
        f"    intent: {review.intent}",
        f"    audience: {review.audience}",
        f"    tone: {review.tone}",
        f"    sources: {', '.join(review.source_basis)}",
        f"    risk: {review.risk_note}",
        f"    approval: {review.approval_state}",
        f"    expires: {review.expires_after}",
        f"    editable body: {review.editable_body}",
    )


def _intent(*, draft_type: str, title: str) -> str:
    if draft_type in {"email_reply", "follow_up"}:
        return "follow_up_reply"
    if "meeting" in title.lower():
        return "meeting_note"
    return "task_update"


def _audience(*, title: str, preview: str) -> str:
    text = f"{title} {preview}".lower()
    if "client" in text or "customer" in text:
        return "external_client"
    if "team" in text:
        return "internal_team"
    return "recipient_from_source_context"


def _tone(*, draft_type: str) -> str:
    if draft_type in {"email_reply", "follow_up"}:
        return "concise_professional"
    return "clear_neutral"


def _risk_note(*, preview: str) -> str:
    lowered = preview.lower()
    if any(marker in lowered for marker in ("legal", "financial", "medical", "contract", "payment")):
        return "review_sensitive_claims_before_approval"
    return "low_risk_local_draft_pending_approval"
