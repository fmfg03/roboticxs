# Roboticxs Roadmap Pivot

## Why the roadmap changes

The current runtime already proves a strong local control plane:
- memory authority
- budget authority
- retrieval authority
- local auditability

That foundation is sufficient for now.

The roadmap should stop optimizing retrieval-control expansion and start proving product utility.

## Retrieval ladder status

The retrieval-control ladder is implemented and sufficient for now.

It is frozen unless a future approved stage explicitly reopens it.

This means:
- no default continuation of retrieval-control-only stages
- no default move to live retrieval
- no default move to OCR/parsing/browser automation

## New stage order

### Stage 26P — Product Reorientation / Runtime Status Alignment
- documentation realignment only
- explain what exists
- explain what is disabled
- freeze retrieval-control expansion
- redirect roadmap

### Stage 27P — Que se me paso v0
- first visible user-value workflow
- summarize active state into attention items

### Stage 28P — Robot Folder / Mi informacion importante
- personal structured memory for family, home, car, services, preferences, and hard boundaries

### Stage 29P — Skill Catalog + Capability Resolver
- classify whether Robbie can already do something, activate it, configure it, register it, or block it safely

### Stage 30P — Super Familiar v0
- caregiver and household-admin wedge
- bounded grocery-preparation flow with approval before payment

### Stage 31P — Web Workflow Preflight Framework
- bounded web-admin preparation pattern
- Robbie prepares, user confirms
- experimental browser-task path only after sandbox-first validation

### Stage 32P — Skill Activation + Pricing Metadata
- pain-based skill activation and setup metadata

### Stage 33P — Opportunity Log / Agentius Lead Handoff
- register unmet high-value requests as product and sales signals

## Planned documentation/spec backlog

The following documents are planned and should not be read as implemented runtime:
- `docs/HERMES_ADAPTER_SPEC_v0_1.md`
- `docs/LATENCY_ROUTING_SPEC_v0_1.md`
- `docs/WEB_TASK_WORKER_SPEC_v0_1.md`
- `docs/ROBOTICXS_MIRIX_MEMORY_EVALUATION_v0_1.md`
- `ROBOT_FOLDER_SPEC_v0_1.md`
- `APPROVED_MEMORY_POLICY_SPEC_v0_1.md`
- `ACTION_BOUNDARY_POLICY_SPEC_v0_1.md`
- `BACKGROUND_WORK_POLICY_SPEC_v0_1.md`
- `SOURCE_POLICY_SPEC_v0_1.md`

These docs should formalize:
- Hermes as runtime substrate, not product
- policy-first low-latency routing
- Web Task Worker / Webwright as experimental sandbox-first infrastructure
- MIRIX as a future internal memory-plane adapter candidate only after MVP
- Robot Folder / Mi informacion importante as a future user-facing surface
- approved memory, source policy, background work policy, and action boundary policy

## Product principle behind the pivot

Roboticxs is not a file-retrieval governance product.

Roboticxs is a personal robot for recurring life/work headaches, memory, skills, approvals, and bounded action.

The next milestone should prove:
- Robbie can reduce anxiety and admin burden
- Robbie can surface what needs attention
- Robbie can prepare meaningful next steps safely

Not:
- more control surfaces around still-disabled retrieval
