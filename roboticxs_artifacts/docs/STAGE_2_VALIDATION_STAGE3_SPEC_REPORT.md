# Roboticxs Stage 2 Validation + Stage 3 Spec Report

1. Stage 2 Validation Summary
  Stage 2 passes validation. The durable memory onboarding path exists, tests pass, compilation passes, and the implementation remains inside
  the approved Stage 2 boundary. The next correct step is Stage 3 memory read/control, not PDF or connectors.

  2. Validation Commands Run

  python3 -m pytest -q
  python3 -m compileall app tests

  Exact outputs:

  $ python3 -m pytest -q
  ......................                                                   [100%]

  $ python3 -m compileall app tests
  Listing 'app'...
  Listing 'tests'...

  3. Files Verified

  - app/models.py: verified. Contains ProposedMemory, MemoryItem, and Task.kind.
  - app/memory_extraction.py: verified. Deterministic trigger detection and extraction logic exist.
  - app/memory_service.py: verified. Proposal creation, expiry, approval, rejection, and pending lookup exist.
  - app/orchestrator.py: verified. Routes between normal tasks, memory proposal, and memory decision flows.
  - app/reply_composer.py: verified. Memory proposal, approval, rejection, and no-pending replies exist.
  - tests/test_memory_onboarding.py: verified. Covers proposal, approve, reject, boundary memory, no-pending reply, cross-user isolation,
    repeated user reuse, and basic persistence counts.
  - Existing Stage 1 files remain present and wired.

  4. Test Results

  - 22/22 tests passed.
  - Stage 1 webhook behavior still passes.
  - Stage 2 memory onboarding tests pass.
  - Compilation passed for app and tests.

  5. Architecture Boundary Review

  - Telegram adapter does not own memory business logic: valid. app/telegram_adapter.py only normalizes payloads.
  - Orchestrator routes flow but does contain substantial branch logic inline: acceptable for Stage 2, but Stage 3 should avoid growing this
    file into a monolith.
  - Memory extraction is deterministic: valid. app/memory_extraction.py.
  - Memory service owns persistence rules for proposal expiry, approval, rejection, and pending lookup: valid. app/memory_service.py.
  - Token logging is reused rather than duplicated in separate codepaths: valid via _persist_route_and_token() in app/orchestrator.py.
  - No PDF, connectors, UI, dashboard, proactive triggers, or real provider routing crept in: valid.

  6. Safety and Memory Review
  Verified facts:

  - APPROVE and REJECT are exact case-insensitive commands.
  - One pending proposal per user/robot is enforced in code by expiring older pending proposals before creating a new one.
  - Cross-user isolation is enforced by filtering pending proposals by both user_id and robot_id.
  - Boundary memories such as never ... and ask before ... are supported.

  Important defect:

  - Safety is recorded during memory proposal flow, but it does not gate proposal creation. In app/orchestrator.py, _process_memory_proposal()
    creates SafetyDecision and still persists ProposedMemory unconditionally. That means prohibited or sensitive memory content can still be
    proposed even if safety would object. This is not a Stage 2 test failure, but it is a real architectural weakness.

  Important risk:

  - The trigger my is overbroad. app/memory_extraction.py will treat any text beginning with my  as memory intent. That is useful for
    onboarding, but it will produce false positives and may capture sensitive data too eagerly.

  7. Persistence Review
  Verified in code:

  - ProposedMemory exists and is persisted.
  - MemoryItem exists and is persisted on approval only.
  - REJECT updates proposal status and creates no durable memory.
  - Task.kind distinguishes GENERAL_TASK, MEMORY_PROPOSAL, and MEMORY_DECISION.
  - SkillManifest is loaded from JSON and persisted in DB.
  - TokenUsageEvent is created for proposal turns and decision turns.

  Verified in tests:

  - Proposal creates ProposedMemory(PENDING) and zero MemoryItem.
  - Approval creates one MemoryItem(ACTIVE) and marks proposal APPROVED.
  - Rejection creates no MemoryItem and marks proposal REJECTED.
  - Cross-user approval does not resolve another user’s proposal.

  Not yet implemented:

  - Active memories are not loaded into normal task flow as context.
  - There is no list/read path.
  - There is no forget/control path.

  8. Stage 2 Defects / Repairs Needed
  Blocking defects:

  - None. Stage 2 is valid enough to proceed.

  Non-blocking but real issues:

  - Safety does not gate memory proposal persistence.
  - Trigger my is too broad and can cause false-positive memory capture.
  - There is no explicit test proving old pending proposals become EXPIRED when replaced.
  - There is no visible memory inspection or forgetting path, which is now the main trust gap.
  - roboticxs.db sits in the repo root, which is poor source-artifact hygiene.

  9. Stage 3 User Story Proposal
  As a Roboticxs user, I can ask my robot what it remembers, remove memories I no longer want it to use, and have approved active memories
  inform normal task replies without creating or changing memory silently.

  10. Stage 3 Technical Spec Proposal
  Stage 3 should add three narrow behaviors:

  1. Memory listing:
      - detect what do you remember
      - load MemoryItem(status=ACTIVE) for the same user/robot
      - return a readable list with stable IDs or short references
  2. Memory forgetting:
      - detect forget memory <id>
      - locate only that user/robot’s memory
      - mark status=FORGOTTEN
      - do not physically delete rows
  3. Normal task memory context:
      - on non-memory-control normal tasks, load active memories read-only
      - do not mutate memory automatically
      - include a simple reply indicator that memory context was used

  Recommended orchestration split:

  - memory_control.py or memory_queries.py for listing and forgetting
  - keep memory_service.py focused on persistence rules
  - extend orchestrator routing, but do not keep piling all policy into one file

  11. Stage 3 Data Model Proposal
  No destructive schema change is required.

  Reuse:

  - MemoryItem.status with ACTIVE, OUTDATED, FORGOTTEN

  Recommended small additions:

  - none required if listing can use id
  - optional updated_at refresh on forget operation
  - optional response metadata only, not necessarily DB schema:
      - memory_context_used: bool
      - memory_context_count: int

  No new major table is required for Stage 3.

  12. Stage 3 Telegram UX Proposal
  Listing:

  User: what do you remember
  Robot:
  Here is what I currently remember:

  1. [mem_123] Preference: You prefer short direct answers.
  2. [mem_456] Boundary: Ask before sending messages to clients.

  Forgetting:

  User: forget memory mem_456
  Robot: Forgotten. I will no longer use that memory.

  Missing memory:

  User: forget memory mem_999
  Robot: I could not find that active memory for your robot.

  Normal task with memory context:

  User: Help me draft a follow-up
  Robot: I can help with that. I used your saved preferences and robot limits as context for this reply.

  13. Stage 3 Acceptance Criteria

  - what do you remember lists active memories for the same user/robot only.
  - The listing excludes FORGOTTEN memories.
  - The listing includes stable memory IDs or equivalent references usable for forgetting.
  - forget memory <id> marks the target memory FORGOTTEN, not deleted.
  - Forgetting is scoped to the same user and robot.
  - Another user cannot forget someone else’s memory.
  - Forgotten memories do not appear in memory listings.
  - Forgotten memories are not loaded into normal task context.
  - Normal task flow loads only ACTIVE memories as read-only context.
  - Normal task flow does not create memory silently.
  - Memory read/control turns still create Task, TaskRun, and TokenUsageEvent.
  - Stage 1 and Stage 2 tests continue to pass.

  14. Stage 3 Non-Goals

  - PDF ingestion
  - Memory Center UI
  - connectors
  - proactive triggers
  - vector or semantic retrieval
  - real LLM extraction
  - real Telegram send
  - billing/admin/dashboard work
  - multi-provider routing changes

  15. Likely Files To Change In Stage 3

  - app/orchestrator.py
  - app/memory_service.py
  - new module such as app/memory_control.py
  - app/reply_composer.py
  - possibly app/schemas.py if response metadata is added
  - tests/test_memory_onboarding.py
  - new tests such as tests/test_memory_control.py

  16. Test Plan For Stage 3

  - list active memories for one user/robot
  - verify another user’s memories do not appear
  - forget one active memory by ID
  - verify forgotten memory status becomes FORGOTTEN
  - verify forgotten memory no longer appears in listings
  - verify forgotten memory is not loaded into normal task context
  - verify normal tasks still create no silent memory
  - verify token usage is logged on list and forget turns
  - rerun all existing Stage 1 and Stage 2 tests unchanged

  17. Human Approval Questions

  - Confirm the exact text trigger for listing. Default: only what do you remember in Stage 3.
  - Confirm the forget command shape. Default: forget memory <id> only, no fuzzy matching yet.
  - Confirm whether normal task replies should expose memory usage in plain text every time. Default: yes, a short explicit indication improves
    trust.

  18. Recommended Next Codex Prompt
  Use a Stage 3 build prompt that says: extend the current text-only FastAPI loop with a memory read/control path, support what do you remember
  and forget memory <id>, mark memories FORGOTTEN instead of deleting them, load only ACTIVE memories as read-only context for normal tasks,
  keep token/task logging intact, preserve Stage 1 and Stage 2 behavior, and add tests for user/robot isolation, forgetting, exclusion of
  forgotten memories, and normal-task memory-context usage.
