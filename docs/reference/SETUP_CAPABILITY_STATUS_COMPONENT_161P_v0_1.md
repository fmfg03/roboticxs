# Setup Capability Status Component 161P v0.1

`161P - Setup Capability Status Component v0` centralizes customer-facing setup and capability status copy.

## Scope

- provide one shared full status section for `/status`;
- provide one shared compact setup block for `/start`, `/today`, `/prep`, and `/inbox`;
- keep Calendar, Gmail, Memory, Documents, and external-write boundaries consistent across product surfaces;
- reduce copy drift without adding commands or runtime authority.

## Authority

161P is a local shared-copy component only. It does not add commands, persistence, onboarding state, document storage, connector activation, OAuth generation, token exchange, Calendar reads or writes, Gmail reads or writes, Memory Center mutation, ProposedMemory writes, model calls, tool calls, worker dispatch, scheduler, proactive outbound sends, billing, deployment, push, merge, PR creation, or external writes beyond approved Telegram replies.
