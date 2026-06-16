# Cost Governor / Model Routing Runtime v0

Status: 100P technical spec approved and implemented locally pending review.

100P implementation was explicitly authorized before build.

101P and later remain unauthorized.

## Purpose

100P defines a deterministic local runtime skeleton for cost authority and model-routing authority before any execution path that could reach a model-backed, routine-backed, async-delegation, Hermes, or future council-style execution surface.

The stage exists to prove that Roboticxs can:

- classify task cost/routing needs locally;
- estimate token and cost exposure deterministically from local inputs only;
- choose the cheapest adequate eligible model for a task;
- block over-budget or unsafe work before execution;
- require confirmation for expensive-but-otherwise-allowed work; and
- preserve cost authority as data-only policy output rather than execution authority.

This specification does not authorize live providers, billing, credential validation, async delegation dispatch, multi-model execution, or 101P+.

## User Story Basis

This technical specification is derived from the approved 100P user story and acceptance criteria supplied by the maintainer on 2026-06-17.

The story and technical specification were approved before implementation.

Implementation authorization was granted as a separate explicit maintainer step before the local 100P build.

## Recommendation

Recommend 100P as a deterministic local runtime skeleton after separate technical-spec approval and later scoped implementation approval.

A spec-only stage would not be enough to prove the interaction boundaries with 95P, 96P, 98P, and future async delegation. A broader implementation would create unnecessary provider, billing, and execution risk. The intended implementation depth for a later approved build is a local, fixture-driven, data-only policy slice.

## Authorization State

- 95P: closed committed
- 96P: closed committed
- 97P: closed committed
- 98P: closed committed
- 99P: closed committed
- 100P: technical specification approved
- 100P implementation: authorized and implemented locally pending review
- 101P and later: unauthorized

No part of this document authorizes:

- live provider/model calls;
- live Telegram sends;
- live Hermes startup;
- live cron scheduling;
- async delegation dispatch;
- multi-model council execution;
- database migration;
- external writes, payments, publishing, browser/email/WhatsApp execution, destructive actions, medical decisions, emergency monitoring, or automatic caregiver alerts.

## Existing Contract Alignment

- 65P remains the canonical budget authority taxonomy baseline. 100P specializes it for deterministic local runtime cost/model-routing decisions, but does not replace its authority framing.
- 88P routine cost policy remains the pre-agent wake baseline. 100P extends the preflight surface from routine wake policy into local task cost/model-route decisions.
- 95P remains the Telegram policy-chain entrypoint. 100P must execute downstream of command/scope/tool policy and upstream of any Hermes/model-backed execution path.
- 96P remains the Hermes packet-binding layer. Hermes is runtime substrate, not cost authority.
- 98P remains responsible for routine preflight ordering. 100P adds cost preflight before any post-preflight execution path that could reach Hermes or future model/provider paths.
- 99P remains separate from cost authority. Memory may inform classification and context size estimation but cannot grant budget approval, model approval, or execution authority.

## Scope

100P defines a local deterministic decision boundary that:

- accepts typed local inputs for task class, routing mode, sensitivity, context estimates, and budget policy;
- evaluates fixture-backed model catalog candidates without live provider calls;
- returns one of `allow`, `downgrade`, `require_confirmation`, or `block`;
- emits inspectable trace records for request-level and candidate-level decisions;
- binds into 95P, 96P, and 98P without expanding tool, memory, permission, or external authority;
- defines the local gate shape that future async delegation must pass before dispatch;
- keeps all results bounded, data-only, and non-authority-expanding.

## Non-Goals

- No live provider/model execution.
- No billing reconciliation, invoice accuracy, payment enforcement, or subscription metering.
- No credential validation, BYOK secret checks, or production key use.
- No external network calls.
- No database migrations or persistence expansion beyond local fixtures in a later approved implementation.
- No Telegram delivery changes.
- No Hermes startup changes.
- No async delegation dispatch implementation.
- No multi-model/council runtime.
- No UI or endpoint expansion.
- No canonical memory writes or memory authority expansion.
- No authorization of 101P or later.

## Shared Vocabularies

```text
TaskClass =
  simple_classification | extraction | drafting | research | reasoning |
  tool_planning | sensitive_review | long_context | creative |
  routine | async_delegation

RoutingMode =
  economy | balanced | premium | byok

CostDecision =
  allow | downgrade | require_confirmation | block

BudgetState =
  within_budget | near_limit | confirmation_required | over_budget |
  policy_invalid

CapabilityTier =
  basic | standard | advanced | premium

TrustLevel =
  trusted | constrained | unsafe | untrusted

AvailabilityState =
  available | unavailable

SensitivityClass =
  ordinary | personal | caregiver | medical | legal | financial |
  safety_critical
```

