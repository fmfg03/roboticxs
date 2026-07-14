# ROBOTICXS — ChatGPT Project Starter

> **Project:** Roboticxs.com
> **Status:** Product planning / MVP definition
> **Purpose:** Use this document as the starting context for a separate ChatGPT Project dedicated only to Roboticxs.
> **Strategic parent:** Agentius
> **Future upgrade path:** Agentius governed workflows → Zaubern authority layer
> **Runtime base:** Hermes Agent as runtime substrate, not consumer-facing product
> **Primary market:** B2C / prosumer / small business
> **Product category:** Personal AI robots with memory, skills, model routing, and safety boundaries

---

## 1. Core Decision

Roboticxs.com is the mass-market B2C entry product in the Agentius / Zaubern ecosystem.

Roboticxs is **not** Agentius.

Roboticxs is **not** Zaubern.

Roboticxs is the low-friction consumer/prosumer front door: a personal AI robot that helps users work better every day, reduces fear of AI through daily use, and eventually exposes business processes worth automating through Agentius.

Strategic chain:

```text
Roboticxs
Personal AI robot / daily AI adoption
        ↓
Agentius
Business workflow automation / governed agentic operations
        ↓
Zaubern
Execution authority / governance for high-consequence workflows
```

Roboticxs should feel simple, useful, personal, and safe.

Agentius should feel operational and B2B.

Zaubern should remain the deeper authority infrastructure layer.

Hermes should be treated as operational runtime substrate, not as the Roboticxs product, consumer UX, safety layer, memory approval layer, or final authority boundary.

---

## 2. Product Thesis

Most users do not need another general chatbot.

They need a personal robot that:

- remembers their work context,
- reads authorized sources for context,
- detects opportunities,
- activates skills when needed,
- picks the cheapest adequate LLM for each task,
- routes by policy first and model second,
- tracks token usage and cost,
- respects explicit boundaries,
- asks before doing sensitive things,
- blocks prohibited actions by default.

The product promise:

> **One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.**

The core contrast:

> ChatGPT answers. Roboticxs remembers, routes, and works with you every day.

Roboticxs should not be framed as a vault, PKM tool, graph UI, or autonomous agent UX. It should be framed as a simple approved-memory robot that turns authorized context into useful attention and prepared actions.

---

## 3. Product Positioning

Important translation rule:

- Do not position Roboticxs as an open-ended autonomous agent.
- Position it as a bounded robot that prepares, organizes, reminds, and asks before acting.

### Spanish

**Robots personales de IA para trabajar mejor.**

Subheadline:

> Elige tu robot, aprueba lo que recuerda y empieza con ayuda útil desde tu estado local hoy.

Sharper version:

> Tu robot personal recuerda tu contexto, revisa lo que tú autorizas y te propone acciones útiles antes de que se te pase algo importante.

### English

**Personal AI robots that remember how you work.**

Subheadline:

> Approve what your robot remembers, start from local state today, and expand its tools only when those capabilities are implemented.

---

## 4. One Robot, Many Skills

Do **not** package Roboticxs as many separate robots.

The user should feel they have **one personal robot** with:

- a name,
- a personality,
- memory,
- working context,
- recurring tasks,
- skill packages,
- model routing,
- token budget,
- action limits,
- safety checks.

Skills are like cable-TV channels. The user has one robot; the subscription determines which skill channels are active.

```text
One Robot Core
  + Memory Center
  + Context Scan
  + Skill Registry
  + Proactive Trigger Engine
  + Model Router
  + Token Counter
  + Lightweight Zaubern Safety Layer
```

---

## 5. Skill Package Model

### Basic Package

For daily personal productivity.

Includes:

- Memory Center,
- Context Scan,
- local-state meeting prep,
- local-state attention summary,
- task reminders,
- basic document review from user-supplied text,
- local-state daily attention brief,
- simple drafting.

### Pro Package

