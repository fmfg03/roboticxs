from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.google_oauth_workspace import resolve_google_workspace_access_token


GMAIL_READONLY_CONTEXT_SCAN_STAGE = "163P"
GMAIL_MESSAGES_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
DEFAULT_GMAIL_QUERY = "newer_than:30d"
DEFAULT_MAX_RESULTS = 10
DEFAULT_TIMEOUT_SECONDS = 30
CONTEXT_MARKERS = (
    "meeting",
    "prep",
    "follow-up",
    "follow up",
    "proposal",
    "review",
    "demo",
    "attached",
    "attachment",
    "pdf",
    "contract",
)


class GmailReadonlyHttpClientProtocol(Protocol):
    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        ...


class UrllibGmailReadonlyHttpClient:
    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        query = urlencode(params)
        request = Request(
            f"{url}?{query}" if query else url,
            headers=headers,
            method="GET",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True, slots=True)
class GmailReadonlyConfig:
    access_token: str
    query: str
    max_results: int
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class GmailMessageContext:
    message_id: str
    thread_id: str
    subject: str
    from_header: str
    date_header: str
    snippet: str
    attachment_count: int
    labels: tuple[str, ...]
    source: str


@dataclass(frozen=True, slots=True)
class GmailContextSignal:
    signal_id: str
    message_id: str
    thread_id: str
    signal_type: str
    summary: str
    confidence: str


