# Roboticxs Hermes Cron Routine Mapping v0.1

Status: 87P implemented pending review.

This document maps verified Hermes cron concepts to future Roboticxs Routine concepts. It does not implement cron execution, a scheduler, a wake gate, gateway delivery, blueprints, MCP/plugin activation, or no-agent execution.

## Contract

Hermes cron schedules work; Roboticxs Routine is the consumer product object.

Hermes cron is a runtime capability. A Roboticxs Routine is a product-level object that must carry user intent, authority state, confirmation state, delivery policy, budget/wake policy, and audit expectations.

Cron `[SILENT]` is not cost control.

`wakeAgent=false` and no-agent mode belong to 88P, not 87P implementation.

## Concept mapping

| Hermes cron surface | Future Roboticxs Routine surface | 87P rule |
| --- | --- | --- |
| job name | routine display name | Naming only. No routine persistence is implemented in 87P. |
| prompt | routine instruction body | Instruction text is not authority. |
| schedule | routine schedule | Scheduling is not execution authorization. |
| `skills` | routine skill references | Skill references require SkillManifest authority. |
| model/provider override | routine runtime preference | Runtime preference is subordinate to Model Router and Cost Governor. |
| delivery target | routine notification target | No send is authorized without Zaubern-lite and user confirmation. |
| `script` pre-run collection | routine input collector | External data collection is not authorized in 87P. |
| `no_agent=True` | future no-agent automation candidate | Deferred to 88P+ and not implemented here. |
| `[SILENT]` output prefix | delivery suppression hint | Suppresses delivery only; it does not prevent model spend or wake activity. |
| cron output storage | routine run audit candidate | Not canonical memory and not Memory Center. |

## Required future authority checks

A later implementation must check, before any external effect:

- Zaubern-lite authority.
- User confirmation for send/update/publish/payment/destructive actions.
- SkillManifest package, scope, plan, confirmation, blocked actions, and upgrade path.
- Cost Governor spend/wake authorization.
- Memory Center policy before any canonical memory write.
- Delivery target ownership and safety.

## 87P forbidden scope

87P does not authorize:

- running Hermes cron;
- creating Hermes cron jobs;
- enabling cron ticks;
- changing gateways or delivery paths;
- activating MCP servers, plugins, connectors, or online skill hubs;
- implementing blueprints;
- implementing wake gates;
- implementing `wakeAgent=false`;
- implementing Hermes `no_agent=True`;
- sending Telegram, email, browser, WhatsApp, webhook, payment, publish, or destructive actions;
- treating `[SILENT]` as cost control;
- treating Hermes memory as canonical Roboticxs Memory Center;
- authorizing 88P+.

## Product boundary

Hermes may schedule and run a job in upstream terms. Roboticxs must treat that as runtime capability only. The consumer product object is Routine, and Routine authority must come from Roboticxs layers, not from the existence of a Hermes job.
