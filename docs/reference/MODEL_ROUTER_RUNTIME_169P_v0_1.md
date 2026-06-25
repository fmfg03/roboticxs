# Model Router Runtime 169P v0.1

169P is Model Router Runtime v0 only.

It adds a local deterministic runtime-facing router contract for Economy, Balanced, and Premium model modes.

## Routing Policy

- `SIMPLE_CLASSIFICATION` -> Economy
- `EXTRACTION` -> Economy
- `DRAFTING` -> Balanced
- `DOCUMENT_REVIEW` -> Balanced with long-context handling
- `SENSITIVE_REVIEW` -> Premium with a sensitive-boundary reminder

Every decision includes the selected provider/model label, estimated input/output tokens, estimated cost, and a human-readable explanation of why that mode was selected.

## Boundaries

169P does not authorize provider calls, raw provider switching, connector activation, model provider credentials, BYOK setup, billing reconciliation, model catalog expansion beyond local stubs, external writes, deployment, push, merge, or PR creation.

170P and later remain unauthorized.
