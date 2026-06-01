# Roboticxs Project Brief Addendum — ADK Pattern Harvest v0.1

**Project:** Roboticxs.com  
**Date:** 2026-06-01  
**Status:** Brief addendum / product architecture update  
**Applies to:** `docs/ROBOTICXS_PROJECT_BRIEF.md`  
**Related artifact:** `docs/research/GOOGLE_ADK_AGENT_GARDEN_HARVEST_INDEX_v0_1.md`  

---

## 1. Why This Addendum Exists

The original Roboticxs brief correctly defines Roboticxs as a mass-market personal AI robot product with memory, skills, model routing, token/cost control, and safety boundaries.

The Google ADK Agent Garden review adds a stronger architecture pattern:

> Roboticxs should not be framed merely as “one robot with many skills.” It should be framed as **one personal robot with a progressive catalog of governed workflows**.

This does not replace the existing brief. It sharpens it.

---

## 2. Updated Product Thesis

Original thesis:

> One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.

Expanded thesis:

> One personal AI robot that loads the right skill, checks authorized context first, prepares useful work, asks before sensitive actions, tracks open cases, and produces receipts for what it did or refused to do.

Short version:

```text
Roboticxs is not a chatbot.
Roboticxs is a personal robot with governed workflows.
```

---

## 3. Updated Product Architecture

```text
Interaction Layer
  - Telegram / chat
  - Web UI
  - future voice/live/screen-share companion

Robot Core
  - user identity
  - robot identity
  - Robot Folder / Mi información importante
  - approved memory
  - pending memory proposals
  - local state
  - token/cost awareness

Progressive Skill Catalog
  - L1: skill metadata
  - L2: full skill instructions
  - L3: templates/resources/playbooks

Assistance Protocol
  - intent classification
  - context-first lookup
  - skill match
  - missing information request
  - recommendation/draft/checklist
  - action packet
  - approval/block/receipt

Workflow Layer
  - attention summaries
  - case/follow-up tracking
  - claims/cancellation prep
  - scheduled digests
  - long-running approved workflows
  - operational workflows

Connector Layer
  - Drive OAuth read-only
  - future Gmail read/draft/send under approval
  - future Calendar read/draft/schedule under approval
  - future APIs under operation allowlist
  - future Maps/location demo skills

Safety / Authority Layer
  - allowed action classes
  - blocked action classes
  - confirmation requirements
  - connector scope
  - memory scope
  - policy decisions
  - receipts
```

---

## 4. New Core Principle: Progressive Skill Disclosure

Robbie should not load every skill into the base prompt.

Skill loading should follow three levels:

```text
L1 — Catalog
  Name, description, package, status, risk class, required approvals.

L2 — Skill instructions
  Loaded only after the request matches the skill.

L3 — Skill resources
  Templates, scripts, checklists, playbooks, examples, provider-specific instructions.
```

This prevents:

- prompt bloat;
- conflicting skill instructions;
- higher token cost;
- unsafe authority leakage;
- accidental execution outside skill scope.

Required rule:

```text
A skill can narrow what Robbie may do.
A skill cannot expand global authority.
```

---

## 5. New Core Principle: Context-First Assistance

Before Robbie asks the user for information, it should check authorized local context.

Correct behavior:

```text
1. Check active skill scope.
2. Check approved memory / Robot Folder.
3. Check local state and open cases.
4. Check authorized documents/connectors only if allowed.
5. Ask only for the missing piece.
```

Bad behavior:

```text
Asking the user to repeat facts already approved and stored.
```

Non-negotiable boundary:

```text
Pending memory is not confirmed fact.
Document content is not memory.
Connector access is not permission to act.
```

---

## 6. New Core Principle: Cases, Not Only Tasks

Roboticxs needs a first-class concept of **cases**.

A task is a discrete action.

A case is an open matter that needs follow-up until closure.

Examples:

- claim against a provider;
- cancellation request;
- refund request;
- warranty issue;
- school/administrative issue;
- service outage;
- subscription change;
- utility/billing issue;
- appointment/trámite follow-up.

Minimum case structure:

```text
case_id
case_type
title
provider_or_counterparty
problem
objective
evidence_refs
status
priority
urgency
impact
next_action
next_follow_up_at
external_reference_id
approval_ids
created_at
updated_at
closure_reason
```

Cases should feed:

- “Qué se me pasó”;
- Robot Folder;
- scheduled attention digest;
- action packets;
- follow-up reminders.

---

## 7. New High-Value Skill: Claims & Cancellation Prep

