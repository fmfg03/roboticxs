# ROBOTICXS Product Pivot Context — 2026-05-30

## 0. Purpose

This document captures the product pivot discussed on 2026-05-30 and compares it against the current `ROBOTICXS_PROJECT_BRIEF.md`.

The existing brief is still valuable. It correctly defines Roboticxs as the low-friction consumer/prosumer front door into the Agentius / Zaubern ecosystem, built around one personal robot with memory, skills, model routing, token/cost visibility, and safety boundaries.

The pivot does **not** reject that foundation.

The pivot changes the center of gravity:

```text
FROM:
Personal AI robot for working better / productivity / prosumer workflows

TO:
Personal admin robot for people who are intimidated by technology,
focused on recurring life and work-admin pains,
with mobile/desktop control, server-side execution, skill activation,
and permissioned escalation into Agentius / Zaubern.
```

---

## 1. Baseline: What the Current Brief Says

The existing brief frames Roboticxs as:

```text
Product:
  Personal AI robots with memory, skills, model routing, and safety boundaries

Market:
  B2C / prosumer / small business

Strategic role:
  Mass-market entry product into Agentius and eventually Zaubern

Core promise:
  One robot that remembers context, helps with real work,
  and knows what it is not allowed to do
```

It also defines the strategic chain:

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

The brief’s original positioning was:

```text
Robots personales de IA para trabajar mejor.
```

and the initial MVP direction included:

```text
Telegram + Context Scan + Document Review + Meeting Briefing
```

The existing brief also assumes a package model:

```text
Basic Package
Pro Package
Specialty Packages
All-Inclusive Package
```

with Specialty Packs priced monthly.

---

## 2. Current Implementation Reality

The runtime has advanced far beyond paper planning.

Implemented / partially implemented areas include:

```text
- Telegram text-only control loop
- memory proposal / approve / reject
- memory list / forget
- text-simulated document review
- document history / forget
- file metadata intake
- file metadata list / forget
- model routing and local cost scaffolding
- local token / usage reporting
- budget guardrails
- per-robot budget configurability
- retrieval intent / control / policy / diagnostics ladder
```

But the implementation is now over-weighted toward control surfaces around retrieval.

Strong today:

```text
control plane
auditability
metadata boundaries
budget authority
retrieval authority boundaries
```

Weak today:

```text
visible consumer utility
real-life workflows
skill discovery
caregiver / household admin
office-admin workflow completion
live connector value
```

The next planned stages in the current implementation status continue retrieval-control work. That direction is defensible for safety, but it is no longer the highest-leverage product direction.

The pivot recommendation is:

```text
Freeze additional retrieval-control expansion for now.
Shift build focus toward product utility:
  - What did I miss?
  - Robot Folder / My Important Info
  - Skill Catalog + Capability Resolver
  - Caregiver / Súper Familiar
  - Web workflow preflight for real errands and admin tasks
```

---

## 3. Core Pivot

### Old center of gravity

```text
Personal AI robot for productivity and daily AI adoption.
```

### New center of gravity

```text
Personal admin robot for life and work-admin pains.
```

The user does not primarily want to “use AI.”

The user wants help with:

```text
- things they forget
- things that create anxiety
- recurring errands
- family responsibilities
- tedious web tasks
- messages and follow-ups
- documents and receipts
- appointments
- payments prepared but not executed
- weekly routines
```

New product statement:

```text
Roboticxs helps you resolve recurring headaches in life and work.
Your robot prepares, organizes, reminds, and asks before doing anything important.
```

Spanish product statement:

```text
Roboticxs es tu robot personal para resolver pendientes de la vida diaria y del trabajo.
Prepara, organiza y te pide permiso antes de actuar.
```

---

## 4. Target User Correction

### Old implied target

```text
B2C / prosumer / small business users who want a personal AI robot.
```

### New explicit target

```text
People who are intimidated by technology or afraid of AI,
but who have recurring life/admin pains they would happily pay to reduce.
```

