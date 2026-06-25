# Brief Memory Proposal 144P v0.1

`144P - Brief-Derived Memory Proposal v0` adds deterministic memory candidates derived from the active owner-requested Meeting Prep Pack flow.

The candidates are shown in `/prep <suggestion_id>` as pending owner review. They are not treated as facts and are not written to Memory Center or ProposedMemory storage.

## Authority Boundary

`144P` does not authorize Memory Center mutation, ProposedMemory writes, approval decisions, Calendar writes, model calls, tool calls, worker dispatch, proactive sends, billing, entitlement enforcement, or external writes beyond the existing owner-requested Telegram reply.

## Candidate Shape

Each candidate includes:

- stable candidate id
- source stage equal to the active Meeting Prep Pack stage
- proposal stage `144P`
- suggestion id
- proposed memory text
- review reason
- approval and rejection command hints for a later approved stage
- status `pending_owner_review`

## Terminal Condition

`145P+` remains unauthorized. `144P` only adds brief-derived memory candidates that require later explicit owner approval.
