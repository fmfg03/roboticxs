# Gmail Read-Only Context Scan 163P v0.1

`163P - Gmail Read-Only Context Scan v0` adds Gmail as a read-only context source.

## Scope

- read recent Gmail message metadata/snippets through authorized read-only access;
- detect meeting, prep, follow-up, proposal, review, and attachment signals;
- provide context signals for later Today/Prep enrichment;
- fail closed when Gmail is unavailable;
- keep Gmail distinct from the robot task inbox.

## Authority

163P is Gmail read-only context scanning only. It does not authorize Gmail send, archive, label, modify, delete, Calendar writes, Memory Center mutation, ProposedMemory writes, model calls, tool calls, worker dispatch, scheduler, proactive outbound sends, billing, deployment, push, merge, PR creation, or external writes beyond approved Telegram replies.
