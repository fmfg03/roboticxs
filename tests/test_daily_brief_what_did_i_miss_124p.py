from __future__ import annotations

from app.async_delegation_inbox import AsyncDelegationInboxRecord
from app.context_scan_candidate_source import ContextScanCandidateSourceRecord
from app.daily_brief_what_did_i_miss import (
    DAILY_BRIEF_STAGE,
    DailyBriefRegistry,
    DailyBriefSourceBundle,
    create_daily_brief_snapshot,
    get_daily_brief_snapshot,
    list_daily_brief_items,
    list_daily_brief_snapshots,
)
from app.followup_delegation_authority import FollowUpDelegationRequestRecord
from app.followup_draft_planner import FollowUpDraftOption, FollowUpDraftPlanRecord
from app.followup_intent_review import FollowUpIntentReviewRecord
from app.followup_memory_proposal import FollowUpMemoryProposalCandidateRecord
from app.followup_result_acknowledgement import FollowUpResultAcknowledgementRecord
from app.memory_center_writeback import MemoryCenterWritebackRecord
from app.proactive_delegation_adapter import ProactiveDelegationAdapterRecord
from app.proactive_execution_skeleton import ProactiveExecutionAttemptRecord
from app.proactive_opportunity_detection import ProactiveOpportunityCandidateRecord
from app.proactive_suggestion_adapter import ProactiveSuggestionFollowupAdapterRecord
from app.proactive_telegram_suggestion import ProactiveTelegramSuggestionDeliveryRecord
from app.telegram_async_result_delivery import TelegramAsyncResultDeliveryRecord
from app.telegram_followup_choice_selection import TelegramFollowUpChoiceSelectionRecord
from app.telegram_followup_choice_surface import TelegramFollowUpChoiceSurfaceRecord
from app.telegram_memory_proposal_approval import TelegramMemoryProposalApprovalDecisionRecord
from app.telegram_result_acknowledgement import TelegramResultAcknowledgementRecord


OWNER_ID = "owner-124p"
ROBOT_ID = "robot-124p"
CHAT_ID = "chat-124p"
WINDOW_START = "2026-06-20T00:00:00+00:00"
WINDOW_END = "2026-06-20T23:59:59+00:00"


