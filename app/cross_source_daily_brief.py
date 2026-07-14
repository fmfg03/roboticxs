from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.document_review_pack import DocumentReviewPackRecord
from app.gmail_readonly_context_scan import GmailReadonlyContextScanRecord
from app.google_calendar_readonly_connector import CalendarReadResult
from app.telegram_memory_center_commands import TelegramMemoryCenterSnapshot


CROSS_SOURCE_DAILY_BRIEF_STAGE = "174P"


@dataclass(frozen=True, slots=True)
class CrossSourceDailyBriefRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    meeting_lines: tuple[str, ...]
    email_context_lines: tuple[str, ...]
    memory_context_lines: tuple[str, ...]
    document_lines: tuple[str, ...]
    open_loop_lines: tuple[str, ...]
    suggested_next_action: str
    blocked_source_lines: tuple[str, ...]
    read_only: bool
    calendar_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    memory_store_written: bool
    memory_center_mutated: bool
    draft_created: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    scheduler_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CROSS_SOURCE_DAILY_BRIEF_STAGE:
            raise ValueError("174P cross-source daily briefs must identify the 174P stage.")
        if not self.read_only:
            raise ValueError("174P cross-source daily briefs must remain read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.memory_store_written,
                self.memory_center_mutated,
                self.draft_created,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.scheduler_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("174P cross-source daily briefs must not expand authority.")


def build_cross_source_daily_brief(
    *,
    owner_id: str,
    robot_id: str,
    calendar_result: CalendarReadResult | None = None,
    gmail_scan: GmailReadonlyContextScanRecord | None = None,
    memory_snapshot: TelegramMemoryCenterSnapshot | None = None,
    document_reviews: tuple[DocumentReviewPackRecord, ...] = (),
) -> CrossSourceDailyBriefRecord:
    meeting_lines, calendar_blocked = _meeting_lines(calendar_result)
    email_lines, gmail_blocked = _email_context_lines(gmail_scan)
    memory_lines, memory_blocked = _memory_context_lines(memory_snapshot)
    document_lines, document_blocked = _document_lines(document_reviews)
    blocked_lines = tuple(
        line
        for group in (calendar_blocked, gmail_blocked, memory_blocked, document_blocked)
        for line in group
    )
    open_loop_lines = _open_loop_lines(
        meeting_lines=meeting_lines,
        email_lines=email_lines,
        memory_lines=memory_lines,
        document_lines=document_lines,
        blocked_lines=blocked_lines,
    )
    status = "completed_with_context"
    if not any((meeting_lines, email_lines, memory_lines, document_lines)):
        status = "completed_empty_sources"
    elif blocked_lines:
        status = "completed_with_blocked_sources"
    return CrossSourceDailyBriefRecord(
        stage=CROSS_SOURCE_DAILY_BRIEF_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=status,
        meeting_lines=meeting_lines,
        email_context_lines=email_lines,
        memory_context_lines=memory_lines,
        document_lines=document_lines,
        open_loop_lines=open_loop_lines,
        suggested_next_action=_suggested_next_action(open_loop_lines=open_loop_lines, blocked_lines=blocked_lines),
        blocked_source_lines=blocked_lines,
        read_only=True,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        memory_store_written=False,
        memory_center_mutated=False,
        draft_created=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        scheduler_allowed=False,
        external_write_allowed=False,
    )


def render_cross_source_daily_brief(record: CrossSourceDailyBriefRecord) -> str:
    return "\n".join(
        [
            "Daily Brief",
            "",
            f"Stage: {record.stage}",
            f"Status: {record.status}",
            "",
            "Meetings:",
            *_section_lines(record.meeting_lines, "No Calendar meetings are visible in this local brief."),
            "",
            "Email context:",
            *_section_lines(record.email_context_lines, "No Gmail context signals are visible in this local brief."),
            "",
            "Memory context:",
            *_section_lines(record.memory_context_lines, "No approved memory context is visible in this local brief."),
            "",
            "Documents:",
            *_section_lines(record.document_lines, "No local document review signals are visible in this local brief."),
            "",
            "Open loops:",
            *_section_lines(record.open_loop_lines, "No open loops were identified from the available local sources."),
            "",
            "Suggested next action:",
            f"- {record.suggested_next_action}",
            "",
            "Blocked / unavailable sources:",
            *_section_lines(record.blocked_source_lines, "None."),
            "",
            "Boundaries:",
            "Calendar writes: disabled",
            "Gmail send/modify: disabled",
            "Memory Store writes: disabled",
            "Memory Center mutation: disabled",
            "Draft creation: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "Scheduler/proactive sends: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )


def _meeting_lines(calendar_result: CalendarReadResult | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if calendar_result is None:
        return (), ("Calendar: no read-only Calendar result supplied.",)
    if not calendar_result.ok:
        return (), (f"Calendar: unavailable ({calendar_result.error_code or 'unknown_error'}).",)
    if not calendar_result.events:
        return (), ()
    return tuple(
        f"{event.start} - {event.summary}"
        + (f" ({event.location})" if event.location else "")
        for event in calendar_result.events
    ), ()


def _email_context_lines(gmail_scan: GmailReadonlyContextScanRecord | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if gmail_scan is None:
        return (), ("Gmail: no read-only context scan supplied.",)
    if gmail_scan.error_code:
        return (), (f"Gmail: unavailable ({gmail_scan.error_code}).",)
    if not gmail_scan.signals:
        return (), ()
    return tuple(f"{signal.signal_type}: {signal.summary}" for signal in gmail_scan.signals), ()


def _memory_context_lines(memory_snapshot: TelegramMemoryCenterSnapshot | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if memory_snapshot is None:
        return (), ("Memory: no local approved-memory snapshot supplied.",)
    if not memory_snapshot.approved_memories:
        return (), ()
    return tuple(f"{memory.memory_kind}: {memory.summary}" for memory in memory_snapshot.approved_memories), ()


def _document_lines(document_reviews: tuple[DocumentReviewPackRecord, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not document_reviews:
        return (), ("Documents: no local document review pack supplied.",)
    visible = tuple(
        f"{record.document_title}: {record.summary}"
        for record in document_reviews
        if record.status == "completed_draft_review"
    )
    blocked = tuple(
        f"Documents: {record.document_title} unavailable ({record.error_code or record.status})."
        for record in document_reviews
        if record.status != "completed_draft_review"
    )
    return visible, blocked


def _open_loop_lines(
    *,
    meeting_lines: tuple[str, ...],
    email_lines: tuple[str, ...],
    memory_lines: tuple[str, ...],
    document_lines: tuple[str, ...],
    blocked_lines: tuple[str, ...],
) -> tuple[str, ...]:
    lines: list[str] = []
    if meeting_lines and not memory_lines:
        lines.append("Meeting context is visible, but no approved memory context is attached.")
    if email_lines:
        lines.append("Review email context signals before deciding whether a follow-up draft is needed.")
    if document_lines:
        lines.append("Review local document signals before the next relevant meeting.")
    if blocked_lines:
        lines.append("Some sources are unavailable; setup may be needed before relying on this brief.")
    return tuple(lines)


def _suggested_next_action(*, open_loop_lines: tuple[str, ...], blocked_lines: tuple[str, ...]) -> str:
    if open_loop_lines:
        return "Review the open loops and choose one owner-approved next step."
    if blocked_lines:
        return "Review setup status for blocked sources."
    return "Review the brief; no owner action is required from available local context."


def _section_lines(lines: tuple[str, ...], empty_line: str) -> tuple[str, ...]:
    if not lines:
        return (f"- {empty_line}",)
    return tuple(f"- {line}" for line in lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.cross_source_daily_brief")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = build_cross_source_daily_brief(owner_id="local-owner", robot_id="roboticxs-dev")
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_cross_source_daily_brief(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