This is not a power-user product.

Power users such as Nicolas Bustamante are useful as leading indicators, not as the main customer.

Power-user pattern:

```text
Codex / Claude Code
+ Gmail / Drive / Calendar / Docs / Sheets via CLI
+ WhatsApp / SMS / browser automation
+ source-of-truth files
+ skills
+ approval gates
```

Roboticxs translation:

```text
Robbie
+ connected accounts
+ Robot Folder
+ approved memories
+ simple skills
+ approval buttons
+ “What did I miss?”
+ safe boundaries
```

Power users tolerate complexity.

Roboticxs users pay to avoid it.

---

## 5. The Winning Job-to-Be-Done

The strongest general workflow identified is:

```text
What did I miss?
¿Qué se me pasó?
¿Qué necesita mi atención?
```

This is stronger than “chat with AI” and broader than “inbox zero.”

It applies across:

```text
home
family
parents / in-laws
car
services
school
documents
messages
small office work
professional admin
```

User-facing promise:

```text
Tu robot revisa lo que autorizas y te dice qué necesita atención.
```

Example output:

```text
Encontré 5 cosas que necesitan atención:

1. Hay un pago de Telmex próximo.
2. Tienes el súper de tus papás en la agenda.
3. Recibí un documento que todavía no he revisado.
4. Hay un trámite del coche pendiente.
5. Tienes 3 mensajes que probablemente requieren respuesta.

¿Quieres que prepare alguno?
```

---

## 6. Robot Folder / My Important Info

Nicolas’ Google Drive pattern is a strong signal, but the consumer UX must hide technical language.

### Do not expose this as:

```text
source of truth
Markdown files
CSV contacts
agent-readable data layer
```

### Expose it as:

```text
Mi Carpeta del Robot
Mi información importante
Lo que Robbie debe saber
```

Initial sections:

```text
- Sobre mí
- Mi familia
- Mis papás / suegros
- Mi coche
- Mi casa
- Mis servicios
- Contactos importantes
- Documentos importantes
- Preferencias
- Cosas que Robbie nunca debe hacer
```

Internally, the system can store this as structured records, Markdown, CSV, or documents. The user should see simple cards and conversational onboarding.

---

## 7. Skills Reframed: One Pain = One Skill

The old brief organizes skills as packages:

```text
Marketing Pack
Sales Pack
Finance/Admin Pack
HR Pack
Documents Pack
```

The pivot reframes the catalog:

```text
One recurring headache = one skill.
```

The skill catalog should grow around pain, not generic productivity categories.

Examples:

```text
- Súper de mis papás
- Pagar Telmex
- Verificación del coche
- Citas médicas
- Mandar comprobantes de escuela
- Renovar seguro
- Recordar medicinas
- Preparar documentos de trámite
- Qué mensajes necesitan respuesta
- Automatizar seguimiento de clientes
- Organizar WhatsApp de consultorio
```

Skill definition template:

```text
Skill:
  Name:
  Pain:
  Frequency:
  Emotional burden:
  Risk if forgotten:
  Required data:
  Required connectors:
  Allowed actions:
  Approval-required actions:
  Blocked actions:
  Setup path:
  Price:
```

Core rule:

```text
Your pain = your price.
```

---

## 8. Pricing Pivot

### Old pricing model

The brief proposes:

```text
Starter: USD 19–29/month
Pro: USD 49–79/month
Specialty Packs: USD 9–29/month per package
All-Inclusive: USD 99–149/month
Done-for-you setup: USD 99–299 one-time
```

### New recommended model

```text
Base subscription:
  around USD 20/month

Usage:
  tokens / model usage / automation usage

Skills:
  mostly prebuilt
  activated/configured one time
  priced by pain intensity, not code complexity
```

Do not frame it as “creating a skill from scratch.”

Frame it as:

```text
Activate this skill for your robot.
Configure this routine.
Teach Robbie this habit.
```

Suggested pricing bands:

