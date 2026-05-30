# Codex Prompt 007 — Stage 3 Validation + Stage 4 Spec Decision

## Role

You are Codex working inside the Roboticxs repository.

You must follow the project coding protocol:

1. Inspect first.
2. Validate existing implementation.
3. Do not modify files in this prompt.
4. Do not implement Stage 4 yet.
5. Produce a written validation report and Stage 4 recommendation grounded in observed repo facts.

## Current Project State

Roboticxs is a Telegram-first personal AI robot product.

The implemented scope should now include:

- Stage 1: Telegram text-only control loop.
- Stage 2: durable memory onboarding with explicit `APPROVE` / `REJECT`.
- Stage 3: memory read/control with `what do you remember`, `forget memory <id>`, and active memory context used read-only in normal task replies.

The reported Stage 3 build also claims it repaired these Stage 2 issues:

- unsafe memory proposals are gated before `ProposedMemory` persistence;
- the overbroad `my` memory trigger was narrowed;
- pending proposal replacement expiry is tested;
- repo-root SQLite artifacts were removed and ignored.

## Hard Restrictions

Do not write, edit, delete, move, rename, or generate files.

Do not run dependency installation commands.

Do not call live Telegram APIs.

Do not call live LLM/model providers.

Do not add PDF parsing, connectors, UI, vector memory, or real Telegram send in this prompt.

Allowed commands are read-only inspection and validation commands only, such as:

```bash
find . -maxdepth 4 -type f | sort
sed -n '1,220p' <file>
python3 -m pytest -q
python3 -m compileall app tests
grep -R "pattern" -n app tests README.md .gitignore .env.example
```

If you need a command that might write generated files, state the reason first and avoid it unless it is part of normal validation. Do not run migrations or create new source files.

## Validation Tasks

### 1. Confirm Stage 3 Claims

Verify these files exist if claimed:

- `app/memory_control.py`
- `tests/test_memory_control.py`
- updated `app/orchestrator.py`
- updated `app/memory_service.py`
- updated `app/memory_extraction.py`
- updated `app/reply_composer.py`
- updated `.gitignore`
- updated `.env.example`

Confirm the app supports:

- `what do you remember`
- `forget memory <id>`
- only `ACTIVE` memories loaded into normal task context
- no silent memory mutation during normal task flow
- `FORGOTTEN` memories excluded from listing and context
- token/task logging for list and forget turns

### 2. Validate Stage 2 Repairs

Confirm whether safety now gates memory proposal persistence.

Specifically inspect the memory proposal path and verify that a blocked or unsafe memory-intent turn:

- creates `Task`
- creates `TaskRun`
- creates `SafetyDecision`
- creates `ModelRouteDecision`
- creates `TokenUsageEvent`
- does **not** create `ProposedMemory`

Confirm the `my` trigger is no longer broad. It should only match explicit profile/context forms, such as:

- `my name is`
- `my role is`
- `my company is`
- `my timezone is`
- `my working hours are`
- `my preferred`

Confirm pending proposal replacement marks the older pending proposal as `EXPIRED` and has test coverage.

Confirm root SQLite artifact hygiene:

- no source-tracked root `roboticxs.db` should be present;
- `.gitignore` should include appropriate DB/cache patterns;
- default local DB path should not encourage committing generated DB artifacts.

### 3. Run Validation Commands

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Report exact output.

If tests fail, stop and produce a repair plan. Do not implement repairs in this prompt.

### 4. Architecture Boundary Review

Evaluate whether Stage 3 preserved the intended boundaries:

- Telegram adapter only normalizes payloads.
- Orchestrator routes flows but does not absorb all policy logic.
- Memory service owns persistence rules.
- Memory control logic lives outside the Telegram adapter.
- Scope guard and safety remain deterministic.
- Model router remains stubbed; no provider calls.
- Token logging remains reused, not duplicated across branches.
- No PDF, connectors, UI, proactive triggers, vector memory, or real LLM routing crept in.

Flag any file that is becoming too large or too policy-heavy.

### 5. Memory Trust Review

Review memory behavior from a product-trust perspective.

Answer:

- Can the user see what the robot remembers?
- Can the user make the robot forget a memory?
- Are forgotten memories still retained as rows but excluded from active use?
- Can one Telegram user see or forget another user’s memories?
- Can memory be created without explicit approval?
- Can unsafe memory content be proposed or stored?
- Does the robot disclose when active memory context was used?

### 6. Decide Stage 4 Direction

If Stage 3 has blocking defects, recommend **Stage 3 Repair Build**.

If Stage 3 passes cleanly, recommend one of these Stage 4 paths:

#### Option A — Stage 4A Memory Hardening

Use this if memory still has trust gaps.

Possible scope:

- `edit memory <id>: <new text>`
- `mark memory <id> outdated`
- memory categories in list output
- stricter boundary-memory handling
- tests for editing, outdated exclusion, and user/robot isolation

Do not add UI yet.

#### Option B — Stage 4B Narrow Documents/PDF Skill

Use this if memory control is clean enough to widen capabilities.

Narrow scope only:

- Telegram-style document/PDF metadata intake route or simulated webhook branch
- no OCR
- no real Telegram file download unless clearly isolated and mocked
- local/simple text extraction only if dependency already exists or is safe to add in a later build prompt
- create `DocumentReview` / `DocumentTask` record or minimal equivalent
- safety disclaimer: not legal, tax, financial, or professional advice
- result is a draft review/summary only
- no signature execution
- no legal-signature claims
- token route estimate and token usage logging preserved
- tests with fixture payloads only

#### Option C — Stage 4C Cost/Budget Governor

Use this only if route/token logging has weak control semantics.

Possible scope:

- per-user/per-robot budget policy
- estimated-cost threshold warning
- ask-confirmation on expensive task estimates
- no billing UI

## Output Required

Produce a report with this exact structure:

```markdown
# Roboticxs Stage 3 Validation + Stage 4 Recommendation

## 1. Executive Finding

## 2. Validation Commands Run

## 3. Files Verified

## 4. Test Results

## 5. Stage 3 Claim Verification

## 6. Stage 2 Repair Verification

## 7. Architecture Boundary Review

## 8. Memory Trust Review

## 9. Defects / Repairs Needed

## 10. Stage 4 Recommendation

## 11. Stage 4 User Story Proposal

## 12. Stage 4 Technical Spec Proposal

## 13. Stage 4 Acceptance Criteria

## 14. Stage 4 Non-Goals

## 15. Likely Files To Change In Stage 4

## 16. Test Plan For Stage 4

## 17. Human Approval Questions

## 18. Recommended Next Codex Prompt
```

## Decision Bias

Bias toward **not widening capability** if memory trust or safety gating is weak.

Bias toward **Stage 4B Narrow Documents/PDF Skill** only if Stage 3 validates cleanly and no memory-control repair is needed.

Remember: Roboticxs should not compete on model intelligence. It should compete on memory, skill packaging, cost visibility, and safe action boundaries.
