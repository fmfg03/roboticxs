from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.followup_memory_proposal import (
    FOLLOWUP_MEMORY_PROPOSAL_STAGE,
    FollowUpMemoryProposalRegistry,
    create_followup_memory_proposal_candidate,
    get_followup_memory_proposal_candidate,
    list_followup_memory_proposal_candidates,
)
from app.followup_result_acknowledgement import (
    FollowUpResultAcknowledgementRegistry,
    bind_followup_result_acknowledgement,
)
from tests.test_followup_completion_loop_113p import FollowUpCompletionLoopRegistry, routed_completion
from tests.test_followup_result_acknowledgement_114p import callback_payload


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = REPO_ROOT / "app/followup_memory_proposal.py"


def routed_acknowledgement(*, action: str = "acknowledge_followup_result", delivery_text: str | None = None):
    route_registry = FollowUpCompletionLoopRegistry()
    route = routed_completion(route_registry=route_registry)
    delivery = route_registry.delivery_registry.get_delivery(route.delivery_record_id)
    assert delivery is not None
    if delivery_text is not None:
        route_registry.delivery_registry.store(replace(delivery, text=delivery_text))
        delivery = route_registry.delivery_registry.get_delivery(route.delivery_record_id)
        assert delivery is not None
    acknowledgement = bind_followup_result_acknowledgement(
        route_registry=route_registry,
        callback_payload=callback_payload(route, delivery, action=action),
        registry=FollowUpResultAcknowledgementRegistry(),
    )
    return route, delivery, route_registry, acknowledgement


def test_115p_valid_owner_acknowledgement_creates_pending_local_memory_proposal_candidate():
    route, delivery, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Checklist for contract review next step."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.status == "pending_user_review"
    assert record.proposal_type == "task_memory_candidate"
    assert record.source_stage == "114P"
    assert record.proposal_stage == FOLLOWUP_MEMORY_PROPOSAL_STAGE
    assert record.memory_write_allowed is False
    assert record.telegram_approval_surface_allowed is False
    assert record.memory_center_mutated is False
    assert record.live_send_allowed is False
    assert record.acknowledgement_id == acknowledgement.acknowledgement_id
    assert record.route_id == route.route_id
    assert record.delivery_record_id == delivery.delivery_id


def test_115p_dismissed_followup_result_cannot_create_memory_proposal_candidate():
    _, _, route_registry, acknowledgement = routed_acknowledgement(action="dismiss_followup_result")

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.status == "rejected_source"
    assert record.rejection_reason == "rejected_dismissed_acknowledgement_source"


def test_115p_lineage_summary_only_acknowledgement_cannot_create_memory_proposal_candidate():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        action="request_followup_result_lineage_summary"
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.status == "rejected_source"
    assert record.rejection_reason == "rejected_lineage_summary_only_acknowledgement_source"


def test_115p_unknown_acknowledgement_record_is_rejected():
    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=object(),
        route_registry=FollowUpCompletionLoopRegistry(),
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.status == "rejected_source"
    assert record.rejection_reason == "rejected_unknown_114p_acknowledgement_record"


def test_115p_acknowledgement_not_linked_to_113p_route_is_rejected():
    _, _, _, acknowledgement = routed_acknowledgement()

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=FollowUpCompletionLoopRegistry(),
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.status == "rejected_source"
    assert record.rejection_reason == "rejected_unknown_113p_route"


def test_115p_wrong_owner_is_rejected():
    _, _, route_registry, acknowledgement = routed_acknowledgement()
    tampered = replace(acknowledgement, owner_id="other-owner")

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=tampered,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.rejection_reason == "rejected_owner_mismatch"


def test_115p_wrong_robot_is_rejected():
    _, _, route_registry, acknowledgement = routed_acknowledgement()
    tampered = replace(acknowledgement, robot_id="other-robot")

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=tampered,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.rejection_reason == "rejected_robot_mismatch"


