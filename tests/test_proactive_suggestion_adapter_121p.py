from __future__ import annotations

from pathlib import Path

import pytest

from app.context_scan_candidate_source import ContextScanCandidateSourceRegistry, create_context_scan_candidate_source, create_local_context_scan_authorization
from app.followup_intent_review import FollowUpIntentReviewQueue
from app.proactive_opportunity_detection import ProactiveOpportunityRegistry, detect_proactive_opportunity_from_context_source
from app.proactive_suggestion_adapter import (
    AUTHORIZATION_KIND,
    PROACTIVE_SUGGESTION_ADAPTER_STAGE,
    ProactiveSuggestionAdapterRegistry,
    authorize_proactive_suggestion_adapter_local,
    adapt_proactive_suggestion_to_followup_intent,
    get_proactive_suggestion_adapter_record,
    list_proactive_suggestion_adapter_records,
)
from app.proactive_telegram_suggestion import (
    ProactiveTelegramSuggestionRegistry,
    deliver_proactive_telegram_suggestion_local,
    render_proactive_telegram_suggestion,
)
from app.telegram_async_result_delivery import TelegramOwnerBinding


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_suggestion_adapter.py"

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
SENTINEL_DELIVERY_OBJECT = object()


class FakeTelegramTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[str, ...]]] = []

    def deliver(self, chat_id: str, text: str, buttons: tuple[str, ...]) -> dict[str, object]:
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


def adapter_registry() -> ProactiveSuggestionAdapterRegistry:
    return ProactiveSuggestionAdapterRegistry()


def followup_queue() -> FollowUpIntentReviewQueue:
    return FollowUpIntentReviewQueue()


def create_auth(registry: ContextScanCandidateSourceRegistry, **overrides):
    values = {
        "owner_id": "owner-121p",
        "robot_id": "robot-121p",
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "allowed_scan_scopes": DEFAULT_SCOPES,
    }
    values.update(overrides)
    return create_local_context_scan_authorization(registry=registry, **values)


def create_source(registry: ContextScanCandidateSourceRegistry, authorization_id: str, **overrides):
    values = {
        "owner_id": "owner-121p",
        "robot_id": "robot-121p",
        "authorization_id": authorization_id,
        "source_type": "mock_document",
        "source_status": "authorized_local_fixture",
        "scan_scope": "summary_fixture",
        "fixture_id": "fixture-121p-default",
        "source_title": "Default source",
        "source_summary": "Default safe fixture summary.",
        "source_timestamp": "2026-06-20T08:00:00Z",
        "source_hint": "local-only fixture",
        "provenance_notes": "safe fixture summary only",
        "retention_policy": "keep_until_fixture_rotation",
    }
    values.update(overrides)
    return create_context_scan_candidate_source(registry=registry, **values)


def binding(**overrides) -> TelegramOwnerBinding:
    values = {
        "owner_id": "owner-121p",
        "robot_id": "robot-121p",
        "telegram_chat_id": "telegram-chat-121p",
    }
    values.update(overrides)
    return TelegramOwnerBinding(**values)


def unsafe_replace_record(record, **overrides):
    values = {field: getattr(record, field) for field in record.__dataclass_fields__}
    values.update(overrides)
    unsafe = object.__new__(record.__class__)
    for field_name, value in values.items():
        object.__setattr__(unsafe, field_name, value)
    return unsafe


def create_delivery_flow(source_overrides: dict[str, object]):
    candidate_registry = source_registry()
    opportunity_store = opportunity_registry()
    suggestion_store = suggestion_registry()
    adapter_store = adapter_registry()
    queue = followup_queue()
    auth = create_auth(candidate_registry)
    source = create_source(candidate_registry, auth.authorization_id, **source_overrides)
    opportunity = detect_proactive_opportunity_from_context_source(
        source_record=source,
        source_registry=candidate_registry,
        registry=opportunity_store,
        owner_id="owner-121p",
        robot_id="robot-121p",
    )
    surface = render_proactive_telegram_suggestion(
        opportunity_record=opportunity,
        source_registry=candidate_registry,
        registry=suggestion_store,
        owner_id="owner-121p",
        robot_id="robot-121p",
        chat_id="telegram-chat-121p",
    )
    delivery = deliver_proactive_telegram_suggestion_local(
        surface_record=surface,
        owner_binding=binding(),
        transport=FakeTelegramTransport(),
        registry=suggestion_store,
    )
    authorization = authorize_proactive_suggestion_adapter_local(
        owner_id="owner-121p",
        robot_id="robot-121p",
        chat_id="telegram-chat-121p",
        delivery_record_id=delivery.delivery_record_id,
        suggestion_surface_id=surface.suggestion_surface_id,
        opportunity_id=opportunity.opportunity_id,
        registry=adapter_store,
    )
    return {
        "candidate_registry": candidate_registry,
        "suggestion_registry": suggestion_store,
        "adapter_registry": adapter_store,
        "queue": queue,
        "authorization": authorization,
        "context_authorization": auth,
        "source": source,
        "opportunity": opportunity,
        "surface": surface,
        "delivery": delivery,
    }