def test_124p_builds_deterministic_daily_brief_snapshot_from_local_records():
    registry = DailyBriefRegistry()
    bundle = DailyBriefSourceBundle(
        inbox_records_103p=(
            AsyncDelegationInboxRecord(
                inbox_record_id="inbox-1",
                event_id="event-1",
                handle_id="handle-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                request_id="request-1",
                event_kind="completed",
                status="accepted",
                reason=None,
                bound_completion_event={"event_id": "event-1"},
                rejection_evidence=None,
                created_at="2026-06-20T08:00:00Z",
            ),
        ),
        delivery_records_105p=(
            TelegramAsyncResultDeliveryRecord(
                delivery_id="delivery-pending",
                surface_id="surface-pending",
                inbox_record_id="inbox-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                delivery_kind="OWNER_ASYNC_RESULT_NOTIFICATION",
                status="delivered",
                text="Pending result text",
                button_labels=("Marcar revisado",),
                lineage_summary={"delivery_stage": "105P", "delivery_id": "delivery-pending", "surface_id": "surface-pending"},
                transport_receipt={"kind": "local"},
                rejection_reason=None,
            ),
            TelegramAsyncResultDeliveryRecord(
                delivery_id="delivery-blocked",
                surface_id="surface-blocked",
                inbox_record_id="inbox-2",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                delivery_kind="OWNER_ASYNC_RESULT_NOTIFICATION",
                status="blocked",
                text="Blocked result text",
                button_labels=("Marcar revisado",),
                lineage_summary={"delivery_stage": "105P", "delivery_id": "delivery-blocked", "surface_id": "surface-blocked"},
                transport_receipt=None,
                rejection_reason="rejected_unknown_telegram_binding",
            ),
            TelegramAsyncResultDeliveryRecord(
                delivery_id="delivery-other-owner",
                surface_id="surface-other-owner",
                inbox_record_id="inbox-3",
                owner_id="other-owner",
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                delivery_kind="OWNER_ASYNC_RESULT_NOTIFICATION",
                status="delivered",
                text="Should be excluded",
                button_labels=("Marcar revisado",),
                lineage_summary={"delivery_stage": "105P"},
                transport_receipt={"kind": "local"},
                rejection_reason=None,
            ),
        ),
        result_acknowledgements_106p=(
            TelegramResultAcknowledgementRecord(
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                callback_action="acknowledge",
                status="recorded",
                response_text="Listo. Marque este resultado como revisado.",
                lineage_summary={"acknowledgement_stage": "106P", "delivery_id": "delivery-ack"},
                rejection_reason=None,
            ),
        ),
        followup_intents_107p=(
            FollowUpIntentReviewRecord(
                followup_intent_id="intent-1",
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                source_action="request_followup_pending",
                status="pending_review",
                review_summary="Owner asked for follow-up review.",
                lineage_summary={"followup_stage": "107P", "upstream_lineage": {"delivery_stage": "105P"}},
                rejection_reason=None,
            ),
        ),
        followup_plans_108p=(
            FollowUpDraftPlanRecord(
                draft_plan_id="plan-1",
                followup_intent_id="intent-1",
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                status="drafted",
                title="Plan title",
                summary="Drafted options for review.",
                options=(
                    FollowUpDraftOption(
                        option_id="option-1",
                        label="Checklist",
                        description="Human review checklist",
                        option_kind="human_review_checklist",
                        local_only=True,
                        creates_authority=False,
                    ),
                ),
                lineage_summary={"followup_stage": "108P"},
                rejection_reason=None,
            ),
        ),
        followup_choice_surfaces_109p=(
            TelegramFollowUpChoiceSurfaceRecord(
                choice_surface_id="choice-1",
                draft_plan_id="plan-1",
                followup_intent_id="intent-1",
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                source_surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                status="delivered",
                text="Choose next follow-up.",
                button_labels=("Checklist",),
                option_refs=("option-1",),
                lineage_summary={"surface_stage": "109P"},
                transport_receipt={"kind": "local"},
                rejection_reason=None,
            ),
        ),
        followup_selections_110p=(
            TelegramFollowUpChoiceSelectionRecord(
                selection_id="selection-1",
                choice_surface_id="choice-1",
                draft_plan_id="plan-1",
                selected_option_id="option-1",
                selected_option_kind="human_review_checklist",
                followup_intent_id="intent-1",
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                source_surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                status="selected_pending_authorization",
                response_text="Selection recorded.",
                lineage_summary={"selection_stage": "110P"},
                rejection_reason=None,
            ),
        ),
        followup_delegations_111p=(
            FollowUpDelegationRequestRecord(
                followup_delegation_id="delegation-1",
                selection_id="selection-1",
                selected_option_id="option-1",
                selected_option_kind="human_review_checklist",
                followup_task_class="FOLLOWUP_HUMAN_REVIEW_CHECKLIST",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                telegram_chat_id=CHAT_ID,
                draft_plan_id="plan-1",
                choice_surface_id="choice-1",
                acknowledgement_id="ack-106",
                delivery_id="delivery-ack",
                source_surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                status="registered",
                async_packet_id="packet-1",
                async_handle_id="handle-1",
                lineage_summary={"delegation_stage": "111P"},
                rejection_reason=None,
            ),
        ),
        followup_acknowledgements_114p=(
            FollowUpResultAcknowledgementRecord(
                acknowledgement_id="followup-ack-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                route_id="route-1",
                delivery_record_id="delivery-ack",
                surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                event_candidate_id="event-candidate-1",
                attempt_id="attempt-1",
                delegation_id="delegation-1",
                packet_id="packet-1",
                handle_id="handle-1",
                action="acknowledge_followup_result",
                status="acknowledged",
                source_stage="113P",
                acknowledged_stage="114P",
                memory_mutation_allowed=False,
                new_delegation_allowed=False,
                external_write_allowed=False,
                live_send_allowed=False,
                acknowledgement_bound=True,
                dedupe_key="followup-ack-dedupe",
                response_text="Follow-up result reviewed.",
                lineage_summary=None,
                lineage_metadata={"acknowledgement_stage": "114P", "route_id": "route-1"},
                created_at="2026-06-20T10:00:00Z",
                rejection_reason=None,
            ),
        ),
        memory_proposals_115p=(
            FollowUpMemoryProposalCandidateRecord(
                proposal_id="proposal-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                acknowledgement_id="followup-ack-1",
                route_id="route-1",
                delivery_record_id="delivery-ack",
                surface_id="surface-ack",
                inbox_record_id="inbox-ack",
                event_candidate_id="event-candidate-1",
                attempt_id="attempt-1",
                delegation_id="delegation-1",
                packet_id="packet-1",
                handle_id="handle-1",
                source_stage="114P",
                proposal_stage="115P",
                proposal_type="task_memory_candidate",
                proposed_memory_text="Remember to review ACME follow-up context.",
                confidence="medium",
                review_reason="Possible task memory candidate.",
                status="pending_user_review",
                memory_write_allowed=False,
                telegram_approval_surface_allowed=False,
                user_approved=False,
                memory_center_mutated=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key="proposal-dedupe-1",
                lineage_summary={"proposal_stage": "115P"},
                created_at="2026-06-20T10:30:00Z",
                rejection_reason=None,
            ),
        ),
        memory_approval_decisions_116p=(
            TelegramMemoryProposalApprovalDecisionRecord(
                decision_id="decision-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                surface_id="memory-surface-1",
                proposal_id="proposal-1",
                action="approve_memory_proposal",
                decision_status="approved_pending_writeback",
                original_proposed_memory_text="Remember to review ACME follow-up context.",
                revised_proposed_memory_text=None,
                source_stage="115P",
                decision_stage="116P",
                writeback_stage_authorized=False,
                memory_write_allowed=False,
                memory_center_mutated=False,
                external_write_allowed=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key="decision-dedupe-1",
                lineage_summary={"decision_stage": "116P", "proposal_id": "proposal-1"},
                created_at="2026-06-20T11:00:00Z",
                response_text="Approved for later local writeback.",
                rejection_reason=None,
            ),
            TelegramMemoryProposalApprovalDecisionRecord(
                decision_id="decision-blocked",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                surface_id="memory-surface-2",
                proposal_id="proposal-blocked",
                action="reject_memory_proposal",
                decision_status="blocked",
                original_proposed_memory_text=None,
                revised_proposed_memory_text=None,
                source_stage="115P",
                decision_stage="116P",
                writeback_stage_authorized=False,
                memory_write_allowed=False,
                memory_center_mutated=False,
                external_write_allowed=False,
                live_send_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key="decision-dedupe-2",
                lineage_summary={"decision_stage": "116P", "proposal_id": "proposal-blocked"},
                created_at="2026-06-20T11:05:00Z",
                response_text="Blocked memory decision.",
                rejection_reason="invalid approval lineage",
            ),
        ),
        memory_writebacks_117p=(
            MemoryCenterWritebackRecord(
                writeback_id="writeback-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                decision_id="decision-written",
                surface_id="memory-surface-written",
                proposal_id="proposal-written",
                acknowledgement_id="followup-ack-1",
                route_id="route-1",
                delivery_record_id="delivery-ack",
                event_candidate_id="event-candidate-1",
                attempt_id="attempt-1",
                delegation_id="delegation-1",
                packet_id="packet-1",
                handle_id="handle-1",
                source_stage="116P",
                writeback_stage="117P",
                proposal_type="task_memory_candidate",
                memory_section="TASK_MEMORY",
                final_memory_text="ACME follow-up reminder stored locally.",
                decision_status="approved_pending_writeback",
                writeback_status="written",
                memory_item_id="memory-item-1",
                memory_center_mutated=True,
                external_write_allowed=False,
                live_send_allowed=False,
                context_scan_allowed=False,
                proactive_detection_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key="writeback-dedupe-1",
                lineage_summary={"writeback_stage": "117P", "proposal_id": "proposal-written"},
                created_at="2026-06-20T12:00:00Z",
                rejection_reason=None,
            ),
        ),
        context_sources_118p=(
            ContextScanCandidateSourceRecord(
                candidate_source_id="source-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                authorization_id="scan-auth-1",
                source_type="mock_calendar_event",
                source_category="calendar_context",
                source_status="authorized_local_fixture",
                scan_scope="metadata_only",
                fixture_id="fixture-calendar-1",
                source_title="Board meeting tomorrow",
                source_summary="Meeting metadata available.",
                source_timestamp="2026-06-20T09:00:00Z",
                source_origin="local_fixture",
                source_stage="118P",
                live_connector_allowed=False,
                external_read_allowed=False,
                external_write_allowed=False,
                memory_write_allowed=False,
                proactive_detection_allowed=False,
                telegram_send_allowed=False,
                worker_dispatch_allowed=False,
                sensitive_data_blocked=False,
                retention_policy="test-only",
                dedupe_key="source-dedupe-1",
                lineage_summary={"source_stage": "118P", "candidate_source_id": "source-1"},
                created_at="2026-06-20T09:00:00Z",
            ),
            ContextScanCandidateSourceRecord(
                candidate_source_id="source-invalid",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                authorization_id="scan-auth-1",
                source_type="mock_document",
                source_category="document_context",
                source_status="authorized_local_fixture",
                scan_scope="metadata_only",
                fixture_id="fixture-invalid",
                source_title="Invalid lineage source",
                source_summary=None,
                source_timestamp="2026-06-20T09:30:00Z",
                source_origin="local_fixture",
                source_stage="118P",
                live_connector_allowed=False,
                external_read_allowed=False,
                external_write_allowed=False,
                memory_write_allowed=False,
                proactive_detection_allowed=False,
                telegram_send_allowed=False,
                worker_dispatch_allowed=False,
                sensitive_data_blocked=False,
                retention_policy="test-only",
                dedupe_key="source-dedupe-invalid",
                lineage_summary={},
                created_at="2026-06-20T09:30:00Z",
            ),
        ),
        proactive_opportunities_119p=(
            ProactiveOpportunityCandidateRecord(
                opportunity_id="opportunity-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                candidate_source_id="source-1",
                authorization_id="scan-auth-1",
                source_type="mock_calendar_event",
                source_category="calendar_context",
                source_stage="118P",
                detection_stage="119P",
                opportunity_type="meeting_brief_missing",
                opportunity_category="meeting",
                title="Meeting brief missing",
                summary="A meeting brief is still missing for tomorrow.",
                trigger_reason="calendar_event_detected",
                suggested_next_step_type="prepare_brief",
                confidence="high",
                evidence_refs=({"candidate_source_id": "source-1"},),
                source_created_detection=False,
                telegram_send_allowed=False,
                followup_adapter_allowed=False,
                async_delegation_allowed=False,
                execution_allowed=False,
                memory_write_allowed=False,
                live_connector_allowed=False,
                external_write_allowed=False,
                worker_dispatch_allowed=False,
                sensitive_data_blocked=False,
                dedupe_key="opportunity-dedupe-1",
                lineage_summary={"detection_stage": "119P", "candidate_source_id": "source-1"},
                created_at="2026-06-20T13:00:00Z",
            ),
        ),
        proactive_deliveries_120p=(
            ProactiveTelegramSuggestionDeliveryRecord(
                delivery_record_id="proactive-delivery-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                suggestion_surface_id="proactive-surface-1",
                opportunity_id="opportunity-delivered",
                candidate_source_id="source-1",
                delivery_stage="120P",
                delivery_mode="injected_local_only",
                delivery_status="delivered_local",
                live_send_allowed=False,
                callback_binding_allowed=False,
                followup_adapter_allowed=False,
                async_delegation_allowed=False,
                execution_allowed=False,
                memory_write_allowed=False,
                external_write_allowed=False,
                worker_dispatch_allowed=False,
                dedupe_key="proactive-delivery-dedupe-1",
                lineage_summary={"delivery_stage": "120P", "opportunity_id": "opportunity-delivered"},
                created_at="2026-06-20T13:30:00Z",
            ),
        ),
        proactive_adapters_121p=(
            ProactiveSuggestionFollowupAdapterRecord(
                adapter_id="proactive-adapter-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                delivery_record_id="proactive-delivery-1",
                suggestion_surface_id="proactive-surface-1",
                opportunity_id="opportunity-delivered",
                candidate_source_id="source-1",
                authorization_id="proactive-auth-1",
                source_stage="118P",
                detection_stage="119P",
                suggestion_stage="120P",
                adapter_stage="121P",
                opportunity_type="meeting_brief_missing",
                opportunity_category="meeting",
                suggested_next_step_type="prepare_brief",
                normalized_intent_kind="prepare_meeting_brief",
                followup_intent_review_record_id="intent-proactive-1",
                explicit_owner_adapter_authorization_id="proactive-auth-1",
                adapter_status="adapted_to_followup_intent",
                planner_called=False,
                choice_surface_created=False,
                selection_bound=False,
                delegation_created=False,
                execution_allowed=False,
                telegram_send_allowed=False,
                memory_write_allowed=False,
                external_write_allowed=False,
                worker_dispatch_allowed=False,
                live_connector_allowed=False,
                dedupe_key="proactive-adapter-dedupe-1",
                lineage_summary={"adapter_stage": "121P", "opportunity_id": "opportunity-delivered"},
                created_at="2026-06-20T14:00:00Z",
            ),
        ),
        proactive_delegations_122p=(
            ProactiveDelegationAdapterRecord(
                proactive_delegation_adapter_id="proactive-delegation-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                proactive_adapter_id="proactive-adapter-1",
                delivery_record_id="proactive-delivery-1",
                suggestion_surface_id="proactive-surface-1",
                opportunity_id="opportunity-delivered",
                candidate_source_id="source-1",
                source_authorization_id="scan-auth-1",
                source_stage="118P",
                detection_stage="119P",
                suggestion_stage="120P",
                adapter_stage="121P",
                delegation_adapter_stage="122P",
                followup_intent_review_record_id="intent-proactive-1",
                followup_plan_id="plan-proactive-1",
                followup_choice_surface_id="choice-proactive-1",
                followup_selection_id="selection-proactive-1",
                explicit_owner_delegation_authorization_id="delegation-auth-1",
                normalized_intent_kind="prepare_meeting_brief",
                selected_option_id="option-proactive-1",
                mapped_task_class="FOLLOWUP_DEEPER_SUMMARY",
                delegation_packet_id="packet-proactive-1",
                delegation_handle_id="handle-proactive-1",
                adapter_status="delegated_registered",
                uses_existing_delegation_authority=True,
                execution_allowed=False,
                worker_dispatch_allowed=False,
                model_call_allowed=False,
                tool_call_allowed=False,
                live_connector_allowed=False,
                telegram_send_allowed=False,
                memory_write_allowed=False,
                external_write_allowed=False,
                dedupe_key="proactive-delegation-dedupe-1",
                lineage_summary={"delegation_adapter_stage": "122P", "opportunity_id": "opportunity-delivered"},
                created_at="2026-06-20T14:30:00Z",
            ),
        ),
        proactive_executions_123p=(
            ProactiveExecutionAttemptRecord(
                proactive_execution_attempt_id="proactive-execution-1",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                proactive_delegation_adapter_id="proactive-delegation-1",
                delegation_packet_id="packet-proactive-1",
                delegation_handle_id="handle-proactive-1",
                proactive_adapter_id="proactive-adapter-1",
                delivery_record_id="proactive-delivery-1",
                suggestion_surface_id="proactive-surface-1",
                opportunity_id="opportunity-delivered",
                candidate_source_id="source-1",
                source_authorization_id="scan-auth-1",
                followup_intent_review_record_id="intent-proactive-1",
                followup_plan_id="plan-proactive-1",
                followup_choice_surface_id="choice-proactive-1",
                followup_selection_id="selection-proactive-1",
                explicit_owner_delegation_authorization_id="delegation-auth-1",
                source_stage="118P",
                detection_stage="119P",
                suggestion_stage="120P",
                adapter_stage="121P",
                delegation_adapter_stage="122P",
                execution_stage="123P",
                mapped_task_class="FOLLOWUP_DEEPER_SUMMARY",
                execution_mode="deterministic_local",
                attempt_status="completed_candidate_created",
                completion_event_candidate_id="completion-event-1",
                failure_event_candidate_id=None,
                result_summary="Prepared a local proactive completion candidate.",
                failure_reason=None,
                inbox_insert_allowed=False,
                result_surface_allowed=False,
                telegram_delivery_allowed=False,
                worker_dispatch_allowed=False,
                model_call_allowed=False,
                tool_call_allowed=False,
                live_connector_allowed=False,
                external_write_allowed=False,
                memory_write_allowed=False,
                dedupe_key="proactive-execution-dedupe-1",
                lineage_summary={"execution_stage": "123P", "opportunity_id": "opportunity-delivered"},
                created_at="2026-06-20T15:00:00Z",
            ),
            ProactiveExecutionAttemptRecord(
                proactive_execution_attempt_id="proactive-execution-2",
                owner_id=OWNER_ID,
                robot_id=ROBOT_ID,
                chat_id=CHAT_ID,
                proactive_delegation_adapter_id="proactive-delegation-1",
                delegation_packet_id="packet-proactive-2",
                delegation_handle_id="handle-proactive-2",
                proactive_adapter_id="proactive-adapter-1",
                delivery_record_id="proactive-delivery-1",
                suggestion_surface_id="proactive-surface-1",
                opportunity_id="opportunity-delivered",
                candidate_source_id="source-1",
                source_authorization_id="scan-auth-1",
                followup_intent_review_record_id="intent-proactive-2",
                followup_plan_id="plan-proactive-2",
                followup_choice_surface_id="choice-proactive-2",
                followup_selection_id="selection-proactive-2",
                explicit_owner_delegation_authorization_id="delegation-auth-2",
                source_stage="118P",
                detection_stage="119P",
                suggestion_stage="120P",
                adapter_stage="121P",
                delegation_adapter_stage="122P",
                execution_stage="123P",
                mapped_task_class="FOLLOWUP_COMPARE_PRIOR_VERSION",
                execution_mode="deterministic_local",
                attempt_status="failure_candidate_created",
                completion_event_candidate_id=None,
                failure_event_candidate_id="failure-event-2",
                result_summary=None,
                failure_reason="missing_local_prior_version_fixture",
                inbox_insert_allowed=False,
                result_surface_allowed=False,
                telegram_delivery_allowed=False,
                worker_dispatch_allowed=False,
                model_call_allowed=False,
                tool_call_allowed=False,
                live_connector_allowed=False,
                external_write_allowed=False,
                memory_write_allowed=False,
                dedupe_key="proactive-execution-dedupe-2",
                lineage_summary={"execution_stage": "123P", "opportunity_id": "opportunity-delivered"},
                created_at="2026-06-20T15:05:00Z",
            ),
        ),
    )

    snapshot = create_daily_brief_snapshot(
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        brief_date="2026-06-20",
        timezone="UTC",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        source_records=bundle,
        registry=registry,
    )

    assert snapshot.brief_stage == DAILY_BRIEF_STAGE
    assert snapshot.telegram_delivery_allowed is False
    assert snapshot.callback_binding_allowed is False
    assert snapshot.followup_intent_creation_allowed is False
    assert snapshot.async_delegation_allowed is False
    assert snapshot.execution_allowed is False
    assert snapshot.memory_write_allowed is False
    assert snapshot.model_call_allowed is False
    assert snapshot.tool_call_allowed is False
    assert snapshot.live_connector_allowed is False
    assert snapshot.external_write_allowed is False
    assert snapshot.worker_dispatch_allowed is False
    assert snapshot.sensitive_data_excluded is True
    assert "pending results" in snapshot.headline_summary.lower()
    assert "No live connectors" in snapshot.local_render_text

    items = list_daily_brief_items(registry=registry, brief_id=snapshot.brief_id)
    assert any(item.section_name == "pending_results" and item.source_stage == "105P" for item in items)
    assert any(item.section_name == "pending_followups" and item.source_stage == "107P" for item in items)
    assert any(item.section_name == "pending_followups" and item.source_stage == "121P" for item in items)
    assert any(item.section_name == "pending_followups" and item.source_stage == "122P" for item in items)
    assert any(item.section_name == "pending_memory_reviews" and item.source_stage == "115P" for item in items)
    assert any(item.section_name == "pending_memory_reviews" and item.source_stage == "116P" for item in items)
    assert any(item.section_name == "memory_written_today" and item.source_stage == "117P" for item in items)
    assert any(item.section_name == "completed_today" and item.source_stage == "118P" for item in items)
    assert any(item.section_name == "proactive_opportunities" and item.source_stage == "119P" for item in items)
    assert any(item.section_name == "proactive_suggestions_sent_local" and item.source_stage == "120P" for item in items)
    assert any(item.section_name == "proactive_execution_candidates" and item.source_stage == "123P" for item in items)
    assert any(item.section_name == "blocked_or_rejected_items" and item.source_stage == "105P" for item in items)
    assert any(item.section_name == "blocked_or_rejected_items" and item.source_stage == "116P" for item in items)
    assert any(item.section_name == "completed_today" and item.source_stage == "106P" for item in items)
    assert any(item.section_name == "completed_today" and item.source_stage == "114P" for item in items)
    assert not any(item.source_record_id == "delivery-other-owner" for item in items)
    assert not any(item.source_record_id == "source-invalid" for item in items)
    assert len([item for item in items if item.source_record_id == "delivery-pending"]) == 1

    assert get_daily_brief_snapshot(registry=registry, brief_id=snapshot.brief_id) == snapshot
    assert list_daily_brief_snapshots(registry=registry) == (snapshot,)


