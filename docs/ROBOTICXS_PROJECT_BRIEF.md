# ROBOTICXS — ChatGPT Project Starter

> **Project:** Roboticxs.com  
> **Status:** Product planning / MVP definition  
> **Purpose:** Use this document as the starting context for a separate ChatGPT Project dedicated only to Roboticxs.  
> **Strategic parent:** Agentius  
> **Future upgrade path:** Agentius governed workflows → Zaubern authority layer  
> **Runtime base:** Hermes Agent  
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

---

## 2. Product Thesis

Most users do not need another general chatbot.

They need a personal robot that:

- remembers their work context,
- reads authorized sources for context,
- detects opportunities,
- activates skills when needed,
- picks the cheapest adequate LLM for each task,
- tracks token usage and cost,
- respects explicit boundaries,
- asks before doing sensitive things,
- blocks prohibited actions by default.

The product promise:

> **One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.**

The core contrast:

> ChatGPT answers. Roboticxs remembers, routes, and works with you every day.

---

## 3. Product Positioning

### Spanish

**Robots personales de IA para trabajar mejor.**

Subheadline:

> Elige tu robot, conecta tus herramientas y empieza a usar IA todos los días.

Sharper version:

> Tu robot personal recuerda tu contexto, revisa lo que tú autorizas y te propone acciones útiles antes de que se te pase algo importante.

### English

**Personal AI robots that remember how you work.**

Subheadline:

> Connect your tools, approve what your robot remembers, and let it help you every day.

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
- calendar / meeting prep,
- inbox summary,
- task reminders,
- basic document summary,
- daily brief,
- simple drafting.

### Pro Package

For users who want a real work operator.

Includes Basic plus:

- PDF/document review,
- sales follow-up,
- marketing drafts,
- recurring reports,
- deeper memory,
- more connectors,
- stronger model routing options,
- higher token/budget limits.

### Specialty Packages

Sold as add-ons.

| Package | Skills |
|---|---|
| Marketing Pack | Content calendar, posts, newsletter, competitor research, campaign briefs |
| Sales Pack | Prospect research, CRM summaries, follow-up drafts, pipeline reminders |
| Finance/Admin Pack | Invoices, payment prep, accounts receivable reminders, expense summaries |
| HR Pack | Candidate summaries, interview prep, internal policy Q&A, onboarding checklists |
| Documents Pack | PDF review, form filling, annotation, meeting-ready document summaries |

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

With explicit user authorization, the robot can inspect approved sources such as:

- email,
- calendar,
- selected messages,
- selected documents,
- selected social/business channels,
- CRM or task system where configured.

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

It should detect useful opportunities from authorized context.

Examples:

- upcoming meeting + related email + attached NDA,
- lead wrote back + no follow-up scheduled,
- invoice received + due date approaching,
- customer complaint + prior refund policy,
- proposal sent + no response after 5 days,
- calendar event tomorrow + missing briefing,
- PDF received + likely needs review before meeting.

Example UX:

> “Francisco, tomorrow you have a meeting with Victor at 11:00. I saw he sent an NDA. Do you want me to review it, give you comments, and prepare a version for signature if you approve it?”

Important: the robot should propose, not execute sensitive actions silently.

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

- receive PDFs through Telegram or web,
- summarize PDFs,
- highlight important sections,
- annotate risks,
- fill simple forms,
- prepare document review notes,
- prepare meeting briefings from document context,
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
- create customer-facing document.

Blocked by default:

- payment execution,
- refund execution,
- account deletion,
- credential or permission change,
- vendor bank change,
- legal acceptance,
- tax, financial, legal, medical, or employment decision,
- production deployment,
- destructive action.

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

The platform needs a model router that selects the cheapest model that can safely complete the task at the required quality level.

Supported providers should include:

- OpenAI,
- Anthropic,
- Google,
- OpenRouter,
- Nous Portal,
- NVIDIA NIM,
- local/open-source endpoints where feasible.

Provider support should be abstracted behind a common interface.

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
- no sensitive connectors
- model routing enabled
- token dashboard visible

### Starter

Target: USD 19–29/month

Includes:

- 1 robot,
- memory profile,
- Telegram/web,
- general tasks,
- Basic Package,
- 1–2 connectors,
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
- more connectors,
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
- more connectors,
- premium support tier.

### Optional Done-for-You Setup

Target: USD 99–299 one-time.

Includes:

- robot setup,
- memory interview,
- connector setup,
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
- basic connector system
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
- connector activation,
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

> Conecta tu correo, calendario y documentos. Roboticxs aprende tu contexto con tu permiso, recuerda lo importante y te propone qué hacer antes de que se te pase algo.

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
10. Define first demo: Telegram + Context Scan + Document Review + Meeting Briefing.
