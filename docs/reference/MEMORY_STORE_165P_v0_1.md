# Memory Store 165P v0.1

165P is local Memory Store v0 only.

It adds a deterministic local store for owner-approved memory:

- approve a 164P context-derived candidate into an active local memory item
- add owner-provided memory
- edit active memory
- forget active memory
- pin active memory
- export active memory into the existing Telegram Memory Center visibility bundle

Minimum item fields:

- `memory_id`
- `robot_id`
- `user_id`
- `memory_type`
- `content`
- `source`
- `confidence`
- `approved_at`
- `status`
- `visibility`

## Boundaries

165P does not authorize Memory Center mutation, database migrations, remote persistence, ProposedMemory writes, Calendar writes, Gmail writes, connector activation, OAuth generation, token exchange, model calls, tool calls, worker dispatch, scheduler work, billing, deployment, push, merge, PR creation, or external writes.

The only mutation authorized by this stage is the local in-process Memory Store registry used by tests and local product surfaces.