```text
Simple skill:
  USD 1–3 one-time

Medium recurring admin skill:
  USD 4–7 one-time

High-pain caregiver/home admin skill:
  USD 9–19 one-time

Assisted setup for complex skill:
  USD 19–49 one-time

Professional/regulated vertical:
  custom / Agentius-led
```

Important correction:

Monthly per-skill charges risk making the product feel expensive too quickly.

Base subscription + one-time skill activation feels more natural:

```text
You pay for your robot monthly.
When your robot learns a new routine, you activate that skill once.
```

---

## 9. Caregiver / Súper Familiar as First Commercial Wedge

The strongest concrete wedge identified is:

```text
Súper semanal para papás / suegros
```

This is not grocery shopping as convenience.

It is caregiver admin:

```text
- weekly recurring burden
- emotionally loaded
- easy to understand
- high willingness to pay
- clear household buyer
- creates weekly habit
```

User story:

```text
As a caregiver, I want Robbie to prepare the weekly Walmart grocery order
for my parents or in-laws, using the usual list, preferences, substitutions,
budget, and delivery window, so I only need to review and approve before payment.
```

Key behavior:

```text
- maintain recurring list
- remember brands
- track substitutions
- respect dietary restrictions
- respect budget
- select delivery window
- prepare cart
- show summary
- ask approval before checkout/payment
- store receipt
- learn changes
```

Boundary:

```text
Robbie prepares the order.
The user approves and pays.
```

Recommended package:

```text
Roboticxs Caregiver
  First skill: Súper Familiar
```

Possible future caregiver skills:

```text
- pharmacy reminders / limited pharmacy prep
- medical appointment scheduling
- service payments preparation
- documents and receipts
- reminders for parents
- check-in messages
```

---

## 10. Web Workflow Preflight

Many valuable Roboticxs workflows are server-side web tasks, not mobile-app control.

Examples:

```text
- agendar verificación vehicular CDMX
- preparar pago Telmex
- preparar carrito Walmart
- restaurant reservation
- appointment scheduling
- service portals
```

Recommended execution principle:

```text
Server-side robot does the web work.
User approves from phone or computer.
```

Do not sell “control your phone.”

Sell:

```text
Robbie opens the web process, prepares what is safe, and stops before the commitment point.
```

Commitment points requiring explicit user approval:

```text
- final payment
- final appointment confirmation
- external message send
- legal acceptance
- account setting change
- document submission
- anything irreversible
```

---

## 11. Examples of Pivot Workflows

### 11.1 Verificación CDMX

```text
User:
  Ayúdame a agendar la verificación del coche.

Robbie:
  asks for plates, hologram, area, schedule preferences;
  checks requirements;
  prepares appointment options;
  stops before final booking;
  asks for approval;
  saves appointment and reminders.
```

### 11.2 Telmex

```text
User:
  Ayúdame a pagar Telmex.

Robbie:
  logs in through authorized path;
  retrieves bill;
  reads amount, due date, period;
  compares against normal consumption;
  prepares payment screen;
  stops before final charge;
  user executes final payment.
```

Boundary:

```text
Robbie prepares. User pays.
No CVV storage. No silent payment.
```

### 11.3 Súper Familiar

```text
User:
  Haz el súper de mis papás.

Robbie:
  uses weekly list;
  checks missing products;
  proposes substitutions;
  controls budget;
  prepares cart;
  stops before payment;
  user approves/pays.
```

### 11.4 WhatsApp médico

```text
User:
  ¿Puedes automatizar mi WhatsApp médico?

Robbie:
  does not claim capability if unavailable;
  explains safe scope:
    triage, summaries, draft replies, scheduling, follow-up;
  blocks autonomous medical advice;
  asks permission to register the opportunity for Agentius.
```

---

## 12. Robbie as Natural Lead Generator

Robbie is not only a robot. It is a demand-discovery surface.

Every user request can become one of five outcomes:

