# Roboticxs Routine Cost Policy v0.1

Status: 88P implemented pending review.

This document defines the cost and wake policy contract for recurring routines. It is documentation/spec/test work only and does not implement provider billing, Model Router behavior, Hermes cron execution, or gateway changes.

## Purpose

Routine cost control must happen before agent wake. Delivery suppression, quiet mode, or `[SILENT]` output must never be treated as spend control.

## Contract

Every recurring routine must declare a `RoutineBudgetPolicy`.

Every recurring routine must declare a wake policy.

`wakeAgent=false` is the zero-token path. The LLM should not run, Model Router should not run, and token usage should be zero.

`wakeAgent=true` is not automatic spend approval. It means bounded context may be eligible for an agent run only after `RoutineBudgetPolicy` allows the wake.

`[SILENT]` suppresses delivery only. It does not prevent agent wake, Model Router use, provider calls, token usage, or spend.

## RoutineBudgetPolicy fields

```json routine-budget-policy-v0
{
  "policy_id": "string",
  "routine_id": "string",
  "max_agent_wakes_per_period": 0,
  "max_tokens_per_period": 0,
  "period": "day",
  "on_budget_exceeded": "BLOCK_BUDGET",
  "allow_script_only_runs_when_blocked": true,
  "requires_observable_budget_record": true
}
```

`BLOCK_BUDGET` means do not wake an agent, do not route a model, and record the blocked run.

Script-only detection may still run when budget is blocked if the routine policy permits it and the script has no sensitive effects.

## Cost decisions

| Condition | Required behavior |
| --- | --- |
| No meaningful source change | `SKIP_NO_CHANGE`, `wakeAgent=false`, zero token usage. |
| Deterministic non-sensitive alert | `SCRIPT_ONLY_ALERT`, no Model Router, zero token usage unless a later separately authorized agent step is requested. |
| Budget exhausted before agent wake | `BLOCK_BUDGET`, no Model Router, observable budget record. |
| Agent judgment needed and budget allows | `WAKE_AGENT`, bounded context only. |
| Sensitive action requested | `ESCALATE_AUTHORITY`, Zaubern-lite and human confirmation before effect. |
| Script failure | `SCRIPT_ERROR`, observable error record, no silent agent fallback. |

## Required accounting semantics

- A skipped no-change run records zero expected tokens.
- A no-agent/script-only run records zero expected tokens.
- A budget-blocked run records zero expected tokens for agent/model usage.
- A `WAKE_AGENT` run records the bounded context handed to the agent and the policy that allowed the wake.
- Silent delivery and token usage are separate fields.

## Forbidden cost-control shortcuts

- `[SILENT]` is not cost control.
- Delivery suppression is not cost control.
- Hermes cron scheduling is not cost control.
- Hermes `no_agent=True` is not Roboticxs authority by itself.
- Agent Skills packaging is not cost authority.
- Script success is not spend approval.

## Non-claims

- no provider execution;
- no billing integration;
- no subscription or payment behavior;
- no Model Router changes;
- no Token Counter changes;
- no production scheduler;
- no 89P or later authorization.
