# Founder Feedback Capture v0 - 203P

203P adds quick owner feedback capture for important Telegram outputs.

The loop is exposed as `/feedback <tag> <item_id> [comment]` and supports:

- useful;
- wrong;
- noisy;
- stale;
- missing_source;
- bad_draft;
- too_verbose;
- not_useful.

Supported output bindings are founder loop, daily brief, prep, suggestions, drafts, approvals, memory, documents, and pilot outputs.

## Boundaries

203P is local capture only. It creates a Telegram-visible receipt and does not persist feedback. 204P is required before feedback is stored in a ledger.

It does not authorize Gmail send/archive/delete/label/modify, Calendar create/update/delete, CRM writes, WhatsApp, autonomous background actions, destructive actions, multi-user logic, billing, connector activation, live billing reconciliation, Memory Center mutation, deployment, push, merge, PR creation, or external writes beyond existing owner-requested Telegram replies.

If a feedback command is incomplete or unsupported, the bot must show explicit usage guidance instead of pretending feedback was captured.

## Local evidence

- `app/founder_feedback_capture.py`
- `app/runnable_telegram_robot_mvp.py`
- `tests/test_founder_feedback_capture_203p.py`
