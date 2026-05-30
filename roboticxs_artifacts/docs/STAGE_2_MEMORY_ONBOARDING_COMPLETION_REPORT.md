# Roboticxs Stage 2 Memory Onboarding — Completion Report

## 1. Summary

Implemented Stage 2 durable memory onboarding on top of the Stage 1 text-only control loop.

The webhook now supports three branches:

1. normal Stage 1 task handling,
2. memory proposal creation,
3. memory decision handling.

Memory intent is detected deterministically from approved trigger phrases. A memory-intent message creates a `ProposedMemory(PENDING)` record and asks the user to reply `APPROVE` or `REJECT`. Approval creates a durable `MemoryItem(ACTIVE)`. Rejection creates no durable memory.

Approval and rejection are scoped to the same user and robot. The system keeps one pending proposal per user/robot by expiring the previous pending proposal when a new one is created.

## 2. Files Changed

- `app/models.py`
- `app/orchestrator.py`
- `app/reply_composer.py`
- `app/memory_extraction.py`
- `app/memory_service.py`
- `tests/conftest.py`
- `tests/test_memory_onboarding.py`
- `README.md`

## 3. Data Model Changes

Added:

- `ProposedMemory`
- `MemoryItem`

Updated:

- `Task.kind` to distinguish:
  - `GENERAL_TASK`
  - `MEMORY_PROPOSAL`
  - `MEMORY_DECISION`

## 4. Validation

Commands run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Results:

- `22 passed`
- `compileall` passed

## 5. Working Behavior

Supported memory-intent triggers:

- `remember that`
- `remember this`
- `my`
- `I prefer`
- `I usually`
- `never`
- `ask before`

Supported decision commands:

- `APPROVE`
- `REJECT`

Confirmed behavior:

- one pending proposal per user/robot,
- cross-user isolation on approval/rejection,
- token usage logged on proposal and decision turns,
- direct tests for `User`, `Robot`, and `SkillManifest` persistence,
- repeated-message reuse of the same user/robot.

## 6. Product Significance

This is the first implemented slice where Roboticxs stops behaving like a plain chat wrapper and starts building an approved memory profile.

The current system can now:

1. receive text,
2. identify memory intent,
3. propose memory instead of saving silently,
4. require explicit user approval,
5. persist approved memory,
6. reject discarded memory,
7. keep token and task records across memory turns.

## 7. Known Gaps

This is still not the MVP.

Missing:

- memory inspection/listing,
- memory recall during normal task handling,
- memory editing,
- memory forgetting,
- Memory Center UI,
- PDF/document ingestion,
- real Telegram send,
- real LLM calls,
- real model-provider routing,
- connectors,
- proactive triggers,
- admin dashboard.

## 8. Recommended Next Step

Do not move to PDF ingestion yet.

Stage 3 should validate Stage 2 and specify the first memory read/control slice:

1. list active memories,
2. show what the robot remembers,
3. forget a memory explicitly,
4. use active memories as read-only context in normal task handling,
5. preserve explicit approval and safety boundaries.

The correct next Codex prompt is a read-only validation/spec prompt, not a build prompt.
