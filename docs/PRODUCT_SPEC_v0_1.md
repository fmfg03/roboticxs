# ROBOTICXS — Product Spec v0.1

> **Product:** Roboticxs.com  
> **Version:** v0.1  
> **Status:** MVP product specification  
> **Parent:** Agentius  
> **Future authority path:** Zaubern-backed governed workflows  
> **Runtime base:** Hermes Agent  
> **Primary channel for MVP:** Telegram  

---

## 1. Product Definition

Roboticxs is a personal AI robot for daily work.

It is not positioned as another blank chatbot. The product gives each user one robot with memory, skills, context, model routing, cost visibility, and explicit action boundaries.

The user should feel:

> “This is my personal robot. It remembers how I work, helps me daily, and asks before doing sensitive things.”

Roboticxs must remain distinct from the other layers in the ecosystem:

```text
Roboticxs = personal AI adoption / B2C / prosumer / small business
Agentius  = business workflow automation / managed operations
Zaubern   = authority infrastructure / high-consequence execution governance
```

---

## 2. Core Promise

**One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.**

Roboticxs competes on:

- useful context acquisition,
- visible memory,
- scoped skill packages,
- proactive triggers,
- model/cost routing,
- token visibility,
- action safety,
- daily habit formation.

It does not compete with frontier chatbots on raw intelligence.

---

## 3. Target Users

### Primary

Prosumer and small-business users who already feel AI can help them but do not want to manually prompt a blank chatbot every day.

Examples:

- independent consultants,
- small agency owners,
- salespeople,
- solo professionals,
- operators with many meetings/documents,
- founders managing inbox/calendar/tasks manually.

### Secondary

Employees in SMB teams who need role-specific assistance but do not yet have formal AI workflow automation.

---

## 4. MVP Positioning

### Spanish

**Tu robot personal de IA para trabajar mejor.**

Subheadline:

> Conecta tu correo, calendario y documentos. Roboticxs aprende tu contexto con tu permiso, recuerda lo importante y te propone qué hacer antes de que se te pase algo.

Trust line:

> Tú apruebas qué recuerda. Tú decides qué puede hacer. Las acciones sensibles requieren confirmación.

### English

**Personal AI robots that remember how you work.**

Subheadline:

> Connect your tools, approve what your robot remembers, and let it help you every day.

---

## 5. Product Model

### One Robot, Many Skills

Roboticxs should not sell many disconnected robots. The user owns one robot with:

- a name,
- a personality,
- editable memory,
- working context,
- recurring tasks,
- active skill packages,
- model routing,
- token/cost budget,
- action limits,
- safety checks.

Skill packages operate like subscription channels. The robot remains the same; the active skills define what it can do.

### Skill Packages

#### Basic Package

Purpose: daily personal productivity.

Includes:

- Memory Center,
- Context Scan,
- calendar/meeting prep,
- inbox summary,
- task reminders,
- basic document summary,
- daily brief,
- simple drafting.

#### Pro Package

Purpose: real work operator.

Includes Basic plus:

- PDF/document review,
- sales follow-up,
- marketing drafts,
- recurring reports,
- deeper memory,
- more connectors,
- stronger routing options,
- higher token/budget limits.

#### Specialty Packs

- Marketing Pack
- Sales Pack
- Finance/Admin Pack
- HR Pack
- Documents Pack

#### All-Inclusive Package

Includes all skill packages and higher limits, but does not give unlimited authority. Confirmation, budget, scope, and blocked-action rules still apply.

---

## 6. MVP Feature Set

### Required for First Demo

1. Telegram bot interface.
2. User account and robot provisioning.
3. Memory Center data model.
4. Context Scan with proposed memories.
5. Document/PDF intake through Telegram.
6. Meeting briefing flow.
7. Skill manifest loader.
8. Scope Guard.
9. Lightweight safety decision layer.
10. Model router abstraction.
11. Token/cost event logging.
12. Basic admin view or logs.

### Not Required for First Demo

- WhatsApp.
- Enterprise team management.
- Full Zaubern terminology.
- Certified digital signatures.
- Production-grade legal/tax/financial advisory.
- Full CRM automation.
- Full payment/refund execution.
- Multi-tenant enterprise governance console.

---

## 7. Core User Flows

### Flow A — First Robot Setup

1. User signs up.
2. User creates or names robot.
3. User selects tone/personality.
4. User picks Basic, Pro, or trial.
5. User connects Telegram.
6. User approves initial memory questions.
7. Robot creates an initial Memory Profile.

### Flow B — Context Scan

1. User authorizes a source.
2. System scans selected content temporarily.
3. System extracts proposed memories.
4. User approves, edits, rejects, or pins memories.
5. Approved memories enter the Robot Memory Profile.
6. Raw source data is not stored by default.

### Flow C — Document Review

1. User sends a PDF/document to Telegram.
2. Robot classifies task and document type.
3. Model router selects route.
4. Token estimator warns user if cost is above threshold.
5. Robot summarizes key points.
6. Robot flags risks and open questions.
7. Robot prepares meeting notes or a review checklist.
8. Safety layer prevents legal/certified-signature claims.

