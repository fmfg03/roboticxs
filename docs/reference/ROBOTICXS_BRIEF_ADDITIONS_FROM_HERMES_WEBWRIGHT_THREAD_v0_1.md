> Reference note preserved from prior Roboticxs planning work. Not runtime behavior.

# ROBOTICXS — Brief Additions from Hermes / LLM Routing / Webwright Thread v0.1

> **Project:** Roboticxs.com  
> **Document type:** Addendum to `ROBOTICXS_PROJECT_BRIEF.md`  
> **Status:** Product / architecture planning  
> **Date:** 2026-06-01  
> **Purpose:** Capture the decisions and additions derived from the Hermes, LLM stack, low-latency routing, and Webwright discussion.  
> **Use:** Append or merge into the main Roboticxs project brief before creating the product spec and MVP technical plan.

---

## 1. Core Update

Roboticxs should use Hermes as an operational runtime base, not as the product itself.

Correct framing:

```text
Hermes = runtime engine
Roboticxs = product, packaging, safety, billing, memory UX, skills, approvals, and consumer experience
```

Roboticxs should not expose Hermes, MCP, Playwright, terminal execution, model routing, or infrastructure concepts to normal users.

User-facing product promise remains:

> One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.

Internal architecture promise:

> Roboticxs domesticates agentic infrastructure for non-technical users through memory approval, skill scope, cost routing, action boundaries, and low-friction daily workflows.

---

## 2. Hermes Positioning

Hermes should be treated as a **runtime substrate** for:

- persistent agent operation,
- skills,
- scheduled tasks,
- messaging gateway,
- model/provider delegation,
- MCP/tool integrations,
- memory-enabled workflows,
- repeatable personal-agent operations.

Hermes should **not** be treated as:

- the Roboticxs product,
- the consumer UX,
- the safety layer,
- the billing layer,
- the memory approval layer,
- the authority boundary,
- the final orchestration policy.

Roboticxs should own the control plane above Hermes.

```text
Roboticxs App / Telegram / Web
        ↓
Roboticxs Control Plane
- user account
- robot profile
- skill subscriptions
- memory approval
- scope guard
- safety layer
- token budget
- model routing policy
- upgrade signals
        ↓
Hermes Runtime Adapter
- Hermes process / CLI / gateway
- skills
- scheduler
- tool connections
- model calls
- runtime logs
        ↓
Per-Robot Isolated Workspace
- memory store
- approved files
- outputs
- credentials vault
- logs
- receipts
```

---

## 3. Hermes Guide Caveat

The CyrilXBT Hermes masterclass is useful as a conceptual guide, but should not be copied literally into the implementation plan.

Implementation must be verified against the current official Hermes repository and documentation before coding.

Current reference targets to verify during technical planning:

- `NousResearch/hermes-agent`
- Hermes Agent official documentation
- Hermes CLI install flow
- Hermes provider configuration
- Hermes Telegram gateway
- Hermes scheduler
- Hermes MCP/tool support

Important caution:

> Do not assume the pasted guide’s repository path, installation commands, provider names, or configuration files are current. Treat them as orientation, not source of truth.

---

## 4. Required New Spec: Hermes Adapter

Add this document to the immediate build list:

```text
docs/HERMES_ADAPTER_SPEC_v0_1.md
```

Minimum contents:

1. Hermes installation and provisioning method.
2. One Hermes runtime per user/robot or shared runtime with strict isolation.
3. How Roboticxs creates, updates, and disables Hermes skills.
4. How Hermes skills map to Roboticxs skill packages.
5. How Roboticxs injects robot profile and approved memory into Hermes.
6. How Roboticxs prevents Hermes from storing raw data by default.
7. How scheduled Hermes jobs are created and audited.
8. How Telegram messages enter Roboticxs before reaching Hermes.
9. How tool calls are intercepted by the Safety Layer.
10. How token usage and cost are captured per task.
11. How outputs are saved, versioned, and surfaced to the user.
12. How errors, retries, model failures, and blocked actions are logged.
13. How credentials are isolated from prompts and skill files.
14. What Hermes features are disabled by default.
15. What requires human approval before execution.

