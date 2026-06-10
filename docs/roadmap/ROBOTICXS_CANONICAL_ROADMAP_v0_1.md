# Roboticxs Canonical Roadmap v0.1

## Purpose

This document materializes the maintainer-approved forward-looking roadmap for Roboticxs.

It is the controlling roadmap for future stage sequencing after Stage 66P. It does not authorize implementation, replace runtime truth, or claim that future sequence entries are implemented locally.

## Source of authority

The forward sequence comes from explicit maintainer direction in the maintainer-approved ChatGPT/web planning thread. Local repository evidence is authoritative only for stages confirmed in the repository.

```json canonical-roadmap-authority
{
  "authority_source":"maintainer_approved_chatgpt_web_planning_thread",
  "local_evidence_scope":"stages_61P_through_66P",
  "forward_sequence_source":"explicit_maintainer_direction",
  "runtime_truth_source":"local_repo",
  "roadmap_inclusion_authorizes_implementation":false
}
```

## Local evidence baseline

The repository confirms these fixed baselines:

- 61P consolidated explicit command routing without adding product behavior.
- 62P created the canonical runtime surface audit.
- 63P froze retrieval-control as local metadata/control-only behavior.
- 64P materialized the canonical roadmap.
- 65P added the Budget Awareness / Cost Authority Guard v0.
- 66P adds the Conversation Continuity Spine v0 as a pure local continuity contract.

No local implementation evidence is claimed for stages 67P–76P.

## Canonical stage registry

```json canonical-stage-registry
[
  {"stage_id":"61P","stage_name":"Command Routing Consolidation v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"c079a96","paths":["docs/reference/COMMAND_ROUTING_CONSOLIDATION_v0_1.md"]},"implementation_authorized":false,"next_action":"Do not reopen except through a separately approved bug or boundary-correction stage."},
  {"stage_id":"62P","stage_name":"Runtime Surface Audit v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"93bcbff","paths":["docs/reference/RUNTIME_SURFACE_AUDIT_v0_1.md"]},"implementation_authorized":false,"next_action":"Use as the source of truth for the audited runtime surface."},
  {"stage_id":"63P","stage_name":"Retrieval Control Freeze v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"86afd53","paths":["docs/reference/RETRIEVAL_CONTROL_FREEZE_v0_1.md"]},"implementation_authorized":false,"next_action":"Keep retrieval-control frozen unless a separately approved stage reopens it."},
  {"stage_id":"64P","stage_name":"Roadmap Canon Materialization v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"2b3c295","paths":["docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Do not reopen except through a separately approved roadmap-canon correction."},
  {"stage_id":"65P","stage_name":"Budget Awareness / Cost Authority Guard v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"d346939","paths":["app/budget_authority.py","docs/reference/BUDGET_AUTHORITY_GUARD_v0_1.md","tests/test_budget_authority_guard.py"]},"implementation_authorized":false,"next_action":"Use as the source of truth for budget authority gating."},
  {"stage_id":"66P","stage_name":"Conversación Horizontal / Continuity Spine v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_66P_closeout","paths":["app/conversation_continuity.py","docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md","tests/test_conversation_continuity_spine.py"]},"implementation_authorized":false,"next_action":"Use as the local continuity-spine baseline and do not reopen except through a separately approved correction stage."},
  {"stage_id":"66P2","stage_name":"Memory Stack Architecture / Criterio Store Spec","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_66P2_closeout","paths":["docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md","tests/test_memory_stack_architecture.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the memory architecture boundary for continuity and criterio; no storage implementation is authorized."},
  {"stage_id":"67P","stage_name":"Caregiver Mode Boundary Spec","status":"NEXT_ELIGIBLE","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Eligible for story drafting only after 66P2 closes."},
  {"stage_id":"68P","stage_name":"Caregiver Telegram Group Relay v0","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"69P","stage_name":"Guided Routine Packets v0","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"70P","stage_name":"Voice Notes Intelligence / VibeVoice Spike","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"71P","stage_name":"Voice Intake for Caregiver Routines","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"72P","stage_name":"Research Radar / Last30Days Skill","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"73P","stage_name":"Understand-Anything + codegraph Factory Skill","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain unopened until prior sequence gates close or explicit maintainer direction changes the canon."},
  {"stage_id":"75P","stage_name":"Agent-Reach Research Parking Lot","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain a research parking-lot sequence entry without runtime authorization."},
  {"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"SEQUENCE_ENTRY_ONLY","authority_source":"explicit_maintainer_direction","local_evidence":null,"implementation_authorized":false,"next_action":"Remain a research parking-lot sequence entry without runtime authorization."}
]
```

