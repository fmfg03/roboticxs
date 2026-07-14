> Reference note preserved from prior Roboticxs planning work. Not runtime behavior.

# Codex Instructions — Roboticxs Brief Additions: Obsidian / Knowledge Loop / Policy Layer

> **Project:** Roboticxs
> **Instruction type:** Documentation-only Codex task
> **Proposed stage:** Stage 26Q-B — Knowledge Loop & Policy Consolidation
> **Status:** Proposed / not implemented
> **Source context:** Roboticxs project discussion around Obsidian-style knowledge loops, GBrain-style memory architecture, AgentWASP/policy boundaries, and the existing Stage 27P “Qué se me pasó v0” implementation.
> **Hard constraint:** Do not modify runtime, app code, tests, database models, providers, connectors, browser automation, or retrieval behavior.

---

## 1. Objective

Incorporate the useful ideas from the Roboticxs Project Overview discussion into the official Roboticxs documentation without implying new implemented capabilities.

The goal is to align the product brief and roadmap around:

- Obsidian/GBrain-style knowledge organization as **product inspiration**, not a user-facing integration.
- A simple **Robot Folder / Mi información importante** concept for approved user context.
- A lightweight **policy layer** inspired by AgentWASP-like guardrails, without claiming an AgentWASP integration.
- Approved/editable memory as the core product rule.
- Bounded background work, not open-ended autonomous operation.
- Clear prohibition of silent sensitive actions.
- Stage 27P as the first implemented local-state attention loop: “qué se me pasó.”

---

## 2. Core Product Decisions to Preserve

### 2.1 Obsidian is not the product

Do **not** position Roboticxs as:

- an Obsidian replacement,
- a vault,
- a PKM tool,
- a markdown graph,
- a knowledge management product for power users.

Roboticxs may borrow the loop:

```text
capture authorized information
→ organize it with low friction
→ detect pending items / risks / connections
→ return useful attention to the user
→ let the user approve, correct, forget, or conserve
```

But the user-facing experience must remain simple, mobile-first, and non-technical.

Correct positioning:

```text
Roboticxs is not a vault.
Roboticxs is a personal robot that turns approved context into useful attention and prepared actions.
```

---

### 2.2 GBrain / graph-style architecture is backend inspiration only

If the docs mention GBrain, Obsidian-like graphs, or similar tools, frame them as backend inspiration.

Allowed framing:

```text
Roboticxs can use structured memory, relationships, documents, events, people, tasks, and decisions internally.
The user should not be forced to manage graphs, folders, markdown, backlinks, or PKM workflows.
```

Not allowed:

```text
Roboticxs exposes a user-managed knowledge graph.
Roboticxs is an autonomous Obsidian vault.
Roboticxs automatically stores everything the user consumes.
```

---

### 2.3 Robot Folder / “Mi información importante”

Add or roadmap the concept of a simple approved-context surface.

Suggested user-facing names:

- `Mi información importante`
- `Lo que Robbie sabe`
- `Robot Folder`
- `Centro de memoria`

Initial sections may include:

- Sobre mí
- Familia
- Papás / suegros
- Casa
- Auto
- Servicios
- Contactos importantes
- Documentos importantes
- Preferencias
- Límites del robot

This is a future product surface, not necessarily implemented in the current runtime.

---

### 2.4 AgentWASP-style policy layer

Do not claim AgentWASP is integrated unless repo evidence confirms it.

Use generic language:

```text
lightweight policy layer
robot safety policy
action boundary policy
permission and confirmation policy
```

The policy layer should govern:

- what the robot may read,
- what it may remember,
- what it may prepare,
- what requires confirmation,
- what must be blocked,
- what must be escalated,
- what must never be performed silently.

---

### 2.5 Stage 27P is the first visible attention loop

Stage 27P has been implemented separately as:

```text
qué se me pasó
what did I miss
qué necesita mi atención
```

Docs may reference it as the first local-only proof that Robbie can turn persisted state into useful attention.

Do not overclaim it.

Correct claim:

```text
Stage 27P uses only local persisted state to summarize what may need attention.
```

Incorrect claims:

```text
Robbie checks your email.
Robbie checks WhatsApp.
Robbie monitors your calendar.
Robbie browses the web.
Robbie detects everything you missed.
```

---

