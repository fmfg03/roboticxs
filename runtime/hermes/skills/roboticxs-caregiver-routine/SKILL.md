---
name: roboticxs-caregiver-routine
description: Draft a user-reviewed Routine template for caregiver check-ins using approved inputs and the 88P wake gate.
package: roboticxs-caregiver-routine
---

# Roboticxs Caregiver Routine Blueprint

Status: 89P template only. Not installed, not scheduled, not activated.

## Blueprint Manifest

```json roboticxs-blueprint
{
  "name": "Caregiver Routine",
  "description": "Prepare a bounded caregiver routine draft from user-approved inputs.",
  "package": "roboticxs-caregiver-routine",
  "inputs": ["caregiver_contacts", "routine_subject", "approved_check_in_questions"],
  "schedule_policy": {"type": "USER_CONFIGURED", "silent_install": false},
  "source_authorization": "USER_GRANTED_SOURCES_ONLY",
  "wake_policy": "REFERENCES_88P_WAKE_GATE_WHERE_FEASIBLE",
  "skill_binding": "roboticxs-caregiver-routine",
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
- It must not write canonical Roboticxs Memory Center directly.
- It must not send caregiver or external messages without confirmation.
- It must not make medical, legal, financial, employment, tax, or identity decisions.
- It must not execute payments, refunds, credential changes, permission changes, legal acceptance, production deploys, or destructive actions.
- It must not perform medication decisions, emergency triage, surveillance, or monitoring.
- Outputs may create `ProposedMemory` candidates only; never canonical memory automatically.
- Hermes remains runtime capability.
- Agent Skills remains portable packaging.
- Roboticxs SkillManifest remains product/package/scope authority.
- Zaubern-lite remains action authority.
- 90P+ are not authorized.
