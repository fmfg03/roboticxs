# Hermes Async Delegation Authority Adapter 102P v0.1

Status: 102P technical specification proposed for human approval only.

102P implementation is not authorized.

103P and later remain unauthorized.

This document defines the proposed technical specification for a deterministic local Hermes Async Delegation Authority Adapter v0. It does not implement runtime code, tests, live Hermes delegation, live subagent execution, live Telegram delivery, connector activation, model/provider calls, billing or token reconciliation, credential validation, browser/email/WhatsApp execution, external writes, payments, publishing, destructive actions, medical decisions, emergency monitoring, automatic caregiver alerts, or 103P authorization.

## Purpose and Scope

102P defines a deterministic local authority adapter for representing future async delegation work as governed local packets, handles, completion-event records, and audit traces without dispatching live async work.

The stage exists to prove that Roboticxs can:

- accept a proposed async delegation request as typed local input;
- preserve 95P through 101P authority boundaries before any local registration occurs;
- run required local cost/model preflight through 100P for every async delegation request;
- require exact 101P approval binding when 100P confirmation is required;
- create a deterministic local non-dispatching handle only after all gates pass;
- record local-only cancellation, expiry, completion, failure, and trace events without execution authority expansion; and
- reject imported or simulated completion records that do not match an existing registered local handle.

102P is an authority adapter only. It is not an execution stage.

## Current Authorization State

- 95P: `CLOSED_COMMITTED`
- 96P: `CLOSED_COMMITTED`
- 97P: `CLOSED_COMMITTED`
- 98P: `CLOSED_COMMITTED`
- 99P: `CLOSED_COMMITTED`
- 100P: `CLOSED_COMMITTED`
- 101P: `CLOSED_COMMITTED`
- 102P technical specification: authorized by maintainer instruction for proposal and human approval only
- 102P implementation: not authorized
- 103P and later: unauthorized

No part of this document:

- authorizes runtime implementation;
- updates canonical roadmap status to `CLOSED_COMMITTED`;
- authorizes live Hermes `delegate_task`;
- authorizes live async dispatch or live subagent startup; or
- authorizes 103P or any later stage.

## Non-Goals

- No live Hermes `delegate_task` call.
- No real async subagent dispatch.
- No background process execution.
- No live Telegram send.
- No connector activation.
- No model/provider call.
- No billing/token reconciliation API.
- No credential validation.
- No live cron.
- No browser/email/WhatsApp execution.
- No external writes.
- No payments.
- No publishing.
- No destructive actions.
- No medical decisions.
- No emergency monitoring.
- No automatic caregiver alerts.
- No UI.
- No database migration unless separately authorized in a later stage.
- No 103P authorization.

## Existing Contract Alignment

- 95P remains the command, scope, and tool authority entrypoint. 102P cannot bypass blocked or approval-required policy outcomes from 95P.
- 96P remains the Hermes OS packet-binding layer. Hermes is runtime substrate, not async delegation authority.
- 98P remains the routine preflight boundary. 102P cannot register async delegation around wake, budget, explicit-approval, or forced-stop preflight outcomes.
- 99P remains the Memory Center projection boundary. 102P may preserve bounded memory evidence but cannot widen memory visibility or treat memory as authority.
- 100P remains the cost-governor and model-routing authority for async delegation preflight. 102P cannot change task class, route, or cost decision.
- 101P remains the Action Packet approval loop. 102P cannot treat a missing, mismatched, expired, cancelled, rejected, or already-used approval artifact as valid registration authority.

## Shared Vocabularies

```text
AsyncDelegationState =
  proposed | preflight_blocked | awaiting_approval | approved_local |
  registered | cancelled | expired | completed | failed | rejected |
  blocked

AsyncDelegationDecision =
  allow_local_register | require_approval | block | cancel | expire |
  record_completion | record_failure

ActorRole =
  owner_admin | caregiver | care_recipient | robot | routine | operator

CompletionStatus =
  completed | failed | cancelled | expired | rejected | blocked
```

Unknown state or decision values are invalid and must block or reject with trace.

## Typed Local Contracts

The contracts below are normative for a future scoped implementation. This document does not create runtime types.

### AsyncDelegationRequest

Proposed local request to represent future async work.

