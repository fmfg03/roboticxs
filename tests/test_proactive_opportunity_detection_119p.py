from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.context_scan_candidate_source import ContextScanCandidateSourceRegistry, create_context_scan_candidate_source, create_local_context_scan_authorization
from app.memory_center_projection import MemoryCenterItem
from app.proactive_opportunity_detection import (
    PROACTIVE_OPPORTUNITY_DETECTION_STAGE,
    ProactiveOpportunityRegistry,
    detect_proactive_opportunity_from_context_source,
    get_proactive_opportunity_candidate,
    list_proactive_opportunity_candidates,
    run_local_proactive_opportunity_detection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_opportunity_detection.py"

ALLOWED_SOURCE_TYPES = [
    "mock_email_thread",
    "mock_calendar_event",
    "mock_document",
    "mock_task_item",
    "mock_crm_note",
    "mock_invoice_record",
    "mock_message_thread",
    "mock_memory_snapshot",
]
DEFAULT_SCOPES = ["metadata_only", "summary_fixture", "selected_fields_fixture", "local_test_snapshot"]


def source_registry() -> ContextScanCandidateSourceRegistry:
    return ContextScanCandidateSourceRegistry()


def opportunity_registry() -> ProactiveOpportunityRegistry:
    return ProactiveOpportunityRegistry()


def create_auth(registry: ContextScanCandidateSourceRegistry, **overrides):
    values = {
        "owner_id": "owner-119p",
        "robot_id": "robot-119p",
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "allowed_scan_scopes": DEFAULT_SCOPES,
    }
    values.update(overrides)
    return create_local_context_scan_authorization(registry=registry, **values)


def create_source(
    registry: ContextScanCandidateSourceRegistry,
    authorization_id: str,
    **overrides,
):
    values = {
        "owner_id": "owner-119p",
        "robot_id": "robot-119p",
        "authorization_id": authorization_id,
        "source_type": "mock_document",
        "source_status": "authorized_local_fixture",
        "scan_scope": "summary_fixture",
        "fixture_id": "fixture-119p-default",
        "source_title": "Default source",
        "source_summary": "Default safe fixture summary.",
        "source_timestamp": "2026-06-20T08:00:00Z",
        "source_hint": "local-only fixture",
        "provenance_notes": "safe fixture summary only",
        "retention_policy": "keep_until_fixture_rotation",
    }
    values.update(overrides)
    return create_context_scan_candidate_source(registry=registry, **values)


def memory_item(item_id: str, **overrides) -> MemoryCenterItem:
    values = {
        "item_id": item_id,
        "owner_id": "owner-119p",
        "robot_id": "robot-119p",
        "memory_kind": "WORK_PREFERENCE",
        "status": "active",
        "scopes": ("general", "telegram", "hermes_os"),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context", "hermes_os_context"),
        "skill_ids": (),
        "content": "Use a briefing checklist before sales calls.",
        "bounded_summary": "Use a briefing checklist before sales calls.",
        "source": "followup_result_approved_memory",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


SENTINEL_SOURCE_OBJECT = object()


def unsafe_replace_source(source, **overrides):
    values = {field: getattr(source, field) for field in source.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(source.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


@pytest.mark.parametrize(
    ("source_kwargs", "expected_type", "expected_category", "expected_next_step"),
    [
        (
            {
                "source_type": "mock_calendar_event",
                "fixture_id": "fixture-calendar",
                "source_title": "Investor sync",
                "source_summary": "Upcoming event with missing brief.",
                "source_hint": "missing brief and empty briefing note",
                "source_timestamp": "2026-06-21T08:00:00Z",
            },
            "meeting_brief_missing",
            "meeting",
            "prepare_brief",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-document",
                "source_title": "NDA draft",
                "source_summary": "Contract review needed before signature.",
            },
            "document_review_needed",
            "document",
            "review_document",
        ),
        (
            {
                "source_type": "mock_crm_note",
                "fixture_id": "fixture-crm",
                "source_title": "Open lead note",
                "source_summary": "Open lead follow-up needed after demo.",
            },
            "lead_followup_due",
            "sales",
            "draft_followup",
        ),
        (
            {
                "source_type": "mock_invoice_record",
                "fixture_id": "fixture-invoice",
                "source_title": "June invoice",
                "source_summary": "Payment due soon for monthly retainer invoice.",
            },
            "invoice_due_soon",
            "finance_admin",
            "review_document",
        ),
        (
            {
                "source_type": "mock_message_thread",
                "fixture_id": "fixture-message",
                "source_title": "Support thread",
                "source_summary": "Customer complaint escalation with refund request.",
            },
            "customer_issue_needs_attention",
            "customer_success",
            "draft_followup",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-proposal",
                "source_title": "Proposal sent to ACME",
                "source_summary": "Proposal sent with no response for 10 days.",
            },
            "stale_proposal_followup",
            "sales",
            "draft_followup",
        ),
        (
            {
                "source_type": "mock_task_item",
                "fixture_id": "fixture-task",
                "source_title": "Renew vendor contract",
                "source_summary": "Deadline at risk because blocker remains unresolved.",
            },
            "task_deadline_risk",
            "task_management",
            "summarize_context",
        ),
        (
            {
                "source_type": "mock_email_thread",
                "fixture_id": "fixture-email",
                "source_title": "Board thread",
                "source_summary": "Unread long thread needs summary before meeting.",
            },
            "unread_context_needs_summary",
            "general_context",
            "summarize_context",
        ),
        (
            {
                "source_type": "mock_memory_snapshot",
                "source_status": "authorized_memory_snapshot",
                "scan_scope": "local_test_snapshot",
                "fixture_id": "fixture-memory-gap",
                "source_title": "Memory context snapshot",
                "source_summary": "Missing preference and missing context for customer calls.",
            },
            "memory_gap_detected",
            "memory",
            "review_boundary",
        ),
        (
            {
                "source_type": "mock_memory_snapshot",
                "source_status": "authorized_memory_snapshot",
                "scan_scope": "local_test_snapshot",
                "fixture_id": "fixture-boundary",
                "source_title": "Boundary snapshot",
                "source_summary": "Conflicting boundary and robot limit unclear.",
            },
            "boundary_review_needed",
            "safety_boundary",
            "review_boundary",
        ),
    ],
)
def test_119p_detects_expected_opportunity_types(source_kwargs, expected_type, expected_category, expected_next_step):
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(candidate_registry, auth.authorization_id, **source_kwargs)
    registry = opportunity_registry()

    record = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
        memory_items=(memory_item("memory-1"),),
    )

    assert record.detection_stage == PROACTIVE_OPPORTUNITY_DETECTION_STAGE
    assert record.opportunity_type == expected_type
    assert record.opportunity_category == expected_category
    assert record.suggested_next_step_type == expected_next_step
    assert record.owner_id == "owner-119p"
    assert record.robot_id == "robot-119p"
    assert record.candidate_source_id == source.candidate_source_id
    assert record.authorization_id == auth.authorization_id
    assert record.source_stage == "118P"
    assert record.source_created_detection is False
    assert record.telegram_send_allowed is False
    assert record.followup_adapter_allowed is False
    assert record.async_delegation_allowed is False
    assert record.execution_allowed is False
    assert record.memory_write_allowed is False
    assert record.live_connector_allowed is False
    assert record.external_write_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.evidence_refs[0]["candidate_source_id"] == source.candidate_source_id
    assert record.lineage_summary["proactive_detection_stage"] == "119P"
    assert record.lineage_summary["detection_stage_authorized"] is True


def test_119p_memory_snapshot_detection_can_preserve_117p_memory_lineage():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(
        candidate_registry,
        auth.authorization_id,
        source_type="mock_memory_snapshot",
        source_status="authorized_memory_snapshot",
        scan_scope="local_test_snapshot",
        fixture_id="fixture-memory-lineage",
        source_title="Memory snapshot",
        source_summary="Missing preference context for briefs.",
    )
    registry = opportunity_registry()
    items = (
        memory_item("memory-117p-a"),
        memory_item("memory-117p-b", memory_kind="BOUNDARY_MEMORY", conflict_group="briefs", is_boundary=True),
    )

    record = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
        memory_items=items,
    )

    assert record.opportunity_type == "memory_gap_detected"
    assert record.lineage_summary["memory_lineage_stage"] == "117P"
    assert record.lineage_summary["memory_lineage_ids"] == ("memory-117p-a", "memory-117p-b")
    assert any(ref.get("memory_item_id") == "memory-117p-a" for ref in record.evidence_refs)