```text
ACTIVE_FOR_USER:
  already available and configured

AVAILABLE_TO_ACTIVATE:
  prebuilt skill exists, needs activation

AVAILABLE_NEEDS_SETUP:
  skill exists but needs credentials/preferences

NEW_VERTICAL_CANDIDATE:
  not available yet, but high-value repeated pain

PROHIBITED_OR_RESTRICTED:
  cannot be done safely or requires bounded version
```

Robbie must answer honestly:

```text
I can do that now.
I can activate that skill.
I can configure that for you.
I do not have that skill yet, but I can register the need.
I cannot do that safely, but I can help with a bounded version.
```

New vertical lead object:

```text
VerticalOpportunity:
  user_id
  robot_id
  raw_request
  pain_description
  frequency_signal
  urgency_signal
  risk_class
  requested_outcome
  allowed_scope_candidate
  blocked_scope
  consent_to_contact
  recommended_stack: Roboticxs / Agentius / Zaubern
```

Example:

```text
User:
  Can you automate my medical WhatsApp?

Robbie:
  I do not have that skill available yet.
  A safe version would classify messages, identify possible urgency,
  prepare drafts, and ask the doctor before sending anything.
  I should not send medical advice automatically.

  Do you want me to register this need for Agentius to evaluate?
```

---

## 13. Zaubern Advantage

Nicolas Bustamante’s setup validates the personal-agent pattern, but it relies on power-user discipline.

Roboticxs needs a packaged trust layer.

Zaubern’s role in Roboticxs is not consumer-facing jargon. It is the internal control layer that helps enforce:

```text
- no silent authority expansion
- no off-mandate execution
- no unauthorized memory
- no silent payments
- no autonomous medical/legal/tax advice
- no silent external sends
- no content-review claims from metadata
- no tool execution beyond current authorization
```

Consumer-facing language:

```text
Robbie prepares. You decide.
Nothing important happens without your permission.
```

Strategic phrasing:

```text
Power users control their agents manually.
Roboticxs packages control for everyone else.
```

---

## 14. Architecture Pivot

The robot should not live on the phone or computer.

It should run in a private server-side workspace/container.

User devices are control surfaces.

```text
User devices:
  phone
  computer
  Telegram
  web app
  email / future channels

Roboticxs Gateway:
  auth
  routing
  notifications
  approvals

Private Robot Workspace:
  memory
  files
  skills
  secrets
  policies
  logs
  connectors
  task execution state

External services:
  Gmail
  Drive
  Calendar
  Walmart
  Telmex
  government sites
  restaurant platforms
```

Product language:

```text
Your robot lives in its own secure workspace.
You control it from your phone or computer.
```

Do not expose:

```text
Docker
container
runtime
orchestrator
```

unless speaking to operators/developers.

---

## 15. Product Positioning Update

### Old hero

```text
Tu robot personal de IA para trabajar mejor.
```

### New hero candidates

```text
Tu robot personal para resolver pendientes de la vida diaria.
```

```text
IA sin miedo. Tu robot prepara, organiza y te pide permiso antes de actuar.
```

```text
Robbie te ayuda con trámites, citas, documentos, mensajes y compras recurrentes.
```

### New subheadline

```text
Mándale lo que necesitas. Robbie revisa lo que autorizas,
prepara el siguiente paso y te pide permiso antes de hacer algo importante.
```

### Trust line

```text
Tú apruebas qué recuerda. Tú decides qué puede hacer.
Nada importante pasa sin tu permiso.
```

---

## 16. Roadmap Pivot

### Stop / freeze for now

Freeze additional retrieval-control expansion after the current state.

Do not continue, for now, with:

```text
- retrieval control activity feed
- retrieval report snapshot variants
- retrieval retention policy
- retrieval admin notes
- transport capability matrix
- pre-live retrieval readiness checklist
```

These are useful later but currently over-optimize control instead of product utility.

### Build next

Recommended next product stages:

