# Roboticxs Command Surface Policy v0.1

Status: 90P implemented pending review.

This document defines the consumer-safe Roboticxs command surface policy. It is story/spec/test work only. It does not implement live command routing, runtime gateway changes, production enforcement code, MCP/plugin activation, tool activation, model-provider switching, or UI.

## Purpose

Roboticxs must expose product commands in consumer-safe language while preserving the authority boundaries established by prior stages.

Hermes capability does not equal Roboticxs permission. Raw Hermes slash commands, CLI commands, tool controls, model controls, gateway controls, MCP/plugin controls, and dangerous bypass commands must be classified before any consumer exposure.

## Policy classes

`EXPOSE`: Consumer-visible Roboticxs command or intent that may be shown directly when mapped to product language and existing authority.

`WRAP`: Hermes or operator capability that may be represented only through a Roboticxs product wrapper with plan, authority, cost, audit, and fallback requirements.

`OPERATOR_ONLY`: Operator/admin capability that must not be consumer-visible. It may be documented for operator governance only.

`BLOCK_CONSUMER`: Capability or command that must never be exposed to consumer users.

`UNKNOWN_UNVERIFIED`: Any raw command or capability not explicitly classified. Unknown commands default to blocked consumer exposure.

## Command exposure invariant

No raw Hermes command is exposed to end users unless it is mapped to all of:

- user intent;
- allowed plan;
- authority boundary;
- cost policy;
- audit log;
- safe fallback.

Consumer users see Roboticxs product language, not Hermes operator language.

## Initial policy matrix

| Surface | Policy class | Roboticxs user-facing treatment | Authority notes |
| --- | --- | --- | --- |
| `help` | `EXPOSE` | Help | Show available Roboticxs actions only. |
| `status` | `EXPOSE` | Status | Summarize safe local runtime and product state. |
| `usage` | `EXPOSE` | Usage | Bound by Cost Governor reporting. |
| `approve` | `EXPOSE` | Approve an Action Packet | Sensitive approvals require an Action Packet. |
| `deny` | `EXPOSE` | Deny an Action Packet | Sensitive denials require an Action Packet reference when applicable. |
| `routines list` | `EXPOSE` | Routines list | Lists Roboticxs Routine/Blueprint state only. |
| `skills list` | `EXPOSE` | Skills list | Lists safe Roboticxs Skill Packages only. |
| `memory review` | `EXPOSE` | Memory review | Memory Center remains canonical memory. |
| `stop` | `EXPOSE` | Stop | Stop/cancel current safe local flow where supported. |
| `/cron` | `WRAP` | Roboticxs Routines | Hermes cron is runtime capability; Roboticxs Routine is the product object. |
| `/skills` | `WRAP` | Habilidades / Skill Packages | Agent Skills package instructions/resources; they do not grant authority. |
| `/bundles` | `WRAP` | Skill Packages | Bundle/package language must map to Roboticxs package authority. |
| `/model` | `WRAP` | Economy / Balanced / Premium | Cost Governor and Model Router remain authorities. |
| `/handoff` | `WRAP` | Approved channel send/delivery | Direct external platform handoff is blocked without authority. |
| `/personality` | `WRAP` | Approved modes | Modes are product-approved behavior styles, not freeform profile authority. |
| `/sessions` | `WRAP` | Conversation history | Must preserve memory and privacy boundaries. |
| `/resume` | `WRAP` | Continue conversation | Continue only within authorized conversation continuity boundaries. |
| `/config` | `OPERATOR_ONLY` | Not consumer-visible | Runtime/admin configuration only. |
| `/reload` | `OPERATOR_ONLY` | Not consumer-visible | Operator lifecycle control only. |
| `/reload-mcp` | `OPERATOR_ONLY` | Not consumer-visible | MCP reload is not consumer authority. |
| `/plugins` | `OPERATOR_ONLY` | Not consumer-visible | Plugin activation/management is operator-only. |
| Browser connect controls | `OPERATOR_ONLY` | Not consumer-visible | Browser/tool session controls are operator-only. |
| `/toolsets` | `OPERATOR_ONLY` | Not consumer-visible | Tool enablement is operator-only. |
| `/debug` | `OPERATOR_ONLY` | Not consumer-visible | Diagnostics only. |
| `/profile` | `OPERATOR_ONLY` | Not consumer-visible | Hermes profile state is not consumer business authority. |
| `/platforms` | `OPERATOR_ONLY` | Not consumer-visible | External platform controls are operator-only. |
| `/gateway` | `OPERATOR_ONLY` | Not consumer-visible | Gateway controls are operator-only. |
| `/codex-runtime` | `OPERATOR_ONLY` | Not consumer-visible | Runtime controls are operator-only. |
| `/branch` | `OPERATOR_ONLY` | Not consumer-visible | Source/runtime branch controls are operator-only. |
| `/rollback` | `OPERATOR_ONLY` | Not consumer-visible | Rollback controls are operator-only. |
| `/yolo` | `BLOCK_CONSUMER` | Never show | Dangerous bypass command; never consumer-visible. |
| Dangerous command approvals without Action Packet | `BLOCK_CONSUMER` | Never allow | Sensitive actions require Action Packets. |
| Arbitrary tool enable/disable | `BLOCK_CONSUMER` | Never allow | Tool authority is not consumer command authority. |
| Arbitrary MCP reload | `BLOCK_CONSUMER` | Never allow | MCP/plugin controls are not consumer commands. |
| Unrestricted model/provider switching | `BLOCK_CONSUMER` | Never allow | Cost Governor and Model Router remain authorities. |
| Direct external platform handoff | `BLOCK_CONSUMER` | Never allow | External sends require approved channel and authority. |
| Any unverified raw Hermes command | `BLOCK_CONSUMER` | Never allow | Unknown commands default blocked. |

## Authority model

Zaubern-lite remains action authority.

Cost Governor remains spend and wake authority.

Memory Center remains canonical memory.

Model Router remains model selection authority within approved product tiers.

Scope Guard remains the boundary for allowed user intent.

Hermes remains runtime capability, not Roboticxs permission.

Agent Skills and plugin packages do not grant consumer authority by existing in a runtime.

## Approval command requirements

`/approve` and `/deny` must not approve sensitive actions by raw text alone.

Sensitive approvals require an Action Packet that includes:

- action id;
- user-visible action summary;
- actor and target;
- authority boundary;
- expected external effect;
- cost or wake implication when applicable;
- audit record location;
- safe fallback or denial outcome.

If an approval or denial references no Action Packet for a sensitive action, the consumer-safe result is blocked with a safe fallback explanation.

## Consumer language

Consumer-visible command labels use Roboticxs product terms:

- Routines, not `/cron`;
- Skill Packages or Habilidades, not raw `/skills` or `/bundles`;
- Economy / Balanced / Premium, not raw provider or model controls;
- Conversation history, not `/sessions`;
- Continue conversation, not `/resume`;
- Approved channel delivery, not direct platform handoff;
- Memory Center, not Hermes memory.

## Non-claims

- no live command routing;
- no runtime gateway changes;
- no production enforcement code;
- no MCP/plugin activation;
- no arbitrary tool enablement;
- no model-provider switching implementation;
- no UI;
- no 91P or later authorization.
