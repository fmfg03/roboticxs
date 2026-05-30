# ROBOTICXS Implementation Status

## 1. Implemented stages

### Core runtime
- Stage 1: text-only Telegram control loop over FastAPI + SQLite
- Stage 2: local skill manifest loading and basic assistant routing
- Stage 3: memory proposal flow
- Stage 4: memory approval / rejection
- Stage 5: memory list / forget
- Stage 6: text-simulated document review
- Stage 7: document review history / forget
- Stage 8: Telegram file metadata intake
- Stage 9: file metadata list / forget
- Stage 10: model routing and cost scaffolding
- Stage 11: local token / usage reporting

### Budget control system
- Stage 12A: budget guardrails across approved spend-producing flows
- Stage 13A: per-robot local budget limit configurability
- Stage 14A: per-robot warn / block threshold configurability
- Stage 15A: budget policy reset / restore defaults

### Retrieval-control ladder
- Stage 16A: metadata-only file retrieval preflight / stub
- Stage 17A: retrieval intent list / cancel
- Stage 18A: mock-only retrieval adapter contract
- Stage 19A: explicit retrieval enablement policy gate
- Stage 20A: retrieval policy status / diagnostics surface
- Stage 21A: retrieval enablement request stub
- Stage 22A: retrieval enablement request pending / approve / reject control surface
- Stage 23A: retrieval enablement request history
- Stage 24A: retrieval control summary
- Stage 25A: retrieval control report

## 2. Current runtime boundaries

### What the runtime can do today
- Receive Telegram text messages
- Persist users, robots, tasks, routing logs, safety decisions, token usage, memories, document-review records, file metadata, retrieval intents, and retrieval enablement requests
- Run local budget guardrails per user and per robot
- Show local retrieval-control state through status, history, summary, and report commands

### What remains explicitly disabled
- No Telegram `getFile`
- No file download
- No HTTP or network retrieval path for attachments
- No raw byte persistence
- No extracted text persistence
- No downloaded file path persistence
- No PDF parsing
- No OCR
- No content review from file bytes
- No provider execution
- No billing, payment, invoice, or reconciliation behavior
- No dashboard UI
- No connector sync

### Retrieval policy state
- Retrieval is still disabled by explicit local policy
- Current adapter seam is mock-only
- All retrieval-related commands are metadata and control only

## 3. Known gaps

- No live file retrieval exists
- No transport implementation exists behind the retrieval adapter
- No attachment-content parsing stack exists
- No OCR stack exists
- No provider execution path exists
- No operator export / download surface exists for audit data
- `app/orchestrator.py` is still acceptable, but command routing continues to grow
- The repo has moved from planning-only into implementation, but top-level repo docs still lag the actual runtime state

## 4. Next 10 stages

### Stage 26A
- Retrieval control activity feed
- Show recent retrieval-intent and enablement-request events in one read-only feed

### Stage 27A
- Retrieval control report snapshot variants
- Add a bounded operator view optimized for recent changes vs current state

### Stage 28A
- Retrieval-control retention policy
- Define how long retrieval intents and enablement-request records should remain active or reportable

### Stage 29A
- Retrieval-control admin notes stub
- Allow local operator annotations on retrieval-control decisions without changing retrieval state

### Stage 30A
- Mock transport capability matrix
- Describe which retrieval capabilities are still disabled and what would be required before any live step

### Stage 31A
- Transport enablement preconditions surface
- Read-only explanation of policy, safety, authority, and audit prerequisites for live retrieval

### Stage 32A
- Attachment-type policy classification stub
- Local-only classification of attachment categories without downloading files

### Stage 33A
- Retrieval adapter contract hardening
- Tighten result semantics before any transport implementation is considered

### Stage 34A
- Operator review queue summary
- Unify pending retrieval intents and pending enablement requests into a higher-level control queue

### Stage 35A
- Pre-live retrieval readiness validation
- Explicit checklist that must pass before even a gated `getFile` implementation is discussed

## 5. Product authority model

### User authority
- The user decides what the robot is allowed to remember
- The user decides local budget policy per robot
- The user can reset local budget policy
- The user can request retrieval intent
- The user can request future retrieval enablement
- The user can inspect and cancel pending retrieval intent
- The user can inspect and resolve retrieval enablement requests

### Robot authority
- The robot may classify, route, log, and persist approved local metadata
- The robot may not silently expand its authority surface
- The robot may not cross from metadata to attachment-content authority without an explicit approved stage

### System authority boundaries
- Budget policy is local guardrail authority, not provider-account authority
- Retrieval policy is local capability authority, not transport authority
- Safety decisions, model routing, and token logging are audit and control mechanisms, not execution licenses

## 6. Skills roadmap

### Near-term product skills
- Personal memory skills
- Bounded document review skills from explicit user-supplied text
- File metadata management skills
- Retrieval-control and operator-audit skills

### Mid-term skills after authority expansion
- Safe attachment preparation skills
- Controlled extraction skills after explicit transport approval
- Domain review skills that operate on parsed content only after the parsing boundary is approved

### Skills principles
- Keep skill manifests structurally separate from orchestration/runtime code
- Treat each skill family as a bounded authority surface
- Do not let a skill imply transport, provider, or billing authority unless that authority was explicitly added

## 7. What must never be automated silently

- Retrieval enablement
- Any flip from disabled retrieval to enabled retrieval
- Telegram `getFile`
- File download
- Any network access for attachment retrieval
- PDF parsing
- OCR
- Raw byte storage
- Extracted text storage
- Content review claims from attachment bytes
- Budget-policy relaxation
- Memory approval
- Any action that changes user-visible authority boundaries
- Any provider execution
- Any billing, payment, invoice, or reconciliation behavior

## Functional MVP estimate

Estimated completion toward a functional bounded MVP: roughly 65% to 75%.

Why this is not higher:
- The control plane is strong
- Auditability is strong
- Budget and retrieval authority boundaries are strong
- But the product still lacks any approved live execution surface for attachment retrieval, parsing, provider execution, and higher-value task completion beyond text-only and metadata-only flows
