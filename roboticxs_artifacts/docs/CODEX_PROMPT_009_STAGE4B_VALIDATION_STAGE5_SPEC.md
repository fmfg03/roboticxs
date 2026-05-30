# CODEX PROMPT 009 — Roboticxs Stage 4B Validation + Stage 5 Spec

You are Codex operating inside the Roboticxs repository.

This is a **read-only validation and specification task**.

Do not modify files. Do not create files. Do not delete files. Do not refactor. Do not install packages. Do not widen scope.

Your job is to validate the Stage 4B narrow Documents/PDF skill implementation and then propose the next Stage 5 direction.

## Canonical Context

Roboticxs is a Telegram-first personal AI robot product. It should compete on memory, skills, cost visibility, safety boundaries, and daily usefulness, not on raw chatbot intelligence.

Relevant product constraints:

- One robot, many skill packages.
- Memory must remain user-approved, inspectable, and forgettable.
- Documents/PDF skill is valuable, but must stay bounded.
- Document review is draft-only.
- The product must never claim legal, tax, financial, medical, employment, certified-signature, or lawyer-replacement authority.
- Sensitive actions require confirmation or must be blocked.
- No silent external side effects.
- Stage 4B intentionally uses text-simulated document review only.

## Current Report To Validate

Stage 4B claims:

- Accepted deterministic commands:
  - `review document: <text>`
  - `summarize document: <text>`
  - `mark risks in document: <text>`
  - `prepare notes from document: <text>`
- No OCR.
- No PDF binary parsing.
- No Telegram file download.
- No connector sync.
- No certified-signature path.
- No professional-advice claims.
- `app/document_review.py` owns deterministic document-review logic.
- Document-review turns create:
  - `Task`
  - `TaskRun`
  - `SafetyDecision`
  - `DocumentTask`
  - `ModelRouteDecision`
  - `TokenUsageEvent`
- `DocumentTask` stores preview + hash, not full raw document text by default.
- Replies include summary, risk notes, follow-up questions, draft notes/checklist, and explicit professional-advice boundary.
- Document-review turns do not create or mutate memory.
- Tests reportedly pass.

## Allowed Commands

You may run read-only / validation commands only:

```bash
python3 -m pytest -q
python3 -m compileall app tests
find . -maxdepth 3 -type f | sort
sed -n '1,240p' app/document_review.py
sed -n '1,260p' app/orchestrator.py
sed -n '1,260p' app/models.py
sed -n '1,260p' app/reply_composer.py
sed -n '1,260p' app/safety.py
sed -n '1,260p' tests/test_document_review.py
grep -R "legal signature\|certified signature\|lawyer replacement\|legal advice\|tax advice\|financial advice\|medical advice" -n app tests README.md docs || true
```

You may inspect additional files if needed, but only read them.

## Forbidden Actions

Do not run:

```bash
pip install
poetry install
uv sync
npm install
pnpm install
rm
mv
cp
mkdir
touch
python scripts that mutate files
formatters that rewrite files
```

Do not edit code.
Do not create migrations.
Do not create tests.
Do not create docs.
Do not add real Telegram file handling.
Do not add OCR.
Do not add PDF parsing.
Do not add connector sync.
Do not add live LLM/provider calls.

## Validation Tasks

### 1. Test and Compile Validation

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests
```

Report exact outputs.

### 2. Stage 4B Claim Verification

Verify whether the implementation actually supports:

- `review document: <text>`
- `summarize document: <text>`
- `mark risks in document: <text>`
- `prepare notes from document: <text>`
- deterministic command detection
- `DocumentTask` persistence
- preview + hash storage
- no full raw text stored by default
- correct user/robot/task linkage
- `Task`, `TaskRun`, `SafetyDecision`, `ModelRouteDecision`, and `TokenUsageEvent` creation
- no memory mutation during document review
- required professional-advice boundary
- no certified-signature/legal-signature claim
- no real file transport, OCR, PDF binary parsing, or connector sync

### 3. Safety Review

Inspect whether document-review prompts that ask for professional authority are refused or bounded.

Check at minimum:

- legal advice request
- tax advice request
- financial advice request
- medical advice request
- employment decision request
- certified signature request
- legal signature request
- signing/execution request

Report whether each is:

- blocked/refused
- bounded as draft-only
- incorrectly answered as authority
- untested/unknown

### 4. Data Minimization Review

Verify:

- full document text is not persisted by default
- preview length is bounded
- hash is deterministic
- preview could still contain sensitive text, so Stage 5 may need document history/control or retention controls

### 5. Architecture Boundary Review

Assess:

- whether document logic is mostly in `app/document_review.py`
- whether `app/orchestrator.py` grew too much
- whether document review duplicated routing/token/safety logic instead of reusing existing helpers
- whether Telegram adapter remains transport-only

### 6. Regression Review

Confirm Stage 1–3 behavior still passes.

At minimum check whether existing tests still cover:

- Telegram text loop
- memory proposal/approval/rejection
- memory listing/forgetting
- safety rules
- token usage logging

## Stage 5 Recommendation

After validation, recommend one of these paths:

### Option A — Stage 5A Document History / Control / Retention

Use this if Stage 4B persists `DocumentTask` previews and there is no user-facing way to inspect or control document review records.

Candidate scope:

- `what documents did you review`
- `forget document <id>` or `delete document record <id>`
- mark document records as `FORGOTTEN` or `REMOVED`, not physical delete by default
- exclude forgotten document records from listings
- keep raw text non-persistence rule
- maintain task/token/safety logging
- no PDF/OCR/file transport yet

Reason: if the product stores document previews/hashes, the user should have a control path before the platform accepts real files.

### Option B — Stage 5B Controlled Telegram File Intake Stub

Use this only if Stage 4B document record control is already adequate or intentionally deferred.

Candidate scope:

- accept mocked Telegram document payload shape only
- no network file download
- no OCR
- no binary PDF parsing
- create `DocumentTask` with metadata only
- reply with “file received, review requires extracted text” or similar safe bounded response
- preserve safety/token/task logging

Reason: prepares real file UX while keeping external file handling disabled.

### Option C — Stage 5C Orchestrator Split / Architecture Hardening

Use this if `app/orchestrator.py` has become too policy-heavy and blocks safe expansion.

Candidate scope:

- refactor routing into narrow handlers without changing behavior
- keep all tests passing
- no new product capability

Reason: avoid turning the orchestrator into an untestable policy sink.

## Default Recommendation Preference

Default to **Stage 5A Document History / Control / Retention** unless validation shows DocumentTask records are not persisted, previews contain no user-sensitive content, or there is already a sufficient document control path.

Do not recommend real PDF parsing, OCR, live Telegram file download, or connector sync yet.

## Required Output Format

Return a report with exactly these sections:

1. Stage 4B Validation Summary
2. Validation Commands Run
3. Files Verified
4. Test Results
5. Stage 4B Claim Verification
6. Safety Review
7. Data Minimization Review
8. Architecture Boundary Review
9. Regression Review
10. Defects / Repairs Needed
11. Stage 5 Recommendation
12. Stage 5 User Story Proposal
13. Stage 5 Technical Spec Proposal
14. Stage 5 Acceptance Criteria
15. Stage 5 Non-Goals
16. Likely Files To Change In Stage 5
17. Test Plan For Stage 5
18. Human Approval Questions
19. Recommended Next Codex Prompt

Keep the report factual. Cite specific files and test names when possible. Separate verified facts from recommendations.
