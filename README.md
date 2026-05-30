# Roboticxs

Roboticxs is a personal robot for recurring life/work headaches, memory, skills, approvals, and bounded action.

Roboticxs is not a file-retrieval governance product.

Robbie prepares, organizes, reminds, and asks before acting. Nothing important happens without your permission.

## What Roboticxs is today

The current repo contains a real local runtime plus product and roadmap documents.

Today the runtime supports:
- Telegram text interaction
- local memory proposal / approve / reject
- memory list / forget
- text-simulated document review
- document review history / forget
- file metadata intake
- file metadata list / forget
- local model routing and token/cost logging
- local budget guardrails per user and robot
- retrieval intent, retrieval policy, and retrieval-control reporting surfaces

This means Roboticxs already has a meaningful local control plane:
- memory authority
- budget authority
- retrieval authority
- routing and audit logs

## What Roboticxs is not

Roboticxs should not be read as a retrieval-governance experiment.

The retrieval-control ladder now exists to preserve trust, not as the product headline.

Live retrieval remains disabled.
No getFile, download, OCR, parsing, provider execution, billing, or connector sync exists today.

Also not present today:
- browser automation
- Walmart automation
- Telmex automation
- raw byte persistence
- extracted text persistence
- dashboard UI

## Runtime status

Current retrieval state:
- retrieval is disabled by explicit local policy
- the retrieval adapter seam is mock-only
- retrieval-related commands are metadata/control only

Current product value is strongest in:
- approved memory
- bounded document handling from explicit text
- file metadata handling
- auditability and approvals
- local budget control

## Why the roadmap changes now

Roboticxs has enough internal governance for this phase.

The next priority is not more retrieval-control expansion.
The next priority is product utility:
- what did I miss
- important personal information
- skill discovery and activation
- caregiver and household workflows
- bounded web-workflow preparation

Roboticxs should stop proving only that it can safely avoid doing things, and start proving that it can safely help with things people actually pay to stop doing themselves.

## New product direction

Roboticxs is a personal admin robot for recurring life and work-admin pains.

Primary framing:
- recurring headaches
- memory and follow-up
- family and caregiver admin
- documents and pending actions
- skills organized around pains, not generic productivity buckets

Core user promise:
- Robbie prepares
- you decide
- nothing important happens without your permission

## Retrieval ladder status

The retrieval-control ladder is implemented and sufficient for now.

It is frozen unless a future approved stage explicitly reopens it.

That means:
- no continued retrieval-control ladder expansion by default
- no move to live retrieval by default
- no OCR/parsing/transport expansion by default

## Next roadmap direction

The next product stages are:
- Stage 26P — Product Reorientation / Runtime Status Alignment
- Stage 27P — Que se me paso v0
- Stage 28P — Robot Folder / Mi informacion importante
- Stage 29P — Skill Catalog + Capability Resolver
- Stage 30P — Super Familiar v0
- Stage 31P — Web Workflow Preflight Framework
- Stage 32P — Skill Activation + Pricing Metadata
- Stage 33P — Opportunity Log / Agentius Lead Handoff

## Recommended docs

Read these next:
- [Project Brief](docs/ROBOTICXS_PROJECT_BRIEF.md)
- [Implementation Status](docs/ROBOTICXS_IMPLEMENTATION_STATUS.md)
- [Product Pivot](docs/ROBOTICXS_PRODUCT_PIVOT_2026_05_30.md)
- [Runtime Status](docs/ROBOTICXS_RUNTIME_STATUS.md)
- [Roadmap Pivot](docs/ROBOTICXS_ROADMAP_PIVOT.md)