@dataclass(frozen=True, slots=True)
class GmailReadonlyContextScanRecord:
    stage: str
    status: str
    query: str
    messages: tuple[GmailMessageContext, ...]
    signals: tuple[GmailContextSignal, ...]
    read_only: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    calendar_write_allowed: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.stage != GMAIL_READONLY_CONTEXT_SCAN_STAGE:
            raise ValueError("163P Gmail context scans must identify the 163P stage.")
        if not self.read_only:
            raise ValueError("163P Gmail context scans must be read-only.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.calendar_write_allowed,
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("163P Gmail context scans must not expand authority.")


def load_gmail_readonly_config_from_env(env: dict[str, str] | None = None) -> GmailReadonlyConfig:
    source = os.environ if env is None else env
    access_token = source.get("ROBOTICXS_GOOGLE_GMAIL_ACCESS_TOKEN", "").strip()
    if not access_token:
        access_token = resolve_google_workspace_access_token(env=source)
    return GmailReadonlyConfig(
        access_token=access_token,
        query=source.get("ROBOTICXS_GMAIL_CONTEXT_QUERY", DEFAULT_GMAIL_QUERY).strip() or DEFAULT_GMAIL_QUERY,
        max_results=int(source.get("ROBOTICXS_GMAIL_CONTEXT_MAX_RESULTS", str(DEFAULT_MAX_RESULTS))),
        timeout_seconds=int(source.get("ROBOTICXS_GMAIL_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
    )


def run_gmail_readonly_context_scan(
    *,
    env: dict[str, str] | None = None,
    http_client: GmailReadonlyHttpClientProtocol | None = None,
) -> GmailReadonlyContextScanRecord:
    config = load_gmail_readonly_config_from_env(env=env)
    return read_gmail_context(config=config, http_client=http_client)


def read_gmail_context(
    *,
    config: GmailReadonlyConfig,
    http_client: GmailReadonlyHttpClientProtocol | None = None,
) -> GmailReadonlyContextScanRecord:
    if not config.access_token:
        return _blocked_scan(config.query, "missing_access_token")
    if config.max_results <= 0:
        return _blocked_scan(config.query, "rejected_invalid_max_results")
    if config.timeout_seconds <= 0:
        return _blocked_scan(config.query, "rejected_invalid_timeout_seconds")
    client = http_client or UrllibGmailReadonlyHttpClient()
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Accept": "application/json",
    }
    try:
        listing = client.get_json(
            GMAIL_MESSAGES_ENDPOINT,
            headers=headers,
            params={"q": config.query, "maxResults": str(config.max_results)},
            timeout_seconds=config.timeout_seconds,
        )
        message_refs = listing.get("messages")
        if not isinstance(message_refs, list):
            message_refs = []
        contexts = tuple(
            _message_context_from_payload(
                client.get_json(
                    f"{GMAIL_MESSAGES_ENDPOINT}/{message_id}",
                    headers=headers,
                    params={
                        "format": "metadata",
                        "metadataHeaders": "Subject",
                    },
                    timeout_seconds=config.timeout_seconds,
                )
            )
            for message_id in _message_ids(message_refs)[: config.max_results]
        )
    except (HTTPError, OSError, URLError, ValueError, json.JSONDecodeError):
        return _blocked_scan(config.query, "gmail_read_failed_closed")
    signals = tuple(signal for context in contexts for signal in _signals_from_context(context))
    status = "completed_with_signals" if signals else "completed_no_signals"
    return GmailReadonlyContextScanRecord(
        stage=GMAIL_READONLY_CONTEXT_SCAN_STAGE,
        status=status,
        query=config.query,
        messages=contexts,
        signals=signals,
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
    )


def render_gmail_readonly_context_scan(record: GmailReadonlyContextScanRecord) -> str:
    lines = [
        "Gmail Read-Only Context Scan",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Query: {record.query}",
        f"Messages scanned: {len(record.messages)}",
        f"Signals: {len(record.signals)}",
        "",
        "Signals:",
    ]
    if record.signals:
        lines.extend(f"- {signal.signal_type}: {signal.summary}" for signal in record.signals)
    else:
        lines.append("- No Gmail context signals were produced.")
    lines.extend(
        [
            "",
            "Boundaries:",
            "Gmail send: disabled",
            "Gmail modify/archive/label: disabled",
            "Gmail delete: disabled",
            "Calendar writes: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _blocked_scan(query: str, error_code: str) -> GmailReadonlyContextScanRecord:
    return GmailReadonlyContextScanRecord(
        stage=GMAIL_READONLY_CONTEXT_SCAN_STAGE,
        status="blocked_gmail_unavailable",
        query=query,
        messages=(),
        signals=(),
        read_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        gmail_delete_allowed=False,
        calendar_write_allowed=False,
        memory_center_mutated=False,
        proposed_memory_written=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        error_code=error_code,
    )


def _message_ids(message_refs: list[object]) -> tuple[str, ...]:
    ids: list[str] = []
    for ref in message_refs:
        if isinstance(ref, dict) and isinstance(ref.get("id"), str) and ref["id"].strip():
            ids.append(ref["id"].strip())
    return tuple(ids)


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
        source="gmail_readonly_metadata",
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


def _signals_from_context(context: GmailMessageContext) -> tuple[GmailContextSignal, ...]:
    normalized = f"{context.subject} {context.snippet}".lower()
    signals: list[GmailContextSignal] = []
    if any(marker in normalized for marker in CONTEXT_MARKERS):
        signals.append(
            GmailContextSignal(
                signal_id=f"gmail-signal:{context.message_id}:context",
                message_id=context.message_id,
                thread_id=context.thread_id,
                signal_type="related_context",
                summary=f"{context.subject} may contain meeting, follow-up, proposal, or review context.",
                confidence="medium",
            )
        )
    if context.attachment_count:
        signals.append(
            GmailContextSignal(
                signal_id=f"gmail-signal:{context.message_id}:attachments",
                message_id=context.message_id,
                thread_id=context.thread_id,
                signal_type="attachment_context",
                summary=f"{context.subject} has {context.attachment_count} attachment(s) that may be relevant for prep.",
                confidence="medium",
            )
        )
    if "follow-up" in normalized or "follow up" in normalized:
        signals.append(
            GmailContextSignal(
                signal_id=f"gmail-signal:{context.message_id}:followup",
                message_id=context.message_id,
                thread_id=context.thread_id,
                signal_type="followup_context",
                summary=f"{context.subject} may contain a follow-up thread.",
                confidence="low",
            )
        )
    return tuple(signals)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.gmail_readonly_context_scan")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    record = run_gmail_readonly_context_scan()
    if args.as_json:
        print(json.dumps(asdict(record), sort_keys=True, indent=2))
    else:
        print(render_gmail_readonly_context_scan(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
