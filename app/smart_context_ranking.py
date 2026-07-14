from __future__ import annotations

from dataclasses import dataclass

from app.document_review_pack import DocumentReviewPackRecord
from app.gmail_readonly_context_scan import GmailReadonlyContextScanRecord
from app.google_calendar_readonly_connector import CalendarReadResult
from app.telegram_memory_center_commands import TelegramMemoryCenterSnapshot


SMART_CONTEXT_RANKING_STAGE = "193P"
MAX_RANKED_CONTEXT_ITEMS = 8


@dataclass(frozen=True, slots=True)
class RankedContextItem:
    source_type: str
    source_id: str
    title: str
    summary: str
    score: int
    reason_codes: tuple[str, ...]
    safe_next_action: str
    source_trace: str

    def __post_init__(self) -> None:
        if self.source_type not in {"calendar", "gmail", "memory", "document"}:
            raise ValueError("193P ranked context source type must be supported.")
        if not self.source_id.strip() or not self.title.strip() or not self.summary.strip():
            raise ValueError("193P ranked context items require id, title, and summary.")
        if not 0 <= self.score <= 100:
            raise ValueError("193P ranked context score must be between 0 and 100.")
        if not self.reason_codes or not self.source_trace.strip():
            raise ValueError("193P ranked context items require reasons and source trace.")


