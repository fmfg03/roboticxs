from __future__ import annotations

from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.memory_center_projection import MemoryCenterItem
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


MEMORY_SOURCE_FORGET_RECEIPTS_STAGE = "187P"
MAX_MEMORY_RECEIPT_SUMMARY_CHARS = 180
MAX_MEMORY_EDIT_TEXT_CHARS = 500
CREDENTIAL_REDACTION_LABEL = "[redacted credential-like memory]"
SENSITIVE_REDACTION_LABEL = "[redacted sensitive memory]"
EDIT_REDACTION_LABEL = "[redacted credential-like edit]"
SECRET_MARKERS = (
    "authorization",
    "bearer",
    "refresh_token",
    "client_secret",
    "api key",
    "secret",
    "token",
)


@dataclass(frozen=True, slots=True)
class MemorySourceReceipt:
    receipt_id: str
    stage: str
    owner_id: str
    robot_id: str
    memory_id: str
    memory_kind: str
    summary: str
    source: str
    source_stage: str
    approved_at: str
    visibility: str
    status: str
    scopes: tuple[str, ...]
    allowed_uses: tuple[str, ...]
    sensitivity: str
    read_only: bool
    memory_center_mutated: bool
    source_evidence_deleted: bool
    connector_read_allowed: bool
    model_call_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != MEMORY_SOURCE_FORGET_RECEIPTS_STAGE:
            raise ValueError("187P memory source receipts must identify the 187P stage.")
        if not self.owner_id or not self.robot_id or not self.memory_id:
            raise ValueError("187P memory source receipts require owner, robot, and memory ids.")
        if not self.read_only:
            raise ValueError("187P memory source receipts must remain read-only.")
        if any(
            (
                self.memory_center_mutated,
                self.source_evidence_deleted,
                self.connector_read_allowed,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("187P memory source receipts must not expand authority.")


@dataclass(frozen=True, slots=True)
class MemoryForgetReceipt:
    receipt_id: str
    stage: str
    owner_id: str
    robot_id: str
    memory_id: str | None
    status: str
    matched_memory: bool
    local_forget_receipt_created: bool
    memory_center_mutated: bool
    memory_store_mutated: bool
    source_evidence_deleted: bool
    connector_read_allowed: bool
    model_call_allowed: bool
    external_write_allowed: bool
    message: str

    def __post_init__(self) -> None:
        if self.stage != MEMORY_SOURCE_FORGET_RECEIPTS_STAGE:
            raise ValueError("187P memory forget receipts must identify the 187P stage.")
        if not self.owner_id or not self.robot_id:
            raise ValueError("187P memory forget receipts require owner and robot ids.")
        if any(
            (
                self.memory_center_mutated,
                self.memory_store_mutated,
                self.source_evidence_deleted,
                self.connector_read_allowed,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("187P memory forget receipts must not expand authority.")


@dataclass(frozen=True, slots=True)
class MemoryEditReceipt:
    receipt_id: str
    stage: str
    owner_id: str
    robot_id: str
    memory_id: str | None
    proposed_text: str
    status: str
    matched_memory: bool
    local_edit_receipt_created: bool
    memory_center_mutated: bool
    memory_store_mutated: bool
    source_evidence_deleted: bool
    connector_read_allowed: bool
    model_call_allowed: bool
    external_write_allowed: bool
    message: str

    def __post_init__(self) -> None:
        if self.stage != MEMORY_SOURCE_FORGET_RECEIPTS_STAGE:
            raise ValueError("187P memory edit receipts must identify the 187P stage.")
        if not self.owner_id or not self.robot_id:
            raise ValueError("187P memory edit receipts require owner and robot ids.")
        if any(
            (
                self.memory_center_mutated,
                self.memory_store_mutated,
                self.source_evidence_deleted,
                self.connector_read_allowed,
                self.model_call_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("187P memory edit receipts must not expand authority.")


def build_memory_source_receipts(
    *,
    owner_id: str,
    robot_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> tuple[MemorySourceReceipt, ...]:
    bundle = TelegramMemoryCenterSourceBundle() if source_bundle is None else source_bundle
    return tuple(
        _source_receipt(owner_id=owner_id, robot_id=robot_id, item=item)
        for item in sorted(bundle.approved_memory_items, key=lambda value: value.item_id)
        if _matches_owner_robot(item, owner_id=owner_id, robot_id=robot_id)
    )


def build_memory_forget_receipt(
    *,
    owner_id: str,
    robot_id: str,
    memory_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> MemoryForgetReceipt:
    normalized_id = memory_id.strip()
    matched = _find_visible_memory(owner_id=owner_id, robot_id=robot_id, memory_id=normalized_id, source_bundle=source_bundle)
    if not normalized_id:
        status = "blocked_missing_memory_id"
        created = False
        message = "No local forget receipt was created because no memory id was provided."
    elif matched is None:
        status = "blocked_memory_not_found"
        created = False
        message = "No local forget receipt was created because the memory id is not visible for this owner and robot."
    else:
        status = "local_forget_receipt_created"
        created = True
        message = "Local forget receipt created. Source evidence was not deleted and Memory Center was not mutated."
    return MemoryForgetReceipt(
        receipt_id=_stable_id("memory_forget_receipt", owner_id, robot_id, normalized_id or "none", status),
        stage=MEMORY_SOURCE_FORGET_RECEIPTS_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=normalized_id or None,
        status=status,
        matched_memory=matched is not None,
        local_forget_receipt_created=created,
        memory_center_mutated=False,
        memory_store_mutated=False,
        source_evidence_deleted=False,
        connector_read_allowed=False,
        model_call_allowed=False,
        external_write_allowed=False,
        message=message,
    )


def build_memory_edit_receipt(
    *,
    owner_id: str,
    robot_id: str,
    memory_id: str,
    proposed_text: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> MemoryEditReceipt:
    normalized_id = memory_id.strip()
    bounded_text = _safe_edit_text(proposed_text)
    matched = _find_visible_memory(owner_id=owner_id, robot_id=robot_id, memory_id=normalized_id, source_bundle=source_bundle)
    if not normalized_id:
        status = "blocked_missing_memory_id"
        created = False
        message = "No local edit receipt was created because no memory id was provided."
    elif matched is None:
        status = "blocked_memory_not_found"
        created = False
        message = "No local edit receipt was created because the memory id is not visible for this owner and robot."
    elif not bounded_text:
        status = "blocked_missing_edit_text"
        created = False
        message = "No local edit receipt was created because no replacement memory text was provided."
    else:
        status = "local_edit_receipt_created"
        created = True
        message = "Local edit receipt created. Memory Store and Memory Center were not mutated."
    return MemoryEditReceipt(
        receipt_id=_stable_id("memory_edit_receipt", owner_id, robot_id, normalized_id or "none", status, bounded_text),
        stage=MEMORY_SOURCE_FORGET_RECEIPTS_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=normalized_id or None,
        proposed_text=bounded_text,
        status=status,
        matched_memory=matched is not None,
        local_edit_receipt_created=created,
        memory_center_mutated=False,
        memory_store_mutated=False,
        source_evidence_deleted=False,
        connector_read_allowed=False,
        model_call_allowed=False,
        external_write_allowed=False,
        message=message,
    )


def memory_id_matches_visible_approved_memory(
    *,
    owner_id: str,
    robot_id: str,
    memory_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> bool:
    return _find_visible_memory(
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=memory_id.strip(),
        source_bundle=source_bundle,
    ) is not None


def render_memory_source_receipts(receipts: tuple[MemorySourceReceipt, ...]) -> str:
    lines = [
        "Memory Source Receipts",
        "",
        f"Stage: {MEMORY_SOURCE_FORGET_RECEIPTS_STAGE}",
        "Status: local read-only provenance",
        "Memory Center mutation: disabled",
        "Source evidence deletion: disabled",
        "Connectors/model calls/external writes: disabled",
        "",
        "Visible approved memory receipts:",
    ]
    if not receipts:
        lines.append("- Empty: no approved memory source receipts are visible for this owner and robot.")
    else:
        for receipt in receipts:
            lines.extend(
                [
                    f"- {receipt.memory_id} | {receipt.memory_kind}: {receipt.summary}",
                    f"  Source: {receipt.source}",
                    f"  Source stage: {receipt.source_stage}",
                    f"  Approved at: {receipt.approved_at}",
                    f"  Visibility: {receipt.visibility}",
                    f"  Status: {receipt.status}",
                    f"  Scopes: {_join_tuple(receipt.scopes)}",
                    f"  Allowed uses: {_join_tuple(receipt.allowed_uses)}",
                ]
            )
    lines.extend(
        [
            "",
            "No Memory Center mutation was performed.",
            "No source evidence was deleted.",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def render_memory_forget_receipt(receipt: MemoryForgetReceipt) -> str:
    return "\n".join(
        [
            "Memory Forget Receipt",
            "",
            f"Stage: {receipt.stage}",
            f"Status: {receipt.status}",
            f"Memory id: {receipt.memory_id or 'none'}",
            f"Matched visible memory: {_bool(receipt.matched_memory)}",
            f"Local forget receipt created: {_bool(receipt.local_forget_receipt_created)}",
            "Memory Store mutation: disabled",
            "Memory Center mutation: disabled",
            "Source evidence deletion: disabled",
            "Connectors/model calls/external writes: disabled",
            "",
            receipt.message,
            "No external action was taken.",
        ]
    )


def render_memory_edit_receipt(receipt: MemoryEditReceipt) -> str:
    lines = [
        "Memory Edit Receipt",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Memory id: {receipt.memory_id or 'none'}",
        f"Matched visible memory: {_bool(receipt.matched_memory)}",
        f"Local edit receipt created: {_bool(receipt.local_edit_receipt_created)}",
    ]
    if receipt.proposed_text:
        lines.append(f"Proposed replacement: {receipt.proposed_text}")
    lines.extend(
        [
            "Memory Store mutation: disabled",
            "Memory Center mutation: disabled",
            "Source evidence deletion: disabled",
            "Connectors/model calls/external writes: disabled",
            "",
            receipt.message,
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _source_receipt(*, owner_id: str, robot_id: str, item: MemoryCenterItem) -> MemorySourceReceipt:
    return MemorySourceReceipt(
        receipt_id=_stable_id("memory_source_receipt", owner_id, robot_id, item.item_id),
        stage=MEMORY_SOURCE_FORGET_RECEIPTS_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=item.item_id,
        memory_kind=item.memory_kind,
        summary=_safe_memory_summary(item),
        source=item.source,
        source_stage=str(getattr(item, "source_stage", "unknown")),
        approved_at=str(getattr(item, "approved_at", "unknown")),
        visibility=item.actor_visibility,
        status=item.status,
        scopes=item.scopes,
        allowed_uses=item.allowed_uses,
        sensitivity=item.sensitivity,
        read_only=True,
        memory_center_mutated=False,
        source_evidence_deleted=False,
        connector_read_allowed=False,
        model_call_allowed=False,
        external_write_allowed=False,
    )


def _find_visible_memory(
    *,
    owner_id: str,
    robot_id: str,
    memory_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None,
) -> MemoryCenterItem | None:
    if not memory_id:
        return None
    bundle = TelegramMemoryCenterSourceBundle() if source_bundle is None else source_bundle
    for item in bundle.approved_memory_items:
        if item.item_id == memory_id and _matches_owner_robot(item, owner_id=owner_id, robot_id=robot_id):
            return item
    return None


def _matches_owner_robot(item: MemoryCenterItem, *, owner_id: str, robot_id: str) -> bool:
    return item.owner_id == owner_id and item.robot_id == robot_id and item.status in {"approved", "active"}


def _safe_memory_summary(item: MemoryCenterItem) -> str:
    if item.sensitivity == "credential_like":
        return CREDENTIAL_REDACTION_LABEL
    if item.sensitivity in {"medical", "legal", "financial", "safety_critical"}:
        if item.bounded_summary:
            return _bounded_text(item.bounded_summary, MAX_MEMORY_RECEIPT_SUMMARY_CHARS)
        return SENSITIVE_REDACTION_LABEL
    return _bounded_text(item.bounded_summary or item.content, MAX_MEMORY_RECEIPT_SUMMARY_CHARS)


def _safe_edit_text(value: str) -> str:
    bounded = _bounded_text(value, MAX_MEMORY_EDIT_TEXT_CHARS)
    lowered = bounded.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        return EDIT_REDACTION_LABEL
    return bounded


def _bounded_text(value: str, max_chars: int) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= max_chars:
        return stripped
    return stripped[: max_chars - 3].rstrip() + "..."


def _join_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "none"


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:memory-source-forget-receipts:" + ":".join(parts)))
