# Pilot User Provisioning 215P v0.1

215P adds local Telegram/admin pilot provisioning visibility through `/pilot_provision <telegram_id> <alias>` and `/pilot_allowlist`.

The provisioning receipt shows role, robot id, allowed Telegram user id, enabled skill packages, connector status, pilot start date, and pilot status. It is strict allowlist only: a rendered provisioning receipt does not modify Telegram owner ids, create open signup, activate connectors, persist accounts, or grant live access.

Safety boundary: 215P is local allowlist evidence only. It does not send invites, provision external accounts, activate connectors, send Gmail, modify Gmail, write Calendar events, write CRM records, access WhatsApp, mutate memory directly, perform destructive actions, deploy, push, merge, create PRs, or introduce 216P behavior.
