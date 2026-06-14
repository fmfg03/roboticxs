# Roboticxs Telegram Memory Routine Flow v0.1

Status: 94P implemented pending review.

This document defines the Telegram memory and routine flow boundaries for the Hermes Gateway MVP contract. It is story/spec/test work only and does not implement live memory provider integration, production sync, scheduler execution, Telegram delivery, or UI.

## Purpose

Telegram requests routed through future Hermes Gateway capability must preserve the Memory Center Bridge and Routine Wake Gate boundaries.

Memory context may personalize, constrain, or enforce boundaries, but it must not authorize tools, external actions, spend, wake decisions, or permission expansion.

Routine requests may reference Hermes cron-style capability and Agent Skills packaging, but Roboticxs Routine remains the product object and the 88P/89P boundaries remain controlling.

## Memory flow

1. Treat Telegram text as a request for product intent, not memory authority.
2. Read candidate memory only from Roboticxs Memory Center.
3. Apply 93P MemoryProjectionPolicy for request scope, active skill, sensitivity, source, expiry, and allowed use.
4. Build a bounded MemoryContextBlock with non-authority metadata.
5. Preserve caregiver, medical, legal, financial, credential-like, safety-critical, stale, revoked, rejected, and inferred-memory constraints.
6. Do not write canonical memory from Hermes runtime output.
7. Treat runtime memory suggestions as ProposedMemory candidates for later explicit review only when an approved future path exists.

## Routine flow

1. Treat Telegram routine messages as Roboticxs Routine intents, not raw Hermes cron commands.
2. Apply 90P Command Surface Policy to block raw `/cron` exposure as consumer UX.
3. Apply 89P Automation Blueprint boundaries for installable templates.
4. Apply 88P Routine Wake Gate before agent wake.
5. Keep script-only/no-agent routines from invoking Model Router.
6. Keep `wakeAgent=false` at zero token expectation.
7. Require budget authority before any agent wake.
8. Require Tool Authority Guard and Action Packet confirmation before any external routine delivery or sensitive effect.

## Caregiver routine boundary

Caregiver Telegram routine flows must preserve human escalation boundaries. They may prepare drafts, checklists, or non-authoritative packets only when in scope. They must not decide medication changes, diagnose symptoms, monitor continuously, dispatch emergency services, or replace a caregiver, clinician, or responsible human.

## TelegramMemoryRoutineFlow schema

```json telegram-memory-routine-flow
{
  "packet_type":"TelegramMemoryRoutineFlow",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"94P",
  "channel":"Telegram",
  "memory_policy":"ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1",
  "routine_wake_policy":"ROBOTICXS_ROUTINE_WAKE_GATE_v0_1",
  "blueprint_policy":"ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1",
  "canonical_memory_source":"Roboticxs Memory Center",
  "hermes_memory_is_canonical":false,
  "memory_projection_authorizes_tools":false,
  "raw_cron_exposed_to_consumers":false,
  "wake_agent_false_token_expectation":0,
  "external_routine_delivery_without_confirmation":false,
  "caregiver_human_escalation_required":true,
  "runtime_scheduler_authorized":false,
  "production_messaging_authorized":false
}
```

## Non-claims

- no live Hermes memory provider integration;
- no production memory sync;
- no canonical memory writes;
- no scheduler execution;
- no Telegram routine delivery;
- no UI;
- no caregiver monitoring or emergency handling runtime;
- no 95P or later authorization.
