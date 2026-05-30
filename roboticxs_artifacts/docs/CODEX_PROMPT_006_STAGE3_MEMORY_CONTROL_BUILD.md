# CODEX PROMPT 006 — Roboticxs Stage 3 Memory Read/Control Build

## Role

You are Codex working inside the Roboticxs repository.

You must follow the existing Roboticxs coding protocol:

1. Preserve the approved scope.
2. Make only the minimum necessary changes.
3. Keep implementation deterministic where the current project uses deterministic logic.
4. Do not introduce external network calls.
5. Do not implement PDF, connectors, real Telegram send, real LLM routing, UI, billing, dashboard, or proactive triggers.
6. Preserve Stage 1 and Stage 2 behavior unless explicitly changed below.
7. Add tests for every new behavior and every repaired defect.
8. Run validation commands and report exact outputs.

## Current State

Stage 1 exists and passed validation:

Telegram text webhook → user/robot → task/task_run → skill manifest → scope guard → safety decision → model route estimate → token usage event → reply payload.

Stage 2 exists and passed validation:

Telegram memory-intent text → ProposedMemory(PENDING) → APPROVE/REJECT → MemoryItem(ACTIVE) only after approval.

Stage 2 also introduced:

- `ProposedMemory`
- `MemoryItem`
- `Task.kind` values for `GENERAL_TASK`, `MEMORY_PROPOSAL`, and `MEMORY_DECISION`
- deterministic memory extraction
- one active pending proposal per user/robot
- cross-user isolation

## Important Stage 2 Defects To Repair In Stage 3

Repair these as part of this Stage 3 build.

### Defect 1 — Safety does not gate memory proposal persistence

Current defect:

Safety is recorded during memory proposal flow, but `_process_memory_proposal()` still persists `ProposedMemory` unconditionally.

Required behavior:

- If safety returns `BLOCK`, do not create `ProposedMemory`.
- If safety returns `REFUSE_SCOPE` or equivalent professional-advice refusal path, do not create `ProposedMemory`.
- If safety returns `ASK_CONFIRMATION`, do not silently create durable memory. For Stage 3, prefer a safe reply explaining that the requested memory/action boundary needs clearer framing. Do not create `ProposedMemory` unless the request is safe as a memory proposal.
- Still create `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent` as appropriate for the turn.
- Add tests proving unsafe memory-intent text does not create `ProposedMemory`.

### Defect 2 — `my` trigger is overbroad

Current risk:

`app/memory_extraction.py` treats any text beginning with `my ` as memory intent.

Required behavior:

Keep Stage 2 deterministic, but reduce false positives.

Approved Stage 3 trigger behavior:

- Keep exact memory-intent triggers:
  - `remember that`
  - `remember this`
  - `i prefer`
  - `i usually`
  - `never`
  - `ask before`
- Narrow `my` so it only triggers for explicit profile/context patterns, for example:
  - `my name is ...`
  - `my role is ...`
  - `my company is ...`
  - `my timezone is ...`
  - `my working hours are ...`
  - `my preferred ...`
- Do not treat arbitrary text such as `my invoice is late` or `my laptop is broken` as memory intent.
- Add tests for positive and negative `my` cases.

### Defect 3 — Pending proposal expiry test missing

Required behavior:

- Keep one active pending proposal per user/robot.
- When a new proposal is created for the same user/robot, the previous `PENDING` proposal must become `EXPIRED`.
- Add a test proving this.

### Defect 4 — Source artifact hygiene

Current risk:

`roboticxs.db` sits in the repo root.

Required behavior:

- Do not commit or package runtime SQLite database files.
- Add or update `.gitignore` if needed to ignore:
  - `*.db`
  - `*.sqlite`
  - `*.sqlite3`
  - `.pytest_cache/`
  - `__pycache__/`
- If `roboticxs.db` exists in the working tree and is untracked/generated, remove it from the source tree only if safe. Report what you did.

## Stage 3 Goal

Add a narrow text-only memory read/control path.

Roboticxs must let a user:

1. Ask what the robot remembers.
2. Forget a specific memory by ID.
3. Have normal task replies load approved active memories as read-only context.

This is not a UI Memory Center. This is only Telegram-style text control.

## Stage 3 User Story

As a Roboticxs user, I can ask my robot what it remembers, remove memories I no longer want it to use, and have approved active memories inform normal task replies without creating or changing memory silently.

## Required Commands / UX

### 1. Memory Listing

Trigger:

```text
what do you remember
```

Required behavior:

- Resolve the same user/robot as the webhook already does.
- Create `Task` and `TaskRun` for the turn.
- Load only `MemoryItem(status=ACTIVE)` for that same user/robot.
- Exclude `FORGOTTEN`, `OUTDATED`, or any other non-active memory.
- Return a readable list.
- Include stable memory references usable for forgetting.
- Continue to create route/token records.

Example response:

```text
Here is what I currently remember:

1. [mem_12] Preference: You prefer short direct answers.
2. [mem_13] Boundary: Ask before sending messages to clients.

To remove one, reply: forget memory mem_12
```

If no active memories exist:

```text
I do not have any approved memories for your robot yet.
```

### 2. Memory Forgetting