---

## 5. Autonomy Translation Rule

Hermes-style language such as “runs without you” should not be used directly in Roboticxs consumer positioning.

Roboticxs translation:

```text
Bad:
Runs autonomously without you.

Correct:
Works on schedule, prepares useful actions, and asks before doing anything sensitive.
```

Roboticxs should allow background operation, but not open-ended autonomy.

Allowed:

- scheduled briefs,
- reminders,
- document preparation,
- source monitoring,
- recurring admin preparation,
- draft generation,
- cart preparation,
- appointment search,
- receipt download with permission.

Not allowed silently:

- payment execution,
- legal acceptance,
- account deletion,
- credential change,
- publication,
- customer-facing send,
- CRM mutation,
- production deployment,
- medical/legal/financial decision.

---

## 6. LLM Stack Principle

Roboticxs should use a mixed LLM stack, but the product asset is not the list of models.

The asset is the routing policy.

Core rule:

> Route by policy first, model second.

The router must evaluate:

- task class,
- risk level,
- user plan,
- skill scope,
- budget remaining,
- latency target,
- context size,
- file type,
- required quality,
- action class,
- provider health,
- data sensitivity,
- reviewer requirement.

The model must not decide whether it has authority to pay, publish, send, delete, sign, accept terms, change credentials, or modify external systems.

Those are policy decisions.

---

## 7. Roboticxs Model Stack v0.1

The coding-oriented stack shown in the reference image should be adapted to Roboticxs task classes.

Recommended v0.1 lanes:

| Lane | Approx. usage | Purpose | Model class |
|---|---:|---|---|
| Router lane | 20–30% | intent, skill, risk, language, urgency, upgrade detection | tiny/cheap/fast model or deterministic rules |
| Economy worker | 30–40% | short summaries, simple extraction, classification, basic replies | low-cost general model |
| Document worker | 15–25% | PDFs, long emails, attachments, meeting briefs, form interpretation | long-context / multimodal model |
| Writer lane | 10–15% | emails, posts, human-sounding replies, tone adjustment | strong writing model |
| Reasoning lane | 5–10% | planning, tradeoffs, ambiguous workflows, sensitive interpretation | higher-reasoning model |
| Safety reviewer | 3–8% | second-pass review before sensitive external action | model different from generator |
| Premium escalation | 1–3% | rare high-impact cases | best available model, gated by plan/budget |

MVP should avoid too many providers at launch. Start with a small, observable stack and expand after latency, cost, and failure data are real.

Suggested initial provider structure:

```text
Direct OpenAI
Direct Anthropic
Direct Google
OpenRouter for fallback / experimentation
Nous Portal / Hermes-native lane where useful
Optional NVIDIA NIM or local endpoints later for enterprise/privacy deployments
```

---

## 8. Model Routing Modes

Roboticxs should expose simple user-facing modes:

### Economy Mode

Use the cheapest adequate model. Good for routine tasks.

### Balanced Mode

Default mode. Optimizes for quality, speed, and cost.

### Premium Mode

Uses stronger models for sensitive, complex, or high-value tasks.

### BYOK Mode

User supplies their own API keys where supported.

Consumer-facing copy:

> “I can do this in Economy Mode for about $0.02 or Premium Mode for about $0.15.”

> “This task may use a long context window. Estimated cost: $0.45. Continue?”

---

## 9. Low-Latency Routing Requirement

Routing must stay near-instant for normal interactions.

Do not build a heavy LLM router that thinks before every request.

Correct design:

```text
User message
  ↓
Fast intent parser
  ↓
Deterministic policy router
  ↓
Only if needed:
- cheap LLM classifier
- safety reviewer
- premium escalation
  ↓
Worker model
  ↓
stream response or background task
```

Targets for MVP:

