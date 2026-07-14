from __future__ import annotations

from dataclasses import dataclass

from app.founder_feedback_capture import FounderFeedbackCaptureReceipt, SUPPORTED_FEEDBACK_TAGS


FEEDBACK_LEDGER_TAGS_STAGE = "204P"
FEEDBACK_LEDGER_TAGS_STATUS = "local_feedback_ledger_v0"


@dataclass(frozen=True, slots=True)
class FeedbackLedgerEntry:
    stage: str
    feedback_id: str
    owner_id: str
    robot_id: str
    item_id: str
    item_type: str
    tag: str
    comment: str
    source_trace_id: str
    created_at: str
    status: str
    storage_scope: str
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != FEEDBACK_LEDGER_TAGS_STAGE:
            raise ValueError("204P feedback ledger entries must identify the 204P stage.")
        if not all((self.feedback_id, self.owner_id, self.robot_id, self.item_id, self.item_type, self.created_at)):
            raise ValueError("204P feedback ledger entries require identity, item binding, and timestamp.")
        if self.tag not in SUPPORTED_FEEDBACK_TAGS:
            raise ValueError("204P feedback ledger tag is unsupported.")
        if self.status not in {"recorded", "rejected"}:
            raise ValueError("204P feedback ledger status is unsupported.")
        if self.storage_scope != "local_structured_ledger":
            raise ValueError("204P feedback ledger must remain local structured storage.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("204P feedback ledger entries must be redacted and approval-preserving.")
        if any(
            (
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("204P feedback ledger entries must not expand external write authority.")


@dataclass(frozen=True, slots=True)
class FeedbackLedger:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    entries: tuple[FeedbackLedgerEntry, ...]
    total_entries: int
    top_tags: tuple[tuple[str, int], ...]
    storage_scope: str
    retrieval_available: bool
    external_write_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != FEEDBACK_LEDGER_TAGS_STAGE:
            raise ValueError("204P feedback ledgers must identify the 204P stage.")
        if self.status != FEEDBACK_LEDGER_TAGS_STATUS:
            raise ValueError("204P feedback ledgers must use the ledger status.")
        if self.total_entries != len(self.entries):
            raise ValueError("204P feedback ledger count must match entries.")
        if self.storage_scope != "local_structured_ledger" or not self.retrieval_available:
            raise ValueError("204P feedback ledger must be locally retrievable.")
        if self.external_write_allowed or not self.secrets_redacted:
            raise ValueError("204P feedback ledger must not expand external writes or expose secrets.")


def build_feedback_ledger_entry_from_capture(
    receipt: FounderFeedbackCaptureReceipt,
    *,
    created_at: str,
) -> FeedbackLedgerEntry:
    return FeedbackLedgerEntry(
        stage=FEEDBACK_LEDGER_TAGS_STAGE,
        feedback_id=f"fb-{receipt.item_type}-{receipt.item_id}-{receipt.tag}".replace(" ", "-"),
        owner_id=receipt.owner_id,
        robot_id=receipt.robot_id,
        item_id=receipt.item_id,
        item_type=receipt.item_type,
        tag=receipt.tag,
        comment=receipt.comment,
        source_trace_id=receipt.source_trace_id,
        created_at=created_at,
        status="recorded",
        storage_scope="local_structured_ledger",
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def build_feedback_ledger(
    *,
    owner_id: str,
    robot_id: str,
    entries: tuple[FeedbackLedgerEntry, ...] = (),
) -> FeedbackLedger:
    scoped_entries = tuple(
        entry for entry in entries if entry.owner_id == owner_id and entry.robot_id == robot_id and entry.status == "recorded"
    )
    tag_counts: dict[str, int] = {}
    for entry in scoped_entries:
        tag_counts[entry.tag] = tag_counts.get(entry.tag, 0) + 1
    top_tags = tuple(sorted(tag_counts.items(), key=lambda item: (-item[1], item[0])))
    return FeedbackLedger(
        stage=FEEDBACK_LEDGER_TAGS_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FEEDBACK_LEDGER_TAGS_STATUS,
        entries=scoped_entries,
        total_entries=len(scoped_entries),
        top_tags=top_tags,
        storage_scope="local_structured_ledger",
        retrieval_available=True,
        external_write_allowed=False,
        secrets_redacted=True,
    )


def render_feedback_ledger(ledger: FeedbackLedger) -> str:
    lines = [
        "Feedback Ledger",
        "",
        f"Stage: {ledger.stage}",
        f"Status: {ledger.status}",
        f"Entries: {ledger.total_entries}",
        "Storage: local structured ledger",
        "",
        "Top tags:",
    ]
    if ledger.top_tags:
        lines.extend(f"- {tag}: {count}" for tag, count in ledger.top_tags)
    else:
        lines.append("- none yet")
    lines.extend(["", "Recent feedback:"])
    if ledger.entries:
        for entry in ledger.entries[:5]:
            lines.append(f"- {entry.feedback_id}: {entry.tag} on {entry.item_type}/{entry.item_id} ({entry.source_trace_id})")
    else:
        lines.append("- No local feedback entries injected yet.")
    lines.extend(
        [
            "",
            "Retrieval: available",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)
