# CODEX PROMPT 004 — Roboticxs Stage 2 Durable Memory Onboarding Build

You are working in the Roboticxs repository.

This is a scoped implementation task. Do not widen the product, do not build PDF features, do not add connectors, do not add UI, and do not replace the Stage 1 architecture.

## Current verified state

Stage 1 has been validated:

- `python3 -m pytest -q` passes with 7/7 tests.
- `python3 -m compileall app tests` passes.
- The app is a Python/FastAPI text-only control loop.
- `POST /api/telegram/webhook` exists.
- Current loop: Telegram update → normalize text → user/robot resolution → Task/TaskRun → starter skill manifest → scope guard → safety decision → stub model route estimate → token usage event → Telegram-style reply payload.
- No live Telegram send exists.
- No live LLM routing exists.
- No PDF, connectors, UI, proactive triggers, or admin dashboard exist.

Preserve this boundary.

## Goal

Implement Stage 2: durable text-only memory onboarding with explicit approval/rejection.

A Roboticxs user must be able to send a text message that contains personal or work context, receive a proposed memory back, and store it durably only after replying `APPROVE`. If the user replies `REJECT`, the proposal must be discarded and no durable memory must be created.

This is the first real product differentiator: the robot should not behave like a generic chatbot. It should start building an approved memory profile.

## Hard constraints

You MAY modify source and tests needed for Stage 2.

You MAY add new app modules and tests.

You MAY update README only if needed to document how to run the new tests or explain the Stage 2 memory flow.

You MUST NOT:

- implement PDF upload/parsing
- implement OCR
- implement email/calendar/social connectors
- implement a web Memory Center UI
- implement vector memory
- implement real LLM extraction
- implement real Telegram send
- implement billing or dashboards
- implement proactive triggers
- call external APIs in tests
- add network-dependent tests
- turn this into a multi-agent framework
- change the Stage 1 route contract unnecessarily
- remove existing tests
- weaken or bypass the safety layer

## Decisions already approved

Use these defaults. Do not ask for clarification.

### Trigger phrases

Stage 2 deterministic memory extraction should support at least:

- `remember that ...`
- `remember this ...`
- `my ...`
- `I prefer ...`
- `I usually ...`
- `never ...`
- `ask before ...`

Implementation can be simple and deterministic. No LLM extraction in Stage 2.

### Pending proposal rule

Keep only one active pending memory proposal per user/robot.

When a new proposal is created for the same user/robot, either:

- reject/expire the previous pending proposal, or
- replace it deterministically.

Pick the cleanest option and document it in a code comment or README note. The Telegram UX must remain simple.

### Approval/rejection commands

Support exact case-insensitive commands:

- `APPROVE`
- `REJECT`

These commands must resolve only the latest pending proposal for the same user and robot.

If no pending proposal exists, return a safe clarification reply and do not create a MemoryItem.

## Data model additions

Add `MemoryItem`.

Recommended fields:

- `id`
- `user_id`
- `robot_id`
- `memory_type`
- `content`
- `source`
- `status`
- `importance`
- `created_at`
- `updated_at`

Recommended `memory_type` values:

- `USER_PROFILE`
- `WORK_PREFERENCE`
- `BUSINESS_CONTEXT`
- `TASK_MEMORY`
- `BOUNDARY_MEMORY`

Recommended `status` values:

- `ACTIVE`
- `OUTDATED`
- `FORGOTTEN`

Add `ProposedMemory`.

Recommended fields:

- `id`
- `user_id`
- `robot_id`
- `task_id`
- `memory_type`
- `proposed_content`
- `source_text`
- `status`
- `created_at`
- `decided_at`

Recommended `status` values:

- `PENDING`
- `APPROVED`
- `REJECTED`
- `EXPIRED`

Optional but recommended: add a lightweight task kind/intent field if it helps keep the orchestrator legible:

- `GENERAL_TASK`
- `MEMORY_PROPOSAL`
- `MEMORY_DECISION`

Do not add this if it creates unnecessary migration churn.

## Service/module boundaries

Keep existing boundaries clean.

Expected structure:

- `telegram_adapter`: unchanged unless payload parsing truly requires a small adjustment.
- `orchestrator`: route between normal task flow, memory proposal flow, and memory decision flow.
- New `memory_extraction` module: deterministic parser only.
- New `memory_service` module: proposal creation, approval, rejection, latest pending proposal lookup.
- `safety`: continue to block or escalate prohibited/unsafe requests before durable memory writes when relevant.
- `token_usage`: reused for proposal and decision turns.
- `reply_composer`: add simple memory proposal/approval/rejection/no-pending reply text.

