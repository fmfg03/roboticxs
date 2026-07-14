# Pilot Metrics Snapshot v0 - 210P

210P adds `/pilot_metrics` for a local pilot metrics snapshot.

The snapshot summarizes locally injected feedback, daily loop outcomes, and usage ledger entries:

- daily loops run
- suggestion feedback
- draft created/approved outcomes
- memory changes signaled
- document reviews
- usage task count and estimated cost
- blocked actions
- top feedback tags

If local metrics are unavailable, `/pilot_metrics` shows an explicit `no_local_metrics_yet` fallback. It does not claim live analytics.

210P does not send Gmail, write Calendar, write CRM, use WhatsApp, mutate Memory Center, activate connectors, read logs, call providers, check live billing, deploy, push, merge, create PRs, or write externally beyond owner-requested Telegram replies.
