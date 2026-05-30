# ROBOTICXS — Hermes MVP Technical Plan v0.1

> **Product:** Roboticxs.com  
> **Version:** v0.1  
> **Status:** Technical implementation plan  
> **Runtime base:** Hermes Agent  
> **Primary MVP channel:** Telegram  

---

## 1. MVP Goal

Build a working personal AI robot demo that proves:

```text
Telegram → Robot → Memory → Skill Scope → Model Router → Safety Decision → Response/Action → Token Log
```

First demo scenario:

> User sends a document through Telegram. The robot reviews it, proposes relevant memories, prepares a meeting brief, asks before sending or storing sensitive information, and logs model/cost usage.

---

## 2. System Components

### Runtime

- Hermes Agent runtime.
- Robot orchestration service.
- Skill manifest loader.
- Scope guard.
- Safety layer.
- Model router.
- Token/cost tracker.
- Telegram adapter.

### Persistence

Minimum database tables:

- `users`
- `workspaces`
- `robots`
- `skill_packages`
- `skill_manifests`
- `memory_items`
- `context_scans`
- `proposed_memories`
- `tasks`
- `task_runs`
- `tool_connections`
- `model_providers`
- `model_catalog_entries`
- `model_route_decisions`
- `token_usage_events`
- `budget_policies`
- `budget_alerts`
- `action_boundaries`
- `safety_decisions`
- `upgrade_signals`

---

## 3. Proposed Architecture

```text
Telegram Bot
   ↓
Telegram Adapter
   ↓
Robot Orchestrator
   ↓
Request Normalizer
   ↓
Skill Scope Guard
   ↓
Task Classifier
   ↓
Memory Retriever
   ↓
Model Router + Cost Governor
   ↓
Hermes Agent Execution
   ↓
Safety Layer
   ↓
Response Composer
   ↓
Telegram Reply
```

For actions:

```text
Proposed Action
   ↓
Action Envelope
   ↓
Safety Decision
   ↓
ALLOW / DRAFT_ONLY / ASK_CONFIRMATION / ESCALATE / BLOCK
   ↓
Execution Adapter or User Confirmation
```

---

## 4. MVP Modules

### 4.1 Telegram Adapter

Responsibilities:

- receive messages,
- receive files,
- map Telegram user to Roboticxs user,
- create task,
- send responses,
- handle confirmation buttons or commands,
- preserve conversation references.

Commands:

- `/start`
- `/help`
- `/memory`
- `/limits`
- `/skills`
- `/budget`
- `/forget`

### 4.2 Robot Orchestrator

Responsibilities:

- load robot profile,
- load active skills,
- route request to skill,
- coordinate memory, model, and safety modules,
- write task/task_run records.

### 4.3 Memory Center

Responsibilities:

- store approved memory items,
- store boundary memories,
- store proposed memories,
- allow user approval/edit/delete,
- retrieve relevant context per task,
- mark stale memories.

Memory item fields:

- `memory_id`
- `user_id`
- `workspace_id`
- `robot_id`
- `memory_type`
- `content`
- `source`
- `confidence`
- `status`
- `tags`
- `pinned`
- `ask_before_using`
- `never_use_for_decisions`
- `created_at`
- `updated_at`

### 4.4 Context Scan

Responsibilities:

- temporarily inspect approved sources,
- extract candidate memories,
- avoid raw storage by default,
- ask user to approve/edit/reject.

Initial MVP context sources:

- Telegram-uploaded documents,
- user-provided profile answers,
- manually pasted business context.

Email/calendar connectors can be mocked or added after core loop works.

### 4.5 Skill Registry

Responsibilities:

- load skill manifests,
- verify schema compliance,
- expose active packages by plan,
- provide safe fallback responses,
- expose allowed/blocked action classes.

Initial skills:

- Basic Assistant,
- Documents Review,
- Meeting Brief,
- Sales Follow-up,
- Marketing Draft.

### 4.6 Scope Guard

Responsibilities:

- detect if request belongs to active skill,
- redirect to enabled skill,
- offer upgrade for disabled paid skill,
- refuse out-of-scope requests,
- block prohibited topics/actions.

### 4.7 Model Router

Responsibilities:

- classify task,
- estimate token usage,
- select provider/model,
- estimate cost,
- request confirmation when above threshold,
- log route decision.

### 4.8 Token Counter / Cost Governor

Responsibilities:

- log usage,
- estimate before calls,
- reconcile after calls,
- enforce per-task and monthly budgets,
- track retry waste.

### 4.9 Safety Layer

Responsibilities:

