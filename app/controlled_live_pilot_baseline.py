from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.action_draft_queue import ActionDraftQueue, build_action_draft_queue, render_action_draft_queue
from app.approved_gmail_draft_creation import (
    ApprovedGmailDraftCreationRecord,
    GmailDraftHttpClientProtocol,
    build_approved_gmail_draft_creation,
    render_approved_gmail_draft_creation,
)
from app.source_trace_receipts import (
    SOURCE_TRACE_RECEIPTS_STATUS,
    SourceTraceActionBoundary,
    SourceTraceReceipt,
    SourceTraceReceiptItem,
    render_source_trace_receipt,
)
from app.suggestion_decision_flow import build_suggestion_decision_receipt, render_suggestion_decision_receipt
from app.suggestion_inbox import SuggestionInbox, build_suggestion_inbox, render_suggestion_inbox
from app.proactive_suggestion_loop import ProactiveSuggestionSignal, build_proactive_suggestion_loop_records
from app.user_confirmation_runtime import UserConfirmationReceipt, build_user_confirmation_receipt, render_user_confirmation_receipt
from app.usage_cost_ledger import (
    UsageCostLedgerEntry,
    build_usage_cost_ledger_entry,
    render_usage_cost_ledger_summary,
    summarize_usage_cost_ledger,
)


CONTROLLED_LIVE_PILOT_BASELINE_STAGE = "190P"
CONTROLLED_LIVE_PILOT_STATUS = "completed_controlled_live_pilot_baseline_v0"


@dataclass(frozen=True, slots=True)
class ControlledLivePilotStep:
    name: str
    status: str
    summary: str
    command: str


