# Roboticxs Stage 3 Validation + Stage 4 Recommendation

## 1. Executive Finding

Stage 3 validates cleanly enough to move forward. Tests pass, compilation passes, Stage 2 repairs are present, memory read/control exists, and the main trust boundaries are now visible to the user: approved memory only, inspectable memory, forgettable memory, and forgotten memory excluded from active use. The remaining issues are non-blocking. Based on the current repo state, Stage 4 can move to a narrow Documents/PDF skill, provided it stays tightly scoped and keeps the same safety discipline.

## 2. Validation Commands Run

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Exact outputs:

```text
$ python3 -m pytest -q
..................................                                      [100%]

$ python3 -m compileall app tests
Listing 'app'...
Listing 'tests'...
```

## 3. Files Verified

Verified present:

- app/memory_control.py
- tests/test_memory_control.py
- app/orchestrator.py
- app/memory_service.py
- app/memory_extraction.py
- app/reply_composer.py
- .gitignore
- .env.example

Also verified:

- app/telegram_adapter.py
- app/safety.py
- app/model_router.py
- tests/test_memory_onboarding.py
- tests/test_telegram_webhook.py

## 4. Test Results

- 34/34 tests passed.
- Stage 1 webhook tests still pass.
- Stage 2 memory onboarding tests still pass.
- Stage 3 memory control tests pass.
- Compile validation passed.

## 5. Stage 3 Claim Verification

Verified in code and tests:

- `what do you remember` exists via `is_list_memories_command()` in `app/memory_control.py` and `_process_memory_listing()` in `app/orchestrator.py`.
- `forget memory <id>` exists via `parse_forget_command()` and `_process_memory_forget()`.
- Only `ACTIVE` memories are listed and loaded into normal task flow: `app/memory_control.py`.
- `FORGOTTEN` memories are excluded from listing and context because queries filter `MemoryItem.status == "ACTIVE"`.
- Normal task flow does not create memory silently. The normal path in `app/orchestrator.py` reads active memories but does not create `ProposedMemory` or `MemoryItem`.
- List and forget turns still create `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent`.
- Tests directly cover listing isolation, forgetting, exclusion of forgotten memories, token logging, and normal-task memory-context indicator: `tests/test_memory_control.py`.

## 6. Stage 2 Repair Verification

Verified:

- Safety now gates unsafe memory proposal persistence. In `_process_memory_proposal()` the code creates `Task`, `TaskRun`, `SafetyDecision`, route, and token event before returning a safe reply, and does not create `ProposedMemory` when the gate fails for non-boundary proposals: `app/orchestrator.py`.
- The old broad `my` trigger is gone. Memory intent now checks only `TRIGGERS` plus explicit `PROFILE_PATTERNS`: `app/memory_extraction.py`.
- Positive explicit patterns exist:
  - `my name is`
  - `my role is`
  - `my company is`
  - `my timezone is`
  - `my working hours are`
  - `my preferred`
- Pending replacement expiry is implemented in `expire_pending_proposals()` and tested in `tests/test_memory_onboarding.py`.
- Root SQLite hygiene is corrected:
  - no `roboticxs.db` present in repo root
  - `.gitignore` ignores `*.db`, `*.sqlite`, `*.sqlite3`, `.pytest_cache/`, `__pycache__/`
  - default local DB path is `/tmp/roboticxs.db` in `app/config.py` and `.env.example`

Constraint:

- Boundary-memory proposals intentionally bypass the generic `ALLOW` gate exception in `_process_memory_proposal()`. That is why “Never send messages to clients...” can still become a proposed robot limit even though its wording overlaps with external-send safety patterns. This is coherent with the product intent, but it is a special-case boundary, not a universal rule.

## 7. Architecture Boundary Review

Good:

- Telegram adapter only normalizes payloads: `app/telegram_adapter.py`
- Memory control logic lives outside Telegram adapter: `app/memory_control.py`
- Memory service owns persistence rules: `app/memory_service.py`
- Memory extraction remains deterministic: `app/memory_extraction.py`
- Safety remains deterministic: `app/safety.py`
- Model router remains stubbed: `app/model_router.py`
- Token logging remains reused via `_persist_route_and_token()` in `app/orchestrator.py`
- No PDF, connectors, UI, proactive triggers, vector memory, or real provider calls crept in.

Concern:

- `app/orchestrator.py` is becoming too policy-heavy. It now routes normal tasks, memory proposal, memory decision, memory listing, memory forgetting, and shared route/token persistence. It is still workable, but this file is the main pressure point for future complexity.

## 8. Memory Trust Review

- Can the user see what the robot remembers?
  - Yes, via `what do you remember`.
- Can the user make the robot forget a memory?
  - Yes, via `forget memory <id>`.
- Are forgotten memories retained as rows but excluded from active use?
  - Yes. They are marked `FORGOTTEN`, not deleted, and active queries filter them out.
- Can one Telegram user see or forget another user’s memories?
  - Tests verify no.
