# Google ADK Agent Garden Harvest Index v0.1

**Project:** Roboticxs / Agentius / Zaubern
**Date:** 2026-06-01
**Status:** Research artifact only
**Scope:** Pattern harvest from selected `google/adk-samples/python/agents` repositories

---

## 1. Purpose

This document captures reusable product, architecture, and governance patterns from selected Google ADK Agent Garden samples.

The goal is **not** to integrate Google Agent Garden directly into Roboticxs, Agentius, or Zaubern.

The goal is to extract patterns that can be adapted into:

1. **Roboticxs** — personal robot UX, skills, memory, workflows, connectors, and safe action boundaries.
2. **Agentius** — B2B agent/workflow implementation blueprints.
3. **Zaubern** — authority surfaces, policy gates, receipts, and evidence discipline.

Core rule:

```text
Steal workflow shape and architecture patterns.
Do not inherit authority semantics from samples.
```

---

## 2. Master Pattern Emerging from the Samples

Across the reviewed samples, the reusable pattern is:

```text
User intent
  → context/state loading
  → skill/workflow selection
  → bounded tool access
  → evidence or external-system interaction
  → approval / HITL if authority is touched
  → artifact, state update, or receipt
```

For Roboticxs, this becomes:

```text
One personal robot
  + progressive skill catalog
  + visible approved memory
  + context-first assistance protocol
  + approved workflow execution
  + case/follow-up tracking
  + connector governance
  + grounded document knowledge
  + action receipts
```

For Zaubern, the governing distinction is:

```text
retrieval ≠ evidence
citation ≠ claim support
recommendation ≠ authorization
playbook lookup ≠ legitimacy
simulated execution ≠ authority
memory ≠ permission
connector access ≠ action rights
```

---

## 3. Reviewed Samples and Reusable Patterns

| Sample | Core pattern | Roboticxs use | Agentius use | Zaubern use | Non-copy rule |
|---|---|---|---|---|---|
| `youtube-analyst` | Attention intelligence / Return on Attention | “Qué se me pasó” source digest; timestamp/evidence-linked summaries | Content intelligence agent | Evidence-linked attention summaries | Do not claim “absolute truth” from YouTube/social content. |
| `RAG` | Minimal grounded answering | Robot Folder grounded Q&A | Knowledge-grounded support bots | RAG authority surface: source, chunk, permission, version | Citation alone is not sufficient proof. |
| `deep-search` | Approved plan → iterative research → cited report | Long-running workflow pattern | Research operations agent | Plan approval, source policy, critic loop, report receipt | Do not let the agent always convert everything into a plan; classify safety/scope first. |
| `customer-service` | Context-first operational assistance | Robbie assistance protocol | Retail/support assistant blueprint | Tool-before-answer, confirmation-before-mutation | Do not copy checkout/cart/payment autonomy. |
| `memory-bank` | Cross-session memory backend | Possible memory provider adapter only | Personalization infra reference | Memory authority risk | Do not allow automatic invisible memory activation. |
| `multiformat-hybrid-rag` | Multi-format document ingestion + hybrid retrieval | Future Document Knowledge Layer | Enterprise knowledge-base MCP | Document scope, delete cascade, source receipts | Document access is not permission to remember or act. |
| `parallel_task_decomposition_execution` | Sequential prep → parallel branches → summary | Limited future workflow decomposition | Delivery factory / execution branches | Worktree isolation and integration receipts | Parallel writes require isolated workspaces and merge control. |
| `workflow-morning_email_debrief` | Scheduled read-only digest | Scheduled Attention Digest | Inbox briefing agent | Background work boundaries | Scheduled read does not authorize sends, archive, delete, or memory. |
| `incident-management` | Case/ticket creation with severity and tracking ID | Case / Follow-up Tracker | ServiceNow/Zendesk/JSM assistant | Identity-bound case creation and status tracking | Tracking must be bounded; no infinite background polling. |
| `agent-skills-tutorial` | L1/L2/L3 progressive skill disclosure | Scalable Skill Catalog | Reusable skill packs | Skill supply-chain/admission | New or external skills are proposals until reviewed. |
| `auto-insurance-agent` | API Hub / catalog APIs as tools | Future connector governance | API-to-agent enterprise integration | API operation allowlist, auth mode, receipts | API exists does not mean an agent may call it. |
| `policy-as-code` | Natural-language policy → generated code → sandbox → violations | Not near-term Roboticxs | Governance consulting pattern | Policy Candidate Compiler | Generated policy code is not authority until admitted. |
| `adk-ae-oauth` | Delegated OAuth for Drive read-only | Google Drive OAuth Connector v0 | Google Workspace connector pattern | User-bound token, scope, read receipt | Drive access does not authorize memory or indexing. |
| `cyber-guardian-agent` | Alert → triage → evidence agents → playbook → HITL → JSON log | Connector/security incident pattern | SecOps incident assistant | Incident authority workflow | Prompt discipline is not a deterministic authority gate. |
| `gemma-food-tour-guide` | Multimodal intent + Google Maps MCP | Demo skill: Antojo Cerca de Mí | Location/experience concierge demo | Tool-grounded identifiers | Do not invent place IDs, addresses, availability, or prices. |
| `hierarchical-workflow-automation` | Sequential business workflow across DB/Calendar/Gmail | Operational workflow orchestration | B2B operations automation | State transition receipts | Do not schedule/send/update without approval and receipts. |
| `realtime-conversational-agent` | Voice/video/screen-share live interface | Robbie Live Companion | Live support/assistants | Interaction surface risk | Live observation is not authority to act or store. |

