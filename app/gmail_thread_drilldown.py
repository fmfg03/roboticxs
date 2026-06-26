from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.gmail_readonly_context_scan import (
    DEFAULT_TIMEOUT_SECONDS,
    GMAIL_MESSAGES_ENDPOINT,
    GmailMessageContext,
    GmailReadonlyConfig,
    GmailReadonlyHttpClientProtocol,
    UrllibGmailReadonlyHttpClient,
    load_gmail_readonly_config_from_env,
)


GMAIL_THREAD_DRILLDOWN_STAGE = "176P"
GMAIL_THREADS_ENDPOINT = GMAIL_MESSAGES_ENDPOINT.replace("/messages", "/threads")
MAX_THREAD_MESSAGES = 8


@dataclass(frozen=True, slots=True)
class GmailThreadDrilldownRecord:
    stage: str
    status: str
    thread_id: str
    subject: str
    messages: tuple[GmailMessageContext, ...]
    timeline_lines: tuple[str, ...]
    context_lines: tuple[str, ...]
    attachment_lines: tuple[str, ...]
    blocked_reason: str | None
    read_only: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    calendar_write_allowed: bool
    memory_center_mutated: bool
    draft_created: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != GMAIL_THREAD_DRILLDOWN_STAGE:
            raise ValueError("176P Gmail thread drilldowns must identify the 176P stage.")
        if not self.read_only:
            raise ValueError("176P Gmail thread drilldowns must be read-only.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.calendar_write_allowed,
                self.memory_center_mutated,
                self.draft_created,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("176P Gmail thread drilldowns must not expand authority.")


def run_gmail_thread_drilldown(
    *,
    thread_id: str,
    env: dict[str, str] | None = None,
    http_client: GmailReadonlyHttpClientProtocol | None = None,
) -> GmailThreadDrilldownRecord:
    config = load_gmail_readonly_config_from_env(env=env)
    return read_gmail_thread(config=config, thread_id=thread_id, http_client=http_client)


def read_gmail_thread(
    *,
    config: GmailReadonlyConfig,
    thread_id: str,
    http_client: GmailReadonlyHttpClientProtocol | None = None,
) -> GmailThreadDrilldownRecord:
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        return _blocked_record(thread_id="", error_code="missing_thread_id")
    if not config.access_token:
        return _blocked_record(thread_id=normalized_thread_id, error_code="missing_access_token")
    if config.timeout_seconds <= 0:
        return _blocked_record(thread_id=normalized_thread_id, error_code="rejected_invalid_timeout_seconds")
    client = http_client or UrllibGmailReadonlyHttpClient()
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Accept": "application/json",
    }
    try:
        payload = client.get_json(
            f"{GMAIL_THREADS_ENDPOINT}/{normalized_thread_id}",
            headers=headers,
            params={
                "format": "metadata",
                "metadataHeaders": "Subject",
                "metadataHeaders": "From",
                "metadataHeaders": "Date",
            },
            timeout_seconds=config.timeout_seconds or DEFAULT_TIMEOUT_SECONDS,
        )
        messages = tuple(_message_context_from_payload(item) for item in _message_payloads(payload))
    except Exception:
        return _blocked_record(thread_id=normalized_thread_id, error_code="gmail_thread_read_failed_closed")
    subject = _subject(messages)
    status = "completed_with_messages" if messages else "completed_empty_thread"
    return GmailThreadDrilldownRecord(
        stage=GMAIL_THREAD_DRILLDOWN_STAGE,
        status=status,
        thread_id=normalized_thread_id,
        subject=subject,
        messages=messages,
        timeline_lines=_timeline_lines(messages),
        context_lines=_context_lines(messages),
        attachment_lines=_attachment_lines(messages),
        blocked_reason=None,
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        draft_created=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_gmail_thread_drilldown(record: GmailThreadDrilldownRecord) -> str:
    lines = [
        "Gmail Thread Drilldown",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Thread: {record.thread_id or '(missing-thread-id)'}",
        f"Subject: {record.subject}",
        f"Messages: {len(record.messages)}",
        "",
        "Timeline:",
        *_section_lines(record.timeline_lines, "No messages are visible in this thread."),
        "",
        "Context:",
        *_section_lines(record.context_lines, "No context snippets are visible in this thread."),
        "",
        "Attachments:",
        *_section_lines(record.attachment_lines, "No attachments are visible from metadata."),
    ]
    if record.blocked_reason:
        lines.extend(["", f"Blocked reason: {record.blocked_reason}"])
    lines.extend(
        [
            "",
            "Boundaries:",
            "Gmail send: disabled",
            "Gmail modify/archive/label: disabled",
            "Gmail delete: disabled",
            "Calendar writes: disabled",
            "Memory Center mutation: disabled",
            "Draft creation: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _blocked_record(*, thread_id: str, error_code: str) -> GmailThreadDrilldownRecord:
    return GmailThreadDrilldownRecord(
        stage=GMAIL_THREAD_DRILLDOWN_STAGE,
        status="blocked_gmail_thread_unavailable",
        thread_id=thread_id,
        subject="(unavailable)",
        messages=(),
        timeline_lines=(),
        context_lines=(),
        attachment_lines=(),
        blocked_reason=error_code,
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        draft_created=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def _message_payloads(payload: dict) -> tuple[dict, ...]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return ()
    return tuple(item for item in messages[:MAX_THREAD_MESSAGES] if isinstance(item, dict))


def _message_context_from_payload(payload: dict) -> GmailMessageContext:
    payload_payload = payload.get("payload")
    headers_payload = payload_payload.get("headers") if isinstance(payload_payload, dict) else []
    headers = _headers_map(headers_payload if isinstance(headers_payload, list) else [])
    parts = payload_payload.get("parts") if isinstance(payload_payload, dict) else []
    return GmailMessageContext(
        message_id=_text(payload.get("id")) or "(missing-message-id)",
        thread_id=_text(payload.get("threadId")) or "(missing-thread-id)",
        subject=headers.get("subject", "(No subject)"),
        from_header=headers.get("from", ""),
        date_header=headers.get("date", ""),
        snippet=_text(payload.get("snippet")) or "",
        attachment_count=_attachment_count(parts if isinstance(parts, list) else []),
        labels=tuple(label for label in payload.get("labelIds", ()) if isinstance(label, str)),
        source="gmail_thread_drilldown_metadata",
    )


def _headers_map(headers_payload: list[object]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in headers_payload:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("name"))
        value = _text(item.get("value"))
        if name and value:
            headers[name.lower()] = value
    return headers


def _attachment_count(parts: list[object]) -> int:
    count = 0
    for part in parts:
        if not isinstance(part, dict):
            continue
        filename = _text(part.get("filename"))
        body = part.get("body")
        attachment_id = body.get("attachmentId") if isinstance(body, dict) else None
        if filename and attachment_id:
            count += 1
        nested = part.get("parts")
        if isinstance(nested, list):
            count += _attachment_count(nested)
    return count


def _subject(messages: tuple[GmailMessageContext, ...]) -> str:
    for message in messages:
        if message.subject:
            return message.subject
    return "(No subject)"


def _timeline_lines(messages: tuple[GmailMessageContext, ...]) -> tuple[str, ...]:
    return tuple(
        f"{message.date_header or '(no date)'} | {message.from_header or '(unknown sender)'} | {message.subject}"
        for message in messages
    )


def _context_lines(messages: tuple[GmailMessageContext, ...]) -> tuple[str, ...]:
    return tuple(
        f"{message.message_id}: {message.snippet}"
        for message in messages
        if message.snippet
    )


def _attachment_lines(messages: tuple[GmailMessageContext, ...]) -> tuple[str, ...]:
    return tuple(
        f"{message.message_id}: {message.attachment_count} attachment(s)"
        for message in messages
        if message.attachment_count
    )


def _section_lines(lines: tuple[str, ...], empty_line: str) -> tuple[str, ...]:
    if not lines:
        return (f"- {empty_line}",)
    return tuple(f"- {line}" for line in lines)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.gmail_thread_drilldown")
    parser.add_argument("thread_id")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = run_gmail_thread_drilldown(thread_id=args.thread_id)
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_gmail_thread_drilldown(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