- normalize proposed actions,
- decide `ALLOW`, `DRAFT_ONLY`, `ASK_CONFIRMATION`, `ESCALATE`, `BLOCK`,
- write safety decision log,
- return user-facing boundary message.

---

## 5. Initial API Endpoints

### Robot

- `POST /api/robots`
- `GET /api/robots/:robot_id`
- `PATCH /api/robots/:robot_id`

### Telegram

- `POST /api/telegram/webhook`

### Tasks

- `POST /api/tasks`
- `GET /api/tasks/:task_id`
- `GET /api/tasks/:task_id/runs`

### Memory

- `GET /api/robots/:robot_id/memory`
- `POST /api/robots/:robot_id/memory/propose`
- `POST /api/memory/:memory_id/approve`
- `PATCH /api/memory/:memory_id`
- `DELETE /api/memory/:memory_id`

### Skills

- `GET /api/skills`
- `GET /api/robots/:robot_id/skills`
- `POST /api/skills/validate-manifest`

### Routing / Cost

- `POST /api/model-router/estimate`
- `GET /api/robots/:robot_id/usage`
- `GET /api/admin/usage`

### Safety

- `POST /api/safety/check-action`
- `GET /api/tasks/:task_id/safety-decisions`

---

## 6. First Demo Script

### Step 1 — Start

User:

> `/start`

Robot:

> “I’m your Roboticxs robot. I can help with meetings, documents, reminders, drafts, and approved context. First, tell me what you do and what you want me to remember.”

### Step 2 — Memory Proposal

User provides context.

Robot proposes:

- name,
- role,
- company,
- working style,
- common task,
- boundary.

User approves.

### Step 3 — Document Upload

User sends PDF.

Robot:

> “I can review this document and prepare a meeting brief. Estimated cost: $0.06. Continue?”

### Step 4 — Review

Robot returns:

- summary,
- important sections,
- risks/open questions,
- suggested follow-up,
- meeting brief.

### Step 5 — Sensitive Action

User:

> “Send this to Victor.”

Robot:

> “I can draft the message, but I need your confirmation before sending anything externally.”

### Step 6 — Cost Log

User:

> `/budget`

Robot:

> “This month: 18,420 tokens, estimated cost $0.31. Most expensive task: document review.”

---

## 7. Development Phases

### Phase 0 — Repo Bootstrap

- Create repo.
- Add `/docs` artifacts.
- Add environment template.
- Add basic README.
- Add local dev instructions.

### Phase 1 — Telegram Skeleton

- Telegram bot webhook.
- User mapping.
- Simple response loop.
- Task/task_run creation.

### Phase 2 — Memory Center MVP

- Memory tables.
- Proposed memory flow.
- Approval/edit/delete.
- `/memory` command.

### Phase 3 — Skill Registry + Scope Guard

- Load JSON manifests.
- Validate schema.
- Route requests by skill.
- Implement safe fallback.

### Phase 4 — Document Review Skill

- File intake.
- Text extraction.
- Summary.
- Review notes.
- Meeting brief.

### Phase 5 — Model Router + Token Counter

- Provider abstraction.
- Estimate cost.
- Log usage.
- Budget threshold prompt.

### Phase 6 — Safety Layer

- Action envelope.
- Decision engine.
- Confirmation flow.
- Safety logs.

### Phase 7 — Admin/Usage Surface

- Basic admin dashboard or CLI.
- Cost by user/model/task.
- Safety decision viewer.

---

## 8. Tech Stack Recommendation

Use pragmatic defaults:

- Backend: Node.js/TypeScript or Python/FastAPI.
- Database: Postgres/Supabase.
- Queue: Redis/BullMQ or equivalent.
- Object storage: S3-compatible bucket for documents.
- Telegram: official Bot API.
- LLM providers: abstracted provider clients.
- PDF extraction: separate service/module with clear failure behavior.

Avoid early complexity:

- no WhatsApp bridge,
- no enterprise SSO,
- no overbuilt governance UI,
- no multi-agent theater,
- no hidden memory writes,
- no certified-signature claims.

---

## 9. MVP Acceptance Criteria

The technical MVP is acceptable when:

1. Telegram bot receives text and documents.
2. User can create or load a robot.
3. User can approve/edit/delete memory.
4. Skill manifest schema validates.
5. Scope guard redirects or refuses out-of-scope requests.
6. Document Review skill works on at least one PDF.
7. Model router logs route decisions.
8. Token/cost tracker logs usage.
9. Safety layer blocks prohibited actions and asks confirmation for external sends.
10. Admin can inspect task runs, usage, and safety decisions.
