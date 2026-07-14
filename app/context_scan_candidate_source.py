from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5


CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE = "118P"
DEFAULT_RECORD_CREATED_AT = "2026-06-20T00:00:00Z"

ALLOWED_SOURCE_TYPES = frozenset(
    {
        "mock_email_thread",
        "mock_calendar_event",
        "mock_document",
        "mock_task_item",
        "mock_crm_note",
        "mock_invoice_record",
        "mock_meeting_note",
        "mock_message_thread",
        "mock_memory_snapshot",
    }
)
BLOCKED_SOURCE_TYPES = frozenset(
    {
        "live_gmail",
        "live_google_calendar",
        "live_google_drive",
        "live_slack",
        "live_crm",
        "live_telegram_history",
        "live_filesystem",
        "live_external_api",
        "unknown_live_connector",
    }
)
ALLOWED_SOURCE_STATUSES = frozenset(
    {
        "authorized_local_fixture",
        "authorized_mock_source",
        "authorized_memory_snapshot",
    }
)
BLOCKED_SOURCE_STATUSES = frozenset(
    {
        "unauthorized",
        "expired_authorization",
        "missing_owner_consent",
        "live_connector_unavailable",
        "revoked",
        "unknown",
    }
)
ALLOWED_SCAN_SCOPES = frozenset(
    {
        "metadata_only",
        "summary_fixture",
        "selected_fields_fixture",
        "local_test_snapshot",
    }
)
BLOCKED_SCAN_SCOPES = frozenset(
    {
        "full_live_history",
        "unrestricted_account_access",
        "credential_access",
        "destructive_access",
        "external_write_access",
        "unknown",
    }
)
SOURCE_CATEGORY_BY_TYPE = {
    "mock_email_thread": "email_context",
    "mock_calendar_event": "calendar_context",
    "mock_document": "document_context",
    "mock_task_item": "task_context",
    "mock_crm_note": "crm_context",
    "mock_invoice_record": "finance_admin_context",
    "mock_meeting_note": "meeting_context",
    "mock_message_thread": "message_context",
    "mock_memory_snapshot": "memory_context",
}
SENSITIVE_KEYWORDS = frozenset(
    {
        "medical record",
        "medical_records",
        "private token",
        "precise geolocation",
        "identity document",
        "passport",
        "driver license",
        "legal instruction",
        "tax instruction",
        "financial instruction",
        "professional judgment",
        "diagnosis",
    }
)
CREDENTIAL_KEYWORDS = frozenset(
    {
        "password",
        "passwd",
        "api_key",
        "api key",
        "secret",
        "token",
        "bearer",
        "credential",
        "access_key",
        "private_key",
    }
)


@dataclass(frozen=True, slots=True)
class ContextScanAuthorizationRecord:
    authorization_id: str
    owner_id: str
    robot_id: str
    allowed_source_types: tuple[str, ...]
    allowed_scan_scopes: tuple[str, ...]
    authorization_status: str
    granted_by_owner: bool
    live_connector_allowed: bool
    external_read_allowed: bool
    expires_at: str | None
    created_at: str

    def __post_init__(self) -> None:
        if not self.owner_id:
            raise ValueError("rejected_unknown_owner")
        if not self.robot_id:
            raise ValueError("rejected_unknown_robot")
        if self.authorization_status not in {"active", "expired", "revoked"}:
            raise ValueError("rejected_invalid_authorization_status")
        if not self.granted_by_owner:
            raise ValueError("rejected_missing_owner_consent")
        if self.live_connector_allowed:
            raise ValueError("rejected_live_connector_access_not_allowed")
        if self.external_read_allowed:
            raise ValueError("rejected_external_read_not_allowed")
        if not set(self.allowed_source_types).issubset(ALLOWED_SOURCE_TYPES):
            raise ValueError("rejected_unsupported_source_type")
        if not set(self.allowed_scan_scopes).issubset(ALLOWED_SCAN_SCOPES):
            raise ValueError("rejected_invalid_scan_scope")


@dataclass(frozen=True, slots=True)
class ContextScanCandidateSourceRecord:
    candidate_source_id: str
    owner_id: str
    robot_id: str
    authorization_id: str
    source_type: str
    source_category: str
    source_status: str
    scan_scope: str
    fixture_id: str
    source_title: str
    source_summary: str | None
    source_timestamp: str | None
    source_origin: str
    source_stage: str
    live_connector_allowed: bool
    external_read_allowed: bool
    external_write_allowed: bool
    memory_write_allowed: bool
    proactive_detection_allowed: bool
    telegram_send_allowed: bool
    worker_dispatch_allowed: bool
    sensitive_data_blocked: bool
    retention_policy: str | None
    dedupe_key: str
    lineage_summary: dict[str, object]
    created_at: str

    def __post_init__(self) -> None:
        if self.source_stage != CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE:
            raise ValueError("rejected_invalid_source_stage")
        if self.source_type not in ALLOWED_SOURCE_TYPES:
            raise ValueError("rejected_unsupported_source_type")
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError("rejected_unauthorized_source_status")
        if self.scan_scope not in ALLOWED_SCAN_SCOPES:
            raise ValueError("rejected_invalid_scan_scope")
        if any(
            (
                self.live_connector_allowed,
                self.external_read_allowed,
                self.external_write_allowed,
                self.memory_write_allowed,
                self.proactive_detection_allowed,
                self.telegram_send_allowed,
                self.worker_dispatch_allowed,
            )
        ):
            raise ValueError("rejected_authority_expansion_not_allowed")


