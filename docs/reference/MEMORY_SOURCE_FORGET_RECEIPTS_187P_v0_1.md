# Memory Source & Forget Receipts 187P v0.1

187P is Memory Source & Forget Receipts v0 only.

## Purpose

Expose approved memory provenance in Telegram and create local owner-requested receipts for forget/edit requests without mutating Memory Center, Memory Store, or source evidence.

## Telegram Surface

- `/memory` continues to show read-only Memory Center visibility and now appends local source receipts for visible approved memories.
- `/memory_forget <memory_id>` creates a local forget receipt only.
- `/memory_edit <memory_id> <text>` creates a local edit receipt only when the id matches a visible approved memory.
- `/memory_edit <candidate_id> <text>` keeps the existing pending proposal edit flow when the id is not a visible approved memory.

## Receipt Fields

Memory source receipts include:

- memory id
- memory kind
- bounded or redacted summary
- source
- source stage when available
- approved-at timestamp when available
- visibility
- status
- scopes
- allowed uses

Forget and edit receipts include:

- requested memory id
- matched visible memory flag
- local receipt-created flag
- blocked status for missing or invisible ids
- disabled mutation and external action flags

## Safety Boundaries

- Memory Center mutation: disabled
- Memory Store mutation: disabled
- ProposedMemory writes: disabled
- Source evidence deletion: disabled
- Connector reads/writes: disabled
- Calendar writes: disabled
- Gmail writes: disabled
- Model calls: disabled
- Tool calls: disabled
- Worker dispatch: disabled
- External writes: disabled

Credential-like memory is always redacted from Telegram receipts. Sensitive memory is bounded or redacted before display.

## Non-Authority

187P does not authorize Memory Center mutation, database migrations, remote persistence, source evidence deletion, vector or graph memory, automatic extraction, model-assisted editing, connector activation, Calendar writes, Gmail writes, Telegram live sends beyond already approved command replies, tool calls, worker dispatch, scheduler/proactive sends, billing, deployment, push, merge, PR creation, or 188P behavior.
