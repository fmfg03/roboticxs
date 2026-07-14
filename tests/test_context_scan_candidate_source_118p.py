from __future__ import annotations

from pathlib import Path

import pytest

from app.context_scan_candidate_source import (
    CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE,
    ContextScanCandidateSourceRegistry,
    create_context_scan_candidate_source,
    create_local_context_scan_authorization,
    get_context_scan_candidate_source,
    get_local_context_scan_authorization,
    list_context_scan_candidate_sources,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/context_scan_candidate_source.py"

ALLOWED_TYPES = [
    ("mock_email_thread", "email_context"),
    ("mock_calendar_event", "calendar_context"),
    ("mock_document", "document_context"),
    ("mock_task_item", "task_context"),
    ("mock_crm_note", "crm_context"),
    ("mock_invoice_record", "finance_admin_context"),
    ("mock_meeting_note", "meeting_context"),
    ("mock_memory_snapshot", "memory_context"),
]


def registry() -> ContextScanCandidateSourceRegistry:
    return ContextScanCandidateSourceRegistry()


def authorization(
    *,
    source_types=None,
    scan_scopes=None,
    authorization_status: str = "active",
    granted_by_owner: bool = True,
):
    return create_local_context_scan_authorization(
        owner_id="owner-118p",
        robot_id="robot-118p",
        allowed_source_types=ALLOWED_TYPES_ONLY if source_types is None else source_types,
        allowed_scan_scopes=DEFAULT_SCOPES if scan_scopes is None else scan_scopes,
        registry=registry(),
        authorization_status=authorization_status,
        granted_by_owner=granted_by_owner,
    )


ALLOWED_TYPES_ONLY = [source_type for source_type, _ in ALLOWED_TYPES] + ["mock_message_thread"]
DEFAULT_SCOPES = ["metadata_only", "summary_fixture", "selected_fields_fixture", "local_test_snapshot"]


def create_auth(registry: ContextScanCandidateSourceRegistry, **overrides):
    values = {
        "owner_id": "owner-118p",
        "robot_id": "robot-118p",
        "allowed_source_types": ALLOWED_TYPES_ONLY,
        "allowed_scan_scopes": DEFAULT_SCOPES,
        "authorization_status": "active",
        "granted_by_owner": True,
    }
    values.update(overrides)
    return create_local_context_scan_authorization(registry=registry, **values)


def create_candidate(registry: ContextScanCandidateSourceRegistry, authorization_id: str, **overrides):
    values = {
        "owner_id": "owner-118p",
        "robot_id": "robot-118p",
        "authorization_id": authorization_id,
        "source_type": "mock_email_thread",
        "source_status": "authorized_mock_source",
        "scan_scope": "summary_fixture",
        "fixture_id": "fixture-118p-email-1",
        "source_title": "Founder follow-up thread",
        "source_summary": "Mock summary only.",
        "source_timestamp": "2026-06-20T08:00:00Z",
        "retention_policy": "keep_until_fixture_rotation",
        "source_hint": "future email scan candidate",
        "provenance_notes": "local fixture only",
    }
    values.update(overrides)
    return create_context_scan_candidate_source(registry=registry, **values)


@pytest.mark.parametrize(("source_type", "category"), ALLOWED_TYPES)
def test_118p_allowed_source_types_create_candidate_records(source_type: str, category: str):
    candidate_registry = registry()
    auth = create_auth(candidate_registry, allowed_source_types=ALLOWED_TYPES_ONLY)

    record = create_candidate(
        candidate_registry,
        auth.authorization_id,
        source_type=source_type,
        fixture_id=f"fixture-{source_type}",
        source_title=f"title-{source_type}",
        source_status="authorized_memory_snapshot" if source_type == "mock_memory_snapshot" else "authorized_local_fixture",
        scan_scope="local_test_snapshot" if source_type == "mock_memory_snapshot" else "summary_fixture",
    )

    assert record.source_type == source_type
    assert record.source_category == category
    assert record.owner_id == "owner-118p"
    assert record.robot_id == "robot-118p"
    assert record.authorization_id == auth.authorization_id
    assert record.source_stage == CONTEXT_SCAN_CANDIDATE_SOURCE_STAGE
    assert record.live_connector_allowed is False
    assert record.external_read_allowed is False
    assert record.memory_write_allowed is False
    assert record.proactive_detection_allowed is False
    assert record.telegram_send_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.sensitive_data_blocked is False
    assert record.lineage_summary["fixture_id"] == f"fixture-{source_type}"


def test_118p_candidate_records_are_queryable_and_deduplicated():
    candidate_registry = registry()
    auth = create_auth(candidate_registry)

    first = create_candidate(candidate_registry, auth.authorization_id)
    second = create_candidate(candidate_registry, auth.authorization_id)

    assert first == second
    assert get_context_scan_candidate_source(registry=candidate_registry, candidate_source_id=first.candidate_source_id) == first
    assert list_context_scan_candidate_sources(registry=candidate_registry) == (first,)


def test_118p_authorization_records_are_queryable_and_deduplicated():
    candidate_registry = registry()

    first = create_auth(candidate_registry)
    second = create_auth(candidate_registry)

    assert first == second
    assert get_local_context_scan_authorization(registry=candidate_registry, authorization_id=first.authorization_id) == first


def test_118p_memory_snapshot_candidates_preserve_memory_snapshot_origin():
    candidate_registry = registry()
    auth = create_auth(candidate_registry)

    record = create_candidate(
        candidate_registry,
        auth.authorization_id,
        source_type="mock_memory_snapshot",
        source_status="authorized_memory_snapshot",
        scan_scope="local_test_snapshot",
        fixture_id="fixture-memory-snapshot-1",
        source_title="Memory snapshot fixture",
        provenance_notes="117P memory center compatible metadata only",
    )

    assert record.source_origin == "memory_snapshot"
    assert record.lineage_summary["source_origin"] == "memory_snapshot"
    assert record.lineage_summary["provenance_notes"] == "117P memory center compatible metadata only"


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"owner_id": ""}, "rejected_unknown_owner"),
        ({"robot_id": ""}, "rejected_unknown_robot"),
        ({"owner_id": "other-owner"}, "rejected_unknown_owner"),
        ({"robot_id": "other-robot"}, "rejected_unknown_robot"),
        ({"source_status": "unauthorized"}, "rejected_unauthorized_source"),
        ({"source_status": "missing_owner_consent"}, "rejected_missing_owner_consent"),
        ({"source_status": "revoked"}, "rejected_revoked_authorization"),
        ({"source_type": "unknown_source"}, "rejected_unsupported_source_type"),
        ({"source_type": "live_gmail"}, "rejected_live_connector_source_type"),
        ({"source_type": "live_google_calendar"}, "rejected_live_connector_source_type"),
        ({"source_type": "live_external_api"}, "rejected_live_connector_source_type"),
        ({"scan_scope": ""}, "rejected_missing_scan_scope"),
        ({"scan_scope": "unrestricted_account_access"}, "rejected_blocked_scan_scope"),
        (
            {"source_payload": {"api_key": "abc-123"}},
            "rejected_credential_like_payload",
        ),
        (
            {"source_payload": {"medical record": "diagnosis details"}},
            "rejected_sensitive_raw_payload",
        ),
    ],
)
def test_118p_rejects_blocked_candidate_inputs(overrides: dict[str, object], error: str):
    candidate_registry = registry()
    auth = create_auth(candidate_registry)

    with pytest.raises(ValueError, match=error):
        create_candidate(candidate_registry, auth.authorization_id, **overrides)


