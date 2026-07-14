# Brief Memory Approval 145P v0.1

`145P - Telegram Memory Approval for Brief Proposals v0` adds owner-requested Telegram decisions for `144P` brief-derived memory candidates.

Supported commands:

- `/memory_approve <candidate_id>`
- `/memory_reject <candidate_id>`

The result is a deterministic local decision receipt only. Approval means `approved_pending_writeback`; it does not execute writeback in `145P`.

## Authority Boundary

`145P` does not authorize Memory Center mutation, ProposedMemory writes, writeback execution, Calendar writes, model calls, tool calls, worker dispatch, proactive sends, billing, entitlement enforcement, or external writes beyond the Telegram reply.

## Terminal Condition

`146P+` remains unauthorized. `145P` only adds explicit owner decision receipts for brief-derived memory candidates.