| Field | Type | Rule |
| --- | --- | --- |
| `delegation_id` | `str` | Stable local delegation identifier. |
| `source_stage` | `str` | Required source stage such as `95P`, `98P`, or another separately authorized local stage. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str \| None` | Required when actor binding applies. |
| `actor_role` | `ActorRole` | Required actor role boundary. |
| `task_class` | `str` | Must resolve to 100P `async_delegation`. |
| `requested_capability` | `str` | Bounded local task shape only. |
| `requested_route_mode` | `str` | Requested routing mode for 100P evaluation. |
| `request_payload` | `dict[str, object]` | Data-only request description. |
| `required_policy_trace` | `tuple[str, ...]` | Required upstream 95P/96P/98P/99P policy evidence ids. |
| `required_memory_projection_request_id` | `str \| None` | Exact bounded 99P evidence when relevant. |
| `required_routine_run_id` | `str \| None` | Exact 98P evidence when routine-originated. |
| `expires_at` | `str \| None` | Optional registration deadline. |
| `authority_expansion_requested` | `bool` | Must be false. |
| `live_dispatch_requested` | `bool` | Must be false in 102P. |

Invariants:

- missing `owner_id` blocks;
- missing `robot_id` blocks;
- `authority_expansion_requested=true` blocks;
- `live_dispatch_requested=true` blocks;
- `task_class` must stay bound to the exact async delegation request being preflighted;
- request payload is proposal data only and grants no execution authority.

### AsyncDelegationPacket

Preserved local packet after upstream evidence and 100P/101P gating are evaluated.

| Field | Type | Rule |
| --- | --- | --- |
| `delegation_id` | `str` | Stable delegation identifier. |
| `packet_version` | `int` | Monotonic revision number starting at 1. |
| `state` | `AsyncDelegationState` | Current delegation state. |
| `decision` | `AsyncDelegationDecision` | Current decision outcome. |
| `source_stage` | `str` | Preserved source stage. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str \| None` | Preserved actor binding. |
| `actor_role` | `ActorRole` | Preserved actor role. |
| `task_class` | `str` | Required async delegation task class. |
| `request_snapshot` | `dict[str, object]` | Exact preserved request evidence. |
| `required_policy_trace` | `tuple[str, ...]` | Required upstream evidence ids. |
| `cost_preflight_request_id` | `str` | Required 100P request id. |
| `cost_preflight_decision` | `str` | Exact preserved 100P decision. |
| `selected_provider_id` | `str \| None` | Exact preserved local route evidence. |
| `selected_model_id` | `str \| None` | Exact preserved local route evidence. |
| `action_packet_id` | `str \| None` | Required when approval is needed. |
| `approval_resume_token_id` | `str \| None` | Required only when valid approval has been issued and consumed for 102P binding. |
| `expires_at` | `str \| None` | Optional packet or handle expiry. |
| `non_dispatching` | `bool` | Must always be true in 102P. |
| `authority_expanded` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false. |
| `live_dispatch_authorized` | `bool` | Must always be false. |

### AsyncDelegationState

| State | Meaning |
| --- | --- |
| `proposed` | Request was formed locally but not yet accepted for registration. |
| `preflight_blocked` | Upstream or cost preflight failed before approval/registration. |
| `awaiting_approval` | 100P required confirmation and 101P approval binding is required before registration. |
| `approved_local` | Exact local preflight and, when required, exact local approval are satisfied. |
| `registered` | Deterministic local non-dispatching handle was created. |
| `cancelled` | Registered or approval-bound delegation was cancelled locally. |
| `expired` | Delegation or handle exceeded its valid time boundary locally. |
| `completed` | Matching local imported/simulated completion record was accepted. |
| `failed` | Matching local imported/simulated failure record was accepted. |
| `rejected` | Imported/simulated completion record or registration attempt was rejected. |
| `blocked` | Any invariant or authority failure blocked progression. |

### AsyncDelegationDecision

| Decision | Meaning |
| --- | --- |
| `allow_local_register` | All required local gates passed and handle registration may occur. |
| `require_approval` | Valid 101P approval is required before local registration. |
| `block` | Registration or event ingestion must stop. |
| `cancel` | Local cancellation must be recorded. |
| `expire` | Local expiry must be recorded. |
| `record_completion` | Matching local completion record may be stored. |
| `record_failure` | Matching local failure record may be stored. |