def test_118p_rejects_expired_authorization():
    candidate_registry = registry()
    auth = create_auth(candidate_registry, authorization_status="expired")

    with pytest.raises(ValueError, match="rejected_expired_authorization"):
        create_candidate(candidate_registry, auth.authorization_id)


def test_118p_rejects_revoked_authorization():
    candidate_registry = registry()
    auth = create_auth(candidate_registry, authorization_status="revoked")

    with pytest.raises(ValueError, match="rejected_revoked_authorization"):
        create_candidate(candidate_registry, auth.authorization_id)


def test_118p_rejects_missing_owner_consent_at_authorization_creation():
    candidate_registry = registry()

    with pytest.raises(ValueError, match="rejected_missing_owner_consent"):
        create_auth(candidate_registry, granted_by_owner=False)


def test_118p_rejects_scope_or_type_not_allowed_by_authorization():
    candidate_registry = registry()
    auth = create_auth(
        candidate_registry,
        allowed_source_types=["mock_document"],
        allowed_scan_scopes=["metadata_only"],
    )

    with pytest.raises(ValueError, match="rejected_unauthorized_source_type_for_authorization"):
        create_candidate(candidate_registry, auth.authorization_id, source_type="mock_email_thread")

    with pytest.raises(ValueError, match="rejected_unauthorized_scan_scope_for_authorization"):
        create_candidate(
            candidate_registry,
            auth.authorization_id,
            source_type="mock_document",
            scan_scope="summary_fixture",
            fixture_id="fixture-doc-118p",
            source_title="Spec doc fixture",
        )


def test_118p_candidate_module_stays_local_only_and_non_executing():
    text = MODULE_PATH.read_text()

    for blocked_import in ["import requests", "import httpx", "import openai", "import slack_sdk", "subprocess"]:
        assert blocked_import not in text
    for blocked_term in [
        "requests.get(",
        "httpx.get(",
        "openai.",
        "slack_sdk.",
        "dispatch_worker(",
        "write_memory_center(",
        "create_memory_proposal(",
        "detect_opportunity(",
    ]:
        assert blocked_term not in text
