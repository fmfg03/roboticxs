# Memory Stack Architecture / Criterio Store Spec v0.1

## Purpose

Stage 66P2 defines the Roboticxs memory architecture boundary after the 66P Conversation Continuity Spine.

66P2 is a continuation of 66P, not a feature expansion. It answers where continuity and criterio concepts should live before Caregiver Mode opens. It does not implement new storage, Mirix, vector memory, graph memory, embeddings, schema migration, connector retrieval, cross-thread retrieval, caregiver behavior, voice behavior, Research Radar, CRM, lead-gen, handoff, or external writes.

Roboticxs runs on Hermes Agent. Hermes is the runtime base, but this repo only confirms the local Roboticxs memory flow implemented around `ProposedMemory`, `MemoryItem`, approval, rejection, pending review, active listing, and forget behavior. Rich criterio support in Hermes remains unverified until a future inspection proves otherwise.

Core principle:

```text
Memory is not only storage. Memory is authority.
```

Canonical authority principle:

```text
Zaubern governs the authority surface of personal continuity.
```

## Current Memory Inventory

Confirmed from local repo inspection:

- `app.models.ProposedMemory` stores pending memory proposals with `PENDING`, `APPROVED`, `REJECTED`, and `EXPIRED` status paths.
- `app.models.MemoryItem` stores active local memories with `ACTIVE` and `FORGOTTEN` status paths.
- `app.memory_service` creates proposals, expires pending proposals, approves proposals into `MemoryItem`, and rejects proposals.
- `app.memory_control` lists active memories and marks active memories forgotten.
- `tests/test_memory_control.py` confirms approval, rejection, pending review, listing isolation, active-only memory use, and forget behavior.

Inferred but not confirmed as rich criterio support:

- Hermes runtime may provide persistence primitives as the runtime base.
- Hermes memory should not be treated as typed criterio, influence-scoped memory, export grouping, expiration, or graph-like relationship memory until verified locally.

Unknown:

- Whether Hermes can natively enforce authority metadata, confirmation state, deletion policy, influence scope, or caregiver-sensitive memory boundaries without Roboticxs-specific architecture.

## Architecture Decision

66P2 classifies continuity memory into four storage lanes:

```text
EXISTING_HERMES_MEMORY
CURRENT_ROBOTICXS_MEMORY_FLOW
FUTURE_CRITERIO_STORE
SESSION_ONLY_OR_DO_NOT_STORE
```

Current durable user-approved memory remains the existing Roboticxs memory proposal flow. Future Criterio Store and Mirix-like architectures are not implemented or authorized by 66P2.

```json memory-authority-policy
{
  "runtime_base": "Hermes Agent",
  "existing_memory_is_authoritative_only_where_verified": true,
  "memory_is_authority_surface": true,
  "user_approval_required_for_durable_sensitive_memory": true,
  "system_inference_is_never_confirmed_fact": true,
  "mirix_implementation_authorized": false,
  "new_storage_authorized": false,
  "caregiver_behavior_authorized": false,
  "external_retrieval_authorized": false,
  "connector_authorized": false,
  "browser_email_whatsapp_authorized": false,
  "crm_lead_gen_handoff_authorized": false,
  "external_writes_authorized": false
}
```

## Storage Lane Registry

