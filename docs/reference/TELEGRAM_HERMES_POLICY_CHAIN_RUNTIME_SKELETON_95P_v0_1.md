# Telegram-Hermes Policy Chain Runtime Skeleton 95P v0.1

Status: 95P implemented pending review.

This stage implements a deterministic local runtime skeleton for the Telegram-to-Hermes policy chain created by 90P through 93P and framed by 94P. It does not implement caregiver behavior, live Telegram sends, live Hermes Gateway startup, live cron scheduling, connector activation, external writes, payments, publishing, browser/email/WhatsApp execution, production credentials, or external side effects.

## Purpose

95P proves that a Telegram webhook/input can execute the Roboticxs policy chain before any Hermes runtime capability is allowed to respond.

Required local path:

Telegram -> command policy -> skill scope policy -> tool authority policy -> memory projection policy -> Action Packet binding -> Hermes Gateway adapter stub -> local response

The Hermes Gateway adapter is a deterministic local stub. It does not start Hermes, call a provider, open a socket, call Telegram, activate tools, execute connectors, schedule cron jobs, or perform external actions.

## Runtime Contract

The 95P runtime path is `POST /api/telegram/policy-chain/webhook`.

The path must:

- parse Telegram text input locally;
- apply 90P Command Surface Policy;
- apply 91P Skill Activation Scope Guard;
- apply 92P Tool Authority Guard;
- project approved scoped Memory Center records as non-authority context under 93P;
- produce a local Action Packet object when Tool Authority Guard returns `ASK_CONFIRMATION`;
- block raw Hermes commands unless explicitly mapped by 90P;
- stop blocked and approval-required actions before the Hermes adapter stub;
- expose an inspectable policy trace in tests and local response objects.

## Required Safety Invariants

- no network calls;
- no live Telegram sends;
- no live Hermes Gateway startup;
- no live Hermes process startup;
- no production credential use;
- no external side effects;
- no connector activation;
- no live cron scheduling;
- no caregiver runtime behavior;
- no payments, publishing, browser/email/WhatsApp execution, or external writes;
- blocked actions must not produce Action Packets;
- blocked actions must not reach the Hermes adapter stub;
- Action Packet confirmation references are bound locally but do not execute an external effect in 95P;
- memory projection is scoped, bounded, non-authority context only.

## Local Response Packet

```json telegram-hermes-policy-chain-runtime-skeleton-95p
{
  "packet_type":"TelegramHermesPolicyChainRuntimeSkeleton",
  "status":"LOCAL_RUNTIME_SKELETON",
  "stage":"95P",
  "webhook_path":"/api/telegram/policy-chain/webhook",
  "command_policy_required":true,
  "skill_scope_policy_required":true,
  "tool_authority_policy_required":true,
  "memory_projection_policy_required":true,
  "action_packet_required_for_ask_confirmation":true,
  "blocked_actions_reach_adapter":false,
  "approval_required_actions_reach_adapter":false,
  "hermes_gateway_adapter":"deterministic_local_stub",
  "network_calls_authorized":false,
  "telegram_send_authorized":false,
  "live_hermes_gateway_start_authorized":false,
  "external_side_effects_authorized":false,
  "future_stage_authorized":false
}
```

## Closeout Packet

```json telegram-hermes-policy-chain-runtime-skeleton-95p-closeout
{
  "stage":"95P",
  "stage_name":"Telegram-Hermes Policy Chain Runtime Skeleton v0",
  "implementation_status":"IMPLEMENTED_PENDING_REVIEW",
  "scope_completed":[
    "local Telegram policy-chain webhook",
    "90P command policy runtime decision",
    "91P skill scope runtime decision",
    "92P tool authority runtime decision",
    "93P scoped Memory Center projection",
    "local Action Packet generation for ASK_CONFIRMATION",
    "deterministic Hermes Gateway adapter stub",
    "inspectable policy trace"
  ],
  "blocked_scope_preserved":[
    "caregiver behavior",
    "live Telegram sends",
    "live Hermes Gateway startup",
    "live cron scheduling",
    "connector activation",
    "external writes",
    "payments",
    "publishing",
    "browser/email/WhatsApp execution",
    "production credentials"
  ],
  "commit_authority":"commit only after tests pass and artifacts remain untracked"
}
```

## Non-Claims

- no production Telegram runtime;
- no live Hermes Gateway integration;
- no live provider/model execution;
- no external action execution;
- no connector, MCP, plugin, browser, email, WhatsApp, payment, publishing, or cron activation;
- no caregiver runtime behavior;
- no 96P or later authorization.
