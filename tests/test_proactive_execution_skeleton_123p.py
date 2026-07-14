from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.followup_delegation_authority import FollowUpDelegationRegistry
from app.proactive_execution_skeleton import (
    PROACTIVE_EXECUTION_MODE,
    PROACTIVE_EXECUTION_SKELETON_STAGE,
    ProactiveExecutionFixture,
    ProactiveExecutionRegistry,
    execute_proactive_delegation_skeleton,
    get_proactive_execution_attempt,
    get_proactive_execution_event_candidate,
    list_proactive_execution_attempts,
    list_proactive_execution_event_candidates,
)
from app.proactive_delegation_adapter import ProactiveDelegationAdapterRecord
from tests.test_proactive_delegation_adapter_122p import (
    approved_async_delegation_packet,
    authorize_proactive_delegation_registration_local,
    budget_policy,
    delegation_adapter_registry,
    followup_registry,
    make_selection,
    proactive_flow,
    register_proactive_delegation_from_existing_selection,
    synthetic_preflight,
    task_cost_request,
    unsafe_replace_record,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/proactive_execution_skeleton.py"


def execution_registry() -> ProactiveExecutionRegistry:
    return ProactiveExecutionRegistry()


def execution_fixture(
    *,
    allowed_task_classes: tuple[str, ...] = (
        "FOLLOWUP_DEEPER_SUMMARY",
        "FOLLOWUP_EXTRACT_QUESTIONS",
        "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        "FOLLOWUP_COMPARE_PRIOR_VERSION",
    ),
    deterministic_payloads: dict[str, str] | None = None,
    compare_prior_version_fixture_ids: tuple[str, ...] = (),
) -> ProactiveExecutionFixture:
    return ProactiveExecutionFixture(
        fixture_id="fixture-123p-execution",
        owner_id="owner-122p",
        robot_id="robot-122p",
        allowed_task_classes=allowed_task_classes,
        deterministic_payloads={} if deterministic_payloads is None else deterministic_payloads,
        compare_prior_version_fixture_ids=compare_prior_version_fixture_ids,
    )


def build_registered_adapter(
    *,
    source_kwargs: dict[str, object],
    selected_option_kind: str,
    selection_status: str = "selected_pending_authorization",
    option_metadata_overrides: dict[str, object] | None = None,
    require_approval: bool = False,
) -> tuple[ProactiveDelegationAdapterRecord, FollowUpDelegationRegistry]:
    flow = proactive_flow(source_kwargs)
    selection = make_selection(
        followup_intent_record=flow["followup_intent"],
        selected_option_kind=selected_option_kind,
        selection_status=selection_status,
        option_metadata_overrides=option_metadata_overrides,
    )
    adapter_store = delegation_adapter_registry()
    followup_store = followup_registry()
    request = task_cost_request()
    preflight = evaluate_preflight(require_approval=require_approval, task_request=request)
    proactive_auth = authorize_proactive_delegation_registration_local(
        owner_id="owner-122p",
        robot_id="robot-122p",
        chat_id="telegram-chat-122p",
        proactive_adapter_id=flow["adapter"].adapter_id,
        followup_selection_id=selection.selection_id,
        cost_lineage_id=request.request_id,
        registry=adapter_store,
    )
    approval = None
    if require_approval:
        approval = approved_async_delegation_packet(
            selection,
            proactive_auth.authorization_id,
            request,
            budget_policy(),
            preflight,
        )
        proactive_auth = unsafe_replace_record(
            proactive_auth,
            action_approval_evidence_id=approval.packet.packet_id,
        )
    adapter = register_proactive_delegation_from_existing_selection(
        proactive_adapter_record=flow["adapter"],
        selection_record=selection,
        delegation_authorization_record=proactive_auth,
        cost_preflight_evidence=preflight,
        task_cost_request=request,
        budget_policy=budget_policy(),
        adapter_registry=adapter_store,
        followup_registry=followup_store,
        approval_evidence=approval,
        occurred_at="2026-06-20T12:00:00Z",
    )
    return adapter, followup_store


def evaluate_preflight(*, require_approval: bool, task_request):
    if require_approval:
        from app.cost_governor import evaluate_cost_preflight

        return evaluate_cost_preflight(request=task_request, budget_policy=budget_policy())
    return synthetic_preflight(task_request)


@pytest.mark.parametrize(
    ("source_kwargs", "option_kind", "expected_task_class"),
    [
        (
            {
                "source_type": "mock_message_thread",
                "fixture_id": "fixture-message",
                "source_title": "Support thread",
                "source_summary": "Customer complaint escalation with refund request.",
            },
            "deeper_summary",
            "FOLLOWUP_DEEPER_SUMMARY",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-proposal",
                "source_title": "Proposal sent to ACME",
                "source_summary": "Proposal sent with no response for 10 days.",
            },
            "extract_questions",
            "FOLLOWUP_EXTRACT_QUESTIONS",
        ),
        (
            {
                "source_type": "mock_document",
                "fixture_id": "fixture-document",
                "source_title": "NDA draft",
                "source_summary": "Contract review needed before signature.",
            },
            "human_review_checklist",
            "FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
        ),
    ],
)
def test_123p_valid_registered_adapter_creates_completion_candidate(source_kwargs, option_kind, expected_task_class):
    adapter, followup_store = build_registered_adapter(
        source_kwargs=source_kwargs,
        selected_option_kind=option_kind,
    )
    registry = execution_registry()
    fixture = execution_fixture()

    attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=fixture,
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )

    assert attempt.attempt_status == "completed_candidate_created"
    assert attempt.mapped_task_class == expected_task_class
    assert attempt.owner_id == adapter.owner_id
    assert attempt.robot_id == adapter.robot_id
    assert attempt.chat_id == adapter.chat_id
    assert attempt.delegation_packet_id == adapter.delegation_packet_id
    assert attempt.delegation_handle_id == adapter.delegation_handle_id
    assert attempt.completion_event_candidate_id is not None
    assert attempt.failure_event_candidate_id is None
    assert attempt.result_summary is not None
    assert attempt.failure_reason is None
    assert attempt.execution_stage == PROACTIVE_EXECUTION_SKELETON_STAGE
    assert attempt.execution_mode == PROACTIVE_EXECUTION_MODE
    assert attempt.inbox_insert_allowed is False
    assert attempt.result_surface_allowed is False
    assert attempt.telegram_delivery_allowed is False
    assert attempt.worker_dispatch_allowed is False
    assert attempt.model_call_allowed is False
    assert attempt.tool_call_allowed is False
    assert attempt.live_connector_allowed is False
    assert attempt.external_write_allowed is False
    assert attempt.memory_write_allowed is False
    event = get_proactive_execution_event_candidate(
        execution_registry=registry,
        event_candidate_id=attempt.completion_event_candidate_id,
    )
    assert event is not None
    assert event.event_type == "proactive_execution_completed"
    assert event.event_status == "completed"
    assert event.owner_id == adapter.owner_id
    assert event.robot_id == adapter.robot_id
    assert event.delegation_packet_id == adapter.delegation_packet_id
    assert event.delegation_handle_id == adapter.delegation_handle_id
    assert event.compatible_with_async_completion_event_shape is True
    assert event.inbox_inserted is False
    assert event.result_surface_created is False
    assert event.telegram_delivered is False
    assert event.memory_mutated is False
    assert event.external_written is False
    async_event = event.result_payload["async_completion_event"]
    assert async_event.completion_status == "completed"
    assert async_event.source_stage == "123P"


