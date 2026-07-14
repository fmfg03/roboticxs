# Telegram Product Shell 150P v0.1

`150P - Telegram Product Shell v0` turns the existing owner-gated Telegram command surface into a customer-facing product shell.

The shell updates `/start`, `/help`, `/status`, and unknown-command replies so a customer can understand the robot's current capabilities, setup gaps, and approval boundaries quickly.

## Product Menu

The product shell exposes these customer-facing areas:

- Today: `/today`, `/miss`
- Brief: `/brief`, `/suggest_brief`
- Prep: `/prep <suggestion_id>`
- Tasks: `/inbox`, `/inbox_done <item_id>`, `/inbox_dismiss <item_id>`
- Memory: `/memory`, `/memory_pending`, `/memory_limits`, `/memory_approve <candidate_id>`, `/memory_reject <candidate_id>`
- Setup Check: `/status`

`/inbox` remains compatible, but customer-facing copy must clarify that it is the robot task inbox, not a Gmail inbox.

## Status Boundary

`/status` reports active capabilities, unavailable or setup-dependent capabilities, intentionally disabled capabilities, and approval boundaries.

Customer-facing copy uses `Setup Check`, not `Doctor`.

## Authority Boundary

150P does not add new commands, connector activation, OAuth generation, OAuth token exchange, Calendar writes, Gmail reads or writes, Memory Center mutation, model calls, tool execution, worker dispatch, scheduler behavior, billing, deployment, push, merge, or PR creation.

150P preserves owner-gated Telegram replies as the only external write already authorized by prior Telegram stages.

## Secret Handling

The shell must not print bot tokens, OAuth tokens, owner allowlist values, secret prefixes, secret suffixes, secret lengths, raw environment values, or local secret file paths.

## Terminal Condition

`152P+` remains unauthorized. `150P` only adds a customer-facing product shell over the existing Telegram command surface. `151P` later improved the customer-facing Meeting Prep Pack product flow only.
