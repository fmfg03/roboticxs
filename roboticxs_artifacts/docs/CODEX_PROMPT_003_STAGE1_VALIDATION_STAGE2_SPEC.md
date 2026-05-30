# Codex Prompt 003 — Stage 1 Validation + Stage 2 Memory Spec

You are working inside the Roboticxs repository.

## Mission

Validate the completed Stage 1 Foundation Build and propose the Stage 2 technical specification for the first durable memory onboarding slice.

Do **not** implement Stage 2 yet.

This prompt is a validation/specification prompt, not a build prompt.

---

## Project Context

Roboticxs is a personal AI robot product built on Hermes Agent principles.

The MVP is not a generic chatbot. The product center is:

- one personal robot,
- editable memory,
- scoped skills,
- action boundaries,
- model routing,
- token/cost logging,
- Telegram-first interaction.

The strategic product rule:

> Roboticxs turns AI from a blank chatbox into a personal robot with memory, skills, cost control, and boundaries.

Stage 1 reportedly implemented the text-only control loop:

```text
Telegram webhook
→ user / robot resolution
→ task / task_run persistence
→ starter skill manifest
→ scope guard
→ safety decision
→ model route estimate
→ token usage event
→ reply payload
```

Stage 2 should add the first durable memory slice, not PDF parsing, not proactive triggers, not live LLM routing.

---

## Canonical Documents To Read First

Read these before making claims:

- `README.md`
- `AGENTS.md`
- `docs/ROBOTICXS_PROJECT_BRIEF.md`
- `docs/PRODUCT_SPEC_v0_1.md`
- `docs/HERMES_MVP_TECHNICAL_PLAN.md`
- `docs/SAFETY_LAYER_SPEC_v0_1.md`
- `docs/MODEL_ROUTER_SPEC_v0_1.md`
- `docs/TOKEN_COUNTER_SPEC_v0_1.md`
- `docs/SKILL_MANIFEST_SCHEMA_v0_1.json`
- `docs/STAGE_0_READONLY_BOOTSTRAP_ASSESSMENT.md`, if present
- `docs/STAGE_1_FOUNDATION_BUILD_COMPLETION_REPORT.md`, if present

If a file is missing, report it. Do not fabricate its contents.

---

## Permissions

You may:

- inspect files,
- read code,
- run tests,
- run safe read-only commands,
- report findings,
- propose exact Stage 2 scope,
- propose files to change later.

You must not:

- modify files,
- create files,
- delete files,
- install packages,
- change dependencies,
- run a server that persists state outside tests,
- call external APIs,
- make real Telegram calls,
- add memory implementation code yet.

Allowed validation commands:

```bash
python3 -m pytest -q
python3 -m pytest -q -ra
find . -maxdepth 3 -type f | sort
python3 -m compileall app tests
```

If the repo has a valid package setup and tests require another safe command, explain it before using it.

---

## Validation Tasks

### 1. Verify Stage 1 claims

Check whether the reported Stage 1 implementation actually exists:

- `pyproject.toml`
- `.env.example`
- `app/config.py`
- `app/db.py`
- `app/models.py`
- `app/schemas.py`
- `app/telegram_adapter.py`
- `app/orchestrator.py`
- `app/skills.py`
- `app/scope_guard.py`
- `app/safety.py`
- `app/model_router.py`
- `app/token_usage.py`
- `app/reply_composer.py`
- `app/main.py`
- `skills/basic_assistant.json`
- `tests/conftest.py`
- `tests/test_health.py`
- `tests/test_scope_guard.py`
- `tests/test_safety.py`
- `tests/test_token_usage.py`
- `tests/test_telegram_webhook.py`

For each, report:

- present / missing,
- purpose,
- whether it matches the Stage 1 control loop.

### 2. Run validation

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Report exact output.

If tests fail, stop and produce a Stage 1 repair plan instead of a Stage 2 spec.

### 3. Inspect architecture boundaries

Validate whether Stage 1 kept these boundaries clean:

- Telegram adapter does not own business logic.
- Orchestrator coordinates but does not hide policy logic.
- Scope guard is deterministic.
- Safety checker is deterministic.
- Model router remains stubbed and does not call live providers.
- Token usage logger persists estimated usage.
- Tests do not rely on external network calls.
- No PDF, memory center, connector, dashboard, or proactive trigger scope crept into Stage 1.

