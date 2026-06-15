from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MEMORY_CENTER_PROJECTION_STAGE = "99P"

MemoryStatus = Literal["proposed", "approved", "active", "stale", "revoked", "conflicted", "never-use-for-decisions"]
ActorRole = Literal["owner_admin", "caregiver", "care_recipient", "robot", "routine"]
ProjectionScope = Literal["general", "caregiver", "routine", "telegram", "hermes_os", "skill_specific"]
Sensitivity = Literal["ordinary", "personal", "caregiver", "credential_like", "medical", "legal", "financial", "safety_critical"]
AllowedUse = Literal[
    "answer_personalization",
    "boundary_enforcement",
    "caregiver_context",
    "routine_context",
    "telegram_context",
    "hermes_os_context",
    "skill_context",
    "audit_only",
]
ProjectionDecision = Literal["include", "include_redacted", "exclude", "include_audit_non_decisional", "reject_request"]

ACTOR_ROLES = frozenset({"owner_admin", "caregiver", "care_recipient", "robot", "routine"})
PROJECTION_SCOPES = frozenset({"general", "caregiver", "routine", "telegram", "hermes_os", "skill_specific"})
MEMORY_STATUSES = frozenset({"proposed", "approved", "active", "stale", "revoked", "conflicted", "never-use-for-decisions"})
SENSITIVITIES = frozenset({"ordinary", "personal", "caregiver", "credential_like", "medical", "legal", "financial", "safety_critical"})
ALLOWED_USES = frozenset(
    {
        "answer_personalization",
        "boundary_enforcement",
        "caregiver_context",
        "routine_context",
        "telegram_context",
        "hermes_os_context",
        "skill_context",
        "audit_only",
    }
)
SUPPORTED_ACTIVE_SKILL_IDS = frozenset({"basic_assistant"})
SENSITIVE = frozenset({"personal", "caregiver", "medical", "legal", "financial", "safety_critical"})
MAX_ITEMS_CAP = 20
MAX_SUMMARY_CHARS_CAP = 500


@dataclass(frozen=True, slots=True)
class MemoryCenterItem:
    item_id: str
    owner_id: str
    robot_id: str
    memory_kind: str
    status: str
    scopes: tuple[str, ...]
    sensitivity: str
    allowed_uses: tuple[str, ...]
    skill_ids: tuple[str, ...]
    content: str
    bounded_summary: str | None
    source: str
    conflict_group: str | None = None
    is_boundary: bool = False
    is_preference: bool = False

    def __post_init__(self) -> None:
        if not self.item_id or not self.owner_id or not self.robot_id:
            raise ValueError("MemoryCenterItem requires item, owner, and robot identifiers.")
        if self.is_boundary and self.is_preference:
            raise ValueError("MemoryCenterItem cannot be both boundary and preference memory.")
        if "skill_specific" in self.scopes and not self.skill_ids:
            raise ValueError("Skill-specific memory requires at least one skill id.")


@dataclass(frozen=True, slots=True)
class MemoryProjectionRequest:
    request_id: str
    actor_id: str
    actor_role: str
    owner_id: str
    robot_id: str
    target_scope: str
    allowed_use: str
    decision_context: bool = True
    audit_only: bool = False
    active_skill_id: str | None = None
    max_items: int = 3
    max_summary_chars: int = 160
    authority_expansion_requested: bool = False


@dataclass(frozen=True, slots=True)
class ProjectedMemorySummary:
    item_id: str
    memory_kind: str
    summary: str
    source: str
    status: str
    matched_scope: str
    sensitivity: str
    allowed_use: str
    decisional: bool
    redacted: bool
    conflict_disposition: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionTraceRecord:
    request_id: str
    item_id: str | None
    decision: ProjectionDecision
    reason_code: str
    actor_role: str
    target_scope: str
    status: str | None
    sensitivity: str | None
    decisional: bool
    authority_expanded: bool = False