### AsyncDelegationHandle

Deterministic local non-dispatching registration artifact created only after all gates pass.

| Field | Type | Rule |
| --- | --- | --- |
| `handle_id` | `str` | Stable local handle identifier. |
| `delegation_id` | `str` | Bound source delegation id. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str \| None` | Bound actor when actor binding applies. |
| `actor_role` | `ActorRole` | Bound actor role. |
| `task_class` | `str` | Bound task class. |
| `packet_version` | `int` | Bound packet revision. |
| `packet_hash` | `str` | Exact preserved packet binding. |
| `cost_preflight_request_id` | `str` | Exact bound 100P request id. |
| `cost_preflight_decision` | `str` | Exact bound 100P decision. |
| `selected_provider_id` | `str \| None` | Exact bound local route evidence. |
| `selected_model_id` | `str \| None` | Exact bound local route evidence. |
| `action_packet_id` | `str \| None` | Bound 101P packet when approval was required. |
| `approval_resume_token_id` | `str \| None` | Bound single-use approval evidence when applicable. |
| `registered_at` | `str` | Deterministic local registration time. |
| `expires_at` | `str \| None` | Required when policy or approval requires expiry. |
| `status` | `AsyncDelegationState` | Must begin as `registered`. |
| `dispatch_authorized` | `bool` | Must always be false. |
| `authority_expanded` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false. |
| `live_dispatch_authorized` | `bool` | Must always be false. |

### AsyncDelegationCompletionEvent

Local simulated or imported completion/failure/cancellation record only.

| Field | Type | Rule |
| --- | --- | --- |
| `event_id` | `str` | Stable local event identifier. |
| `handle_id` | `str` | Required bound local handle id. |
| `delegation_id` | `str` | Required bound delegation id. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str \| None` | Preserved actor binding when applicable. |
| `source_stage` | `str` | Local completion source label only. |
| `original_request_evidence` | `dict[str, object]` | Exact preserved request evidence. |
| `cost_preflight_evidence` | `dict[str, object]` | Exact preserved 100P evidence. |
| `approval_evidence` | `dict[str, object] \| None` | Exact preserved 101P evidence when applicable. |
| `completion_status` | `CompletionStatus` | Required local terminal record status. |
| `completion_payload_summary` | `dict[str, object]` | Data-only bounded summary. |
| `reason_code` | `str` | Stable machine-inspectable reason. |
| `authority_expanded` | `bool` | Must always be false. |
| `memory_access_expanded` | `bool` | Must always be false. |
| `tool_authority_granted` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false. |
| `live_dispatch_authorized` | `bool` | Must always be false. |

Invariants:

- completion events are imported or simulated local records only;
- completion payloads are data-only;
- completion payloads cannot grant memory, tool, provider, connector, external-effect, or execution authority;
- completion acceptance is not trusted execution proof by itself and requires a matching registered local handle.

### AsyncDelegationTraceRecord

Inspectable trace record for registration, approval binding, cancellation, expiry, completion, failure, and rejection outcomes.

| Field | Type | Rule |
| --- | --- | --- |
| `trace_id` | `str` | Stable local trace identifier. |
| `delegation_id` | `str` | Required delegation id. |
| `handle_id` | `str \| None` | Present only when a handle exists. |
| `previous_state` | `AsyncDelegationState \| None` | Null only at creation. |
| `next_state` | `AsyncDelegationState` | Resulting state. |
| `decision` | `AsyncDelegationDecision \| str` | Evaluated decision. |
| `owner_id` | `str` | Preserved owner boundary. |
| `robot_id` | `str` | Preserved robot boundary. |
| `actor_id` | `str \| None` | Preserved actor binding. |
| `actor_role` | `ActorRole` | Preserved actor role. |
| `task_class` | `str` | Preserved task class. |
| `source_stage` | `str` | Preserved source stage. |
| `cost_preflight_decision` | `str \| None` | Preserved 100P decision. |
| `action_packet_id` | `str \| None` | Preserved 101P packet when applicable. |
| `reason_code` | `str` | Stable machine-readable reason. |
| `authority_expanded` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false. |
| `live_dispatch_authorized` | `bool` | Must always be false. |

## Supported Delegation States