@dataclass(frozen=True, slots=True)
class SmartContextRankingRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    ranked_items: tuple[RankedContextItem, ...]
    calendar_read_used: bool
    gmail_read_used: bool
    memory_snapshot_used: bool
    document_context_used: bool
    read_only: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SMART_CONTEXT_RANKING_STAGE:
            raise ValueError("193P smart context ranking records must identify the 193P stage.")
        if not self.read_only:
            raise ValueError("193P smart context ranking must remain read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.gmail_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("193P smart context ranking must not expand authority.")


def build_smart_context_ranking(
    *,
    owner_id: str,
    robot_id: str,
    calendar_result: CalendarReadResult | None = None,
    gmail_scan: GmailReadonlyContextScanRecord | None = None,
    memory_snapshot: TelegramMemoryCenterSnapshot | None = None,
    document_reviews: tuple[DocumentReviewPackRecord, ...] = (),
) -> SmartContextRankingRecord:
    items = (
        *_calendar_items(calendar_result),
        *_gmail_items(gmail_scan),
        *_memory_items(memory_snapshot),
        *_document_items(document_reviews),
    )
    ranked = tuple(sorted(items, key=lambda item: (-item.score, item.source_type, item.source_id))[:MAX_RANKED_CONTEXT_ITEMS])
    return SmartContextRankingRecord(
        stage=SMART_CONTEXT_RANKING_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="ranked_context_available" if ranked else "ranked_context_empty",
        ranked_items=ranked,
        calendar_read_used=calendar_result is not None,
        gmail_read_used=gmail_scan is not None,
        memory_snapshot_used=memory_snapshot is not None,
        document_context_used=bool(document_reviews),
        read_only=True,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_smart_context_ranking(record: SmartContextRankingRecord) -> str:
    lines = [
        "Prioritized context",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        "Ranking: deterministic local score",
        "",
        "Top context:",
    ]
    if not record.ranked_items:
        lines.append("- No rankable context is available from current local sources.")
    else:
        for index, item in enumerate(record.ranked_items, start=1):
            lines.append(f"{index}. P{_priority_band(item.score)} | {item.source_type} | {item.title}")
            lines.append(f"   Score: {item.score}")
            lines.append(f"   Why: {', '.join(item.reason_codes)}")
            lines.append(f"   Source: {item.source_trace}")
            lines.append(f"   Next: {item.safe_next_action}")
    lines.extend(
        [
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Gmail writes: disabled",
            "Memory Center mutation: disabled",
            "Model/tool calls: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
        ]
    )
    return "\n".join(lines)


def _calendar_items(calendar_result: CalendarReadResult | None) -> tuple[RankedContextItem, ...]:
    if calendar_result is None or not calendar_result.ok:
        return ()
    return tuple(
        RankedContextItem(
            source_type="calendar",
            source_id=event.event_id,
            title=event.summary,
            summary=f"{event.start} - {event.end}",
            score=min(100, 70 + min(event.attendee_count, 10) + _keyword_score(event.summary, event.description_preview or "")),
            reason_codes=("meeting", "upcoming", *_keyword_reasons(event.summary, event.description_preview or "")),
            safe_next_action="Use /prep for read-only meeting preparation.",
            source_trace=f"calendar:{calendar_result.calendar_id}:{event.event_id}",
        )
        for event in calendar_result.events
    )


def _gmail_items(gmail_scan: GmailReadonlyContextScanRecord | None) -> tuple[RankedContextItem, ...]:
    if gmail_scan is None or gmail_scan.error_code:
        return ()
    return tuple(
        RankedContextItem(
            source_type="gmail",
            source_id=signal.signal_id,
            title=signal.signal_type,
            summary=signal.summary,
            score=62 + _keyword_score(signal.signal_type, signal.summary),
            reason_codes=("recent_email", signal.confidence, *_keyword_reasons(signal.signal_type, signal.summary)),
            safe_next_action="Review before creating any owner-approved draft.",
            source_trace=f"gmail:{signal.thread_id}:{signal.message_id}",
        )
        for signal in gmail_scan.signals
    )


def _memory_items(memory_snapshot: TelegramMemoryCenterSnapshot | None) -> tuple[RankedContextItem, ...]:
    if memory_snapshot is None:
        return ()
    return tuple(
        RankedContextItem(
            source_type="memory",
            source_id=memory.item_id,
            title=memory.memory_kind,
            summary=memory.summary,
            score=55 + _keyword_score(memory.memory_kind, memory.summary),
            reason_codes=("approved_memory", memory.sensitivity, *_keyword_reasons(memory.memory_kind, memory.summary)),
            safe_next_action="Use as context only; memory changes still require approval.",
            source_trace=f"memory:{memory.source}:{memory.item_id}",
        )
        for memory in memory_snapshot.approved_memories
    )


def _document_items(document_reviews: tuple[DocumentReviewPackRecord, ...]) -> tuple[RankedContextItem, ...]:
    return tuple(
        RankedContextItem(
            source_type="document",
            source_id=record.document_hash or record.document_title,
            title=record.document_title,
            summary=record.summary,
            score=58 + _keyword_score(record.document_title, record.summary, *record.possible_risk_notes),
            reason_codes=("document_review", "draft_only", *_keyword_reasons(record.document_title, record.summary, *record.possible_risk_notes)),
            safe_next_action=record.safe_next_step,
            source_trace=f"document:{record.source_stage}:{record.document_hash or 'no_hash'}",
        )
        for record in document_reviews
        if record.status == "completed_draft_review"
    )


def _keyword_score(*values: str) -> int:
    text = " ".join(values).lower()
    score = 0
    for marker, weight in (
        ("deadline", 12),
        ("urgent", 12),
        ("meeting", 8),
        ("follow", 8),
        ("proposal", 7),
        ("contract", 7),
        ("payment", 6),
        ("review", 5),
        ("demo", 5),
    ):
        if marker in text:
            score += weight
    return min(score, 25)


def _keyword_reasons(*values: str) -> tuple[str, ...]:
    text = " ".join(values).lower()
    reasons = []
    for marker, reason in (
        ("deadline", "deadline"),
        ("urgent", "urgent"),
        ("meeting", "meeting_related"),
        ("follow", "follow_up"),
        ("proposal", "proposal"),
        ("contract", "document_risk"),
        ("payment", "commercial_risk"),
        ("review", "review_needed"),
        ("demo", "customer_demo"),
    ):
        if marker in text:
            reasons.append(reason)
    return tuple(dict.fromkeys(reasons))


def _priority_band(score: int) -> int:
    if score >= 90:
        return 0
    if score >= 75:
        return 1
    if score >= 60:
        return 2
    return 3
