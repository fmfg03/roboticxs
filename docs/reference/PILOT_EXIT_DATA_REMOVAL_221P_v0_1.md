# Pilot Exit / Data Removal 221P v0.1

221P adds local Telegram receipts for pilot exit and data-removal requests:

- `/end_pilot`
- `/export_pilot_data`
- `/delete_pilot_memory`
- `/disable_pilot_connectors`

The receipts show the pilot user, requested scope, local policy, export manifest, deletion manifest, connector-disable manifest, and safety boundary.

Authority boundary:

- It does not end external accounts.
- It does not delete provider data.
- It does not mutate Memory Store.
- It does not disable live connectors.
- It does not create external exports.
- It does not send Gmail.
- It does not write Calendar events.
- It does not write CRM records.
- It does not use WhatsApp.
- It does not perform destructive actions.
- It does not expose secrets.

If data removal or connector disablement is still local-only, the receipt says so explicitly. This keeps pilot exit UX visible without pretending external deletion or connector changes happened.