| Stage | Target |
|---|---:|
| Telegram/web acknowledgement | < 500 ms |
| Deterministic routing | < 50 ms |
| Routing with cache/embedding | < 200–300 ms |
| Routing with cheap LLM | < 800–1200 ms |
| First visible response | < 2 s |
| Simple task complete | 2–5 s |
| Medium document/PDF | 10–30 s with progress |
| Long workflow | asynchronous/background |

Latency principle:

> The robot should acknowledge immediately, route cheaply, stream when useful, and move long work to background.

---

## 10. Two Execution Lanes

Roboticxs should separate realtime interaction from background work.

### Realtime Lane

For:

- questions,
- simple summaries,
- memory lookup,
- quick drafts,
- task classification,
- scope decisions,
- confirmation flows.

Properties:

- fast,
- low-cost,
- streaming where possible,
- minimal context,
- no unnecessary retrieval.

### Background Lane

For:

- PDF review,
- browser automation,
- weekly reports,
- source monitoring,
- research,
- recurring grocery preparation,
- bill retrieval,
- long document processing,
- memory consolidation.

Properties:

- asynchronous,
- progress messages,
- resumable,
- auditable,
- output saved,
- notification when done.

Example robot response:

> “Lo preparo y te aviso aquí cuando esté listo.”

---

## 11. Routing Optimization Rules

To maintain low latency and margin:

1. Use deterministic rules before LLMs.
2. Cache routing decisions per user, skill, and recurring workflow.
3. Maintain provider health metrics and avoid slow providers for urgent tasks.
4. Use aggressive timeouts and fallbacks.
5. Stream output for drafts and analysis.
6. Avoid memory retrieval unless the task class requires it.
7. Pack only the minimum relevant context.
8. Run safety review only when the output is about to cross a boundary.
9. Use async by default for documents and browser tasks.
10. Use speculative parallel calls only for premium/high-value cases where margin allows it.

---

## 12. Webwright Addition

Add Webwright as a candidate **Browser Task Worker** for Roboticxs.

Positioning:

```text
Webwright = experimental browser automation worker
Roboticxs = user-facing product and safety control plane
```

Webwright should be used to convert repetitive browser tasks into reusable, inspectable scripts rather than disposable click-by-click sessions.

Internal framing:

> Browser tasks should become repeatable workflows, not improvisational browsing.

User-facing framing:

> “Tu robot puede ayudarte con trámites y páginas web aburridas.”

Do not expose the terms Webwright, Playwright, terminal, script, MCP, or browser agent in consumer copy.

---

## 13. Required New Spec: Web Task Worker

Add this document to the build list:

```text
docs/WEB_TASK_WORKER_SPEC_v0_1.md
```

Minimum contents:

1. Webwright sandbox setup.
2. Allowed websites/domains for MVP pilots.
3. How browser credentials are handled.
4. How generated scripts are reviewed and stored.
5. How scripts are parameterized for repeated use.
6. How screenshots, DOM snapshots, and logs are captured.
7. How failures are surfaced to the user.
8. What actions require confirmation.
9. What actions are blocked.
10. How reusable browser workflows become paid skills.
11. How each browser workflow is tested before becoming generally available.
12. How site layout changes invalidate or pause a workflow.

Status:

```text
Experimental / sandbox first / not production-critical dependency
```

---

## 14. Webwright Candidate Workflows

Initial browser workflows should focus on practical, everyday administrative pain.

Good candidates:

| Workflow | User value | Risk |
|---|---:|---:|
| Search vehicle emissions verification appointment | High | Low/medium |
| Download Telmex/CFE bill | High | Medium due to login |
| Prepare payment checklist | High | High if execution attempted |
| Prepare recurring grocery cart | Very high | Medium/high due to checkout |
| Fill simple government/admin form draft | High | Medium |
| Search appointment availability | High | Medium |
| Download invoice or receipt | High | Medium |
| Compare delivery options | Medium/high | Low |

Hard rule:

> Webwright may prepare, search, extract, fill drafts, and stage workflows. It must not execute payments, accept legal terms, change credentials, or perform destructive actions.

---

