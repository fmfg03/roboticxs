# Setup & Capability Status 153P v0.1

## Status

153P is a customer-facing Telegram status stage.

## Scope

153P improves the existing owner-requested `/status` reply so it clearly explains:

- what is active now
- what needs setup
- what is unavailable
- what is intentionally disabled
- what requires owner approval
- the next useful action

## Authority Boundary

153P does not add new commands, read secrets, print secrets, activate connectors, generate OAuth URLs, exchange tokens, read Calendar, read Gmail, write Calendar, write Gmail, mutate Memory Center, write ProposedMemory, call models, execute tools, dispatch workers, persist state, schedule jobs, send proactive outbound messages, bill, deploy, push, merge, or create PRs.

Telegram replies remain owner-gated and are the only approved external write already present in the existing runtime.

## Product Copy Rules

The customer-facing name is `Setup Check`.

The status surface must not use `Doctor` as user-facing copy.

Task Inbox must be described as the robot task inbox, not Gmail.
