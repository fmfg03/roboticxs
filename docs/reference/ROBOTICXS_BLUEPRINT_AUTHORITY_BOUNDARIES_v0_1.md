# Roboticxs Blueprint Authority Boundaries v0.1

Status: 89P implemented pending review.

This document defines authority boundaries for Roboticxs Automation Blueprints. It is documentation/spec/test work only and does not implement blueprint execution, scheduling, gateway behavior, connector activation, MCP activation, plugin activation, or UI.

## Authority model

Hermes remains runtime capability.

Agent Skills remains portable packaging.

Roboticxs SkillManifest remains product/package/scope authority.

Zaubern-lite remains action authority.

Human confirmation remains required for sensitive external effects.

## Prohibited blueprint actions

No blueprint may:

- schedule silently;
- write canonical Roboticxs Memory Center directly;
- send external messages without confirmation;
- execute payments;
- execute refunds;
- change credentials;
- change permissions;
- accept legal terms;
- run production deploys;
- perform destructive actions;
- perform legal decisions;
- perform medical decisions;
- perform tax decisions;
- perform financial decisions;
- perform employment decisions;
- perform identity decisions.

## Memory boundary

Blueprint outputs may create `ProposedMemory` candidates when the user has granted source and memory-proposal authority.

Blueprint outputs must never write canonical memory automatically.

Hermes memory remains runtime memory, not canonical Roboticxs Memory Center.

## Confirmation boundary

External sends, updates, publishing, payments, destructive operations, sensitive caregiver messages, and any permission-affecting action require Zaubern-lite authorization and human confirmation.

Instruction text inside an Agent Skill is not authority. A package existing under `runtime/hermes/skills/` is not installation, activation, scheduling, or permission to act.

## Non-claims

- no live execution;
- no cron creation;
- no scheduler;
- no gateway changes;
- no MCP/plugin/connector activation;
- no UI;
- no 90P or later authorization.