## 15. Web Task Action Classes

Add these action classes to the Lightweight Zaubern Safety Layer:

```json
{
  "READ_WEB": "ALLOW",
  "SEARCH_WEB": "ALLOW",
  "EXTRACT_WEB_DATA": "ALLOW",
  "NAVIGATE_WEB": "ALLOW",
  "FILL_FORM_DRAFT": "ASK_CONFIRMATION",
  "SUBMIT_FORM": "ASK_CONFIRMATION",
  "LOGIN_WITH_USER_APPROVAL": "ASK_CONFIRMATION",
  "DOWNLOAD_DOCUMENT": "ASK_CONFIRMATION",
  "PREPARE_CHECKOUT": "ASK_CONFIRMATION",
  "PLACE_ORDER": "BLOCK_OR_STRONG_CONFIRMATION_BY_POLICY",
  "EXECUTE_PAYMENT": "BLOCK",
  "ACCEPT_LEGAL_TERMS": "BLOCK",
  "CHANGE_PASSWORD": "BLOCK",
  "CHANGE_BANK_ACCOUNT": "BLOCK",
  "DELETE_ACCOUNT": "BLOCK",
  "GRANT_PERMISSION": "BLOCK",
  "REVOKE_PERMISSION": "BLOCK"
}
```

For MVP, `PLACE_ORDER` should be treated as blocked unless a specific workflow defines a supervised final-approval path.

---

## 16. Skill Manifest Additions

Extend the Roboticxs Skill Manifest with execution, model, and browser fields.

Suggested additions:

```json
{
  "execution_lane": "realtime | background",
  "default_model_lane": "router | economy | balanced | document | writer | reasoning | safety_reviewer | premium",
  "max_expected_latency_ms": 5000,
  "requires_memory": true,
  "requires_context_scan": false,
  "requires_browser_worker": false,
  "requires_human_confirmation": ["SEND_NOTIFY", "SUBMIT_FORM"],
  "blocked_action_classes": ["PAY", "DELETE", "ACCEPT_LEGAL_TERMS"],
  "async_allowed": true,
  "progress_updates_required": true,
  "output_storage_required": true,
  "cost_estimate_required": true
}
```

---

## 17. Memory Rules Update

Hermes-style “remember everything” is not acceptable for Roboticxs.

Roboticxs memory rule:

> The robot may detect possible memories, but the user approves what becomes durable memory.

Memory flow:

```text
Temporary context
  → proposed memory
  → user approves / edits / rejects
  → durable robot memory
```

Default policy:

- Do not store raw data by default.
- Store extracted user-approved facts, preferences, recurring tasks, and boundaries.
- Sensitive memory should be explicitly labeled.
- User can edit, forget, pin, or mark memory as outdated.
- Browser automation outputs should not become memory unless approved.

---

## 18. Demo Update

Update the first demo from:

```text
Telegram + Context Scan + Document Review + Meeting Briefing
```

to:

```text
Telegram + Memory Approval + Document Review + Meeting Briefing + Low-Latency Model Routing
```

Second demo candidate:

```text
Telegram + Web Task Worker + Appointment Search + Human Confirmation
```

Example first demo:

> “Robbie, mañana tengo reunión con Victor. Revisa este PDF, dime riesgos, prepara resumen y dime qué debo preguntar.”

Expected robot behavior:

1. Acknowledge immediately.
2. Classify as `DOCUMENT_REVIEW + MEETING_BRIEF`.
3. Estimate cost if document is large.
4. Process in background if needed.
5. Return summary, risks, questions, and next steps.
6. Propose memory items.
7. Ask approval before storing memory.
8. Take no external action without confirmation.

Example second demo:

> “Robbie, búscame cita para verificación vehicular la próxima semana.”

Expected robot behavior:

1. Ask for missing vehicle/location/date constraints.
2. Use browser worker only after permission.
3. Search availability.
4. Present options.
5. Ask before submitting any form.
6. Never pay or accept legal terms.

---

## 19. Data Model Additions