For users who want a real work operator.

Includes Basic plus:

- deeper document review planning,
- sales follow-up,
- marketing drafts,
- recurring reports,
- deeper memory,
- future connector options,
- stronger routing policy options,
- higher token/budget limits.

### Specialty Packages

Sold as add-ons.

| Package | Skills |
|---|---|
| Marketing Pack | Content calendar, posts, newsletter, competitor research, campaign briefs |
| Sales Pack | Prospect research, CRM summaries, follow-up drafts, pipeline reminders |
| Finance/Admin Pack | Invoices, payment prep, accounts receivable reminders, expense summaries |
| HR Pack | Candidate summaries, interview prep, internal policy Q&A, onboarding checklists |
| Documents Pack | Document review planning, form-draft preparation, annotation, meeting-ready summaries from approved text |

### All-Inclusive Package

Includes all skill packages, higher budgets, priority model routing, and advanced memory.

Important:

> All-inclusive does **not** mean unlimited authority.

Even with all skills enabled, the robot remains bound by action limits, confirmation rules, budget policies, and blocked-action policies.

---

## 6. Skill Scope Guard

Every skill package must define scope.

The robot must not answer out-of-scope questions as if it were a general chatbot when operating inside a role skill.

Example anti-pattern:

User asks a Customer Support robot:

> “What is JSON?”

Bad answer:

> “Excellent question. JSON is a data format...”

Correct answer:

> “I’m currently operating in Customer Support mode. I can help with tickets, customer context, response drafts, escalations, refunds within policy, and support documentation. For general technical explanations, switch to General Assistant mode or enable the Technical Help skill.”

Scope guard decisions:

- `ANSWER`: request is inside skill scope.
- `CLARIFY`: request may relate to scope but needs context.
- `REDIRECT`: request belongs to another enabled skill.
- `OFFER_UPGRADE`: request belongs to a disabled paid skill.
- `REFUSE_SCOPE`: request is outside available robot capabilities.
- `BLOCK`: request asks for a prohibited action.

Each skill must declare:

- allowed topics,
- allowed action classes,
- blocked topics,
- blocked action classes,
- escalation triggers,
- upgrade paths,
- safe fallback response.

---

## 7. Skill Manifest

Every skill package should ship with a machine-readable manifest.

Minimum structure:

```json
{
  "skill_id": "customer_support",
  "display_name": "Customer Support",
  "package": "pro",
  "allowed_topics": ["tickets", "customer history", "support policy", "response drafts"],
  "blocked_topics": ["general programming tutorial", "legal advice", "medical advice"],
  "allowed_action_classes": ["READ", "ROUTE", "DRAFT_NOTIFY"],
  "confirmation_required": ["SEND_NOTIFY", "WRITE_EXTERNAL_RECORD"],
  "blocked_action_classes": ["PAY", "DELETE", "CONFIGURE", "RELEASE"],
  "safe_fallback": "I can help with customer-support tasks. For this request, switch skills or enable the required package."
}
```

---

## 8. Context Scan

Context Scan is the onboarding mechanism that makes the robot useful quickly.

With explicit user authorization, future versions of the robot may inspect approved sources such as:

- email,
- calendar,
- selected messages,
- selected documents,
- selected social/business channels,
- CRM or task system where configured.

Today, the committed runtime should be described as local-state-first. It can use persisted local records, approved memory, document-review records, file metadata, and local control surfaces. It must not imply live connector access unless that capability is explicitly implemented and authorized.

Robbie only uses authorized sources. When connectors are not active, Robbie must say it is using local state only and must not imply it checked email, WhatsApp, calendar, web, files, or external systems live.

The robot should not store raw data by default.

It should extract proposed memories and ask the user to approve them.

Correct flow:

```text
Authorized source
  → temporary scan
  → extracted context
  → proposed memories
  → user approval / edit / delete
  → Robot Memory Profile
```

User-facing promise:

