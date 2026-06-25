from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from uuid import NAMESPACE_URL, uuid5


PROACTIVE_SUGGESTION_LOOP_STAGE = "170P"
TRIGGER_TYPES = (
    "upcoming_meeting_no_prep",
    "meeting_related_document",
    "email_thread_no_followup",
    "pdf_received_meeting_tomorrow",
    "open_task_due_soon",
)
NEXT_STEPS = {
    "upcoming_meeting_no_prep": "offer_prep_pack",
    "meeting_related_document": "offer_prep_pack",
    "email_thread_no_followup": "offer_followup_draft",
    "pdf_received_meeting_tomorrow": "offer_document_review_pack",
    "open_task_due_soon": "offer_task_summary",
}


@dataclass(frozen=True, slots=True)
class ProactiveSuggestionSignal:
    signal_id: str
    owner_id: str
    robot_id: str
    trigger_type: str
    title: str
    summary: str
    source_refs: tuple[str, ...]
    authorized_read_only: bool = True

    def __post_init__(self) -> None:
        if self.trigger_type not in TRIGGER_TYPES:
            raise ValueError("170P proactive signal trigger type must be known.")
        if not self.authorized_read_only:
            raise ValueError("170P proactive signals must come from authorized read-only context.")


@dataclass(frozen=True, slots=True)
class ProactiveSuggestionLoopRecord:
    stage: str
    owner_id: str
    robot_id: str
    suggestion_id: str
    trigger_type: str
    title: str
    suggestion_text: str
    suggested_next_step: str
    source_refs: tuple[str, ...]
    local_deterministic: bool
    live_send_allowed: bool
    callback_binding_allowed: bool
    execution_allowed: bool
    connector_activation_allowed: bool
    memory_write_allowed: bool
    external_write_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != PROACTIVE_SUGGESTION_LOOP_STAGE:
            raise ValueError("170P proactive suggestions must identify the 170P stage.")
        if self.trigger_type not in TRIGGER_TYPES:
            raise ValueError("170P proactive suggestion trigger type must be known.")
        if not self.local_deterministic:
            raise ValueError("170P proactive suggestions must remain local deterministic records.")
        if any(
            (
                self.live_send_allowed,
                self.callback_binding_allowed,
                self.execution_allowed,
                self.connector_activation_allowed,
                self.memory_write_allowed,
                self.external_write_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("170P proactive suggestions must not expand authority.")


def build_proactive_suggestion_loop_records(
    *,
    owner_id: str,
    robot_id: str,
    signals: tuple[ProactiveSuggestionSignal, ...],
) -> tuple[ProactiveSuggestionLoopRecord, ...]:
    records: list[ProactiveSuggestionLoopRecord] = []
    seen: set[str] = set()
    for signal in signals:
        if signal.owner_id != owner_id or signal.robot_id != robot_id:
            continue
        suggestion_id = _stable_id(owner_id, robot_id, signal.signal_id, signal.trigger_type)
        if suggestion_id in seen:
            continue
        seen.add(suggestion_id)
        records.append(
            ProactiveSuggestionLoopRecord(
                stage=PROACTIVE_SUGGESTION_LOOP_STAGE,
                owner_id=owner_id,
                robot_id=robot_id,
                suggestion_id=suggestion_id,
                trigger_type=signal.trigger_type,
                title=signal.title,
                suggestion_text=_suggestion_text(signal),
                suggested_next_step=NEXT_STEPS[signal.trigger_type],
                source_refs=signal.source_refs,
                local_deterministic=True,
                live_send_allowed=False,
                callback_binding_allowed=False,
                execution_allowed=False,
                connector_activation_allowed=False,
                memory_write_allowed=False,
                external_write_allowed=False,
                worker_dispatch_allowed=False,
            )
        )
    return tuple(records)


def render_proactive_suggestion(record: ProactiveSuggestionLoopRecord) -> str:
    return "\n".join(
        [
            "Proactive Suggestion",
            "",
            f"Stage: {record.stage}",
            f"Trigger: {record.trigger_type}",
            f"Title: {record.title}",
            record.suggestion_text,
            f"Suggested next step: {record.suggested_next_step}",
            "",
            "No action has been taken.",
            "Live send: disabled",
            "Callbacks: disabled",
            "Execution: disabled",
            "Connector activation: disabled",
            "Memory writes: disabled",
            "External writes: disabled",
        ]
    )


def _suggestion_text(signal: ProactiveSuggestionSignal) -> str:
    if signal.trigger_type == "upcoming_meeting_no_prep":
        return f"You have an upcoming meeting that does not appear to have prep yet: {signal.summary}. Do you want a prep pack?"
    if signal.trigger_type == "meeting_related_document":
        return f"I found a document that appears related to a meeting: {signal.summary}. Do you want me to prepare a prep pack?"
    if signal.trigger_type == "email_thread_no_followup":
        return f"I found an email thread that may need follow-up: {signal.summary}. Do you want a draft?"
    if signal.trigger_type == "pdf_received_meeting_tomorrow":
        return f"I found a PDF and a meeting tomorrow: {signal.summary}. Do you want a draft review pack?"
    return f"I found an open task that may be due soon: {signal.summary}. Do you want a short status summary?"


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.proactive_suggestion_loop")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    records = build_proactive_suggestion_loop_records(owner_id="local-owner", robot_id="roboticxs-dev", signals=())
    if args.as_json:
        print(json.dumps([asdict(record) for record in records], sort_keys=True, indent=2))
    else:
        print("No proactive suggestions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
