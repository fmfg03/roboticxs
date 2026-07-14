# Inbox Item Decision 147P v0.1

`147P - Inbox Resolve / Dismiss v0` adds owner-requested local decision receipts for inbox items.

Supported commands:

- `/inbox_done <item_id>`
- `/inbox_dismiss <item_id>`

The receipt is local and deterministic. It does not delete source evidence, write persistent state, mutate Memory Center, write Calendar, or dispatch workers.

## Terminal Condition

`148P+` remains unauthorized. `147P` only adds local inbox item decision receipts.
