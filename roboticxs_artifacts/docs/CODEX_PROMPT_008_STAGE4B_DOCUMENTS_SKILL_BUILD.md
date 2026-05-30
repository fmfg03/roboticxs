# CODEX PROMPT 008 — Stage 4B Narrow Documents/PDF Skill Build

You are working inside the Roboticxs repository.

Follow the repo instructions in `AGENTS.md` and the existing staged Codex protocol. This is a scoped build prompt, not a general MVP prompt.

## 0. Current validated baseline

Stage 1, Stage 2, and Stage 3 are already implemented and validated.

The app currently supports:

- FastAPI backend
- Telegram-style text webhook
- deterministic scope guard
- deterministic safety decisions
- stub model routing
- token usage logging
- durable memory onboarding with `ProposedMemory` and explicit `APPROVE` / `REJECT`
- memory read/control through `what do you remember` and `forget memory <id>`
- active memory context loaded read-only during normal task replies

Validation baseline:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

The previous validation reported:

- `34/34 tests passed`
- compileall passed
- no blocking defects

## 1. Objective

Implement Stage 4B: a narrow, draft-only Documents/PDF skill entrypoint.

This stage must not become a full PDF pipeline. It must add the first safe document-review capability while preserving the Stage 1–3 control loop.

## 2. Product boundary

Roboticxs may help users review document-like text.

Allowed outputs:

- summary
- draft review
- risk notes
- meeting-prep notes
- action checklist

Forbidden outputs / claims:

- legal advice
- tax advice
- financial advice
- medical advice
- employment decision advice
- certified signature claim
- legal signature claim
- lawyer/accountant/doctor replacement claim
- silent external action
- signature execution
- payment/refund/deletion/configuration action

The output must be explicitly bounded and draft-only.

## 3. Stage 4 implementation decisions

Use these decisions. Do not ask for approval again.

### 3.1 Intake mode

Start with pure text-simulated document review only.

Do not implement live Telegram file download.
Do not implement mocked Telegram file payloads yet.
Do not implement OCR.
Do not implement PDF binary parsing.

Accepted Stage 4 text command forms:

```text
review document: <document-like text>
summarize document: <document-like text>
mark risks in document: <document-like text>
prepare notes from document: <document-like text>
```

Command matching should be deterministic and case-insensitive.

### 3.2 Persistence

Add a minimal `DocumentTask` or equivalent table/model now.

Reason: Documents/PDF is a distinct premium skill surface and should not be hidden inside generic `Task` only.

Keep the model narrow.

Recommended fields:

- `id`
- `user_id`
- `robot_id`
- `task_id`
- `review_type`
- `source_kind`
- `source_text_preview`
- `source_text_hash`
- `status`
- `created_at`
- `updated_at`

Do not store full raw document text by default.

Use:

- `source_kind = TEXT_SIMULATED`
- `status = DRAFTED` or equivalent
- `source_text_preview` capped to a safe short length, such as 500 characters
- `source_text_hash` deterministic hash of the input text

### 3.3 First output mode

Prioritize summary plus risk-marking together, both draft-only.

The response should include:

- brief summary
- possible risk notes
- suggested follow-up questions
- explicit boundary/disclaimer

The review may be deterministic and simple. No live LLM call is required.

## 4. Required architecture

Add document-review logic outside the Telegram adapter.

Preferred new module:

```text
app/document_review.py
```

Keep responsibilities separated:

- Telegram adapter: payload normalization only
- orchestrator: route to document-review branch
- document_review module: detect command, parse review type, generate draft review payload
- safety layer: ensure document-review outputs remain bounded
- reply composer: format bounded user reply
- token logger/model router: reused from existing Stage 1–3 helper flow

`app/orchestrator.py` is already becoming policy-heavy. Avoid adding large inline document policy there. Keep document-specific logic in the new module.

## 5. Required behavior

When a user sends one of the accepted document-review commands:

1. Normalize the Telegram text update using the existing path.
2. Resolve/create user and robot using existing behavior.
3. Create `Task` and `TaskRun`.
4. Detect document-review intent deterministically.
5. Run safety decision before composing the final reply.
6. Create a `DocumentTask` record.
7. Create `ModelRouteDecision`.
8. Create `TokenUsageEvent`.
9. Return a Telegram-style reply payload.

The response must not claim the robot performed legal review or certified signing.

## 6. Required reply language

Every document-review reply must include a boundary like this, or semantically equivalent wording:

```text
This is a draft document review, not legal, tax, financial, medical, or professional advice. I can help summarize and flag items for your review, but you must decide what to do next.
```

Do not use consumer-facing Zaubern/SAL/DSSE/conformity language.

## 7. Memory interaction rule

Document-review turns may load active memory context read-only if the current normal task path already does so, but Stage 4 must not create, edit, or forget memory.

Do not automatically store document content as memory.

Do not create `ProposedMemory` from document-review text.

## 8. Safety rules to preserve

Existing safety behavior must remain intact:

- payment execution: `BLOCK`
- account deletion: `BLOCK`
- credential/permission changes: `BLOCK`
- external send/write/scheduling: `ASK_CONFIRMATION`
- legal/tax/medical professional advice: refused/escalated or bounded, not answered as authority

Document review must be allowed only as draft-only summarization/review, not as professional advice.

If a document-review command asks for legal/tax/financial/medical/employment decision authority, reply with a bounded refusal/escalation-style message, not a review.

Examples that should not produce a normal review:

```text
review document: tell me if this contract is legally enforceable
review document: should I sign this tax settlement?
review document: certify this signature
review document: sign this document for me
```

## 9. Tests required

Add tests in a new file such as:

```text
tests/test_document_review.py
```

Cover at least:

1. `review document: ...` creates a document-review response.
2. `summarize document: ...` creates a bounded summary response.
3. `mark risks in document: ...` includes risk-note language.
4. `prepare notes from document: ...` includes notes/checklist language.
5. A `DocumentTask` or equivalent record is persisted.
6. The record is linked to the correct user, robot, and task.
7. The full raw document text is not stored by default; preview/hash behavior is used.
8. `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent` are created.
9. The reply includes the required professional-advice boundary.
10. The reply contains no certified/legal signature claim.
11. Legal/tax/financial/professional authority requests do not produce an authoritative answer.
12. Stage 1, Stage 2, and Stage 3 tests continue to pass.

Also preserve existing tests unchanged unless a change is strictly required by the new feature and justified in the completion report.

## 10. Non-goals

Do not implement:

- OCR
- PDF binary parsing
- live Telegram file retrieval
- mocked Telegram file payload handling
- connector sync
- Memory Center UI
- memory editing
- vector memory
- proactive triggers
- real LLM/provider calls
- real Telegram send
- billing/admin dashboard
- certified signature workflow
- legal-signature workflow

## 11. Validation commands

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

If either fails, fix the implementation before reporting completion.

## 12. Required completion report

Return a concise completion report with:

1. Summary
2. Files changed
3. Stage 4 behavior implemented
4. Data model changes
5. Safety boundaries implemented
6. Tests added
7. Exact validation commands and outputs
8. Remaining known gaps
9. Recommended next prompt

## 13. Stop condition

Stop after Stage 4B is implemented and validated.

Do not proceed to Stage 5.
Do not implement live file transport.
Do not widen into connectors or UI.