### Flow D — Proactive Meeting Brief

1. Robot detects upcoming meeting.
2. Robot checks approved context.
3. Robot detects related documents/emails.
4. Robot proposes a brief.
5. User approves.
6. Robot generates agenda, key context, open questions, and prep notes.

### Flow E — Sensitive Action Boundary

1. User asks robot to send, publish, update, pay, delete, or accept something.
2. System maps the request to an action class.
3. Safety layer returns `ALLOW`, `DRAFT_ONLY`, `ASK_CONFIRMATION`, `ESCALATE`, or `BLOCK`.
4. Robot uses simple language to explain the boundary.

---

## 8. Scope Guard

Every skill has a declared scope.

Scope decisions:

- `ANSWER`
- `CLARIFY`
- `REDIRECT`
- `OFFER_UPGRADE`
- `REFUSE_SCOPE`
- `BLOCK`

The robot must not answer out-of-scope requests as if every skill were a general chatbot.

Example:

> “I’m currently operating in Sales mode. I can help with prospect research, pipeline reminders, CRM summaries, and follow-up drafts. For general programming help, switch to General Assistant mode or enable the Technical Help skill.”

---

## 9. Memory Center

Memory is the product center.

### Memory Sections

- Who you are
- How you work
- Your business context
- People and clients
- Recurring tasks
- Robot limits
- Things to never do

### Memory Actions

- Add memory
- Edit memory
- Forget memory
- Pin as important
- Mark as outdated
- Ask before using this
- Never use this for decisions

### Memory Rule

The robot may propose memories. The user approves what becomes durable memory.

---

## 10. Safety Layer UX

Consumer language must stay simple.

Allowed language:

- “I can draft this, but I need your confirmation before sending.”
- “I cannot execute payments. I can prepare a payment checklist.”
- “This changes an external record. Please confirm before I continue.”
- “This action is blocked by your robot limits.”

Avoid consumer-facing language:

- SAL
- DSSE
- deterministic authority
- conformity
- cryptographic governance
- execution substrate

---

## 11. Model Routing UX

The robot should communicate cost and quality choices when useful.

Examples:

- “I can do this in Economy Mode for about $0.02 or Premium Mode for about $0.15.”
- “This task may use a long context window. Estimated cost: $0.45. Continue?”

Routing modes:

- Economy Mode
- Balanced Mode
- Premium Mode
- BYOK Mode

---

## 12. Pricing v0.1

### Free Trial

- 7 days
- 1 robot
- limited memory
- limited usage
- no sensitive connectors
- token dashboard visible

### Starter

Target: USD 19–29/month.

Includes:

- 1 robot,
- Basic Package,
- Telegram/web,
- 1–2 connectors,
- token counter,
- economy/balanced routing,
- BYOK option.

### Pro

Target: USD 49–79/month.

Includes:

- Pro Package,
- more memory,
- recurring tasks,
- more connectors,
- weekly reports,
- model routing modes,
- budget controls,
- task templates.

### Specialty Packs

Target: USD 9–29/month per pack.

### All-Inclusive

Target: USD 99–149/month.

### Done-for-You Setup

Target: USD 99–299 one-time.

---

## 13. Upgrade Path to Agentius

Roboticxs should detect when the user has crossed from personal assistance into business workflow automation.

Upgrade signals:

- repeated task pattern,
- team access request,
- CRM/ticket/process automation request,
- approval flow request,
- customer-facing operation,
- money/legal/identity/operations touchpoint,
- budget or complexity ceiling hit.

Upgrade line:

> “This looks like a business workflow, not just a personal robot task. Agentius can turn it into a governed workflow.”

---

## 14. Success Metrics

### Activation

- account created,
- robot created,
- Telegram connected,
- first memory approved,
- first useful task completed.

### Retention

- day-7 retention,
- day-30 retention,
- tasks per active user,
- recurring task creation,
- proactive suggestion acceptance.

### Memory

- memory profile completion,
- approved memories per user,
- rejected proposed memories,
- outdated memories marked,
- boundary memories configured.

### Cost

- average cost per task,
- cost per active user,
- margin by plan,
- premium model usage rate,
- routing savings,
- retry waste.

### Funnel

- Free → Starter,
- Starter → Pro,
- Pro → All-Inclusive,
- Specialty Pack attachment,
- Roboticxs → Agentius Assessment.

---

## 15. v0.1 Non-Goals

Roboticxs v0.1 must not claim:

- certified legal signature,
- legal/tax/financial/medical advice,
- enterprise-grade governance,
- autonomous authority over money or external systems,
- unlimited all-inclusive execution,
- replacement for professional review.

---

## 16. MVP Acceptance Criteria

The MVP is acceptable when:

1. A user can create a robot.
2. A user can interact through Telegram.
3. A user can approve at least one memory.
4. A user can send a PDF/document and receive a useful review.
5. The robot can produce a meeting brief from approved context.
6. Out-of-scope requests are redirected or refused.
7. Sensitive actions require confirmation or are blocked.
8. Every task logs model route and token/cost event.
9. Admin can inspect task runs, safety decisions, and usage.
10. Consumer UX does not expose enterprise Zaubern terminology.