@dataclass(slots=True)
class ContextScanCandidateSourceRegistry:
    authorizations_by_id: dict[str, ContextScanAuthorizationRecord] = field(default_factory=dict)
    candidates_by_id: dict[str, ContextScanCandidateSourceRecord] = field(default_factory=dict)
    candidate_ids_by_dedupe_key: dict[str, str] = field(default_factory=dict)

    def store_authorization(self, record: ContextScanAuthorizationRecord) -> ContextScanAuthorizationRecord:
        self.authorizations_by_id[record.authorization_id] = record
        return record

    def get_authorization(self, authorization_id: str) -> ContextScanAuthorizationRecord | None:
        return self.authorizations_by_id.get(authorization_id)

    def store_candidate(self, record: ContextScanCandidateSourceRecord) -> ContextScanCandidateSourceRecord:
        self.candidates_by_id[record.candidate_source_id] = record
        self.candidate_ids_by_dedupe_key[record.dedupe_key] = record.candidate_source_id
        return record

    def get_candidate(self, candidate_source_id: str) -> ContextScanCandidateSourceRecord | None:
        return self.candidates_by_id.get(candidate_source_id)

    def get_candidate_by_dedupe_key(self, dedupe_key: str) -> ContextScanCandidateSourceRecord | None:
        candidate_source_id = self.candidate_ids_by_dedupe_key.get(dedupe_key)
        if candidate_source_id is None:
            return None
        return self.candidates_by_id.get(candidate_source_id)

    def list_candidates(self) -> tuple[ContextScanCandidateSourceRecord, ...]:
        return tuple(self.candidates_by_id[key] for key in sorted(self.candidates_by_id))


