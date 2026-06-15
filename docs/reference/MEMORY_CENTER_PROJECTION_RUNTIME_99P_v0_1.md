# Memory Center Projection Runtime Slice v0

Status: 99P closed committed.

99P implements a deterministic local runtime skeleton only. This document does not authorize migrations, canonical memory writes, UI, endpoints, live Telegram or Hermes behavior, cron, connectors, providers, external actions, medical behavior, automatic caregiver alerts, production credentials, or 100P+.

## User Story

As Roboticxs runtime, I need to project Memory Center items into Telegram, Hermes OS, caregiver, and routine contexts using bounded, actor-aware, scope-aware rules, so runtime consumers receive useful context without exposing unrelated sensitive data or gaining authority.

## Recommendation

Recommend 99P as a **deterministic local runtime skeleton** after separate technical-spec and implementation approval.

A spec-only stage would not prove the actor and scope isolation behavior against the existing 95P-98P local runtime. A broader implementation slice would create unnecessary migration, persistence, endpoint, and live-runtime risk. The recommended skeleton should operate on typed local inputs, produce typed local data-only results and traces, and integrate only with the existing deterministic local 95P-98P paths.

The approved implementation remains limited to this deterministic local runtime skeleton.

## Scope

99P defines a local projection decision boundary that:

- accepts canonical Memory Center items as typed local inputs;
- filters items by actor, target scope, status, sensitivity, allowed use, and optional active skill;
- emits bounded summaries rather than unrestricted raw memory;
- preserves boundary-memory precedence over preference memory;
- supports explicitly labeled audit-only visibility without allowing audit-only records into decision context;
- produces an inspectable trace for every included, redacted, excluded, conflicted, or rejected record;
- supplies bounded data-only projections to the existing 95P Telegram policy chain, 96P Hermes OS contract, 97P caregiver slice, and successfully preflighted 98P routines;
- preserves Memory Center as canonical and preserves all existing authority gates.

## Non-Goals

- No canonical memory creation, update, approval, revocation, conflict resolution, or writeback.
- No migration or persistence-model expansion.
- No UI or API endpoint.
- No live Telegram sends, live Hermes startup, live cron, scheduler, connector, provider, model, or network behavior.
- No external actions, external writes, payments, publishing, browser/email/WhatsApp execution, or destructive actions.
- No tool, action, permission, confirmation, budget, skill activation, model/provider, or external-effect authority.
- No medical decisions, diagnosis, treatment advice, medication changes, emergency monitoring, or automatic caregiver alerts.
- No automatic inference that a caregiver or care recipient may access owner memory.
- No 100P or later authorization.

## Existing Contract Alignment

- 93P remains the canonical Memory Center and non-authority projection policy baseline.
- 95P remains the Telegram policy-chain entrypoint and may consume only bounded 99P results.
- 96P remains the Hermes OS packet-binding layer; Hermes is substrate, not authority.
- 97P caregiver actor isolation and sensitive-memory boundaries remain intact.
- 98P wake, budget, explicit-approval, manual-start, and forced-failure preflight remains before routine projection.
- Roboticxs SkillManifest remains canonical for skill scope. An optional skill filter may narrow projection but cannot activate a skill or grant permission.

## Typed Local Contracts

The contracts below are proposed local immutable value objects. Names and fields are normative for a future scoped build, but no runtime types are created by this specification.

### Shared Vocabularies

```text
MemoryStatus =
  proposed | approved | active | stale | revoked | conflicted |
  never-use-for-decisions

ActorRole = owner_admin | caregiver | care_recipient | robot | routine

ProjectionScope =
  general | caregiver | routine | telegram | hermes_os | skill_specific

Sensitivity =
  ordinary | personal | caregiver | credential_like | medical | legal |
  financial | safety_critical

AllowedUse =
  answer_personalization | boundary_enforcement | caregiver_context |
  routine_context | telegram_context | hermes_os_context |
  skill_context | audit_only

ProjectionDecision =
  include | include_redacted | exclude | include_audit_non_decisional |
  reject_request
```

