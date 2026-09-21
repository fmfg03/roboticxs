# Roboticxs Canonical Roadmap v0.2 — Runtime Re-baseline

## Status

**Planning authority only.** This canon changes how future work is selected. It
does not authorize implementation, adoption of a runtime, dependencies, a fork,
a migration, deployment, connectors, or an external action.

## Purpose

Roboticxs must invest in capabilities that make the robot more useful, personal,
proactive, or safe for its user. Generic agent-runtime plumbing is a dependency
concern unless a documented product blocker proves otherwise.

```text
Runtime = dependency
Roboticxs = product
Zaubern = authority
```

The controlling invariants are:

```text
classification != authorization
ABSORBED_BY_NANOBOT != dependency_adopted
```

## Historical preservation and authority transition

`ROBOTICXS_CANONICAL_ROADMAP_v0_1.md` is preserved without alteration as the
historical record of the planning sequence under which stages 1P–226P were
completed or recorded. 226P remains the last historical closeout under v0.1.

This v0.2 document is a new planning authority. It does not reinterpret,
invalidate, delete, or alter historical code, commits, documents, test evidence,
or prior closeouts.

```json canonical-roadmap-v0-2-authority
{
  "packet_type": "RoboticxsCanonicalRoadmapV02",
  "status": "PLANNING_AUTHORITY_ONLY",
  "previous_canon": "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md",
  "previous_canon_preserved": true,
  "historical_terminal_stage": "226P",
  "next_implementation_stage_authorized": false,
  "classification_is_authorization": false,
  "absorbed_by_nanobot_is_dependency_adopted": false,
  "authorized_effects": [
    "future_roadmap_reclassification",
    "future_work_freeze_for_commodity_runtime"
  ],
  "forbidden_effects": [
    "nanobot_install",
    "nanobot_dependency",
    "nanobot_fork",
    "nanobot_migration",
    "hermes_replacement",
    "runtime_change",
    "connector_change",
    "deployment",
    "next_feature_implementation"
  ]
}
```

## Classification contract

Every future roadmap candidate has exactly one classification:

| Classification | Meaning |
| --- | --- |
| `KEEP` | Retain a future planning candidate that is neither commodity runtime nor a product/authority classification candidate. |
| `DELETE` | Remove only the candidate from the future execution plan. Do not delete or alter code, commits, documents, tests, or historical evidence. |
| `ABSORBED_BY_NANOBOT` | Do not reconstruct the capability while the cited upstream candidate sufficiently covers it. This is not technical adoption. |
| `ROBOTICXS_FEATURE` | Product behavior that must produce an observable user outcome and remain above the runtime boundary. |
| `ZAUBERN_BOUNDARY` | Authority, confirmation, action decision, effect proof, or high-consequence governance that belongs outside the runtime. |

`ABSORBED_BY_NANOBOT` is valid only when its referenced
`UpstreamCapabilityEvidenceRecord` identifies an observed ref, a concrete
upstream capability, the reviewed source, a sufficiency assessment, and every
residual product gap. A conceptual resemblance is insufficient.

## Commodity runtime freeze

Do not open future work primarily to build or rebuild these capabilities:

- channels and gateway lifecycle;
- sessions and basic memory persistence;
- cron, heartbeat, and generic scheduling;
- MCP lifecycle and generic provider abstraction;
- generic subagents, shell/files tooling, and base WebUI plumbing.

A change touching runtime is permitted only after a separately approved
`RuntimeBlockerRecord`. It must state the blocked Roboticxs capability, concrete
evidence of the block, alternatives evaluated, why a plugin/adapter/extension
does not resolve it, affected upstream surface, and the human decision required.

```json runtime-blocker-record-schema
{
  "packet_type": "RuntimeBlockerRecord",
  "status": "REQUIRES_SEPARATE_HUMAN_APPROVAL",
  "roboticxs_capability_blocked": "string",
  "blocker_evidence": ["string"],
  "alternatives_evaluated": ["plugin", "adapter", "extension"],
  "why_alternatives_do_not_suffice": "string",
  "upstream_surface_affected": "string",
  "proposed_runtime_change": "string",
  "human_decision_required": true
}
```

## Upstream capability evidence baseline

