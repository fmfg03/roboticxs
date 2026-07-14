from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.context_scan_candidate_source import ContextScanCandidateSourceRegistry, create_context_scan_candidate_source, create_local_context_scan_authorization
from app.proactive_opportunity_detection import ProactiveOpportunityRegistry, detect_proactive_opportunity_from_context_source
from app.proactive_telegram_suggestion import (
    PROACTIVE_TELEGRAM_SUGGESTION_STAGE,
    ProactiveTelegramSuggestionRegistry,
    deliver_proactive_telegram_suggestion_local,
    get_proactive_telegram_suggestion_delivery,
    get_proactive_telegram_suggestion_surface,
    list_proactive_telegram_deliveries,
    list_proactive_telegram_suggestions,
    render_proactive_telegram_suggestion,
)
from app.telegram_async_result_delivery import TelegramOwnerBinding


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_telegram_suggestion.py"

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


class FakeTelegramTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[str, ...]]] = []

    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict:
        self.calls.append((chat_id, text, buttons))
        return {
            "transport": "fake_telegram_local",
            "chat_id": chat_id,
            "message_fingerprint": f"{len(text)}:{len(buttons)}",
        }


def source_registry() -> ContextScanCandidateSourceRegistry:
    return ContextScanCandidateSourceRegistry()


def opportunity_registry() -> ProactiveOpportunityRegistry:
    return ProactiveOpportunityRegistry()


def suggestion_registry() -> ProactiveTelegramSuggestionRegistry:
    return ProactiveTelegramSuggestionRegistry()


def create_auth(registry: ContextScanCandidateSourceRegistry, **overrides):
    values = {
        "owner_id": "owner-120p",
        "robot_id": "robot-120p",
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "allowed_scan_scopes": DEFAULT_SCOPES,
    }
    values.update(overrides)
    return create_local_context_scan_authorization(registry=registry, **values)


def create_source(registry: ContextScanCandidateSourceRegistry, authorization_id: str, **overrides):
    values = {
        "owner_id": "owner-120p",
        "robot_id": "robot-120p",
        "authorization_id": authorization_id,
        "source_type": "mock_document",
        "source_status": "authorized_local_fixture",
        "scan_scope": "summary_fixture",
        "fixture_id": "fixture-120p-default",
        "source_title": "Default source",
        "source_summary": "Default safe fixture summary.",
        "source_timestamp": "2026-06-20T08:00:00Z",
        "source_hint": "local-only fixture",
        "provenance_notes": "safe fixture summary only",
        "retention_policy": "keep_until_fixture_rotation",
    }
    values.update(overrides)
    return create_context_scan_candidate_source(registry=registry, **values)


def create_opportunity(candidate_registry: ContextScanCandidateSourceRegistry, **source_overrides):
    auth = create_auth(candidate_registry)
    source = create_source(candidate_registry, auth.authorization_id, **source_overrides)
    record = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=opportunity_registry(),
        owner_id="owner-120p",
        robot_id="robot-120p",
    )
    return auth, source, record


def binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-120p",
        "robot_id": "robot-120p",
        "telegram_chat_id": "telegram-chat-120p",
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def unsafe_replace_opportunity(opportunity, **overrides):
    values = {field: getattr(opportunity, field) for field in opportunity.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(opportunity.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


SENTINEL_OPPORTUNITY_OBJECT = object()


@pytest.mark.parametrize(
    ("source_kwargs", "expected_type"),
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
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-document",
                "source_title": "NDA draft",
                "source_summary": "Contract review needed before signature.",
            },
            "document_review_needed",
        ),
        (
            {
                "source_type": "mock_crm_note",
                "fixture_id": "fixture-crm",
                "source_title": "Open lead note",
                "source_summary": "Open lead follow-up needed after demo.",
            },
            "lead_followup_due",
        ),
        (
            {
                "source_type": "mock_invoice_record",
                "fixture_id": "fixture-invoice",
                "source_title": "June invoice",
                "source_summary": "Payment due soon for monthly retainer invoice.",
            },
            "invoice_due_soon",
        ),
        (
            {
                "source_type": "mock_message_thread",
                "fixture_id": "fixture-message",
                "source_title": "Support thread",
                "source_summary": "Customer complaint escalation with refund request.",
            },
            "customer_issue_needs_attention",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-proposal",
                "source_title": "Proposal sent to ACME",
                "source_summary": "Proposal sent with no response for 10 days.",
            },
            "stale_proposal_followup",
        ),
        (
            {
                "source_type": "mock_task_item",
                "fixture_id": "fixture-task",
                "source_title": "Renew vendor contract",
                "source_summary": "Deadline at risk because blocker remains unresolved.",
            },
            "task_deadline_risk",
        ),
        (
            {
                "source_type": "mock_email_thread",
                "fixture_id": "fixture-email",
                "source_title": "Board thread",
                "source_summary": "Unread long thread needs summary before meeting.",
            },
            "unread_context_needs_summary",
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
        ),
    ],
)
def test_120p_valid_opportunity_renders_surface(source_kwargs, expected_type):
    candidate_registry = source_registry()
    auth, source, opportunity = create_opportunity(candidate_registry, **source_kwargs)
    registry = suggestion_registry()

    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )

    assert surface.suggestion_stage == PROACTIVE_TELEGRAM_SUGGESTION_STAGE
    assert surface.opportunity_type == expected_type
    assert surface.owner_id == "owner-120p"
    assert surface.robot_id == "robot-120p"
    assert surface.opportunity_id == opportunity.opportunity_id
    assert surface.candidate_source_id == source.candidate_source_id
    assert surface.authorization_id == auth.authorization_id
    assert surface.source_stage == "118P"
    assert surface.detection_stage == "119P"
    assert surface.telegram_transport == "injected_local_only"
    assert surface.live_send_allowed is False
    assert surface.callback_binding_allowed is False
    assert surface.followup_adapter_allowed is False
    assert surface.async_delegation_allowed is False
    assert surface.execution_allowed is False
    assert surface.memory_write_allowed is False
    assert surface.external_write_allowed is False
    assert surface.worker_dispatch_allowed is False
    assert surface.sensitive_data_blocked is False
    assert "No action has been taken." in surface.display_text
    assert surface.safe_evidence_refs[0]["candidate_source_id"] == source.candidate_source_id
    assert surface.lineage_summary["suggestion_stage_authorized"] is True
    assert surface.lineage_summary["telegram_suggestion_stage"] == "120P"


def test_120p_valid_rendered_surface_creates_local_delivery_record():
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_document",
        fixture_id="fixture-delivery",
        source_summary="Contract review needed before signature.",
    )
    registry = suggestion_registry()
    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )
    transport = FakeTelegramTransport()

    delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=surface,
        owner_binding=binding(),
        transport=transport,
        registry=registry,
    )

    assert delivery.delivery_stage == "120P"
    assert delivery.delivery_mode == "injected_local_only"
    assert delivery.delivery_status == "delivered_local"
    assert delivery.live_send_allowed is False
    assert delivery.callback_binding_allowed is False
    assert delivery.followup_adapter_allowed is False
    assert delivery.async_delegation_allowed is False
    assert delivery.execution_allowed is False
    assert delivery.memory_write_allowed is False
    assert delivery.external_write_allowed is False
    assert delivery.worker_dispatch_allowed is False
    assert transport.calls == [("telegram-chat-120p", surface.display_text, ())]