Do not bury policy decisions inside the Telegram adapter.

## Required behavior

### 1. Proposed memory creation

Example input:

`Remember that I prefer short direct answers.`

Expected behavior:

- Creates Task/TaskRun.
- Extracts a deterministic proposed memory.
- Creates `ProposedMemory(status=PENDING)`.
- Does NOT create `MemoryItem` yet.
- Creates token usage event.
- Returns reply similar to:

```text
I can remember this:

Preference: You prefer short direct answers.

Reply APPROVE to save it or REJECT to discard it.
```

Exact wording can differ, but must be clear and consumer-safe.

### 2. Approval

Example input:

`APPROVE`

Expected behavior:

- Resolves only latest pending proposal for that same user/robot.
- Creates one `MemoryItem(status=ACTIVE)`.
- Marks proposal `APPROVED` and sets `decided_at`.
- Creates Task/TaskRun.
- Creates token usage event.
- Returns reply similar to:

```text
Saved to your robot memory.
```

### 3. Rejection

Example input:

`REJECT`

Expected behavior:

- Resolves only latest pending proposal for that same user/robot.
- Marks proposal `REJECTED` and sets `decided_at`.
- Does NOT create `MemoryItem`.
- Creates Task/TaskRun.
- Creates token usage event.
- Returns reply similar to:

```text
Discarded. I will not remember that.
```

### 4. Boundary memory

Example input:

`Never send messages to clients without asking me first.`

Expected behavior:

- Creates `ProposedMemory(memory_type=BOUNDARY_MEMORY, status=PENDING)`.
- Does not create a durable `MemoryItem` until `APPROVE`.
- Reply should frame it as a robot limit/boundary.

Example input:

`Ask before scheduling meetings with clients.`

Expected behavior:

- Creates `ProposedMemory(memory_type=BOUNDARY_MEMORY, status=PENDING)`.

### 5. Missing pending proposal

Example input:

`APPROVE`

If no pending proposal exists for that user/robot:

- Do not create MemoryItem.
- Return a safe clarification message.
- Still preserve normal request handling records if that is the Stage 1 pattern.

### 6. Cross-user isolation

User A must not approve or reject User B’s pending proposal.

Approval/rejection lookup must filter by both `user_id` and `robot_id`.

## Safety requirements

- No proposed memory automatically becomes durable memory.
- Unsafe/prohibited requests must still respect existing safety behavior.
- Boundary memories are allowed as proposed memories, but still require approval.
- Do not claim legal, medical, tax, or professional authority.
- Do not store raw sensitive context beyond the proposed memory content required for this deterministic Stage 2 flow.
- Keep the language consumer-facing. Do not expose Zaubern/SAL/DSSE/conformity terminology.

## Tests required

Add or update tests so the following pass:

1. Existing Stage 1 tests still pass unchanged or with only necessary fixture updates.
2. Proposal from `Remember that I prefer short direct answers.` creates exactly one `ProposedMemory(PENDING)` and zero `MemoryItem` records.
3. `APPROVE` after a pending proposal creates exactly one `MemoryItem(ACTIVE)` and marks the proposal `APPROVED`.
4. `REJECT` after a pending proposal marks proposal `REJECTED` and creates no `MemoryItem`.
5. Boundary memory from `Never send messages to clients without asking me first.` creates a `ProposedMemory` with `memory_type=BOUNDARY_MEMORY`.
6. `APPROVE` with no pending proposal returns a safe clarification and creates no `MemoryItem`.
7. Cross-user isolation: User B cannot approve User A’s pending proposal.
8. Token usage events are created for both proposal and approval/rejection turns.
9. Add direct tests for User, Robot, and SkillManifest persistence if low-cost, since Stage 1 validation identified that gap.
10. Add a repeated-message test confirming the same Telegram user reuses the same User/Robot.

## Validation commands

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

If tests fail, fix them before completing.

## Completion report required

Return a concise completion report with:

1. Summary
2. Files changed
3. Data model changes
4. Memory flow implemented
5. Safety/scope behavior preserved
6. Tests added/updated
7. Exact validation commands and outputs
8. Known gaps
9. Recommended next prompt

## Recommended next stage after this task

Do not implement this now. The likely Stage 3 after successful validation is either:

- Stage 2 validation + Stage 3 spec, or
- a narrow Memory Center read-only API slice.

Do not jump to PDF until memory approval and retrieval are stable.
