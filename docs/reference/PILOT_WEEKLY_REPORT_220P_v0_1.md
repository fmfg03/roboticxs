# Pilot Weekly Report 220P v0.1

220P adds `/pilot_weekly_report` as a local Telegram report for friendly pilot learning.

The report summarizes local pilot signals only:

- active days
- loops run
- prep packs generated
- suggestions accepted and dismissed
- drafts created, revised, and approved
- memories approved, corrected, and forgotten
- documents reviewed
- feedback tags
- issues opened and resolved
- safety incidents
- estimated cost
- top 3 product learnings

Authority boundary:

- It does not claim live analytics.
- It does not create external tickets.
- It does not send Gmail.
- It does not write Calendar events.
- It does not write CRM records.
- It does not use WhatsApp.
- It does not perform destructive actions.
- It does not expose secrets.

The command is owner-gated through the existing Telegram runtime and skill manifest gates. Empty local inputs render an explicit `no_local_weekly_data_yet` fallback instead of pretending live pilot data exists.