def test_115p_mismatched_lineage_is_rejected():
    _, _, route_registry, acknowledgement = routed_acknowledgement()

    route_mismatch = create_followup_memory_proposal_candidate(
        acknowledgement_record=replace(acknowledgement, route_id="other-route"),
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )
    surface_mismatch = create_followup_memory_proposal_candidate(
        acknowledgement_record=replace(acknowledgement, surface_id="other-surface"),
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )
    event_mismatch = create_followup_memory_proposal_candidate(
        acknowledgement_record=replace(acknowledgement, event_candidate_id="other-event"),
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )
    packet_mismatch = create_followup_memory_proposal_candidate(
        acknowledgement_record=replace(acknowledgement, packet_id="other-packet"),
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )
    handle_mismatch = create_followup_memory_proposal_candidate(
        acknowledgement_record=replace(acknowledgement, handle_id="other-handle"),
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert route_mismatch.rejection_reason == "rejected_unknown_113p_route"
    assert surface_mismatch.rejection_reason == "rejected_surface_lineage_mismatch"
    assert event_mismatch.rejection_reason == "rejected_event_candidate_lineage_mismatch"
    assert packet_mismatch.rejection_reason == "rejected_packet_lineage_mismatch"
    assert handle_mismatch.rejection_reason == "rejected_handle_lineage_mismatch"


def test_115p_duplicate_creation_is_deduplicated():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Client contract review summary."
    )
    registry = FollowUpMemoryProposalRegistry()

    first = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=registry,
    )
    second = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=registry,
    )

    assert first == second
    assert len(list_followup_memory_proposal_candidates(proposal_registry=registry)) == 1
    assert get_followup_memory_proposal_candidate(
        proposal_registry=registry,
        proposal_id=first.proposal_id,
    ) == first


def test_115p_proposal_preserves_100p_101p_102p_111p_112p_113p_114p_lineage():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Client contract review summary."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.lineage_summary["cost_preflight_summary"]["route_decision"]["selected_model_id"] == "balanced_standard_v1"
    assert record.lineage_summary["task_cost_request_summary"]["request_id"] == "cost-request-112p"
    assert record.lineage_summary["followup_delegation_stage"] == "111P"
    assert record.lineage_summary["followup_execution_stage"] == "112P"
    assert record.lineage_summary["followup_completion_loop_stage"] == "113P"
    assert record.lineage_summary["acknowledgement_stage"] == "114P"
    assert record.lineage_summary["acknowledgement_lineage"]["callback_action"] == "acknowledge_followup_result"
    assert record.lineage_summary["async_authority_state"]["packet"]["delegation_id"] == record.delegation_id


def test_115p_safe_task_memory_candidate_can_be_produced():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Checklist for NDA review next step."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "task_memory_candidate"
    assert record.status == "pending_user_review"
    assert record.proposed_memory_text is not None


def test_115p_safe_work_preference_candidate_can_be_produced():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Prefer checklist format for review work."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "work_preference_candidate"
    assert record.status == "pending_user_review"


def test_115p_safe_business_context_candidate_can_be_produced():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Client NDA requires manual review before signing."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "business_context_candidate"
    assert record.status == "pending_user_review"


def test_115p_safe_boundary_memory_candidate_can_be_produced():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Ask before sending external messages."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "boundary_memory_candidate"
    assert record.status == "pending_user_review"


def test_115p_non_useful_result_produces_no_memory_candidate():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Fixture deeper summary."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "no_memory_candidate"
    assert record.status == "no_memory_recommended"
    assert record.proposed_memory_text is None


def test_115p_sensitive_personal_attribute_is_downgraded_to_no_memory_candidate():
    _, _, route_registry, acknowledgement = routed_acknowledgement(
        delivery_text="Health status update for the owner."
    )

    record = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )

    assert record.proposal_type == "no_memory_candidate"
    assert record.status == "no_memory_recommended"
    assert record.sensitive_data_blocked is True


def test_115p_candidate_stays_local_without_memory_or_telegram_side_effects():
    text = PROPOSAL_PATH.read_text()

    for forbidden in [
        "MemoryCenterItem(",
        "MemoryItem(",
        "send_message",
        "telegram.Bot",
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "delegate_task",
        "register_async_delegation_handle",
    ]:
        assert forbidden not in text


def test_115p_116p_plus_remains_unauthorized():
    roadmap = (REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md").read_text()

    assert "117P and later remain unauthorized" in roadmap or "117P+ remains unauthorized" in roadmap