---

## 4. Patterns to Adopt

### 4.1 Progressive Skill Disclosure

Derived from `agent-skills-tutorial`.

Roboticxs should not load every skill into the base prompt. It should use:

```text
L1: Skill catalog metadata
L2: Full skill instructions loaded only when matched
L3: Skill resources/templates/playbooks loaded only when needed
```

Required Roboticxs additions:

```text
skill_id
display_name
package
status
risk_class
allowed_actions
blocked_actions
required_approvals
required_connectors
memory_scope
data_scope
pricing/setup_fee
zaubern_policy_tags
```

### 4.2 Context-First Assistance Protocol

Derived from `customer-service`.

Robbie should follow this sequence:

```text
1. Identify intent.
2. Load approved context before asking the user to repeat information.
3. Match enabled skill or identify missing/paid skill.
4. Use allowed local tools/state before relying on general model knowledge.
5. Ask only for missing information.
6. Prepare recommendation, draft, checklist, or action packet.
7. Require confirmation before mutation.
8. Block prohibited actions.
9. Log proposed, approved, blocked, or completed steps.
```

### 4.3 Case / Follow-up Tracking

Derived from `incident-management`.

Roboticxs needs “cases,” not only tasks.

A case is a live matter that requires tracking until closure:

```text
case_id
external_reference_id
title
description
status
priority
urgency
impact
created_at
last_checked_at
next_action
next_follow_up_at
source/evidence references
approval_id
closure_reason
```

Initial use cases:

- claims;
- cancellations;
- service changes;
- refunds;
- guarantees;
- school/admin matters;
- utilities;
- subscription changes;
- complaint follow-up.

### 4.4 Approved Workflow Execution

Derived from `deep-search`, `hierarchical-workflow-automation`, and `cyber-guardian-agent`.

Robbie should not jump from intent to action.

Correct pattern:

```text
user request
  → plan / case summary / action packet
  → user approval
  → bounded execution or prepared artifact
  → receipt / follow-up
```

For v0, execution should remain mostly:

```text
READ
PREPARE
DRAFT
TRACK_LOCAL
```

External mutation should remain blocked or explicit-approval-only.

### 4.5 Connector Governance

Derived from `adk-ae-oauth`, `auto-insurance-agent`, and `hierarchical-workflow-automation`.

Roboticxs connector rule:

```text
Connector access is scoped by:
- user identity
- robot identity
- skill scope
- OAuth/API scope
- operation class
- approval requirement
- receipt requirement
```

Operation classes:

```text
READ
PREPARE
DRAFT
WRITE_LOCAL
SEND_EXTERNAL
WRITE_EXTERNAL_RECORD
SCHEDULE
PURCHASE
PAY
DELETE
CONFIGURE
ESCALATE
BLOCK
```

Default near-term posture:

```text
READ / PREPARE / DRAFT / WRITE_LOCAL = allowed when in scope
SEND / SCHEDULE / WRITE_EXTERNAL = approval required
PAY / PURCHASE / DELETE / CONFIGURE = blocked unless separately admitted
```