### 4. Inspect safety behavior

Confirm whether Stage 1 supports these decisions:

- `ANSWER`
- `CLARIFY`
- `REFUSE_SCOPE`
- `ASK_CONFIRMATION`
- `BLOCK`

Confirm whether professional advice and prohibited actions are handled without pretending to provide legal, tax, medical, employment, payment, credential, deletion, or external-write authority.

### 5. Inspect persistence behavior

Confirm whether one accepted Telegram text request creates the expected records:

- User
- Robot
- Task
- TaskRun
- SafetyDecision
- ModelRouteDecision
- TokenUsageEvent

Also confirm whether SkillManifest is loaded from JSON and whether it is persisted or only read from file.

---

## Stage 2 Scope To Propose

If Stage 1 passes validation, propose Stage 2 as:

> Text-only Memory Onboarding with Proposed Memories and Explicit Approval / Rejection.

The user should be able to send a Telegram message that contains durable self/work context. The robot should not automatically store that context as approved memory. It should extract proposed memory candidates, present them back to the user, and require explicit approval before moving them into durable memory.

Correct product flow:

```text
Telegram text
→ task
→ context/memory extraction candidate
→ ProposedMemory record
→ reply asking for approval
→ user approves / rejects
→ approved MemoryItem record or rejected ProposedMemory state
→ token/cost event logged
```

Stage 2 should stay text-only.

No email, calendar, PDF, files, connectors, UI dashboard, proactive trigger engine, or real LLM extraction yet.

Use deterministic extraction rules for now. Example:

- “remember that my company is X”
- “remember that I prefer Y”
- “my timezone is Z”
- “never do X”
- “ask before doing Y”

---

## Stage 2 Required Entities

Propose minimal schema additions or model changes for:

### `MemoryItem`

Fields should include at least:

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

### `ProposedMemory`

Fields should include at least:

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

---

## Stage 2 Telegram UX To Propose

Support these text-only flows:

### A. Proposed memory creation

User:

```text
Remember that I prefer short direct answers.
```

Robot:

```text
I can remember this:

Preference: You prefer short direct answers.

Reply APPROVE to save it or REJECT to discard it.
```

### B. Approval

User:

```text
APPROVE
```

Robot:

```text
Saved to your robot memory.
```

### C. Rejection

User:

```text
REJECT
```

Robot:

```text
Discarded. I will not remember that.
```

### D. Boundary memory

User:

```text
Never send messages to clients without asking me first.
```

Robot:

```text
I can save this as a robot limit:

Boundary: Ask before sending messages to clients.

Reply APPROVE to save it or REJECT to discard it.
```

---

## Stage 2 Acceptance Criteria To Propose

Your Stage 2 spec must include acceptance criteria covering:

- deterministic proposed memory extraction from text,
- no automatic approved memory creation,
- approval creates an active `MemoryItem`,
- rejection does not create a `MemoryItem`,
- pending proposal state is persisted,
- approval/rejection is scoped to the correct user and robot,
- memory-related actions still create task/task_run records,
- safety layer blocks prohibited memory requests where appropriate,
- token usage is logged for memory proposal and decision flows,
- tests cover proposal, approval, rejection, boundary memory, and cross-user isolation.

---

## Output Format

Return a structured report with these sections:

1. Stage 1 Validation Summary
2. Validation Commands Run
3. Files Verified
4. Test Results
5. Architecture Boundary Review
6. Safety Review
7. Persistence Review
8. Stage 1 Defects / Repairs Needed
9. Stage 2 User Story Proposal
10. Stage 2 Technical Spec Proposal
11. Stage 2 Data Model Proposal
12. Stage 2 Telegram UX Proposal
13. Stage 2 Acceptance Criteria
14. Stage 2 Non-Goals
15. Likely Files To Change In Stage 2
16. Test Plan For Stage 2
17. Human Approval Questions
18. Recommended Next Codex Prompt

If Stage 1 fails validation, skip sections 9–18 and instead provide a Stage 1 repair prompt.

---

## Hard Constraints

Do not broaden Stage 2 into:

- PDF ingestion,
- Memory Center UI,
- email/calendar scanning,
- social connectors,
- proactive triggers,
- real LLM extraction,
- vector memory,
- real Telegram send,
- billing,
- admin dashboard,
- multi-provider routing.

The correct Stage 2 is durable memory approval, not feature sprawl.