Unknown values are invalid for projection and must be excluded with trace. Unknown request-level actor or scope values reject the request because no safe actor/scope policy can be selected.

### MemoryCenterItem

Canonical item input read from Memory Center.

| Field | Type | Rule |
| --- | --- | --- |
| `item_id` | `str` | Stable canonical identifier. |
| `owner_id` | `str` | Owner whose memory boundary applies. |
| `robot_id` | `str` | Robot boundary for the item. |
| `memory_kind` | `str` | Includes boundary, preference, or other existing memory kind. |
| `status` | `MemoryStatus` | Evaluated before content projection. |
| `scopes` | `tuple[ProjectionScope, ...]` | Explicit eligible target scopes. |
| `sensitivity` | `Sensitivity` | Drives redact/exclude behavior. |
| `allowed_uses` | `tuple[AllowedUse, ...]` | Uses the item may support; never grants authority. |
| `skill_ids` | `tuple[str, ...]` | Empty unless explicitly skill-specific. |
| `content` | `str` | Canonical raw content; not projected by default when sensitive. |
| `bounded_summary` | `str | None` | Explicit runtime-safe summary when one exists. |
| `source` | `str` | Preserved provenance label. |
| `conflict_group` | `str | None` | Groups known conflicting records. |
| `is_boundary` | `bool` | Boundary records take precedence. |
| `is_preference` | `bool` | Preference records remain subordinate to boundaries. |

Invariants:

- `item_id`, `owner_id`, and `robot_id` are required.
- `is_boundary` and `is_preference` must not both be true.
- `skill_specific` scope requires at least one `skill_id`.
- A bounded summary is data, not authority, and must not contain raw secrets or credentials.

### MemoryProjectionRequest

Local request describing one intended projection context.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Stable local request identifier. |
| `actor_id` | `str` | Actor receiving or using the projection. |
| `actor_role` | `ActorRole` | Selects actor isolation policy. |
| `owner_id` | `str` | Owner boundary against which access is evaluated. |
| `robot_id` | `str` | Required robot boundary. |
| `target_scope` | `ProjectionScope` | One target context per request. |
| `allowed_use` | `AllowedUse` | Intended use; must match item policy. |
| `decision_context` | `bool` | True when output may influence a decision. |
| `audit_only` | `bool` | Permits labeled non-decisional audit visibility only. |
| `active_skill_id` | `str | None` | Optional narrowing filter; never activates a skill. |
| `max_items` | `int` | Positive bounded result limit. |
| `max_summary_chars` | `int` | Positive per-summary bound. |
| `authority_expansion_requested` | `bool` | Must be false or the request is rejected. |

Invariants:

- `audit_only=true` requires `decision_context=false`.
- `target_scope=skill_specific` requires `active_skill_id`.
- `max_items` and `max_summary_chars` must use conservative implementation caps.
- `authority_expansion_requested=true` rejects the entire request before item evaluation.

### ProjectedMemorySummary

Bounded data-only record exposed to a runtime consumer.

| Field | Type | Rule |
| --- | --- | --- |
| `item_id` | `str` | Links to the canonical item without copying it. |
| `memory_kind` | `str` | Preserves boundary/preference classification. |
| `summary` | `str` | Bounded text; raw sensitive data is forbidden by default. |
| `source` | `str` | Preserved provenance. |
| `status` | `MemoryStatus` | Preserved status label. |
| `matched_scope` | `ProjectionScope` | Scope that allowed the result. |
| `sensitivity` | `Sensitivity` | Preserved sensitivity label. |
| `allowed_use` | `AllowedUse` | The single matched use. |
| `decisional` | `bool` | False for every audit-only or conflicted preference record. |
| `redacted` | `bool` | True when content was replaced by a bounded safe summary. |
| `conflict_disposition` | `str | None` | Explains boundary precedence or non-decisional conflict handling. |