@dataclass(frozen=True, slots=True)
class MemoryProjectionResult:
    request_id: str
    status: Literal["completed", "rejected"]
    summaries: tuple[ProjectedMemorySummary, ...]
    trace: tuple[ProjectionTraceRecord, ...]
    excluded_count: int
    redacted_count: int
    audit_only_count: int
    bounded: bool = True
    data_only: bool = True
    tool_action_authorization: bool = False
    permission_expansion_authorized: bool = False
    external_effect_authorized: bool = False
    model_provider_access_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.bounded or not self.data_only:
            raise ValueError("99P projection results must be bounded data-only results.")
        if any(
            (
                self.tool_action_authorization,
                self.permission_expansion_authorized,
                self.external_effect_authorized,
                self.model_provider_access_authorized,
            )
        ):
            raise ValueError("99P projection cannot expand authority.")


def project_memory(
    *,
    request: MemoryProjectionRequest,
    items: tuple[MemoryCenterItem, ...],
) -> MemoryProjectionResult:
    rejection = _request_rejection(request)
    if rejection is not None:
        return _rejected(request, rejection)

    candidates: list[tuple[MemoryCenterItem, ProjectedMemorySummary]] = []
    traces: list[ProjectionTraceRecord] = []
    boundaries = {
        item.conflict_group
        for item in items
        if item.is_boundary
        and item.conflict_group
        and _exclusion_reason(request, item, set()) is None
        and _summary_for(request, item)[0] is not None
    }

    for item in sorted(items, key=lambda value: (not value.is_boundary, value.item_id)):
        reason = _exclusion_reason(request, item, boundaries)
        if reason is not None:
            traces.append(_trace(request, item, "exclude", reason, decisional=False))
            continue

        if request.audit_only:
            traces.append(_trace(request, item, "include_audit_non_decisional", "included_audit_non_decisional", False))
            continue

        summary, redacted = _summary_for(request, item)
        if summary is None:
            explicitly_scoped = request.target_scope in item.scopes and request.allowed_use in item.allowed_uses
            reason = (
                "excluded_sensitive_no_safe_summary"
                if item.sensitivity in SENSITIVE and explicitly_scoped
                else "excluded_sensitive_unauthorized"
            )
            traces.append(_trace(request, item, "exclude", reason, decisional=False))
            continue
        bounded = summary[: min(request.max_summary_chars, MAX_SUMMARY_CHARS_CAP)]
        projected = ProjectedMemorySummary(
            item_id=item.item_id,
            memory_kind=item.memory_kind,
            summary=bounded,
            source=item.source,
            status=item.status,
            matched_scope=request.target_scope,
            sensitivity=item.sensitivity,
            allowed_use=request.allowed_use,
            decisional=True,
            redacted=redacted,
        )
        candidates.append((item, projected))

    limit = min(request.max_items, MAX_ITEMS_CAP)
    summaries = tuple(projected for _, projected in candidates[:limit])
    for item, projected in candidates[:limit]:
        traces.append(
            _trace(
                request,
                item,
                "include_redacted" if projected.redacted else "include",
                "included_redacted_sensitive_summary" if projected.redacted else "included_allowed_context",
                decisional=True,
            )
        )
    for item, _ in candidates[limit:]:
        traces.append(_trace(request, item, "exclude", "excluded_result_bound", decisional=False))

    return MemoryProjectionResult(
        request_id=request.request_id,
        status="completed",
        summaries=summaries,
        trace=tuple(sorted(traces, key=lambda trace: (trace.item_id or "", trace.reason_code))),
        excluded_count=sum(trace.decision == "exclude" for trace in traces),
        redacted_count=sum(summary.redacted for summary in summaries),
        audit_only_count=sum(trace.decision == "include_audit_non_decisional" for trace in traces),
    )


def _request_rejection(request: MemoryProjectionRequest) -> str | None:
    if request.actor_role not in ACTOR_ROLES:
        return "rejected_unknown_actor"
    if request.target_scope not in PROJECTION_SCOPES:
        return "rejected_unknown_scope"
    if request.allowed_use not in ALLOWED_USES:
        return "rejected_unknown_allowed_use"
    if request.audit_only and request.decision_context:
        return "rejected_invalid_audit_decision_combination"
    if request.target_scope == "skill_specific" and not request.active_skill_id:
        return "rejected_unknown_scope"
    if request.target_scope == "skill_specific" and request.active_skill_id not in SUPPORTED_ACTIVE_SKILL_IDS:
        return "rejected_unsupported_active_skill"
    if request.authority_expansion_requested:
        return "rejected_authority_expansion"
    if request.max_items <= 0 or request.max_summary_chars <= 0:
        return "rejected_invalid_bounds"
    return None