```json storage-lane-registry
[
  {
    "lane_id": "EXISTING_HERMES_MEMORY",
    "description": "Runtime-native Hermes memory or persistence capabilities, only where verified by local runtime inspection.",
    "allowed_item_classes": ["FACT", "PREFERENCE", "PROJECT_CONTEXT", "BOUNDARY"],
    "forbidden_item_classes": ["INFERENCE", "SYNTHESIS", "PRIORITY_GATE_DECISION", "DAILY_START_CONTEXT", "CAREGIVER_CONTEXT_FUTURE"],
    "authority_requirements": ["verified_runtime_capability", "no_rich_criterio_assumption", "no_sensitive_inference_as_fact"],
    "implementation_status": "EXISTING_NEEDS_VERIFICATION",
    "reopen_requirements": ["local_Hermes_memory_capability_audit", "authority_metadata_mapping", "tests_before_runtime_use"]
  },
  {
    "lane_id": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "description": "Existing user-approved ProposedMemory to MemoryItem flow with pending, approve, reject, list, and forget behavior.",
    "allowed_item_classes": ["FACT", "PREFERENCE", "PROJECT_CONTEXT", "OPEN_LOOP", "DECISION", "BOUNDARY", "COMMUNICATION_STYLE"],
    "forbidden_item_classes": ["SENSITIVE_HEALTH_CONTEXT", "UNCONFIRMED_INFERENCE", "SYNTHESIS", "CAREGIVER_CONTEXT_FUTURE"],
    "authority_requirements": ["user_approval_preserved", "reject_preserved", "forget_preserved", "system_inference_not_confirmed_fact"],
    "implementation_status": "EXISTING_CONFIRMED",
    "reopen_requirements": ["separate_story", "technical_spec", "migration_review_if_fields_change", "approval_flow_tests"]
  },
  {
    "lane_id": "FUTURE_CRITERIO_STORE",
    "description": "Future architecture for structured criterio, authority-scoped inferences, synthesis, priority decisions, Daily Start history, influence scope, expiration, and export grouping.",
    "allowed_item_classes": ["GOAL", "VALUE", "RISK", "OPERATING_PATTERN", "INFERENCE", "STRATEGIC_OPINION", "SYNTHESIS", "PRIORITY_GATE_DECISION", "DAILY_START_CONTEXT", "CAREGIVER_CONTEXT_FUTURE"],
    "forbidden_item_classes": ["BLOCKED_DATA", "NEVER_STORE_CAREGIVER_DATA", "UNCONFIRMED_SENSITIVE_INFERENCE_AS_CONFIRMED"],
    "authority_requirements": ["future_design_required", "confirmation_status_required", "expiration_policy_required", "export_delete_required", "influence_scope_enforced"],
    "implementation_status": "ARCHITECTURE_ONLY",
    "reopen_requirements": ["approved_story", "approved_technical_spec", "storage_design", "migration_plan", "authority_tests", "rollback_plan"]
  },
  {
    "lane_id": "SESSION_ONLY_OR_DO_NOT_STORE",
    "description": "Ephemeral synthesis, low-authority material, unconfirmed sensitive inference, blocked data, and anything the user says not to remember or not to use for decisions.",
    "allowed_item_classes": ["INFERENCE", "SYNTHESIS", "DAILY_START_CONTEXT", "CAREGIVER_CONTEXT_FUTURE", "LOW_AUTHORITY_SIGNAL"],
    "forbidden_item_classes": ["CONFIRMED_FACT_DURABLE_STORAGE", "USER_CONFIRMED_PREFERENCE_DURABLE_STORAGE"],
    "authority_requirements": ["non_durable_by_default", "confirmation_gate_for_sensitive_use", "blocked_data_not_stored", "do_not_use_for_decisions_respected"],
    "implementation_status": "BLOCKED_FOR_DURABLE_STORAGE",
    "reopen_requirements": ["explicit_user_confirmation", "future_authority_review", "sensitivity_review", "deletion_and_export_policy"]
  }
]
```

## Continuity Item Storage Map