- Can memory be created without explicit approval?
  - Durable memory: no.
  - Proposed memory: yes, but only as `PENDING`, which is the intended approval workflow.
- Can unsafe memory content be proposed or stored?
  - Unsafe non-boundary memory intent is blocked from creating `ProposedMemory`.
  - Boundary-memory proposals are still allowed as proposed robot limits.
- Does the robot disclose when active memory context was used?
  - Yes, but weakly. It appends a sentence such as “I used your saved preferences...” rather than materially changing reply behavior from memory content.

Important trust caveat:

- Active memory context is currently shallow. The code loads active memories and derives a summary label for disclosure, but it does not yet deeply incorporate the actual stored content into task reasoning or output generation. This is not a Stage 3 failure, but it means “memory used as context” currently means “memory loaded and acknowledged,” not “memory materially shaped response logic.”

## 9. Defects / Repairs Needed

Blocking:

- None.

Non-blocking:

- `app/orchestrator.py` is getting too large and policy-dense.
- Active memory context use is lightweight disclosure rather than substantive behavior shaping.
- Boundary-memory safety is handled by a special-case bypass. It works, but the rule should stay explicit in future work.
- `.pytest_cache/` and `__pycache__/` exist in the working tree as generated artifacts, though they are ignored now.

## 10. Stage 4 Recommendation

Recommend Option B — Stage 4B Narrow Documents/PDF Skill.

Reason:

- Stage 3 closed the main memory trust loop: inspect, forget, active-only use, no silent mutation, user/robot isolation.
- No blocking memory-control defect remains.
- The product docs already identify Documents/PDF as a strong premium pack.
- Widening capability now is justified, as long as the new skill stays narrow, draft-only, and heavily bounded.

## 11. Stage 4 User Story Proposal

As a Roboticxs user, I can send a document or document-like task through the Telegram-first workflow and receive a draft review or summary with visible safety boundaries, token logging, and no claim of legal, tax, financial, or certified-signature authority.

## 12. Stage 4 Technical Spec Proposal

Keep Stage 4 narrow.

Recommended Stage 4B scope:

- Add a document-review branch to the existing text-first orchestration.
- Start with simulated or fixture-backed document intake paths, not live Telegram file download unless isolated and mocked.
- Persist a minimal document/task record such as `DocumentTask` or equivalent.
- Allow draft-only outputs:
  - summarize
  - review
  - mark risks
  - prepare notes
- Preserve:
  - `Task`
  - `TaskRun`
  - `SafetyDecision`
  - `ModelRouteDecision`
  - `TokenUsageEvent`

Safety rules:

- no legal advice
- no tax/financial/professional advice
- no certified signature claims
- no silent external action
- no signature execution
- no hidden side effects

Implementation shape:

- `document_control.py` or `document_review.py`
- orchestrator routes document-review intent
- safety layer adds disclaimer-oriented outcomes
- route/token logging reused as-is

## 13. Stage 4 Acceptance Criteria

- A narrow document-review path exists without widening into OCR, connectors, or real external file APIs.
- Document-review turns create `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent`.
- Output is draft-only and explicitly bounded.
- Replies clearly state that the robot is not providing legal, tax, financial, or professional advice.
- No certified-signature or legal-signature claims appear.
- No real Telegram file send/download dependency is required in tests.
- Existing Stage 1, Stage 2, and Stage 3 tests continue to pass.

## 14. Stage 4 Non-Goals

- OCR
- full PDF ingestion pipeline
- legal-signature workflow
- connector sync
- Memory Center UI
- vector memory
- proactive triggers
- live Telegram file transport
- real provider routing changes
- billing/admin dashboard work

## 15. Likely Files To Change In Stage 4

- `app/orchestrator.py`
- new module such as `app/document_review.py`
- possibly `app/models.py`
- `app/reply_composer.py`
- `app/safety.py`
- new tests such as `tests/test_document_review.py`

## 16. Test Plan For Stage 4

- text or simulated document-review request creates task records
- safety disclaimer appears for document-review output
- no prohibited claims appear
- draft-only review/summary response is returned
- token usage is logged
- route estimate is logged
- no external network calls are required
- Stage 1, 2, and 3 tests remain green

## 17. Human Approval Questions

- Confirm whether Stage 4 should start with pure text-simulated document review first, before any mocked Telegram file payload shape.
- Confirm whether a minimal `DocumentTask` record should be added now, or whether Stage 4 should reuse generic `Task` plus metadata until the skill proves itself.
- Confirm whether Stage 4 should prioritize summary first or risk-marking first. Default recommendation: summary plus risk-marking together, both as draft-only.

## 18. Recommended Next Codex Prompt

Use a Stage 4B build prompt that says: extend the current text-only FastAPI loop with a narrow Documents/PDF skill entrypoint, keep it draft-only, reuse existing safety/token/route/task logging, prohibit legal/tax/financial/professional authority claims and certified-signature claims, avoid real Telegram file/network dependency in tests, and keep all Stage 1–3 tests passing.
