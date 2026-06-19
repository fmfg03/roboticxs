from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.action_packet_approval import ActionPacketDecision, apply_action_packet_decision, create_action_packet, submit_action_packet_for_approval
from app.async_delegation_authority import (
    AsyncDelegationRequest,
    bind_async_delegation_approval,
    build_async_delegation_action_packet_request,
    build_completion_event,
    create_async_delegation_authority_state,
    register_async_delegation_handle,
)
from app.async_delegation_inbox import AsyncDelegationCompletionInbox, AsyncDelegationInboxRecord, create_async_delegation_registry
from app.async_result_surface import (
    ASYNC_RESULT_SURFACE_STAGE,
    build_async_result_message_envelope,
    build_async_result_surface,
    render_async_result_surface_text,
)
from app.cost_governor import (
    BudgetPolicy,
    CostPreflightResult,
    CostTraceRecord,
    ModelRouteDecision,
    TaskCostRequest,
    TokenUsageEstimate,
    evaluate_cost_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SURFACE_PATH = REPO_ROOT / "app/async_result_surface.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def delegation_request(**overrides) -> AsyncDelegationRequest:
    values = {
        "delegation_id": "delegation-104p",
        "source_stage": "98P",
        "owner_id": "owner-104p",
        "robot_id": "robot-104p",
        "actor_id": "actor-104p",
        "actor_role": "owner_admin",
        "task_class": "async_delegation",
        "requested_capability": "Preparar resumen del documento NDA",
        "requested_route_mode": "balanced",
        "request_payload": {"summary": "Preparar resumen del documento NDA"},
        "required_policy_trace": (
            "command_surface_policy_90p",
            "skill_scope_policy_91p",
            "tool_authority_policy_92p",
        ),
        "required_memory_projection_request_id": None,
        "required_routine_run_id": "routine-104p",
        "expires_at": "2026-06-20T00:00:00Z",
        "authority_expansion_requested": False,
        "live_dispatch_requested": False,
    }
    values.update(overrides)
    return AsyncDelegationRequest(**values)


def task_cost_request(**overrides) -> TaskCostRequest:
    values = {
        "request_id": "cost-request-104p",
        "owner_id": "owner-104p",
        "robot_id": "robot-104p",
        "task_class": "async_delegation",
        "routing_mode": "balanced",
        "sensitivity": "ordinary",
        "requires_tools": False,
        "requires_long_context": False,
        "input_chars_estimate": 1200,
        "expected_output_chars": 800,
        "context_item_count": 2,
        "active_skill_id": "basic_assistant",
        "memory_context_used": True,
        "routine_requested": True,
        "async_delegation_requested": True,
        "authority_expansion_requested": False,
    }
    values.update(overrides)
    return TaskCostRequest(**values)


def budget_policy(**overrides) -> BudgetPolicy:
    values = {
        "policy_id": "policy-104p",
        "owner_id": "owner-104p",
        "robot_id": "robot-104p",
        "routing_mode_allowlist": ("economy", "balanced", "premium", "byok"),
        "default_routing_mode": "balanced",
        "max_estimated_cost_usd": 0.08,
        "confirmation_cost_usd": 0.02,
        "max_input_tokens": 4000,
        "max_output_tokens": 1800,
        "long_context_confirmation_tokens": 2400,
        "byok_allowed": False,
        "async_delegation_allowed": True,
        "premium_allowed_without_confirmation": False,
        "allowed_task_classes": (
            "simple_classification",
            "extraction",
            "drafting",
            "research",
            "reasoning",
            "tool_planning",
            "sensitive_review",
            "long_context",
            "creative",
            "routine",
            "async_delegation",
        ),
        "sensitive_task_min_tier": "advanced",
        "unsafe_model_block": True,
        "untrusted_model_block": True,
        "requires_trace": True,
    }
    values.update(overrides)
    return BudgetPolicy(**values)


def approval_decision(packet_state, *, choice: str, occurred_at: str = "2026-06-17T14:00:00Z") -> ActionPacketDecision:
    return ActionPacketDecision(
        packet_id=packet_state.packet.packet_id,
        packet_version=packet_state.packet.packet_version,
        decision=choice,
        actor_id=packet_state.packet.actor_id,
        actor_role=packet_state.packet.actor_role,
        owner_id=packet_state.packet.owner_id,
        robot_id=packet_state.packet.robot_id,
        reason_code=f"{choice}_async_delegation",
        edit_payload=None,
        resume_token_id=None,
        occurred_at=occurred_at,
    )


def synthetic_allow_preflight(request: TaskCostRequest) -> CostPreflightResult:
    token_estimate = TokenUsageEstimate(
        estimated_input_tokens=300,
        estimated_output_tokens=220,
        estimated_total_tokens=520,
        estimation_basis="test_fixture",
        long_context_applied=False,
    )
    route = ModelRouteDecision(
        selected_provider_id="local_fixture",
        selected_model_id="balanced_standard_v1",
        selected_capability_tier="standard",
        selected_trust_level="trusted",
        candidate_models_considered=("balanced_standard_v1",),
        rejected_candidates=(),
        downgrade_from_model_id=None,
        decision_reason="allow_selected_eligible_route",
    )
    trace = CostTraceRecord(
        request_id=request.request_id,
        task_class=request.task_class,
        routing_mode=request.routing_mode,
        candidate_model_id=None,
        selected_model_id="balanced_standard_v1",
        candidate_model_ids=("balanced_standard_v1",),
        decision="allow",
        reason_code="allow_selected_eligible_route",
        estimated_input_tokens=token_estimate.estimated_input_tokens,
        estimated_output_tokens=token_estimate.estimated_output_tokens,
        estimated_cost_usd=0.03,
        budget_state="within_budget",
    )
    return CostPreflightResult(
        request_id=request.request_id,
        decision="allow",
        budget_policy_id="policy-104p",
        token_estimate=token_estimate,
        route_decision=route,
        estimated_cost_usd=0.03,
        confirmation_required=False,
        blocked=False,
        trace=(trace,),
    )


def create_and_approve_async_action_packet(
    *,
    request: AsyncDelegationRequest,
    task_request: TaskCostRequest,
    policy: BudgetPolicy,
    preflight: CostPreflightResult,
):
    packet_request = build_async_delegation_action_packet_request(
        request=request,
        cost_preflight=preflight,
        task_cost_request=task_request,
        budget_policy=policy,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )
    approval_state = create_action_packet(
        request=packet_request,
        occurred_at="2026-06-17T12:00:00Z",
    )
    submitted = submit_action_packet_for_approval(
        approval_state=approval_state,
        actor_id=request.owner_id,
        actor_role="owner_admin",
        occurred_at="2026-06-17T12:05:00Z",
    )
    approved = apply_action_packet_decision(
        approval_state=submitted,
        decision=approval_decision(submitted, choice="approve"),
    )
    return approved


def registered_state(*, require_approval: bool = False):
    request = delegation_request()
    task_request = task_cost_request()
    if require_approval:
        policy = budget_policy(async_delegation_allowed=True)
        preflight = evaluate_cost_preflight(request=task_request, budget_policy=policy)
        awaiting = create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=policy,
            cost_preflight=preflight,
            occurred_at="2026-06-17T12:00:00Z",
        )
        approved = create_and_approve_async_action_packet(
            request=request,
            task_request=task_request,
            policy=policy,
            preflight=preflight,
        )
        return register_async_delegation_handle(
            authority_state=bind_async_delegation_approval(
                authority_state=awaiting,
                approval_state=approved,
                occurred_at="2026-06-17T14:00:00Z",
            ),
            occurred_at="2026-06-17T14:05:00Z",
        )
    return register_async_delegation_handle(
        authority_state=create_async_delegation_authority_state(
            request=request,
            task_cost_request=task_request,
            budget_policy=budget_policy(),
            cost_preflight=synthetic_allow_preflight(task_request),
            occurred_at="2026-06-17T12:00:00Z",
        ),
        occurred_at="2026-06-17T12:05:00Z",
    )


