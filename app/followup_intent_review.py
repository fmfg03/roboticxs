from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import NAMESPACE_URL, uuid5

from app.telegram_result_acknowledgement import TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE, TelegramResultAcknowledgementRecord


FOLLOWUP_INTENT_REVIEW_STAGE = "107P"
FOLLOWUP_SOURCE_ACTION = "request_followup_pending"
FOLLOWUP_INTENT_STATUSES = frozenset({"pending_review", "duplicate", "blocked", "dismissed", "resolved_no_action"})
ALLOWED_STATUS_TRANSITIONS = {
    ("pending_review", "dismissed"),
    ("pending_review", "resolved_no_action"),
    ("blocked", "blocked"),
    ("duplicate", "duplicate"),
}


@dataclass(frozen=True, slots=True)
class FollowUpIntentReviewRecord:
    followup_intent_id: str
    acknowledgement_id: str
    delivery_id: str
    surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    source_action: str
    status: str
    review_summary: str
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in FOLLOWUP_INTENT_STATUSES:
            raise ValueError("Unsupported follow-up intent review status.")
        if self.status != "blocked" and self.source_action != FOLLOWUP_SOURCE_ACTION:
            raise ValueError("Only request_followup_pending can create a normal follow-up intent review record.")


@dataclass(frozen=True, slots=True)
class FollowUpIntentReviewResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("107P only supports local Telegram-compatible envelopes.")
        if self.send_allowed is not False:
            raise ValueError("107P follow-up intent envelopes must not authorize sending.")


@dataclass(slots=True)
class FollowUpIntentReviewQueue:
    records_by_id: dict[str, FollowUpIntentReviewRecord] = field(default_factory=dict)

    def get_record(self, followup_intent_id: str) -> FollowUpIntentReviewRecord | None:
        return self.records_by_id.get(followup_intent_id)

    def store(self, record: FollowUpIntentReviewRecord) -> FollowUpIntentReviewRecord:
        self.records_by_id[record.followup_intent_id] = record
        return record

    def list_records(self) -> tuple[FollowUpIntentReviewRecord, ...]:
        return tuple(self.records_by_id[key] for key in sorted(self.records_by_id))

    def list_pending(self) -> tuple[FollowUpIntentReviewRecord, ...]:
        return tuple(record for record in self.list_records() if record.status == "pending_review")

    def list_blocked(self) -> tuple[FollowUpIntentReviewRecord, ...]:
        return tuple(record for record in self.list_records() if record.status == "blocked")

    def list_resolved(self) -> tuple[FollowUpIntentReviewRecord, ...]:
        return tuple(record for record in self.list_records() if record.status in {"dismissed", "resolved_no_action"})

    def update_status(self, *, followup_intent_id: str, status: str) -> FollowUpIntentReviewRecord:
        record = self.get_record(followup_intent_id)
        if record is None:
            raise KeyError(f"Unknown follow-up intent review id: {followup_intent_id}")
        if (record.status, status) not in ALLOWED_STATUS_TRANSITIONS:
            raise ValueError("Follow-up intent review status transition is not allowed in 107P.")
        updated = replace(record, status=status)
        self.records_by_id[followup_intent_id] = updated
        return updated


def create_followup_intent_from_acknowledgement(
    *,
    acknowledgement_record: TelegramResultAcknowledgementRecord,
    queue: FollowUpIntentReviewQueue,
) -> FollowUpIntentReviewRecord:
    if not isinstance(acknowledgement_record, TelegramResultAcknowledgementRecord):
        raise TypeError("107P follow-up intent review requires a 106P TelegramResultAcknowledgementRecord.")

    followup_intent_id = _followup_intent_id(acknowledgement_record=acknowledgement_record)
    existing = queue.get_record(followup_intent_id)
    if existing is not None:
        return replace(existing, status="duplicate", rejection_reason="duplicate_followup_intent")

    rejection_reason = _validate_acknowledgement_source(acknowledgement_record=acknowledgement_record)
    if rejection_reason is not None:
        return queue.store(
            _blocked_record(
                acknowledgement_record=acknowledgement_record,
                rejection_reason=rejection_reason,
            )
        )

    return queue.store(
        FollowUpIntentReviewRecord(
            followup_intent_id=followup_intent_id,
            acknowledgement_id=acknowledgement_record.acknowledgement_id,
            delivery_id=acknowledgement_record.delivery_id,
            surface_id=acknowledgement_record.surface_id,
            inbox_record_id=acknowledgement_record.inbox_record_id,
            owner_id=acknowledgement_record.owner_id,
            robot_id=acknowledgement_record.robot_id,
            telegram_chat_id=acknowledgement_record.telegram_chat_id,
            source_action=acknowledgement_record.callback_action,
            status="pending_review",
            review_summary=_review_summary(acknowledgement_record=acknowledgement_record),
            lineage_summary=_followup_lineage_summary(acknowledgement_record=acknowledgement_record),
            rejection_reason=None,
        )
    )


def build_followup_intent_response_envelope(
    record: FollowUpIntentReviewRecord,
) -> FollowUpIntentReviewResponseEnvelope:
    text = "No pude registrar tu solicitud de seguimiento en esta version."
    if record.status in {"pending_review", "dismissed", "resolved_no_action", "duplicate"}:
        text = (
            "Registré tu solicitud de seguimiento. Todavía no ejecuté nada. "
            "El siguiente paso será revisar qué tipo de seguimiento quieres."
        )
    return FollowUpIntentReviewResponseEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=text,
        send_allowed=False,
    )


