# Customer MVP Demo Pack v1 180P v0.1

## Status

180P is Customer MVP Demo Pack v1 only.

## Purpose

Provide a deterministic local demo proving the customer-facing Telegram loop from first-run surface to local export payload.

## Demo Path

The demo pack covers:

- `/start`
- `/status`
- `/today`
- `/prep <suggestion_id>`
- `/suggestions`
- `/suggestion_draft <suggestion_id>`
- `/drafts`
- `/draft_approve <draft_id>`
- `/export_text <confirmation_id>`

## Boundaries

180P does not authorize:

- Live Telegram sends beyond owner-requested replies.
- Connector activation.
- Gmail draft creation.
- Gmail send, archive, label, modify, or delete.
- Calendar writes.
- Local file writes.
- Task persistence.
- Memory Store writes.
- Memory Center mutation.
- Model calls.
- Tool calls.
- Worker dispatch.
- Scheduler or proactive sends.
- Deployment, push, merge, or PR creation.
- 181P behavior.

Every reply must say: "No external action was taken."

## Runtime Contract

- Stage id: `180P`.
- Demo status is `completed_local_customer_mvp_demo_v1`.
- Demo is deterministic and local-only.
- Demo proves today, meeting prep, suggestion, draft, confirmation, and local export payload.
- External write authority remains false.

## Non-Claims

180P does not create a hosted demo environment, live Telegram delivery, real connector reads, email sends, Gmail drafts, file writes, persistent queue state, or production onboarding. It packages a local deterministic customer MVP demo only.

185P and later remain unauthorized.