Unknown enum values are invalid and must produce a blocking result with trace.

## Typed Local Contracts

The following contracts are normative for the local 100P implementation and any later revisions. This specification now has matching runtime code.

### BudgetPolicy

Local budget-authority policy for one cost evaluation context.

| Field | Type | Rule |
| --- | --- | --- |
| `policy_id` | `str` | Required stable identifier. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `routing_mode_allowlist` | `tuple[RoutingMode, ...]` | Allowed routing modes for the context. |
| `default_routing_mode` | `RoutingMode` | Must be in allowlist. |
| `max_estimated_cost_usd` | `float` | Hard block threshold. |
| `confirmation_cost_usd` | `float` | Confirmation threshold below or equal to hard max. |
| `max_input_tokens` | `int` | Hard context/input ceiling. |
| `max_output_tokens` | `int` | Hard output ceiling. |
| `long_context_confirmation_tokens` | `int` | Threshold for confirmation or block logic. |
| `byok_allowed` | `bool` | Local-only allowance for BYOK mode. |
| `async_delegation_allowed` | `bool` | Future gate placeholder; false means local block. |
| `premium_allowed_without_confirmation` | `bool` | Usually false. |
| `allowed_task_classes` | `tuple[TaskClass, ...]` | Hard allowlist. |
| `sensitive_task_min_tier` | `CapabilityTier` | Minimum capability for sensitive work. |
| `unsafe_model_block` | `bool` | Must be true in 100P. |
| `untrusted_model_block` | `bool` | Must be true in 100P. |
| `requires_trace` | `bool` | Must be true. |

Invariants:

- missing or malformed policy blocks the request;
- `confirmation_cost_usd` must be less than or equal to `max_estimated_cost_usd`;
- `routing_mode_allowlist` must not be empty;
- `byok` mode requires `byok_allowed=true`;
- `async_delegation` tasks require `async_delegation_allowed=true` and still remain future-blocked in 100P.

### TaskCostRequest

Local request describing one cost/model-routing evaluation.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Required stable request id. |
| `owner_id` | `str` | Required owner boundary. |
| `robot_id` | `str` | Required robot boundary. |
| `task_class` | `TaskClass` | Required. |
| `routing_mode` | `RoutingMode` | Required. |
| `sensitivity` | `SensitivityClass` | Required. |
| `requires_tools` | `bool` | Capability filter only; not tool authority. |
| `requires_long_context` | `bool` | Signals long-context routing/filtering. |
| `input_chars_estimate` | `int` | Deterministic local estimate input. |
| `expected_output_chars` | `int` | Deterministic local estimate output. |
| `context_item_count` | `int` | Local context-size hint. |
| `active_skill_id` | `str \| None` | Optional classification context only. |
| `memory_context_used` | `bool` | Indicates 99P context informed estimation only. |
| `routine_requested` | `bool` | True for 98P routine path. |
| `async_delegation_requested` | `bool` | Future gate shape only. |
| `authority_expansion_requested` | `bool` | Must reject/block if true. |

Invariants:

- request fields are local-only and deterministic;
- memory-derived hints cannot grant authority;
- async delegation requests remain blocked in 100P even when shaped correctly;
- authority expansion requests must not succeed.

### TokenUsageEstimate

Deterministic local estimate record.

| Field | Type | Rule |
| --- | --- | --- |
| `estimated_input_tokens` | `int` | Derived from local request only. |
| `estimated_output_tokens` | `int` | Derived from local request only. |
| `estimated_total_tokens` | `int` | Sum of input and output estimates. |
| `estimation_basis` | `str` | Stable reason text such as `char_ratio_fixture_v0`. |
| `long_context_applied` | `bool` | True when long-context adjustment was applied. |

Invariants:

- all values are estimates, not billing truth;
- no provider response data may influence the record in 100P.

### ModelCatalogEntry

Local fixture-backed candidate model description.