> You approve what your robot remembers.

Spanish:

> Tú apruebas lo que tu robot recuerda.

---

## 9. Memory Layer

Memory is the product center.

Roboticxs should not behave like a generic chatbot. It should maintain a structured, editable profile for each user and robot.

The robot may detect possible memories, but the user approves what becomes durable memory.

### Memory Types

#### User Profile Memory

- name,
- role,
- company,
- language,
- timezone,
- working hours,
- communication style,
- preferred output formats.

#### Work Preference Memory

- preferred email tone,
- report structure,
- meeting brief format,
- follow-up style,
- content style,
- things the user dislikes repeating.

#### Business Context Memory

- products/services,
- target customers,
- pricing notes,
- common objections,
- key contacts,
- FAQs,
- simple policies,
- recurring business goals.

#### Task Memory

- recurring tasks,
- pending follow-ups,
- open commitments,
- decisions made,
- upcoming deadlines,
- task status.

#### Boundary Memory

- actions the robot can perform,
- actions that require confirmation,
- actions that are blocked,
- sensitive topics,
- sensitive contacts,
- data the robot should not use.

---

## 10. Memory Center UX

Create a visible **Memory Center**.

This should remain a simple user-facing surface, not a vault, markdown graph, backlink system, or user-managed PKM workflow.

Sections:

- Who you are
- How you work
- Your business context
- People and clients
- Recurring tasks
- Robot limits
- Things to never do

Actions:

- Add memory
- Edit memory
- Forget memory
- Pin as important
- Mark as outdated
- Ask before using this
- Never use this for decisions

---

## 11. Proactive Trigger Engine

The robot should not only wait for commands.

It should detect useful opportunities from authorized context as those sources are implemented over time. Today, the first shipped attention loop is local-state-only.

Examples:

- upcoming meeting record + approved notes + pending NDA review,
- local lead follow-up reminder with no next step scheduled,
- local invoice reminder + due date approaching,
- customer complaint + prior refund policy,
- proposal sent + no response after 5 days,
- local calendar/task record tomorrow + missing briefing,
- document metadata received + likely needs review before meeting.

Example UX:

> “Francisco, tomorrow you have a meeting with Victor at 11:00. I saw he sent an NDA. Do you want me to review it, give you comments, and prepare a version for signature if you approve it?”

That example is future-facing product behavior. Current runtime truth is narrower: local-state summaries, text-simulated document review, and approval-gated preparation without live connector checks or file-content parsing.

Important: the robot should propose, not execute sensitive actions silently.

Scheduled or background work should remain bounded, auditable, and approval-based at sensitive boundaries. Roboticxs should not use open-ended autonomy language for consumer-facing behavior.

Stage 27P should be understood as the first local-state-only attention loop. It summarizes what may need attention using only persisted local state and must not imply live email, WhatsApp, calendar, web, or connector monitoring.

---

## 12. Telegram Only for MVP

Use Telegram as the primary interaction channel for MVP.

Do not launch WhatsApp initially.

Reason:

- Telegram bot setup is simpler.
- It is more stable for automation.
- It avoids WhatsApp Business Platform friction.
- It avoids risk from unofficial WhatsApp Web/Baileys-style bridges.
- It is good enough for early adopters and prosumer workflows.

Future WhatsApp support can be evaluated after traction, preferably through official WhatsApp Business Platform.

---

## 13. Documents / PDF Skill

The Documents Pack is one of the strongest initial premium packs.

Capabilities:

- receive file metadata through Telegram today, with richer document flows planned later,
- summarize user-supplied text today, with PDF-content review planned for a future approved stage,
- highlight important sections from approved text,
- annotate risks in user-supplied text,
- prepare simple form drafts in planning scope,
- prepare document review notes,
- prepare meeting briefings from approved text or persisted local context,
- place visual signature/initials only after confirmation.

Important boundary:

