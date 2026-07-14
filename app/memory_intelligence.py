from __future__ import annotations

from dataclasses import dataclass

from app.telegram_memory_center_commands import TelegramMemoryCenterSnapshot


MEMORY_INTELLIGENCE_STAGE = "196P"


@dataclass(frozen=True, slots=True)
class MemoryIntelligenceFinding:
    finding_type: str
    memory_ids: tuple[str, ...]
    summary: str
    suggested_action: str
    influence: str

    def __post_init__(self) -> None:
        if self.finding_type not in {"duplicate", "stale", "conflict", "high_impact", "used_memory"}:
            raise ValueError("196P memory intelligence finding type must be supported.")
        if not self.memory_ids or not self.summary or not self.suggested_action:
            raise ValueError("196P memory intelligence findings require ids, summary, and action.")


@dataclass(frozen=True, slots=True)
class MemoryIntelligenceReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    findings: tuple[MemoryIntelligenceFinding, ...]
    read_only: bool
    memory_center_mutated: bool
    memory_store_mutated: bool
    model_call_allowed: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != MEMORY_INTELLIGENCE_STAGE:
            raise ValueError("196P memory intelligence reports must identify the 196P stage.")
        if not self.read_only:
            raise ValueError("196P memory intelligence must remain read-only.")
        if any((self.memory_center_mutated, self.memory_store_mutated, self.model_call_allowed, self.external_write_allowed)):
            raise ValueError("196P memory intelligence must not expand authority.")


def build_memory_intelligence_report(snapshot: TelegramMemoryCenterSnapshot) -> MemoryIntelligenceReport:
    findings = [
        *_duplicate_findings(snapshot),
        *_stale_findings(snapshot),
        *_conflict_findings(snapshot),
        *_high_impact_findings(snapshot),
        *_used_memory_findings(snapshot),
    ]
    return MemoryIntelligenceReport(
        stage=MEMORY_INTELLIGENCE_STAGE,
        owner_id=snapshot.owner_id,
        robot_id=snapshot.robot_id,
        status="findings_available" if findings else "no_memory_intelligence_findings",
        findings=tuple(findings),
        read_only=True,
        memory_center_mutated=False,
        memory_store_mutated=False,
        model_call_allowed=False,
        external_write_allowed=False,
    )


def render_memory_intelligence_report(report: MemoryIntelligenceReport) -> str:
    lines = [
        "Memory Intelligence",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        "Read-only: true",
        "",
        "Findings:",
    ]
    if not report.findings:
        lines.append("- No duplicate, stale, conflicting, or high-impact memory signals found.")
    else:
        for finding in report.findings:
            lines.append(f"- {finding.finding_type}: {finding.summary}")
            lines.append(f"  memories: {', '.join(finding.memory_ids)}")
            lines.append(f"  suggested action: {finding.suggested_action}")
            lines.append(f"  influence: {finding.influence}")
    lines.extend(
        [
            "",
            "Boundaries:",
            "Memory Center mutation: disabled",
            "Memory Store mutation: disabled",
            "Model calls: disabled",
            "External writes: disabled",
            "",
            "No memory was merged, edited, forgotten, or written.",
        ]
    )
    return "\n".join(lines)


def _duplicate_findings(snapshot: TelegramMemoryCenterSnapshot) -> tuple[MemoryIntelligenceFinding, ...]:
    groups: dict[str, list[str]] = {}
    for memory in snapshot.approved_memories:
        groups.setdefault(_norm(memory.summary), []).append(memory.item_id)
    return tuple(
        MemoryIntelligenceFinding(
            finding_type="duplicate",
            memory_ids=tuple(ids),
            summary="Approved memories have matching summaries.",
            suggested_action="Review /memory_edit or future merge flow; no merge is automatic.",
            influence="duplicate memories may over-weight the same preference",
        )
        for ids in groups.values()
        if len(ids) > 1
    )


def _stale_findings(snapshot: TelegramMemoryCenterSnapshot) -> tuple[MemoryIntelligenceFinding, ...]:
    return tuple(
        MemoryIntelligenceFinding(
            finding_type="stale",
            memory_ids=(memory.item_id,),
            summary=f"{memory.memory_kind} may be stale: {memory.summary}",
            suggested_action="Review /memory_forget or /memory_edit if the memory is no longer true.",
            influence="stale memory may mislead prep, drafts, or priorities",
        )
        for memory in snapshot.approved_memories
        if any(marker in memory.summary.lower() for marker in ("old", "stale", "deprecated", "no longer"))
    )


def _conflict_findings(snapshot: TelegramMemoryCenterSnapshot) -> tuple[MemoryIntelligenceFinding, ...]:
    by_kind: dict[str, list[object]] = {}
    for memory in snapshot.approved_memories:
        by_kind.setdefault(memory.memory_kind, []).append(memory)
    findings = []
    for memories in by_kind.values():
        summaries = {_norm(memory.summary) for memory in memories}
        if len(memories) > 1 and len(summaries) > 1:
            findings.append(
                MemoryIntelligenceFinding(
                    finding_type="conflict",
                    memory_ids=tuple(memory.item_id for memory in memories),
                    summary="Multiple approved memories of the same kind may conflict.",
                    suggested_action="Review and edit the incorrect memory; no conflict resolution is automatic.",
                    influence="conflicting memories may reduce answer quality",
                )
            )
    return tuple(findings)


def _high_impact_findings(snapshot: TelegramMemoryCenterSnapshot) -> tuple[MemoryIntelligenceFinding, ...]:
    return tuple(
        MemoryIntelligenceFinding(
            finding_type="high_impact",
            memory_ids=(memory.item_id,),
            summary=f"{memory.memory_kind} can strongly influence outputs.",
            suggested_action="Keep only if still accurate and owner-approved.",
            influence=f"used in scopes: {', '.join(memory.scopes) if memory.scopes else 'general'}",
        )
        for memory in snapshot.approved_memories
        if memory.sensitivity != "normal" or "meeting_prep" in memory.scopes or "drafting" in memory.scopes
    )


def _used_memory_findings(snapshot: TelegramMemoryCenterSnapshot) -> tuple[MemoryIntelligenceFinding, ...]:
    return tuple(
        MemoryIntelligenceFinding(
            finding_type="used_memory",
            memory_ids=(memory.item_id,),
            summary=f"{memory.memory_kind}: {memory.summary}",
            suggested_action="This approved memory may influence today, prep, and draft outputs.",
            influence=f"source {memory.source}",
        )
        for memory in snapshot.approved_memories
    )


def _norm(value: str) -> str:
    return " ".join(value.lower().split())