### ProjectionTraceRecord

Inspectable record for each item decision and request-level rejection.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Projection request identifier. |
| `item_id` | `str | None` | Null only for request-level rejection. |
| `decision` | `ProjectionDecision` | Include, redact, exclude, audit-only, or reject. |
| `reason_code` | `str` | Stable machine-inspectable reason. |
| `actor_role` | `str` | Preserves the evaluated actor value. |
| `target_scope` | `str` | Preserves the evaluated scope value. |
| `status` | `str | None` | Preserves the evaluated item status. |
| `sensitivity` | `str | None` | Preserves the evaluated sensitivity. |
| `decisional` | `bool` | Must be false for excluded and audit-only records. |
| `authority_expanded` | `bool` | Must always be false. |

Trace records must not copy excluded raw sensitive content.

### MemoryProjectionResult

Data-only output of a valid local request.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Matches the request. |
| `status` | `str` | `completed` or `rejected`. |
| `summaries` | `tuple[ProjectedMemorySummary, ...]` | Bounded by `max_items`. |
| `trace` | `tuple[ProjectionTraceRecord, ...]` | Inspectable decisions without sensitive-content leakage. |
| `excluded_count` | `int` | Number excluded from consumer context. |
| `redacted_count` | `int` | Number included only as redacted summaries. |
| `audit_only_count` | `int` | Number visible only as non-decisional audit records. |
| `bounded` | `bool` | Must always be true. |
| `data_only` | `bool` | Must always be true. |
| `tool_action_authorization` | `bool` | Must always be false. |
| `permission_expansion_authorized` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `model_provider_access_authorized` | `bool` | Must always be false. |

Rejected requests contain no summaries and include only a request-level rejection trace.

## Actor Isolation Rules

| Actor | Default projection boundary |
| --- | --- |
| `owner_admin` | May receive owner-bound records allowed for the requested scope/use; sensitive data still requires explicit bounded-summary policy. |
| `caregiver` | May receive only explicitly caregiver-scoped records relevant to the care recipient/context; unrelated owner memory is excluded. |
| `care_recipient` | May receive only records explicitly allowed for the care-recipient-facing context; unrelated owner or caregiver-private memory is excluded. |
| `robot` | May receive only owner/robot-bound records allowed for the target runtime scope and use. |
| `routine` | May receive only routine-scoped records after successful 98P preflight. |

Actor role alone never grants access. Owner/admin does not bypass sensitivity, scope, allowed-use, or status filters.

## Scope and Skill Rules

- `general` items may be considered only for general requests whose actor and allowed use match.
- `telegram` and `hermes_os` items require the matching target scope.
- `caregiver` items require caregiver-context policy and preserve 97P isolation.
- `routine` items require routine scope and successful 98P preflight.
- `skill_specific` items require a matching `active_skill_id` that is already supported by the current canonical SkillManifest.
- Optional skill filtering only narrows eligible memory. It cannot activate a skill, enable a package, grant permission, or widen another scope.
- An item with no matching explicit scope is excluded.

## Status Rules

| Status | Decision-context default | Audit-only behavior |
| --- | --- | --- |
| `proposed` | Exclude. | May be labeled non-decisional when explicitly requested. |
| `approved` | Eligible only when the item is otherwise explicitly allowed for projection. Approval alone is insufficient. | May be shown non-decisionally. |
| `active` | Eligible after all filters. | May be shown non-decisionally. |
| `stale` | Exclude by default. | May be labeled stale and non-decisional. |
| `revoked` | Always exclude from consumer context. | May be represented only by metadata/trace, never content. |
| `conflicted` | Exclude or include only as explicitly labeled non-decisional conflict context. | May be labeled non-decisional. |
| `never-use-for-decisions` | Exclude from every decision context. | May be labeled non-decisional. |

