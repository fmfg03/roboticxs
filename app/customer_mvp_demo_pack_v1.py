from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.action_draft_queue import build_action_draft_queue, render_action_draft_queue
from app.approved_output_export import build_approved_output_export, render_approved_output_export
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.runnable_telegram_robot_mvp import (
    DEFAULT_OWNER_ID,
    DEFAULT_ROBOT_ID,
    NO_ACTION_TAKEN_LINE,
    TelegramRobotConfig,
    render_start_command_reply,
    render_status_command_reply,
)
from app.suggestion_decision_flow import build_suggestion_decision_receipt, render_suggestion_decision_receipt
from app.suggestion_inbox import build_suggestion_inbox, render_suggestion_inbox
from app.telegram_demo_loop import build_telegram_demo_loop_transcript
from app.user_confirmation_runtime import build_user_confirmation_receipt, render_user_confirmation_receipt


CUSTOMER_MVP_DEMO_PACK_V1_STAGE = "180P"
CUSTOMER_MVP_DEMO_PACK_V1_STATUS = "completed_local_customer_mvp_demo_v1"


@dataclass(frozen=True, slots=True)
class CustomerMvpDemoPackV1Step:
    command: str
    title: str
    reply_text: str
    authorized: bool
    telegram_api_called: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if not self.authorized:
            raise ValueError("180P demo steps must be owner-authorized local examples.")
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
            raise ValueError("180P demo steps must not expand authority.")


@dataclass(frozen=True, slots=True)
class CustomerMvpDemoPackV1:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    steps: tuple[CustomerMvpDemoPackV1Step, ...]
    local_only: bool
    deterministic: bool
    telegram_api_called: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CUSTOMER_MVP_DEMO_PACK_V1_STAGE:
            raise ValueError("180P demo pack must identify the 180P stage.")
        if self.status != CUSTOMER_MVP_DEMO_PACK_V1_STATUS:
            raise ValueError("180P demo pack must report completed local demo status.")
        if not self.local_only or not self.deterministic:
            raise ValueError("180P demo pack must be local-only and deterministic.")
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
            raise ValueError("180P demo pack must not expand authority.")


def build_customer_mvp_demo_pack_v1(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
) -> CustomerMvpDemoPackV1:
    config = TelegramRobotConfig(
        bot_token="",
        owner_ids=frozenset({111111111}),
        robot_id=robot_id,
        owner_id=owner_id,
        poll_timeout_seconds=30,
        poll_limit=10,
        dry_run=True,
        dev_mode=True,
    )
    base_demo = build_telegram_demo_loop_transcript(owner_id=owner_id, robot_id=robot_id)
    base_steps_by_command = {step.command.split()[0]: step for step in base_demo.steps}
    suggestion_inbox = _demo_suggestion_inbox(owner_id=owner_id, robot_id=robot_id)
    suggestion = suggestion_inbox.items[0]
    decision = build_suggestion_decision_receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        suggestion_id=suggestion.suggestion_id,
        choice="create_draft",
        inbox=suggestion_inbox,
    )
    draft_queue = build_action_draft_queue(owner_id=owner_id, robot_id=robot_id, decisions=(decision,))
    draft = draft_queue.drafts[0]
    confirmation = build_user_confirmation_receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        draft_id=draft.draft_id,
        choice="approve",
        queue=draft_queue,
    )
    export = build_approved_output_export(
        owner_id=owner_id,
        robot_id=robot_id,
        confirmation_id=confirmation.confirmation_id,
        export_format="text",
        confirmations=(confirmation,),
    )
    steps = (
        _step("/start", "First-run product shell", render_start_command_reply(config)),
        _step("/status", "Setup and capability status", render_status_command_reply(config)),
        _step("/today", "Daily value view", base_steps_by_command["/today"].reply_text),
        _step(base_steps_by_command["/prep"].command, "Meeting prep pack", base_steps_by_command["/prep"].reply_text),
        _step("/suggestions", "Suggestion inbox", render_suggestion_inbox(suggestion_inbox)),
        _step(f"/suggestion_draft {suggestion.suggestion_id}", "Draft intent receipt", render_suggestion_decision_receipt(decision)),
        _step("/drafts", "Action draft queue", render_action_draft_queue(draft_queue)),
        _step(f"/draft_approve {draft.draft_id}", "User confirmation receipt", render_user_confirmation_receipt(confirmation)),
        _step(f"/export_text {confirmation.confirmation_id}", "Approved output export", render_approved_output_export(export)),
    )
    return CustomerMvpDemoPackV1(
        stage=CUSTOMER_MVP_DEMO_PACK_V1_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=CUSTOMER_MVP_DEMO_PACK_V1_STATUS,
        steps=steps,
        local_only=True,
        deterministic=True,
        telegram_api_called=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def render_customer_mvp_demo_pack_v1(pack: CustomerMvpDemoPackV1) -> str:
    lines = [
        "Customer MVP Demo Pack v1",
        "",
        f"Stage: {pack.stage}",
        f"Status: {pack.status}",
        "Local-only: true",
        "Deterministic: true",
        "",
        "Demo path:",
    ]
    for index, step in enumerate(pack.steps, start=1):
        lines.extend((f"{index}. {step.command} - {step.title}", _first_non_empty_line(step.reply_text)))
    lines.extend(
        [
            "",
            "Loop proven:",
            "- today",
            "- meeting prep",
            "- suggestion",
            "- draft",
            "- confirmation",
            "- local export payload",
            "",
            "Boundaries:",
            "Telegram API called: false",
            "Connector activation: disabled",
            "External writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "",
            NO_ACTION_TAKEN_LINE,
        ]
    )
    return "\n".join(lines)


def _demo_suggestion_inbox(*, owner_id: str, robot_id: str):
    suggestions = build_proactive_suggestion_loop_records(
        owner_id=owner_id,
        robot_id=robot_id,
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-180p-demo",
                owner_id=owner_id,
                robot_id=robot_id,
                trigger_type="email_thread_no_followup",
                title="Prepare approved follow-up",
                summary="meeting prep is ready and a follow-up draft can be prepared",
                source_refs=("calendar:evt-180p", "gmail:thread-180p"),
            ),
        ),
    )
    return build_suggestion_inbox(owner_id=owner_id, robot_id=robot_id, suggestions=suggestions)


def _step(command: str, title: str, reply_text: str) -> CustomerMvpDemoPackV1Step:
    return CustomerMvpDemoPackV1Step(
        command=command,
        title=title,
        reply_text=reply_text,
        authorized=True,
        telegram_api_called=False,
        connector_activation_allowed=False,
        external_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(empty reply)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.customer_mvp_demo_pack_v1")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    pack = build_customer_mvp_demo_pack_v1()
    if args.as_json:
        print(json.dumps(asdict(pack), sort_keys=True, indent=2))
    else:
        print(render_customer_mvp_demo_pack_v1(pack))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