Add or confirm these entities in the technical model:

- HermesRuntime
- HermesSkillBinding
- RuntimeProvider
- ModelLane
- ModelRoutingPolicy
- ProviderHealthMetric
- LatencyBudget
- ExecutionLane
- BrowserWorkflow
- BrowserWorkflowRun
- BrowserScriptArtifact
- BrowserCredentialGrant
- BrowserActionBoundary
- HumanConfirmationRequest
- AsyncTaskProgressEvent
- WorkflowInvalidationEvent
- WebTaskReceipt

---

## 20. Metrics Additions

Add these metrics to product and operations tracking.

### Latency Metrics

- routing latency,
- first response latency,
- time to useful output,
- async completion time,
- provider latency by model,
- fallback rate,
- timeout rate.

### Routing Metrics

- task class distribution,
- model lane distribution,
- economy/balanced/premium usage,
- reviewer invocation rate,
- cross-model disagreement rate,
- routing override rate.

### Cost Metrics

- cost per task class,
- cost per skill,
- cost per browser workflow,
- cost per successful document review,
- cost per successful web task,
- retry waste,
- premium escalation cost.

### Browser Worker Metrics

- workflow success rate,
- script reuse rate,
- script invalidation rate,
- human confirmation rate,
- blocked action rate,
- average steps saved for user,
- workflow maintenance burden.

---

## 21. Updated Immediate Next Steps

Original next steps should be expanded as follows:

1. Create Roboticxs repo/project.
2. Add main brief as `docs/ROBOTICXS_PROJECT_BRIEF.md`.
3. Add this addendum as `docs/ROBOTICXS_BRIEF_ADDITIONS_HERMES_ROUTING_WEBWRIGHT_v0_1.md`.
4. Create `PRODUCT_SPEC_v0_1.md`.
5. Create `HERMES_ADAPTER_SPEC_v0_1.md`.
6. Create `SKILL_MANIFEST_SCHEMA_v0_1.json`.
7. Create `SAFETY_LAYER_SPEC_v0_1.md`.
8. Create `MODEL_ROUTER_SPEC_v0_1.md`.
9. Create `LATENCY_ROUTING_SPEC_v0_1.md`.
10. Create `TOKEN_COUNTER_SPEC_v0_1.md`.
11. Create `WEB_TASK_WORKER_SPEC_v0_1.md`.
12. Create landing page copy.
13. Create Hermes MVP technical plan.
14. Define demo 1: Telegram + Memory Approval + Document Review + Meeting Briefing.
15. Define demo 2: Telegram + Web Task Worker + Appointment Search + Human Confirmation.
16. Run Hermes sandbox verification.
17. Run Webwright sandbox verification.
18. Decide which features are allowed into MVP and which remain experimental.

---

## 22. Non-Claims

Roboticxs must not claim:

- full autonomy,
- legal/medical/financial advice,
- certified digital signature,
- payment execution,
- guaranteed browser workflow success,
- that Hermes alone provides safety,
- that model routing alone solves risk,
- that Webwright is production-proven before sandbox validation,
- that a robot can act without user-approved permissions,
- that memory stores everything automatically.

Correct claims:

- Roboticxs can help prepare tasks.
- Roboticxs asks before sensitive actions.
- Roboticxs lets users approve memory.
- Roboticxs routes tasks to cost-appropriate models.
- Roboticxs can run scheduled workflows with limits.
- Roboticxs can help with repetitive browser/admin tasks after permission.

---

## 23. Strategic Conclusion

Hermes gives Roboticxs an operational engine.

The mixed LLM stack gives Roboticxs cost and quality control.

Low-latency routing keeps Roboticxs usable as a daily assistant.

Webwright can turn painful web errands into repeatable workflows.

But the real Roboticxs product remains:

> A personal AI robot for normal users, with approved memory, packaged skills, visible cost, fast routing, useful daily workflows, and strict action boundaries.

The winning product is not “an autonomous agent.”

The winning product is:

> A robot that does the boring preparation work and stops before the dangerous part.
