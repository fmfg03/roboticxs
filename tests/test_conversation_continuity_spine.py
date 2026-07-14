from __future__ import annotations

from pathlib import Path
from typing import get_args

from app.budget_authority import BudgetAuthorityRequest
from app.conversation_continuity import (
    ConversationClassification,
    ConversationContinuityRequest,
    ContinuityAuthorityRequest,
    ContinuityItemType,
    NextStepDecision,
    ProactiveInterventionRequest,
    StorageTarget,
    build_continuity_memory_candidate,
    build_daily_start_plan,
    classify_conversation_event,
    evaluate_continuity_authority,
    evaluate_priority_gate,
    evaluate_proactive_intervention,
    export_continuity_candidates,
    PriorityGateRequest,
    DailyStartRequest,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md"


def test_taxonomies_match_66p_contract():
    assert set(get_args(ConversationClassification)) == {
        "CURIOSITY",
        "SIGNAL",
        "CANDIDATE_IDEA",
        "EXECUTION_PRIORITY",
        "ROUTINE",
        "DECISION",
        "OPEN_LOOP",
        "CRISIS_OR_SENSITIVE",
        "CONTEXT_UPDATE",
        "NO_ACTION",
    }
    assert set(get_args(NextStepDecision)) == {
        "NO_ACTION",
        "ANSWER_ONLY",
        "NOTE_PROPOSED",
        "MEMORY_UPDATE_PROPOSED",
        "BACKLOG_ITEM",
        "OPEN_LOOP_CREATED",
        "DECISION_RECORDED",
        "STORY_RECOMMENDED",
        "SPEC_RECOMMENDED",
        "EXECUTION_PLAN",
        "ESCALATE_OR_CONFIRM",
    }
    assert set(get_args(ContinuityItemType)) >= {"FACT", "PREFERENCE", "INFERENCE", "STRATEGIC_OPINION"}
    assert set(get_args(StorageTarget)) == {
        "EXISTING_MEMORY_PROPOSAL_FLOW",
        "FUTURE_CRITERIO_STORE",
        "SESSION_ONLY",
        "DO_NOT_STORE",
    }


def test_exploratory_repo_message_is_curiosity_or_signal():
    result = classify_conversation_event(
        ConversationContinuityRequest(raw_text="Mira este repo, nos sirve para algo?")
    )

    assert result.classification in {"CURIOSITY", "SIGNAL"}
    assert result.next_step_decision == "ANSWER_ONLY"


def test_curiosity_does_not_create_task_story_spec_or_roadmap_item():
    result = classify_conversation_event(
        ConversationContinuityRequest(raw_text="Mira este paper, que opinas de esta herramienta?")
    )

    assert result.classification == "CURIOSITY"
    assert result.next_step_decision not in {
        "BACKLOG_ITEM",
        "STORY_RECOMMENDED",
        "SPEC_RECOMMENDED",
        "OPEN_LOOP_CREATED",
    }
    assert result.memory_candidate is None
    assert result.priority_gate_result is None
    assert result.external_execution_authorized is False


def test_candidate_idea_defaults_to_backlog_unless_priority_criteria_are_met():
    result = classify_conversation_event(
        ConversationContinuityRequest(raw_text="Esto podria servir para Roboticxs, pero es otro repo para investigar.")
    )

    assert result.classification == "CANDIDATE_IDEA"
    assert result.next_step_decision == "BACKLOG_ITEM"
    assert result.priority_gate_result is not None
    assert result.priority_gate_result.classification == "BACKLOG"
    assert result.priority_gate_result.recommendation == "Not now. Backlog."
    assert "Do not open GitHub" in result.priority_gate_result.do_not_do_now


def test_active_client_payment_or_deadline_message_becomes_execution_priority():
    result = classify_conversation_event(
        ConversationContinuityRequest(
            raw_text="Victor ya pidio factura y cuenta bancaria para cerrar el pago del cliente.",
            cash_or_client_pressure_present=True,
        )
    )

    assert result.classification == "EXECUTION_PRIORITY"
    assert result.next_step_decision == "EXECUTION_PLAN"
    assert result.daily_start_plan is not None
    assert result.priority_gate_result is not None
    assert result.priority_gate_result.classification == "PRIORITY"


def test_que_hago_hoy_produces_limited_daily_start_plan():
    result = classify_conversation_event(
        ConversationContinuityRequest(
            raw_text="Que hago hoy?",
            known_open_loops=("Enviar factura a Victor", "Revisar propuesta Roboticxs"),
            known_priorities=("Cerrar pago de cliente activo", "Actualizar demo"),
            active_projects=("nuevo repo interesante",),
            cash_or_client_pressure_present=True,
        )
    )

    assert result.classification == "EXECUTION_PRIORITY"
    assert "DAILY_START" in result.secondary_labels
    assert result.daily_start_plan is not None
    assert result.daily_start_plan.starting_priority == "Cerrar pago de cliente activo"
    assert len(result.daily_start_plan.commitments) <= 3


def test_daily_start_includes_first_action_transition_distractions_and_backlog_parking():
    plan = build_daily_start_plan(
        DailyStartRequest(
            known_priorities=("Preparar entrega de cliente",),
            known_open_loops=("Confirmar cuenta bancaria",),
            non_urgent_backlog=("investigar paper nuevo",),
        )
    )

    assert plan.first_concrete_action
    assert plan.transition_to_next_block
    assert plan.distractions_to_avoid
    assert "papers or tool research" in plan.distractions_to_avoid
    assert plan.backlog_parking == ("investigar paper nuevo",)
    assert len(plan.commitments) <= 3


def test_reflective_message_can_resolve_to_no_action():
    result = classify_conversation_event(
        ConversationContinuityRequest(raw_text="Hoy solo estoy pensando en todo esto sin decidir nada.")
    )

    assert result.classification == "NO_ACTION"
    assert result.next_step_decision == "NO_ACTION"
    assert result.memory_candidate is None


def test_sensitive_inference_requires_label_and_confirmation():
    result = evaluate_continuity_authority(
        ContinuityAuthorityRequest(
            item_type="INFERENCE",
            authority_level="SYSTEM_INFERENCE",
            sensitivity_level="SENSITIVE",
            allowed_influence_scope="PLANNING",
            uses_sensitive_context=True,
            confirmation_present=False,
        )
    )

    assert result.decision == "ASK_CONFIRMATION"
    assert result.label_required is True
    assert result.confirmation_required is True
    assert result.allowed_to_store is False
    assert result.allowed_to_influence_planning is False


def test_strategic_opinion_is_not_treated_as_fact():
    result = evaluate_continuity_authority(
        ContinuityAuthorityRequest(
            item_type="STRATEGIC_OPINION",
            authority_level="STRATEGIC_RECOMMENDATION",
            sensitivity_level="LOW",
            allowed_influence_scope="PRIORITY_GATING",
        )
    )

    assert result.decision == "ALLOW_WITH_LABEL"
    assert result.label_required is True
    assert "not presented as fact" in result.reason
    assert result.allowed_to_store is False


def test_confirmed_preference_may_influence_tone_only_within_scope():
    result = evaluate_continuity_authority(
        ContinuityAuthorityRequest(
            item_type="PREFERENCE",
            authority_level="USER_CONFIRMED",
            sensitivity_level="LOW",
            allowed_influence_scope="TONE_ONLY",
            confirmation_present=True,
        )
    )

    assert result.decision == "ALLOW"
    assert result.allowed_to_store is True
    assert result.allowed_to_influence_planning is False
    assert result.allowed_to_trigger_proactive_intervention is False


def test_proactive_intervention_requires_evidence():
    no_evidence = evaluate_proactive_intervention(ProactiveInterventionRequest(confirmation_present=True))
    with_evidence = evaluate_proactive_intervention(
        ProactiveInterventionRequest(repeated_dispersion=True, confirmation_present=True)
    )

    assert no_evidence.eligible is False
    assert no_evidence.classification == "PROACTIVE_NOT_ELIGIBLE"
    assert with_evidence.eligible is True
    assert with_evidence.classification == "PROACTIVE_ELIGIBLE"
    assert with_evidence.authority_label == "[Inference]"


def test_sensitive_proactive_intervention_needs_confirmation():
    result = evaluate_proactive_intervention(
        ProactiveInterventionRequest(repeated_bottleneck=True, uses_sensitive_context=True)
    )

    assert result.eligible is False
    assert result.authority_result.decision == "ESCALATE"
    assert result.authority_result.confirmation_required is True


def test_priority_gate_blocks_dispersion():
    result = evaluate_priority_gate(
        PriorityGateRequest(
            message="Abramos este repo y paper nuevo.",
            core_product_relevance=True,
            dispersion_risk=True,
        )
    )

    assert result.classification == "BACKLOG"
    assert result.recommendation == "Not now. Backlog."
    assert "Do not open GitHub" in result.do_not_do_now


def test_continuity_memory_candidate_supports_future_criterio_store():
    candidate = build_continuity_memory_candidate(
        content="The user may prefer cash/client work before research.",
        item_type="OPERATING_PATTERN",
        reason="Rich criterio belongs to the future criterio store.",
        authority_level="SYSTEM_INFERENCE",
        storage_target="FUTURE_CRITERIO_STORE",
        allowed_influence_scope="PRIORITY_GATING",
    )

    assert candidate.storage_target == "FUTURE_CRITERIO_STORE"
    assert candidate.confirmation_required is True
    assert candidate.confirmed_by_user is False


def test_existing_memory_proposal_flow_is_the_only_durable_memory_target_in_66p():
    fact = build_continuity_memory_candidate(
        content="Victor asked for an invoice.",
        item_type="FACT",
        reason="Simple user-stated fact.",
        authority_level="USER_STATED",
        storage_target="EXISTING_MEMORY_PROPOSAL_FLOW",
    )
    sensitive = build_continuity_memory_candidate(
        content="This may be a health-related pattern.",
        item_type="INFERENCE",
        reason="Sensitive inference cannot be stored directly.",
        authority_level="SYSTEM_INFERENCE",
        sensitivity_level="SENSITIVE",
        storage_target="DO_NOT_STORE",
    )

    assert fact.storage_target == "EXISTING_MEMORY_PROPOSAL_FLOW"
    assert sensitive.storage_target == "DO_NOT_STORE"
    assert sensitive.confirmation_required is True


def test_export_separates_candidate_types_for_readiness():
    candidates = (
        build_continuity_memory_candidate(
            content="Invoice requested.",
            item_type="FACT",
            reason="User-stated fact.",
            authority_level="USER_STATED",
        ),
        build_continuity_memory_candidate(
            content="User may be over-researching.",
            item_type="INFERENCE",
            reason="System inference.",
            authority_level="SYSTEM_INFERENCE",
        ),
        build_continuity_memory_candidate(
            content="Do cash before research.",
            item_type="STRATEGIC_OPINION",
            reason="Strategic recommendation.",
            authority_level="STRATEGIC_RECOMMENDATION",
        ),
        build_continuity_memory_candidate(
            content="Send proposal.",
            item_type="OPEN_LOOP",
            reason="Open loop.",
            authority_level="USER_STATED",
        ),
    )

    exported = export_continuity_candidates(candidates)

    assert exported["facts"] == [candidates[0]]
    assert exported["inferences"] == [candidates[1]]
    assert exported["strategic_recommendations"] == [candidates[2]]
    assert exported["open_loops"] == [candidates[3]]


def test_external_execution_is_always_false():
    result = classify_conversation_event(
        ConversationContinuityRequest(raw_text="Envia el WhatsApp al cliente y cierra el pago.")
    )

    assert result.classification == "EXECUTION_PRIORITY"
    assert result.external_execution_authorized is False


def test_budget_guard_can_defer_future_stage_continuity_work():
    result = classify_conversation_event(
        ConversationContinuityRequest(
            raw_text="Haz sintesis continua historica de todas mis conversaciones.",
            budget_context={"future_stage_requested": True},
        )
    )

    assert result.budget_decision is not None
    assert result.budget_decision.task_class == "CONVERSATION_CONTINUITY_FUTURE"
    assert result.budget_decision.decision == "DEFER"
    assert result.next_step_decision == "ESCALATE_OR_CONFIRM"


def test_budget_guard_caps_high_cost_long_context_continuity_work():
    result = classify_conversation_event(
        ConversationContinuityRequest(
            raw_text="Sintetiza un contexto largo para continuidad.",
            budget_context=BudgetAuthorityRequest(
                task_class="GENERAL_TASK",
                estimated_input_tokens=24_000,
                estimated_output_tokens=1_000,
                requires_long_context=True,
            ),
        )
    )

    assert result.budget_decision is not None
    assert result.budget_decision.decision == "ALLOW_WITH_CAP"
    assert result.budget_decision.cap_applied is True


def test_documentation_states_67p_owns_memory_stack_architecture():
    text = DOC_PATH.read_text()

    assert "Zaubern governs the authority surface of personal continuity" in text
    assert "67P owns Memory Stack Architecture / Criterio Store Spec" in text
    assert "does not decide where long-term criterio is stored" in text
    assert "does not add database writes" in text
    assert "external_execution_authorized` is always false" in text