## Canonical product-spine stage

CH-01 is materialized as Stage 66P, a foundational product-spine baseline. It is additive and does not authorize storage, connectors, retrieval, browser/email/WhatsApp behavior, CRM, lead-gen, handoff, external writes, caregiver behavior, voice behavior, or Research Radar.

```json canonical-product-spine-stage
{
  "spine_id":"CH-01",
  "stage_id":"66P",
  "stage_name":"Conversación Horizontal / Continuity Spine v0",
  "status":"COMPLETED_FIXED_BASELINE",
  "rationale":"Defines continuity across conversations before later caregiver, voice, research, and advanced-skill stages.",
  "scope_signals":[
    "conversation_classification",
    "selective_notes",
    "user_criterio",
    "priority_gate",
    "que_hago_hoy_mode",
    "proactive_intervention_rules",
    "cross_topic_synthesis",
    "next_step_resolver",
    "zaubern_authority_checks"
  ],
  "implementation_authorized":false,
  "baseline_paths":[
    "app/conversation_continuity.py",
    "docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md",
    "tests/test_conversation_continuity_spine.py"
  ],
  "next_stage":"66P2"
}
```

## 66P2 continuation stage

66P2 is a continuation of 66P, not a feature expansion. It defines the memory architecture boundary for continuity and criterio.

Allowed scope:

- story/spec for memory architecture;
- docs/tests only by default;
- inventory existing memory surfaces;
- map `ContinuityMemoryCandidate` from 66P to current and future storage targets;
- define authority, sensitivity, confirmation, expiration, export, deletion, and influence rules.

Forbidden scope:

- no storage migration;
- no new backend;
- no Mirix implementation;
- no vector store;
- no graph store;
- no external retrieval;
- no connector;
- no caregiver behavior.

## Stage 66P completion transition

The stage registry records the 66P closeout sequence state. Stage 66P2 is the sole next eligible stage after 66P.

```json stage-66p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"66P2",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 66P closeout does not authorize memory storage implementation. It permits 66P2 story and technical-spec drafting only.

## Stage 66P2 completion transition

The stage registry records the 66P2 closeout sequence state. Stage 67P is the sole next eligible stage after 66P2.

```json stage-66p2-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"67P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 66P2 closeout does not authorize memory storage implementation, Mirix, retrieval, connectors, or caregiver behavior. It permits 67P story drafting only.

## Sequencing and authorization rules

```json roadmap-sequencing-rules
[
  "exactly_one_stage_may_be_next_eligible",
  "sole_next_eligible_stage_is_67P",
  "eligibility_permits_story_drafting_only",
  "roadmap_inclusion_never_authorizes_implementation",
  "every_stage_requires_story_approval",
  "every_stage_requires_technical_spec_approval",
  "runtime_implementation_requires_separately_approved_scoped_build_tests_and_validation",
  "stages_68P_through_76P_remain_unopened_until_67P_closes_or_explicit_maintainer_direction_changes_the_canon",
  "sequence_changes_require_explicit_maintainer_approval_and_canonical_roadmap_update",
  "external_repositories_and_recent_planning_threads_cannot_independently_change_sequence"
]
```

## Deferred-candidate registry

Deferred and radar candidates require future story approval and technical-spec approval. They are not runtime base or implementation authorization.

