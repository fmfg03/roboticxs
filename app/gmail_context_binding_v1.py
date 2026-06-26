from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.gmail_readonly_context_scan import GmailReadonlyContextScanRecord, run_gmail_readonly_context_scan
from app.hermes_runtime_bootstrap import DEFAULT_OWNER_ID, DEFAULT_ROBOT_ID


GMAIL_CONTEXT_BINDING_V1_STAGE = "183P"
GMAIL_CONTEXT_BINDING_V1_STATUS = "completed_gmail_context_binding_v1"
MAX_GMAIL_TRACE_REFS = 5


@dataclass(frozen=True, slots=True)
class GmailContextSourceTrace:
    source_name: str
    status: str
    query: str
    messages_scanned: int
    thread_refs: tuple[str, ...]
    signal_refs: tuple[str, ...]
    blocked_reason: str | None
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool

    def __post_init__(self) -> None:
        if self.source_name != "gmail_readonly_metadata":
            raise ValueError("183P Gmail trace must identify gmail_readonly_metadata.")
        if self.status not in {"connected", "connected_no_signals", "not_connected", "blocked"}:
            raise ValueError("183P Gmail trace has unsupported status.")
        if any((self.gmail_send_allowed, self.gmail_modify_allowed, self.gmail_delete_allowed)):
            raise ValueError("183P Gmail trace must not allow Gmail writes.")


@dataclass(frozen=True, slots=True)
class GmailContextBindingV1Record:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    gmail_connected: bool
    messages_scanned: int
    signals_found: int
    source_trace: GmailContextSourceTrace
    read_only: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    calendar_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != GMAIL_CONTEXT_BINDING_V1_STAGE:
            raise ValueError("183P Gmail binding records must identify the 183P stage.")
        if self.status != GMAIL_CONTEXT_BINDING_V1_STATUS:
            raise ValueError("183P Gmail binding record must use the binding status.")
        if not self.read_only:
            raise ValueError("183P Gmail binding must remain read-only.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.calendar_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("183P Gmail binding must not expand authority.")


def build_gmail_context_binding_v1_record(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
    gmail_scan: GmailReadonlyContextScanRecord,
) -> GmailContextBindingV1Record:
    trace = build_gmail_context_source_trace(gmail_scan=gmail_scan)
    gmail_connected = trace.status in {"connected", "connected_no_signals"}
    return GmailContextBindingV1Record(
        stage=GMAIL_CONTEXT_BINDING_V1_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=GMAIL_CONTEXT_BINDING_V1_STATUS,
        gmail_connected=gmail_connected,
        messages_scanned=len(gmail_scan.messages),
        signals_found=len(gmail_scan.signals),
        source_trace=trace,
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def build_gmail_context_source_trace(*, gmail_scan: GmailReadonlyContextScanRecord) -> GmailContextSourceTrace:
    if gmail_scan.error_code:
        status = "not_connected" if gmail_scan.error_code == "missing_access_token" else "blocked"
        blocked_reason = gmail_scan.error_code
    else:
        status = "connected" if gmail_scan.signals else "connected_no_signals"
        blocked_reason = None
    return GmailContextSourceTrace(
        source_name="gmail_readonly_metadata",
        status=status,
        query=gmail_scan.query,
        messages_scanned=len(gmail_scan.messages),
        thread_refs=tuple(
            _safe_thread_ref(
                thread_id=message.thread_id,
                message_id=message.message_id,
                subject=message.subject,
            )
            for message in gmail_scan.messages[:MAX_GMAIL_TRACE_REFS]
        ),
        signal_refs=tuple(
            _safe_signal_ref(signal_type=signal.signal_type, summary=signal.summary)
            for signal in gmail_scan.signals[:MAX_GMAIL_TRACE_REFS]
        ),
        blocked_reason=blocked_reason,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
    )


def append_gmail_source_trace(reply_text: str, trace: GmailContextSourceTrace) -> str:
    return "\n".join([reply_text, "", render_gmail_context_source_trace(trace)])


def render_gmail_context_binding_v1_record(record: GmailContextBindingV1Record) -> str:
    return "\n".join(
        [
            "Gmail Context Binding v1",
            "",
            f"Stage: {record.stage}",
            f"Status: {record.status}",
            f"Gmail connected: {'true' if record.gmail_connected else 'false'}",
            f"Messages scanned: {record.messages_scanned}",
            f"Signals found: {record.signals_found}",
            "",
            render_gmail_context_source_trace(record.source_trace),
            "",
            "Boundaries:",
            "Gmail reads: read-only metadata",
            "Gmail send: disabled",
            "Gmail modify/archive/label: disabled",
            "Gmail delete: disabled",
            "Calendar writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )


def render_gmail_context_source_trace(trace: GmailContextSourceTrace) -> str:
    lines = [
        "Gmail source trace:",
        f"- Gmail: {trace.status}",
        f"- Query: {trace.query}",
        f"- Messages scanned: {trace.messages_scanned}",
    ]
    if trace.blocked_reason:
        lines.extend(
            [
                f"- Reason: {trace.blocked_reason}",
                "- Next: run /checkup",
            ]
        )
    if trace.thread_refs:
        lines.append("- Threads used:")
        lines.extend(f"  - {thread_ref}" for thread_ref in trace.thread_refs)
    else:
        lines.append("- Threads used: none")
    if trace.signal_refs:
        lines.append("- Signals used:")
        lines.extend(f"  - {signal_ref}" for signal_ref in trace.signal_refs)
    else:
        lines.append("- Signals used: none")
    lines.append("- Writes: disabled")
    return "\n".join(lines)


def _safe_thread_ref(*, thread_id: str, message_id: str, subject: str) -> str:
    return f"{thread_id} | {message_id} | {_bounded(subject)}"


def _safe_signal_ref(*, signal_type: str, summary: str) -> str:
    return f"{signal_type} | {_bounded(summary)}"


def _bounded(value: str, limit: int = 160) -> str:
    compact = " ".join(value.split())
    return compact[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.gmail_context_binding_v1")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = build_gmail_context_binding_v1_record(gmail_scan=run_gmail_readonly_context_scan())
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_gmail_context_binding_v1_record(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