- `proposed`
- `preflight_blocked`
- `awaiting_approval`
- `approved_local`
- `registered`
- `cancelled`
- `expired`
- `completed`
- `failed`
- `rejected`
- `blocked`

## Supported Decisions

- `allow_local_register`
- `require_approval`
- `block`
- `cancel`
- `expire`
- `record_completion`
- `record_failure`

## State Transition Rules

All transitions are local-only and auditable.

| From | To | Required condition |
| --- | --- | --- |
| `null` | `proposed` | Valid local request object is created. |
| `proposed` | `preflight_blocked` | 95P, 96P, 98P, 99P, or 100P evidence is missing or blocking. |
| `proposed` | `awaiting_approval` | 100P returns `require_confirmation` and exact 101P approval binding is not yet satisfied. |
| `proposed` | `approved_local` | 100P allows local registration and no 101P approval is required. |
| `awaiting_approval` | `approved_local` | Valid exact-match 101P approval evidence is present and unused. |
| `approved_local` | `registered` | Deterministic local non-dispatching handle is created. |
| `registered` | `cancelled` | Local cancellation is recorded. |
| `registered` | `expired` | Handle expiry is reached or approval-bound validity expires. |
| `registered` | `completed` | Valid matching imported/simulated completion record is accepted. |
| `registered` | `failed` | Valid matching imported/simulated failure record is accepted. |
| `proposed` | `blocked` | Unknown state, unknown decision, missing owner/robot, authority expansion, live dispatch request, or other invariant failure occurs. |
| `awaiting_approval` | `blocked` | Approval is missing, invalid, expired, mismatched, cancelled, rejected, or already used. |
| `registered` | `rejected` | Invalid completion/failure event is submitted for the registered handle. |
| `registered` | `blocked` | Any attempt is made to dispatch live work or expand authority. |

Terminal states in 102P are:

- `cancelled`
- `expired`
- `completed`
- `failed`
- `rejected`
- `blocked`
- `preflight_blocked`

No terminal state may transition back to `registered` in 102P.

## Owner, Robot, and Actor Scoping Rules

- Every request, packet, handle, completion event, and trace record must be owner-bound.
- Every request, packet, handle, completion event, and trace record must be robot-bound.
- Actor binding is required whenever the originating stage or approval artifact binds work to a specific actor.
- `owner_id` mismatch blocks registration and rejects completion ingestion.
- `robot_id` mismatch blocks registration and rejects completion ingestion.
- `actor_id` mismatch blocks registration and rejects completion ingestion when actor binding is required.
- Actor role alone never substitutes for exact actor binding when the request or approval requires a specific actor.
- Routine-originated async delegation must preserve exact `required_routine_run_id` linkage and cannot widen to unrelated routines or actors.
- Bounded 99P memory evidence may be preserved by identifier or exact snapshot, but 102P cannot reveal excluded memory or treat memory as approval authority.

## AsyncDelegationHandle Rules

An `AsyncDelegationHandle` may be created only after all required gates pass.

The handle must be:

- owner-bound;
- robot-bound;
- actor-bound when applicable;
- packet-bound;
- task-class-bound;
- cost-preflight-bound;
- approval-bound when applicable;
- expiry-aware;
- auditable; and
- non-dispatching in 102P.

Additional handle rules:

- the handle must bind exactly one preserved packet revision;
- the handle must bind the exact preserved 100P request id, decision, and selected route evidence;
- when approval is required, the handle must bind the exact preserved 101P packet id and resume-token evidence;
- the handle must not authorize Hermes `delegate_task`, background processes, subagent startup, provider calls, connector activation, or external effects;
- the handle is a local registration artifact, not an execution ticket;
- once a handle becomes `cancelled`, `expired`, `completed`, or `failed`, 102P must treat it as non-reopenable.

## Integration Rules

### 95P Telegram Policy Chain

- 102P must never bypass 95P command, scope, or tool authority outcomes.
- A 95P-blocked action cannot become an async delegation registration candidate.
- A 95P approval-required outcome must preserve its Action Packet lineage into 101P and 102P rather than being silently converted into direct registration authority.

### 96P Hermes OS Runtime Contract

- 102P treats Hermes as substrate only.
- 102P may define local packet-binding shapes compatible with 96P but must not treat Hermes as async delegation authority.
- 102P must not call live Hermes runtime delegation APIs.