A visual signature is not a certified digital signature unless a formal signing integration exists.

Never claim:

- “legal signature”,
- “certified signature”,
- “legal advice”,
- “lawyer replacement”.

Correct positioning:

> Roboticxs can help you review, summarize, mark, and prepare documents. It does not replace legal, tax, financial, or professional advice.

Current runtime note:

> Today, Roboticxs supports text-simulated document review and file metadata handling. It does not yet parse PDFs, OCR files, or review attachment bytes directly.

---

## 14. Lightweight Zaubern Safety Layer

Roboticxs should include a very small Zaubern-backed safety layer from the beginning.

Do not expose full Zaubern, SAL, SLM, DSSE, or enterprise conformity language to consumers.

Goal:

> Prevent the robot from doing prohibited actions.

The lightweight layer checks proposed actions before execution.

Decision types:

- `ALLOW`
- `DRAFT_ONLY`
- `ASK_CONFIRMATION`
- `ESCALATE`
- `BLOCK`

### Default Policy

Allowed by default:

- summarize,
- organize,
- classify,
- draft,
- remind,
- research,
- suggest,
- prepare,
- search approved context.

Ask confirmation by default:

- send external message,
- update external record,
- schedule with third party,
- publish content,
- modify CRM field,
- create customer-facing document,
- submit forms,
- download documents from external systems.

Blocked by default:

- payment execution,
- refund execution,
- account deletion,
- credential or permission change,
- vendor bank change,
- legal acceptance,
- tax, financial, legal, medical, or employment decision,
- production deployment,
- destructive action,
- contract approval.

### UX Language

Use simple user-facing language:

- “I can draft this, but I need your confirmation before sending.”
- “I cannot execute payments. I can prepare a payment checklist.”
- “This changes an external record. Please confirm before I continue.”
- “This action is blocked by your robot limits.”

Avoid consumer-facing terms:

- SAL,
- deterministic authority,
- conformity,
- DSSE,
- cryptographic governance,
- execution substrate.

---

## 15. Model Stack and Routing

Roboticxs should not use the most expensive LLM for every task.

The platform needs a routing layer that selects the cheapest adequate model path that can safely complete the task at the required quality level.

Core routing rule:

> Route by policy first, model second.

The model does not decide whether it has authority to pay, publish, send, delete, accept legal terms, change credentials, or modify external systems. Those are policy decisions.

Low-latency principle:

> Acknowledge quickly, route cheaply, stream when useful, and move long work to bounded background execution.

Target provider strategy should eventually include:

- OpenAI,
- Anthropic,
- Google,
- OpenRouter,
- Nous Portal,
- NVIDIA NIM,
- local/open-source endpoints where feasible.

In the committed runtime today, routing and cost behavior should be described as local scaffolding and policy logic, not as a broad live multi-provider execution surface.

Provider support should be abstracted behind a common interface as the runtime expands.

### Task Classes

| Task Class | Examples | Preferred Model Type |
|---|---|---|
| SIMPLE_CLASSIFICATION | tag, route, label, priority | cheapest reliable small model |
| EXTRACTION | pull fields, summarize structured docs | low/mid-cost model |
| DRAFTING | emails, posts, replies | mid-cost model |
| RESEARCH | multi-source synthesis | mid/high model depending on depth |
| REASONING | planning, tradeoffs, complex analysis | higher model |
| TOOL_PLANNING | multi-step tool use | reliable agent-capable model |
| SENSITIVE_REVIEW | legal/finance/admin sensitive review | higher model + disclaimer + escalation |
| LONG_CONTEXT | large docs/history | long-context cost-optimized model |
| CREATIVE | content ideas, brand language | model selected by style quality |

### Routing Modes

- Economy Mode
- Balanced Mode
- Premium Mode
- BYOK Mode

Realtime and background work should be treated as distinct execution lanes. Long-running document or web-admin preparation belongs in bounded async/background execution with user-visible progress and approval gates where sensitive actions would begin.

