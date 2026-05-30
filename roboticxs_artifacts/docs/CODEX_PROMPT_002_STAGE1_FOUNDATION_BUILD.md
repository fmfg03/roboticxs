# CODEX PROMPT 002 — Roboticxs Stage 1 Foundation Build

You are working inside the Roboticxs repo.

Follow the global Codex Factory protocol and the repo-local `AGENTS.md` instructions if present.

This is **not** a full MVP build.
This is the first approved implementation slice after the read-only bootstrap assessment.

## Stage 0 Result

The Stage 0 read-only assessment found that this repo is currently docs-only:

- no valid app scaffold,
- no runtime manifest,
- no tests,
- no `.env.example`,
- no implementation files,
- no package manager decision,
- no confirmed database implementation.

The product docs are the current source of truth:

- `docs/ROBOTICXS_PROJECT_BRIEF.md`
- `docs/PRODUCT_SPEC_v0_1.md`
- `docs/SKILL_MANIFEST_SCHEMA_v0_1.json`
- `docs/SAFETY_LAYER_SPEC_v0_1.md`
- `docs/MODEL_ROUTER_SPEC_v0_1.md`
- `docs/TOKEN_COUNTER_SPEC_v0_1.md`
- `docs/HERMES_MVP_TECHNICAL_PLAN.md`
- `docs/LAUNCH_PAGE_COPY_v0_1.md`

## Approved Stage 1 Decision

Use this stack for the first implementation slice:

- **Backend:** Python 3.11+ / FastAPI
- **Persistence:** SQLite for local development, Postgres-ready via `DATABASE_URL`
- **ORM:** SQLAlchemy 2.x or SQLModel. Prefer the simpler reliable option.
- **Tests:** pytest + FastAPI TestClient
- **Telegram:** official Telegram webhook shape, but no live Telegram network calls in tests
- **LLM calls:** stubbed only in this slice
- **Model routing:** estimate/stub only in this slice
- **Token usage:** estimate/stub only in this slice

Do not choose Node/TypeScript unless the repo already contains committed evidence that Python/FastAPI is impossible. If you find such evidence, stop and report it before writing implementation.

## Goal

Build the smallest working Roboticxs backend loop:

```text
Telegram webhook
  → normalize message
  → resolve/create user + robot
  → create task + task_run
  → load one active skill manifest
  → run scope guard
  → run lightweight safety decision
  → create model route estimate
  → create token usage event
  → compose Telegram-style reply payload
```

The output should prove the architecture path, not the full product.

## Hard Scope

Implement only the text-message path.

No PDF upload.
No document parsing.
No memory center UI.
No email/calendar connectors.
No proactive trigger engine.
No admin dashboard.
No real LLM provider calls.
No real Telegram send call.
No payments.
No external side effects.

## Write Permissions

You may create or edit only files needed for this Stage 1 slice.

Expected files/directories include, but are not limited to:

```text
pyproject.toml
.env.example
README.md
app/
app/main.py
app/config.py
app/db.py
app/models.py
app/schemas.py
app/telegram_adapter.py
app/orchestrator.py
app/skills.py
app/scope_guard.py
app/safety.py
app/model_router.py
app/token_usage.py
app/reply_composer.py
skills/basic_assistant.json
tests/
tests/test_health.py
tests/test_telegram_webhook.py
tests/test_scope_guard.py
tests/test_safety.py
tests/test_token_usage.py
```

You may adjust names if your implementation needs a cleaner structure, but keep the slice small and obvious.

## Required Endpoints

### `GET /health`

Return a simple health payload.

Expected shape:

```json
{
  "status": "ok",
  "service": "roboticxs"
}
```

### `POST /api/telegram/webhook`

Accept a Telegram webhook update for a text message.

Minimum accepted input shape:

```json
{
  "update_id": 10001,
  "message": {
    "message_id": 501,
    "date": 1710000000,
    "chat": {
      "id": 123456,
      "type": "private"
    },
    "from": {
      "id": 123456,
      "is_bot": false,
      "first_name": "Francisco",
      "username": "francisco"
    },
    "text": "Help me prepare for my meeting tomorrow"
  }
}
```

Return a Telegram-style reply payload, not a live Telegram send.

Minimum output shape:

```json
{
  "ok": true,
  "reply": {
    "chat_id": 123456,
    "text": "..."
  },
  "task_id": "...",
  "scope_decision": "ANSWER",
  "safety_decision": "ALLOW",
  "model_route_decision_id": "...",
  "token_usage_event_id": "..."
}
```

For invalid/non-text Telegram updates, return a safe handled response or a clear 4xx error. Do not crash.

## Minimal Data Model

Create only the entities needed for the Stage 1 loop.

Required persisted concepts:

- User
- Robot
- Task
- TaskRun
- SkillManifest
- SafetyDecision
- ModelRouteDecision
- TokenUsageEvent

Use practical local identifiers. UUIDs are fine.

Persistence must work under tests without external services.

Use `DATABASE_URL` from environment, defaulting to a local SQLite database.
For tests, use isolated SQLite/in-memory or temp-file storage.

## Skill Manifest

Create one starter skill manifest:

```text
skills/basic_assistant.json
```

It should conform to the intent of `docs/SKILL_MANIFEST_SCHEMA_v0_1.json`.

