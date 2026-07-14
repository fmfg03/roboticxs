from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from uuid import NAMESPACE_URL, uuid5

from app.context_scan_proposed_memory import (
    CONTEXT_SCAN_PROPOSED_MEMORY_STAGE,
    CONTEXT_SCAN_PROPOSED_MEMORY_STATUS,
    ContextScanProposedMemoryCandidate,
)
from app.memory_center_projection import MemoryCenterItem
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


MEMORY_STORE_STAGE = "165P"
MEMORY_STORE_ACTIVE_STATUS = "active"
MEMORY_STORE_FORGOTTEN_STATUS = "forgotten"
MEMORY_STORE_VISIBILITY = "owner_private"
MAX_MEMORY_CONTENT_CHARS = 500


@dataclass(frozen=True, slots=True)
class MemoryStoreItem:
    memory_id: str
    robot_id: str
    user_id: str
    memory_type: str
    content: str
    source: str
    confidence: str
    approved_at: str
    status: str
    visibility: str
    pinned: bool
    source_stage: str
    source_id: str

    def __post_init__(self) -> None:
        if not self.memory_id or not self.robot_id or not self.user_id:
            raise ValueError("165P memory store items require memory, robot, and user ids.")
        if not self.memory_type or not self.content.strip():
            raise ValueError("165P memory store items require type and content.")
        if self.visibility != MEMORY_STORE_VISIBILITY:
            raise ValueError("165P memory store items must remain owner-private.")
        if self.status not in {MEMORY_STORE_ACTIVE_STATUS, MEMORY_STORE_FORGOTTEN_STATUS}:
            raise ValueError("165P memory store items require active or forgotten status.")


