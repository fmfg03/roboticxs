from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re

from app.runnable_telegram_robot_mvp import (
    DEFAULT_OWNER_ID,
    DEFAULT_ROBOT_ID,
    NO_ACTION_TAKEN_LINE,
    PRODUCT_APPROVAL_BOUNDARY_LINES,
    PRODUCT_MENU_LINES,
    TelegramRobotConfig,
    render_help_command_reply,
    render_start_command_reply,
    render_status_command_reply,
)
from app.telegram_demo_loop import build_telegram_demo_loop_transcript
from app.telegram_document_intake_stub import (
    TelegramDocumentIntakeMetadata,
    build_telegram_document_intake_stub_record,
    render_telegram_document_intake_stub,
)


CUSTOMER_MVP_BASELINE_STAGE = "160P"
CUSTOMER_MVP_STATUS = "customer_mvp_baseline_ready"
SECRET_PATTERN = re.compile(
    r"BEGIN|PRIVATE KEY|TOKEN=|SECRET=|BOT_TOKEN=|client_secret|refresh_token|access_token",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class CustomerMvpBaselineStatus:
    stage: str
    status: str
    product_menu_lines: tuple[str, ...]
    demo_commands: tuple[str, ...]
    demo_deterministic: bool
    setup_clear: bool
    memory_review_clear: bool
    task_inbox_functional: bool
    meeting_prep_sellable: bool
    document_intake_stub: bool
    safety_language_visible: bool
    no_secrets_included: bool
    local_only: bool
    telegram_api_called: bool
    connector_activation_allowed: bool
    external_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CUSTOMER_MVP_BASELINE_STAGE:
            raise ValueError("160P customer MVP baseline must identify the 160P stage.")
        if self.status != CUSTOMER_MVP_STATUS:
            raise ValueError("160P customer MVP baseline must report ready status.")
        required_ready = (
            self.demo_deterministic,
            self.setup_clear,
            self.memory_review_clear,
            self.task_inbox_functional,
            self.meeting_prep_sellable,
            self.document_intake_stub,
            self.safety_language_visible,
            self.no_secrets_included,
            self.local_only,
        )
        if not all(required_ready):
            raise ValueError("160P customer MVP baseline requires all MVP readiness checks to pass.")
        forbidden_authority = (
            self.telegram_api_called,
            self.connector_activation_allowed,
            self.external_write_allowed,
            self.memory_center_mutated,
            self.model_call_allowed,
            self.tool_call_allowed,
            self.worker_dispatch_allowed,
        )
        if any(forbidden_authority):
            raise ValueError("160P customer MVP baseline must not expand runtime authority.")


def build_customer_mvp_baseline_status(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
) -> CustomerMvpBaselineStatus:
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
    start_reply = render_start_command_reply(config)
    help_reply = render_help_command_reply()
    status_reply = render_status_command_reply(config)
    demo = build_telegram_demo_loop_transcript(owner_id=owner_id, robot_id=robot_id)
    demo_commands = tuple(step.command.split()[0] for step in demo.steps)
    demo_text = "\n\n".join(step.reply_text for step in demo.steps)
    document_record = build_telegram_document_intake_stub_record(
        owner_id=owner_id,
        robot_id=robot_id,
        document=TelegramDocumentIntakeMetadata(
            file_id="customer-mvp-baseline-file",
            file_unique_id=None,
            file_name="customer-demo.pdf",
            mime_type="application/pdf",
            file_size=None,
        ),
    )
    document_reply = render_telegram_document_intake_stub(document_record)
    safety_text = "\n\n".join((start_reply, help_reply, status_reply, document_reply))
    return CustomerMvpBaselineStatus(
        stage=CUSTOMER_MVP_BASELINE_STAGE,
        status=CUSTOMER_MVP_STATUS,
        product_menu_lines=PRODUCT_MENU_LINES,
        demo_commands=demo_commands,
        demo_deterministic=demo.status == "completed_local_demo" and demo_commands == (
            "/start",
            "/status",
            "/today",
            "/prep",
            "/memory_pending",
            "/inbox_done",
        ),
        setup_clear=all(
            marker in status_reply
            for marker in (
                "Active now:",
                "Needs setup:",
                "Unavailable:",
                "Intentionally disabled:",
                "Suggested next action:",
            )
        ),
        memory_review_clear="Memory Review" in demo_text and "/memory_pending" in demo_commands,
        task_inbox_functional="Task Inbox Decision" in demo_text and "/inbox_done" in demo_commands,
        meeting_prep_sellable="Meeting Prep Pack" in demo_text and "/prep" in demo_commands,
        document_intake_stub=all(
            marker in document_reply
            for marker in (
                "Document Intake",
                "Document review is currently draft-only.",
                "I received Telegram metadata only.",
                "External writes: disabled",
            )
        ),
        safety_language_visible=all(line in safety_text for line in PRODUCT_APPROVAL_BOUNDARY_LINES)
        and NO_ACTION_TAKEN_LINE in safety_text,
        no_secrets_included=SECRET_PATTERN.search(safety_text) is None,
        local_only=demo.local_only,
        telegram_api_called=demo.telegram_api_called,
        connector_activation_allowed=demo.connector_activation_allowed,
        external_write_allowed=demo.external_write_allowed or document_record.external_write_allowed,
        memory_center_mutated=demo.memory_center_mutated or document_record.memory_center_mutated,
        model_call_allowed=demo.model_call_allowed or document_record.model_call_allowed,
        tool_call_allowed=demo.tool_call_allowed or document_record.tool_call_allowed,
        worker_dispatch_allowed=demo.worker_dispatch_allowed or document_record.worker_dispatch_allowed,
    )


def render_customer_mvp_baseline_status(status: CustomerMvpBaselineStatus) -> str:
    lines = [
        "Customer MVP Baseline",
        "",
        f"Stage: {status.stage}",
        f"Status: {status.status}",
        "Local-only: true",
        "",
        "Product surface:",
    ]
    lines.extend(f"- {line}" for line in status.product_menu_lines)
    lines.extend(
        [
            "",
            "Demo loop:",
            "- " + ", ".join(status.demo_commands),
            "",
            "Readiness:",
            "- setup clear",
            "- memory review clear",
            "- task inbox functional",
            "- meeting prep sellable",
            "- document intake draft-only",
            "- safety language visible",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.customer_mvp_baseline")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    status = build_customer_mvp_baseline_status()
    if args.as_json:
        print(json.dumps(asdict(status), sort_keys=True, indent=2))
    else:
        print(render_customer_mvp_baseline_status(status))
    return 0
