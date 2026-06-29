# Suggestion Quality Tuning v0 - 206P

206P uses local feedback ledger entries and founder loop outcome signals to produce deterministic suggestion ranking decisions.

The tuning view is exposed as `/suggestion_quality`.

It can promote, keep, downgrade, or suppress suggestions using feedback tags such as useful, wrong, noisy, stale, missing_source, and not_useful.

206P is local tuning guidance only. It does not add proactive sends, automatic execution, scheduler behavior, connector activation, Gmail send, Calendar writes, CRM writes, WhatsApp, Memory Center mutation, billing, deployment, push, merge, PR creation, or external writes beyond owner-requested Telegram replies.