def test_124p_empty_input_produces_valid_no_updates_brief():
    registry = DailyBriefRegistry()

    snapshot = create_daily_brief_snapshot(
        owner_id=OWNER_ID,
        robot_id=ROBOT_ID,
        brief_date="2026-06-20",
        timezone="UTC",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        source_records=DailyBriefSourceBundle(),
        registry=registry,
    )

    assert snapshot.headline_summary == "No updates were recorded in the selected window."
    assert "No updates were recorded in the selected window." in snapshot.local_render_text
    assert snapshot.total_item_count >= 3


def test_124p_rejects_missing_owner_robot_and_invalid_window():
    registry = DailyBriefRegistry()
    bundle = DailyBriefSourceBundle()

    try:
        create_daily_brief_snapshot(
            owner_id="",
            robot_id=ROBOT_ID,
            brief_date="2026-06-20",
            timezone="UTC",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            source_records=bundle,
            registry=registry,
        )
    except ValueError as exc:
        assert str(exc) == "rejected_missing_owner_id"
    else:
        raise AssertionError("Expected missing owner rejection.")

    try:
        create_daily_brief_snapshot(
            owner_id=OWNER_ID,
            robot_id="",
            brief_date="2026-06-20",
            timezone="UTC",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            source_records=bundle,
            registry=registry,
        )
    except ValueError as exc:
        assert str(exc) == "rejected_missing_robot_id"
    else:
        raise AssertionError("Expected missing robot rejection.")

    try:
        create_daily_brief_snapshot(
            owner_id=OWNER_ID,
            robot_id=ROBOT_ID,
            brief_date="2026-06-20",
            timezone="UTC",
            window_start="2026-06-20T12:00:00+00:00",
            window_end="2026-06-20T11:00:00+00:00",
            source_records=bundle,
            registry=registry,
        )
    except ValueError as exc:
        assert str(exc) == "rejected_invalid_window_range"
    else:
        raise AssertionError("Expected invalid window rejection.")
