# Memory Review Flow 155P v0.1

## Status

155P is a customer-facing Telegram Memory Review stage.

## Scope

155P improves the existing owner-requested `/memory_pending`, `/memory_approve <candidate_id>`, and `/memory_reject <candidate_id>` replies so the user understands that Roboticxs never remembers new facts without approval.

The Memory Review surface includes:

- pending
- approved pending writeback
- rejected
- not a fact yet
- useful empty state
- local receipt boundaries

## Authority Boundary

155P does not add new commands, persist memory review state, mutate Memory Center, write ProposedMemory, execute writeback, read Calendar, write Calendar, read Gmail, write Gmail, call models, execute tools, dispatch workers, schedule jobs, send proactive outbound messages, bill, deploy, push, merge, or create PRs.

Telegram replies remain owner-gated and are the only approved external write already present in the existing runtime.

## Product Copy Rules

The customer-facing name is `Memory Review`.

Pending proposals must be described as not facts yet.

Approval creates only an `approved_pending_writeback` local receipt until a later stage explicitly approves Memory Center writeback.