```json continuity-item-storage-map
[
  {
    "item_class": "FACT",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "NONE",
    "allowed_influence_scope": ["PLANNING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_fact",
    "deletion_policy": "forget_marks_memory_forgotten",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Low-risk user-stated facts can use current proposal approval flow."
  },
  {
    "item_class": "PREFERENCE",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_CONFIRMED",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["TONE_ONLY", "PLANNING", "EXPORT_ONLY"],
    "export_policy": "export_as_preference",
    "deletion_policy": "forget_marks_memory_forgotten",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Preferences may influence tone or planning only within approved scope."
  },
  {
    "item_class": "GOAL",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["PLANNING", "PRIORITY_GATING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_goal",
    "deletion_policy": "future_delete_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Goals need status, influence scope, and reconfirmation beyond current flat memory."
  },
  {
    "item_class": "VALUE",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "USER_CONFIRMED",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["PLANNING", "PRIORITY_GATING", "EXPORT_ONLY"],
    "export_policy": "export_as_value",
    "deletion_policy": "future_delete_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Values are high-influence criterio and need explicit confirmation."
  },
  {
    "item_class": "RISK",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "STALE_AFTER_DAYS",
    "allowed_influence_scope": ["PLANNING", "PRIORITY_GATING", "PROACTIVE_INTERVENTION", "EXPORT_ONLY"],
    "export_policy": "export_as_risk",
    "deletion_policy": "future_delete_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Risk memory can influence priorities only with authority and freshness controls."
  },
  {
    "item_class": "OPERATING_PATTERN",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "SYSTEM_INFERENCE",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["PRIORITY_GATING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_inference",
    "deletion_policy": "future_delete_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Operating patterns are inference-like and cannot become confirmed fact."
  },
  {
    "item_class": "COMMUNICATION_STYLE",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_CONFIRMED",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["TONE_ONLY", "EXPORT_ONLY"],
    "export_policy": "export_as_preference",
    "deletion_policy": "forget_marks_memory_forgotten",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Communication style may affect tone only."
  },
  {
    "item_class": "PROJECT_CONTEXT",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "STALE_AFTER_DAYS",
    "allowed_influence_scope": ["PLANNING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_project_context",
    "deletion_policy": "forget_marks_memory_forgotten",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Basic project context can use existing approval flow when low-risk."
  },
  {
    "item_class": "OPEN_LOOP",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "STALE_AFTER_DAYS",
    "allowed_influence_scope": ["PLANNING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_open_loop",
    "deletion_policy": "forget_or_close_loop_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Simple open commitments can be proposed, but lifecycle state needs future design."
  },
  {
    "item_class": "DECISION",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_STATED",
    "confirmation_required": true,
    "expiration_policy": "NONE",
    "allowed_influence_scope": ["PLANNING", "PRIORITY_GATING", "EXPORT_ONLY"],
    "export_policy": "export_as_decision",
    "deletion_policy": "forget_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Decisions may be proposed as memory but must preserve approval and revocation."
  },
  {
    "item_class": "INFERENCE",
    "default_storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "authority_level": "SYSTEM_INFERENCE",
    "confirmation_required": true,
    "expiration_policy": "SESSION",
    "allowed_influence_scope": ["MEMORY_PROPOSAL_ONLY", "DO_NOT_USE_FOR_DECISIONS", "EXPORT_ONLY"],
    "export_policy": "export_as_inference_if_retained",
    "deletion_policy": "discard_or_reject_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Inference cannot map directly to confirmed durable memory."
  },
  {
    "item_class": "STRATEGIC_OPINION",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "STRATEGIC_RECOMMENDATION",
    "confirmation_required": true,
    "expiration_policy": "STALE_AFTER_DAYS",
    "allowed_influence_scope": ["PRIORITY_GATING", "PLANNING", "EXPORT_ONLY"],
    "export_policy": "export_as_strategic_recommendation",
    "deletion_policy": "future_delete_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Strategic opinion must be labeled and never treated as fact."
  },
  {
    "item_class": "SYNTHESIS",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "LOW_AUTHORITY_SIGNAL",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["MEMORY_PROPOSAL_ONLY", "EXPORT_ONLY"],
    "export_policy": "export_as_synthesis",
    "deletion_policy": "future_delete_or_expire_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Synthesis requires future authority metadata or remains session-only."
  },
  {
    "item_class": "PRIORITY_GATE_DECISION",
    "default_storage_lane": "FUTURE_CRITERIO_STORE",
    "authority_level": "STRATEGIC_RECOMMENDATION",
    "confirmation_required": true,
    "expiration_policy": "STALE_AFTER_DAYS",
    "allowed_influence_scope": ["PRIORITY_GATING", "DAILY_START", "EXPORT_ONLY"],
    "export_policy": "export_as_priority_decision",
    "deletion_policy": "future_delete_or_expire_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Priority decision history needs future lifecycle and influence controls."
  },
  {
    "item_class": "DAILY_START_CONTEXT",
    "default_storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "authority_level": "LOW_AUTHORITY_SIGNAL",
    "confirmation_required": false,
    "expiration_policy": "SESSION",
    "allowed_influence_scope": ["DAILY_START", "DO_NOT_USE_FOR_DECISIONS"],
    "export_policy": "export_only_if_promoted_later",
    "deletion_policy": "discard_at_session_end",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Daily Start context is ephemeral unless future Criterio Store explicitly promotes it."
  },
  {
    "item_class": "BOUNDARY",
    "default_storage_lane": "CURRENT_ROBOTICXS_MEMORY_FLOW",
    "authority_level": "USER_CONFIRMED",
    "confirmation_required": true,
    "expiration_policy": "NONE",
    "allowed_influence_scope": ["PLANNING", "PRIORITY_GATING", "PROACTIVE_INTERVENTION", "EXPORT_ONLY"],
    "export_policy": "export_as_boundary",
    "deletion_policy": "forget_or_revoke_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Boundary memory can use current flow when explicit and user-approved."
  },
  {
    "item_class": "CAREGIVER_CONTEXT_FUTURE",
    "default_storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "authority_level": "LOW_AUTHORITY_SIGNAL",
    "confirmation_required": true,
    "expiration_policy": "RECONFIRM_BEFORE_USE",
    "allowed_influence_scope": ["CAREGIVER_FUTURE", "DO_NOT_USE_FOR_DECISIONS"],
    "export_policy": "future_caregiver_export_policy_required",
    "deletion_policy": "future_delete_or_block_required",
    "caregiver_allowed_before_67P": false,
    "mirix_required_now": false,
    "notes": "Caregiver context is mapped for future boundary design only; no runtime use before 67P."
  }
]
```