def test_123p_compare_prior_version_without_fixture_creates_failure_candidate():
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        },
        selected_option_kind="deeper_summary",
    )
    option_id = "option-compare-prior-version"
    adapter = unsafe_replace_record(
        adapter,
        selected_option_id=option_id,
        mapped_task_class="FOLLOWUP_COMPARE_PRIOR_VERSION",
        lineage_summary={
            **adapter.lineage_summary,
            "upstream_lineage": {
                **adapter.lineage_summary["upstream_lineage"],
                "selection": {
                    **adapter.lineage_summary["upstream_lineage"]["selection"],
                    "upstream_lineage": {
                        **adapter.lineage_summary["upstream_lineage"]["selection"]["upstream_lineage"],
                        "option_metadata_by_ref": {
                            **adapter.lineage_summary["upstream_lineage"]["selection"]["upstream_lineage"][
                                "option_metadata_by_ref"
                            ],
                            option_id: {"prior_version_fixture_id": "prior-fixture-123p"},
                        },
                    },
                },
            },
        },
    )
    followup_record = next(iter(followup_store.records_by_id.values()))
    followup_store.records_by_id[followup_record.followup_delegation_id] = replace(
        followup_record,
        selected_option_id=option_id,
        selected_option_kind="compare_prior_version",
        followup_task_class="FOLLOWUP_COMPARE_PRIOR_VERSION",
    )
    registry = execution_registry()

    attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=execution_fixture(compare_prior_version_fixture_ids=()),
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )

    assert attempt.attempt_status == "failure_candidate_created"
    assert attempt.completion_event_candidate_id is None
    assert attempt.failure_event_candidate_id is not None
    assert attempt.failure_reason == "missing_local_prior_version_fixture"
    event = get_proactive_execution_event_candidate(
        execution_registry=registry,
        event_candidate_id=attempt.failure_event_candidate_id,
    )
    assert event is not None
    assert event.event_type == "proactive_execution_failed"
    assert event.event_status == "failed"
    assert event.failure_reason == "missing_local_prior_version_fixture"
    assert event.retry_allowed is False
    async_event = event.result_payload["async_completion_event"]
    assert async_event.completion_status == "failed"
    assert async_event.reason_code == "failed_local_prior_version_unavailable"