The following observed baseline is evidence for planning classification only. It
does not add a package, vendor, source checkout, configuration, or runtime
behavior to Roboticxs.

```json upstream-capability-evidence-records
[
  {
    "record_id": "NB-RUNTIME-001",
    "packet_type": "UpstreamCapabilityEvidenceRecord",
    "upstream_repository": "https://github.com/HKUDS/nanobot",
    "observed_ref": "main",
    "observed_commit": "7cede64f078f4435053f4a33964ea719ce582684",
    "reviewed_sources": [
      "docs/architecture.md",
      "docs/concepts.md",
      "docs/automations.md"
    ],
    "capabilities_observed": [
      "channel_message_bus_agent_loop_provider_tool_flow",
      "gateway_and_webui",
      "workspace_scoped_sessions_and_basic_memory",
      "provider_presets_and_routing_fallbacks",
      "mcp_and_tool_registry_lifecycle",
      "cron_heartbeat_and_local_triggers",
      "subagents_shell_files_and_web_tools"
    ],
    "sufficiency_assessment": "Sufficient upstream runtime candidate for planning purposes; operational adoption remains unassessed.",
    "residual_gap": [
      "approved_canonical_memory_and_provenance",
      "skill_manifest_and_scope_guard_semantics",
      "cost_governor_and_budget_authority",
      "allow_draft_only_ask_confirmation_block_decisions",
      "zaubern_effect_authority_and_receipts",
      "Roboticxs_consumer_ux_and_subscription_packaging"
    ],
    "dependency_adopted": false,
    "adoption_authorized": false
  }
]
```

## Reclassified future candidates

The 33P–46P entries below are prior planning candidates, not historical stage
closeouts and not authorized next work. Their classifications provide an
auditable starting inventory for future planning.

```json future-roadmap-classification-registry
[
  {"candidate_id":"33P","candidate_name":"Command Routing Consolidation / Flow Registry Hardening","classification":"DELETE","reason":"Generic routing plumbing is not a future product objective; existing historical evidence remains preserved.","user_observable_outcome":null},
  {"candidate_id":"34P","candidate_name":"ADK Agent Garden Harvest Index","classification":"DELETE","reason":"Framework-pattern harvesting is not a user-visible capability and is superseded by runtime-candidate evaluation.","user_observable_outcome":null},
  {"candidate_id":"35P","candidate_name":"Skill Progressive Disclosure v0","classification":"ROBOTICXS_FEATURE","reason":"Skill packaging and safe consumer discovery remain product semantics above the runtime.","user_observable_outcome":"The user sees which skill can help, its limits, and any required approval."},
  {"candidate_id":"36P","candidate_name":"Robbie Assistance Protocol v0","classification":"ROBOTICXS_FEATURE","reason":"The user-facing help behavior and safe preparation model are product behavior.","user_observable_outcome":"Robbie prepares useful next steps and explains what needs confirmation."},
  {"candidate_id":"37P","candidate_name":"Case / Follow-up Tracker v0","classification":"ROBOTICXS_FEATURE","reason":"Follow-up detection directly contributes to the What did I miss product promise.","user_observable_outcome":"Robbie surfaces a missed commitment from authorized context and proposes a next step."},
  {"candidate_id":"38P","candidate_name":"Claims & Cancellation Prep v0","classification":"ROBOTICXS_FEATURE","reason":"This is a bounded domain Skill Pack, not generic orchestration.","user_observable_outcome":"The user receives a prepared, reviewable claim or cancellation draft."},
  {"candidate_id":"39P","candidate_name":"Scheduled Attention Digest v0","classification":"ROBOTICXS_FEATURE","reason":"Attention prioritization is the product; scheduling remains runtime-provided.","user_observable_outcome":"The user receives a useful daily brief only when authorized context warrants attention."},
  {"candidate_id":"40P","candidate_name":"Google Drive OAuth Connector v0","classification":"ROBOTICXS_FEATURE","reason":"A consented source expands Context Scan; connector transport remains below the product boundary.","user_observable_outcome":"The user can authorize a source and receive concrete memory or action proposals with provenance."},
  {"candidate_id":"41P","candidate_name":"Grounded Document Knowledge Layer v0","classification":"ROBOTICXS_FEATURE","reason":"Document-derived context, provenance, and proposed memory are product outcomes.","user_observable_outcome":"The user can review document-based proposals and their sources before approval."},
  {"candidate_id":"42P","candidate_name":"Operational Workflow Orchestration v0","classification":"ZAUBERN_BOUNDARY","reason":"Cross-system execution and effect governance require an authority boundary, not generic agent orchestration.","user_observable_outcome":"The user sees a bounded proposal and the required confirmation before a consequential action."},
  {"candidate_id":"43P","candidate_name":"Approved Long-Running Workflow v0","classification":"ZAUBERN_BOUNDARY","reason":"Long-running external work needs explicit authority, idempotency, and effect evidence.","user_observable_outcome":"The user can inspect an approved action's status and evidence without silent execution claims."},
  {"candidate_id":"44P","candidate_name":"Connector API Governance v0","classification":"ZAUBERN_BOUNDARY","reason":"Credential, capability, and external-effect authorization are authority concerns.","user_observable_outcome":"The user can understand and control what a connected capability may do."},
  {"candidate_id":"45P","candidate_name":"Robbie Live Companion v0","classification":"ROBOTICXS_FEATURE","reason":"A natural, personal interaction surface is product UX; media runtime is replaceable infrastructure.","user_observable_outcome":"The user can provide approved voice or document input and receive a clear, safe response."},
  {"candidate_id":"46P","candidate_name":"Antojo Cerca de Mí Demo Skill","classification":"DELETE","reason":"A narrow demo does not fit the approved product-priority queue.","user_observable_outcome":null},
  {"candidate_id":"runtime-channels-gateway-sessions","candidate_name":"Generic channels, gateway, and session plumbing","classification":"ABSORBED_BY_NANOBOT","upstream_evidence_record_id":"NB-RUNTIME-001","reason":"Concrete candidate coverage is recorded in NB-RUNTIME-001; no adoption is authorized.","user_observable_outcome":null},
  {"candidate_id":"runtime-cron-mcp-providers-tools","candidate_name":"Generic cron, MCP lifecycle, providers, subagents, and base tools","classification":"ABSORBED_BY_NANOBOT","upstream_evidence_record_id":"NB-RUNTIME-001","reason":"Concrete candidate coverage is recorded in NB-RUNTIME-001; residual Roboticxs governance remains above the runtime.","user_observable_outcome":null}
]
```