@pytest.mark.parametrize(
    ("source_kwargs", "expected_type", "expected_intent"),
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
            "prepare_meeting_brief",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-document",
                "source_title": "NDA draft",
                "source_summary": "Contract review needed before signature.",
            },
            "document_review_needed",
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
            "prepare_checklist",
        ),
        (
            {
                "source_type": "mock_message_thread",
                "fixture_id": "fixture-message",
                "source_title": "Support thread",
                "source_summary": "Customer complaint escalation with refund request.",
            },
            "customer_issue_needs_attention",
            "summarize_context",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-proposal",
                "source_title": "Proposal sent to ACME",
                "source_summary": "Proposal sent with no response for 10 days.",
            },
            "stale_proposal_followup",
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
            "review_memory_gap",
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
            "review_boundary",
        ),
    ],
)
def test_121p_valid_delivered_suggestion_adapts_to_followup_intent(source_kwargs, expected_type, expected_intent):
    flow = create_delivery_flow(source_kwargs)

    adapter = adapt_proactive_suggestion_to_followup_intent(
        delivery_record=flow["delivery"],
        suggestion_registry=flow["suggestion_registry"],
        opportunity_record=flow["opportunity"],
        source_registry=flow["candidate_registry"],
        queue=flow["queue"],
        adapter_registry=flow["adapter_registry"],
        authorization_record=flow["authorization"],
        owner_id="owner-121p",
        robot_id="robot-121p",
    )

    followup_record = flow["queue"].get_record(adapter.followup_intent_review_record_id)

    assert adapter.adapter_stage == PROACTIVE_SUGGESTION_ADAPTER_STAGE
    assert adapter.adapter_status == "adapted_to_followup_intent"
    assert adapter.owner_id == "owner-121p"
    assert adapter.robot_id == "robot-121p"
    assert adapter.chat_id == "telegram-chat-121p"
    assert adapter.delivery_record_id == flow["delivery"].delivery_record_id
    assert adapter.suggestion_surface_id == flow["surface"].suggestion_surface_id
    assert adapter.opportunity_id == flow["opportunity"].opportunity_id
    assert adapter.candidate_source_id == flow["source"].candidate_source_id
    assert adapter.authorization_id == flow["context_authorization"].authorization_id
    assert adapter.opportunity_type == expected_type
    assert adapter.normalized_intent_kind == expected_intent
    assert adapter.planner_called is False
    assert adapter.choice_surface_created is False
    assert adapter.selection_bound is False
    assert adapter.delegation_created is False
    assert adapter.execution_allowed is False
    assert adapter.telegram_send_allowed is False
    assert adapter.memory_write_allowed is False
    assert adapter.external_write_allowed is False
    assert adapter.worker_dispatch_allowed is False
    assert adapter.live_connector_allowed is False
    assert adapter.lineage_summary["source_kind"] == "proactive_suggestion"
    assert adapter.lineage_summary["source_stage"] == "120P"
    assert adapter.lineage_summary["adapter_stage"] == "121P"

    assert followup_record is not None
    assert followup_record.acknowledgement_id == flow["authorization"].authorization_id
    assert followup_record.delivery_id == flow["delivery"].delivery_record_id
    assert followup_record.surface_id == flow["surface"].suggestion_surface_id
    assert followup_record.owner_id == "owner-121p"
    assert followup_record.robot_id == "robot-121p"
    assert followup_record.telegram_chat_id == "telegram-chat-121p"
    assert followup_record.status == "pending_review"
    assert followup_record.lineage_summary["source_kind"] == "proactive_suggestion"
    assert followup_record.lineage_summary["adapter_stage"] == "121P"
    assert followup_record.lineage_summary["planner_called"] is False
    assert followup_record.lineage_summary["delegation_created"] is False
    assert followup_record.lineage_summary["execution_allowed"] is False
    assert followup_record.lineage_summary["normalized_intent_kind"] == expected_intent
    assert "No planner" in followup_record.review_summary


