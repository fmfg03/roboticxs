# Today / Brief Product Flow 152P v0.1

## Status

152P is a customer-facing Telegram product flow stage.

## Scope

152P improves the existing owner-requested `/today` and `/brief` replies so they read as product surfaces instead of internal stage receipts.

`/today` presents:

- meetings
- open loops
- things waiting for the owner
- brief options
- known memory
- suggested next action
- blocked or unavailable sources
- boundaries

`/brief` presents:

- meeting context
- agenda
- watchpoints
- suggested prep
- safe next step
- boundaries

## Authority Boundary

152P does not add new commands, activate connectors, generate OAuth URLs, exchange tokens, read Gmail, write Calendar, write Gmail, mutate Memory Center, write ProposedMemory, call models, execute tools, dispatch workers, persist state, schedule jobs, send proactive outbound messages, bill, deploy, push, merge, or create PRs.

Telegram replies remain owner-gated and are the only approved external write already present in the existing runtime.

## Failure Behavior

If Calendar is unavailable, `/today` and `/brief` continue to fail closed into deterministic local context and explicitly list Calendar as a blocked or unavailable source.

Pending memory proposals remain pending. They are never rendered as approved facts.