## Sensitivity and Summary Rules

- Raw sensitive data is excluded by default.
- Credential-like data and secrets must never be projected as raw content or bounded summaries.
- Personal, caregiver, medical, legal, financial, and safety-critical records require explicit actor, scope, and allowed-use authorization for a bounded summary.
- An unauthorized caregiver or care recipient receives exclusion or a non-sensitive redacted summary only when an explicit policy permits that summary.
- A missing safe bounded summary causes exclusion rather than raw-content fallback.
- Every summary is truncated or rejected to satisfy `max_summary_chars`.
- Projection trace must state whether the item was included, redacted, or excluded without leaking excluded content.

## Allowed-Use Rules

- The request's single `allowed_use` must be explicitly present on each included item.
- `boundary_enforcement` may influence policy interpretation but cannot grant tools or actions.
- `answer_personalization`, `telegram_context`, `hermes_os_context`, `caregiver_context`, `routine_context`, and `skill_context` remain context-only uses.
- `audit_only` records must never enter decision context or consumer summaries marked `decisional=true`.
- An allowed-use match cannot override actor, scope, status, sensitivity, conflict, preflight, or authority rules.

## Projection Decision Order

1. Validate request actor, scope, allowed use, bounds, audit/decision combination, optional skill requirement, and non-authority invariant.
2. Reject the entire request if it attempts authority expansion.
3. Evaluate owner and robot isolation.
4. Evaluate actor isolation.
5. Evaluate explicit target scope and optional skill.
6. Evaluate status.
7. Evaluate allowed use.
8. Evaluate sensitivity and choose bounded summary, redaction, or exclusion.
9. Apply conflict handling and boundary-memory precedence.
10. Order boundary memory before remaining valid records.
11. Apply item and character bounds.
12. Emit summaries and a trace for every evaluated item without leaking excluded sensitive content.

No later step may reverse an earlier exclusion.

## Audit-Only Behavior

- Audit-only requests may inspect excluded record metadata only when explicitly requested.
- Eligible audit-only records use `include_audit_non_decisional`, `decisional=false`, and an explicit reason label.
- Revoked items expose trace metadata only, never content.
- Audit-only output is separate from decision-context summaries.
- Audit-only records must not be passed into 95P decision context, 96P Hermes context, 97P caregiver decision context, or 98P routine decision context.
- `audit_only=true` with `decision_context=true` is invalid and rejects the request.

## Conflict Behavior

- Valid boundary memory precedes preference memory.
- A preference that conflicts with a valid boundary is excluded from decision context and traced as `preference_conflicts_with_boundary`.
- A conflicted preference may appear only in audit-only output or explicitly labeled non-decisional conflict context.
- Conflicting preferences without a controlling boundary are excluded or marked non-decisional; they must not be blended into a synthetic fact.
- A conflicted boundary remains excluded from decision context unless a separately approved future policy defines resolution. 99P does not resolve conflicts.

## Authority Rules

Projection is data-only.

- Projection cannot grant tools, actions, permissions, confirmation, external effects, live runtime authority, skill activation, budget authority, model routing, or model/provider access.
- Projection cannot bypass command policy, skill scope policy, tool authority policy, budget authority, Action Packet confirmation, blocked-action policy, caregiver isolation, or routine preflight.
- A projection result must always set all authority-expansion flags to false.
- 96P `MemoryProjectionPacket` binding must preserve `bounded=true`, `scoped=true`, and all authority flags as false.
- Hermes OS binding cannot reinterpret memory text as permission or authority.
- Boundary memory may restrict behavior but cannot independently authorize behavior.

## Integration Rules

### 95P Telegram Policy Chain

- 95P constructs a 99P request only after actor and request scope are known.
- 95P consumes only `MemoryProjectionResult.summaries` that are bounded, decisional as appropriate, and allowed for Telegram context.
- 95P must not consume excluded or audit-only records as decision context.
- 95P tool-authority decisions remain independent and cannot be widened by projection.