Minimum behavior:

- allowed topics: meetings, task help, drafting, summaries, reminders, basic productivity
- blocked topics: legal advice, medical advice, tax advice, payment execution, account deletion, credential changes
- allowed action classes: READ, DRAFT_NOTIFY, CLASSIFY, SUMMARIZE, PREPARE
- confirmation required: SEND_NOTIFY, WRITE_EXTERNAL_RECORD, SCHEDULE_EXTERNAL
- blocked action classes: PAY, DELETE, CONFIGURE, RELEASE, LEGAL_ACCEPTANCE
- safe fallback: short user-facing message explaining available scope

## Scope Guard

Implement a deterministic, simple scope guard.

Required decisions:

- `ANSWER`
- `CLARIFY`
- `REDIRECT`
- `OFFER_UPGRADE`
- `REFUSE_SCOPE`
- `BLOCK`

For Stage 1, simple keyword/rule logic is acceptable.

Minimum cases:

- meeting prep / drafting / summary / reminder → `ANSWER`
- general vague text with no clear task → `CLARIFY`
- legal/medical/tax advice → `REFUSE_SCOPE`
- payment execution/account deletion/credential change → `BLOCK`

## Safety Layer

Implement a lightweight deterministic safety checker.

Decision types:

- `ALLOW`
- `DRAFT_ONLY`
- `ASK_CONFIRMATION`
- `ESCALATE`
- `BLOCK`

Minimum behavior:

- summarizing, preparing, drafting → `ALLOW` or `DRAFT_ONLY`
- sending external messages, writing records, scheduling with a third party → `ASK_CONFIRMATION`
- payment execution, refund execution, account deletion, credential/permission change, vendor bank change, legal acceptance, tax/financial/legal/medical/employment decision, production deployment, destructive action → `BLOCK`

Return a persisted safety decision record with:

- task_id
- decision
- reason_code
- user_message
- action_class
- created_at

Use consumer-facing language only.
Do not expose SAL, DSSE, SLM, conformity, cryptographic governance, or enterprise Zaubern terms in user-facing replies.

## Model Router Stub

Implement a route estimator, not live model routing.

Input fields should include:

- task_id
- task_class
- routing_mode
- estimated_input_tokens
- estimated_output_tokens
- sensitivity_level

Output/persisted record should include:

- provider
- model
- routing_mode
- estimated_cost_usd
- reason
- created_at

Use one default fake or configured model, for example:

```text
provider=openai
model=gpt-4o-mini-or-equivalent
routing_mode=economy
```

Do not call any provider API.

## Token Usage Stub

Implement token usage logging with estimated values.

Persist at least:

- user_id
- robot_id
- task_id
- provider
- model
- input_tokens
- output_tokens
- estimated_cost_usd
- status
- created_at

A crude deterministic estimator is acceptable for Stage 1, for example character count / 4.

## Reply Behavior

For normal allowed requests, return a short helpful reply that makes clear this is the first text-only robot loop.

Example:

```text
I can help with that. For this Stage 1 loop, I recorded the task, checked scope and safety, selected an estimated model route, and logged estimated token usage.
```

For blocked requests:

```text
This action is blocked by your robot limits. I can help prepare a checklist or draft, but I cannot execute this action.
```

For confirmation-required requests:

```text
I can draft this, but I need your confirmation before sending or changing anything externally.
```

## Tests Required

Add tests that run locally.

Minimum tests:

1. `GET /health` returns ok.
2. Valid Telegram text webhook returns `ok: true` and a reply.
3. Valid Telegram text webhook persists task, task_run, safety decision, model route decision, and token usage event.
4. Meeting-prep request returns `scope_decision=ANSWER` and `safety_decision=ALLOW` or `DRAFT_ONLY`.
5. Payment execution request returns `scope_decision=BLOCK` or `safety_decision=BLOCK`.
6. External send request returns `safety_decision=ASK_CONFIRMATION`.
7. Legal/medical/tax advice request is refused or blocked without pretending to give professional advice.
8. Invalid Telegram payload does not crash.

## Validation Commands

After implementation, run the smallest relevant validation commands.

Expected commands:

```bash
python -m pytest -q
```

If dependency installation is required, document the exact command you used.
Do not hide failing tests.
If tests fail because the environment lacks dependencies, report that explicitly and still provide the implementation diff summary.

## Completion Report Required

When finished, report in this exact structure:

```markdown
# Roboticxs Stage 1 Foundation Build — Completion Report

## 1. Summary

## 2. Files Created / Changed

## 3. Runtime / Stack Chosen

## 4. Implemented Flow

## 5. Data Model Implemented

## 6. Safety / Scope Behavior

## 7. Model Routing / Token Logging Behavior

## 8. Tests Added

## 9. Validation Results

## 10. Known Gaps

## 11. Recommended Next Prompt
```

## Non-Claims

Do not claim:

- this is the MVP,
- Telegram is live in production,
- memory center is implemented,
- PDF review is implemented,
- model routing is real provider routing,
- token cost is exact,
- Zaubern governance is fully integrated,
- Roboticxs can execute external actions.

Correct claim:

> Stage 1 proves the first text-only Roboticxs control loop: Telegram-style intake, task persistence, scope guard, safety decision, model route estimate, token usage logging, and reply composition.
