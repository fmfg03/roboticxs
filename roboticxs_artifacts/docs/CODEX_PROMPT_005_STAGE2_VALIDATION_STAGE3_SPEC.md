# CODEX PROMPT 005 — Stage 2 Validation + Stage 3 Memory Read/Control Spec

## Role

You are Codex operating under the Roboticxs coding protocol.

You must validate the current implementation before proposing the next build step.

This is a read-only validation and specification task.

## Project Context

Roboticxs is a personal AI robot product built around memory, skills, model routing, token/cost visibility, and explicit action boundaries.

The approved implementation sequence is incremental:

1. Stage 0: read-only repo bootstrap assessment.
2. Stage 1: text-only Telegram control loop.
3. Stage 2: durable memory onboarding with explicit approval/rejection.
4. Stage 3: memory read/control path.

Stage 1 and Stage 2 are reported as implemented.

Stage 2 added:

- `ProposedMemory`,
- `MemoryItem`,
- `Task.kind`,
- deterministic memory-intent extraction,
- `APPROVE` / `REJECT`,
- one pending proposal per user/robot,
- cross-user isolation,
- token logging for memory proposal and decision turns.

## Hard Rules

Do not modify files.

Do not create files.

Do not delete files.

Do not install dependencies.

Do not add features.

Do not refactor.

Do not run external network calls.

You may run read-only inspection commands and validation commands only.

Allowed commands:

```bash
find . -maxdepth 4 -type f | sort
python3 -m pytest -q
python3 -m compileall app tests
python3 - <<'PY'
# read-only inspection snippets only
PY
```

If a command would modify the repo, do not run it.

## Task A — Validate Stage 2

Verify that Stage 2 actually exists and matches the reported behavior.

Validate:

1. `ProposedMemory` model exists.
2. `MemoryItem` model exists.
3. `Task.kind` exists and distinguishes at least:
   - `GENERAL_TASK`
   - `MEMORY_PROPOSAL`
   - `MEMORY_DECISION`
4. deterministic memory extraction module exists.
5. memory service module exists.
6. webhook can create a pending proposed memory.
7. `APPROVE` creates one active durable memory.
8. `REJECT` creates no durable memory.
9. approval/rejection is scoped to the same user and robot.
10. only one pending proposal is active per user/robot.
11. token usage is logged for proposal turns and decision turns.
12. Stage 1 behavior still passes.
13. tests pass.
14. bytecode compilation passes.

## Task B — Architecture Boundary Review

Review whether Stage 2 preserved the intended boundaries:

- Telegram adapter should not own memory business logic.
- Orchestrator may route flow but should not bury all memory logic inline.
- Memory extraction should remain deterministic for this stage.
- Memory service should own proposal/approval/rejection persistence rules.
- Safety should still apply before unsafe or prohibited behavior.
- Token logging should remain reused rather than duplicated.
- No PDF, connector, UI, dashboard, real LLM routing, or proactive trigger logic should have crept in.

## Task C — Defect and Risk Review

Identify blocking and non-blocking issues.

Pay special attention to:

- overbroad memory triggers, especially `my`,
- false-positive memory capture,
- unsafe memory content,
- approval ambiguity,
- stale pending proposals,
- lack of user-facing memory inspection,
- inability to forget memories,
- active memories not being used by normal task flow,
- gaps in tests,
- source-only artifact hygiene, including local SQLite files.

## Task D — Stage 3 Recommendation

If Stage 2 passes validation, propose Stage 3.

Stage 3 should stay narrow.

Recommended Stage 3 theme:

**Memory Read/Control Path**

Do not propose PDF ingestion yet.

Do not propose connectors yet.

Do not propose a UI yet.

Stage 3 should add text-only memory controls and read-context use:

1. user can ask what the robot remembers,
2. robot can list active memories for the same user/robot,
3. user can forget a specific memory,
4. forgotten memory is marked `FORGOTTEN`, not deleted,
5. normal task flow can read active memories as context,
6. reply payload can include a simple indication that memory context was used,
7. Stage 1 and Stage 2 tests remain passing.

## Stage 3 Candidate User Story

As a Roboticxs user, I can ask my robot what it remembers, remove memories I no longer want it to use, and have approved active memories inform normal task replies without creating or changing memory silently.

## Stage 3 Candidate Acceptance Criteria

Propose detailed acceptance criteria, but do not implement them.

Minimum expected criteria:

- `what do you remember` lists active memories for the same user/robot.
- active memory listing does not show another user’s memories.
- list output includes stable memory IDs or short references usable for forgetting.
- `forget memory <id>` marks the memory as `FORGOTTEN`.
- forgetting is scoped to the same user and robot.
- forgotten memories do not appear in active memory listings.
- forgotten memories are not included in normal task context.
- normal task flow loads active memories read-only.
- no normal task creates memory silently.
- memory read/control turns still create `Task`, `TaskRun`, and `TokenUsageEvent` records.
- existing Stage 1 and Stage 2 tests keep passing.

## Stage 3 Non-Goals

Keep these out:

- PDF ingestion,
- Memory Center UI,
- email/calendar connectors,
- proactive triggers,
- vector search,
- semantic memory retrieval,
- real LLM extraction,
- real Telegram send,
- billing/dashboard work,
- admin UI,
- multi-provider live routing.

## Required Output

Return a report with these sections:

1. Stage 2 Validation Summary
2. Validation Commands Run
3. Files Verified
4. Test Results
5. Architecture Boundary Review
6. Safety and Memory Review
7. Persistence Review
8. Stage 2 Defects / Repairs Needed
9. Stage 3 User Story Proposal
10. Stage 3 Technical Spec Proposal
11. Stage 3 Data Model Proposal
12. Stage 3 Telegram UX Proposal
13. Stage 3 Acceptance Criteria
14. Stage 3 Non-Goals
15. Likely Files To Change In Stage 3
16. Test Plan For Stage 3
17. Human Approval Questions
18. Recommended Next Codex Prompt

## Output Discipline

Be precise.

Separate verified facts from recommendations.

Do not claim implementation unless you verified it in files or tests.

Do not widen scope beyond Stage 3.

If Stage 2 fails validation, stop and recommend a repair prompt instead of Stage 3.
