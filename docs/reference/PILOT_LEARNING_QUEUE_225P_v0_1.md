# Pilot Learning Queue 225P v0.1

225P adds `/pilot_learnings` as a local prioritized product learning queue for the friendly pilot.

The command answers one pilot question: what should Roboticxs fix or improve next based on real dogfooding and pilot signals?

## Telegram surface

`/pilot_learnings` renders:

- total local learning items
- priority counts for P0, P1, P2, and P3
- learning backlog with reason, source, and recommended action
- explicit fallback status when no local learning signals exist
- safety boundaries

## Local inputs

The queue can summarize injected local records from:

- feedback ledger
- pilot support issues
- pilot safety incidents
- usage/cost ledger
- pilot review session packs

## Priority policy

- P0: blocks pilot trust or safety
- P1: materially improves daily value or fixes wrong/missing-source outputs
- P2: improves UX, clarity, verbosity, or cost trend
- P3: later/nice-to-have

## Authority boundary

225P does not:

- create external tickets
- write to an external backlog
- write CRM records
- send Gmail
- write Calendar events
- use WhatsApp
- perform destructive actions
- perform external writes
- expose secrets

Approval, source trace, and usage/cost semantics remain preserved.