@dataclass(frozen=True, slots=True)
class ControlledLivePilotReceipt:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    mode: str
    steps: tuple[ControlledLivePilotStep, ...]
    suggestion_inbox: SuggestionInbox
    draft_queue: ActionDraftQueue
    confirmation: UserConfirmationReceipt
    gmail_draft_creation: ApprovedGmailDraftCreationRecord
    source_trace_receipt: SourceTraceReceipt
    usage_entries: tuple[UsageCostLedgerEntry, ...]
    calendar_read_used: bool
    gmail_read_used: bool
    memory_used: bool
    source_receipt_created: bool
    usage_receipt_created: bool
    gmail_draft_created: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    calendar_write_allowed: bool
    oauth_flow_allowed: bool
    connector_activation_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    scheduler_allowed: bool
    billing_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CONTROLLED_LIVE_PILOT_BASELINE_STAGE:
            raise ValueError("190P pilot receipts must identify the 190P stage.")
        if self.status != CONTROLLED_LIVE_PILOT_STATUS:
            raise ValueError("190P pilot receipts must use the controlled live pilot status.")
        if self.mode not in {"fixture", "live_capable"}:
            raise ValueError("190P pilot mode must be fixture or live_capable.")
        if len(self.steps) < 7:
            raise ValueError("190P pilot receipts must include the complete pilot path.")
        if self.gmail_draft_created != self.gmail_draft_creation.gmail_draft_created:
            raise ValueError("190P Gmail draft created flag must match the Gmail draft record.")
        if not self.source_receipt_created or not self.usage_receipt_created:
            raise ValueError("190P pilot receipts require source and usage receipts.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.calendar_write_allowed,
                self.oauth_flow_allowed,
                self.connector_activation_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.scheduler_allowed,
                self.billing_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("190P pilot baseline must not expand execution authority.")


class FixtureGmailDraftHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: dict,
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": {"Authorization": "[redacted]", "Accept": headers.get("Accept", "")},
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return {"id": "draft-190p-fixture", "message": {"id": "msg-190p-fixture"}}


def build_controlled_live_pilot_baseline(
    *,
    owner_id: str,
    robot_id: str,
    gmail_draft_http_client: GmailDraftHttpClientProtocol | None = None,
    env: dict[str, str] | None = None,
    usage_entries: tuple[UsageCostLedgerEntry, ...] = (),
) -> ControlledLivePilotReceipt:
    mode = "live_capable" if gmail_draft_http_client is not None or (env and env.get("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN")) else "fixture"
    suggestion_inbox = _build_pilot_suggestion_inbox(owner_id=owner_id, robot_id=robot_id)
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
    gmail_client = gmail_draft_http_client or FixtureGmailDraftHttpClient()
    gmail_env = env if env is not None else {"ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN": "fixture-token-redacted"}
    gmail_draft_creation = build_approved_gmail_draft_creation(
        owner_id=owner_id,
        robot_id=robot_id,
        confirmation_id=confirmation.confirmation_id,
        confirmations=(confirmation,),
        env=gmail_env,
        http_client=gmail_client,
    )
    entries = usage_entries or _build_fixture_usage_entries(owner_id=owner_id, robot_id=robot_id)
    usage_summary = summarize_usage_cost_ledger(owner_id=owner_id, robot_id=robot_id, entries=entries)
    source_receipt = _build_pilot_source_receipt(
        owner_id=owner_id,
        robot_id=robot_id,
        draft_queue=draft_queue,
        usage_summary=usage_summary,
    )
    return ControlledLivePilotReceipt(
        stage=CONTROLLED_LIVE_PILOT_BASELINE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=CONTROLLED_LIVE_PILOT_STATUS,
        mode=mode,
        steps=(
            ControlledLivePilotStep("Daily brief", "ready", "Cross-source daily brief prepared from pilot source set.", "/daily_brief"),
            ControlledLivePilotStep("Meeting prep", "ready", "Meeting prep pack prepared with Calendar, Gmail, and Memory context.", "/prep pilot-meeting"),
            ControlledLivePilotStep("Suggestion", suggestion.status, suggestion.title, "/suggestions"),
            ControlledLivePilotStep("Draft intent", decision.decision_status, decision.suggestion_title, f"/suggestion_draft {suggestion.suggestion_id}"),
            ControlledLivePilotStep("Draft queue", draft_queue.status, f"{len(draft_queue.drafts)} draft approval candidate(s).", "/drafts"),
            ControlledLivePilotStep("Approval", confirmation.confirmation_status, confirmation.draft_title, f"/draft_approve {draft.draft_id}"),
            ControlledLivePilotStep("Gmail draft", gmail_draft_creation.status, gmail_draft_creation.draft_id or "no draft id", f"/export_email {confirmation.confirmation_id}"),
            ControlledLivePilotStep("Source receipt", source_receipt.status, "Source trace receipt created.", "/source_receipt"),
            ControlledLivePilotStep("Usage receipt", usage_summary.status_breakdown[0][0] if usage_summary.status_breakdown else "estimated", "Usage cost ledger summarized.", "/usage"),
        ),
        suggestion_inbox=suggestion_inbox,
        draft_queue=draft_queue,
        confirmation=confirmation,
        gmail_draft_creation=gmail_draft_creation,
        source_trace_receipt=source_receipt,
        usage_entries=entries,
        calendar_read_used=True,
        gmail_read_used=True,
        memory_used=True,
        source_receipt_created=True,
        usage_receipt_created=True,
        gmail_draft_created=gmail_draft_creation.gmail_draft_created,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        oauth_flow_allowed=False,
        connector_activation_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        scheduler_allowed=False,
        billing_allowed=False,
        external_write_allowed=False,
    )


def render_controlled_live_pilot_receipt(receipt: ControlledLivePilotReceipt) -> str:
    usage_summary = summarize_usage_cost_ledger(
        owner_id=receipt.owner_id,
        robot_id=receipt.robot_id,
        entries=receipt.usage_entries,
    )
    lines = [
        "Controlled Live Pilot Baseline",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Mode: {receipt.mode}",
        "",
        "Pilot path:",
    ]
    for index, step in enumerate(receipt.steps, start=1):
        lines.append(f"{index}. {step.command} - {step.name}: {step.status}")
        lines.append(f"   {step.summary}")
    lines.extend(
        [
            "",
            "Suggestion receipt:",
            _indent(render_suggestion_inbox(receipt.suggestion_inbox)),
            "",
            "Draft intent receipt:",
            _indent(render_suggestion_decision_receipt(_decision_from_queue(receipt))),
            "",
            "Draft queue receipt:",
            _indent(render_action_draft_queue(receipt.draft_queue)),
            "",
            "Approval receipt:",
            _indent(render_user_confirmation_receipt(receipt.confirmation)),
            "",
            "Gmail draft receipt:",
            _indent(render_approved_gmail_draft_creation(receipt.gmail_draft_creation)),
            "",
            "Source receipt:",
            _indent(render_source_trace_receipt(receipt.source_trace_receipt)),
            "",
            "Usage receipt:",
            _indent(render_usage_cost_ledger_summary(usage_summary)),
            "",
            "Pilot boundaries:",
            f"Calendar read used: {str(receipt.calendar_read_used).lower()}",
            f"Gmail read used: {str(receipt.gmail_read_used).lower()}",
            f"Memory used: {str(receipt.memory_used).lower()}",
            f"Gmail draft created: {str(receipt.gmail_draft_created).lower()}",
            "Gmail send: disabled",
            "Gmail modify/archive/label/delete: disabled",
            "Calendar writes: disabled",
            "OAuth flow/token refresh: disabled",
            "Connector activation: disabled",
            "Memory Center mutation: disabled",
            "Model/tool calls: disabled",
            "Workers/scheduler: disabled",
            "Billing/payment: disabled",
            "External irreversible actions: disabled",
            "",
            "No email was sent.",
            "No external irreversible action was taken.",
        ]
    )
    return "\n".join(lines)


def receipt_to_dict(receipt: ControlledLivePilotReceipt) -> dict:
    return asdict(receipt)


def _build_pilot_suggestion_inbox(*, owner_id: str, robot_id: str) -> SuggestionInbox:
    suggestions = build_proactive_suggestion_loop_records(
        owner_id=owner_id,
        robot_id=robot_id,
        signals=(
            ProactiveSuggestionSignal(
                signal_id="signal-190p-pilot",
                owner_id=owner_id,
                robot_id=robot_id,
                trigger_type="upcoming_meeting_no_prep",
                title="Prepare and draft pilot follow-up",
                summary="Calendar, Gmail, and approved memory indicate this meeting needs a follow-up draft.",
                source_refs=("calendar:pilot-event", "gmail:pilot-thread", "memory:pilot-context"),
            ),
        ),
    )
    return build_suggestion_inbox(owner_id=owner_id, robot_id=robot_id, suggestions=suggestions)


def _build_fixture_usage_entries(*, owner_id: str, robot_id: str) -> tuple[UsageCostLedgerEntry, ...]:
    return (
        build_usage_cost_ledger_entry(
            owner_id=owner_id,
            robot_id=robot_id,
            task_id="task-190p-daily-brief",
            command="/daily_brief",
            task_class="daily_brief",
            provider="local_estimate",
            model="none",
            model_mode="Economy",
            input_tokens=900,
            output_tokens=320,
            estimated_cost_usd=0.012,
            latency_ms=120,
            status="completed",
            source="190p_fixture",
            created_at="2026-06-20T08:00:00+00:00",
        ),
        build_usage_cost_ledger_entry(
            owner_id=owner_id,
            robot_id=robot_id,
            task_id="task-190p-prep",
            command="/prep",
            task_class="meeting_prep",
            provider="local_estimate",
            model="none",
            model_mode="Balanced",
            input_tokens=1400,
            output_tokens=540,
            estimated_cost_usd=0.028,
            latency_ms=180,
            status="completed",
            source="190p_fixture",
            created_at="2026-06-20T08:01:00+00:00",
        ),
        build_usage_cost_ledger_entry(
            owner_id=owner_id,
            robot_id=robot_id,
            task_id="task-190p-gmail-draft",
            command="/export_email",
            task_class="gmail_draft_creation",
            provider="local_estimate",
            model="none",
            model_mode="Economy",
            input_tokens=500,
            output_tokens=180,
            estimated_cost_usd=0.006,
            latency_ms=150,
            status="completed",
            source="190p_fixture",
            created_at="2026-06-20T08:02:00+00:00",
        ),
    )


def _build_pilot_source_receipt(*, owner_id: str, robot_id: str, draft_queue: ActionDraftQueue, usage_summary: object) -> SourceTraceReceipt:
    return SourceTraceReceipt(
        stage="184P",
        owner_id=owner_id,
        robot_id=robot_id,
        status=SOURCE_TRACE_RECEIPTS_STATUS,
        items=(
            SourceTraceReceiptItem("Calendar", "used", "Pilot Calendar event context considered.", ("calendar:pilot-event",)),
            SourceTraceReceiptItem("Gmail", "used", "Pilot Gmail read-only thread context considered.", ("gmail:pilot-thread",)),
            SourceTraceReceiptItem("Memory", "used", "Approved pilot memory context considered.", ("memory:pilot-context",)),
            SourceTraceReceiptItem("Documents", "not_connected", "No pilot document review source was connected.", next_step="Send a document or enable document review."),
            SourceTraceReceiptItem("Draft Queue", "used", f"{len(draft_queue.drafts)} local draft approval candidate(s).", tuple(draft.draft_id for draft in draft_queue.drafts)),
            SourceTraceReceiptItem("Usage", "used", "Local estimated usage summary included.", ("usage:190p-pilot",)),
        ),
        action_boundaries=(
            SourceTraceActionBoundary("Gmail send", "disabled", "190P creates draft receipts only; send is blocked."),
            SourceTraceActionBoundary("Calendar writes", "disabled", "190P reads Calendar context only."),
            SourceTraceActionBoundary("Gmail modify/archive/delete", "disabled", "190P does not modify existing Gmail data."),
            SourceTraceActionBoundary("Professional decisions", "blocked", "Legal, medical, tax, and financial decisions remain blocked."),
        ),
        read_only=True,
        connector_activation_allowed=False,
        oauth_flow_allowed=False,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _decision_from_queue(receipt: ControlledLivePilotReceipt):
    suggestion = receipt.suggestion_inbox.items[0]
    return build_suggestion_decision_receipt(
        owner_id=receipt.owner_id,
        robot_id=receipt.robot_id,
        suggestion_id=suggestion.suggestion_id,
        choice="create_draft",
        inbox=receipt.suggestion_inbox,
    )


def _indent(text: str) -> str:
    return "\n".join(f"  {line}" if line else "" for line in text.splitlines())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.controlled_live_pilot_baseline")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    receipt = build_controlled_live_pilot_baseline(owner_id="local-owner", robot_id="roboticxs-dev")
    if args.as_json:
        print(json.dumps(receipt_to_dict(receipt), sort_keys=True, indent=2))
    else:
        print(render_controlled_live_pilot_receipt(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
