# Roboticxs Hermes Raw Command Blocklist v0.1

Status: 90P implemented pending review.

This document defines the initial raw Hermes command blocklist for consumer exposure. It is a reference contract only and does not implement runtime enforcement, gateway interception, plugin activation, MCP activation, or UI.

## Default rule

Any raw Hermes command not explicitly mapped by the 90P command surface policy defaults to `UNKNOWN_UNVERIFIED` and is blocked from consumer exposure.

Unknown is not safe. Unknown is blocked until a later approved stage classifies the command with user intent, allowed plan, authority boundary, cost policy, audit log, and safe fallback.

## Blocked consumer commands and surfaces

| Raw surface | Consumer policy | Reason |
| --- | --- | --- |
| `/yolo` | `BLOCK_CONSUMER` | Dangerous bypass behavior is never consumer-visible. |
| Dangerous command approvals without Action Packet | `BLOCK_CONSUMER` | Sensitive actions require Zaubern-lite Action Packets. |
| Arbitrary tool enable/disable | `BLOCK_CONSUMER` | Tool authority is not consumer authority. |
| Arbitrary MCP reload | `BLOCK_CONSUMER` | MCP lifecycle control is operator-only. |
| Unrestricted model/provider switching | `BLOCK_CONSUMER` | Model Router and Cost Governor remain authorities. |
| Direct external platform handoff | `BLOCK_CONSUMER` | External sends require approved channel and authority. |
| Any unverified raw Hermes command | `BLOCK_CONSUMER` | Unclassified commands default blocked. |

## Operator-only raw commands

These raw commands and controls are not consumer-visible. They may be operator/admin surfaces only in a future approved operator flow:

- `/config`;
- `/reload`;
- `/reload-mcp`;
- `/plugins`;
- browser connect controls;
- `/toolsets`;
- `/debug`;
- `/profile`;
- `/platforms`;
- `/gateway`;
- `/codex-runtime`;
- `/branch`;
- `/rollback`.

## Wrapped-only raw commands

These raw commands must not be shown as raw Hermes commands to consumers. They require Roboticxs wrappers:

- `/cron` as Roboticxs Routines;
- `/skills` as Habilidades / Skill Packages;
- `/bundles` as Skill Packages;
- `/model` as Economy / Balanced / Premium;
- `/handoff` as approved channel send/delivery;
- `/personality` as approved modes;
- `/sessions` as conversation history;
- `/resume` as continue conversation.

## Action Packet requirement

Raw approval text is not enough for sensitive actions.

Approving or denying a sensitive action without an Action Packet is consumer-blocked even if the underlying runtime could technically accept a command.

## Non-claims

- no gateway interception;
- no command parser changes;
- no live enforcement;
- no plugin or MCP activation;
- no model-provider switching implementation;
- no UI;
- no 91P or later authorization.
