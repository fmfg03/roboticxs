# Feedback Ledger & Tags v0 - 204P

204P turns captured feedback into local structured ledger entries.

The ledger is exposed as `/feedback_ledger` and can show:

- feedback id;
- owner id;
- robot id;
- item id;
- item type;
- tag;
- optional redacted comment;
- source trace id;
- created timestamp;
- status.

## Boundaries

204P is local structured ledger behavior only. It does not add tuning, automatic ranking changes, background jobs, live analytics, billing, multi-user pilot behavior, or durable external storage.

It does not authorize Gmail send/archive/delete/label/modify, Calendar create/update/delete, CRM writes, WhatsApp, destructive actions, connector activation, Memory Center mutation, deployment, push, merge, PR creation, or external writes beyond existing owner-requested Telegram replies.

If no local feedback entries are injected, `/feedback_ledger` must show an explicit empty state.
