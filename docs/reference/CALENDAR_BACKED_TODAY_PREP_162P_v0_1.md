# Calendar-Backed Today / Prep 162P v0.1

`162P - Calendar-Backed Today / Prep v0` connects the customer-facing Today and Prep surfaces to authorized read-only Calendar context.

## Scope

- use Google Calendar read-only results as the primary source for Today meeting context;
- generate a Meeting Prep Pack from Calendar-backed meeting suggestions when available;
- show sources used and sources not connected;
- fail closed with setup guidance when Calendar is unavailable;
- preserve local Memory Center approval-mode visibility only.

## Authority

162P is read-only Calendar product integration only. It does not authorize Calendar writes, Gmail reads or writes, OAuth generation, token exchange, token refresh, Memory Center mutation, ProposedMemory writes, model calls, tool calls, worker dispatch, scheduler, proactive outbound sends, billing, deployment, push, merge, PR creation, or external writes beyond approved Telegram replies.
