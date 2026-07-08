from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.memory_center_projection import MemoryCenterItem
from app.memory_intelligence import (
    MEMORY_INTELLIGENCE_STAGE,
    MemoryIntelligenceReport,
    build_memory_intelligence_report,
    render_memory_intelligence_report,
)
from app.telegram_memory_center_commands import TelegramMemoryCenterSourceBundle, build_memory_center_telegram_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/MEMORY_INTELLIGENCE_196P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_196p_detects_duplicate_stale_conflict_high_impact_and_used_memory():
    report = build_memory_intelligence_report(snapshot())
    rendered = render_memory_intelligence_report(report)
    finding_types = {finding.finding_type for finding in report.findings}

    assert report.stage == MEMORY_INTELLIGENCE_STAGE
    assert report.status == "findings_available"
    assert {"duplicate", "stale", "conflict", "high_impact", "used_memory"}.issubset(finding_types)
    assert "Memory Intelligence" in rendered
    assert "suggested action:" in rendered
    assert "influence:" in rendered
    assert "No memory was merged, edited, forgotten, or written." in rendered


def test_196p_empty_memory_remains_read_only():
    empty = build_memory_center_telegram_snapshot(owner_id="owner-196p", robot_id="robot-196p")
    report = build_memory_intelligence_report(empty)

    assert report.status == "no_memory_intelligence_findings"
    assert report.findings == ()
    assert report.memory_center_mutated is False
    assert report.memory_store_mutated is False
    assert report.external_write_allowed is False


def test_196p_rejects_authority_expansion():
    report = build_memory_intelligence_report(snapshot())

    with pytest.raises(ValueError, match="must not expand authority"):
        MemoryIntelligenceReport(**{**asdict(report), "memory_center_mutated": True})


def test_196p_reference_and_roadmap_close_memory_intelligence_without_actions():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "196P analyzes visible approved memory" in reference
    assert "does not perform those actions" in reference
    assert '"stage_id":"196P","stage_name":"Memory Intelligence v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "221P and later remain unauthorized" in roadmap


def snapshot():
    return build_memory_center_telegram_snapshot(
        owner_id="owner-196p",
        robot_id="robot-196p",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(
                memory("mem-a", "preference", "Prefers short prep notes", scopes=("meeting_prep",)),
                memory("mem-b", "preference", "Prefers short prep notes", scopes=("meeting_prep",)),
                memory("mem-c", "preference", "No longer prefers long meeting notes"),
                memory("mem-d", "preference", "Prefers detailed risk notes", sensitivity="sensitive"),
            )
        ),
    )


def memory(
    item_id: str,
    kind: str,
    summary: str,
    *,
    scopes: tuple[str, ...] = ("general",),
    sensitivity: str = "normal",
) -> MemoryCenterItem:
    return MemoryCenterItem(
        item_id=item_id,
        owner_id="owner-196p",
        robot_id="robot-196p",
        memory_kind=kind,
        status="approved",
        scopes=scopes,
        sensitivity=sensitivity,
        allowed_uses=("context",),
        skill_ids=(),
        content=summary,
        bounded_summary=summary,
        source="owner_approved",
    )
