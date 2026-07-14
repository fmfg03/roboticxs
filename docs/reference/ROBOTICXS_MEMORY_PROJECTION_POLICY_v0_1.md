# Roboticxs Memory Projection Policy v0.1

Status: 93P implemented pending review.

This document defines the policy for projecting approved Roboticxs `MemoryItem` records into Hermes runtime context. It is story/spec/test work only and does not implement a memory provider, gateway, production sync, or UI.

## Projection eligibility

A `MemoryItem` may become a `MemoryProjection` only when all of these conditions are true:

- the source of truth is Roboticxs Memory Center;
- approval status is approved;
- request scope and active skill are allowed by `MemoryUseConstraint`;
- `MemorySensitivity` is permitted by an explicit `MemoryProjectionPolicy`;
- `MemoryExpiry` is absent, still valid, or covered by an explicit review-after policy;
- the memory is not rejected, revoked, outdated, or stale beyond policy;
- projection does not authorize a tool/action or expand permissions.

Rejected memories must not be injected.

Outdated memories must not be injected.

Stale memories must not be injected unless the policy explicitly allows stale review context and labels it as stale.

Sensitive memories must require explicit projection policy.

## Priority order

Boundary Memory has higher priority than preference memory.

Caregiver escalation boundaries have higher priority than convenience, style, routine, or personalization preferences.

Safety, consent, scope, allowed-use, and escalation constraints have higher priority than personalization.

When memories conflict, choose the most restrictive valid memory and mark the conflict for review rather than blending incompatible facts.

## Representation rules

Every `MemoryProjection` must preserve:

- `MemorySource`;
- approval status;
- scope;
- `MemorySensitivity`;
- `MemoryExpiry`;
- `MemoryUseConstraint`;
- projection reason;
- inference label when applicable;
- preference label when applicable.

Inferences must be labeled as inferences.

Opinions/preferences must not be represented as facts.

Caregiver memories must preserve human escalation boundaries.

## Allowed use examples

| Memory kind | Example | Projection decision |
| --- | --- | --- |
| Boundary Memory | The user requires confirmation before external sends. | Project first and treat as boundary context. |
| Caregiver boundary | Medication ambiguity requires caregiver or clinician escalation. | Project only with explicit caregiver policy and preserve escalation. |
| Preference memory | The user prefers concise summaries. | Project after boundary memory and label as preference. |
| Inferred preference | The user may prefer morning briefings. | Project only if approved and label as inference. |
| Rejected memory | A memory candidate rejected by the user. | Do not inject. |
| Outdated memory | A stale address or old workplace. | Do not inject. |

## Non-claims

- no live Hermes memory provider integration;
- no production projection service;
- no canonical memory writes;
- no automatic memory approval;
- no tool/action authorization;
- no permission expansion;
- no 94P or later authorization.
