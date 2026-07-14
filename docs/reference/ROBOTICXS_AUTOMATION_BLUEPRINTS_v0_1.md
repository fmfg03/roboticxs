# Roboticxs Automation Blueprints v0.1

Status: 89P implemented pending review.

This document defines Roboticxs Automation Blueprints as user-installable routine templates. It is story/spec/test work only. It does not implement live Hermes cron execution, a production scheduler, gateway changes, actual MCP activation, plugin activation, connector activation, or UI.

## Purpose

Automation Blueprints give users installable starting points for recurring `Routine` definitions on top of Hermes runtime capability, Agent Skills packaging, cron-style scheduling concepts, and the 88P Routine Wake Gate.

The user-facing product object is `Routine`, not `cron job`.

Automation Blueprints are installable routine templates, not silently scheduled jobs.

## Contract

Every blueprint must declare:

- name;
- description;
- package;
- inputs;
- schedule policy;
- source authorization;
- wake policy;
- skill binding;
- model/budget policy;
- delivery target;
- authority boundary;
- memory sink policy;
- confirmation behavior.

Every recurring blueprint must reference the 88P wake-gate policy where feasible.

No blueprint schedules silently.

No blueprint writes canonical Roboticxs Memory Center directly.

No blueprint sends external messages without confirmation.

Blueprint outputs may create `ProposedMemory` candidates, but never canonical memory automatically.

## Required blueprint manifest fields

```json roboticxs-blueprint-manifest-v0
{
  "name": "string",
  "description": "string",
  "package": "string",
  "inputs": [],
  "schedule_policy": {
    "type": "USER_CONFIGURED",
    "silent_install": false
  },
  "source_authorization": "USER_GRANTED_SOURCES_ONLY",
  "wake_policy": "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE",
  "skill_binding": "string",
  "model_budget_policy": "REQUIRED_BEFORE_AGENT_WAKE",
  "delivery_target": "USER_CONFIRMED_TARGET",
  "authority_boundary": "ZAUBERN_LITE_PLUS_HUMAN_CONFIRMATION_FOR_SENSITIVE_ACTIONS",
  "memory_sink_policy": "PROPOSED_MEMORY_ONLY_NO_CANONICAL_AUTO_WRITE",
  "confirmation_behavior": "CONFIRM_BEFORE_EXTERNAL_OR_SENSITIVE_EFFECT"
}
```

## Initial blueprint examples

The 89P initial examples are:

- `roboticxs-daily-brief`;
- `roboticxs-research-radar`;
- `roboticxs-caregiver-routine`.

These examples are portable skill-template packages under `runtime/hermes/skills/`. They are not installed into a live scheduler, not wired to a gateway, not connected to MCP or plugins, and not product UI.

## Architecture roles

Hermes remains runtime capability.

Agent Skills remains portable packaging.

Roboticxs SkillManifest remains product/package/scope authority.

Zaubern-lite remains action authority.

Routine remains the user-facing product object.

## Non-claims

- no live Hermes cron execution;
- no production scheduler;
- no gateway changes;
- no actual MCP/plugin/connector activation;
- no UI;
- no silent schedule creation;
- no direct canonical Memory Center writes;
- no 90P or later authorization.
