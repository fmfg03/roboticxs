from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from app.calendar_context_binding_v1 import CalendarContextSourceTrace
from app.gmail_context_binding_v1 import GmailContextSourceTrace
from app.hermes_runtime_bootstrap import DEFAULT_OWNER_ID, DEFAULT_ROBOT_ID
from app.telegram_memory_center_commands import TelegramMemoryCenterSnapshot


SOURCE_TRACE_RECEIPTS_STAGE = "184P"
SOURCE_TRACE_RECEIPTS_STATUS = "completed_source_trace_receipts_v0"
SOURCE_TRACE_RECEIPT_STATUSES = frozenset(
    {
        "used",
        "not_connected",
        "not_used",
        "blocked",
        "disabled",
        "approval_required",
    }
)
MAX_RECEIPT_REFS = 5
SECRET_MARKERS = (
    "authorization",
    "bearer",
    "refresh_token",
    "client_secret",
    "token-",
    "gmail-token",
    "calendar-token",
)


@dataclass(frozen=True, slots=True)
class SourceTraceReceiptItem:
    source_name: str
    status: str
    summary: str
    refs: tuple[str, ...] = ()
    reason: str | None = None
    next_step: str | None = None

    def __post_init__(self) -> None:
        if self.status not in SOURCE_TRACE_RECEIPT_STATUSES:
            raise ValueError("184P source trace receipt item has unsupported status.")
        if not self.source_name:
            raise ValueError("184P source trace receipt items require a source name.")


@dataclass(frozen=True, slots=True)
class SourceTraceActionBoundary:
    action_name: str
    status: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in SOURCE_TRACE_RECEIPT_STATUSES:
            raise ValueError("184P source trace action boundary has unsupported status.")
        if self.status not in {"disabled", "approval_required", "blocked"}:
            raise ValueError("184P action boundaries must be disabled, approval-required, or blocked.")