def test_123p_preserves_100p_101p_102p_and_118p_to_122p_lineage():
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        },
        selected_option_kind="deeper_summary",
        selection_status="explicitly_authorized_for_proactive_delegation",
        require_approval=True,
    )
    registry = execution_registry()
    attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=execution_fixture(),
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )

    lineage = attempt.lineage_summary
    assert lineage["async_authority_stage"] == "102P"
    assert lineage["followup_delegation_stage"] == "111P"
    upstream = lineage["upstream_lineage"]["proactive_delegation_adapter"]
    assert upstream["source_stage"] == "118P"
    assert upstream["detection_stage"] == "119P"
    assert upstream["suggestion_stage"] == "120P"
    assert upstream["adapter_stage"] == "121P"
    assert upstream["delegation_adapter_stage"] == "122P"
    followup_lineage = lineage["upstream_lineage"]["followup_delegation"]
    assert followup_lineage["cost_preflight_stage"] == "100P"
    assert followup_lineage["approval_stage"] == "101P"
    assert followup_lineage["async_delegation_stage"] == "102P"
    assert followup_lineage["selection_stage"] == "110P"
    assert followup_lineage["choice_surface_stage"] == "109P"
    assert followup_lineage["draft_planner_stage"] == "108P"
    assert followup_lineage["followup_stage"] == "107P"


def test_123p_missing_or_invalid_sources_are_rejected():
    registry = execution_registry()
    fixture = execution_fixture()
    followup_store = followup_registry()

    unknown = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=object(),
        followup_registry=followup_store,
        fixture=fixture,
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )
    assert unknown.attempt_status == "rejected_invalid_lineage"

    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        },
        selected_option_kind="human_review_checklist",
    )
    bad_stage = unsafe_replace_record(adapter, delegation_adapter_stage="999P")
    missing_packet = unsafe_replace_record(adapter, delegation_packet_id=None)
    missing_handle = unsafe_replace_record(adapter, delegation_handle_id=None)
    missing_auth = unsafe_replace_record(adapter, explicit_owner_delegation_authorization_id="")
    rejected_status = unsafe_replace_record(adapter, adapter_status="rejected_invalid_lineage")

    for candidate in (bad_stage, missing_packet, missing_handle, missing_auth, rejected_status):
        attempt = execute_proactive_delegation_skeleton(
            proactive_delegation_adapter_record=candidate,
            followup_registry=followup_store,
            fixture=fixture,
            execution_registry=registry,
            created_at="2026-06-20T13:00:00Z",
        )
        assert attempt.attempt_status == "rejected_invalid_lineage"


