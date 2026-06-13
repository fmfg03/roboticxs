# Telegram Memory Proposal Loop v0.1

## Status

Stage 82P establishes the first Telegram-visible memory proposal loop for Roboticxs.

It builds on the 78P Hermes runtime foundation, 79P Telegram runtime bootstrap, 80P Telegram conversation loop, and 81P manual Telegram runtime smoke path.

## Decision

82P establishes a Telegram memory proposal loop.
It creates proposed-memory candidates only from explicit user memory intent.
It does not create active memory automatically.
It does not extract memory from normal conversation.
It does not scan external sources.
It does not implement Context Scan.
It does not implement retrieval.
It does not implement connectors.
It does not implement caregiver routines.
It does not implement document intake.
It does not implement voice handling.
It requires explicit user approval before a memory becomes active.

## Why this stage exists

Roboticxs should start behaving like a personal robot without silently remembering user facts.

82P adds the minimal controlled memory path for Telegram runtime messages: explicit memory intent creates an inert proposal, the user sees exactly what would be remembered, and active memory is created only after an explicit approval command.

## Memory proposal loop

```text
Telegram explicit memory intent
  -> runtime text parser
  -> proposed-memory candidate
  -> approval/rejection prompt
  -> APROBAR memoria <id> or RECHAZAR memoria <id>
  -> active MemoryItem only after approval
```

Normal conversation continues through the 80P deterministic Telegram conversation loop and does not create `ProposedMemory` or `MemoryItem` records.

## Supported user phrases

Spanish phrases:

- `recuerda que ...`
- `acuérdate que ...`
- `acuerdate que ...`
- `guarda que ...`
- `quiero que recuerdes que ...`

English phrases:

- `remember that ...`
- `save that ...`
- `please remember that ...`
- `I want you to remember that ...`

Preference phrasing is normalized deterministically. For example, `recuerda que prefiero respuestas cortas` proposes `Prefieres respuestas cortas.`

## Approval commands

Approval requires an explicit proposal ID:

```text
APROBAR memoria <id>
APPROVE memory <id>
```

Approval creates an active local `MemoryItem` from the matching pending `ProposedMemory`.

## Rejection commands

Rejection requires an explicit proposal ID:

```text
RECHAZAR memoria <id>
REJECT memory <id>
```

Rejection marks the matching pending proposal as `REJECTED` and creates no active memory.

## Active memory creation rule

Active memory is never created at proposal time.

Only a pending proposal for the same Telegram user and active robot can become active memory, and only after an explicit approval command with that proposal ID.

## Duplicate/invalid proposal behavior

Invalid proposal IDs return a safe fallback.

Duplicate approval, duplicate rejection, or rejection after approval returns an already-finalized fallback and does not create another active memory.

Creating a new proposal expires prior pending proposals for the same user and robot through the existing local memory service.

## What is intentionally not implemented

- automatic memory activation
- implicit memory extraction from normal conversation
- background memory extraction
- Context Scan
- external source scanning
- email, calendar, document, social, or CRM ingestion
- semantic deduplication
- memory ranking
- memory expiration policy beyond existing pending-proposal expiry
- Memory Center UI
- edit-memory UX
- caregiver routines
- medication or care logic
- document/PDF intake
- file download
- voice/audio handling
- retrieval
- connectors
- proactive/background suggestions
- scheduler or cron
- production deployment

## Authority boundaries

82P authorizes only explicit Telegram memory proposal and decision handling on the runtime webhook path.

It does not authorize retrieval.
It does not authorize connectors.
It does not authorize caregiver behavior.
It does not authorize document or file handling.
It does not authorize voice handling.
It does not authorize external source scanning.
It does not authorize background or proactive behavior.
It does not authorize 83P as `NEXT_ELIGIBLE`.
Validation pass does not imply staging authority.
Validation pass does not imply commit authority.

## Privacy boundaries

The proposal prompt shows the user exactly what would be remembered.

Pending proposals are inert until approval.
Rejected proposals do not become active memory.
Normal conversation is not mined for memory.
No external source is scanned for memory.

## Future stages unlocked

82P makes it possible for a future approved stage to improve memory wording, add edit-before-approval, add richer memory types, or connect controlled memory behavior to other product flows.

Those future stages require explicit maintainer authorization.

## Non-claims

82P does not claim Context Scan support.
82P does not claim retrieval support.
82P does not claim connector support.
82P does not claim caregiver support.
82P does not claim document, file, voice, or external-source memory extraction.
82P does not claim proactive memory suggestions.