### 98P Routine Execution Engine

- Routine-originated async delegation requests must remain downstream of 98P preflight.
- Wake-stopped, budget-stopped, forced-failure, or approval-stopped routines cannot register async delegation.
- 102P cannot resume or reclassify routine work around 98P preflight outcomes.

### 99P Memory Center Projection Runtime

- 102P may preserve bounded 99P projection evidence as non-authority context only.
- 99P output may inform request evidence and context size lineage only.
- 102P cannot widen memory visibility, write memory, or treat projected memory as approval, route, or execution authority.

### 100P Cost Governor / Model Routing Runtime

- Every async delegation request must pass through local 100P cost/model preflight before registration.
- 102P must preserve the exact 100P request shape, decision, and selected route evidence.
- 102P cannot alter 100P task class, routing mode, selected model, or budget result.

### 101P Action Packet Approval Loop

- When 100P requires confirmation, 102P must produce or bind a 101P Action Packet approval requirement before registration.
- 102P must require exact packet and token matching for owner, robot, actor, task class, selected route, and cost evidence.
- 102P cannot treat 101P approval as execution authority. It is registration authority only within 102P.

## Required Behavior for 100P Async Delegation Paths

- If cost preflight blocks, 102P blocks.
- If cost preflight requires confirmation, 102P requires valid 101P approval before local registration.
- If cost preflight allows, 102P may register a local non-dispatching handle after all non-cost gates also pass.
- If `async_delegation_allowed=false`, 102P blocks.

Additional 100P binding rules:

- missing 100P cost preflight blocks;
- `require_confirmation` without valid 101P approval blocks;
- `allow` does not authorize live dispatch;
- downgraded or route-selected results remain local evidence only and do not imply execution authority.

## Required Behavior for 101P Approval Paths

- Approval must match the exact preserved async delegation request.
- Approval must match `owner_id`, `robot_id`, `actor_id` when applicable, `task_class`, selected route, and cost evidence.
- Expired approval cannot register delegation.
- Mismatched approval cannot register delegation.
- Rejected approval cannot register delegation.
- Cancelled approval cannot register delegation.
- Already-used approval or resume token cannot register delegation.

Further approval invariants:

- approval may authorize only local registration of the exact preserved packet;
- approval may not broaden route choice, payload scope, task class, actor scope, or memory scope;
- approval may not authorize external effects, providers, connectors, or dispatch.

## Local Completion-Event Rules

- Completion events are imported or simulated local records only.
- Unknown handles are rejected.
- Owner mismatch is rejected.
- Robot mismatch is rejected.
- Cancelled, expired, completed, or otherwise terminal handles are rejected for new completion ingestion.
- Completion payloads are data-only.
- Completion payloads cannot grant tools, memory, provider access, connectors, external effects, or execution authority.

Additional ingestion rules:

- completion acceptance requires a matching existing registered local handle;
- completion events are not trusted execution proof by default;
- payloads requesting authority expansion are rejected;
- payloads attempting external effects are rejected;
- a valid failure record may transition `registered -> failed`;
- a valid completion record may transition `registered -> completed`;
- cancellation and failure recording remain local-only in 102P.

## Trace and Audit Contract

Every registration attempt, approval-binding outcome, cancellation, expiry, completion acceptance, failure acceptance, rejection, and block must emit an `AsyncDelegationTraceRecord`.

Required trace fields:

- `delegation_id`
- `handle_id` when created
- `previous_state`
- `next_state`
- `decision`
- `owner_id`
- `robot_id`
- `actor_id`
- `actor_role`
- `task_class`
- `source_stage`
- `cost_preflight_decision`
- `action_packet_id` when applicable
- `reason_code`
- `authority_expanded: false`
- `external_effect_authorized: false`
- `provider_call_authorized: false`
- `execution_authorized: false`
- `live_dispatch_authorized: false`

Audit requirements:

- trace order must be deterministic and inspectable;
- traces must preserve exact blocking reason codes for failed gates;
- traces must not leak excluded memory or hidden approval payload data beyond bounded evidence references;
- every accepted completion or failure event must reference the original registration lineage.

## Failure Paths