## 3. Required Documentation Updates

Perform a read-only inspection first. Do not assume exact file names beyond confirmed existing docs.

Likely relevant docs:

- `docs/ROBOTICXS_PROJECT_BRIEF.md`
- `docs/ROBOTICXS_ROADMAP_PIVOT.md`
- `docs/ROBOTICXS_BRIEF_ADDITIONS_HERMES_ROUTING_WEB_TASK_v0_1.md`
- `README.md`

Only modify documentation files.

---

## 4. Proposed New Addendum

Create an official addendum under `docs/` if repo naming conventions support it.

Suggested filename:

```text
docs/ROBOTICXS_BRIEF_ADDITIONS_KNOWLEDGE_LOOP_POLICY_v0_1.md
```

Alternative if the repo prefers stage names:

```text
docs/STAGE_26Q_B_KNOWLEDGE_LOOP_POLICY_ADDITION.md
```

The addendum should include:

1. Obsidian/GBrain as inspiration, not integration.
2. Robot Folder / Mi información importante as a future user-facing surface.
3. Approved-memory policy.
4. Source policy.
5. Background-work policy.
6. Action policy.
7. Policy-layer backlog.
8. How Stage 27P fits this direction.
9. Non-claims.
10. Future specs/backlog.

---

## 5. Brief Alignment Requirements

Patch `docs/ROBOTICXS_PROJECT_BRIEF.md` only where materially misaligned.

The brief should clearly state:

```text
Roboticxs should not expose a vault, graph, or autonomous agent UX.
Roboticxs should expose a simple approved-memory robot that turns authorized local context into useful attention, reminders, and prepared actions.
Policy gates prevent silent sensitive execution.
```

Make sure the brief does **not** imply:

- automatic capture of all user data,
- raw memory storage by default,
- unlimited autonomous operation,
- live connector access before implemented,
- browser automation before implemented,
- Obsidian/GBrain/AgentWASP integration unless confirmed,
- payments, credential changes, legal acceptance, or destructive actions.

---

## 6. Roadmap / Backlog Alignment

Update roadmap/spec backlog references to include the following future docs or stages.

### Future product docs/specs

```text
ROBOT_FOLDER_SPEC_v0_1.md
APPROVED_MEMORY_POLICY_SPEC_v0_1.md
ACTION_BOUNDARY_POLICY_SPEC_v0_1.md
BACKGROUND_WORK_POLICY_SPEC_v0_1.md
SOURCE_POLICY_SPEC_v0_1.md
```

These should be listed as planned/backlog unless created as placeholders.

### Future stages

Recommended order:

```text
Stage 26Q-B — Knowledge Loop & Policy Consolidation
Stage 28F — File Review Linkage v0
Stage 29P — Robot Folder / Mi información importante v0
Stage 30P — Policy Layer Spec v0.1
```

Do not create implementation tasks for connectors, Webwright, Hermes runtime, or browser automation in this stage.

---

## 7. Policy Language to Add

### 7.1 Memory Policy

```text
The robot does not remember everything by default.
It proposes memories.
The user approves, edits, or rejects proposed memories.
The user can forget approved memories.
Raw data should not be stored by default.
Memory must be visible, editable, and bounded.
```

Spanish user-facing version:

```text
Tú apruebas lo que tu robot recuerda.
Puedes editarlo, corregirlo u olvidarlo.
```

---

### 7.2 Source Policy

```text
Robbie only uses authorized sources.
When connectors are not active, Robbie must say it is using local state only.
Robbie must not imply that it checked email, WhatsApp, calendar, web, files, or external systems unless that capability actually ran.
```

---

### 7.3 Background Work Policy

```text
Robbie may perform bounded background work only inside authorized tasks, schedules, or local-state checks.
Robbie must not operate as an open-ended autonomous daemon.
Sensitive actions must stop before execution and ask for user confirmation or remain blocked.
```

---

### 7.4 Action Policy

Allowed by default:

- summarize,
- organize,
- classify,
- draft,
- remind,
- prepare,
- search approved local context,
- propose next steps.

Confirmation required:

- send external messages,
- publish content,
- update external records,
- schedule with third parties,
- submit forms,
- download documents from external systems,
- modify CRM/task systems,
- create customer-facing documents.

Blocked by default:

