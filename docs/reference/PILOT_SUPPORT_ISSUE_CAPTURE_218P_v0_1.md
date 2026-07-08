# Pilot Support & Issue Capture 218P v0.1

218P adds local Telegram issue capture through `/report_issue`, `/report_bug`, `/report_confusing`, `/report_wrong`, `/report_missing`, and `/report_slow`.

Each issue receipt includes issue id, owner id, robot id, pilot user id, command, item id, severity, category, comment, source trace id, created timestamp, and status. It captures friction inside Roboticxs instead of relying on external chat, notes, or logs.

Safety boundary: 218P is local issue capture only. It does not create external tickets, write CRM records, send Gmail, modify Gmail, write Calendar events, access WhatsApp, mutate memory, perform destructive actions, deploy, push, merge, create PRs, or introduce 219P behavior.