This should become a priority paid/high-value skill.

Positioning:

> Robbie helps you organize evidence, prepare claims, cancel services, request refunds, change subscriptions, and track the case until it is closed.

Scope v0:

```text
Allowed:
- classify claim/cancellation/refund/service-change request
- gather missing facts
- identify evidence needed
- prepare message/script/checklist
- create local case after approval
- schedule local follow-up

Blocked:
- send external message
- cancel service
- accept settlement
- pay fee
- sign document
- submit legal complaint
- access account without explicit connector permission
```

Product value:

```text
This skill attacks defensive administrative friction:
companies make cancellation, refunds, claims, and corrections difficult.
Robbie turns that into a tracked case with evidence, next action, and follow-up.
```

---

## 8. Connector Governance Update

Roboticxs should adopt connector access in stages.

Near-term connector sequence:

```text
1. No connector / local state only.
2. Read-only connector by explicit user action.
3. Read-only scoped source selection.
4. Draft-only external action preparation.
5. External mutation only after explicit approval.
6. High-risk external actions require stronger admission later.
```

Google Drive v0 should be:

```text
read-only
single file or selected folder
explicit OAuth consent
no silent indexing
no direct MemoryItem creation
no external write/delete/share
read receipt required
```

Global connector rule:

```text
Connector access ≠ permission to remember.
Connector access ≠ permission to act.
Connector access ≠ permission to scan everything forever.
```

---

## 9. Memory Policy Reaffirmed

Roboticxs should not copy automatic memory activation.

Correct memory lifecycle:

```text
conversation/source observation
  → candidate extraction
  → sensitivity filter
  → ProposedMemory
  → user approval/edit/reject
  → MemoryItem ACTIVE
  → visible in Robot Folder
  → usable within declared scope
  → removable by user
```

Blocked:

```text
auto-extract conversation → active memory
auto-preload sensitive memory invisibly
memory changing action authority
memory overriding policy
```

Rule:

```text
Policy > user preference > approved memory > session context > model default.
```

---

## 10. Document Knowledge Policy

Roboticxs needs a document knowledge layer, but not immediately as heavy infrastructure.

Document rules:

```text
Document ≠ memory
Chunk ≠ fact
Embedding ≠ authorization
Retrieval ≠ permission
Citation ≠ support
Deletion must cascade to text/chunks/embeddings/references
```

Near-term document use should remain:

```text
read/review/summarize/prepare notes/propose memory
```

Not:

```text
auto-index all Drive
auto-store all content
auto-use documents across every skill
auto-create memory
```

---

## 11. Realtime / Live Companion Positioning

Realtime voice, camera, or screen share should be treated as an interaction surface.

Product name candidate:

```text
Robbie Live
Modo Acompañamiento
```

Promise:

> Share voice, screen, or camera and Robbie guides you step by step.

Boundary:

```text
Observation/guidance only in v0.
No sending, clicking, submitting, paying, scheduling, cancelling, or storing without explicit approval.
```

---

## 12. Demo / Gimmick Skills

Demo skills are useful, but should not distort the roadmap.

Good demo candidate:

```text
Antojo Cerca de Mí
```

Promise:

> Send Robbie a food photo or craving, location, and budget; Robbie suggests a small route and what to order.

Why it works:

- easy to understand;
- visual;
- low-risk if scoped;
- demonstrates multimodal + tool-grounded output;
- good for acquisition.

Rules:

```text
No reservation.
No ordering.
No payment.
No location storage by default.
No invented place IDs, addresses, prices, or availability.
```

---

## 13. Updated Product Sentence

Use this as the new strategic sentence in Roboticxs docs:

> Roboticxs gives each user one personal robot with visible memory, a progressive catalog of governed skills, context-first assistance, approval-based workflows, and follow-up tracking for the everyday administrative work people hate doing.

Sharper marketing version:

> Robbie remembers what you approve, prepares what needs doing, asks before sensitive actions, and keeps track until the issue is closed.

---

## 14. Near-Term Roadmap Impact

Before adding heavy connectors or realtime UI, prioritize:

```text
33P Command Routing Consolidation
34P ADK Agent Garden Harvest Index
35P Skill Progressive Disclosure
36P Robbie Assistance Protocol
37P Case / Follow-up Tracker
38P Claims & Cancellation Prep
```

Only after these are stable should Roboticxs advance into:

```text
Scheduled digest
Drive OAuth
Document knowledge layer
Operational workflow orchestration
Long-running approved workflows
Connector API governance
Realtime companion
Demo/gimmick skills
```