- execute payments,
- accept legal terms,
- change credentials,
- change permissions,
- delete accounts,
- delete external data,
- approve contracts,
- make tax/financial/legal/medical/employment decisions,
- perform destructive system actions.

---

## 8. Non-Claims

The documentation must explicitly avoid these claims:

- Roboticxs is an Obsidian replacement.
- Roboticxs exposes a live knowledge graph.
- Roboticxs integrates GBrain.
- Roboticxs integrates AgentWASP.
- Roboticxs remembers everything automatically.
- Roboticxs reads email/WhatsApp/calendar/web unless connectors are implemented and authorized.
- Roboticxs runs autonomously without boundaries.
- Roboticxs can execute payments.
- Roboticxs can accept legal terms.
- Roboticxs can change passwords or permissions.
- Roboticxs can perform destructive actions.
- Roboticxs browser automation is live.
- Roboticxs Webwright integration is production-ready.
- Roboticxs Hermes integration is live unless repo evidence confirms it.

---

## 9. Acceptance Criteria

- An official addendum exists under `docs/` covering knowledge-loop and policy-layer additions.
- `docs/ROBOTICXS_PROJECT_BRIEF.md` is aligned with:
  - Obsidian/GBrain as inspiration only,
  - approved memory,
  - Robot Folder / Mi información importante as future product surface,
  - local-state attention loop,
  - bounded background work,
  - no open-ended autonomy,
  - policy-gated sensitive actions.
- Roadmap/spec backlog references include:
  - Robot Folder,
  - approved memory policy,
  - action boundary policy,
  - background work policy,
  - source policy.
- Docs clearly state Stage 27P is local-state-only and does not imply live connectors.
- Docs do not claim Obsidian, GBrain, AgentWASP, Hermes, Webwright, browser automation, or connectors are implemented unless repo evidence confirms it.
- No files outside documentation are modified.
- No runtime capabilities are changed.
- No tests, app code, DB models, provider logic, retrieval logic, connector logic, parsing, OCR, browser automation, or billing behavior are modified.

---

## 10. Non-Goals

- No code.
- No tests.
- No database changes.
- No runtime changes.
- No new commands.
- No connectors.
- No live retrieval.
- No browser automation.
- No Webwright integration.
- No Hermes runtime integration.
- No Obsidian integration.
- No GBrain integration.
- No AgentWASP integration.
- No provider execution.
- No parsing/OCR.
- No billing.
- No file download.
- No policy engine implementation.
- No production capability claims.

---

## 11. Implementation Guidance for Codex

1. Start with read-only repo inspection.
2. Identify current documentation files and naming conventions.
3. Inspect the existing Roboticxs brief and roadmap.
4. Add the official knowledge-loop/policy addendum under `docs/`.
5. Patch only materially misaligned parts of the core brief.
6. Patch roadmap/spec backlog references if a roadmap doc exists.
7. Do not create full specs unless repo conventions already use planned placeholders.
8. If placeholders are created, mark them clearly:

```text
Status: Planned / Not Implemented
```

9. Do not modify `app/`, `tests/`, migrations, models, provider code, connector code, or runtime config.
10. Confirm changes with a concise readback.

---

## 12. Validation Commands

Documentation-only validation:

```bash
git status --short
git diff --stat
git diff -- docs README.md
```

Optional text checks:

```bash
grep -R "Obsidian" -n docs README.md
grep -R "GBrain" -n docs README.md
grep -R "AgentWASP" -n docs README.md
grep -R "qué se me pasó" -n docs README.md
grep -R "open-ended autonomy\|autonomous" -n docs README.md
```

Expected result:

- only documentation files changed;
- no app/runtime/test files changed;
- no implementation claims introduced;
- no connector/browser/Hermes/Webwright/AgentWASP integration claims introduced.

---

## 13. Recommended Commit Shape

Use a documentation-only commit.

Suggested commit message:

```text
docs(roboticxs): add knowledge loop and policy addendum
```

Suggested PR title:

```text
Stage 26Q-B — Knowledge Loop & Policy Consolidation
```

---

## 14. Final Readback Required

Before finalizing, report:

- files changed;
- where the addendum was placed;
- what brief sections were patched;
- what roadmap/spec backlog references were added;
- confirmation that no runtime/app/test files were modified;
- confirmation that no new capabilities were claimed.
