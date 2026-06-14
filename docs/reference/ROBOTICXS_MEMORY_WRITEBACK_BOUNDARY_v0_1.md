# Roboticxs Memory Writeback Boundary v0.1

Status: 93P implemented pending review.

This document defines the writeback boundary for Hermes runtime output that may propose memory candidates. It is story/spec/test work only and does not implement canonical memory writes, production sync, runtime gateway changes, or UI.

## Boundary

Hermes runtime output may produce `ProposedMemory` candidates.

Hermes runtime output must not write canonical memory directly.

A `MemoryWritebackRequest` is a review request for a `ProposedMemory`, not a canonical memory write.

Only Roboticxs Memory Center may accept, reject, modify, expire, or deactivate canonical `MemoryItem` records through a separately authorized product path.

## Required writeback metadata

Every `MemoryWritebackRequest` must preserve:

- proposed memory text;
- `MemorySource`;
- source transcript or event reference when allowed;
- source actor;
- proposed scope;
- proposed `MemorySensitivity`;
- proposed `MemoryUseConstraint`;
- proposed `MemoryExpiry`;
- whether the proposal is a fact, inference, opinion, or preference;
- reason for proposal;
- user-review requirement.

Inferences must be labeled as inferences.

Opinions/preferences must not be represented as facts.

Sensitive proposed memories must require explicit review policy before they can become canonical.

Caregiver proposed memories must preserve human escalation boundaries and must not downgrade caregiver or clinician review.

## Forbidden writeback behavior

Hermes must not directly create canonical `MemoryItem` records.

Hermes must not directly approve `ProposedMemory`.

Hermes must not silently convert runtime memory into product memory.

Hermes must not use memory writeback to authorize a tool/action.

Hermes must not use memory writeback to silently expand a user's permissions.

Hermes must not write credential-like, medical, legal, financial, caregiver, or safety-critical memory without explicit future policy and review.

## MemoryWritebackRequest schema

```json memory-writeback-request
{
  "packet_type":"MemoryWritebackRequest",
  "status":"NON_CANONICAL_REVIEW_REQUEST",
  "stage":"93P",
  "proposed_memory_type":"ProposedMemory",
  "canonical_write_authorized":false,
  "requires_user_review":true,
  "source":"hermes_runtime_output",
  "sensitivity":"personal",
  "use_constraint":"answer_personalization_only",
  "fact_status":"preference",
  "future_stage_authorized":false
}
```

## Non-claims

- no canonical memory writes;
- no production memory sync;
- no live Hermes memory provider integration;
- no automatic approval;
- no UI;
- no tool/action authorization;
- no 94P or later authorization.
