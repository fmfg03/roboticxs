# Usage & Cost Ledger 188P v0.1

188P is Usage & Cost Ledger v0 only.

## Purpose

Expose local estimated task usage and cost as a customer-facing ledger. This stage builds on the 168P Token Usage + Cost Meter and keeps the product boundary explicit: local estimates only, not live billing or provider reconciliation.

## Ledger Entry

Each local entry records:

- task id
- command
- task class
- provider
- model
- model mode
- input tokens
- output tokens
- estimated cost in USD
- latency in milliseconds
- status
- failure reason
- source
- created at

## Telegram Surface

`/usage` renders a monthly local summary:

- tasks run
- estimated cost
- input/output/total tokens
- documents reviewed
- failures or blocked tasks
- most expensive task
- command breakdown
- task class breakdown
- model mode breakdown
- status breakdown

If no local ledger entries are injected, `/usage` renders an empty state and clearly states that there are no local usage records yet.

## Safety Boundaries

- Live billing: disabled
- Provider calls: disabled
- Provider reconciliation: disabled
- Connector activation: disabled
- Persistence: disabled
- External writes: disabled
- Payment enforcement: disabled
- Deployment, push, merge, and PR creation: disabled

Rendered ledger text must not print secrets, access tokens, refresh tokens, bearer tokens, auth headers, client secrets, or API keys.

## Non-Authority

188P does not authorize provider calls, billing API calls, live billing reconciliation, connector activation, model routing changes, BYOK setup, payment enforcement, database migrations, remote persistence, file persistence, external writes, deployment, push, merge, PR creation, or 189P behavior.

189P and later remain unauthorized.
