# Memory Correction Loop v0 - 209P

209P adds local memory correction receipts from Telegram.

Commands:

- `/memory_wrong <memory_id>`
- `/memory_stale <memory_id>`
- `/memory_duplicate <memory_id>`
- `/memory_merge <memory_id> <target_memory_id>`
- `/memory_never_use <memory_id>`

Each command creates a local receipt only when the memory is visible for the owner and robot. `/memory_merge` requires both memories to be visible.

209P does not mutate Memory Store, mutate Memory Center, delete source evidence, call models, activate connectors, send Gmail, write Calendar, write CRM, use WhatsApp, deploy, push, merge, create PRs, or write externally beyond owner-requested Telegram replies.