### 96P Hermes OS Contract

- 96P binds the bounded 99P result into `MemoryProjectionPacket`.
- The packet preserves source of truth, target scope, trace reference, bounds, and false authority flags.
- Binding must not grant permission, tools, model/provider access, or external effects.

### 97P Caregiver Slice

- 97P requests caregiver-scoped projection with an explicit actor role.
- Caregiver and care-recipient isolation remains intact.
- Unrelated owner memory and unauthorized sensitive memory remain excluded or safely redacted.
- Projection cannot create medical behavior, automatic caregiver alerts, hidden escalation, or live delivery.

### 98P Routine Execution

- A routine may request 99P projection only after successful wake, budget, explicit-approval, manual-start, and forced-failure preflight.
- A successful routine request uses actor role `routine`, target scope `routine`, and routine-context allowed use.
- Routine projection includes only routine-scoped eligible memory.
- A preflight-stopped routine must not invoke the 99P projection runtime and must not call the Hermes adapter.
- Existing synthetic preflight-stopped audit objects remain outside the 99P runtime and must record zero projections.

## Failure Paths

| Failure | Required behavior |
| --- | --- |
| Unknown request actor or scope | Reject request with trace; emit no summaries. |
| Unknown item status or sensitivity | Exclude item with trace. |
| Unknown allowed use | Reject request when request-level; exclude item when item-level. |
| Sensitive memory without actor authorization | Redact only when an explicit bounded safe summary is allowed; otherwise exclude with trace. |
| Invalid request attempting authority expansion | Reject request before item evaluation. |
| Invalid audit-only decision-context combination | Reject request. |
| Skill-specific request without supported active skill | Reject request or exclude skill-specific items with trace; never activate the skill. |
| Preflight-stopped routine | Do not invoke 99P runtime; produce no 99P result; do not call Hermes adapter. |
| Conflicting boundary and preference | Retain valid boundary; exclude preference from decision context as a non-decisional conflict. |
| Result bound exceeded | Deterministically retain highest-priority eligible records and trace bound exclusions. |
| No safe bounded summary for sensitive item | Exclude with trace; never fall back to raw content. |

## Determinism and Ordering

- Apply boundary-memory precedence first.
- Within the same priority, order by stable canonical `item_id`.
- Apply `max_items` only after all safety and conflict filters.
- The same typed inputs must produce the same summaries, ordering, and reason codes.
- No clock, network, provider, random, or external-state dependency is permitted in the future local skeleton.

## Proposed Reason Codes

The future skeleton should use stable reason codes including:

```text
included_allowed_context
included_redacted_sensitive_summary
included_audit_non_decisional
excluded_owner_isolation
excluded_actor_isolation
excluded_scope_mismatch
excluded_skill_mismatch
excluded_status_proposed
excluded_status_stale
excluded_status_revoked
excluded_status_conflicted
excluded_never_use_for_decisions
excluded_allowed_use_mismatch
excluded_sensitive_unauthorized
excluded_sensitive_no_safe_summary
excluded_preference_conflicts_with_boundary
excluded_result_bound
rejected_unknown_actor
rejected_unknown_scope
rejected_unknown_allowed_use
rejected_invalid_audit_decision_combination
rejected_authority_expansion
```

## Test Plan

Future implementation tests must prove:

