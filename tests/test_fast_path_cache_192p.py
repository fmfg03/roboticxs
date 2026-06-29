from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.fast_path_cache import (
    FAST_PATH_CACHE_STAGE,
    FastPathCacheEntry,
    build_fast_path_cache_entry,
    find_fast_path_cache_entry,
    render_fast_path_cached_reply,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/FAST_PATH_CACHE_192P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_192p_cache_entry_renders_freshness_and_source_trace():
    entry = build_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/today",
        cached_reply="Today cached summary",
        source_trace="calendar:trace-192p memory:snapshot-192p",
        cached_at_epoch_seconds=1_000,
        ttl_seconds=120,
    )
    rendered = render_fast_path_cached_reply(entry, now_epoch_seconds=1_030)

    assert entry.stage == FAST_PATH_CACHE_STAGE
    assert entry.is_fresh(now_epoch_seconds=1_030) is True
    assert "Status: hit" in rendered
    assert "Freshness: fresh (30s old, ttl 120s)" in rendered
    assert "Source trace: calendar:trace-192p memory:snapshot-192p" in rendered
    assert "Today cached summary" in rendered
    assert "Connector reads: not performed for this reply" in rendered
    assert "External writes: disabled" in rendered


def test_192p_cache_lookup_rejects_stale_and_cross_owner_entries():
    fresh = build_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/usage",
        cached_reply="Usage cached summary",
        source_trace="usage:ledger-192p",
        cached_at_epoch_seconds=1_000,
        ttl_seconds=60,
    )
    stale = build_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/usage",
        cached_reply="Stale usage",
        source_trace="usage:old",
        cached_at_epoch_seconds=800,
        ttl_seconds=60,
    )

    assert find_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/usage",
        entries=(stale, fresh),
        now_epoch_seconds=1_030,
    ) == fresh
    assert find_fast_path_cache_entry(
        owner_id="other-owner",
        robot_id="robot-192p",
        command="/usage",
        entries=(fresh,),
        now_epoch_seconds=1_030,
    ) is None
    assert find_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/usage",
        entries=(stale,),
        now_epoch_seconds=1_030,
    ) is None


def test_192p_cache_rejects_authority_expansion():
    entry = build_fast_path_cache_entry(
        owner_id="owner-192p",
        robot_id="robot-192p",
        command="/memory",
        cached_reply="Memory cached summary",
        source_trace="memory:snapshot-192p",
        cached_at_epoch_seconds=1_000,
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        FastPathCacheEntry(**{**asdict(entry), "external_write_allowed": True})


def test_192p_reference_and_roadmap_close_cache_without_ranking():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "192P adds a safe local fast path" in reference
    assert "connector reads for cached replies" in reference
    assert "no smart context ranking" in reference
    assert '"stage_id":"192P","stage_name":"Fast Path Cache v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "201P and later remain unauthorized" in roadmap