## Product planning order

This is an ordered planning queue only. No entry is `NEXT_ELIGIBLE`, and none
authorizes a story, specification, implementation, runtime change, or external
effect without a later explicit approval.

```json product-planning-queue
[
  {"priority":1,"name":"Que se me paso","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"From authorized context, Robbie detects commitments, follow-ups, and attention items, proposes a useful next step, and never acts silently."},
  {"priority":2,"name":"Memory Center with approval and provenance","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"The user can inspect, edit, approve, reject, and forget visible memories with their source."},
  {"priority":3,"name":"Context Scan","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"Authorized email, calendar, documents, and future sources produce concrete, reviewable memory or action proposals."},
  {"priority":4,"name":"Skill Packs and Scope Guard","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"Robbie chooses or explains the relevant skill and redirects or blocks work outside its scope."},
  {"priority":5,"name":"Proactive Trigger Engine","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"Signal combinations become useful, reviewable opportunities rather than noisy cron output."},
  {"priority":6,"name":"Cost Router and Governor","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"The user receives adequate quality with visible spend and confirmation when policy requires it."},
  {"priority":7,"name":"Zaubern Lite","product_layer":"ZAUBERN_BOUNDARY","observable_outcome":"Before an action, the user receives a clear ALLOW, DRAFT_ONLY, ASK_CONFIRMATION, or BLOCK decision."},
  {"priority":8,"name":"Telegram UX","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"Approvals, drafts, briefs, voice intake, documents, and notifications feel natural and understandable."},
  {"priority":9,"name":"Super Familiar","product_layer":"ROBOTICXS_FEATURE","observable_outcome":"After the individual robot is stable, authorized family context supports bounded household workflows."}
]
```

## No authorized next stage

There is no authorized next implementation stage after this re-baseline. A
future maintainer must separately approve a user story and technical
specification for one candidate. This canon alone never authorizes a dependency,
runtime adoption, implementation, commit, deployment, or external action.
