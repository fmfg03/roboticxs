from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.telegram_memory_proposal_approval import (
    TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE,
    TelegramMemoryProposalApprovalRegistry,
    TelegramMemoryProposalApprovalSelectionPayload,
    bind_memory_proposal_approval_selection,
    build_memory_proposal_approval_response_envelope,
    get_memory_proposal_approval_decision,
    get_memory_proposal_approval_surface,
    list_memory_proposal_approval_decisions,
    list_memory_proposal_approval_surfaces,
    render_memory_proposal_approval_surface,
)
from tests.test_followup_memory_proposal_115p import routed_acknowledgement
from app.followup_memory_proposal import FollowUpMemoryProposalRegistry, create_followup_memory_proposal_candidate


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = REPO_ROOT / "app/telegram_memory_proposal_approval.py"


def pending_proposal(*, delivery_text: str = "Checklist for NDA review next step."):
    _, _, route_registry, acknowledgement = routed_acknowledgement(delivery_text=delivery_text)
    proposal = create_followup_memory_proposal_candidate(
        acknowledgement_record=acknowledgement,
        route_registry=route_registry,
        proposal_registry=FollowUpMemoryProposalRegistry(),
    )
    return proposal


def render_surface(*, proposal=None, registry=None):
    proposal = pending_proposal() if proposal is None else proposal
    registry = TelegramMemoryProposalApprovalRegistry() if registry is None else registry
    surface = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )
    return proposal, registry, surface


def payload(surface, **overrides) -> TelegramMemoryProposalApprovalSelectionPayload:
    values = {
        "owner_id": surface.owner_id,
        "robot_id": surface.robot_id,
        "chat_id": surface.chat_id,
        "proposal_id": surface.proposal_id,
        "surface_id": surface.surface_id,
        "action": "approve_memory_proposal",
        "revised_proposed_memory_text": None,
    }
    values.update(overrides)
    return TelegramMemoryProposalApprovalSelectionPayload(**values)


def test_116p_valid_pending_115p_memory_proposal_candidate_renders_one_local_telegram_surface():
    proposal, registry, surface = render_surface()

    assert surface.status == "rendered"
    assert surface.source_stage == "115P"
    assert surface.surface_stage == TELEGRAM_MEMORY_PROPOSAL_APPROVAL_STAGE
    assert surface.proposal_id == proposal.proposal_id
    assert surface.live_send_allowed is False
    assert surface.memory_write_allowed is False
    assert surface.memory_center_mutated is False
    assert surface.external_write_allowed is False


def test_116p_duplicate_rendering_returns_existing_surface_without_duplicates():
    proposal = pending_proposal()
    registry = TelegramMemoryProposalApprovalRegistry()

    first = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )
    second = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )

    assert first == second
    assert len(list_memory_proposal_approval_surfaces(registry=registry)) == 1
    assert get_memory_proposal_approval_surface(registry=registry, surface_id=first.surface_id) == first


def test_116p_valid_owner_approval_callback_records_approved_pending_writeback():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface),
        registry=registry,
    )

    assert record.decision_status == "approved_pending_writeback"
    assert record.writeback_stage_authorized is False
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.external_write_allowed is False
    assert record.live_send_allowed is False


def test_116p_valid_owner_rejection_callback_records_rejected_no_write():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, action="reject_memory_proposal"),
        registry=registry,
    )

    assert record.decision_status == "rejected_no_write"
    assert "No memory write was authorized" in record.response_text


def test_116p_valid_owner_edit_callback_records_edited_pending_writeback():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(
            surface,
            action="edit_memory_proposal_text",
            revised_proposed_memory_text="Use checklist format for NDA review follow-ups.",
        ),
        registry=registry,
    )

    assert record.decision_status == "edited_pending_writeback"
    assert record.revised_proposed_memory_text == "Use checklist format for NDA review follow-ups."


def test_116p_valid_owner_lineage_summary_callback_returns_deterministic_safe_summary():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, action="request_memory_proposal_lineage_summary"),
        registry=registry,
    )
    envelope = build_memory_proposal_approval_response_envelope(record)

    assert record.decision_status == "lineage_summary_requested"
    assert record.lineage_summary is not None
    assert "Memory proposal lineage summary:" in record.lineage_summary
    assert "No Memory Center write, MemoryItem mutation, external write, or live send was authorized." in record.lineage_summary
    assert envelope.live_send_allowed is False
    assert envelope.text == record.response_text


def test_116p_wrong_owner_callback_is_rejected():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, owner_id="other-owner"),
        registry=registry,
    )

    assert record.decision_status == "blocked"
    assert record.rejection_reason == "rejected_owner_mismatch"


def test_116p_wrong_robot_callback_is_rejected():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, robot_id="other-robot"),
        registry=registry,
    )

    assert record.rejection_reason == "rejected_robot_mismatch"


def test_116p_wrong_chat_callback_is_rejected():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, chat_id="other-chat"),
        registry=registry,
    )

    assert record.rejection_reason == "rejected_chat_mismatch"


