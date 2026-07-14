# Telegram Active Memory Forget v0.1

## Status

Stage 84P is implemented pending review.

This document does not authorize staging, commit, 85P, `NEXT_ELIGIBLE`, or any runtime behavior outside the approved 84P scope.

## Decision

84P adds deterministic active-memory forget commands to the Telegram runtime webhook.

It lets a Telegram MVP user forget one approved active local memory by ID for the resolved Telegram user and active robot.

It does not forget pending proposals.
It does not forget rejected proposals.
It does not reveal whether an ID belongs to another user or robot.
It does not bulk forget memories.
It does not edit or replace memory.
It does not add retrieval or Context Scan.

## Runtime path

84P targets only:

```text
POST /api/telegram/runtime/webhook
```

It does not change the legacy Telegram webhook:

```text
POST /api/telegram/webhook
```

## Intent precedence

The runtime memory branch uses this strict order:

```text
approval/rejection
  -> explicit memory proposal
  -> active memory forget
  -> active memory recall
  -> generic conversation
```

Forget commands never create memory. Memory proposal matching remains higher precedence than forget matching.

## Supported forget phrases

Spanish:

- `olvida memoria <id>`
- `olvidar memoria <id>`
- `borra memoria <id>`
- `elimina memoria <id>`
- `forget memoria <id>`

English:

- `forget memory <id>`
- `delete memory <id>`
- `remove memory <id>`
- `forget memoria <id>`

Matching is deterministic and local. It does not use fuzzy matching or LLM-based intent classification.

## Success responses

Spanish:

```text
Listo. Olvidé esa memoria.
```

English:

```text
Done. I forgot that memory.
```

## Safe failure responses

Spanish:

```text
No encontré una memoria activa con ese id.
```

English:

```text
I could not find an active memory with that id.
```

The failure response is identical for missing, inactive, invalid, already-forgotten, and foreign IDs.

## Forget rule

84P reuses the existing runtime user and robot resolution.

It only transitions `ACTIVE` memory to `FORGOTTEN` when the memory ID belongs to the resolved `user_id` and `robot_id`.

It does not expose whether an unmatched ID exists in another user or robot scope.

## Recall ID visibility

84P keeps 83P recall behavior and extends listed active memory lines to include IDs:

```text
1. <memory content> [id: <memory_id>]
```

Forgotten memories are no longer listed by active memory recall.

## What is intentionally not implemented

- legacy `/api/telegram/webhook`
- schema changes
- migrations
- new tables
- retrieval
- Context Scan
- connectors
- caregiver runtime
- document or PDF handling
- voice or audio
- proactive or background jobs
- LLM intent classification
- fuzzy matching
- bulk forget
- forget everything
- memory edit, update, or replacement
- staging artifacts
- 85P
- `NEXT_ELIGIBLE`

## Non-claims

84P is not Memory Center UX.
84P is not full memory management.
84P is not deletion from durable storage.
84P is only active approved memory deactivation over the Telegram runtime path.
