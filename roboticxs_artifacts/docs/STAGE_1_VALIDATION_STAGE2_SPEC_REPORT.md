# Roboticxs Stage 1 Validation + Stage 2 Spec Report

──────────────────────────────────────────────────────

• 1. Stage 1 Validation Summary
  Stage 1 passes validation. The text-only control loop exists, tests pass, bytecode compilation passes, and the implementation stayed inside
  the approved scope. The correct next step is Stage 2 durable memory onboarding with explicit approval/rejection, not PDF or connectors.

  2. Validation Commands Run

  python3 -m pytest -q
  python3 -m compileall app tests

  Exact outputs:

  $ python3 -m pytest -q
  .......                                                           [100%]

  $ python3 -m compileall app tests
  Listing 'app'...
  Listing 'tests'...
  Compiling 'tests/conftest.py'...
  Compiling 'tests/test_health.py'...
  Compiling 'tests/test_safety.py'...
  Compiling 'tests/test_scope_guard.py'...
  Compiling 'tests/test_telegram_webhook.py'...
  Compiling 'tests/test_token_usage.py'...

  3. Files Verified

  - pyproject.toml: present; runtime/test manifest; matches Stage 1 foundation.
  - .env.example: present; local config defaults; matches Stage 1 foundation.
  - app/config.py: present; reads DATABASE_URL and stub model settings; matches loop.
  - app/db.py: present; engine/session/table init; matches persistence slice.
  - app/models.py: present; defines User, Robot, Task, TaskRun, SkillManifest, SafetyDecision, ModelRouteDecision, TokenUsageEvent; matches
    Stage 1 loop.
  - app/schemas.py: present; request/response envelope models; matches webhook/reply path.
  - app/telegram_adapter.py: present; normalizes Telegram text-only update; matches scope.
  - app/orchestrator.py: present; coordinates the loop; matches scope.
  - app/skills.py: present; loads and persists starter manifest from JSON; matches scope.
  - app/scope_guard.py: present; deterministic keyword/rule logic; matches scope.
  - app/safety.py: present; deterministic safety decisions; matches scope.
  - app/model_router.py: present; stub classifier/estimator only; matches scope.
  - app/token_usage.py: present; estimated token event builder; matches scope.
  - app/reply_composer.py: present; reply payload text composition; matches scope.
  - app/main.py: present; exposes GET /health and POST /api/telegram/webhook; matches scope.
  - skills/basic_assistant.json: present; starter manifest; matches scope.
  - tests/conftest.py: present; local ASGI client and isolated SQLite test DB; matches scope.
  - tests/test_health.py: present; health endpoint test; matches scope.
  - tests/test_scope_guard.py: present; scope behavior tests; matches scope.
  - tests/test_safety.py: present; safety behavior tests; matches scope.
  - tests/test_token_usage.py: present; token builder test; matches scope.
  - tests/test_telegram_webhook.py: present; end-to-end webhook behavior tests; matches scope.

  4. Test Results

  - 7/7 tests passed.
  - Health path passes.
  - Webhook path passes.
  - Persistence of Task, TaskRun, SafetyDecision, ModelRouteDecision, and TokenUsageEvent is asserted in tests.
  - Invalid Telegram payload returns 422 and does not crash.

  5. Architecture Boundary Review

  - Telegram adapter does not own business logic: valid. app/telegram_adapter.py only parses/validates.
  - Orchestrator coordinates but does not hide policy logic: valid. app/orchestrator.py calls scope, safety, routing, token logging explicitly.
  - Scope guard is deterministic: valid. app/scope_guard.py.
  - Safety checker is deterministic: valid. app/safety.py.
  - Model router is stubbed and does not call providers: valid. app/model_router.py.
  - Token logger persists estimated usage only: valid. app/token_usage.py plus TokenUsageEvent.
  - Tests do not use external network calls: valid. tests/conftest.py uses local ASGI transport.
  - No PDF, memory center, connectors, dashboard, or proactive triggers crept into Stage 1: valid.

  6. Safety Review
  Supported and verified:

  - ANSWER
  - CLARIFY
  - REFUSE_SCOPE
  - ASK_CONFIRMATION
  - BLOCK

  Behavior is directionally correct:

  - legal/medical/tax advice is refused/escalated, not answered as authority
  - payment/deletion/credential actions are blocked
  - external send/write/scheduling requires confirmation
  - no fake execution authority is claimed

  Constraint: the current safety layer is still simple keyword logic, which is acceptable for Stage 1 but should remain explicit in claims.

  7. Persistence Review
  Confirmed in code:

  - one accepted Telegram text request resolves or creates User and Robot in app/orchestrator.py
  - creates Task
  - creates TaskRun
  - creates SafetyDecision
  - creates ModelRouteDecision
  - creates TokenUsageEvent

  Confirmed in tests:

  - Task, TaskRun, SafetyDecision, ModelRouteDecision, TokenUsageEvent are asserted in tests/test_telegram_webhook.py

  Skill manifest behavior:

  - loaded from skills/basic_assistant.json
  - persisted into skill_manifests via seed_skill_manifest() in app/skills.py
  - then read back from DB via get_active_skill_manifest()

  Gap: tests do not explicitly assert User, Robot, or SkillManifest counts, even though code clearly creates/persists them.

  8. Stage 1 Defects / Repairs Needed
  No blocking defects.

  Non-blocking repairs worth folding into Stage 2 or a small cleanup:

  - add direct tests for User, Robot, and SkillManifest persistence
  - add a test for repeated messages from the same Telegram user to confirm reuse of the same robot
  - make action-class vocabulary consistent with product docs where names differ slightly across docs/code
  - keep roboticxs.db out of durable artifact packaging if the repo is meant to stay source-only

  9. Stage 2 User Story Proposal
  As a Roboticxs user, I can send a text message that contains personal or work context, receive a proposed memory back for explicit approval or
  rejection, and only have that memory stored durably if I approve it.

  10. Stage 2 Technical Spec Proposal
  Stage 2 should add one new text-only branch to the existing loop:

  - detect whether inbound text is a memory-onboarding candidate
  - extract deterministic proposed memory candidates
  - persist ProposedMemory as PENDING
  - reply with approval/rejection prompt
  - accept follow-up APPROVE or REJECT
  - on approval, create durable MemoryItem
  - on rejection, mark proposal rejected and do not create MemoryItem
  - still create Task/TaskRun and token usage records for both proposal and decision turns

  Service boundaries:

  - telegram_adapter: unchanged
  - orchestrator: route between normal task flow and memory-onboarding flow
  - new memory extraction module: deterministic parser only
  - new memory service: proposal creation, approval, rejection, lookup of latest pending proposal per user/robot
  - safety layer: continue to block prohibited memory requests where relevant
  - token logging: reused for proposal and decision flows

  Telegram path:

  - normal text memory statement -> proposal path
  - APPROVE / REJECT -> pending-proposal resolution path

  11. Stage 2 Data Model Proposal
  Add MemoryItem:

  - id
  - user_id
  - robot_id
  - memory_type
  - content
  - source
  - status
  - importance
  - created_at
  - updated_at

  Recommended memory_type:

  - USER_PROFILE
  - WORK_PREFERENCE
  - BUSINESS_CONTEXT
  - TASK_MEMORY
  - BOUNDARY_MEMORY

  Recommended status:

  - ACTIVE
  - OUTDATED
  - FORGOTTEN

  Add ProposedMemory:

  - id
  - user_id
  - robot_id
  - task_id
  - memory_type
  - proposed_content
  - source_text
  - status
  - created_at
  - decided_at

  Recommended status:

  - PENDING
  - APPROVED
  - REJECTED
  - EXPIRED

  Likely useful additions to existing models:

  - Task may need a simple kind or intent field such as GENERAL_TASK, MEMORY_PROPOSAL, MEMORY_DECISION
  - TokenUsageEvent can remain unchanged for Stage 2

  12. Stage 2 Telegram UX Proposal
  A. Proposed memory creation:

  User: Remember that I prefer short direct answers.
  Robot: I can remember this:

  Preference: You prefer short direct answers.

  Reply APPROVE to save it or REJECT to discard it.

  B. Approval:

  User: APPROVE
  Robot: Saved to your robot memory.

  C. Rejection:

  User: REJECT
  Robot: Discarded. I will not remember that.

  D. Boundary memory:

  User: Never send messages to clients without asking me first.
  Robot: I can save this as a robot limit:

  Boundary: Ask before sending messages to clients.

  Reply APPROVE to save it or REJECT to discard it.

  Rule:

  - APPROVE and REJECT must resolve only the latest pending proposal for that same user and robot
  - if no pending proposal exists, return a safe clarification message

  13. Stage 2 Acceptance Criteria

  - deterministic text rules extract proposed memory candidates
  - no proposed memory automatically becomes approved memory
  - proposal creates a persisted ProposedMemory with PENDING
  - APPROVE creates one MemoryItem and marks the proposal APPROVED
  - REJECT marks the proposal REJECTED and creates no MemoryItem
  - approval/rejection is scoped to the correct user and robot
  - memory-related turns still create Task and TaskRun
  - memory proposal and approval/rejection flows create token usage events
  - boundary memory is supported
  - prohibited or unsafe requests still respect safety rules
  - tests cover proposal, approval, rejection, boundary memory, missing-pending-proposal behavior, and cross-user isolation

  14. Stage 2 Non-Goals

  - PDF ingestion
  - Memory Center UI
  - connectors
  - email/calendar scanning
  - proactive triggers
  - real LLM extraction
  - vector memory
  - real Telegram send
  - billing/dashboard work
  - admin UI
  - multi-provider routing

  15. Likely Files To Change In Stage 2

  - app/models.py
  - app/orchestrator.py
  - app/schemas.py
  - app/reply_composer.py
  - app/safety.py
  - new module such as app/memory_extraction.py
  - new module such as app/memory_service.py
  - tests/test_telegram_webhook.py
  - new tests such as tests/test_memory_onboarding.py

  16. Test Plan For Stage 2

  - proposal from “remember that …” text creates ProposedMemory(PENDING)
  - approval creates MemoryItem(ACTIVE) and updates proposal status
  - rejection updates proposal status and creates no MemoryItem
  - boundary memory proposal is typed as BOUNDARY_MEMORY
  - APPROVE with no pending proposal returns safe clarification
  - cross-user isolation prevents one user from approving another user’s proposal
  - token usage event is created for proposal turn and approval/rejection turn
  - existing Stage 1 webhook tests keep passing unchanged

  17. Human Approval Questions

  - Confirm the deterministic trigger phrases for Stage 2. Default recommendation: start with remember that, my, I prefer, never, and ask
    before.
  - Confirm whether only one pending proposal per user/robot should be active at a time. Default recommendation: yes, keep one pending proposal
    active to keep Telegram UX simple in Stage 2.

  18. Recommended Next Codex Prompt
  Use a Stage 2 build prompt that says: extend the current FastAPI text-only loop with ProposedMemory and MemoryItem, implement deterministic
  extraction from explicit memory-intent messages, require APPROVE / REJECT before durable storage, preserve existing scope/safety/token logging
  behavior, and add tests for proposal creation, approval, rejection, boundary memory, no-pending-proposal handling, and cross-user isolation.
