# Customer MVP Baseline 160P v0.1

`160P - Customer MVP Baseline v0` closes the first Telegram customer MVP arc with a local baseline check.

## Scope

- verify the deterministic demo loop still covers `/start`, `/status`, `/today`, `/prep`, `/memory_pending`, and `/inbox_done`;
- verify the customer-facing command surface remains coherent;
- verify setup clarity, memory review, task inbox, meeting prep, draft-only document intake, and safety language are visible;
- verify the baseline does not include secret-like values.

## Authority

160P is a local baseline contract only. It does not add commands, persistence, onboarding state, document storage, connector activation, OAuth generation, token exchange, Calendar reads or writes, Gmail reads or writes, Memory Center mutation, ProposedMemory writes, model calls, tool calls, worker dispatch, scheduler, proactive outbound sends, billing, deployment, push, merge, PR creation, or external writes beyond approved Telegram replies.