def test_116p_unknown_proposal_is_rejected():
    registry = TelegramMemoryProposalApprovalRegistry()
    proposal = pending_proposal()
    surface = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )

    record = bind_memory_proposal_approval_selection(
        proposal_record=object(),
        surface_record=surface,
        payload=payload(surface),
        registry=registry,
    )

    assert record.decision_status == "blocked"
    assert record.rejection_reason == "rejected_unknown_115p_memory_proposal_record"


def test_116p_unknown_surface_is_rejected():
    proposal = pending_proposal()
    registry = TelegramMemoryProposalApprovalRegistry()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=object(),
        payload=payload(
            type(
                "FixtureSurface",
                (),
                {
                    "owner_id": proposal.owner_id,
                    "robot_id": proposal.robot_id,
                    "chat_id": "telegram-chat-112p",
                    "proposal_id": proposal.proposal_id,
                    "surface_id": "surface-missing",
                },
            )()
        ),
        registry=registry,
    )

    assert record.decision_status == "blocked"
    assert record.rejection_reason == "rejected_unknown_surface_record"


def test_116p_proposal_not_in_pending_user_review_is_rejected():
    proposal = replace(pending_proposal(), status="rejected_source", rejection_reason="fixture")
    registry = TelegramMemoryProposalApprovalRegistry()

    surface = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )

    assert surface.status == "blocked"
    assert surface.rejection_reason == "rejected_rejected_source_proposal"


def test_116p_no_memory_recommended_proposal_does_not_render_approval_surface():
    proposal = pending_proposal(delivery_text="Fixture deeper summary.")
    registry = TelegramMemoryProposalApprovalRegistry()

    surface = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )

    assert surface.status == "blocked"
    assert surface.rejection_reason == "rejected_no_memory_recommended_proposal"


def test_116p_rejected_source_proposal_does_not_render_approval_surface():
    proposal = replace(pending_proposal(), status="rejected_source", rejection_reason="fixture")
    registry = TelegramMemoryProposalApprovalRegistry()

    surface = render_memory_proposal_approval_surface(
        proposal_record=proposal,
        registry=registry,
        chat_id="telegram-chat-112p",
    )

    assert surface.status == "blocked"
    assert surface.rejection_reason == "rejected_rejected_source_proposal"


def test_116p_mismatched_proposal_surface_lineage_is_rejected():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, proposal_id="other-proposal"),
        registry=registry,
    )

    assert record.rejection_reason == "rejected_proposal_surface_mismatch"


def test_116p_unsupported_approval_action_is_rejected():
    proposal, registry, surface = render_surface()

    try:
        payload(surface, action="archive_memory_proposal")
    except ValueError as exc:
        assert "Unsupported 116P memory proposal approval action." in str(exc)
    else:
        raise AssertionError("Expected unsupported 116P action to fail.")

    blocked = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=replace(surface, status="blocked", rejection_reason="fixture"),
        payload=payload(surface),
        registry=registry,
    )
    assert blocked.rejection_reason == "rejected_non_rendered_surface_status_blocked"


def test_116p_sensitive_edit_text_is_rejected_locally():
    proposal, registry, surface = render_surface()

    record = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(
            surface,
            action="edit_memory_proposal_text",
            revised_proposed_memory_text="Remember the owner's health diagnosis.",
        ),
        registry=registry,
    )

    assert record.decision_status == "rejected_sensitive_edit"
    assert record.sensitive_data_blocked is True


def test_116p_duplicate_decision_callbacks_are_deduplicated():
    proposal, registry, surface = render_surface()
    decision_payload = payload(surface, action="reject_memory_proposal")

    first = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=decision_payload,
        registry=registry,
    )
    second = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=decision_payload,
        registry=registry,
    )

    assert first == second
    assert len(list_memory_proposal_approval_decisions(registry=registry)) == 1
    assert get_memory_proposal_approval_decision(registry=registry, decision_id=first.decision_id) == first


def test_116p_terminal_decision_blocks_replacement_action():
    proposal, registry, surface = render_surface()
    bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, action="approve_memory_proposal"),
        registry=registry,
    )

    blocked = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, action="reject_memory_proposal"),
        registry=registry,
    )

    assert blocked.decision_status == "blocked"
    assert blocked.rejection_reason == "rejected_proposal_already_decided"


def test_116p_records_preserve_100p_through_115p_lineage():
    proposal, registry, surface = render_surface()

    assert surface.lineage_summary["followup_execution_stage"] == "112P"
    assert surface.lineage_summary["followup_delegation_stage"] == "111P"
    assert surface.lineage_summary["proposal_stage"] == "115P"
    assert surface.lineage_summary["acknowledgement_stage"] == "114P"
    assert surface.lineage_summary["upstream_lineage"]["cost_preflight_summary"]["route_decision"]["selected_model_id"] == "balanced_standard_v1"

    decision = bind_memory_proposal_approval_selection(
        proposal_record=proposal,
        surface_record=surface,
        payload=payload(surface, action="request_memory_proposal_lineage_summary"),
        registry=registry,
    )
    assert "packet_id=" in decision.response_text


def test_116p_stage_stays_local_without_memory_or_external_side_effects():
    text = APPROVAL_PATH.read_text()

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


def test_116p_117p_plus_remains_unauthorized():
    roadmap = (REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md").read_text()

    assert "119P and later remain unauthorized" in roadmap or "119P+ remains unauthorized" in roadmap