def test_121p_duplicate_adaptation_is_dedupe_safe():
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-dedupe",
            "source_summary": "Contract review needed before signature.",
        }
    )

    first = adapt_proactive_suggestion_to_followup_intent(
        delivery_record=flow["delivery"],
        suggestion_registry=flow["suggestion_registry"],
        opportunity_record=flow["opportunity"],
        source_registry=flow["candidate_registry"],
        queue=flow["queue"],
        adapter_registry=flow["adapter_registry"],
        authorization_record=flow["authorization"],
        owner_id="owner-121p",
        robot_id="robot-121p",
    )
    second = adapt_proactive_suggestion_to_followup_intent(
        delivery_record=flow["delivery"],
        suggestion_registry=flow["suggestion_registry"],
        opportunity_record=flow["opportunity"],
        source_registry=flow["candidate_registry"],
        queue=flow["queue"],
        adapter_registry=flow["adapter_registry"],
        authorization_record=flow["authorization"],
        owner_id="owner-121p",
        robot_id="robot-121p",
    )

    assert first == second
    assert get_proactive_suggestion_adapter_record(adapter_registry=flow["adapter_registry"], adapter_id=first.adapter_id) == first
    assert list_proactive_suggestion_adapter_records(adapter_registry=flow["adapter_registry"]) == (first,)
    assert len(flow["queue"].list_records()) == 1


@pytest.mark.parametrize(
    ("authorization_override", "error"),
    [
        (None, "rejected_missing_owner_authorization"),
        ({"owner_id": "other-owner"}, "rejected_non_owner_authorization"),
        ({"robot_id": "other-robot"}, "rejected_robot_mismatch"),
        ({"chat_id": "other-chat"}, "rejected_chat_mismatch"),
        ({"authorization_kind": "other"}, "rejected_invalid_lineage"),
        ({"authorization_stage": "120P"}, "rejected_invalid_lineage"),
    ],
)
def test_121p_rejects_missing_or_invalid_explicit_owner_authorization(authorization_override, error):
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-auth",
            "source_summary": "Contract review needed before signature.",
        }
    )
    authorization = (
        None if authorization_override is None else unsafe_replace_record(flow["authorization"], **authorization_override)
    )

    with pytest.raises(ValueError, match=error):
        adapt_proactive_suggestion_to_followup_intent(
            delivery_record=flow["delivery"],
            suggestion_registry=flow["suggestion_registry"],
            opportunity_record=flow["opportunity"],
            source_registry=flow["candidate_registry"],
            queue=flow["queue"],
            adapter_registry=flow["adapter_registry"],
            authorization_record=authorization,
            owner_id="owner-121p",
            robot_id="robot-121p",
        )


@pytest.mark.parametrize(
    ("delivery_override", "error"),
    [
        (SENTINEL_DELIVERY_OBJECT, "rejected_unknown_delivery_record"),
        ({"delivery_stage": "119P"}, "rejected_invalid_lineage"),
        ({"owner_id": "other-owner"}, "rejected_owner_mismatch"),
        ({"robot_id": "other-robot"}, "rejected_robot_mismatch"),
        ({"delivery_mode": "live_telegram_api"}, "rejected_invalid_lineage"),
        ({"delivery_status": "rejected_invalid_lineage"}, "rejected_invalid_lineage"),
        ({"callback_binding_allowed": True}, "rejected_invalid_lineage"),
    ],
)
def test_121p_rejects_invalid_delivery_lineage(delivery_override, error):
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-delivery-lineage",
            "source_summary": "Contract review needed before signature.",
        }
    )
    invalid = delivery_override if delivery_override is SENTINEL_DELIVERY_OBJECT else unsafe_replace_record(flow["delivery"], **delivery_override)

    with pytest.raises((TypeError, ValueError), match=error):
        adapt_proactive_suggestion_to_followup_intent(
            delivery_record=invalid,
            suggestion_registry=flow["suggestion_registry"],
            opportunity_record=flow["opportunity"],
            source_registry=flow["candidate_registry"],
            queue=flow["queue"],
            adapter_registry=flow["adapter_registry"],
            authorization_record=flow["authorization"],
            owner_id="owner-121p",
            robot_id="robot-121p",
        )


