# Roboticxs Action Packet Approval Loop 101P v0.1

Status: 101P technical specification proposed for human approval only.

101P technical specification is authorized by the maintainer instruction for specification work only.

101P implementation is not authorized.

102P and later remain unauthorized.

## Purpose

101P defines a deterministic local approval-loop skeleton for any proposed action that requires explicit human review before execution authority may ever be considered in a later stage.

The stage exists to prove that Roboticxs can:

- represent approval-required work as typed local packets;
- review, approve, reject, edit, cancel, expire, and resume packets locally;
- preserve owner, robot, actor, policy-trace, memory, routine, and cost boundaries;
- convert 100P confirmation-shaped results into Action Packet-compatible approval records; and
- emit bounded local resume metadata without executing anything.

101P is a local approval-governance stage only. It does not execute tools, start Hermes, call providers, send Telegram messages, dispatch async work, or perform external effects.

## User Story Basis

This technical specification is derived from the approved 101P user story and acceptance criteria supplied by the maintainer on 2026-06-17.

The story is approved for technical specification only.

Implementation authorization is explicitly withheld.

## Recommendation

Recommend 101P as a deterministic local runtime skeleton after separate technical-spec approval and later separate implementation approval.

A spec-only stage is appropriate here because the repo now has closed-committed policy, routine, memory, and cost layers that need a bounded approval-loop design before any future execution-resume stage is considered. A broader implementation would create unnecessary authority and execution risk.

## Current Authorization State

- 95P: closed committed
- 96P: closed committed
- 97P: closed committed
- 98P: closed committed
- 99P: closed committed
- 100P: closed committed
- 101P technical specification: proposed for human approval only
- 101P implementation: not authorized
- 102P and later: unauthorized

No part of this document authorizes:

- live execution;
- live Telegram sends;
- live Hermes Gateway startup;
- async delegation dispatch;
- connector activation;
- external writes;
- payments;
- publishing;
- browser, email, or WhatsApp execution;
- destructive actions;
- model or provider calls;
- billing or token reconciliation;
- production credentials;
- medical decisions, emergency monitoring, or automatic caregiver alerts; or
- 102P or later implementation.

## Scope

101P defines a local deterministic approval decision boundary that:

- accepts typed local packet requests from existing local runtime stages;
- records approval state transitions without mutating prior history invisibly;
- issues bounded local resume tokens only after valid approval;
- blocks resume when scope, actor, owner, robot, policy, cost, memory, or expiry requirements fail;
- preserves all existing 95P through 100P boundaries; and
- remains data-only and non-executing even after approval.

## Non-Goals

- No live tool execution.
- No live Telegram delivery.
- No live Hermes startup.
- No async delegation dispatch.
- No connector or MCP activation.
- No external writes, payments, publishing, browser/email/WhatsApp execution, or destructive actions.
- No provider or model calls.
- No billing, token reconciliation, or credential checks.
- No production credentials.
- No UI, operator console, or human notification system.
- No automatic memory exposure beyond bounded 99P projections.
- No override of 98P preflight or 100P budget/model constraints.
- No 102P authorization.

## Existing Contract Alignment

- 92P remains the baseline Action Packet contract for approval-required tool/action proposals.
- 95P remains the Telegram policy-chain entrypoint. 101P cannot bypass command, scope, or tool authority decisions.
- 96P remains the Hermes OS packet-binding layer. Hermes is substrate, not approval authority.
- 98P remains the routine preflight boundary. 101P cannot resume around wake, budget, explicit-approval, or manual-start rules.
- 99P remains the Memory Center projection boundary. 101P cannot reveal excluded or unprojected memory.
- 100P remains the cost-governor authority for cost/model preflight. 101P cannot change the approved cost shape or selected route.

## Shared Vocabularies