def test_120p_duplicate_rendering_and_delivery_are_dedupe_safe():
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_task_item",
        fixture_id="fixture-dedupe",
        source_summary="Deadline at risk because blocker remains unresolved.",
    )
    registry = suggestion_registry()

    first_surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )
    second_surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )
    transport = FakeTelegramTransport()
    first_delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=first_surface,
        owner_binding=binding(),
        transport=transport,
        registry=registry,
    )
    second_delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=first_surface,
        owner_binding=binding(),
        transport=transport,
        registry=registry,
    )

    assert first_surface == second_surface
    assert first_delivery == second_delivery
    assert get_proactive_telegram_suggestion_surface(registry=registry, suggestion_surface_id=first_surface.suggestion_surface_id) == first_surface
    assert get_proactive_telegram_suggestion_delivery(registry=registry, delivery_record_id=first_delivery.delivery_record_id) == first_delivery
    assert list_proactive_telegram_suggestions(registry=registry) == (first_surface,)
    assert list_proactive_telegram_deliveries(registry=registry) == (first_delivery,)
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("opportunity_override", "error"),
    [
            (SENTINEL_OPPORTUNITY_OBJECT, "rejected_unknown_119p_opportunity_record"),
        ({"detection_stage": "118P"}, "rejected_invalid_detection_stage"),
        ({"source_stage": "117P"}, "rejected_missing_118p_source_lineage"),
        ({"owner_id": "other-owner"}, "rejected_owner_mismatch"),
        ({"robot_id": "other-robot"}, "rejected_robot_mismatch"),
        ({"opportunity_type": "no_opportunity"}, "rejected_no_opportunity"),
        ({"sensitive_data_blocked": True}, "rejected_sensitive_data"),
        ({"live_connector_allowed": True}, "rejected_live_connector_read_required"),
        ({"execution_allowed": True}, "rejected_execution_implied"),
        ({"memory_write_allowed": True}, "rejected_memory_mutation_implied"),
        ({"lineage_summary": {"model_calls_required": True}}, "rejected_model_call_required"),
        ({"lineage_summary": {"tool_calls_required": True}}, "rejected_tool_call_required"),
    ],
)
def test_120p_rejects_invalid_opportunities(opportunity_override, error):
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_document",
        fixture_id="fixture-invalid",
        source_summary="Contract review needed before signature.",
    )
    registry = suggestion_registry()

    invalid = (
        opportunity_override
        if opportunity_override is SENTINEL_OPPORTUNITY_OBJECT
        else unsafe_replace_opportunity(opportunity, **opportunity_override)
    )

    with pytest.raises((ValueError, TypeError), match=error):
        render_proactive_telegram_suggestion(
            opportunity_record=invalid,
            source_registry=candidate_registry,
            registry=registry,
            owner_id="owner-120p",
            robot_id="robot-120p",
            chat_id="telegram-chat-120p",
        )


def test_120p_rejects_missing_118p_source_lineage():
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_document",
        fixture_id="fixture-missing-lineage",
        source_summary="Contract review needed before signature.",
    )
    registry = suggestion_registry()
    candidate_registry.candidates_by_id.clear()

    with pytest.raises(ValueError, match="rejected_missing_118p_source_lineage"):
        render_proactive_telegram_suggestion(
            opportunity_record=opportunity,
            source_registry=candidate_registry,
            registry=registry,
            owner_id="owner-120p",
            robot_id="robot-120p",
            chat_id="telegram-chat-120p",
        )


def test_120p_delivery_rejects_invalid_owner_binding_without_live_send():
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_invoice_record",
        fixture_id="fixture-binding",
        source_summary="Payment due soon for monthly retainer invoice.",
    )
    registry = suggestion_registry()
    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )
    transport = FakeTelegramTransport()

    delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=surface,
        owner_binding=binding(owner_id="other-owner"),
        transport=transport,
        registry=registry,
    )

    assert delivery.delivery_status == "rejected_invalid_lineage"
    assert transport.calls == []


def test_120p_surface_text_is_safe_and_concise():
    candidate_registry = source_registry()
    _, _, opportunity = create_opportunity(
        candidate_registry,
        source_type="mock_calendar_event",
        fixture_id="fixture-copy",
        source_title="Investor sync",
        source_summary="Upcoming event with missing brief.",
        source_hint="missing brief and empty briefing note",
        source_timestamp="2026-06-21T08:00:00Z",
    )
    registry = suggestion_registry()
    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=registry,
        owner_id="owner-120p",
        robot_id="robot-120p",
        chat_id="telegram-chat-120p",
    )

    assert "password" not in surface.display_text.lower()
    assert "medical record" not in surface.display_text.lower()
    assert "No action has been taken." in surface.display_text
    assert len(surface.display_text) < 260


def test_120p_module_stays_local_only_and_non_executing():
    text = MODULE_PATH.read_text()

    for blocked_import in ["import requests", "import httpx", "import openai", "import slack_sdk", "subprocess"]:
        assert blocked_import not in text
    for blocked_term in [
        "requests.get(",
        "httpx.get(",
        "openai.",
        "slack_sdk.",
        "bind_telegram",
        "create_followup_intent(",
        "dispatch_worker(",
        "write_approved_memory_proposal_to_memory_center(",
    ]:
        assert blocked_term not in text