| Field | Type | Rule |
| --- | --- | --- |
| `provider_id` | `str` | Local provider label only. |
| `model_id` | `str` | Local model label only. |
| `display_name` | `str` | Human-readable label. |
| `enabled` | `bool` | Hard filter. |
| `availability` | `AvailabilityState` | Hard filter. |
| `routing_modes` | `tuple[RoutingMode, ...]` | Modes supported by this entry. |
| `task_classes` | `tuple[TaskClass, ...]` | Supported task classes. |
| `max_context_tokens` | `int` | Hard context limit. |
| `capability_tier` | `CapabilityTier` | Used for adequacy checks. |
| `trust_level` | `TrustLevel` | Sensitive-task safety filter. |
| `safe_for_sensitive` | `bool` | Hard filter for sensitive classes. |
| `supports_tools` | `bool` | Capability filter only. |
| `supports_long_context` | `bool` | Long-context filter. |
| `estimated_input_cost_per_1k_usd` | `float` | Local fixture only. |
| `estimated_output_cost_per_1k_usd` | `float` | Local fixture only. |
| `selection_priority` | `int` | Stable deterministic tie-breaker. |

Invariants:

- unavailable, unsafe, or untrusted models are not eligible for sensitive tasks;
- pricing fields are local fixture values only;
- `byok` entries still remain local placeholders in 100P.

### ModelRouteDecision

Candidate selection output when a route exists.

| Field | Type | Rule |
| --- | --- | --- |
| `selected_provider_id` | `str \| None` | Null when blocked without route. |
| `selected_model_id` | `str \| None` | Null when blocked without route. |
| `selected_capability_tier` | `CapabilityTier \| None` | Preserved selected tier. |
| `selected_trust_level` | `TrustLevel \| None` | Preserved selected trust classification. |
| `candidate_models_considered` | `tuple[str, ...]` | Stable ordered candidate list. |
| `rejected_candidates` | `tuple[str, ...]` | Stable rejected candidate ids. |
| `downgrade_from_model_id` | `str \| None` | Present only for downgrade decisions. |
| `decision_reason` | `str` | Stable reason code. |

### CostTraceRecord

Inspectable trace record for request-level and candidate-level decisions.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Required request id. |
| `task_class` | `TaskClass \| str` | Preserves evaluated value. |
| `routing_mode` | `RoutingMode \| str` | Preserves evaluated value. |
| `candidate_model_id` | `str \| None` | Null for request-level trace. |
| `decision` | `CostDecision` | Stable decision enum. |
| `reason_code` | `str` | Stable machine-readable reason. |
| `estimated_input_tokens` | `int` | Preserved estimate. |
| `estimated_output_tokens` | `int` | Preserved estimate. |
| `estimated_cost_usd` | `float` | Preserved estimate. |
| `budget_state` | `BudgetState` | Preserved budget state. |
| `authority_expanded` | `bool` | Must always be false. |
| `tool_action_authorized` | `bool` | Must always be false. |
| `memory_access_expanded` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `model_provider_access_authorized` | `bool` | Must always be false in 100P. |

### CostPreflightResult

Top-level data-only result returned by 100P.

| Field | Type | Rule |
| --- | --- | --- |
| `request_id` | `str` | Matches request. |
| `decision` | `CostDecision` | `allow`, `downgrade`, `require_confirmation`, or `block`. |
| `budget_policy_id` | `str \| None` | Null only for invalid policy block. |
| `token_estimate` | `TokenUsageEstimate` | Required on validly parsed requests. |
| `route_decision` | `ModelRouteDecision \| None` | Null only when no route exists or block occurs before routing. |
| `estimated_cost_usd` | `float` | Local deterministic estimate. |
| `confirmation_required` | `bool` | True only for `require_confirmation`. |
| `blocked` | `bool` | True only for `block`. |
| `trace` | `tuple[CostTraceRecord, ...]` | Required inspectable trace. |
| `data_only` | `bool` | Must always be true. |
| `tool_action_authorization` | `bool` | Must always be false. |
| `permission_expansion_authorized` | `bool` | Must always be false. |
| `memory_access_authorized` | `bool` | Must always be false. |
| `external_effect_authorized` | `bool` | Must always be false. |
| `model_provider_access_authorized` | `bool` | Must always be false in 100P. |
| `execution_authorized` | `bool` | Must always be false. |

## Deterministic Estimation Rules

100P must not use live provider tokenizers or billing APIs.

The local deterministic estimate should use a stable documented fixture method, for example:

1. derive input tokens from `input_chars_estimate` using a conservative local ratio;
2. derive output tokens from `expected_output_chars` using the same local ratio;
3. add a bounded long-context overhead only when `requires_long_context=true`;
4. apply task-class-specific conservative output floors where needed;
5. calculate estimated cost using only `ModelCatalogEntry` fixture prices.

The exact coefficients must be fixed in the later implementation and recorded in the trace as `estimation_basis`.

## Decision Rules

The governor evaluates in this order:

