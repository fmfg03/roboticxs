# Live Smoke Script v0 - 201P

201P adds a manual live smoke script for running the controlled customer pilot from Telegram.

The script gives the operator:

- prerequisites;
- ordered Telegram commands;
- expected result for each command;
- acceptable explicit fallback for unavailable sources;
- stop conditions;
- pass condition;
- safety boundaries.

## Customer behavior

Telegram exposes `/live_smoke` as an owner-requested smoke guide.

The smoke path checks `/start`, `/pilot_pack`, `/pilot_audit`, `/daily_brief`, `/prep`, `/suggestions`, `/drafts`, `/usage`, and `/pilot`.

The run passes only when Francisco can complete the demo with real sources or explicit fallback, source trace, approval boundaries, and usage/cost visibility.

## Boundaries

201P is script-only and manual.

It does not authorize automated live smoke execution, background jobs, connector activation, OAuth generation, token exchange, Gmail send/archive/delete/label/modify, Calendar create/update/delete, CRM writes, WhatsApp, external destructive actions, live billing reconciliation, new provider calls, Memory Center mutation, persistence expansion, deployment, push, merge, PR creation, or external writes beyond existing owner-requested Telegram replies.

## Local evidence

- `app/live_smoke_script.py`
- `app/runnable_telegram_robot_mvp.py`
- `tests/test_live_smoke_script_201p.py`