### 4.6 Document Knowledge Layer

Derived from `RAG` and `multiformat-hybrid-rag`.

Roboticxs must keep these concepts separate:

```text
Document ≠ memory
Chunk ≠ fact
Embedding ≠ authorization
Retrieval ≠ permission
Citation ≠ support
File access ≠ long-term retention
```

Document lifecycle:

```text
file received
  → metadata captured
  → sensitivity classification
  → purpose/scope check
  → optional extraction/review
  → source reference
  → possible ProposedMemory
  → user approval before MemoryItem
  → delete cascade when forgotten
```

### 4.7 Scheduled Attention

Derived from `workflow-morning_email_debrief`.

Robbie can eventually prepare scheduled attention digests, but only under strict constraints:

```text
read-only
bounded source list
bounded time window
bounded cost
no outbound action
no silent memory
last-run receipt
user can disable
```

### 4.8 Realtime / Live Companion

Derived from `realtime-conversational-agent`.

Robbie Live should be treated as an interaction surface, not as extra authority.

```text
Voice/camera/screen share = observation and guidance.
Not permission to store, send, click, pay, schedule, or submit.
```

---

## 5. What Not to Copy from Google Samples

1. Auto-memory activation without user approval.
2. Silent preload of personal/sensitive memory into prompts without visibility.
3. Checkout, payment, scheduling, sending, or external mutation without explicit confirmation.
4. Prompt-only safety as the authority boundary.
5. `include_thoughts` or hidden reasoning as evidence.
6. Generated policy code as runtime authority.
7. Dummy fallback presented as real execution.
8. Broad OAuth scopes when read-only is enough.
9. Tool access not bound to skill scope.
10. External/community skills without review.
11. Agent-created new skills becoming active without admission.
12. Playbook retrieval treated as authorization.
13. Threat-intel/retrieval results collapsed into binary truth.
14. Background work with no stop condition.
15. Live screen/camera observation stored as memory by default.

---

## 6. Immediate Product Decisions

1. **Keep Roboticxs as one robot with many skills.**
2. **Move from “skills” to “governed workflows.”**
3. **Implement progressive skill disclosure before adding many more flows.**
4. **Make Assistance Protocol a core runtime concept.**
5. **Prioritize Case / Follow-up Tracker before heavy external connectors.**
6. **Prioritize Claims & Cancellation Prep as a high-value paid skill.**
7. **Treat Drive OAuth as connector foundation, not full memory/document system.**
8. **Treat Memory Bank as backend pattern only; preserve visible approved memory policy.**
9. **Treat realtime voice/screen share as UI layer, not authority layer.**
10. **Use demo/gimmick skills only after policy and routing are stable.**

---

## 7. Recommended Next Documents

1. `docs/ROBOTICXS_PROJECT_BRIEF_ADK_PATTERN_ADDENDUM_v0_1.md`
2. `docs/ROBOTICXS_ROADMAP_PIVOT_STAGE_33P_46P_ADK_HARVEST_v0_1.md`
3. `docs/specs/ROBOTICXS_SKILL_PROGRESSIVE_DISCLOSURE_v0_1.md`
4. `docs/specs/ROBBIE_ASSISTANCE_PROTOCOL_v0_1.md`
5. `docs/specs/CASE_FOLLOWUP_TRACKER_v0_1.md`
6. `docs/specs/CLAIMS_CANCELLATION_PREP_v0_1.md`

---

## 8. Source References

Primary source family:

- `https://github.com/google/adk-samples/tree/main/python/agents`

Reviewed sample paths:

- `python/agents/youtube-analyst`
- `python/agents/RAG`
- `python/agents/deep-search`
- `python/agents/customer-service`
- `python/agents/memory-bank`
- `python/agents/multiformat-hybrid-rag`
- `python/agents/parallel_task_decomposition_execution`
- `python/agents/workflow-morning_email_debrief`
- `python/agents/incident-management`
- `python/agents/agent-skills-tutorial`
- `python/agents/auto-insurance-agent`
- `python/agents/policy-as-code`
- `python/agents/adk-ae-oauth`
- `python/agents/cyber-guardian-agent`
- `python/agents/gemma-food-tour-guide`
- `python/agents/hierarchical-workflow-automation`
- `python/agents/realtime-conversational-agent`