def test_119p_no_trigger_creates_safe_no_opportunity_record():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(
        candidate_registry,
        auth.authorization_id,
        fixture_id="fixture-none",
        source_title="Neutral note",
        source_summary="Reference metadata only.",
    )
    registry = opportunity_registry()

    record = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
    )

    assert record.opportunity_type == "no_opportunity"
    assert record.confidence == "not_applicable"
    assert record.suggested_next_step_type == "no_action"


def test_119p_sensitive_content_downgrades_to_safe_no_opportunity():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(
        candidate_registry,
        auth.authorization_id,
        fixture_id="fixture-sensitive",
        source_summary="Medical record attached for diagnosis review.",
    )
    registry = opportunity_registry()

    record = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
    )

    assert record.opportunity_type == "no_opportunity"
    assert record.sensitive_data_blocked is True
    assert "Sensitive source content was blocked" in record.summary


def test_119p_rejects_credential_like_payload_text():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(
        candidate_registry,
        auth.authorization_id,
        fixture_id="fixture-credential",
        source_summary="Contains password rotation notes.",
    )
    registry = opportunity_registry()

    with pytest.raises(ValueError, match="rejected_credential_like_payload"):
        detect_proactive_opportunity_from_context_source(
            source_record=source,
            source_registry=candidate_registry,
            registry=registry,
            owner_id="owner-119p",
            robot_id="robot-119p",
        )


