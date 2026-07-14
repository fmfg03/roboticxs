from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.document_review_pack import DocumentReviewPackRecord
from app.gmail_readonly_context_scan import GmailReadonlyContextScanRecord
from app.meeting_prep_pack import MeetingPrepPackRecord, render_meeting_prep_pack, run_meeting_prep_pack


MEETING_PREP_PACK_V1_STAGE = "175P"
MAX_CONTEXT_LINES = 4


@dataclass(frozen=True, slots=True)
class MeetingPrepPackV1Record:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    source_stages: tuple[str, ...]
    base_pack: MeetingPrepPackRecord
    people_lines: tuple[str, ...]
    recent_email_lines: tuple[str, ...]
    document_context_lines: tuple[str, ...]
    risk_lines: tuple[str, ...]
    next_step_lines: tuple[str, ...]
    blocked_source_lines: tuple[str, ...]
    read_only: bool
    calendar_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    memory_write_allowed: bool
    memory_center_mutated: bool
    draft_created: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    scheduler_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != MEETING_PREP_PACK_V1_STAGE:
            raise ValueError("175P meeting prep pack v1 records must identify the 175P stage.")
        if self.base_pack.owner_id != self.owner_id or self.base_pack.robot_id != self.robot_id:
            raise ValueError("rejected_meeting_prep_v1_owner_robot_mismatch")
        if "151P" not in self.source_stages:
            raise ValueError("175P meeting prep pack v1 records must include 151P prep pack lineage.")
        if not self.read_only:
            raise ValueError("175P meeting prep pack v1 records must remain read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.draft_created,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.scheduler_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("175P meeting prep pack v1 records must not expand authority.")


def build_meeting_prep_pack_v1(
    *,
    base_pack: MeetingPrepPackRecord,
    gmail_scan: GmailReadonlyContextScanRecord | None = None,
    document_reviews: tuple[DocumentReviewPackRecord, ...] = (),
) -> MeetingPrepPackV1Record:
    people_lines = _people_lines(base_pack)
    recent_email_lines, gmail_blocked = _recent_email_lines(gmail_scan)
    document_lines, document_risks, document_blocked = _document_lines(document_reviews)
    blocked_lines = gmail_blocked + document_blocked
    status = _status(base_pack=base_pack, recent_email_lines=recent_email_lines, document_lines=document_lines, blocked_lines=blocked_lines)
    return MeetingPrepPackV1Record(
        stage=MEETING_PREP_PACK_V1_STAGE,
        owner_id=base_pack.owner_id,
        robot_id=base_pack.robot_id,
        status=status,
        source_stages=_source_stages(base_pack, gmail_scan, document_reviews),
        base_pack=base_pack,
        people_lines=people_lines,
        recent_email_lines=recent_email_lines,
        document_context_lines=document_lines,
        risk_lines=_risk_lines(base_pack=base_pack, document_risks=document_risks),
        next_step_lines=_next_step_lines(base_pack=base_pack, recent_email_lines=recent_email_lines, document_lines=document_lines, blocked_lines=blocked_lines),
        blocked_source_lines=blocked_lines,
        read_only=True,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        memory_write_allowed=False,
        memory_center_mutated=False,
        draft_created=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        scheduler_allowed=False,
        external_write_allowed=False,
    )


def render_meeting_prep_pack_v1(record: MeetingPrepPackV1Record) -> str:
    lines = [
        "Meeting Prep Pack",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Suggestion id: {record.base_pack.suggestion_id}",
        "Owner requested: true",
        "Read-only: true",
        "",
        "Meeting context:",
        *_section_lines(record.base_pack.meeting_lines, "No meeting context is visible."),
        "",
        "Agenda:",
        *_section_lines(record.base_pack.agenda_lines, "No agenda was generated."),
        "",
        "People:",
        *_section_lines(record.people_lines, "No people signals are visible."),
        "",
        "Known memory:",
        *_section_lines(record.base_pack.memory_context_lines, "No approved memory is visible."),
        "",
        "Recent email context:",
        *_section_lines(record.recent_email_lines, "No Gmail context signals are visible."),
        "",
        "Documents / risks:",
        *_section_lines(record.document_context_lines, "No local document review signals are visible."),
        "",
        "Risks and questions:",
        *_section_lines(record.risk_lines, "No risks or questions were identified from available local context."),
        "",
        "Open loops:",
        *_section_lines(record.base_pack.open_loop_lines, "No open loops were found in the local prep context."),
        "",
        "Next steps:",
        *_section_lines(record.next_step_lines, "Review the pack before the meeting."),
        "",
        "Blocked / unavailable sources:",
        *_section_lines(record.blocked_source_lines, "None."),
        "",
        "Boundaries:",
        "Calendar writes: disabled",
        "Gmail send/modify: disabled",
        "Memory writes: disabled",
        "Memory Center mutation: disabled",
        "Draft creation: disabled",
        "Model calls: disabled",
        "Tools/workers: disabled",
        "Scheduler/proactive sends: disabled",
        "External writes: disabled",
        "",
        "No external action was taken.",
    ]
    return "\n".join(lines)


def run_meeting_prep_pack_v1(
    *,
    owner_id: str = "local-owner",
    robot_id: str = "roboticxs-dev",
    suggestion_id: str,
    gmail_scan: GmailReadonlyContextScanRecord | None = None,
    document_reviews: tuple[DocumentReviewPackRecord, ...] = (),
) -> MeetingPrepPackV1Record:
    base_pack = run_meeting_prep_pack(owner_id=owner_id, robot_id=robot_id, suggestion_id=suggestion_id)
    return build_meeting_prep_pack_v1(
        base_pack=base_pack,
        gmail_scan=gmail_scan,
        document_reviews=document_reviews,
    )


def _source_stages(
    base_pack: MeetingPrepPackRecord,
    gmail_scan: GmailReadonlyContextScanRecord | None,
    document_reviews: tuple[DocumentReviewPackRecord, ...],
) -> tuple[str, ...]:
    stages = ["151P", *base_pack.source_stages]
    if gmail_scan is not None:
        stages.append(gmail_scan.stage)
    stages.extend(record.stage for record in document_reviews)
    return tuple(dict.fromkeys(stages))


def _status(
    *,
    base_pack: MeetingPrepPackRecord,
    recent_email_lines: tuple[str, ...],
    document_lines: tuple[str, ...],
    blocked_lines: tuple[str, ...],
) -> str:
    if base_pack.status != "completed":
        return base_pack.status
    if recent_email_lines or document_lines:
        return "completed_with_context"
    if blocked_lines:
        return "completed_with_blocked_sources"
    return "completed"


def _people_lines(base_pack: MeetingPrepPackRecord) -> tuple[str, ...]:
    suggestion = base_pack.suggested_brief.selected_suggestion
    if suggestion is None:
        return ()
    return (
        f"Meeting: {suggestion.event_summary}",
        f"Source event: {suggestion.event_id}",
        "Attendees: available only when Calendar read-only context exposes them.",
    )


def _recent_email_lines(gmail_scan: GmailReadonlyContextScanRecord | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if gmail_scan is None:
        return (), ("Gmail: no read-only context scan supplied.",)
    if gmail_scan.error_code:
        return (), (f"Gmail: unavailable ({gmail_scan.error_code}).",)
    return tuple(
        f"{signal.signal_type}: {signal.summary}"
        for signal in gmail_scan.signals[:MAX_CONTEXT_LINES]
    ), ()


def _document_lines(
    document_reviews: tuple[DocumentReviewPackRecord, ...]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if not document_reviews:
        return (), (), ("Documents: no local document review pack supplied.",)
    visible = []
    risks = []
    blocked = []
    for record in document_reviews:
        if record.status != "completed_draft_review":
            blocked.append(f"Documents: {record.document_title} unavailable ({record.error_code or record.status}).")
            continue
        visible.append(f"{record.document_title}: {record.summary}")
        risks.extend(f"{record.document_title}: {line}" for line in record.possible_risk_notes[:2])
        risks.extend(f"{record.document_title}: {line}" for line in record.suggested_questions[:2])
    return tuple(visible[:MAX_CONTEXT_LINES]), tuple(risks[:MAX_CONTEXT_LINES]), tuple(blocked)


def _risk_lines(*, base_pack: MeetingPrepPackRecord, document_risks: tuple[str, ...]) -> tuple[str, ...]:
    lines = list(document_risks)
    lines.extend(line for line in base_pack.watchpoints if line not in {"No external action was taken."})
    return tuple(lines[:MAX_CONTEXT_LINES])


def _next_step_lines(
    *,
    base_pack: MeetingPrepPackRecord,
    recent_email_lines: tuple[str, ...],
    document_lines: tuple[str, ...],
    blocked_lines: tuple[str, ...],
) -> tuple[str, ...]:
    lines = list(base_pack.next_steps)
    if recent_email_lines:
        lines.append("Review recent email context before deciding whether a follow-up draft is needed.")
    if document_lines:
        lines.append("Review document risks and questions before the meeting.")
    if blocked_lines:
        lines.append("Check setup for blocked sources before relying on this prep pack.")
    return tuple(dict.fromkeys(lines))[:MAX_CONTEXT_LINES]


def _section_lines(lines: tuple[str, ...], empty_line: str) -> tuple[str, ...]:
    if not lines:
        return (f"- {empty_line}",)
    return tuple(f"- {line}" for line in lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.meeting_prep_pack_v1")
    parser.add_argument("suggestion_id")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = run_meeting_prep_pack_v1(suggestion_id=args.suggestion_id)
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2, default=str))
    else:
        print(render_meeting_prep_pack_v1(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