1. Validate request enums and policy integrity.
2. Reject authority-expansion attempts.
3. Compute deterministic token estimate.
4. Enforce hard budget ceilings.
5. Enforce routing mode and BYOK policy.
6. Filter candidate catalog entries by enablement, availability, task class, context limit, long-context support, and tool capability need.
7. Apply sensitive-task filters:
   - block `unsafe`
   - block `untrusted`
   - block `unavailable`
   - block below required capability tier
8. Score eligible candidates deterministically for the requested routing mode:
   - `economy`: choose cheapest adequate model
   - `balanced`: choose cheapest model that still satisfies adequacy and policy thresholds
   - `premium`: choose strongest allowed model, but require confirmation when policy demands it
   - `byok`: choose only local BYOK-allowed placeholder entries
9. Compare selected estimate against confirmation and hard block thresholds.
10. Return `allow`, `downgrade`, `require_confirmation`, or `block`.

Tie-breaking must be deterministic and based on:

1. policy adequacy,
2. estimated total cost ascending,
3. capability tier descending when required,
4. `selection_priority`,
5. stable `(provider_id, model_id)` lexical ordering.

## Decision Semantics

### `allow`

Returned when:

- request and policy are valid;
- at least one eligible model exists;
- estimated cost is within hard and confirmation-free thresholds;
- no downgrade is required;
- no confirmation is required.

`allow` is still data-only. It does not authorize execution by itself.

### `downgrade`

Returned when:

- a higher-cost or stronger route was requested or implied;
- a cheaper adequate route exists and policy prefers it;
- the downgraded route remains within policy and sensitivity constraints.

The result must include both the original intended route class and the cheaper selected route in trace and route metadata.

### `require_confirmation`

Returned when:

- estimated cost exceeds `confirmation_cost_usd` but not hard max;
- long-context work crosses a configured confirmation threshold;
- premium routing is otherwise allowed but requires explicit confirmation;
- an expensive route is adequate and legal but should not execute silently.

The result must be Action Packet-compatible in shape, but must not itself create or bind a tool/action authority grant.

### `block`

Returned when:

- task class or routing mode is unknown;
- budget policy is missing or invalid;
- no eligible model exists;
- estimated cost exceeds hard budget;
- sensitive task has only unsafe/untrusted/unavailable/underpowered candidates;
- long-context work exceeds hard limits;
- BYOK is requested without local allowance;
- async delegation is requested without valid preflight allowance;
- authority expansion is requested.

## Failure Paths

| Failure path | Required result |
| --- | --- |
| Unknown task class | `block` with trace reason `blocked_unknown_task_class`. |
| Unknown routing mode | `block` with trace reason `blocked_unknown_routing_mode`. |
| Missing or invalid budget policy | `block` with trace reason `blocked_invalid_budget_policy`. |
| No eligible model | `block` with trace reason `blocked_no_eligible_model`. |
| Over budget | `block` with trace reason `blocked_over_budget`. |
| Estimated cost above confirmation threshold | `require_confirmation` with trace reason `confirmation_cost_threshold`. |
| Sensitive task with only unsafe/low-trust candidates | `block` with trace reason `blocked_sensitive_candidate_policy`. |
| Long-context task exceeding configured limits | `block` or `require_confirmation` according to policy; trace required. |
| BYOK requested without local BYOK allowance | `block` with trace reason `blocked_byok_not_allowed`. |
| Cost result used as tool/action authority | `block` or reject with trace reason `blocked_authority_expansion_attempt`. |
| Future async delegation request without cost preflight | `block` with trace reason `blocked_async_without_cost_preflight`. |

## Integration Rules

### 95P Telegram Policy Chain

100P integrates into 95P after command/scope/tool policy and after any bounded 99P context shaping used for task estimation, but before any Hermes adapter or future model/provider adapter path.

Required 95P invariants:

- 100P must not bypass 90P/91P/92P policy decisions;
- blocked 95P requests remain blocked regardless of 100P result;
- 100P output is attached as non-authority cost context only;
- `require_confirmation` must be representable as Action Packet-compatible metadata without skipping existing policy controls;
- 95P blocked and confirmation-required actions must still not reach Hermes.

### 96P Hermes OS Runtime Contract

100P should later add a local `CostPreflightPacket`-style binding or equivalent extension to the 96P contract.

Required 96P invariants:

- budget approval is not tool/action authority;
- Hermes remains substrate, not cost authority;
- TaskRunRecord may record cost preflight evidence and selected route metadata;
- blocked or confirmation-required cost results do not become execution permission by packet binding alone.

### 98P Routine Execution Engine

100P must run after 98P wake/manual/budget/forced-failure preflight succeeds and before any post-preflight path that could reach Hermes or a future model/provider adapter.