```text
Stage 26P — Product Reorientation Docs
  Update README / product docs to reflect the pivot.

Stage 27P — “Qué se me pasó?” v0
  Summarize active local state into user-visible attention items.

Stage 28P — Robot Folder / Mi información importante
  Structured personal/family/home/work info store.

Stage 29P — Skill Catalog + Capability Resolver
  Classify user requests into active skill, activatable skill, setup-needed skill,
  new vertical opportunity, or blocked/restricted request.

Stage 30P — Súper Familiar v0
  Manual/semi-manual caregiver grocery workflow.

Stage 31P — Web Workflow Preflight Framework
  Generic bounded flow for Telmex, verification, Walmart, restaurants, appointments.

Stage 32P — Skill Activation + Pricing Metadata
  One-time activation fees, setup type, pain-based pricing.

Stage 33P — Opportunity Log / Agentius Lead Handoff
  Register high-value unmet requests for Agentius / Zaubern evaluation.
```

---

## 17. What Changes Compared to the Current Brief

| Area | Current Brief | Pivot |
|---|---|---|
| Positioning | Personal AI robot to work better | Personal admin robot for recurring life/work headaches |
| Target | B2C / prosumer / small business | Non-technical users, caregivers, families, personal/work admin |
| First demo | Telegram + Context Scan + Document Review + Meeting Briefing | Qué se me pasó + Súper Familiar + Robot Folder |
| Skill model | Packages like Basic/Pro/Marketing/Sales/Documents | Pain-based skills; one headache = one skill |
| Pricing | Monthly packages and Specialty Packs | Base subscription + usage + one-time skill activation/setup |
| Differentiator | Memory, skills, routing, boundaries | Relief from anxiety/cognitive load + approval-based action |
| Upgrade path | Agentius for business workflows | Robbie discovers vertical pain and hands qualified leads to Agentius |
| User language | Work better, connect tools | Robbie prepares, organizes, reminds, and asks before acting |
| Runtime focus | Context scan, docs, routing, token cost | Private robot workspace + web workflows + approval gates |
| Next build | More control/retrieval stages | Utility workflows and skill discovery |

---

## 18. What Does Not Change

The following remain correct and should be preserved:

```text
- One robot, many skills
- Memory approval
- Skill manifests
- Scope guards
- Proactive suggestions from authorized context
- Token/cost visibility
- Budget as authority surface
- Lightweight Zaubern safety layer
- Telegram/web-first interaction
- Agentius upgrade path
- Zaubern as deeper authority layer
- Do not compete with ChatGPT/Claude on intelligence
```

The pivot changes market framing and roadmap priority, not the underlying architecture.

---

## 19. Updated MVP Definition

A credible pivoted MVP should demonstrate:

```text
1. User can talk to Robbie from Telegram/web.
2. Robbie can remember approved info.
3. Robbie can show “Qué se me pasó?”
4. Robbie can maintain “Mi información importante.”
5. Robbie can classify whether a requested task is:
   - available,
   - activatable,
   - setup-needed,
   - new vertical,
   - prohibited/restricted.
6. Robbie can run at least one high-pain skill:
   - Súper Familiar v0.
7. Robbie can prepare but not execute sensitive actions.
8. Robbie can log and hand off unmet high-value requests to Agentius.
```

This is more commercially meaningful than more retrieval diagnostics.

---

## 20. Immediate Action Recommendation

Do not discard the existing `ROBOTICXS_PROJECT_BRIEF.md`.

Create a new pivot overlay:

```text
docs/ROBOTICXS_PRODUCT_PIVOT_2026_05_30.md
```

Then update the next Codex prompt:

```text
Read current implementation status.
Read original project brief.
Read product pivot overlay.
Freeze retrieval-control expansion.
Propose product utility roadmap starting with:
  - Qué se me pasó
  - Robot Folder
  - Skill Catalog + Capability Resolver
  - Súper Familiar
```

Final decision:

```text
Roboticxs should stop proving that it can safely avoid doing things,
and start proving that it can safely help with things people actually pay to stop doing themselves.
```