@dataclass(frozen=True, slots=True)
class MemoryStoreReceipt:
    receipt_id: str
    stage: str
    action: str
    memory_id: str | None
    status: str
    source_stage: str | None
    owner_requested: bool
    local_memory_store_mutated: bool
    memory_center_mutated: bool
    proposed_memory_written: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool
    external_write_allowed: bool
    message: str

    def __post_init__(self) -> None:
        if self.stage != MEMORY_STORE_STAGE:
            raise ValueError("165P memory store receipts must identify the 165P stage.")
        if not self.owner_requested:
            raise ValueError("165P memory store receipts require owner request.")
        if any(
            (
                self.memory_center_mutated,
                self.proposed_memory_written,
                self.calendar_write_allowed,
                self.gmail_write_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("165P memory store receipts must not expand external authority.")


@dataclass(slots=True)
class MemoryStoreRegistry:
    items_by_id: dict[str, MemoryStoreItem] = field(default_factory=dict)
    receipts_by_id: dict[str, MemoryStoreReceipt] = field(default_factory=dict)

    def store_item(self, item: MemoryStoreItem) -> MemoryStoreItem:
        self.items_by_id[item.memory_id] = item
        return item

    def store_receipt(self, receipt: MemoryStoreReceipt) -> MemoryStoreReceipt:
        self.receipts_by_id[receipt.receipt_id] = receipt
        return receipt

    def get_item(self, memory_id: str) -> MemoryStoreItem | None:
        return self.items_by_id.get(memory_id)

    def list_active_items(self, *, user_id: str, robot_id: str) -> tuple[MemoryStoreItem, ...]:
        return tuple(
            item
            for item in sorted(self.items_by_id.values(), key=lambda value: (not value.pinned, value.approved_at, value.memory_id))
            if item.user_id == user_id and item.robot_id == robot_id and item.status == MEMORY_STORE_ACTIVE_STATUS
        )


def approve_context_candidate_to_memory_store(
    *,
    candidate: ContextScanProposedMemoryCandidate,
    registry: MemoryStoreRegistry,
    approved_at: str,
) -> MemoryStoreReceipt:
    if candidate.stage != CONTEXT_SCAN_PROPOSED_MEMORY_STAGE:
        raise ValueError("rejected_context_memory_candidate_stage")
    if candidate.status != CONTEXT_SCAN_PROPOSED_MEMORY_STATUS:
        raise ValueError("rejected_context_memory_candidate_status")
    if candidate.treated_as_fact:
        raise ValueError("rejected_context_memory_candidate_already_fact")
    memory_id = _memory_id(candidate.owner_id, candidate.robot_id, candidate.candidate_id, candidate.proposed_memory_text)
    existing = registry.get_item(memory_id)
    if existing is None:
        registry.store_item(
            MemoryStoreItem(
                memory_id=memory_id,
                robot_id=candidate.robot_id,
                user_id=candidate.owner_id,
                memory_type=_memory_type_from_candidate(candidate),
                content=_bounded_text(candidate.proposed_memory_text),
                source="context_scan_owner_approved",
                confidence=candidate.confidence,
                approved_at=approved_at,
                status=MEMORY_STORE_ACTIVE_STATUS,
                visibility=MEMORY_STORE_VISIBILITY,
                pinned=False,
                source_stage=candidate.source_stage,
                source_id=candidate.candidate_id,
            )
        )
    return _receipt(
        action="approve_context_candidate",
        memory_id=memory_id,
        status="stored" if existing is None else "duplicate_existing",
        source_stage=candidate.source_stage,
        local_memory_store_mutated=existing is None,
        message="Approved context candidate is now active in the local memory store.",
    )


def add_memory_to_store(
    *,
    registry: MemoryStoreRegistry,
    user_id: str,
    robot_id: str,
    content: str,
    memory_type: str = "owner_note",
    approved_at: str,
    source: str = "telegram_memory_add",
    confidence: str = "owner_asserted",
) -> MemoryStoreReceipt:
    bounded_content = _bounded_text(content)
    if not bounded_content:
        raise ValueError("rejected_empty_memory_content")
    memory_id = _memory_id(user_id, robot_id, source, memory_type, bounded_content)
    existing = registry.get_item(memory_id)
    if existing is None:
        registry.store_item(
            MemoryStoreItem(
                memory_id=memory_id,
                robot_id=robot_id,
                user_id=user_id,
                memory_type=memory_type,
                content=bounded_content,
                source=source,
                confidence=confidence,
                approved_at=approved_at,
                status=MEMORY_STORE_ACTIVE_STATUS,
                visibility=MEMORY_STORE_VISIBILITY,
                pinned=False,
                source_stage=MEMORY_STORE_STAGE,
                source_id=memory_id,
            )
        )
    return _receipt(
        action="memory_add",
        memory_id=memory_id,
        status="stored" if existing is None else "duplicate_existing",
        source_stage=MEMORY_STORE_STAGE,
        local_memory_store_mutated=existing is None,
        message="Owner-provided memory is active in the local memory store.",
    )


def edit_memory_in_store(
    *,
    registry: MemoryStoreRegistry,
    memory_id: str,
    content: str,
) -> MemoryStoreReceipt:
    existing = registry.get_item(memory_id)
    if existing is None or existing.status != MEMORY_STORE_ACTIVE_STATUS:
        return _receipt(
            action="memory_edit",
            memory_id=memory_id,
            status="not_found",
            source_stage=MEMORY_STORE_STAGE,
            local_memory_store_mutated=False,
            message="No active memory was edited.",
        )
    bounded_content = _bounded_text(content)
    if not bounded_content:
        raise ValueError("rejected_empty_memory_content")
    registry.store_item(MemoryStoreItem(**{**asdict(existing), "content": bounded_content, "source": "telegram_memory_edit"}))
    return _receipt(
        action="memory_edit",
        memory_id=memory_id,
        status="edited",
        source_stage=MEMORY_STORE_STAGE,
        local_memory_store_mutated=True,
        message="Active memory was edited locally.",
    )


def forget_memory_in_store(*, registry: MemoryStoreRegistry, memory_id: str) -> MemoryStoreReceipt:
    existing = registry.get_item(memory_id)
    if existing is None or existing.status != MEMORY_STORE_ACTIVE_STATUS:
        return _receipt(
            action="memory_forget",
            memory_id=memory_id,
            status="not_found",
            source_stage=MEMORY_STORE_STAGE,
            local_memory_store_mutated=False,
            message="No active memory was forgotten.",
        )
    registry.store_item(MemoryStoreItem(**{**asdict(existing), "status": MEMORY_STORE_FORGOTTEN_STATUS, "pinned": False}))
    return _receipt(
        action="memory_forget",
        memory_id=memory_id,
        status="forgotten",
        source_stage=MEMORY_STORE_STAGE,
        local_memory_store_mutated=True,
        message="Active memory was forgotten locally.",
    )


def pin_memory_in_store(*, registry: MemoryStoreRegistry, memory_id: str) -> MemoryStoreReceipt:
    existing = registry.get_item(memory_id)
    if existing is None or existing.status != MEMORY_STORE_ACTIVE_STATUS:
        return _receipt(
            action="memory_pin",
            memory_id=memory_id,
            status="not_found",
            source_stage=MEMORY_STORE_STAGE,
            local_memory_store_mutated=False,
            message="No active memory was pinned.",
        )
    registry.store_item(MemoryStoreItem(**{**asdict(existing), "pinned": True}))
    return _receipt(
        action="memory_pin",
        memory_id=memory_id,
        status="pinned",
        source_stage=MEMORY_STORE_STAGE,
        local_memory_store_mutated=True,
        message="Active memory was pinned locally.",
    )


def build_memory_center_source_bundle_from_store(
    *,
    registry: MemoryStoreRegistry,
    user_id: str,
    robot_id: str,
) -> TelegramMemoryCenterSourceBundle:
    return TelegramMemoryCenterSourceBundle(
        approved_memory_items=tuple(_to_memory_center_item(item) for item in registry.list_active_items(user_id=user_id, robot_id=robot_id)),
        pending_memory_proposals=(),
    )


def render_memory_store_receipt(receipt: MemoryStoreReceipt) -> str:
    return "\n".join(
        [
            "Memory Store",
            "",
            f"Stage: {receipt.stage}",
            f"Action: {receipt.action}",
            f"Status: {receipt.status}",
            f"Memory id: {receipt.memory_id or 'none'}",
            "Local memory store mutation: true" if receipt.local_memory_store_mutated else "Local memory store mutation: false",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Calendar writes: disabled",
            "Gmail writes: disabled",
            "Model calls: disabled",
            "Tools/workers: disabled",
            "External writes: disabled",
            "",
            receipt.message,
        ]
    )


def _to_memory_center_item(item: MemoryStoreItem) -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id=item.memory_id,
        owner_id=item.user_id,
        robot_id=item.robot_id,
        memory_kind=item.memory_type,
        status=item.status,
        scopes=("general", "telegram", "hermes_os"),
        sensitivity="ordinary",
        allowed_uses=("answer_personalization", "telegram_context", "hermes_os_context"),
        skill_ids=(),
        content=item.content,
        bounded_summary=item.content,
        source=item.source,
        actor_visibility=item.visibility,
        is_boundary=item.memory_type == "boundary_memory",
        is_preference=item.memory_type in {"owner_preference", "work_preference"},
    )


def _receipt(
    *,
    action: str,
    memory_id: str | None,
    status: str,
    source_stage: str | None,
    local_memory_store_mutated: bool,
    message: str,
) -> MemoryStoreReceipt:
    receipt_id = _stable_id("memory_store_receipt", action, memory_id or "none", status, message)
    return MemoryStoreReceipt(
        receipt_id=receipt_id,
        stage=MEMORY_STORE_STAGE,
        action=action,
        memory_id=memory_id,
        status=status,
        source_stage=source_stage,
        owner_requested=True,
        local_memory_store_mutated=local_memory_store_mutated,
        memory_center_mutated=False,
        proposed_memory_written=False,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
        external_write_allowed=False,
        message=message,
    )


def _memory_type_from_candidate(candidate: ContextScanProposedMemoryCandidate) -> str:
    if "followup" in candidate.proposal_type:
        return "followup_memory"
    if "attachment" in candidate.proposal_type:
        return "document_context_memory"
    if "relationship" in candidate.proposal_type:
        return "relationship_context_memory"
    if "business" in candidate.proposal_type:
        return "business_context_memory"
    return "context_memory"


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_MEMORY_CONTENT_CHARS:
        return stripped
    return stripped[: MAX_MEMORY_CONTENT_CHARS - 3].rstrip() + "..."


def _memory_id(*parts: str) -> str:
    return _stable_id("memory_store_item", *parts)


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "roboticxs:memory-store:" + ":".join(parts)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.memory_store")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    registry = MemoryStoreRegistry()
    receipt = add_memory_to_store(
        registry=registry,
        user_id="local-owner",
        robot_id="roboticxs-dev",
        content="Demo memory store item.",
        approved_at="2026-06-25T00:00:00Z",
    )
    if args.as_json:
        print(json.dumps({"receipt": asdict(receipt), "items": [asdict(item) for item in registry.items_by_id.values()]}, sort_keys=True, indent=2))
    else:
        print(render_memory_store_receipt(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