- Unknown delegation state: block with trace.
- Unknown decision: block with trace.
- Missing `owner_id`: block.
- Missing `robot_id`: block.
- `owner_id` mismatch: block.
- `robot_id` mismatch: block.
- `actor_id` mismatch where actor binding is required: block.
- Missing 100P cost preflight: block.
- 100P block decision: block.
- 100P `require_confirmation` without valid 101P approval: block.
- 101P approval mismatch: block.
- 101P resume token expired or already used: block.
- `async_delegation_allowed=false` in 100P policy: block.
- Attempt to dispatch live Hermes `delegate_task`: block.
- Attempt to start live background subagent: block.
- Unknown completion handle: reject.
- Completion event for cancelled, expired, or completed handle: reject.
- Completion payload attempting authority expansion: reject.
- Completion payload containing external-effect instructions: reject.

## Test Plan

This section defines future verification scope only. It does not authorize creating tests in 102P.

Future implementation validation should include:

- contract construction tests for all typed local contracts;
- state-transition tests for every valid transition;
- failure-path tests for unknown state, unknown decision, and required-boundary mismatches;
- owner/robot/actor binding tests;
- 100P integration tests proving every async delegation request requires cost preflight;
- `async_delegation_allowed=false` tests proving hard block behavior;
- 100P `require_confirmation` tests proving registration cannot occur without exact 101P approval;
- 101P token single-use, expiry, and mismatch tests;
- handle-creation tests proving non-dispatching flags remain false;
- completion-ingestion tests for accepted completion, accepted failure, and rejected invalid events;
- trace determinism and audit completeness tests;
- no-dispatch regression tests proving Hermes `delegate_task`, background processes, subagents, providers, connectors, Telegram sends, and external effects are never started in 102P;
- roadmap authorization tests proving 102P remains spec-only until later explicit implementation authorization;
- 103P and later non-authorization tests.

## Expected Future Files

If a later implementation is separately authorized, expected files are likely:

- `app/async_delegation_authority.py`
- `docs/reference/HERMES_ASYNC_DELEGATION_AUTHORITY_ADAPTER_102P_v0_1.md`
- `tests/test_async_delegation_authority_102p.py`
- narrow integration-test updates only as needed in:
  `tests/test_telegram_policy_chain_95p.py`
  `tests/test_hermes_os_runtime_contract_96p.py`
  `tests/test_routine_execution_engine_98p.py`
  `tests/test_memory_center_projection_99p.py`
  `tests/test_cost_governor_model_routing_100p.py`
  `tests/test_action_packet_approval_101p.py`
  `tests/test_canonical_roadmap.py`
  `tests/test_roadmap_continuation_authorization_gate.py`

These are planning expectations only. This document does not authorize creating them.

## Rollback and Compatibility Notes

- 102P should be additive to 95P through 101P, not a rewrite.
- 100P cost-preflight evidence should remain reusable without changing 100P authority semantics.
- 101P Action Packet and resume-token evidence should remain reusable without changing 101P approval semantics.
- rollback should be able to disable 102P local registration without changing 95P, 96P, 98P, 99P, 100P, or 101P behavior.
- incomplete compatibility evidence must default to blocked registration and rejected event ingestion.
- future implementation should preserve existing packet contracts by wrapper mapping or explicit versioned adapters rather than back-editing earlier-stage authority rules.

## Roadmap and Continuation Authorization Rules

- This document proposes the 102P technical specification for human approval only.
- This document does not authorize 102P implementation.
- This document does not update 102P to `CLOSED_COMMITTED`.
- No next stage becomes eligible from this document alone.
- 103P and later remain unauthorized.
- Any 102P implementation requires separate explicit maintainer authorization after this spec is reviewed and approved.
- Any 103P or later story, spec, or implementation requires separate explicit maintainer direction.

## Explicit Future Boundary for 103P and Later

103P or a later separately authorized stage would be the earliest point at which the project could even propose live Telegram delivery and later live async dispatch boundaries.

102P does not authorize:

- live Telegram delivery;
- live Hermes async dispatch;
- live subagent startup;
- background worker execution;
- provider execution;
- connector activation; or
- any external effect path.

If a future stage is proposed for live Telegram delivery, it must remain separate from live async dispatch authorization unless a later maintainer-approved story and spec intentionally combine them. No such authorization exists here.

## Approval Boundary Statement

102P technical spec proposed for human approval only.

102P implementation is not authorized.

103P and later remain unauthorized.
