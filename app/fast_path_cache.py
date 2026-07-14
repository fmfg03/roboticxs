from __future__ import annotations

from dataclasses import dataclass


FAST_PATH_CACHE_STAGE = "192P"
FAST_PATH_CACHEABLE_COMMANDS = frozenset({"/status", "/today", "/usage", "/memory"})
DEFAULT_FAST_PATH_TTL_SECONDS = 120


@dataclass(frozen=True, slots=True)
class FastPathCacheEntry:
    stage: str
    owner_id: str
    robot_id: str
    command: str
    cache_key: str
    cached_reply: str
    source_trace: str
    cached_at_epoch_seconds: int
    ttl_seconds: int
    local_only: bool
    connector_read_performed: bool
    external_write_allowed: bool
    memory_center_mutated: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    worker_dispatch_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != FAST_PATH_CACHE_STAGE:
            raise ValueError("192P fast path cache entries must identify the 192P stage.")
        if self.command not in FAST_PATH_CACHEABLE_COMMANDS:
            raise ValueError("192P fast path cache only supports approved fast commands.")
        if not self.owner_id or not self.robot_id or not self.cache_key:
            raise ValueError("192P fast path cache entries require owner, robot, and key.")
        if not self.cached_reply.strip() or not self.source_trace.strip():
            raise ValueError("192P fast path cache entries require reply and source trace.")
        if self.ttl_seconds <= 0:
            raise ValueError("192P fast path cache entries require positive TTL.")
        if not self.local_only:
            raise ValueError("192P fast path cache entries must remain local only.")
        if any(
            (
                self.connector_read_performed,
                self.external_write_allowed,
                self.memory_center_mutated,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("192P fast path cache entries must not expand authority.")

    def age_seconds(self, *, now_epoch_seconds: int) -> int:
        return max(0, now_epoch_seconds - self.cached_at_epoch_seconds)

    def is_fresh(self, *, now_epoch_seconds: int) -> bool:
        return self.age_seconds(now_epoch_seconds=now_epoch_seconds) <= self.ttl_seconds


def build_fast_path_cache_entry(
    *,
    owner_id: str,
    robot_id: str,
    command: str,
    cached_reply: str,
    source_trace: str,
    cached_at_epoch_seconds: int,
    ttl_seconds: int = DEFAULT_FAST_PATH_TTL_SECONDS,
    cache_key: str | None = None,
) -> FastPathCacheEntry:
    normalized_command = command.strip().split()[0] if command.strip() else ""
    return FastPathCacheEntry(
        stage=FAST_PATH_CACHE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        command=normalized_command,
        cache_key=cache_key or _cache_key(owner_id=owner_id, robot_id=robot_id, command=normalized_command),
        cached_reply=_bounded_text(cached_reply),
        source_trace=_bounded_text(source_trace),
        cached_at_epoch_seconds=cached_at_epoch_seconds,
        ttl_seconds=ttl_seconds,
        local_only=True,
        connector_read_performed=False,
        external_write_allowed=False,
        memory_center_mutated=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        worker_dispatch_allowed=False,
    )


def find_fast_path_cache_entry(
    *,
    owner_id: str,
    robot_id: str,
    command: str,
    entries: tuple[FastPathCacheEntry, ...],
    now_epoch_seconds: int,
) -> FastPathCacheEntry | None:
    normalized_command = command.strip().split()[0] if command.strip() else ""
    candidates = tuple(
        entry
        for entry in entries
        if entry.owner_id == owner_id
        and entry.robot_id == robot_id
        and entry.command == normalized_command
        and entry.is_fresh(now_epoch_seconds=now_epoch_seconds)
    )
    return max(candidates, key=lambda entry: entry.cached_at_epoch_seconds, default=None)


def render_fast_path_cached_reply(entry: FastPathCacheEntry, *, now_epoch_seconds: int) -> str:
    return "\n".join(
        [
            "Fast Path Cache",
            "",
            f"Stage: {entry.stage}",
            "Status: hit",
            f"Command: {entry.command}",
            f"Freshness: fresh ({entry.age_seconds(now_epoch_seconds=now_epoch_seconds)}s old, ttl {entry.ttl_seconds}s)",
            f"Source trace: {entry.source_trace}",
            "Local cache: true",
            "",
            entry.cached_reply,
            "",
            "Boundaries:",
            "Connector reads: not performed for this reply",
            "External writes: disabled",
            "Memory Center mutation: disabled",
            "Model/tool calls: disabled",
            "Worker dispatch: disabled",
            "",
            "No external action was taken.",
        ]
    )


def _cache_key(*, owner_id: str, robot_id: str, command: str) -> str:
    return f"{owner_id}:{robot_id}:{command}:fast-path"


def _bounded_text(value: str) -> str:
    normalized = " ".join(value.split())
    return normalized[:2_000] or "No cached text available."
