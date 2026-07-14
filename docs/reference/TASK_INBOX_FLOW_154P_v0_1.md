# Task Inbox Flow 154P v0.1

## Status

154P is a customer-facing Telegram Task Inbox stage.

## Scope

154P improves the existing owner-requested `/inbox`, `/inbox_done <item_id>`, and `/inbox_dismiss <item_id>` replies so the user sees a product task inbox instead of internal receipts.

The Task Inbox surface includes:

- pending
- done
- dismissed
- needs approval
- blocked
- useful empty state
- local receipt boundaries

## Authority Boundary

154P does not add new commands, persist inbox state, delete evidence, read Gmail, write Gmail, read Calendar, write Calendar, mutate Memory Center, write ProposedMemory, call models, execute tools, dispatch workers, schedule jobs, send proactive outbound messages, bill, deploy, push, merge, or create PRs.

Telegram replies remain owner-gated and are the only approved external write already present in the existing runtime.

## Product Copy Rules

The customer-facing name is `Task Inbox`.

The inbox must be described as the robot task inbox, not Gmail.

Done and dismissed states are local receipts only until a later stage explicitly approves persisted inbox state.