def _validate_acknowledgement_source(*, acknowledgement_record: TelegramResultAcknowledgementRecord) -> str | None:
    if acknowledgement_record.status == "blocked":
        return acknowledgement_record.rejection_reason or "rejected_blocked_acknowledgement_record"
    if acknowledgement_record.status != "recorded":
        return "rejected_non_recorded_acknowledgement_status"
    if acknowledgement_record.callback_action != FOLLOWUP_SOURCE_ACTION:
        return "rejected_non_followup_acknowledgement_action"
    if not acknowledgement_record.owner_id:
        return "rejected_missing_owner_id"
    if not acknowledgement_record.robot_id:
        return "rejected_missing_robot_id"
    if not acknowledgement_record.telegram_chat_id:
        return "rejected_missing_telegram_chat_id"
    if not acknowledgement_record.delivery_id:
        return "rejected_missing_delivery_id"
    if not acknowledgement_record.surface_id:
        return "rejected_missing_surface_id"
    if not acknowledgement_record.inbox_record_id:
        return "rejected_missing_inbox_record_id"

    lineage = acknowledgement_record.lineage_summary
    if not lineage:
        return "rejected_missing_lineage_summary"
    if lineage.get("acknowledgement_stage") != TELEGRAM_RESULT_ACKNOWLEDGEMENT_STAGE:
        return "rejected_unknown_acknowledgement_stage"
    if lineage.get("callback_action") != acknowledgement_record.callback_action:
        return "rejected_callback_action_lineage_mismatch"
    if lineage.get("delivery_id") != acknowledgement_record.delivery_id:
        return "rejected_delivery_mismatch"
    if lineage.get("surface_id") != acknowledgement_record.surface_id:
        return "rejected_surface_mismatch"
    if lineage.get("inbox_record_id") != acknowledgement_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    if lineage.get("owner_id") != acknowledgement_record.owner_id:
        return "rejected_owner_mismatch"
    if lineage.get("robot_id") != acknowledgement_record.robot_id:
        return "rejected_robot_mismatch"
    if lineage.get("telegram_chat_id") != acknowledgement_record.telegram_chat_id:
        return "rejected_chat_mismatch"
    upstream_lineage = lineage.get("upstream_lineage")
    if not isinstance(upstream_lineage, dict):
        return "rejected_missing_upstream_lineage"
    if upstream_lineage.get("delivery_stage") != "105P":
        return "rejected_missing_105p_delivery_lineage"
    return None


def _blocked_record(
    *,
    acknowledgement_record: TelegramResultAcknowledgementRecord,
    rejection_reason: str,
) -> FollowUpIntentReviewRecord:
    return FollowUpIntentReviewRecord(
        followup_intent_id=_followup_intent_id(acknowledgement_record=acknowledgement_record),
        acknowledgement_id=acknowledgement_record.acknowledgement_id,
        delivery_id=acknowledgement_record.delivery_id,
        surface_id=acknowledgement_record.surface_id,
        inbox_record_id=acknowledgement_record.inbox_record_id,
        owner_id=acknowledgement_record.owner_id,
        robot_id=acknowledgement_record.robot_id,
        telegram_chat_id=acknowledgement_record.telegram_chat_id,
        source_action=acknowledgement_record.callback_action,
        status="blocked",
        review_summary="La solicitud de seguimiento quedó bloqueada y no ejecutó ninguna acción.",
        lineage_summary=_followup_lineage_summary(acknowledgement_record=acknowledgement_record),
        rejection_reason=rejection_reason,
    )


def _review_summary(*, acknowledgement_record: TelegramResultAcknowledgementRecord) -> str:
    return (
        "El usuario pidió seguimiento sobre un resultado async entregado por Telegram. "
        "Este registro solo conserva la intención; no se ejecutó ninguna acción."
    )


def _followup_lineage_summary(
    *,
    acknowledgement_record: TelegramResultAcknowledgementRecord,
) -> dict[str, object]:
    acknowledgement_lineage = acknowledgement_record.lineage_summary
    delivery_lineage = acknowledgement_lineage.get("upstream_lineage")
    return {
        "followup_stage": FOLLOWUP_INTENT_REVIEW_STAGE,
        "acknowledgement_stage": acknowledgement_lineage.get("acknowledgement_stage"),
        "acknowledgement_id": acknowledgement_record.acknowledgement_id,
        "delivery_stage": acknowledgement_lineage.get("delivery_stage"),
        "delivery_id": acknowledgement_record.delivery_id,
        "surface_id": acknowledgement_record.surface_id,
        "inbox_record_id": acknowledgement_record.inbox_record_id,
        "owner_id": acknowledgement_record.owner_id,
        "robot_id": acknowledgement_record.robot_id,
        "telegram_chat_id": acknowledgement_record.telegram_chat_id,
        "source_action": acknowledgement_record.callback_action,
        "upstream_lineage": delivery_lineage,
    }


def _followup_intent_id(*, acknowledgement_record: TelegramResultAcknowledgementRecord) -> str:
    return "followup_intent_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                acknowledgement_record.acknowledgement_id,
                acknowledgement_record.delivery_id,
                acknowledgement_record.surface_id,
                acknowledgement_record.inbox_record_id,
                acknowledgement_record.owner_id,
                acknowledgement_record.robot_id,
                acknowledgement_record.telegram_chat_id,
                acknowledgement_record.callback_action,
            ]
        ),
    ).hex[:12]