---

## 16. Token Counter and Cost Governor

Token and cost visibility is required from day one.

Track per request:

- user ID,
- robot ID,
- task ID,
- provider,
- model,
- input tokens,
- cached input tokens where available,
- output tokens,
- tool-call count,
- retry count,
- estimated cost,
- final cost if provider returns usage,
- latency,
- status,
- failure reason if any.

Track per period:

- daily tokens,
- monthly tokens,
- cost by robot,
- cost by task class,
- cost by provider,
- cost by model,
- cost by workflow,
- cost per successful task,
- waste from retries/failures.

User-facing cost UX:

- Tokens used this month
- Estimated cost this month
- Cost by robot
- Most expensive tasks
- Model savings from routing
- Budget remaining

Example robot message:

> “I can do this in Economy Mode for about $0.02 or Premium Mode for about $0.15.”

Another:

> “This task may use a long context window. Estimated cost: $0.45. Continue?”

Budget is also an authority surface.

A robot should not get unlimited model-spend authority just because it can call an LLM.

---

## 17. Plans and Pricing

### Free Trial

- 7 days
- 1 robot
- limited memory
- limited usage
- no sensitive connectors in the initial planned offer
- model routing visibility enabled
- token dashboard visible

### Starter

Target: USD 19–29/month

Includes:

- 1 robot,
- memory profile,
- Telegram first, with web expansion planned,
- general tasks,
- Basic Package,
- planned connector options once implemented,
- token counter,
- economy/balanced routing,
- BYOK option.

### Pro

Target: USD 49–79/month

Includes:

- one robot,
- Pro Package,
- more memory,
- recurring tasks,
- additional planned connector options once implemented,
- weekly reports,
- model routing modes,
- budget controls,
- task templates.

### Specialty Packs

Target: USD 9–29/month per package

Examples:

- Marketing Pack
- Sales Pack
- Documents Pack
- Finance/Admin Pack
- HR Pack

### All-Inclusive

Target: USD 99–149/month

Includes:

- all skill packages,
- higher token/budget limits,
- advanced memory,
- priority routing,
- future connector expansion where implemented,
- premium support tier.

### Optional Done-for-You Setup

Target: USD 99–299 one-time.

Includes:

- robot setup,
- memory interview,
- future connector setup where implemented,
- initial task setup,
- usage tutorial.

---

## 18. Upgrade Path to Agentius

Roboticxs should detect when a user is ready for deeper automation.

Upgrade signals:

- user repeats the same task frequently,
- user asks the robot to update systems,
- user wants team access,
- user asks for CRM/ticket/process automation,
- user requests approval flows,
- task touches customers, money, legal, identity, or operations,
- user hits complexity or budget limits.

Upgrade message:

> “This looks like a business workflow, not just a personal robot task. Agentius can turn it into a governed workflow.”

Agentius offers:

- Authority Surface Assessment,
- Governed Workflow Pilot,
- Managed Agentic Operations.

---

## 19. MVP Build List

### Core

- Hermes deployment template
- robot provisioning
- user accounts
- Memory Center
- Context Scan
- Skill Registry
- Skill Manifest loader
- Scope Guard
- Proactive Trigger Engine
- model provider abstraction
- model router
- token counter
- cost dashboard
- budget governor
- future connector system
- Telegram interface
- lightweight Zaubern safety layer

### Initial Skill Packs

- Basic Package
- Pro Package
- Documents Pack
- Sales Pack
- Marketing Pack

### Admin

- user usage dashboard
- provider cost table
- model catalog
- error/retry logs
- support console
- budget override controls
- blocked-action logs

---

## 20. Technical Data Model

Minimum entities:

