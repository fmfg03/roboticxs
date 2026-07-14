# Roboticxs Roadmap Pivot — Stage 33P–46P after ADK Pattern Harvest v0.1

**Project:** Roboticxs.com
**Date:** 2026-06-01
**Status:** Planning / roadmap candidate
**Depends on:** Clean runtime branch / workspace hygiene from Stages 27P–32P

This document does not authorize runtime implementation.

Runtime truth remains the clean `runtime/cherry-pick-27p-32p` branch until separately promoted.

Stages listed here require individual story/spec approval before implementation.

---

## 1. Current Runtime Baseline

Implemented runtime stages before this pivot:

```text
27P — Qué se me pasó / Attention Summary v0
28P — Robot Folder / Mi información importante v0
29P — Skill Catalog + Capability Resolver v0
30P — Súper Familiar v0
31P — Web Workflow Preflight Framework v0
32P — Action Approval Packets v0
```

Operational note:

```text
Before starting new runtime functionality, finish workspace hygiene and promote only from the clean runtime branch, not from a mixed dirty workspace.
```

---

## 2. Roadmap Principle

Do not add Google ADK samples directly to Roboticxs.

Convert them into internal Roboticxs patterns:

```text
ADK sample → pattern harvest → Roboticxs spec → scoped runtime story → tests → validation
```

Priority rule:

```text
First improve routing, skill loading, assistance protocol, and case tracking.
Then add heavier connectors, realtime UI, and demo skills.
```

---

## 3. Updated Stage Sequence

| Stage | Name | Type | Main source inspiration | Runtime impact |
|---|---|---|---|---|
| 33P | Command Routing Consolidation / Flow Registry Hardening | Runtime architecture | Current Roboticxs debt | Refactor/control only |
| 34P | ADK Agent Garden Harvest Index | Docs/research | All reviewed samples | No runtime |
| 35P | Skill Progressive Disclosure | Runtime architecture | `agent-skills-tutorial` | Skill loading/control |
| 36P | Robbie Assistance Protocol | Runtime behavior | `customer-service` | Cross-skill handling |
| 37P | Case / Follow-up Tracker v0 | Runtime feature | `incident-management` | Local cases |
| 38P | Claims & Cancellation Prep v0 | Runtime feature | Customer service + incident patterns | Draft/prep only |
| 39P | Scheduled Attention Digest v0 | Runtime feature | `workflow-morning_email_debrief` | Read-only local/simulated schedule |
| 40P | Google Drive OAuth Connector v0 | Connector foundation | `adk-ae-oauth` | Read-only file access |
| 41P | Grounded Document Knowledge Layer v0 | Runtime/document layer | `RAG`, `multiformat-hybrid-rag` | Local scoped docs/retrieval |
| 42P | Operational Workflow Orchestration v0 | Runtime architecture | `hierarchical-workflow-automation` | Sequential workflows |
| 43P | Approved Long-Running Workflow v0 | Runtime architecture | `deep-search` | Plan approval before work |
| 44P | Connector API Governance v0 | Connector governance | `auto-insurance-agent` | API operation policy |
| 45P | Robbie Live Companion v0 | Interaction layer | `realtime-conversational-agent` | Voice/live observation only |
| 46P | Antojo Cerca de Mí Demo Skill | Demo skill | `gemma-food-tour-guide` | Low-risk wow demo |

---

## 4. Stage Details

## Stage 33P — Command Routing Consolidation / Flow Registry Hardening

**Objective:** Shrink `app/orchestrator.py` and stop adding linear parse branches before more flows are added.

**Why now:** Stages 27P–32P expanded routing. New stages will multiply flows unless routing is consolidated first.

**Scope:**

```text
- consolidate exact-command flow registry
- separate parse-based routing from flow execution
- preserve existing behavior
- no new product feature
- no connector work
```

**Acceptance criteria:**

```text
- existing Stage 27P–32P commands still pass
- flow registry owns exact commands
- orchestrator has fewer direct branches
- no behavior expansion
- full test suite passes
```

---

## Stage 34P — ADK Agent Garden Harvest Index

**Objective:** Add official research artifact summarizing harvested Google ADK patterns.

**Scope:**

