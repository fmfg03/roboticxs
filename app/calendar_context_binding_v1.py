from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.google_calendar_readonly_connector import CalendarReadResult
from app.hermes_runtime_bootstrap import DEFAULT_OWNER_ID, DEFAULT_ROBOT_ID


CALENDAR_CONTEXT_BINDING_V1_STAGE = "182P"
CALENDAR_CONTEXT_BINDING_V1_STATUS = "completed_calendar_context_binding_v1"
MAX_SOURCE_TRACE_EVENTS = 5


@dataclass(frozen=True, slots=True)
class CalendarContextSourceTrace:
    source_name: str
    status: str
    calendar_id: str
    window_start: str
    window_end: str
    event_refs: tuple[str, ...]
    blocked_reason: str | None
    calendar_write_allowed: bool

    def __post_init__(self) -> None:
        if self.source_name != "google_calendar_readonly":
            raise ValueError("182P Calendar trace must identify google_calendar_readonly.")
        if self.status not in {"connected", "not_connected", "blocked"}:
            raise ValueError("182P Calendar trace has unsupported status.")
        if self.calendar_write_allowed:
            raise ValueError("182P Calendar trace must not allow Calendar writes.")


@dataclass(frozen=True, slots=True)
class CalendarContextBindingV1Record:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    calendar_connected: bool
    calendar_event_count: int
    source_trace: CalendarContextSourceTrace
    read_only: bool
    calendar_write_allowed: bool
    gmail_read_allowed: bool
    gmail_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != CALENDAR_CONTEXT_BINDING_V1_STAGE:
            raise ValueError("182P Calendar binding records must identify the 182P stage.")
        if self.status != CALENDAR_CONTEXT_BINDING_V1_STATUS:
            raise ValueError("182P Calendar binding record must use the binding status.")
        if not self.read_only:
            raise ValueError("182P Calendar binding must remain read-only.")
        if any(
            (
                self.calendar_write_allowed,
                self.gmail_read_allowed,
                self.gmail_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("182P Calendar binding must not expand authority.")


def build_calendar_context_binding_v1_record(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
    calendar_result: CalendarReadResult,
) -> CalendarContextBindingV1Record:
    trace = build_calendar_context_source_trace(calendar_result=calendar_result)
    return CalendarContextBindingV1Record(
        stage=CALENDAR_CONTEXT_BINDING_V1_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=CALENDAR_CONTEXT_BINDING_V1_STATUS,
        calendar_connected=calendar_result.ok,
        calendar_event_count=len(calendar_result.events),
        source_trace=trace,
        read_only=True,
        calendar_write_allowed=False,
        gmail_read_allowed=False,
        gmail_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def build_calendar_context_source_trace(*, calendar_result: CalendarReadResult) -> CalendarContextSourceTrace:
    status = "connected" if calendar_result.ok else "not_connected"
    blocked_reason = None if calendar_result.ok else (calendar_result.error_code or "unknown_error")
    return CalendarContextSourceTrace(
        source_name="google_calendar_readonly",
        status=status,
        calendar_id=calendar_result.calendar_id,
        window_start=calendar_result.window_start,
        window_end=calendar_result.window_end,
        event_refs=tuple(
            _safe_event_ref(event_id=event.event_id, summary=event.summary, start=event.start)
            for event in calendar_result.events[:MAX_SOURCE_TRACE_EVENTS]
        ),
        blocked_reason=blocked_reason,
        calendar_write_allowed=False,
    )


def append_calendar_source_trace(reply_text: str, trace: CalendarContextSourceTrace) -> str:
    return "\n".join([reply_text, "", render_calendar_context_source_trace(trace)])


def render_calendar_context_binding_v1_record(record: CalendarContextBindingV1Record) -> str:
    return "\n".join(
        [
            "Calendar Context Binding v1",
            "",
            f"Stage: {record.stage}",
            f"Status: {record.status}",
            f"Calendar connected: {'true' if record.calendar_connected else 'false'}",
            f"Calendar events: {record.calendar_event_count}",
            "",
            render_calendar_context_source_trace(record.source_trace),
            "",
            "Boundaries:",
            "Calendar reads: read-only",
            "Calendar writes: disabled",
            "Gmail reads: disabled",
            "Gmail writes: disabled",
            "Memory Center mutation: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )


def render_calendar_context_source_trace(trace: CalendarContextSourceTrace) -> str:
    lines = [
        "Source trace:",
        f"- Calendar: {trace.status}",
        f"- Calendar id: {trace.calendar_id}",
        f"- Window: {trace.window_start} -> {trace.window_end}",
    ]
    if trace.blocked_reason:
        lines.extend(
            [
                f"- Reason: {trace.blocked_reason}",
                "- Next: run /checkup",
            ]
        )
    if trace.event_refs:
        lines.append("- Events used:")
        lines.extend(f"  - {event_ref}" for event_ref in trace.event_refs)
    else:
        lines.append("- Events used: none")
    lines.append("- Writes: disabled")
    return "\n".join(lines)


def _safe_event_ref(*, event_id: str, summary: str, start: str) -> str:
    return f"{event_id} | {summary} | {start}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.calendar_context_binding_v1")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    from app.google_calendar_readonly_connector import run_google_calendar_readonly_connector

    calendar_result = run_google_calendar_readonly_connector()
    record = build_calendar_context_binding_v1_record(calendar_result=calendar_result)
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_calendar_context_binding_v1_record(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