- User
- Workspace
- Robot
- SkillPackage
- SkillManifest
- MemoryItem
- ContextScan
- ProposedMemory
- Task
- TaskRun
- ToolConnection
- ModelProvider
- ModelCatalogEntry
- ModelRouteDecision
- TokenUsageEvent
- BudgetPolicy
- BudgetAlert
- ActionBoundary
- SafetyDecision
- UpgradeSignal

---

## 21. Success Metrics

### Product Metrics

- activation rate,
- first useful task completed,
- day-7 retention,
- day-30 retention,
- memory profile completion,
- context scan completion,
- recurring task creation,
- future connector activation after implementation,
- tasks per active user,
- proactive suggestions accepted,
- user-reported usefulness.

### Cost Metrics

- average cost per task,
- cost per active user,
- cost per robot,
- margin by plan,
- premium model usage rate,
- routing savings,
- retry waste,
- support cost per user.

### Funnel Metrics

- Free → Starter conversion,
- Starter → Pro conversion,
- Pro → All-Inclusive conversion,
- Specialty Pack attachment rate,
- Roboticxs → Agentius Assessment conversion,
- Agentius Assessment → Governed Workflow Pilot conversion.

---

## 22. Launch Page Copy

### Hero

> **Tu robot personal de IA para trabajar mejor.**

### Subheadline

> Autoriza lo que Robbie puede usar, aprueba lo que recuerda y deja que te señale qué necesita atención antes de que se te pase algo.

### CTA

> Crear mi robot

### Secondary CTA

> Ver habilidades

### Trust Line

> Tú apruebas qué recuerda. Tú decides qué puede hacer. Las acciones sensibles requieren confirmación.

### Skill Section

> Un robot. Muchas habilidades.

Cards:

- Reuniones
- Documentos / PDFs
- Ventas
- Marketing
- Administración
- Small Business

---

## 23. Strategic Rule

Do not compete with ChatGPT or Claude on intelligence.

Compete on:

- context acquisition,
- memory structure,
- skill packaging,
- proactive triggers,
- cost routing,
- token visibility,
- action safety,
- daily habit.

Final product statement:

> Roboticxs turns AI from a blank chatbox into a personal robot with memory, skills, cost control, and boundaries.

---

## 24. Immediate Next Steps

1. Create Roboticxs repo/project.
2. Add this document as `docs/ROBOTICXS_PROJECT_BRIEF.md`.
3. Create `PRODUCT_SPEC_v0_1.md`.
4. Create `SKILL_MANIFEST_SCHEMA_v0_1.json`.
5. Create `SAFETY_LAYER_SPEC_v0_1.md`.
6. Create `MODEL_ROUTER_SPEC_v0_1.md`.
7. Create `TOKEN_COUNTER_SPEC_v0_1.md`.
8. Create landing page copy.
9. Create Hermes MVP technical plan.
10. Add planning addendum: `ROBOTICXS_BRIEF_ADDITIONS_HERMES_ROUTING_WEB_TASK_v0_1.md`.
11. Create planned future specs:
   - `HERMES_ADAPTER_SPEC_v0_1.md`
   - `LATENCY_ROUTING_SPEC_v0_1.md`
   - `WEB_TASK_WORKER_SPEC_v0_1.md`
12. Add planning addendum: `ROBOTICXS_BRIEF_ADDITIONS_KNOWLEDGE_LOOP_POLICY_v0_1.md`.
13. Add planned future docs/specs:
   - `ROBOT_FOLDER_SPEC_v0_1.md`
   - `APPROVED_MEMORY_POLICY_SPEC_v0_1.md`
   - `ACTION_BOUNDARY_POLICY_SPEC_v0_1.md`
   - `BACKGROUND_WORK_POLICY_SPEC_v0_1.md`
   - `SOURCE_POLICY_SPEC_v0_1.md`
14. Define first demo: Telegram + Memory Approval + Document Review + Meeting Briefing + Low-Latency Model Routing.
15. Define second demo candidate: Telegram + Web Task Worker + Appointment Search + Human Confirmation.