```text
- docs/research/GOOGLE_ADK_AGENT_GARDEN_HARVEST_INDEX_v0_1.md
- no runtime
- no repo integration
- no claims of Google compatibility
```

**Acceptance criteria:**

```text
- reviewed samples are listed
- pattern/use/non-copy matrix included
- Roboticxs/Agentius/Zaubern mappings included
- source references included
```

---

## Stage 35P — Skill Progressive Disclosure v0

**Objective:** Upgrade Skill Catalog from static listing to L1/L2/L3 skill loading architecture.

**Inspired by:** `agent-skills-tutorial`.

**Scope:**

```text
- L1 catalog metadata remains always available
- L2 skill instruction loader introduced
- L3 resource/template loader introduced as local static registry
- no external skill loading
- no generated active skills
- no paid billing effects
```

**Acceptance criteria:**

```text
- capability resolver can identify skill using L1 metadata
- skill instructions load only when matched
- skill resources load only when requested by skill logic
- blocked actions remain globally blocked
- tests prove L2/L3 do not expand authority
```

---

## Stage 36P — Robbie Assistance Protocol v0

**Objective:** Establish a cross-skill protocol for how Robbie handles operational requests.

**Inspired by:** `customer-service`.

**Protocol:**

```text
1. classify intent
2. check skill scope
3. check approved context before asking user
4. ask only missing information
5. prepare recommendation/draft/checklist
6. create action packet if action is sensitive
7. block prohibited actions
8. log outcome
```

**Scope:**

```text
- local-only
- no connector calls
- no external action
- no memory mutation except existing approved flows
```

**Acceptance criteria:**

```text
- Robbie checks approved memory/local context before asking repeat questions
- pending memory is not treated as fact
- out-of-scope requests redirect/offer upgrade/block correctly
- sensitive requests produce action packet, not execution
```

---

## Stage 37P — Case / Follow-up Tracker v0

**Objective:** Add first-class local cases for open matters that need tracking.

**Inspired by:** `incident-management`.

**Scope:**

```text
- local case creation
- status / urgency / impact / next action
- follow-up date
- manual close/delete
- appears in Qué se me pasó
- no external ticket creation
- no polling
```

**Acceptance criteria:**

```text
- user can create a local case only after summary/approval
- case has status, urgency, impact, next action, follow-up date
- case appears in attention summary
- case can be closed or deleted
- no external systems touched
```

---

## Stage 38P — Claims & Cancellation Prep v0

**Objective:** Add high-value prep-only skill for claims, cancellations, refunds, service changes, and subscription changes.

**Scope:**

```text
- classify request type
- gather missing facts
- identify evidence needed
- draft message/script/checklist
- create local follow-up case after approval
- no external send
- no cancellation submission
- no account login
- no legal/financial decision
```

**Acceptance criteria:**

```text
- Robbie distinguishes claim/cancellation/refund/service-change/subscription-change
- Robbie produces case summary and missing evidence checklist
- Robbie drafts message/script
- Robbie creates action packet for any external step
- Robbie creates local case only after approval
```

---

## Stage 39P — Scheduled Attention Digest v0

**Objective:** Prepare the scheduling model for periodic attention summaries without external live sources.

**Inspired by:** `workflow-morning_email_debrief`.

**Scope:**

```text
- local/simulated scheduler metadata
- last-run digest state
- read-only local attention sources
- no Gmail live connector yet
- no send/archive/delete
- no silent memory
```

**Acceptance criteria:**

```text
- user can see scheduled digest configuration
- digest uses local state only
- last run has receipt
- no connector calls
- no external actions
```

---

## Stage 40P — Google Drive OAuth Connector v0

**Objective:** Add delegated read-only Google Drive access foundation.

**Inspired by:** `adk-ae-oauth`.

**Scope:**

```text
- OAuth delegated read-only scope
- single file read by user-provided file ID or selected file path
- file metadata receipt
- no folder sync
- no write/delete/share
- no automatic indexing
- no direct MemoryItem creation
```

**Acceptance criteria:**

```text
- user explicitly authorizes read-only Drive scope
- Robbie reads selected file only
- read event records file id/name/mime/time
- content is not persisted unless user approves document review artifact
- ProposedMemory only after explicit user-facing explanation
- disconnect/revoke path exists
```