@dataclass(frozen=True, slots=True)
class SourceTraceReceipt:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    items: tuple[SourceTraceReceiptItem, ...]
    action_boundaries: tuple[SourceTraceActionBoundary, ...]
    read_only: bool
    connector_activation_allowed: bool
    oauth_flow_allowed: bool
    calendar_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    gmail_delete_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SOURCE_TRACE_RECEIPTS_STAGE:
            raise ValueError("184P source trace receipts must identify the 184P stage.")
        if self.status != SOURCE_TRACE_RECEIPTS_STATUS:
            raise ValueError("184P source trace receipts must use the 184P status.")
        if not self.read_only:
            raise ValueError("184P source trace receipts must remain read-only.")
        if any(
            (
                self.connector_activation_allowed,
                self.oauth_flow_allowed,
                self.calendar_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.gmail_delete_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("184P source trace receipts must not expand authority.")


def build_source_trace_receipt(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
    calendar_trace: CalendarContextSourceTrace | None = None,
    gmail_trace: GmailContextSourceTrace | None = None,
    memory_snapshot: TelegramMemoryCenterSnapshot | None = None,
    document_reviews: tuple[object, ...] = (),
    draft_queue: object | None = None,
    usage_summary: object | None = None,
) -> SourceTraceReceipt:
    return SourceTraceReceipt(
        stage=SOURCE_TRACE_RECEIPTS_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=SOURCE_TRACE_RECEIPTS_STATUS,
        items=(
            _calendar_item(calendar_trace),
            _gmail_item(gmail_trace),
            _memory_item(memory_snapshot),
            _documents_item(document_reviews),
            _draft_queue_item(draft_queue),
            _usage_cost_item(usage_summary),
        ),
        action_boundaries=_default_action_boundaries(),
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


def append_source_trace_receipt(reply_text: str, receipt: SourceTraceReceipt) -> str:
    return "\n".join([reply_text, "", render_source_trace_receipt(receipt)])


def render_source_trace_receipt(receipt: SourceTraceReceipt) -> str:
    lines = [
        "Source Trace Receipt",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        "Sources:",
    ]
    for item in receipt.items:
        lines.append(f"- {item.source_name}: {item.status} - {_safe_text(item.summary)}")
        if item.reason:
            lines.append(f"  Reason: {_safe_text(item.reason)}")
        if item.next_step:
            lines.append(f"  Next: {_safe_text(item.next_step)}")
        if item.refs:
            lines.append("  Refs:")
            lines.extend(f"  - {_safe_text(ref)}" for ref in item.refs[:MAX_RECEIPT_REFS])
        else:
            lines.append("  Refs: none")
    lines.extend(["", "Action boundaries:"])
    lines.extend(
        f"- {boundary.action_name}: {boundary.status} - {_safe_text(boundary.reason)}"
        for boundary in receipt.action_boundaries
    )
    lines.extend(
        [
            "",
            "Authority:",
            "Connector activation: disabled",
            "OAuth flow: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _calendar_item(trace: CalendarContextSourceTrace | None) -> SourceTraceReceiptItem:
    if trace is None:
        return SourceTraceReceiptItem(
            source_name="Calendar",
            status="not_used",
            summary="Calendar source trace was not provided for this reply.",
        )
    status = "used" if trace.status == "connected" else trace.status
    return SourceTraceReceiptItem(
        source_name="Calendar",
        status=status,
        summary=f"{len(trace.event_refs)} calendar event(s) considered.",
        refs=trace.event_refs,
        reason=trace.blocked_reason,
        next_step="run /checkup" if trace.blocked_reason else None,
    )


def _gmail_item(trace: GmailContextSourceTrace | None) -> SourceTraceReceiptItem:
    if trace is None:
        return SourceTraceReceiptItem(
            source_name="Gmail",
            status="not_used",
            summary="Gmail source trace was not provided for this reply.",
        )
    status = "used" if trace.status in {"connected", "connected_no_signals"} else trace.status
    refs = trace.signal_refs if trace.signal_refs else trace.thread_refs
    return SourceTraceReceiptItem(
        source_name="Gmail",
        status=status,
        summary=f"{trace.messages_scanned} Gmail message(s) scanned as read-only metadata.",
        refs=refs,
        reason=trace.blocked_reason,
        next_step="run /checkup" if trace.blocked_reason else None,
    )


def _memory_item(snapshot: TelegramMemoryCenterSnapshot | None) -> SourceTraceReceiptItem:
    if snapshot is None:
        return SourceTraceReceiptItem(
            source_name="Memory",
            status="not_used",
            summary="Memory snapshot was not provided for this reply.",
        )
    if snapshot.pending_total_count:
        return SourceTraceReceiptItem(
            source_name="Memory",
            status="approval_required",
            summary=f"{snapshot.pending_total_count} pending memory proposal(s) require owner approval.",
            refs=tuple(proposal.proposal_id for proposal in snapshot.pending_proposals),
            next_step="use /memory_review",
        )
    if snapshot.approved_total_count:
        return SourceTraceReceiptItem(
            source_name="Memory",
            status="used",
            summary=f"{snapshot.approved_total_count} approved memory item(s) available.",
            refs=tuple(
                f"{memory.item_id} | {memory.memory_kind} | {memory.summary}"
                for memory in snapshot.approved_memories
            ),
        )
    return SourceTraceReceiptItem(
        source_name="Memory",
        status="not_used",
        summary="No approved or pending memory was visible in the local snapshot.",
    )


def _documents_item(document_reviews: tuple[object, ...]) -> SourceTraceReceiptItem:
    if not document_reviews:
        return SourceTraceReceiptItem(
            source_name="Documents",
            status="not_used",
            summary="No document review pack was attached to this reply.",
        )
    refs = tuple(str(getattr(review, "document_title", "document")) for review in document_reviews)
    return SourceTraceReceiptItem(
        source_name="Documents",
        status="used",
        summary=f"{len(document_reviews)} draft-only document review pack(s) attached.",
        refs=refs,
    )


def _draft_queue_item(draft_queue: object | None) -> SourceTraceReceiptItem:
    if draft_queue is None:
        return SourceTraceReceiptItem(
            source_name="Draft Queue",
            status="not_used",
            summary="No local draft queue was attached to this reply.",
        )
    draft_count = len(getattr(draft_queue, "drafts", ()))
    return SourceTraceReceiptItem(
        source_name="Draft Queue",
        status="approval_required" if draft_count else "not_used",
        summary=f"{draft_count} local draft(s) waiting for explicit confirmation.",
        next_step="use /drafts" if draft_count else None,
    )


def _usage_cost_item(usage_summary: object | None) -> SourceTraceReceiptItem:
    if usage_summary is None:
        return SourceTraceReceiptItem(
            source_name="Usage/Cost",
            status="not_used",
            summary="Usage ledger is not bound to this 184P receipt.",
        )
    return SourceTraceReceiptItem(
        source_name="Usage/Cost",
        status="used",
        summary="Usage summary was attached without expanding authority.",
    )


def _default_action_boundaries() -> tuple[SourceTraceActionBoundary, ...]:
    return (
        SourceTraceActionBoundary(
            action_name="Gmail send",
            status="disabled",
            reason="184P receipts do not authorize email sends.",
        ),
        SourceTraceActionBoundary(
            action_name="Gmail modify/delete",
            status="disabled",
            reason="184P receipts do not archive, label, modify, or delete Gmail data.",
        ),
        SourceTraceActionBoundary(
            action_name="Calendar writes",
            status="disabled",
            reason="184P receipts do not create, update, or delete Calendar events.",
        ),
        SourceTraceActionBoundary(
            action_name="Memory mutation",
            status="approval_required",
            reason="Memory changes require explicit owner approval and a separate approved flow.",
        ),
        SourceTraceActionBoundary(
            action_name="External writes",
            status="disabled",
            reason="184P receipts are local render-only evidence.",
        ),
    )


def _safe_text(value: str) -> str:
    compact = " ".join(value.split())
    lowered = compact.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        return "[redacted]"
    return compact[:240]


def main() -> int:
    receipt = build_source_trace_receipt()
    print(json.dumps(asdict(receipt), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
