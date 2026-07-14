# Founder Daily Use Loop v0 - 202P

202P adds a repeatable founder morning routine for Telegram.

The loop is exposed as `/founder_loop` and summarizes:

- today overview;
- next useful prep;
- pending suggestions;
- pending approvals;
- pending drafts;
- pending memory reviews;
- usage/cost snapshot;
- setup warnings;
- source trace status;
- one recommended next action.

## Boundaries

202P is operational orchestration only.

It does not authorize Gmail send/archive/delete/label/modify, Calendar create/update/delete, CRM writes, WhatsApp, autonomous background actions, destructive actions, multi-user logic, billing, connector activation, live billing reconciliation, Memory Center mutation, deployment, push, merge, PR creation, or external writes beyond existing owner-requested Telegram replies.

If live connectors are unavailable, `/founder_loop` must show explicit fallback status rather than pretending live data exists.

## Local evidence

- `app/founder_daily_use_loop.py`
- `app/runnable_telegram_robot_mvp.py`
- `tests/test_founder_daily_use_loop_202p.py`
