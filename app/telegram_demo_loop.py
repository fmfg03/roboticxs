from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.brief_memory_proposal import build_brief_memory_proposal_record, render_brief_memory_candidate_section
from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.inbox_item_decision import build_inbox_item_decision, render_inbox_item_decision
from app.meeting_prep_pack import build_meeting_prep_pack, render_meeting_prep_pack
from app.memory_center_projection import MemoryCenterItem
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.runnable_telegram_robot_mvp import (
    DEFAULT_OWNER_ID,
    DEFAULT_ROBOT_ID,
    TelegramRobotConfig,
    render_start_command_reply,
    render_status_command_reply,
)
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
    render_memory_pending_command_reply,
)
from app.today_command import build_today_command_record, render_today_command


TELEGRAM_DEMO_LOOP_STAGE = "157P"
DEMO_OWNER_TELEGRAM_ID = 111111111


@dataclass(frozen=True, slots=True)
class PendingMemoryDemoProposal:
    proposal_id: str
    owner_id: str
    robot_id: str
    status: str
    proposal_type: str
    proposed_memory_text: str
    confidence: str
    review_reason: str
    source_stage: str


@dataclass(frozen=True, slots=True)
class TelegramDemoLoopStep:
    command: str
    title: str
    reply_text: str
    authorized: bool
    external_write_allowed: bool
    connector_activation_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if not self.authorized:
            raise ValueError("157P demo loop steps must be owner-authorized local examples.")
        if any(
            (
                self.external_write_allowed,
                self.connector_activation_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("157P demo loop steps must not expand authority.")


@dataclass(frozen=True, slots=True)
class TelegramDemoLoopTranscript:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    steps: tuple[TelegramDemoLoopStep, ...]
    local_only: bool
    telegram_api_called: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != TELEGRAM_DEMO_LOOP_STAGE:
            raise ValueError("157P demo loop transcript must identify the 157P stage.")
        if not self.local_only:
            raise ValueError("157P demo loop must remain local-only.")
        if any(
            (
                self.telegram_api_called,
                self.connector_activation_allowed,
                self.external_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("157P demo loop must not expand authority.")


def build_telegram_demo_loop_transcript(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
) -> TelegramDemoLoopTranscript:
    config = _demo_config(owner_id=owner_id, robot_id=robot_id)
    suggestion_scan = _demo_suggestion_scan(owner_id=owner_id, robot_id=robot_id)
    memory_snapshot = build_memory_center_telegram_snapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(_demo_memory_item(owner_id=owner_id, robot_id=robot_id),),
        ),
    )
    today_record = build_today_command_record(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    suggestion_id = suggestion_scan.suggestions[0].suggestion_id
    prep_record = build_meeting_prep_pack(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion_id,
        suggestion_scan=suggestion_scan,
        memory_snapshot=memory_snapshot,
    )
    memory_proposal = build_brief_memory_proposal_record(prep_pack=prep_record)
    memory_pending_snapshot = build_memory_center_telegram_snapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(_demo_pending_memory(owner_id=owner_id, robot_id=robot_id),),
        ),
    )
    inbox_done = build_inbox_item_decision(
        owner_id=owner_id,
        robot_id=robot_id,
        item_id="pending-memory:demo-proposal-157p",
        choice="done",
    )
    steps = (
        _step("/start", "First-run onboarding", render_start_command_reply(config)),
        _step("/status", "Setup and capability status", render_status_command_reply(config)),
        _step("/today", "Daily value view", render_today_command(today_record)),
        _step(
            f"/prep {suggestion_id}",
            "Meeting prep pack",
            "\n".join(
                [
                    render_meeting_prep_pack(prep_record),
                    "",
                    *render_brief_memory_candidate_section(memory_proposal),
                ]
            ),
        ),
        _step("/memory_pending", "Memory review", render_memory_pending_command_reply(memory_pending_snapshot)),
        _step(
            "/inbox_done pending-memory:demo-proposal-157p",
            "Task inbox local receipt",
            render_inbox_item_decision(inbox_done),
        ),
    )
    return TelegramDemoLoopTranscript(
        stage=TELEGRAM_DEMO_LOOP_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status="completed_local_demo",
        steps=steps,
        local_only=True,
        telegram_api_called=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def render_telegram_demo_loop_transcript(transcript: TelegramDemoLoopTranscript) -> str:
    lines = [
        "Telegram Demo Loop",
        "",
        f"Stage: {transcript.stage}",
        f"Status: {transcript.status}",
        "Local-only: true",
        "Telegram API called: false",
        "",
        "Steps:",
    ]
    for index, step in enumerate(transcript.steps, start=1):
        lines.extend(
            [
                f"{index}. {step.command} - {step.title}",
                _first_non_empty_line(step.reply_text),
            ]
        )
    lines.extend(
        [
            "",
            "Boundaries:",
            "Connector activation: disabled",
            "Telegram live sends: disabled",
            "External writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _step(command: str, title: str, reply_text: str) -> TelegramDemoLoopStep:
    return TelegramDemoLoopStep(
        command=command,
        title=title,
        reply_text=reply_text,
        authorized=True,
        external_write_allowed=False,
        connector_activation_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def _demo_config(*, owner_id: str, robot_id: str) -> TelegramRobotConfig:
    return TelegramRobotConfig(
        bot_token="",
        owner_ids=frozenset({DEMO_OWNER_TELEGRAM_ID}),
        robot_id=robot_id,
        owner_id=owner_id,
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=True,
        dev_mode=True,
    )


def _demo_event() -> CalendarEventSnapshot:
    return CalendarEventSnapshot(
        event_id="evt-157p-demo",
        summary="Client demo prep meeting",
        start="2026-06-25T10:00:00-06:00",
        end="2026-06-25T10:30:00-06:00",
        all_day=False,
        location="Google Meet",
        description_preview="Review proposal context and prepare open questions.",
        organizer_email="owner@example.com",
        attendee_count=3,
        html_link="https://calendar.google.com/event?eid=157p",
        source="local_demo_fixture",
    )


def _demo_calendar_result() -> CalendarReadResult:
    return CalendarReadResult(
        ok=True,
        calendar_id="local-demo",
        window_start="2026-06-25T00:00:00-06:00",
        window_end="2026-06-26T00:00:00-06:00",
        events=(_demo_event(),),
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=None,
        error_message=None,
    )


def _demo_suggestion_scan(*, owner_id: str, robot_id: str):
    context_scan = build_calendar_context_scan_record(
        owner_id=owner_id,
        robot_id=robot_id,
        calendar_result=_demo_calendar_result(),
    )
    return build_proactive_meeting_suggestion_scan(
        owner_id=owner_id,
        robot_id=robot_id,
        context_scan=context_scan,
    )


def _demo_memory_item(*, owner_id: str, robot_id: str) -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id="mem-157p-demo",
        owner_id=owner_id,
        robot_id=robot_id,
        memory_kind="preference",
        status="active",
        scopes=("telegram", "meeting_prep"),
        sensitivity="ordinary",
        allowed_uses=("telegram_context",),
        skill_ids=(),
        content="Francisco prefers compact meeting prep with open questions first.",
        bounded_summary="Francisco prefers compact meeting prep with open questions first.",
        source="local_demo_fixture",
    )


def _demo_pending_memory(*, owner_id: str, robot_id: str) -> PendingMemoryDemoProposal:
    return PendingMemoryDemoProposal(
        proposal_id="demo-proposal-157p",
        owner_id=owner_id,
        robot_id=robot_id,
        status="pending_user_review",
        proposal_type="meeting_prep_preference_candidate",
        proposed_memory_text="For client demos, prepare open questions before reviewing slides.",
        confidence="medium",
        review_reason="Demo loop pending memory review example.",
        source_stage=TELEGRAM_DEMO_LOOP_STAGE,
    )


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return f"  reply: {line.strip()}"
    return "  reply: <empty>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.telegram_demo_loop")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    transcript = build_telegram_demo_loop_transcript()
    if args.json:
        print(json.dumps(asdict(transcript), indent=2, sort_keys=True))
    else:
        print(render_telegram_demo_loop_transcript(transcript))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
