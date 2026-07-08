# Friendly Pilot Launch Baseline 222P v0.1

222P adds `/pilot_launch` as a local controlled launch baseline for the first friendly pilot.

The launch baseline ties together:

- allowlisted pilot user
- consent text
- Day 0-Day 7 runbook
- owner/robot data boundary
- daily loop
- feedback capture
- issue capture
- safety log
- weekly report
- exit/data-removal flow

Authority boundary:

- It does not send invites.
- It does not activate connectors.
- It does not claim live pilot data.
- It does not send Gmail.
- It does not write Calendar events.
- It does not write CRM records.
- It does not use WhatsApp.
- It does not perform destructive actions.
- It does not create external writes.
- It does not expose secrets.

The command is an integration checklist and launch receipt only. If live connectors or local evidence are unavailable, the baseline requires explicit fallback status instead of fake data.
