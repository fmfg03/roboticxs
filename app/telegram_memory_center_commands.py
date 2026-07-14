from __future__ import annotations

from dataclasses import dataclass, field

from app.memory_center_projection import MemoryCenterItem


TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE = "136P"
APPROVED_MEMORY_STATUSES = frozenset({"approved", "active"})
PENDING_PROPOSAL_STATUS = "pending_user_review"
MAX_VISIBLE_APPROVED_MEMORIES = 5
MAX_VISIBLE_PENDING_PROPOSALS = 5
MAX_MEMORY_SUMMARY_CHARS = 180
CREDENTIAL_REDACTION_LABEL = "[redacted credential-like memory]"
SENSITIVE_REDACTION_LABEL = "[redacted sensitive memory]"


@dataclass(frozen=True, slots=True)
class TelegramMemoryCenterApprovedMemory:
    item_id: str
    memory_kind: str
    summary: str
    source: str
    status: str
    sensitivity: str
    scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TelegramMemoryCenterPendingProposal:
    proposal_id: str
    proposal_type: str
    proposed_memory_text: str
    confidence: str
    review_reason: str
    source_stage: str


@dataclass(frozen=True, slots=True)
class TelegramMemoryCenterSourceBundle:
    approved_memory_items: tuple[MemoryCenterItem, ...] = ()
    pending_memory_proposals: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class TelegramMemoryCenterSnapshot:
    owner_id: str
    robot_id: str
    stage: str
    approved_memories: tuple[TelegramMemoryCenterApprovedMemory, ...]
    pending_proposals: tuple[TelegramMemoryCenterPendingProposal, ...]
    approved_total_count: int
    pending_total_count: int
    max_visible_approved_memories: int
    max_visible_pending_proposals: int
    read_only: bool = True
    memory_write_allowed: bool = False
    memory_center_mutated: bool = False
    external_write_allowed: bool = False
    connector_read_allowed: bool = False
    model_call_allowed: bool = False
    worker_dispatch_allowed: bool = False
    limits: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.stage != TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE:
            raise ValueError("136P snapshots must identify the 136P stage.")
        if not self.read_only:
            raise ValueError("136P memory command snapshots must be read-only.")
        if any(
            (
                self.memory_write_allowed,
                self.memory_center_mutated,
                self.external_write_allowed,
                self.connector_read_allowed,
                self.model_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("136P memory command snapshots must not expand authority.")


def build_memory_center_telegram_snapshot(
    *,
    owner_id: str,
    robot_id: str,
    source_bundle: TelegramMemoryCenterSourceBundle | None = None,
) -> TelegramMemoryCenterSnapshot:
    bundle = TelegramMemoryCenterSourceBundle() if source_bundle is None else source_bundle
    approved = tuple(
        _visible_approved_memory(item)
        for item in sorted(bundle.approved_memory_items, key=lambda value: value.item_id)
        if _is_visible_approved_memory(item, owner_id=owner_id, robot_id=robot_id)
    )
    pending = tuple(
        proposal
        for proposal in (
            _visible_pending_proposal(candidate, owner_id=owner_id, robot_id=robot_id)
            for candidate in sorted(
                bundle.pending_memory_proposals,
                key=lambda value: str(getattr(value, "proposal_id", "")),
            )
        )
        if proposal is not None
    )
    return TelegramMemoryCenterSnapshot(
        owner_id=owner_id,
        robot_id=robot_id,
        stage=TELEGRAM_MEMORY_CENTER_COMMANDS_STAGE,
        approved_memories=approved[:MAX_VISIBLE_APPROVED_MEMORIES],
        pending_proposals=pending[:MAX_VISIBLE_PENDING_PROPOSALS],
        approved_total_count=len(approved),
        pending_total_count=len(pending),
        max_visible_approved_memories=MAX_VISIBLE_APPROVED_MEMORIES,
        max_visible_pending_proposals=MAX_VISIBLE_PENDING_PROPOSALS,
        limits=(
            "Only approved or active Memory Center items appear in /memory.",
            "Pending proposals appear only in /memory_pending.",
            "No Telegram memory command writes, approves, rejects, edits, or deletes memory.",
            "Sensitive memory is bounded or redacted before display.",
            "Credential-like memory is always redacted from Telegram replies.",
            "Memory projection does not authorize tools, connectors, workers, model calls, or external writes.",
        ),
    )


def render_memory_center_command_reply(snapshot: TelegramMemoryCenterSnapshot) -> str:
    lines = [
        "Memory Center",
        "",
        "Status: local read-only visibility",
        f"Stage: {snapshot.stage}",
        f"Approved visible memories: {snapshot.approved_total_count}",
        f"Pending proposals: {snapshot.pending_total_count}",
        "Memory writes: disabled",
        "LLM/model calls: disabled",
        "External writes: disabled",
        "",
        "Approved memories:",
    ]
    if not snapshot.approved_memories:
        lines.append("- No approved Memory Center items are visible in this local snapshot.")
    else:
        for memory in snapshot.approved_memories:
            lines.append(f"- {memory.memory_kind}: {memory.summary}")
    if snapshot.approved_total_count > len(snapshot.approved_memories):
        remaining = snapshot.approved_total_count - len(snapshot.approved_memories)
        lines.append(f"- Plus {remaining} more approved memory item(s) hidden by the local bound.")
    lines.extend(
        [
            "",
            "Related commands:",
            "- /memory_limits",
            "- /memory_pending",
            "",
            "No Memory Center mutation was performed.",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def render_memory_limits_command_reply(snapshot: TelegramMemoryCenterSnapshot) -> str:
    return "\n".join(
        [
            "Memory Center Limits",
            "",
            f"Stage: {snapshot.stage}",
            f"Approved display bound: {snapshot.max_visible_approved_memories}",
            f"Pending proposal display bound: {snapshot.max_visible_pending_proposals}",
            "Read-only: enabled",
            "Memory writes: disabled",
            "Approvals/rejections: disabled in 136P commands",
            "Deletes/forgetting: disabled in 136P commands",
            "Connectors: disabled",
            "LLM/model calls: disabled",
            "Workers: disabled",
            "External writes: disabled",
            "",
            "Rules:",
            *(f"- {limit}" for limit in snapshot.limits),
            "",
            "No external action was taken.",
        ]
    )


def render_memory_pending_command_reply(snapshot: TelegramMemoryCenterSnapshot) -> str:
    lines = [
        "Memory Review",
        "",
        "Status: pending owner review",
        f"Pending proposals: {snapshot.pending_total_count}",
        "Read-only: true",
        "",
        "States:",
        "- pending: waiting for owner review",
        "- approved pending writeback: approved locally, not written to Memory Center yet",
        "- rejected: rejected locally, not written",
        "- not a fact yet: pending proposals are never used as approved memory",
        "",
        "Pending review:",
    ]
    if not snapshot.pending_proposals:
        lines.append("- Empty: no pending memory proposals are visible right now.")
    else:
        for proposal in snapshot.pending_proposals:
            lines.append(
                f"- pending | {proposal.proposal_id} | {proposal.proposal_type}: {proposal.proposed_memory_text} "
                f"(confidence: {proposal.confidence})"
            )
    if snapshot.pending_total_count > len(snapshot.pending_proposals):
        remaining = snapshot.pending_total_count - len(snapshot.pending_proposals)
        lines.append(f"- Plus {remaining} more pending proposal(s) hidden by the local bound.")
    lines.extend(
        [
            "",
            "Suggested next action:",
            "- Use /memory_approve <candidate_id> to create a local approved-pending-writeback receipt.",
            "- Use /memory_reject <candidate_id> to create a local rejected receipt.",
            "",
            "Boundaries:",
            "Memory writes: disabled",
            "Memory Center mutation: disabled",
            "ProposedMemory writes: disabled",
            "Model calls: disabled",
            "Tools: disabled",
            "Worker dispatch: disabled",
            "External writes: disabled",
            "",
            "No pending proposal was approved, rejected, edited, or written.",
            "No Memory Center mutation was performed.",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def _is_visible_approved_memory(item: MemoryCenterItem, *, owner_id: str, robot_id: str) -> bool:
    return (
        item.owner_id == owner_id
        and item.robot_id == robot_id
        and item.status in APPROVED_MEMORY_STATUSES
    )


def _visible_approved_memory(item: MemoryCenterItem) -> TelegramMemoryCenterApprovedMemory:
    return TelegramMemoryCenterApprovedMemory(
        item_id=item.item_id,
        memory_kind=item.memory_kind,
        summary=_safe_memory_summary(item),
        source=item.source,
        status=item.status,
        sensitivity=item.sensitivity,
        scopes=item.scopes,
    )


def _visible_pending_proposal(
    candidate: object,
    *,
    owner_id: str,
    robot_id: str,
) -> TelegramMemoryCenterPendingProposal | None:
    if getattr(candidate, "owner_id", None) != owner_id:
        return None
    if getattr(candidate, "robot_id", None) != robot_id:
        return None
    if getattr(candidate, "status", None) != PENDING_PROPOSAL_STATUS:
        return None
    proposed_memory_text = getattr(candidate, "proposed_memory_text", None)
    if not isinstance(proposed_memory_text, str) or not proposed_memory_text.strip():
        return None
    return TelegramMemoryCenterPendingProposal(
        proposal_id=str(getattr(candidate, "proposal_id", "unknown-proposal")),
        proposal_type=str(getattr(candidate, "proposal_type", "unknown_proposal")),
        proposed_memory_text=_bounded_text(proposed_memory_text),
        confidence=str(getattr(candidate, "confidence", "unknown")),
        review_reason=str(getattr(candidate, "review_reason", "pending user review")),
        source_stage=str(getattr(candidate, "source_stage", "unknown")),
    )


def _safe_memory_summary(item: MemoryCenterItem) -> str:
    if item.sensitivity == "credential_like":
        return CREDENTIAL_REDACTION_LABEL
    if item.sensitivity in {"medical", "legal", "financial", "safety_critical"}:
        if item.bounded_summary:
            return _bounded_text(item.bounded_summary)
        return SENSITIVE_REDACTION_LABEL
    return _bounded_text(item.bounded_summary or item.content)


def _bounded_text(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= MAX_MEMORY_SUMMARY_CHARS:
        return stripped
    return stripped[: MAX_MEMORY_SUMMARY_CHARS - 3].rstrip() + "..."