def accepted_record(
    *,
    completion_status: str = "completed",
    completion_payload_summary: dict[str, object] | None = None,
    require_approval: bool = False,
) -> AsyncDelegationInboxRecord:
    state = registered_state(require_approval=require_approval)
    event = build_completion_event(
        authority_state=state,
        completion_status=completion_status,
        source_stage="simulated_import",
        completion_payload_summary=completion_payload_summary
        or {
            "highlights": [
                "El documento contiene obligaciones de confidencialidad amplias.",
                "La duracion principal parece ser de 3 anos.",
                "No se detecto clausula de exclusividad.",
                "Requiere revision humana antes de firma.",
            ]
        },
        reason_code="completed_local_record" if completion_status == "completed" else "failed_local_record",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def duplicate_record() -> AsyncDelegationInboxRecord:
    state = registered_state()
    event = build_completion_event(
        authority_state=state,
        completion_status="completed",
        source_stage="simulated_import",
        completion_payload_summary={"summary": "Resumen listo"},
        reason_code="completed_local_record",
    )
    first = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    second = first.inbox.receive_event(event=event, registry=first.registry)
    return second.record


def quarantined_record() -> AsyncDelegationInboxRecord:
    state = registered_state()
    event = replace(
        build_completion_event(
            authority_state=state,
            completion_status="completed",
            source_stage="simulated_import",
            completion_payload_summary={"summary": "Resumen listo"},
            reason_code="completed_local_record",
        ),
        owner_id="other-owner",
    )
    receipt = AsyncDelegationCompletionInbox().receive_event(
        event=event,
        registry=create_async_delegation_registry(state),
    )
    return receipt.record


def test_104p_completed_inbox_record_renders_user_surface():
    surface = build_async_result_surface(accepted_record())

    assert surface is not None
    assert surface.status == "completed"
    assert surface.title == "Resultado listo"
    assert surface.telegram_envelope is not None


def test_104p_failed_inbox_record_renders_user_surface():
    surface = build_async_result_surface(
        accepted_record(
            completion_status="failed",
            completion_payload_summary={"summary": "La tarea no pudo completarse bajo la autoridad registrada."},
        )
    )

    assert surface is not None
    assert surface.status == "failed"
    assert surface.title == "Resultado no disponible"
    assert "autoridad registrada" in surface.summary


def test_104p_quarantined_record_does_not_render_success_surface():
    assert build_async_result_surface(quarantined_record()) is None


def test_104p_duplicate_record_is_idempotent():
    accepted_surface = build_async_result_surface(accepted_record(completion_payload_summary={"summary": "Resumen listo"}))
    duplicate_surface = build_async_result_surface(duplicate_record())

    assert accepted_surface is not None
    assert duplicate_surface is not None
    assert duplicate_surface.surface_id == accepted_surface.surface_id
    assert render_async_result_surface_text(duplicate_surface) == render_async_result_surface_text(accepted_surface)


def test_104p_surface_id_is_deterministic():
    first = build_async_result_surface(accepted_record())
    second = build_async_result_surface(accepted_record())

    assert first is not None
    assert second is not None
    assert first.surface_id == second.surface_id


def test_104p_surface_includes_task_status_result_cost_and_route_summary():
    surface = build_async_result_surface(accepted_record())

    assert surface is not None
    assert surface.task_label == "Preparar resumen del documento NDA"
    assert surface.cost_summary == "$0.03"
    assert surface.route_summary == "balanced / balanced_standard_v1"
    text = render_async_result_surface_text(surface)
    assert "Tarea: Preparar resumen del documento NDA" in text
    assert "Estado: completed" in text
    assert "Costo estimado: $0.03" in text
    assert "Ruta/modelo: balanced / balanced_standard_v1" in text


def test_104p_surface_preserves_100p_101p_102p_103p_lineage_internally():
    record = accepted_record(require_approval=True)
    surface = build_async_result_surface(record)

    assert surface is not None
    assert surface.lineage_summary["inbox_stage"] == "103P"
    assert surface.lineage_summary["inbox_record_id"] == record.inbox_record_id
    assert surface.lineage_summary["request_evidence"] == record.bound_completion_event["original_request_evidence"]
    assert surface.lineage_summary["cost_preflight_evidence"] == record.bound_completion_event["cost_preflight_evidence"]
    assert surface.lineage_summary["approval_evidence"] == record.bound_completion_event["approval_evidence"]


def test_104p_surface_does_not_dump_raw_private_evidence():
    surface = build_async_result_surface(
        accepted_record(
            completion_payload_summary={
                "original_request_evidence": {"secret": "value"},
                "approval_evidence": {"token": "private"},
            }
        )
    )

    assert surface is not None
    text = render_async_result_surface_text(surface)
    assert "original_request_evidence" not in text
    assert "approval_evidence" not in text
    assert "cost_preflight_evidence" not in text
    assert "packet" not in text


def test_104p_action_options_are_local_only_and_create_no_authority():
    surface = build_async_result_surface(accepted_record())

    assert surface is not None
    for option in surface.action_options:
        assert option.local_only is True
        assert option.creates_authority is False


def test_104p_request_followup_option_does_not_create_delegation():
    surface = build_async_result_surface(accepted_record())
    followup = next(option for option in surface.action_options if option.action_kind == "request_followup")

    assert surface is not None
    assert followup.label == "Pedir seguimiento"
    assert followup.creates_authority is False
    assert followup.local_only is True


def test_104p_telegram_envelope_is_local_and_send_disallowed():
    surface = build_async_result_surface(accepted_record())
    assert surface is not None

    envelope = build_async_result_message_envelope(surface)

    assert envelope.channel == "telegram"
    assert envelope.send_allowed is False
    assert envelope.recipient_owner_id == surface.owner_id
    assert envelope.robot_id == surface.robot_id
    assert "Resultado listo" in envelope.text


def test_104p_no_telegram_send_or_external_dispatch_occurs():
    text = SURFACE_PATH.read_text()

    assert ASYNC_RESULT_SURFACE_STAGE == "104P"
    for forbidden in [
        "send_message",
        "delegate_task",
        "asyncio.create_task",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "subprocess",
    ]:
        assert forbidden not in text


def test_104p_no_memory_center_mutation_occurs():
    text = SURFACE_PATH.read_text()

    assert "memory_center" not in text
    assert "mutate" not in text
    assert "writeback" not in text


def test_104p_no_action_packet_or_approval_is_created():
    text = SURFACE_PATH.read_text()

    for forbidden in [
        "create_action_packet",
        "submit_action_packet_for_approval",
        "apply_action_packet_decision",
        "bind_async_delegation_approval",
    ]:
        assert forbidden not in text


def test_104p_regression_103p_inbox_still_passes():
    record = accepted_record()

    assert record.status == "accepted"
    assert record.bound_completion_event is not None


def test_104p_105p_plus_remains_unauthorized():
    roadmap_text = ROADMAP_PATH.read_text()

    assert "106P and later remain unauthorized" in roadmap_text or "106P+ remains unauthorized" in roadmap_text