```json deferred-candidate-registry
[
  {"candidate_id":"connector_architecture","name":"Connector architecture","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","authority_and_data_boundary_design","scoped_build_tests_and_validation"],"implementation_authorized":false},
  {"candidate_id":"live_retrieval","name":"Live retrieval","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","63P_freeze_reopening_approval","connector_authority_design"],"implementation_authorized":false},
  {"candidate_id":"browser_email_whatsapp_execution","name":"Browser, email, or WhatsApp execution","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","external_action_authority_design","approval_packet_enforcement"],"implementation_authorized":false},
  {"candidate_id":"external_skills","name":"External skills","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","supply_chain_and_authority_review","scoped_build_tests_and_validation"],"implementation_authorized":false},
  {"candidate_id":"agent_reach","name":"Agent-Reach","classification":"PARKING_LOT","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","external_action_boundary_review"],"implementation_authorized":false},
  {"candidate_id":"voxcpm","name":"VoxCPM","classification":"PARKING_LOT","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","voice_strategy_decision","privacy_and_authority_review"],"implementation_authorized":false}
]
```

## Blocked-v0 registry

Blocked-v0 behavior remains blocked even when related work appears in the sequence or deferred registry.

```json canonical-blocked-v0-registry
[
  {"blocked_id":"total_autonomy","behavior":"Total autonomy","reason":"Roboticxs v0 remains user-controlled and bounded.","reopen_requirements":["explicit_product_boundary_change","story_and_spec_approval","authority_model_review"],"implementation_authorized":false},
  {"blocked_id":"continuous_screen_tracking","behavior":"Continuous screen tracking","reason":"Continuous observation exceeds the approved v0 privacy and authority boundary.","reopen_requirements":["explicit_product_boundary_change","privacy_review","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"authenticated_scraping","behavior":"Scraping with login or cookies","reason":"Credentialed scraping and session authority are outside v0.","reopen_requirements":["explicit_product_boundary_change","credential_and_connector_architecture","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"automatic_publishing_or_direct_messages","behavior":"Automatic publishing or direct messages","reason":"External communication requires explicit authority not present in v0.","reopen_requirements":["explicit_product_boundary_change","approval_packet_enforcement","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"cloned_voice","behavior":"Cloned voice","reason":"Voice cloning is outside the approved v0 privacy and identity boundary.","reopen_requirements":["explicit_product_boundary_change","identity_and_privacy_review","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"external_action_without_approval_packet","behavior":"External action without approval packet","reason":"Nothing important may happen externally without explicit user approval.","reopen_requirements":["not_reopenable_within_v0"],"implementation_authorized":false},
  {"blocked_id":"connector_activation","behavior":"Connector activation","reason":"No connector architecture or activation authority is approved in v0.","reopen_requirements":["explicit_product_boundary_change","connector_architecture_approval","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"live_retrieval_execution","behavior":"Live retrieval execution","reason":"Stage 63P freezes retrieval-control as metadata and control only.","reopen_requirements":["63P_freeze_reopening_approval","connector_architecture_approval","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"browser_email_whatsapp_execution","behavior":"Browser, email, or WhatsApp execution","reason":"These external execution surfaces are outside v0.","reopen_requirements":["explicit_product_boundary_change","external_action_authority_design","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"crm_lead_pipeline_handoff","behavior":"CRM, lead generation, pipeline, or handoff","reason":"Roboticxs is a personal robot, not Agentius or a commercial pipeline product.","reopen_requirements":["not_reopenable_within_roboticxs_v0"],"implementation_authorized":false},
  {"blocked_id":"external_writes","behavior":"External writes","reason":"External writes require authority and connector architecture not present in v0.","reopen_requirements":["explicit_product_boundary_change","connector_and_external_action_authority_design","story_and_spec_approval"],"implementation_authorized":false}
]
```

## Reopening and change control

Roadmap inclusion is not implementation approval. Every stage requires story approval, technical-spec approval, scoped implementation approval, tests, and validation.

Sequence changes require explicit maintainer approval and an update to this canonical roadmap. External repositories, planning threads, and historical documents cannot independently change the sequence.

## Non-claims

- no feature work
- no connectors
- no live retrieval
- no browser/email/WhatsApp execution
- no caregiver implementation
- no voice implementation
- no Research Radar implementation
- no external skills
- no CRM
- no lead-gen
- no pipeline
- no handoff
- no external writes

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_canonical_roadmap.py`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q tests/test_retrieval_control_freeze.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git diff --check`
- `git status --short`