@pytest.mark.parametrize(
        ("source_override", "error"),
        [
            (SENTINEL_SOURCE_OBJECT, "rejected_unknown_source_record"),
            ({"source_stage": "117P"}, "rejected_invalid_source_stage"),
            ({"owner_id": ""}, "rejected_unknown_owner"),
            ({"robot_id": ""}, "rejected_unknown_robot"),
        ({"owner_id": "other-owner"}, "rejected_owner_mismatch"),
        ({"robot_id": "other-robot"}, "rejected_robot_mismatch"),
        ({"source_type": "live_gmail"}, "rejected_live_connector_source_type"),
        ({"source_type": "live_google_calendar"}, "rejected_live_connector_source_type"),
        ({"source_type": "live_external_api"}, "rejected_live_connector_source_type"),
        ({"source_type": "unknown_source"}, "rejected_unsupported_source_type"),
        ({"source_status": "revoked"}, "rejected_unauthorized_source"),
        ({"source_status": "unauthorized"}, "rejected_unauthorized_source"),
        ({"live_connector_allowed": True}, "rejected_live_connector_access_not_allowed"),
        ({"external_read_allowed": True}, "rejected_external_read_not_allowed"),
    ],
)
def test_119p_rejects_invalid_or_unauthorized_sources(source_override, error):
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(candidate_registry, auth.authorization_id)
    registry = opportunity_registry()

    invalid_source = source_override if source_override is SENTINEL_SOURCE_OBJECT else unsafe_replace_source(source, **source_override)

    with pytest.raises(ValueError, match=error):
        detect_proactive_opportunity_from_context_source(
            source_record=invalid_source,
            source_registry=candidate_registry,
            registry=registry,
            owner_id="owner-119p",
            robot_id="robot-119p",
        )


def test_119p_rejects_expired_and_revoked_authorizations():
    for status, error in [("expired", "rejected_expired_authorization"), ("revoked", "rejected_revoked_authorization")]:
        candidate_registry = source_registry()
        auth = create_auth(candidate_registry)
        source = create_source(candidate_registry, auth.authorization_id)
        candidate_registry.authorizations_by_id[auth.authorization_id] = replace(auth, authorization_status=status)
        registry = opportunity_registry()

        with pytest.raises(ValueError, match=error):
            detect_proactive_opportunity_from_context_source(
                source_record=source,
                source_registry=candidate_registry,
                registry=registry,
                owner_id="owner-119p",
                robot_id="robot-119p",
            )


def test_119p_deduplicates_by_source_and_opportunity_lineage():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    source = create_source(
        candidate_registry,
        auth.authorization_id,
        source_type="mock_document",
        fixture_id="fixture-dedupe",
        source_summary="NDA review needed before signature.",
    )
    registry = opportunity_registry()

    first = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
    )
    second = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
    )

    assert first == second
    assert get_proactive_opportunity_candidate(registry=registry, opportunity_id=first.opportunity_id) == first
    assert list_proactive_opportunity_candidates(registry=registry) == (first,)


def test_119p_detection_run_collects_sorted_ids_without_authority_expansion():
    candidate_registry = source_registry()
    auth = create_auth(candidate_registry)
    first_source = create_source(
        candidate_registry,
        auth.authorization_id,
        fixture_id="fixture-run-a",
        source_type="mock_document",
        source_summary="Contract review needed.",
    )
    second_source = create_source(
        candidate_registry,
        auth.authorization_id,
        fixture_id="fixture-run-b",
        source_type="mock_task_item",
        source_summary="Deadline at risk because blocker remains.",
    )
    registry = opportunity_registry()

    run = run_local_proactive_opportunity_detection(
        candidate_sources=(first_source, second_source),
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-119p",
        robot_id="robot-119p",
    )

    assert run.detection_stage == "119P"
    assert run.detection_mode == "deterministic_local"
    assert run.live_connector_allowed is False
    assert run.telegram_send_allowed is False
    assert run.memory_write_allowed is False
    assert len(run.input_candidate_source_ids) == 2
    assert len(run.opportunity_ids) == 2


def test_119p_module_stays_local_only_and_non_executing():
    text = MODULE_PATH.read_text()

    for blocked_import in ["import requests", "import httpx", "import openai", "import slack_sdk", "subprocess"]:
        assert blocked_import not in text
    for blocked_term in [
        "requests.get(",
        "httpx.get(",
        "openai.",
        "slack_sdk.",
        "send_telegram",
        "create_followup_intent(",
        "dispatch_worker(",
        "write_approved_memory_proposal_to_memory_center(",
    ]:
        assert blocked_term not in text