@pytest.mark.parametrize(
    ("adapter_overrides", "expected_status"),
    [
        ({"mapped_task_class": "UNSUPPORTED_TASK"}, "rejected_unsupported_task_class"),
        ({"owner_id": "other-owner"}, "rejected_invalid_lineage"),
        ({"robot_id": "other-robot"}, "rejected_invalid_lineage"),
        ({"chat_id": "other-chat"}, "rejected_invalid_lineage"),
        ({"live_connector_allowed": True}, "rejected_live_dependency"),
        ({"model_call_allowed": True}, "rejected_live_dependency"),
        ({"tool_call_allowed": True}, "rejected_live_dependency"),
        ({"external_write_allowed": True}, "rejected_live_dependency"),
    ],
)
def test_123p_direct_adapter_mismatches_are_rejected(adapter_overrides, expected_status):
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        },
        selected_option_kind="human_review_checklist",
    )
    registry = execution_registry()
    candidate = unsafe_replace_record(adapter, **adapter_overrides)

    attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=candidate,
        followup_registry=followup_store,
        fixture=execution_fixture(),
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )

    assert attempt.attempt_status == expected_status


def test_123p_sensitive_and_live_dependency_lineage_are_rejected():
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_document",
            "fixture_id": "fixture-document",
            "source_title": "NDA draft",
            "source_summary": "Contract review needed before signature.",
        },
        selected_option_kind="human_review_checklist",
    )
    sensitive = unsafe_replace_record(
        adapter,
        lineage_summary={
            **adapter.lineage_summary,
            "upstream_lineage": {
                **adapter.lineage_summary["upstream_lineage"],
                "proactive_adapter": {
                    **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"],
                    "upstream_lineage": {
                        **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"]["upstream_lineage"],
                        "opportunity": {
                            **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"]["upstream_lineage"]["opportunity"],
                            "sensitive_data_blocked": True,
                        },
                    },
                },
            },
        },
    )
    live = unsafe_replace_record(
        adapter,
        lineage_summary={
            **adapter.lineage_summary,
            "upstream_lineage": {
                **adapter.lineage_summary["upstream_lineage"],
                "proactive_adapter": {
                    **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"],
                    "upstream_lineage": {
                        **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"]["upstream_lineage"],
                        "opportunity": {
                            **adapter.lineage_summary["upstream_lineage"]["proactive_adapter"]["upstream_lineage"]["opportunity"],
                            "model_calls_required": True,
                        },
                    },
                },
            },
        },
    )

    sensitive_attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=sensitive,
        followup_registry=followup_store,
        fixture=execution_fixture(),
        execution_registry=execution_registry(),
        created_at="2026-06-20T13:00:00Z",
    )
    live_attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=live,
        followup_registry=followup_store,
        fixture=execution_fixture(),
        execution_registry=execution_registry(),
        created_at="2026-06-20T13:00:00Z",
    )

    assert sensitive_attempt.attempt_status == "rejected_sensitive_data"
    assert live_attempt.attempt_status == "rejected_live_dependency"


def test_123p_duplicate_execution_attempt_returns_existing_record():
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        },
        selected_option_kind="deeper_summary",
    )
    registry = execution_registry()
    fixture = execution_fixture()

    first = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=fixture,
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )
    second = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=fixture,
        execution_registry=registry,
        created_at="2026-06-20T13:05:00Z",
    )

    assert second.proactive_execution_attempt_id == first.proactive_execution_attempt_id
    assert len(list_proactive_execution_attempts(execution_registry=registry)) == 1
    assert len(list_proactive_execution_event_candidates(execution_registry=registry)) == 1


def test_123p_getters_and_listing_helpers_return_records():
    adapter, followup_store = build_registered_adapter(
        source_kwargs={
            "source_type": "mock_message_thread",
            "fixture_id": "fixture-message",
            "source_title": "Support thread",
            "source_summary": "Customer complaint escalation with refund request.",
        },
        selected_option_kind="deeper_summary",
    )
    registry = execution_registry()
    attempt = execute_proactive_delegation_skeleton(
        proactive_delegation_adapter_record=adapter,
        followup_registry=followup_store,
        fixture=execution_fixture(),
        execution_registry=registry,
        created_at="2026-06-20T13:00:00Z",
    )
    assert get_proactive_execution_attempt(
        execution_registry=registry,
        proactive_execution_attempt_id=attempt.proactive_execution_attempt_id,
    ) == attempt
    assert list_proactive_execution_attempts(execution_registry=registry) == (attempt,)
    assert attempt.completion_event_candidate_id is not None
    event = get_proactive_execution_event_candidate(
        execution_registry=registry,
        event_candidate_id=attempt.completion_event_candidate_id,
    )
    assert event is not None
    assert list_proactive_execution_event_candidates(execution_registry=registry) == (event,)
    assert MODULE_PATH.is_file()
