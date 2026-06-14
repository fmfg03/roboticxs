# Roboticxs Routine Wake Gate / Zero-Token Preflight v0.1

Status: 88P implemented pending review.

This document defines the Roboticxs Routine Wake Gate contract for recurring routines. It is story/spec/test work only. It does not implement live Hermes cron execution, runtime gateway changes, automation blueprints, production scheduling, MCP activation, plugin activation, connector activation, or external delivery.

## Purpose

Recurring routines must be able to determine whether there is meaningful change before waking an agent. The wake gate keeps cheap deterministic checks in scripts and reserves LLM work for bounded cases where judgment is actually required.

## Contract

Scripts detect.

Agents judge.

Zaubern-lite authorizes.

Humans confirm sensitive actions.

Every recurring routine must declare a wake policy and a budget policy before it can be considered valid.

`wakeAgent=false` means the LLM should not run and token usage should be zero.

`wakeAgent=true` may pass bounded context to an agent run.

No-agent/script-only routines never invoke Model Router.

`[SILENT]` suppresses delivery only. It is not cost control and must not be used as a substitute for `wakeAgent=false`, budget policy, or a wake decision.

## WakeDecision vocabulary

| Decision | Meaning |
| --- | --- |
| `SKIP_NO_CHANGE` | The script found no meaningful change. Do not wake the LLM. Token usage should be zero. |
| `SCRIPT_ONLY_ALERT` | The script found a deterministic non-sensitive alert that can be recorded or delivered without agent judgment, subject to delivery and authority policy. |
| `WAKE_AGENT` | The script found bounded context that needs agent judgment. Model routing may run only after budget and authority checks pass. |
| `BLOCK_BUDGET` | The routine is blocked by its declared budget policy. Do not wake the LLM. |
| `ESCALATE_AUTHORITY` | The routine requires authority escalation or human confirmation before any sensitive action. |
| `SCRIPT_ERROR` | The script failed or returned invalid output. Produce an observable error record. Do not silently retry through an agent. |

## Conceptual data model

| Object | Required meaning |
| --- | --- |
| `Routine` | Product-level recurring routine definition. It carries user intent, schedule reference, wake policy, budget policy, authority policy, source references, delivery target, and audit expectations. |
| `RoutineRun` | One attempted routine execution. It records preflight result, wake decision, budget outcome, authority outcome, token expectation, delivery disposition, and error state. |
| `RoutinePreflight` | Deterministic pre-agent evaluation produced from scripts and source fingerprints. |
| `WakeDecision` | Enumerated result from the preflight gate. |
| `RoutineScript` | Deterministic collection or comparison script. It may inspect approved sources and emit bounded structured output. |
| `RoutineSourceFingerprint` | Stable fingerprint of the observed source state, such as a file hash, HTTP ETag/content digest, external flag value, or timestamp plus digest. |
| `RoutineDeliveryTarget` | Declared output target. Delivery is separate from wake, cost, and authority. |
| `RoutineBudgetPolicy` | Declared spend and wake budget. It can block agent wake before Model Router runs. |
| `RoutineAuthorityPolicy` | Declared authority and confirmation policy for sensitive actions. |
| `RoutineOutput` | Structured result of the routine run, including user-visible content, internal audit content, errors, and non-claims. |

## Required preflight packet fields

```json routine-preflight-packet-v0
{
  "routine_id": "string",
  "run_id": "string",
  "wake_policy_id": "string",
  "budget_policy_id": "string",
  "authority_policy_id": "string",
  "wakeAgent": false,
  "decision": "SKIP_NO_CHANGE",
  "source_fingerprints": [],
  "bounded_context": null,
  "token_expectation": 0,
  "model_router_allowed": false,
  "delivery_suppressed": false,
  "requires_human_confirmation": false,
  "observable_error": null
}
```

When `wakeAgent=false`, `token_expectation` must be `0`, `model_router_allowed` must be `false`, and no agent prompt may be constructed.

When `wakeAgent=true`, `bounded_context` must be minimal, source-scoped, and safe to pass to an agent. The run still requires budget authorization before Model Router and authority checks before any external effect.

## Script boundaries

Routine scripts may:

- read approved local inputs or approved external metadata sources declared by the routine;
- compare current source fingerprints with prior source fingerprints;
- emit deterministic `RoutinePreflight` output;
- emit deterministic `SCRIPT_ONLY_ALERT` output for non-sensitive changes;
- emit observable `SCRIPT_ERROR` records.

Routine scripts must not:

- write directly to canonical Roboticxs Memory Center;
- write `ProposedMemory`;
- execute sensitive actions;
- send Telegram, email, browser, WhatsApp, webhook, payment, publishing, or destructive actions;
- invoke Model Router;
- invoke an LLM through any provider path;
- activate MCP servers, plugins, connectors, or online skill hubs;
- treat Hermes memory as canonical Roboticxs memory.

## Authority flow

1. Routine schedule selects a due routine.
2. The declared `RoutineScript` runs deterministic preflight.
3. The wake gate maps script output and policies to a `WakeDecision`.
4. Budget policy may return `BLOCK_BUDGET` before Model Router.
5. `wakeAgent=false` exits without agent wake and with zero token usage.
6. `wakeAgent=true` may pass bounded context to an agent only after budget policy allows it.
7. Zaubern-lite authorizes any external or sensitive effect.
8. Humans confirm send/update/publish/payment/destructive actions.

## Non-claims

- no live Hermes cron execution;
- no production scheduler;
- no runtime gateway change;
- no automation blueprint;
- no MCP/plugin/connector activation;
- no canonical Memory Center write path;
- no model routing implementation;
- no Telegram delivery implementation;
- no 89P or later authorization.
