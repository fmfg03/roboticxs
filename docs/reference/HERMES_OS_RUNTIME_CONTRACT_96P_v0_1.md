# Hermes OS Runtime Contract 96P v0.1

Status: 96P closed committed.

This stage defines deterministic local packet contracts for treating Hermes as a persistent OS-like runtime substrate for Roboticxs. It does not implement caregiver behavior, live Hermes startup, live Telegram sends, live cron execution, connector activation, model provider calls, auto skill install, production credentials, external writes, payments, publishing, browser/email/WhatsApp execution, or destructive actions.

## Purpose

95P proved a safe Telegram policy-chain entrypoint.

96P defines how Roboticxs represents runtime primitives when Hermes operates as the persistent substrate for goals, routines, skills, profiles, task execution, memory projection, and tool requests.

Hermes is runtime substrate, not authority layer.

All Hermes OS packets remain downstream of:

- command policy;
- skill scope policy;
- tool authority policy;
- memory projection policy;
- budget authority where applicable;
- Action Packet confirmation;
- blocked-action policy.

## Required Packets

`RobotConstitution`: identity and runtime role for a Roboticxs robot. It records that Hermes is substrate and Roboticxs policy chain is authority.

`GoalPacket`: normalized user goal bound to policy trace and requested tool classes. Goals requesting blocked tools must be blocked.

`RoutinePacket`: routine-shaped contract with wake and budget preflight placeholders. It does not authorize live cron, delivery, or model routing before budget.

`SkillActivationPacket`: active skill contract preserving Roboticxs SkillManifest as authority. Hermes skill activation does not grant permission.

`MemoryProjectionPacket`: bounded, scoped, non-authority projection from Roboticxs Memory Center into Hermes OS context.

`ToolRequestPacket`: proposed tool/action request after policy classification. Blocked requests and approval-required requests must not reach the Hermes adapter.

`ActionPacket`: binding to a 95P local Action Packet when `ASK_CONFIRMATION` is required. The binding cannot execute external effects.

`PolicyTrace`: complete inspectable trace of 90P command policy, 91P skill scope policy, and 92P tool authority policy when the request reaches tool authority.

`TaskRunRecord`: local runtime audit record for the deterministic contract. It cannot record live Hermes startup, network calls, or external side effects in 96P.

## Required Behavior

- raw Hermes commands cannot bypass the 95P policy-chain entrypoint;
- goal packets cannot request blocked tools unless the goal is blocked;
- routine packets require wake and budget preflight placeholders;
- skill activation respects manifest and scope boundaries;
- memory projection is bounded, scoped, and non-authority-expanding;
- tool requests requiring confirmation produce Action Packet output;
- blocked actions never reach the Hermes adapter;
- policy trace remains complete and inspectable;
- no external side effects occur.

## Contract Packet

```json hermes-os-runtime-contract-96p
{
  "packet_type":"HermesOSRuntimeContract",
  "status":"LOCAL_CONTRACT_LAYER",
  "stage":"96P",
  "runtime_role":"persistent_runtime_substrate",
  "hermes_is_authority":false,
  "required_packets":[
    "RobotConstitution",
    "GoalPacket",
    "RoutinePacket",
    "SkillActivationPacket",
    "MemoryProjectionPacket",
    "ToolRequestPacket",
    "ActionPacket",
    "PolicyTrace",
    "TaskRunRecord"
  ],
  "policy_chain_entrypoint_required":true,
  "blocked_actions_reach_adapter":false,
  "approval_required_actions_reach_adapter":false,
  "live_hermes_start_authorized":false,
  "live_cron_authorized":false,
  "live_telegram_send_authorized":false,
  "connector_activation_authorized":false,
  "model_provider_calls_authorized":false,
  "external_side_effects_authorized":false,
  "future_stage_authorized":false
}
```

## Closeout Packet

```json hermes-os-runtime-contract-96p-closeout
{
  "stage":"96P",
  "stage_name":"Hermes OS Runtime Contract v0",
  "implementation_status":"CLOSED_COMMITTED",
  "scope_completed":[
    "RobotConstitution",
    "GoalPacket",
    "RoutinePacket",
    "SkillActivationPacket",
    "MemoryProjectionPacket",
    "ToolRequestPacket",
    "ActionPacket binding",
    "PolicyTrace",
    "TaskRunRecord",
    "deterministic local contract tests"
  ],
  "blocked_scope_preserved":[
    "caregiver workflows",
    "live Hermes startup",
    "live cron execution",
    "live Telegram sends",
    "external tools/connectors",
    "model provider calls",
    "auto skill install",
    "production credentials",
    "external writes",
    "payments",
    "publishing",
    "browser/email/WhatsApp execution",
    "destructive actions"
  ],
  "commit_authority":"commit only after tests pass and artifacts remain untracked"
}
```

## Non-Claims

- no live Hermes startup;
- no live Gateway integration;
- no live cron execution;
- no live Telegram sends;
- no caregiver workflows;
- no connector, MCP, plugin, browser, email, WhatsApp, payment, publishing, or external-write execution;
- no model provider calls;
- no auto skill install;
- no production credentials;
- no 97P or later authorization.
