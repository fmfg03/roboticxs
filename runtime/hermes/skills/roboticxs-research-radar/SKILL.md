---
name: roboticxs-research-radar
description: Draft a user-reviewed Routine template for a research radar using approved sources and the 88P wake gate.
package: roboticxs-research-radar
---

# Roboticxs Research Radar Blueprint

Status: 89P template only. Not installed, not scheduled, not activated.

## Blueprint Manifest

```json roboticxs-blueprint
{
  "name": "Research Radar",
  "description": "Prepare a bounded research update from user-approved sources.",
  "package": "roboticxs-research-radar",
  "inputs": ["approved_sources", "research_topics", "recency_window"],
  "schedule_policy": {"type": "USER_CONFIGURED", "silent_install": false},
  "source_authorization": "USER_GRANTED_SOURCES_ONLY",
  "wake_policy": "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE",
  "skill_binding": "roboticxs-research-radar",
  "model_budget_policy": "REQUIRED_BEFORE_AGENT_WAKE",
  "delivery_target": "USER_CONFIRMED_TARGET",
  "authority_boundary": "ZAUBERN_LITE_PLUS_HUMAN_CONFIRMATION_FOR_SENSITIVE_ACTIONS",
  "memory_sink_policy": "PROPOSED_MEMORY_ONLY_NO_CANONICAL_AUTO_WRITE",
  "confirmation_behavior": "CONFIRM_BEFORE_EXTERNAL_OR_SENSITIVE_EFFECT"
}
```

## Boundaries

- The user-facing product object is `Routine`, not `cron job`.
- This blueprint is an installable routine template, not a silently scheduled job.
- It must not schedule silently.
- It must not activate live retrieval, connectors, MCP servers, plugins, or external APIs.
- It must not write canonical Roboticxs Memory Center directly.
- It must not send external messages without confirmation.
- It must not execute payments, refunds, credential changes, permission changes, legal acceptance, production deploys, or destructive actions.
- It must not perform legal, medical, tax, financial, employment, or identity decisions.
- Outputs may create `ProposedMemory` candidates only; never canonical memory automatically.
- Hermes remains runtime capability.
- Agent Skills remains portable packaging.
- Roboticxs SkillManifest remains product/package/scope authority.
- Zaubern-lite remains action authority.
- 90P+ are not authorized.