def _exclusion_reason(
    request: MemoryProjectionRequest,
    item: MemoryCenterItem,
    boundaries: set[str | None],
) -> str | None:
    if item.owner_id != request.owner_id or item.robot_id != request.robot_id:
        return "excluded_owner_isolation"
    if item.status not in MEMORY_STATUSES:
        return "excluded_unknown_status"
    if any(scope not in PROJECTION_SCOPES for scope in item.scopes):
        return "excluded_unknown_scope"
    if item.sensitivity not in SENSITIVITIES:
        return "excluded_unknown_sensitivity"
    if any(use not in ALLOWED_USES for use in item.allowed_uses):
        return "excluded_unknown_allowed_use"
    if request.actor_role in {"caregiver", "care_recipient"} and request.target_scope != "caregiver":
        return "excluded_actor_isolation"
    if request.actor_role == "routine" and request.target_scope != "routine":
        return "excluded_actor_isolation"
    if request.target_scope not in item.scopes:
        return "excluded_scope_mismatch"
    if request.target_scope == "skill_specific" and request.active_skill_id not in item.skill_ids:
        return "excluded_skill_mismatch"
    if item.status == "revoked":
        return "excluded_status_revoked"
    if item.status == "stale":
        return "excluded_status_stale"
    if item.status == "proposed":
        return "excluded_status_proposed"
    if item.status == "conflicted":
        return "excluded_status_conflicted"
    if item.status == "never-use-for-decisions" and request.decision_context:
        return "excluded_never_use_for_decisions"
    if request.allowed_use not in item.allowed_uses:
        return "excluded_allowed_use_mismatch"
    if item.is_preference and item.conflict_group and item.conflict_group in boundaries:
        return "excluded_preference_conflicts_with_boundary"
    if item.sensitivity == "credential_like":
        return "excluded_sensitive_unauthorized"
    return None


def _summary_for(request: MemoryProjectionRequest, item: MemoryCenterItem) -> tuple[str | None, bool]:
    if item.sensitivity == "ordinary":
        return item.bounded_summary or item.content, False
    if item.sensitivity in SENSITIVE:
        explicitly_scoped = request.target_scope in item.scopes and request.allowed_use in item.allowed_uses
        if explicitly_scoped and item.bounded_summary and request.actor_role not in {"caregiver", "care_recipient"}:
            return item.bounded_summary, True
        if explicitly_scoped and item.bounded_summary and request.target_scope == "caregiver":
            return item.bounded_summary, True
    return None, False


def _trace(
    request: MemoryProjectionRequest,
    item: MemoryCenterItem,
    decision: ProjectionDecision,
    reason_code: str,
    decisional: bool,
) -> ProjectionTraceRecord:
    return ProjectionTraceRecord(
        request_id=request.request_id,
        item_id=item.item_id,
        decision=decision,
        reason_code=reason_code,
        actor_role=request.actor_role,
        target_scope=request.target_scope,
        status=item.status,
        sensitivity=item.sensitivity,
        decisional=decisional,
    )


def _rejected(request: MemoryProjectionRequest, reason: str) -> MemoryProjectionResult:
    trace = ProjectionTraceRecord(
        request_id=request.request_id,
        item_id=None,
        decision="reject_request",
        reason_code=reason,
        actor_role=request.actor_role,
        target_scope=request.target_scope,
        status=None,
        sensitivity=None,
        decisional=False,
    )
    return MemoryProjectionResult(
        request_id=request.request_id,
        status="rejected",
        summaries=(),
        trace=(trace,),
        excluded_count=0,
        redacted_count=0,
        audit_only_count=0,
    )
