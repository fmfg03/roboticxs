from __future__ import annotations

from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from app.memory_source_forget_receipts import memory_id_matches_visible_approved_memory
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle


MEMORY_CORRECTION_LOOP_STAGE = "209P"
MEMORY_CORRECTION_STATUS_CREATED = "local_memory_correction_receipt_created"
MEMORY_CORRECTION_STATUS_MISSING_MEMORY_ID = "blocked_missing_memory_id"
MEMORY_CORRECTION_STATUS_MEMORY_NOT_FOUND = "blocked_memory_not_found"
MEMORY_CORRECTION_STATUS_MISSING_MERGE_TARGET = "blocked_missing_merge_target"
SUPPORTED_MEMORY_CORRECTIONS = ("wrong", "stale", "duplicate", "merge", "never_use")
MEMORY_CORRECTION_COMMANDS = {
    "/memory_wrong": "wrong",
    "/memory_stale": "stale",
    "/memory_duplicate": "duplicate",
    "/memory_merge": "merge",
    "/memory_never_use": "never_use",
}


@dataclass(frozen=True, slots=True)
class MemoryCorrectionReceipt:
    receipt_id: str
    stage: str
    owner_id: str
    robot_id: str
    correction_type: str
    memory_id: str | None
    merge_target_memory_id: str | None
    status: str
    matched_memory: bool
    matched_merge_target: bool
    local_receipt_created: bool
    memory_center_mutated: bool
    memory_store_mutated: bool
    source_evidence_deleted: bool
    connector_read_allowed: bool
    model_call_allowed: bool
    external_write_allowed: bool
    approval_gate_preserved: bool
    message: str

    def __post_init__(self) -> None:
        if self.stage != MEMORY_CORRECTION_LOOP_STAGE:
            raise ValueError("209P memory correction receipts must identify the 209P stage.")
        if self.correction_type not in SUPPORTED_MEMORY_CORRECTIONS:
            raise ValueError("209P memory correction type is unsupported.")
        if self.status not in {
            MEMORY_CORRECTION_STATUS_CREATED,
            MEMORY_CORRECTION_STATUS_MISSING_MEMORY_ID,
            MEMORY_CORRECTION_STATUS_MEMORY_NOT_FOUND,
            MEMORY_CORRECTION_STATUS_MISSING_MERGE_TARGET,
        }:
            raise ValueError("209P memory correction status is unsupported.")
        if not self.owner_id or not self.robot_id:
            raise ValueError("209P memory correction receipts require owner and robot ids.")
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
            raise ValueError("209P memory corrections must not expand authority.")
        if not self.approval_gate_preserved:
            raise ValueError("209P memory corrections must preserve approval semantics.")


def correction_type_from_command(command: str) -> str:
    return MEMORY_CORRECTION_COMMANDS[command]


def parse_memory_correction_argument(correction_type: str, argument: str | None) -> tuple[str, str]:
    parts = (argument or "").strip().split(maxsplit=1)
    if correction_type == "merge":
        if len(parts) != 2:
            return (parts[0].strip() if parts else ""), ""
        return parts[0].strip(), parts[1].strip()
    return (parts[0].strip() if parts else ""), ""


def build_memory_correction_receipt(
    *,
    owner_id: str,
    robot_id: str,
    correction_type: str,
    memory_id: str,
    merge_target_memory_id: str = "",
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> MemoryCorrectionReceipt:
    normalized_memory_id = memory_id.strip()
    normalized_merge_target = merge_target_memory_id.strip()
    matched_memory = _matches_visible_memory(
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=normalized_memory_id,
        source_bundle=source_bundle,
    )
    matched_merge_target = (
        _matches_visible_memory(
            owner_id=owner_id,
            robot_id=robot_id,
            memory_id=normalized_merge_target,
            source_bundle=source_bundle,
        )
        if correction_type == "merge" and normalized_merge_target
        else False
    )
    if not normalized_memory_id:
        status = MEMORY_CORRECTION_STATUS_MISSING_MEMORY_ID
        created = False
        message = "No local memory correction receipt was created because no memory id was provided."
    elif not matched_memory:
        status = MEMORY_CORRECTION_STATUS_MEMORY_NOT_FOUND
        created = False
        message = "No local memory correction receipt was created because the memory id is not visible for this owner and robot."
    elif correction_type == "merge" and not normalized_merge_target:
        status = MEMORY_CORRECTION_STATUS_MISSING_MERGE_TARGET
        created = False
        message = "No local memory correction receipt was created because /memory_merge requires two memory ids."
    elif correction_type == "merge" and not matched_merge_target:
        status = MEMORY_CORRECTION_STATUS_MEMORY_NOT_FOUND
        created = False
        message = "No local memory correction receipt was created because the merge target is not visible for this owner and robot."
    else:
        status = MEMORY_CORRECTION_STATUS_CREATED
        created = True
        message = "Local memory correction receipt created. Memory Store and Memory Center were not mutated."
    return MemoryCorrectionReceipt(
        receipt_id=_stable_id(
            "memory_correction_receipt",
            owner_id,
            robot_id,
            correction_type,
            normalized_memory_id or "none",
            normalized_merge_target or "none",
            status,
        ),
        stage=MEMORY_CORRECTION_LOOP_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        correction_type=correction_type,
        memory_id=normalized_memory_id or None,
        merge_target_memory_id=normalized_merge_target or None,
        status=status,
        matched_memory=matched_memory,
        matched_merge_target=matched_merge_target,
        local_receipt_created=created,
        memory_center_mutated=False,
        memory_store_mutated=False,
        source_evidence_deleted=False,
        connector_read_allowed=False,
        model_call_allowed=False,
        external_write_allowed=False,
        approval_gate_preserved=True,
        message=message,
    )


def render_memory_correction_receipt(receipt: MemoryCorrectionReceipt) -> str:
    lines = [
        "Memory Correction Receipt",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Correction: {receipt.correction_type}",
        f"Memory id: {receipt.memory_id or 'none'}",
        f"Matched visible memory: {_bool(receipt.matched_memory)}",
    ]
    if receipt.correction_type == "merge":
        lines.extend(
            [
                f"Merge target: {receipt.merge_target_memory_id or 'none'}",
                f"Matched merge target: {_bool(receipt.matched_merge_target)}",
            ]
        )
    lines.extend(
        [
            f"Local receipt created: {_bool(receipt.local_receipt_created)}",
            "Memory Store mutation: disabled",
            "Memory Center mutation: disabled",
            "Source evidence deletion: disabled",
            "Connectors/model calls/external writes: disabled",
            "Approval gate: preserved",
            "",
            receipt.message,
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def render_memory_correction_usage() -> str:
    return "\n".join(
        [
            "Memory Correction Loop",
            "",
            "Usage:",
            "- /memory_wrong <memory_id>",
            "- /memory_stale <memory_id>",
            "- /memory_duplicate <memory_id>",
            "- /memory_merge <memory_id> <target_memory_id>",
            "- /memory_never_use <memory_id>",
        ]
    )


def _matches_visible_memory(
    *,
    owner_id: str,
    robot_id: str,
    memory_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None,
) -> bool:
    return memory_id_matches_visible_approved_memory(
        owner_id=owner_id,
        robot_id=robot_id,
        memory_id=memory_id,
        source_bundle=source_bundle,
    )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, ":".join(parts)))


def _bool(value: bool) -> str:
    return "true" if value else "false"
