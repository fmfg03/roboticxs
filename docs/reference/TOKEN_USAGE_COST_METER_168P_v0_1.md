# Token Usage Cost Meter 168P v0.1

168P is Token Usage + Cost Meter v0 only.

It adds a local estimated usage meter for Roboticxs task runs. The meter records and summarizes:

- provider
- model
- task class
- input tokens
- output tokens
- estimated cost
- latency
- status
- failure reason

The customer-facing summary is suitable for `/usage`-style output:

- tasks run
- estimated cost this month
- most expensive task
- documents reviewed
- model mode breakdown
- task class breakdown

## Boundaries

This is local estimated usage only, not live billing or provider reconciliation. 168P does not authorize provider calls, billing API calls, connector activation, external writes, database migrations, remote persistence, model routing changes, BYOK setup, payment enforcement, deployment, push, merge, or PR creation.

177P and later remain unauthorized.