```text
ActionType =
  cost_confirmation | tool_action | routine_continuation |
  async_delegation | live_delivery | connector_action |
  external_tool_execution

ActionPacketApprovalState =
  proposed | awaiting_approval | approved | rejected |
  edited | cancelled | expired | resumed | blocked

ActionPacketDecision =
  approve | reject | edit | cancel | expire | resume

ActorRole =
  owner_admin | caregiver | care_recipient | robot | routine | operator

ResumeScope =
  exact_packet | exact_revision | exact_preflight | exact_routine_run |
  exact_memory_projection | future_local_runtime_only
```

Unknown state or decision values are invalid and must produce `blocked` traceable outcomes.

## Typed Local Contracts

The contracts below are normative for a future scoped implementation. This document does not create runtime types.

### ActionPacket

Canonical local approval artifact representing one proposed action under bounded conditions.

| Field | Type | Rule |
| --- | --- | --- |
| `packet_id` | `str` | Stable packet identifier. |
| `packet_version` | `int` | Monotonic revision number starting at 1. |
| `state` | `ActionPacketApprovalState` | Current approval state. |
| `action_type` | `ActionType` | One bounded proposal class. |
| `source_stage` | `str` | Usually `95P`, `98P`, `100P`, or future local-only stage. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str` | Actor expected to review or resume. |
| `actor_role` | `ActorRole` | Role boundary for review and resume. |
| `requested_by_actor_id` | `str` | Original requesting actor. |
| `requested_by_actor_role` | `ActorRole` | Original request role. |
| `required_policy_trace` | `tuple[str, ...]` | Required upstream policy identifiers. |
| `required_cost_preflight_request_id` | `str \| None` | Required for cost-shaped packets. |
| `required_cost_preflight_decision` | `str \| None` | Must match exact required decision shape. |
| `required_selected_model_id` | `str \| None` | Preserves 100P selected route when applicable. |
| `required_memory_projection_request_id` | `str \| None` | Required when bounded memory context matters. |
| `required_routine_run_id` | `str \| None` | Required for routine continuation packets. |
| `action_payload` | `dict[str, object]` | Bounded local proposal payload only. |
| `review_expires_at` | `str \| None` | Optional approval expiry timestamp. |
| `resume_scope` | `ResumeScope` | Bounded future resume shape. |
| `resume_token_id` | `str \| None` | Null until approval yields a token. |
| `supersedes_packet_id` | `str \| None` | Prior version when created by edit flow. |
| `audit_note` | `str \| None` | Optional human-readable bounded note. |
| `authority_expanded` | `bool` | False in packet form. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false in 101P. |

Invariants:

- Action Packets are data-only until explicitly approved.
- Action Packets do not grant authority by themselves.
- `action_payload` must fully describe the bounded proposed action or bounded resume conditions.
- `authority_expanded` remains false in the packet even after approval; any bounded future authority is represented only by a resume token.
- `external_effect_authorized`, `provider_call_authorized`, and `execution_authorized` must remain false in 101P.

### ActionPacketRequest

Local request to create one Action Packet.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Stable request identifier. |
| `source_stage` | `str` | Upstream local source stage. |
| `action_type` | `ActionType` | Proposed approval class. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `actor_id` | `str` | Actor expected to review/act. |
| `actor_role` | `ActorRole` | Role expected to review/act. |
| `requested_by_actor_id` | `str` | Original requesting actor. |
| `requested_by_actor_role` | `ActorRole` | Original requesting role. |
| `required_policy_trace` | `tuple[str, ...]` | Required upstream policies. |
| `required_cost_preflight` | `dict[str, object] \| None` | Required exact 100P preflight snapshot when applicable. |
| `required_memory_projection` | `dict[str, object] \| None` | Required exact bounded 99P snapshot when applicable. |
| `required_routine_context` | `dict[str, object] \| None` | Required exact 98P context when applicable. |
| `action_payload` | `dict[str, object]` | Bounded proposal payload. |
| `review_expires_at` | `str \| None` | Optional expiry. |
| `resume_scope` | `ResumeScope` | Bounded intended future resume shape. |

Invariants:

- missing required policy trace blocks packet creation;
- cost-shaped packets require exact 100P preflight evidence;
- memory-sensitive packets require exact bounded 99P evidence;
- routine continuation packets require exact 98P preflight context;
- request creation is local-only and non-executing.

### ActionPacketDecision

Local review or resume command against one Action Packet.

| Field | Type | Rule |
| --- | --- | --- |
| `packet_id` | `str` | Target packet identifier. |
| `packet_version` | `int` | Expected packet revision. |
| `decision` | `ActionPacketDecision` | Approve, reject, edit, cancel, expire, or resume. |
| `actor_id` | `str` | Reviewing/resuming actor. |
| `actor_role` | `ActorRole` | Reviewing/resuming role. |
| `owner_id` | `str` | Must match packet. |
| `robot_id` | `str` | Must match packet. |
| `reason_code` | `str` | Stable machine-inspectable reason. |
| `edit_payload` | `dict[str, object] \| None` | Required when decision is `edit`. |
| `resume_token_id` | `str \| None` | Required when decision is `resume`. |
| `occurred_at` | `str` | Deterministic local event time. |

Invariants:

- unknown decision values block;
- actor, owner, or robot mismatch blocks;
- `edit` never mutates prior history invisibly;
- `resume` requires a valid single-use token;
- `approve` in 101P creates local resume metadata only, not execution.

### ActionPacketApprovalState

Approval lifecycle vocabulary.

| State | Meaning |
| --- | --- |
| `proposed` | Packet created but not yet submitted for human approval. |
| `awaiting_approval` | Packet is pending explicit human action. |
| `approved` | Packet was approved locally; bounded resume token may exist. |
| `rejected` | Packet was denied and cannot resume. |
| `edited` | Prior packet was superseded by an edited revision. |
| `cancelled` | Packet was withdrawn and cannot resume. |
| `expired` | Packet timed out and cannot resume. |
| `resumed` | Resume token was consumed locally for future-stage handoff metadata only. |
| `blocked` | Packet or decision was blocked by invariant failure. |

### ActionPacketReviewEvent

One auditable state transition event.

| Field | Type | Rule |
| --- | --- | --- |
| `event_id` | `str` | Stable event identifier. |
| `packet_id` | `str` | Target packet identifier. |
| `packet_version` | `int` | Revision associated with the event. |
| `previous_state` | `ActionPacketApprovalState \| None` | Null only at creation. |
| `next_state` | `ActionPacketApprovalState` | Resulting state. |
| `decision` | `ActionPacketDecision \| None` | Null only for initial creation/automatic expiry. |
| `actor_id` | `str` | Acting actor. |
| `actor_role` | `ActorRole` | Acting role. |
| `owner_id` | `str` | Preserved owner boundary. |
| `robot_id` | `str` | Preserved robot boundary. |
| `reason_code` | `str` | Stable transition reason. |
| `created_resume_token_id` | `str \| None` | Present only after approval. |
| `superseded_by_packet_id` | `str \| None` | Present only for edit flows. |
| `occurred_at` | `str` | Deterministic local event time. |

### ActionPacketResumeToken

Bounded local resume artifact created only after valid approval.

| Field | Type | Rule |
| --- | --- | --- |
| `resume_token_id` | `str` | Stable token identifier. |
| `packet_id` | `str` | Bound source packet. |
| `packet_version` | `int` | Bound source revision. |
| `owner_id` | `str` | Must match packet. |
| `robot_id` | `str` | Must match packet. |
| `actor_id` | `str` | Single allowed actor. |
| `actor_role` | `ActorRole` | Single allowed role. |
| `resume_scope` | `ResumeScope` | Exact bounded future resume shape. |
| `source_stage` | `str` | Stage that created the packet. |
| `required_policy_trace` | `tuple[str, ...]` | Required upstream policies preserved. |
| `required_cost_preflight_request_id` | `str \| None` | Required exact 100P request id when applicable. |
| `required_selected_model_id` | `str \| None` | Required exact selected route when applicable. |
| `required_memory_projection_request_id` | `str \| None` | Required exact bounded memory projection when applicable. |
| `required_routine_run_id` | `str \| None` | Required exact routine context when applicable. |
| `issued_at` | `str` | Deterministic local event time. |
| `expires_at` | `str \| None` | Optional expiry boundary. |
| `used_at` | `str \| None` | Null until consumed. |
| `used` | `bool` | Must begin false and become true exactly once. |
| `authority_expanded` | `bool` | True only to mean bounded local resume metadata exists. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false in 101P. |

Invariants:

- single-use;
- owner-bound;
- robot-bound;
- actor-bound;
- packet-bound;
- scope-bound;
- expiry-aware;
- auditable;
- non-executing in 101P.

### ActionPacketTraceRecord

Inspectable trace for creation, review, block, and resume events.

| Field | Type | Rule |
| --- | --- | --- |
| `packet_id` | `str` | Target packet identifier. |
| `packet_version` | `int` | Revision evaluated. |
| `previous_state` | `ActionPacketApprovalState \| None` | Null only for initial creation. |
| `next_state` | `ActionPacketApprovalState` | Resulting state. |
| `decision` | `ActionPacketDecision \| None` | Null only for packet creation. |
| `actor_id` | `str` | Acting actor. |
| `actor_role` | `ActorRole` | Acting role. |
| `owner_id` | `str` | Evaluated owner boundary. |
| `robot_id` | `str` | Evaluated robot boundary. |
| `action_type` | `ActionType` | Preserved proposal class. |
| `source_stage` | `str` | Preserved source stage. |
| `reason_code` | `str` | Stable machine-inspectable reason. |
| `authority_expanded` | `bool` | False except bounded token issuance after approval. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `provider_call_authorized` | `bool` | Must always be false. |
| `execution_authorized` | `bool` | Must always be false in 101P. |

## Supported States

- `proposed`
- `awaiting_approval`
- `approved`
- `rejected`
- `edited`
- `cancelled`
- `expired`
- `resumed`
- `blocked`

## Supported Decisions

- `approve`
- `reject`
- `edit`
- `cancel`
- `expire`
- `resume`

## State Transition Rules

Valid local transitions:

- `proposed -> awaiting_approval`
- `awaiting_approval -> approved`
- `awaiting_approval -> rejected`
- `awaiting_approval -> edited`
- `awaiting_approval -> cancelled`
- `awaiting_approval -> expired`
- `approved -> resumed`
- `approved -> expired`
- `approved -> blocked`
- `proposed -> blocked`
- `awaiting_approval -> blocked`
- `approved -> blocked`

Rules:

- packet creation begins as `proposed` or directly `awaiting_approval` depending on source-stage contract;
- `approve` may move only from `awaiting_approval` to `approved`;
- `reject` may move only from `awaiting_approval` to `rejected`;
- `cancel` may move only from `proposed` or `awaiting_approval` to `cancelled`;
- `expire` may move only from `proposed`, `awaiting_approval`, or `approved` to `expired`;
- `edit` never mutates the prior packet into new content invisibly; it marks the prior packet `edited` and creates a new `proposed` or `awaiting_approval` revision;
- `resume` may move only from `approved` to `resumed` and requires a valid single-use resume token;
- `rejected`, `cancelled`, `expired`, `blocked`, and `edited` prior packets cannot resume;
- any unknown transition blocks with trace.

## Owner, Robot, and Actor Scoping Rules

- `owner_id` must match at packet creation, review, approval, rejection, edit, cancellation, expiry, and resume.
- `robot_id` must match at packet creation, review, approval, rejection, edit, cancellation, expiry, and resume.
- `actor_id` and `actor_role` must match the packet’s review/resume scope for approval and resume.
- packets are not transferable across owners, robots, or actors.
- packets cannot be resumed by a different actor merely because the role name matches.
- role alone never overrides actor-bound constraints.
- packets originating from caregiver or care-recipient contexts must preserve the originating actor boundary and 99P projection limits.

## Resume Token Rules

- single-use;
- owner-bound;
- robot-bound;
- actor-bound;
- packet-bound;
- exact-revision-bound;
- scope-bound;
- expiry-aware;
- auditable;
- non-executing in 101P.

Additional rules:

- token issuance is allowed only after valid approval;
- token issuance preserves required policy trace, cost preflight, memory projection, and routine context bindings;
- using a token marks it consumed permanently;
- already-used or expired tokens block resume with trace;
- 101P resume does not execute the underlying action; it only records a local resumable handoff shape for a future separately authorized stage.

## Integration Rules

### 95P Telegram Policy Chain

- 95P remains the required consumer entrypoint for Telegram-sourced approval flows.
- `ASK_CONFIRMATION` and cost-confirmation local results may be represented as 101P-compatible Action Packet requests.
- 101P does not bypass 95P command, scope, or tool authority decisions.
- blocked 95P requests do not become resumable approval packets unless a future approved story changes that policy.

### 96P Hermes OS Runtime Contract

- 101P approval artifacts bind into Hermes OS as local governance evidence only.
- Hermes remains substrate, not approval authority.
- approved packets and resume tokens may be attached to future `TaskRunRecord` or packet bindings, but 101P itself does not start Hermes or authorize execution.

### 98P Routine Execution Engine

- routine continuation packets must preserve exact 98P preflight state.
- 101P cannot revive wake-skipped, budget-blocked, silent-execution-blocked, or forced-failure routine runs by itself.
- approval of a routine continuation packet does not override 98P preflight; it only records bounded local continuation metadata.

### 99P Memory Center Projection Runtime

- memory-sensitive packets must carry only bounded 99P projection evidence.
- 101P cannot expose memory excluded by actor, scope, allowed-use, status, or sensitivity filters.
- approval does not expand memory access.

### 100P Cost Governor / Model Routing Runtime

- `require_confirmation` preflight results must be convertible into Action Packet-compatible approval metadata.
- 101P must preserve exact `request_id`, selected route, and budget constraints.
- approval of a cost-confirmation packet cannot widen model choice, raise budget ceilings, or authorize provider execution.
- 101P emits bounded resume metadata only.

## Required 100P Confirmation Behavior

100P `require_confirmation` results must be representable as Action Packet-compatible local records containing at minimum:

- `owner_id`
- `robot_id`
- `actor_id`
- `actor_role`
- `required_cost_preflight_request_id`
- `required_cost_preflight_decision=require_confirmation`
- `required_selected_model_id`
- exact estimated token and cost summary
- exact source-stage reference to `100P`
- non-authority flags set to false

Rules:

- the packet must represent the exact preflighted request only;
- the selected route is fixed and cannot be swapped during approval;
- approval must not execute the task in 101P;
- approval may issue only bounded resume metadata for future local stages.

## Future-Gate Shapes

The following remain future-gate shapes only in 101P:

- `async_delegation`
  Rule: local approval representation only; no dispatch occurs.
- `live_delivery`
  Rule: local approval representation only; no Telegram send occurs.
- `connector_action`
  Rule: local approval representation only; no connector activation occurs.
- `external_tool_execution`
  Rule: local approval representation only; no tool or external effect occurs.

These packet classes are allowed only as deterministic local approval contracts, not as execution paths.

## Trace and Audit Contract

Every packet creation, state change, invalid transition, block, token issuance, token use, expiry, and edit supersession must emit inspectable trace.

Required trace fields:

- `packet_id`
- `previous_state`
- `next_state`
- `decision`
- `actor_id`
- `actor_role`
- `owner_id`
- `robot_id`
- `action_type`
- `source_stage`
- `reason_code`
- `authority_expanded`
- `external_effect_authorized`
- `provider_call_authorized`
- `execution_authorized`

Trace rules:

- `authority_expanded=false` for all packet-only transitions;
- `authority_expanded=true` is permitted only on the bounded local token-issuance event after approval;
- `external_effect_authorized=false` always;
- `provider_call_authorized=false` always;
- `execution_authorized=false` always in 101P;
- trace must remain inspectable and deterministic.

## Failure Paths

- unknown packet state: block with trace;
- unknown decision: block with trace;
- owner mismatch: block with trace;
- robot mismatch: block with trace;
- actor mismatch on approval or resume: block with trace;
- stale or expired packet: block with trace;
- already-used resume token: block with trace;
- packet without required policy trace: block;
- packet requiring cost preflight but missing exact 100P result: block;
- packet requiring memory projection but missing bounded 99P result: block;
- packet requiring routine continuation context but missing exact 98P result: block;
- rejected, cancelled, expired, edited, or blocked packet cannot resume;
- edited packet cannot silently overwrite prior history;
- approval cannot authorize provider calls, external effects, live sends, cron, connectors, payments, publishing, browser/email/WhatsApp execution, destructive actions, medical decisions, emergency monitoring, or automatic caregiver alerts.

## Test Plan

Future implementation validation should include:

- contract construction tests for all typed local packets;
- state-transition tests for every valid transition;
- failure-path tests for unknown state, unknown decision, and mismatch boundaries;
- single-use resume-token tests;
- expiry tests;
- edit-versioning tests proving prior history is preserved;
- 95P integration tests for action-request and cost-confirmation packet creation;
- 96P integration tests for packet-binding evidence only;
- 98P integration tests proving routine preflight is not bypassed;
- 99P integration tests proving excluded memory is not exposed;
- 100P integration tests proving selected route and budget constraints are preserved;
- trace determinism and audit completeness tests;
- no-execution tests proving no provider call, Hermes start, external side effect, Telegram send, or async dispatch occurs.

## Expected Future Files

If a later implementation is separately authorized, expected files are likely:

- `app/action_packet_approval.py`
- `docs/reference/ROBOTICXS_ACTION_PACKET_APPROVAL_LOOP_101P_v0_1.md`
- `tests/test_action_packet_approval_101p.py`
- optional narrow integration test updates in:
  `tests/test_telegram_policy_chain_95p.py`
  `tests/test_hermes_os_runtime_contract_96p.py`
  `tests/test_routine_execution_engine_98p.py`
  `tests/test_memory_center_projection_99p.py`
  `tests/test_cost_governor_model_routing_100p.py`

These are planning expectations only. This document does not authorize creating them.

## Rollback and Compatibility Notes

- 101P should be additive to 95P through 100P, not a rewrite.
- existing 95P Action Packet shape should remain compatible by conversion or wrapper mapping.
- 100P cost-confirmation metadata should remain usable without changing 100P authority rules.
- future rollback should be able to disable 101P packet issuance without changing 95P, 98P, 99P, or 100P authority semantics.
- any future implementation must default to blocked/no-resume behavior when compatibility evidence is incomplete.

## Roadmap and Continuation Authorization Rules

- this specification does not mark 101P closed committed;
- this specification does not authorize 101P implementation;
- this specification does not authorize 102P or later;
- no next stage becomes eligible from this document alone;
- any 101P implementation requires separate human approval of the technical specification and separate implementation authorization;
- any 102P+ story or implementation requires explicit maintainer direction after 101P review.

## Approval Boundary Statement

101P technical spec is proposed for human approval only.

101P implementation is not authorized.

102P and later remain unauthorized.
