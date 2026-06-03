# ROBOTICXS — Brief Additions: Knowledge Loop / Policy v0.1

> **Project:** Roboticxs  
> **Document type:** Official addendum to `ROBOTICXS_PROJECT_BRIEF.md`  
> **Status:** Planning addendum / Not implemented runtime behavior  
> **Date:** 2026-06-01  
> **Purpose:** Consolidate the knowledge-loop and policy-layer decisions derived from the Roboticxs Project Overview discussion without implying new runtime capability.

This addendum does not mean the repo already implements Obsidian integration, GBrain integration, AgentWASP integration, live connectors, browser automation, or a policy engine runtime.

## 1. Core framing

Roboticxs is not:
- an Obsidian replacement
- a vault product
- a PKM tool for power users
- a user-managed knowledge graph

Roboticxs may borrow the loop:

```text
capture authorized information
-> organize it with low friction
-> detect pending items / risks / useful connections
-> return useful attention to the user
-> let the user approve, correct, forget, or conserve
```

User-facing framing:

> Roboticxs is not a vault.  
> Roboticxs is a personal robot that turns approved context into useful attention and prepared actions.

## 2. Obsidian / GBrain / graph-style systems

If Obsidian, GBrain, or graph-style systems are mentioned, they should be framed only as inspiration for backend organization.

Allowed framing:
- structured memory
- relationships between people, tasks, documents, events, and decisions
- internal organization of approved context

Not allowed:
- user-managed graph UX
- live knowledge graph integration
- automatic storage of everything the user consumes

## 3. Robot Folder / Mi información importante

Roboticxs should roadmap a simple approved-context surface for users.

Possible names:
- Mi información importante
- Lo que Robbie sabe
- Robot Folder
- Centro de memoria

Candidate sections:
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

This is a future product surface, not a current runtime claim.

## 4. Approved memory policy

Roboticxs does not remember everything by default.

Correct memory rule:

> The robot may detect possible memories, but the user approves what becomes durable memory.

Required expectations:
- memory is proposed first
- user may approve, edit, reject, or forget it
- raw data should not be stored by default
- memory must be visible, editable, and bounded

Spanish user-facing form:

> Tú apruebas lo que tu robot recuerda.  
> Puedes editarlo, corregirlo u olvidarlo.

## 5. Source policy

Robbie only uses authorized sources.

When connectors are not active, Robbie must say it is using local state only.

Robbie must not imply that it checked:
- email
- WhatsApp
- calendar
- web
- files outside current local state
- external systems

unless that capability actually ran and is implemented.

## 6. Background work policy

Robbie may perform bounded background work only inside authorized tasks, schedules, or local-state checks.

Robbie must not be framed as an open-ended autonomous daemon.

Sensitive actions must stop before execution and either:
- ask for confirmation
- remain blocked
- escalate by policy

## 7. Action policy

Allowed by default:
- summarize
- organize
- classify
- draft
- remind
- prepare
- search approved local context
- propose next steps

Confirmation required:
- send external messages
- publish content
- update external records
- schedule with third parties
- submit forms
- download documents from external systems
- modify CRM/task systems
- create customer-facing documents

Blocked by default:
- execute payments
- accept legal terms
- change credentials
- change permissions
- delete accounts
- delete external data
- approve contracts
- make tax, financial, legal, medical, or employment decisions
- destructive system actions

## 8. Stage 27P fit

Stage 27P is the first visible local-only attention loop:
- `qué se me pasó`
- `what did I miss`
- `qué necesita mi atención`

Correct claim:

> Stage 27P uses only local persisted state to summarize what may need attention.

Incorrect claims:
- Robbie checks your email
- Robbie checks WhatsApp
- Robbie monitors your calendar
- Robbie browses the web
- Robbie detects everything you missed

## 9. Planned future docs/specs

The following are planned documentation/spec work, not implemented runtime:
- `ROBOT_FOLDER_SPEC_v0_1.md`
- `APPROVED_MEMORY_POLICY_SPEC_v0_1.md`
- `ACTION_BOUNDARY_POLICY_SPEC_v0_1.md`
- `BACKGROUND_WORK_POLICY_SPEC_v0_1.md`
- `SOURCE_POLICY_SPEC_v0_1.md`

## 10. Non-claims

Roboticxs must not claim:
- Obsidian integration
- GBrain integration
- AgentWASP integration
- automatic remember-everything behavior
- live email/WhatsApp/calendar/web monitoring unless implemented and authorized
- open-ended autonomous operation
- payment execution
- legal acceptance
- credential changes
- destructive actions
- live browser automation
- production-ready Webwright integration
- live Hermes integration unless repo evidence confirms it