---

## Stage 41P — Grounded Document Knowledge Layer v0

**Objective:** Establish document-grounded answering over approved local/document-review sources.

**Inspired by:** `RAG`, `multiformat-hybrid-rag`.

**Scope:**

```text
- local document references only
- simple source references
- no heavy GCS/BigQuery/Vector Search dependency
- no broad Drive indexing
- no OCR unless separately approved later
- no automatic memory
```

**Acceptance criteria:**

```text
- answers cite internal document/source references
- Robbie abstains when no source supports the answer
- pending/unapproved documents are not used
- delete/forget document removes source references from retrieval path
```

---

## Stage 42P — Operational Workflow Orchestration v0

**Objective:** Introduce sequential workflow orchestration with state handoff and receipts.

**Inspired by:** `hierarchical-workflow-automation`.

**Scope:**

```text
- local workflow steps only
- state handoff between steps
- action class per step
- no real email/calendar/API mutation
- simulated steps must be clearly labeled
```

**Acceptance criteria:**

```text
- workflow step state is explicit
- each step has action class
- blocked/sensitive steps produce action packet
- simulated/fallback steps are labeled
- final workflow summary includes receipt-style state
```

---

## Stage 43P — Approved Long-Running Workflow v0

**Objective:** Add plan-before-work pattern for longer tasks.

**Inspired by:** `deep-search`.

**Scope:**

```text
- plan creation
- user approval required before execution
- bounded local execution
- no web search unless separately allowed later
- no connector actions
```

**Acceptance criteria:**

```text
- Robbie proposes plan before long work
- user can approve/edit/reject
- execution stays within approved plan
- final artifact lists sources/steps/limitations
```

---

## Stage 44P — Connector API Governance v0

**Objective:** Define connector/API operation policy before adding more external tools.

**Inspired by:** `auto-insurance-agent`.

**Scope:**

```text
- connector registry metadata
- operation allowlist
- auth mode classification
- action class classification
- approval and receipt requirements
- no broad API integrations yet
```

**Acceptance criteria:**

```text
- each connector operation has action class
- each operation declares auth mode and approval requirement
- write/mutate operations are blocked or approval-gated
- receipts required for external mutations
```

---

## Stage 45P — Robbie Live Companion v0

**Objective:** Add or prototype realtime voice/screen-share interaction surface, observation-only.

**Inspired by:** `realtime-conversational-agent`.

**Scope:**

```text
- voice/live transcript or UI prototype
- optional screen/camera observation later
- no memory persistence by default
- no send/click/pay/book/cancel
- guidance only
```

**Acceptance criteria:**

```text
- session start/stop explicit
- no recording retention by default
- sensitive visible data is not stored as memory
- action requests route to action packets
```

---

## Stage 46P — Antojo Cerca de Mí Demo Skill

**Objective:** Add a low-risk consumer wow demo skill using food/location planning.

**Inspired by:** `gemma-food-tour-guide`.

**Scope:**

```text
- text/photo craving input
- explicit location permission
- search places / suggest route conceptually
- no reservation
- no ordering
- no payment
- no persistent location memory
```

**Acceptance criteria:**

```text
- no invented place IDs/addresses
- prices and availability labeled approximate
- user location is session-scoped unless approved
- output is recommendation only
```

---

## 5. Priority Summary

Immediate sequence:

```text
33P → 34P → 35P → 36P → 37P → 38P
```

Rationale:

```text
Before adding external sources, Robbie needs clean routing, skill loading, assistance protocol, and case tracking.
```

Connector sequence:

```text
39P scheduled local digest
40P Drive OAuth read-only
41P grounded document knowledge
44P connector API governance
```

Demo/interface sequence:

```text
45P Robbie Live Companion
46P Antojo Cerca de Mí
```

---

## 6. Hard Non-Goals Across Stages 33P–46P

Unless a later spec explicitly admits it, these remain blocked:

```text
- autonomous checkout
- autonomous payment
- autonomous cancellation submission
- autonomous email send
- autonomous calendar booking
- autonomous legal/medical/financial decisions
- silent memory creation
- broad Drive/Gmail/Calendar scanning
- hidden background polling
- external mutation without approval receipt
- use of prompt-only safety as authority gate
```