Trigger:

```text
forget memory <id>
```

Required behavior:

- Resolve the same user/robot as the webhook already does.
- Create `Task` and `TaskRun` for the turn.
- Locate only an active memory belonging to the same user/robot.
- Mark the memory `FORGOTTEN`.
- Do not physically delete the row.
- Continue to create route/token records.

Example success response:

```text
Forgotten. I will no longer use that memory.
```

Example missing/not-owned response:

```text
I could not find that active memory for your robot.
```

No fuzzy matching in Stage 3.

### 3. Normal Task Memory Context

Required behavior:

- On non-memory-control normal tasks, load only `MemoryItem(status=ACTIVE)` for that same user/robot.
- Use these active memories as read-only context.
- Do not create, update, approve, reject, or forget memories during normal task handling.
- Add a simple reply indicator when active memory context was used.

Example:

```text
I can help with that. I used your saved preferences and robot limits as context for this reply.
```

If there are no active memories, preserve the existing Stage 1 reply behavior as much as possible.

## Recommended Module Boundary

Do not keep growing `app/orchestrator.py` into a monolith.

Preferred implementation:

- Add `app/memory_control.py` or equivalent for:
  - detecting memory-control commands
  - listing active memories
  - parsing `forget memory <id>`
  - marking memory as forgotten
  - returning memory context counts
- Keep `app/memory_service.py` focused on persistence rules for proposals, approvals, rejections, expiry, and memory storage.
- Keep `app/memory_extraction.py` focused on deterministic extraction only.
- Keep `app/telegram_adapter.py` unchanged unless there is a strong reason.

## Data Model Rules

No new major table is required.

Reuse:

- `MemoryItem.status = ACTIVE | OUTDATED | FORGOTTEN`

Allowed small changes:

- Add `updated_at` to `MemoryItem` if useful for `FORGOTTEN` updates.
- Add response metadata if needed, but avoid schema churn.

Do not perform destructive schema changes.

## Acceptance Criteria

Stage 3 is accepted only if all criteria pass:

### Stage 2 repair criteria

- Unsafe/prohibited memory-intent text does not create `ProposedMemory`.
- Safety decisions still persist for blocked/refused memory-intent turns.
- Overbroad `my` trigger is narrowed.
- Positive `my name is`, `my role is`, `my company is`, `my timezone is`, `my working hours are`, and `my preferred ...` cases still work.
- Negative `my invoice is late` or equivalent non-profile text does not trigger memory proposal.
- Replacing an existing pending proposal expires the previous proposal.
- Runtime database files are ignored or removed from source artifacts as appropriate.

### Stage 3 memory-control criteria

- `what do you remember` lists active memories for the same user/robot only.
- Listing excludes `FORGOTTEN` memories.
- Listing includes stable memory IDs or equivalent references usable for forgetting.
- `forget memory <id>` marks the target memory `FORGOTTEN`, not deleted.
- Forgetting is scoped to the same user and robot.
- Another user cannot forget someone else’s memory.
- Forgotten memories do not appear in memory listings.
- Forgotten memories are not loaded into normal task context.
- Normal task flow loads only `ACTIVE` memories as read-only context.
- Normal task flow does not create memory silently.
- Memory listing and forgetting turns still create `Task`, `TaskRun`, `ModelRouteDecision`, and `TokenUsageEvent`.
- Stage 1 and Stage 2 tests continue to pass.

## Required Tests

Add or update tests for:

1. List active memories for one user/robot.
2. Verify another user’s memories do not appear.
3. Forget one active memory by ID.
4. Verify forgotten memory status becomes `FORGOTTEN`.
5. Verify forgotten memory no longer appears in listings.
6. Verify forgotten memory is not loaded into normal task context.
7. Verify normal tasks still create no silent memory.
8. Verify token usage is logged on list and forget turns.
9. Verify unsafe memory-intent text does not create a `ProposedMemory`.
10. Verify overbroad `my` negative case does not trigger memory proposal.
11. Verify explicit `my name is` / profile-style trigger still creates proposal.
12. Verify old pending proposals become `EXPIRED` when replaced.
13. Rerun all existing Stage 1 and Stage 2 tests unchanged.

## Non-Goals

Do not implement:

- PDF ingestion
- document parsing
- Memory Center UI
- connectors
- email/calendar scanning
- proactive triggers
- vector search
- semantic retrieval
- real LLM extraction
- real Telegram send
- billing
- admin dashboard
- multi-provider routing changes
- payments
- external side effects

## Validation Commands

Run at minimum:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

If you add formatting or linting tooling, run it only if already present in the repo or if you explicitly justify the addition.

## Required Completion Report

After implementation, return a concise completion report with:

1. Summary
2. Files changed
3. Stage 2 repairs implemented
4. Stage 3 memory-control behavior implemented
5. Data model changes, if any
6. Test coverage added
7. Exact validation commands and outputs
8. Remaining known gaps
9. Recommended next prompt

## Recommended Next Step After Stage 3

Do not recommend PDF automatically unless Stage 3 validates.

Likely Stage 4 should be one of:

1. Stage 3 validation + Stage 4 spec, or
2. first narrow Documents/PDF skill, but only after memory control is confirmed.
