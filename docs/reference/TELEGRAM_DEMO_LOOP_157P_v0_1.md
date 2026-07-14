# Telegram Demo Loop 157P v0.1

`157P - Telegram Demo Loop v0` provides a local deterministic demo transcript for the customer-facing Telegram product.

## Scope

The demo loop covers:

- `/start`
- `/status`
- `/today`
- `/prep <suggestion_id>`
- `/memory_pending`
- `/inbox_done <item_id>`

It uses local fixtures and existing renderers only.

## Authority

157P does not send Telegram messages, activate connectors, read live Calendar or Gmail, mutate Memory Center, write ProposedMemory, persist demo state, call models, call tools, dispatch workers, schedule proactive sends, bill, deploy, push, merge, create a PR, or perform external writes.

## Output

The transcript must be deterministic and must label:

- local-only mode;
- Telegram API not called;
- disabled connector activation;
- disabled external writes;
- disabled Memory Center mutation.