def create_local_context_scan_authorization(
    *,
    owner_id: str,
    robot_id: str,
    allowed_source_types: tuple[str, ...] | list[str],
    allowed_scan_scopes: tuple[str, ...] | list[str],
    registry: ContextScanCandidateSourceRegistry,
    authorization_status: str = "active",
    granted_by_owner: bool = True,
    live_connector_allowed: bool = False,
    external_read_allowed: bool = False,
    expires_at: str | None = None,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ContextScanAuthorizationRecord:
    allowed_source_types_tuple = tuple(sorted(set(allowed_source_types)))
    allowed_scan_scopes_tuple = tuple(sorted(set(allowed_scan_scopes)))
    authorization_id = _stable_id(
        "context_scan_authorization",
        owner_id,
        robot_id,
        authorization_status,
        ",".join(allowed_source_types_tuple),
        ",".join(allowed_scan_scopes_tuple),
        expires_at or "no-expiry",
    )
    existing = registry.get_authorization(authorization_id)
    if existing is not None:
        return existing
    record = ContextScanAuthorizationRecord(
        authorization_id=authorization_id,
        owner_id=owner_id,
        robot_id=robot_id,
        allowed_source_types=allowed_source_types_tuple,
        allowed_scan_scopes=allowed_scan_scopes_tuple,
        authorization_status=authorization_status,
        granted_by_owner=granted_by_owner,
        live_connector_allowed=live_connector_allowed,
        external_read_allowed=external_read_allowed,
        expires_at=expires_at,
        created_at=created_at,
    )
    return registry.store_authorization(record)


def create_context_scan_candidate_source(
    *,
    owner_id: str,
    robot_id: str,
    authorization_id: str,
    source_type: str,
    source_status: str,
    scan_scope: str,
    fixture_id: str,
    source_title: str,
    registry: ContextScanCandidateSourceRegistry,
    source_summary: str | None = None,
    source_timestamp: str | None = None,
    source_hint: str | None = None,
    retention_policy: str | None = None,
    provenance_notes: str | None = None,
    source_payload: object | None = None,
    created_at: str = DEFAULT_RECORD_CREATED_AT,
) -> ContextScanCandidateSourceRecord:
    authorization = get_local_context_scan_authorization(registry=registry, authorization_id=authorization_id)
    if authorization is None:
        raise ValueError("rejected_unknown_authorization")
    if not owner_id:
        raise ValueError("rejected_unknown_owner")
    if not robot_id:
        raise ValueError("rejected_unknown_robot")
    if owner_id != authorization.owner_id:
        raise ValueError("rejected_unknown_owner")
    if robot_id != authorization.robot_id:
        raise ValueError("rejected_unknown_robot")
    if authorization.authorization_status == "expired":
        raise ValueError("rejected_expired_authorization")
    if authorization.authorization_status == "revoked":
        raise ValueError("rejected_revoked_authorization")
    if not authorization.granted_by_owner:
        raise ValueError("rejected_missing_owner_consent")
    if authorization.live_connector_allowed:
        raise ValueError("rejected_live_connector_access_not_allowed")
    if authorization.external_read_allowed:
        raise ValueError("rejected_external_read_not_allowed")
    if source_type in BLOCKED_SOURCE_TYPES:
        raise ValueError("rejected_live_connector_source_type")
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("rejected_unsupported_source_type")
    if source_status in BLOCKED_SOURCE_STATUSES:
        raise ValueError(_blocked_source_status_error(source_status))
    if source_status not in ALLOWED_SOURCE_STATUSES:
        raise ValueError("rejected_unauthorized_source_status")
    if not scan_scope:
        raise ValueError("rejected_missing_scan_scope")
    if scan_scope in BLOCKED_SCAN_SCOPES:
        raise ValueError("rejected_blocked_scan_scope")
    if scan_scope not in ALLOWED_SCAN_SCOPES:
        raise ValueError("rejected_invalid_scan_scope")
    if source_type not in authorization.allowed_source_types:
        raise ValueError("rejected_unauthorized_source_type_for_authorization")
    if scan_scope not in authorization.allowed_scan_scopes:
        raise ValueError("rejected_unauthorized_scan_scope_for_authorization")
    if not fixture_id:
        raise ValueError("rejected_missing_fixture_id")
    if source_payload is not None:
        payload_text = _flatten_text(source_payload)
        if _contains_blocked_keywords(payload_text, CREDENTIAL_KEYWORDS):
            raise ValueError("rejected_credential_like_payload")
        if _contains_blocked_keywords(payload_text, SENSITIVE_KEYWORDS):
            raise ValueError("rejected_sensitive_raw_payload")
        raise ValueError("rejected_raw_payload_not_allowed")

    dedupe_key = _stable_id(
        "context_scan_candidate_dedupe",
        owner_id,
        robot_id,
        authorization_id,
        source_type,
        source_status,
        scan_scope,
        fixture_id,
        source_timestamp or "no-timestamp",
    )
    existing = registry.get_candidate_by_dedupe_key(dedupe_key)
    if existing is not None:
        return existing

    source_origin = _source_origin(source_type=source_type, source_status=source_status)
    candidate_source_id = _stable_id("context_scan_candidate_source", dedupe_key)
    record = ContextScanCandidateSourceRecord(
        candidate_source_id=candidate_source_id,
        owner_id=owner_id,
        robot_id=robot_id,
        authorization_id=authorization_id,
        source_type=source_type,
        source_category=SOURCE_CATEGORY_BY_TYPE[source_type],
        source_status=source_status,
        scan_scope=scan_scope,
        fixture_id=fixture_id,
        source_title=source_title,
        source_summary=source_summary,
        source_timestamp=source_timestamp,
        source_origin=source_origin,
        source_stage=CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
        live_connector_allowed=False,
        external_read_allowed=False,
        external_write_allowed=False,
        memory_write_allowed=False,
        proactive_detection_allowed=False,
        telegram_send_allowed=False,
        worker_dispatch_allowed=False,
        sensitive_data_blocked=False,
        retention_policy=retention_policy,
        dedupe_key=dedupe_key,
        lineage_summary={
            "owner_id": owner_id,
            "robot_id": robot_id,
            "authorization_id": authorization_id,
            "source_type": source_type,
            "source_status": source_status,
            "scan_scope": scan_scope,
            "fixture_id": fixture_id,
            "source_origin": source_origin,
            "source_stage": CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
            "source_hint": source_hint,
            "provenance_notes": provenance_notes,
            "retention_policy": retention_policy,
        },
        created_at=created_at,
    )
    return registry.store_candidate(record)


def get_context_scan_candidate_source(
    *,
    registry: ContextScanCandidateSourceRegistry,
    candidate_source_id: str,
) -> ContextScanCandidateSourceRecord | None:
    return registry.get_candidate(candidate_source_id)


def list_context_scan_candidate_sources(
    *,
    registry: ContextScanCandidateSourceRegistry,
) -> tuple[ContextScanCandidateSourceRecord, ...]:
    return registry.list_candidates()


def get_local_context_scan_authorization(
    *,
    registry: ContextScanCandidateSourceRegistry,
    authorization_id: str,
) -> ContextScanAuthorizationRecord | None:
    return registry.get_authorization(authorization_id)


def _blocked_source_status_error(source_status: str) -> str:
    return {
        "unauthorized": "rejected_unauthorized_source",
        "expired_authorization": "rejected_expired_authorization",
        "missing_owner_consent": "rejected_missing_owner_consent",
        "live_connector_unavailable": "rejected_live_connector_access_not_allowed",
        "revoked": "rejected_revoked_authorization",
        "unknown": "rejected_unknown_source_status",
    }[source_status]


def _source_origin(*, source_type: str, source_status: str) -> str:
    if source_type == "mock_memory_snapshot" or source_status == "authorized_memory_snapshot":
        return "memory_snapshot"
    if source_status == "authorized_local_fixture":
        return "local_fixture"
    return "local_mock"


def _contains_blocked_keywords(text: str, keywords: frozenset[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _flatten_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple, set, frozenset)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "::".join(parts)))