Required 98P invariants:

- preflight-stopped routines still do not call Hermes;
- cost-blocked routines do not call Hermes;
- cost-blocked routines do not dispatch async delegation;
- cost-confirmation-required routines remain locally represented and non-executing;
- routine cost preflight remains auditable.

### 99P Memory Projection

99P remains separate from cost authority.

Permitted 99P influence:

- task-class hints;
- context-size hints;
- long-context estimation hints.

Forbidden 99P influence:

- budget approval;
- model trust override;
- routing mode override;
- confirmation bypass;
- execution authorization.

## Future Async-Delegation Gating Shape

100P does not implement async delegation.

It must define the local gate shape proving that future `async_delegation` tasks cannot dispatch without cost preflight.

Required future gate shape:

```text
AsyncDelegationRequest
  -> 100P cost preflight
  -> if decision != allow then no dispatch
  -> if decision == allow, dispatch still requires later stage authorization
```

Required 100P invariants for future async delegation:

- `async_delegation` is a first-class `TaskClass`;
- absence of a valid 100P result blocks dispatch;
- `require_confirmation` blocks dispatch until a later approved confirmation path exists;
- `allow` in 100P still does not authorize dispatch by itself;
- multi-model/council execution must also pass the same preflight family later.

## Trace Requirements

Every result must emit inspectable trace records including:

- task class;
- routing mode;
- candidate models considered;
- selected model if any;
- estimated tokens;
- estimated cost;
- budget state;
- decision reason;
- authority flags.

Trace must not imply execution permission.

All authority flags remain false in 100P.

## Test Plan For Later Approved Implementation

This section is now materially covered by the local 100P implementation and tests.

### Unit Coverage

- contract validation for all typed local contracts;
- deterministic token estimation;
- candidate filtering by task class, context, tools, long-context support, routing mode, availability, trust, and sensitivity;
- downgrade selection correctness;
- confirmation threshold behavior;
- hard budget block behavior;
- BYOK local-only behavior;
- authority-expansion rejection behavior;
- async delegation gate-shape blocking.

### Integration Coverage

- 95P consumes a `CostPreflightResult` without bypassing command/scope/tool/memory policy;
- 96P binds cost preflight as non-authority runtime evidence;
- 98P allowed routines run cost preflight before any Hermes/model path;
- 98P preflight-stopped routines still do not invoke cost-governed execution paths that reach Hermes;
- 99P memory hints affect estimation only, not authority.

### Regression Coverage

- 95P, 96P, 98P, and 99P behavior remains intact;
- 101P+ remains unauthorized in canonical tests;
- no network/provider execution surfaces are introduced.

### Expected Later Test Files

- `tests/test_cost_governor_100p.py`
- `tests/test_telegram_policy_chain_95p.py`
- `tests/test_hermes_os_runtime_contract_96p.py`
- `tests/test_routine_execution_engine_98p.py`
- `tests/test_memory_center_projection_99p.py`
- `tests/test_canonical_roadmap.py`
- `tests/test_roadmap_continuation_authorization_gate.py`

## Expected Future Files For An Approved Implementation

The later scoped implementation would likely touch only a narrow, local set of files:

- `app/cost_governor.py`
- `app/model_routing.py`
- `app/telegram_policy_chain.py`
- `app/hermes_os_contract.py`
- `app/routine_execution_engine.py`
- `docs/reference/COST_GOVERNOR_MODEL_ROUTING_RUNTIME_100P_v0_1.md`
- `tests/test_cost_governor_100p.py`
- existing 95P/96P/98P roadmap or contract tests only as needed

This file list is now substantially realized in the local 100P implementation.

## Rollback And Compatibility Notes

- 100P should be additive to 95P/96P/98P/99P.
- If a later implementation must be rolled back, removing 100P should restore prior 95P/96P/98P/99P execution behavior without rewriting their authority boundaries.
- 100P must not require schema migration or provider credential changes in v0.
- Existing local stubs and packet contracts should continue to function when 100P is absent.
- BYOK remains representable as local policy/config shape even if no later live provider wiring exists.

## Implementation Constraints For A Later Approved Build

- No live provider calls.
- No network calls.
- No real token reconciliation.
- No billing APIs.
- No credential checks.
- No production execution.
- No tool, permission, memory, or external authority expansion.
- No 101P authorization.

## Approval Gate

This document was approved before implementation and remains the normative contract for the local 100P build.

At build time, the repo had:

1. explicit human approval of this technical specification;
2. explicit authorization to implement 100P;
3. explicit confirmation that 101P and later remain unauthorized.
