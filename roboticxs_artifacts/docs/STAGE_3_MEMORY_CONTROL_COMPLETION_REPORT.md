# Roboticxs Stage 3 Memory Control — Completion Report

## 1. Summary

Implemented Stage 3 memory read/control and repaired the Stage 2 defects called out in validation.

The app now supports:

- `what do you remember`
- `forget memory <id>`
- loading only `ACTIVE` memories as read-only context during normal task replies

It also now blocks unsafe memory proposals before creating `ProposedMemory`, narrows the old overbroad `my` trigger, proves pending-proposal expiry with tests, and removes repo-root SQLite from source artifacts.

## 2. Files Changed

- `app/config.py`
- `.env.example`
- `.gitignore`
- `app/models.py`
- `app/memory_extraction.py`
- `app/memory_service.py`
- `app/memory_control.py`
- `app/reply_composer.py`
- `app/orchestrator.py`
- `tests/test_memory_onboarding.py`
- `tests/test_memory_control.py`
- `README.md`

Removed generated artifact:

- `roboticxs.db`

## 3. Stage 2 Repairs Implemented

- Safety now gates memory proposal persistence in `app/orchestrator.py`. Unsafe memory-intent turns still create `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent`, but no longer create `ProposedMemory`.
- The `my` trigger was narrowed in `app/memory_extraction.py` to explicit profile/context forms only:
  - `my name is`
  - `my role is`
  - `my company is`
  - `my timezone is`
  - `my working hours are`
  - `my preferred`
- Pending replacement expiry is now covered by test in `tests/test_memory_onboarding.py`.
- Source artifact hygiene fixed:
  - default SQLite path moved to `/tmp/roboticxs.db`
  - `.gitignore` added for DB/cache files
  - root `roboticxs.db` removed

## 4. Stage 3 Memory-Control Behavior Implemented

### `what do you remember`

- Lists only `ACTIVE` memories for the same user/robot.
- Includes stable IDs usable for forgetting.
- Excludes forgotten memories.

### `forget memory <id>`

- Marks only that same user/robot’s active memory as `FORGOTTEN`.
- Does not delete the row.
- Returns not-found for missing or another user’s memory IDs.

### Normal task flow

- Loads only `ACTIVE` memories as read-only context.
- Does not create or mutate memory silently.
- Appends a simple “used your saved ... as context” indicator when active memory context exists.

## 5. Data Model Changes

- Added `MemoryItem.display_label` in `app/models.py` to support readable listing output.
- Reused existing `MemoryItem.status` values and `updated_at` for forgetting.
- No new major Stage 3 table was added.

## 6. Test Coverage Added

New coverage includes:

- unsafe memory-intent text does not create `ProposedMemory`
- negative `my` case does not trigger memory proposal
- positive `my name is` case still creates proposal
- old pending proposal becomes `EXPIRED` when replaced
- memory listing for same user/robot
- listing isolation by user/robot
- forgetting marks `FORGOTTEN`
- forgotten memories disappear from listings
- another user cannot forget someone else’s memory
- normal task with no active memories does not claim memory context
- normal task with active memories shows memory-context indicator
- list/forget turns log token usage

## 7. Exact Validation Commands and Outputs

Commands run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Outputs:

```text
$ python3 -m pytest -q
..................................                                      [100%]

$ python3 -m compileall app tests
Listing 'app'...
Compiling 'app/orchestrator.py'...
Listing 'tests'...
```

## 8. Remaining Known Gaps

- No Memory Center UI.
- No memory editing path.
- No semantic/vector retrieval.
- No PDF/doc ingestion.
- No connectors.
- No real Telegram send.
- No real LLM routing.
- Active memories are only surfaced as lightweight deterministic context, not yet used for deeper structured reasoning.

## 9. Recommended Next Prompt

The next correct step is a read-only validation/spec prompt for Stage 3 before widening capability again.

If Stage 3 validates cleanly, decide whether Stage 4 is:

1. memory validation and tighter memory controls, or
2. the first narrow Documents/PDF skill.
