# Roboticxs Memory Center Bridge v0.1

Status: 93P implemented pending review.

This document defines the Roboticxs Memory Center Bridge contract. It is story/spec/test work only. It does not implement live Hermes memory provider integration, runtime gateway changes, production memory sync, or UI.

## Purpose

The Memory Center Bridge defines how approved canonical Roboticxs memory may be projected into Hermes runtime context without treating Hermes memory as the product memory source of truth.

Roboticxs Memory Center is canonical product memory. Hermes memory is runtime memory only. The bridge is a projection boundary, not a synchronization system, ingestion system, permission system, or writeback path.

## Required entities

`MemoryItem`: A canonical Roboticxs memory record owned by Memory Center.

`MemoryProjection`: A bounded projection of an approved `MemoryItem` into a runtime-safe form.

`MemoryProjectionPolicy`: The policy that decides whether a `MemoryItem` may be projected for a specific request, scope, skill, and sensitivity level.

`MemoryContextBlock`: The context block injected into Hermes runtime context after projection filtering.

`ProposedMemory`: A non-canonical candidate memory produced by runtime output or user conversation for later explicit review.

`MemoryWritebackRequest`: A request to review a `ProposedMemory`; it is not a canonical memory write.

`MemorySensitivity`: The sensitivity classification for a memory, including ordinary, personal, caregiver, credential-like, medical, legal, financial, and safety-critical categories.

`MemoryUseConstraint`: Allowed-use constraints such as answer personalization, boundary enforcement, caregiver escalation, safety refusal, or draft-only use.

`MemoryExpiry`: Expiry, stale-after, review-after, and revoked-state metadata used to prevent outdated context injection.

`MemorySource`: The provenance for a memory, including user-approved, caregiver-approved, imported, inferred, or system-generated candidate source labels.

## Authority invariants

Roboticxs Memory Center is canonical.

Hermes memory is runtime memory, not canonical product memory.

Approved Roboticxs `MemoryItem` records may be projected into Hermes runtime context.

Hermes runtime output may propose memory candidates, but must not write canonical memory directly.

Projection must preserve source, approval status, scope, sensitivity, expiry/staleness, and allowed-use constraints.

Boundary Memory must have higher priority than preference memory.

Sensitive memories must require explicit projection policy.

Outdated or rejected memories must not be injected.

Inferences must be labeled as inferences.

Opinions/preferences must not be represented as facts.

Caregiver memories must preserve human escalation boundaries.

Memory projection must not override Tool Authority Guard, Scope Guard, Cost Governor, or Zaubern-lite decisions.

No projection may authorize a tool/action.

No projection may silently expand a user's permissions.

94P+ must remain not authorized.

## Bridge decision order

1. Read candidate `MemoryItem` records only from Roboticxs Memory Center.
2. Reject records that are not approved, are rejected, are revoked, are expired, or are stale without a valid review policy.
3. Apply `MemoryProjectionPolicy` for request scope, active skill, sensitivity, source, and allowed use.
4. Preserve `MemorySource`, approval status, scope, `MemorySensitivity`, `MemoryExpiry`, and `MemoryUseConstraint` in every `MemoryProjection`.
5. Prioritize Boundary Memory before preference memory.
6. Label inferences as inferences and opinions/preferences as preferences.
7. Build a `MemoryContextBlock` with explicit non-authority metadata.
8. Keep Tool Authority Guard, Scope Guard, Cost Governor, and Zaubern-lite decisions outside memory projection.

## MemoryBridgeContractPacket schema

```json memory-bridge-contract-packet
{
  "packet_type":"MemoryBridgeContractPacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"93P",
  "canonical_memory_source":"Roboticxs Memory Center",
  "runtime_memory_role":"Hermes runtime memory only",
  "projection_allowed":true,
  "canonical_write_authorized":false,
  "tool_authority_authorized":false,
  "future_stage_authorized":false
}
```

## Non-claims

- no live Hermes memory provider integration;
- no runtime gateway changes;
- no production memory sync;
- no canonical memory writes;
- no automatic memory ingestion;
- no UI;
- no tool/action authorization;
- no 94P or later authorization.