## Authority Metadata Contract

Every memory-like item must be representable with:

```text
item_id
item_type
content_ref_or_summary
source_event_ref
source_type
authority_level
sensitivity_level
confirmation_status
storage_lane
allowed_influence_scope
expiration_policy
export_group
deletion_policy
audit_required
created_at
updated_at
```

Confirmation status values:

```text
NOT_REQUIRED
PROPOSED_PENDING
CONFIRMED
REJECTED
EXPIRED
REVOKED
```

Expiration policy values:

```text
NONE
SESSION
DATE_BASED
STALE_AFTER_DAYS
RECONFIRM_BEFORE_USE
```

## Mirix / Advanced Memory Evaluation Frame

66P2 does not implement Mirix or a Mirix-like architecture.

```json mirix-evaluation-frame
{
  "decision_status": "DESIGN_CRITERIO_STORE",
  "not_authorized_in_66P2": true,
  "evaluation_criteria": [
    "typed_memory",
    "authority_metadata",
    "source_tracking",
    "confirmation_state",
    "deletion_forget_semantics",
    "export_grouping",
    "influence_scope_enforcement",
    "expiration_reconfirmation",
    "cross_topic_synthesis",
    "relationship_between_facts_open_loops_decisions_and_routines"
  ],
  "minimum_evidence_required": [
    "current_stack_gap_analysis",
    "Hermes_memory_capability_audit",
    "Criterio_Store_design_failure_or_gap",
    "privacy_and_authority_review",
    "migration_and_rollback_plan",
    "testable_delete_export_confirmation_semantics"
  ],
  "blocked_until": "future_approved_memory_architecture_stage"
}
```

## Caregiver Memory Prerequisite

Caregiver Mode cannot use continuity memory until 67P defines its boundary. 66P2 only maps future caregiver memory classes.

```json caregiver-memory-prerequisite
[
  {
    "caregiver_memory_class": "MEDICATION_ADJACENT_ROUTINE",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_medical_or_medication_reminder_runtime",
    "notes": "Requires future caregiver boundary and sensitive-context policy."
  },
  {
    "caregiver_memory_class": "HEARING_AID_ROUTINE",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_caregiver_routine_runtime",
    "notes": "Routine support requires 67P boundary approval."
  },
  {
    "caregiver_memory_class": "FAMILY_SUPERVISION_NOTE",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_family_supervision_or_monitoring",
    "notes": "No supervision behavior is authorized before 67P."
  },
  {
    "caregiver_memory_class": "ROUTINE_COMPLETION_STATE",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_recurring_routine_state_tracking",
    "notes": "Completion state needs future lifecycle and consent rules."
  },
  {
    "caregiver_memory_class": "SENSITIVE_HEALTH_CONTEXT",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED_AND_FUTURE_BOUNDARY_APPROVAL",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_sensitive_health_context_durable_memory",
    "notes": "Sensitive health context must not map to confirmed durable memory without future boundary spec approval."
  },
  {
    "caregiver_memory_class": "ESCALATION_PREFERENCE",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_CONFIRMED",
    "confirmation_required": true,
    "allowed_use_before_67P": false,
    "blocked_behavior": "no_escalation_or_external_contact",
    "notes": "Escalation preferences cannot trigger external messages before authority design."
  },
  {
    "caregiver_memory_class": "NEVER_STORE_CAREGIVER_DATA",
    "storage_lane_before_67P": "SESSION_ONLY_OR_DO_NOT_STORE",
    "required_authority": "USER_STATED",
    "confirmation_required": false,
    "allowed_use_before_67P": false,
    "blocked_behavior": "never_store_and_never_use_for_decisions",
    "notes": "Never-store data remains blocked from durable memory."
  }
]
```

## Non-Authorization

66P2 does not authorize:

- storage migration;
- new backend;
- Mirix implementation;
- vector store;
- graph store;
- embeddings;
- direct memory writes;
- connector retrieval;
- cross-thread retrieval;
- browser, email, or WhatsApp execution;
- caregiver behavior;
- voice behavior;
- Research Radar;
- CRM, lead-gen, pipeline, or handoff;
- external writes.

## Caregiver Readiness Boundary

Before 67P can build caregiver behavior, it must define how caregiver context handles authority, sensitivity, confirmation, expiration, deletion, export, escalation, and never-store rules. 66P2 only provides the memory contract that 67P must respect.