1. Active approved memory projects into an allowed context.
2. Revoked memory is excluded.
3. Stale memory is excluded by default.
4. Conflicted memory is excluded or marked non-decisional.
5. `never-use-for-decisions` is excluded from decision context.
6. Sensitive memory is redacted or excluded for an unauthorized caregiver or care recipient.
7. Actor isolation prevents a caregiver from seeing unrelated owner memory.
8. Routine projection includes only routine-scoped memory.
9. Valid boundary memory overrides conflicting preference memory.
10. Projection cannot expand tool authority.
11. Projection result includes inspectable trace and audit data without leaking excluded sensitive content.
12. 95P receives bounded memory only and does not consume audit-only records as decision context.
13. 96P binding is non-authority-expanding.
14. 97P caregiver isolation remains intact.
15. A 98P preflight-stopped routine does not invoke projection and does not call the Hermes adapter.
16. Unknown actor, scope, status, sensitivity, and allowed-use values follow the specified reject/exclude paths.
17. Credential-like data never projects.
18. Bounds and ordering are deterministic.
19. 100P+ remains unauthorized.

Required future regression coverage:

- `tests/test_memory_center_projection_99p.py`
- `tests/test_telegram_policy_chain_95p.py`
- `tests/test_hermes_os_runtime_contract_96p.py`
- `tests/test_caregiver_telegram_mvp_97p.py`
- `tests/test_routine_execution_engine_98p.py`
- `tests/test_canonical_roadmap.py`
- `tests/test_roadmap_continuation_authorization_gate.py`

## Expected Future Implementation Files

These paths describe a future separately approved scoped build. This specification creates none of them except this docs-only specification file.

- `app/memory_center_projection.py`
- `tests/test_memory_center_projection_99p.py`
- existing 95P-98P integration modules and tests only where separately approved
- `docs/reference/MEMORY_CENTER_PROJECTION_RUNTIME_99P_v0_1.md`
- canonical roadmap update only after explicit stage-status authorization

No migration, UI file, endpoint, dependency, connector configuration, provider configuration, or production credential file is expected or authorized.

## Rollback and Compatibility

For a future approved local skeleton:

- keep existing 95P projection behavior available until 99P integration tests pass;
- make integration changes narrow and reversible;
- do not migrate or rewrite canonical Memory Center records;
- preserve 93P contract meaning and 95P-98P authority invariants;
- rollback consists of removing the local 99P binding and restoring prior bounded local projection behavior, with no data migration required.

## Risks Requiring Implementation Review

- Existing `MemoryItem` persistence fields do not encode the full proposed status, actor, scope, sensitivity, allowed-use, skill, and conflict model. A future skeleton should use typed local fixtures/adapters rather than inventing a migration.
- Current 95P projection is type-based and actor-light; replacing it without regression coverage could expose unrelated memory.
- Current 97P and 98P apply additional ad hoc redaction. Future integration must preserve those restrictions until equivalent 99P tests prove stricter behavior.
- Audit traces can leak sensitive content if they copy item text. Trace records must contain metadata and reason codes only.
- Boundary precedence can become accidental authority expansion if interpreted as permission. Boundary memory may restrict, never grant.

## Authorization State

- 95P: `CLOSED_COMMITTED`
- 96P: `CLOSED_COMMITTED`
- 97P: `CLOSED_COMMITTED`
- 98P: `CLOSED_COMMITTED`
- 99P user story and technical specification: approved
- 99P implementation: closed committed as a deterministic local runtime skeleton
- 100P and later: unauthorized

No migration, canonical memory write, UI, endpoint, live runtime, external effect, medical behavior, automatic caregiver alert, or future-stage authority is granted by this closeout.

## Closeout Evidence

- implementation commit: `same_commit_as_99P_closeout`
- typed local contracts: `MemoryCenterItem`, `MemoryProjectionRequest`, `MemoryProjectionResult`, `ProjectedMemorySummary`, `ProjectionTraceRecord`
- deterministic actor, scope, status, sensitivity, allowed-use, optional-skill, conflict, bounds, and trace behavior
- bounded 95P consumption and non-authority 96P binding
- 97P caregiver isolation preserved
- 98P projection only after successful preflight; preflight-stopped routines do not invoke 99P or Hermes adapter
- no migrations, canonical memory writes, UI, endpoints, live runtime, external effects, medical behavior, or automatic caregiver alerts
- 100P and later: unauthorized