def test_121p_rejects_missing_120p_surface_lineage():
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-surface-lineage",
            "source_summary": "Contract review needed before signature.",
        }
    )
    flow["suggestion_registry"].surfaces_by_id.clear()

    with pytest.raises(ValueError, match="rejected_invalid_lineage"):
        adapt_proactive_suggestion_to_followup_intent(
            delivery_record=flow["delivery"],
            suggestion_registry=flow["suggestion_registry"],
            opportunity_record=flow["opportunity"],
            source_registry=flow["candidate_registry"],
            queue=flow["queue"],
            adapter_registry=flow["adapter_registry"],
            authorization_record=flow["authorization"],
            owner_id="owner-121p",
            robot_id="robot-121p",
        )


@pytest.mark.parametrize(
    ("opportunity_override", "error"),
    [
        ({"detection_stage": "118P"}, "rejected_invalid_lineage"),
        ({"source_stage": "117P"}, "rejected_invalid_lineage"),
        ({"owner_id": "other-owner"}, "rejected_owner_mismatch"),
        ({"robot_id": "other-robot"}, "rejected_robot_mismatch"),
        ({"opportunity_type": "no_opportunity"}, "rejected_no_opportunity"),
        ({"sensitive_data_blocked": True}, "rejected_sensitive_data"),
        ({"live_connector_allowed": True}, "rejected_invalid_lineage"),
        ({"execution_allowed": True}, "rejected_invalid_lineage"),
        ({"memory_write_allowed": True}, "rejected_invalid_lineage"),
        ({"external_write_allowed": True}, "rejected_invalid_lineage"),
        ({"lineage_summary": {"model_calls_required": True}}, "rejected_invalid_lineage"),
        ({"lineage_summary": {"tool_calls_required": True}}, "rejected_invalid_lineage"),
    ],
)
def test_121p_rejects_invalid_opportunity_lineage(opportunity_override, error):
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-opportunity-lineage",
            "source_summary": "Contract review needed before signature.",
        }
    )
    invalid = unsafe_replace_record(flow["opportunity"], **opportunity_override)

    with pytest.raises(ValueError, match=error):
        adapt_proactive_suggestion_to_followup_intent(
            delivery_record=flow["delivery"],
            suggestion_registry=flow["suggestion_registry"],
            opportunity_record=invalid,
            source_registry=flow["candidate_registry"],
            queue=flow["queue"],
            adapter_registry=flow["adapter_registry"],
            authorization_record=flow["authorization"],
            owner_id="owner-121p",
            robot_id="robot-121p",
        )


def test_121p_rejects_missing_118p_source_lineage():
    flow = create_delivery_flow(
        {
            "source_type": "mock_document",
            "fixture_id": "fixture-source-lineage",
            "source_summary": "Contract review needed before signature.",
        }
    )
    flow["candidate_registry"].candidates_by_id.clear()

    with pytest.raises(ValueError, match="rejected_invalid_lineage"):
        adapt_proactive_suggestion_to_followup_intent(
            delivery_record=flow["delivery"],
            suggestion_registry=flow["suggestion_registry"],
            opportunity_record=flow["opportunity"],
            source_registry=flow["candidate_registry"],
            queue=flow["queue"],
            adapter_registry=flow["adapter_registry"],
            authorization_record=flow["authorization"],
            owner_id="owner-121p",
            robot_id="robot-121p",
        )


def test_121p_module_stays_local_only_and_stops_before_later_stages():
    text = MODULE_PATH.read_text()

    for blocked_import in ["import requests", "import httpx", "import openai", "import slack_sdk", "subprocess"]:
        assert blocked_import not in text
    for blocked_term in [
        "requests.get(",
        "httpx.get(",
        "openai.",
        "create_followup_choice_surface(",
        "bind_followup_choice_selection(",
        "create_followup_delegation(",
        "execute_followup(",
        "write_approved_memory_proposal_to_memory_center(",
        "send_message(",
    ]:
        assert blocked_term not in text


def test_121p_authorization_helper_uses_local_owner_scope_only():
    registry = adapter_registry()

    record = authorize_proactive_suggestion_adapter_local(
        owner_id="owner-121p",
        robot_id="robot-121p",
        chat_id="telegram-chat-121p",
        delivery_record_id="delivery-121p",
        suggestion_surface_id="surface-121p",
        opportunity_id="opportunity-121p",
        registry=registry,
    )

    assert record.authorization_kind == AUTHORIZATION_KIND
    assert record.authorization_stage == "121P"
    assert record.granted_by_owner is True
