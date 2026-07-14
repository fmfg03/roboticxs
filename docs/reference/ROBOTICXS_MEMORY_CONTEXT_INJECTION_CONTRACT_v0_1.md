# Roboticxs Memory Context Injection Contract v0.1

Status: 93P implemented pending review.

This document defines the `MemoryContextBlock` contract for injecting approved Roboticxs memory projections into Hermes runtime context. It is story/spec/test work only and does not implement live context injection, gateway changes, production sync, or UI.

## Context block purpose

`MemoryContextBlock` is the runtime-safe representation of selected `MemoryProjection` records. It gives Hermes bounded context for the current request while preserving that Roboticxs Memory Center remains canonical and that memory context is not authority.

## Injection requirements

Every `MemoryContextBlock` must include:

- block id;
- source of truth set to Roboticxs Memory Center;
- runtime target set to Hermes context;
- projection policy id;
- request scope;
- active skill id when present;
- list of `MemoryProjection` records;
- non-authority disclaimer;
- expiry/staleness summary;
- sensitivity summary;
- allowed-use summary;
- blocked-use summary.

Each injected projection must preserve source, approval status, scope, sensitivity, expiry/staleness, and allowed-use constraints.

Outdated or rejected memories must not be injected.

Sensitive memories must require explicit projection policy.

Boundary Memory must be ordered before preference memory.

Inferences must be labeled as inferences.

Opinions/preferences must not be represented as facts.

Caregiver memories must preserve human escalation boundaries.

## Authority boundary

Memory projection must not override Tool Authority Guard, Scope Guard, Cost Governor, or Zaubern-lite decisions.

No projection may authorize a tool/action.

No projection may silently expand a user's permissions.

No `MemoryContextBlock` may claim that Hermes runtime memory is canonical product memory.

## MemoryContextBlock schema

```json memory-context-block
{
  "packet_type":"MemoryContextBlock",
  "status":"NON_AUTHORITY_RUNTIME_CONTEXT",
  "stage":"93P",
  "source_of_truth":"Roboticxs Memory Center",
  "runtime_target":"Hermes context",
  "projection_policy_id":"memory_projection_policy_v0_1",
  "contains_boundary_memory":true,
  "contains_preference_memory":true,
  "boundary_memory_priority":"higher_than_preference_memory",
  "tool_action_authorization":false,
  "permission_expansion_authorized":false,
  "future_stage_authorized":false
}
```

## Non-claims

- no live context injection;
- no live Hermes memory provider integration;
- no runtime gateway changes;
- no production memory sync;
- no canonical memory writes;
- no tool/action authorization;
- no permission expansion;
- no 94P or later authorization.
