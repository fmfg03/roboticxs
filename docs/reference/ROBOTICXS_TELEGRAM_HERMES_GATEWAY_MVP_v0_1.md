# Roboticxs Telegram Hermes Gateway MVP v0.1

Status: 94P implemented pending review.

This document defines the Telegram MVP on Hermes Gateway contract. It is story/spec/test work only. It does not start a live Hermes gateway, add real Telegram credentials, activate production messaging, implement full runtime integration, or add UI.

## Purpose

Telegram is the MVP user-facing channel for Roboticxs.

Hermes Gateway is runtime capability, not the product UX. Consumer users must see the Roboticxs command surface and approval model, not raw Hermes gateway commands or operator controls.

94P defines how Telegram messages may enter a future Hermes Gateway backed runtime while preserving:

- Roboticxs Command Surface Policy from 90P;
- Skill Activation Scope Guard from 91P;
- Hermes Tool Authority Guard from 92P;
- Roboticxs Memory Center Bridge from 93P;
- Routine Wake Gate from 88P;
- Roboticxs Automation Blueprints from 89P;
- Action Packet confirmation before sensitive actions.

## MVP contract

Inbound Telegram text is treated as user intent, not gateway authority.

The future gateway adapter must normalize each Telegram message into a Roboticxs request envelope before any Hermes runtime capability sees it.

The request envelope must preserve:

- Telegram channel identity;
- user or chat identity without committing secrets;
- message text or command alias;
- reply target or Action Packet reference when present;
- active skill or routine context when present;
- memory projection request scope;
- audit metadata needed for policy decisions.

The request envelope must not include Telegram bot tokens, bot secrets, webhook URLs, production config, session cookies, or credential material.

## Required decision order

1. Accept Telegram as the MVP channel input.
2. Normalize raw Telegram message text into Roboticxs product intent.
3. Apply 90P Command Surface Policy before exposing or forwarding any command.
4. Block raw Hermes operator, gateway, MCP/plugin, toolset, debug, config, reload, and bypass commands from consumer users.
5. Apply 91P Skill Activation Scope Guard for skill-bound requests.
6. Apply 93P Memory Center Bridge only as bounded memory projection context.
7. Apply 88P wake-gate and 89P blueprint boundaries for routine-related messages.
8. Apply 92P Tool Authority Guard before any tool/action proposal.
9. Produce a visible Action Packet for every confirmable sensitive action.
10. Require `/approve` or `/deny` equivalents to reference one specific Action Packet.
11. Block any external send, write, publish, payment, or destructive action unless policy and confirmation both pass.

## TelegramHermesGatewayMvpPacket schema

```json telegram-hermes-gateway-mvp-packet
{
  "packet_type":"TelegramHermesGatewayMvpPacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"94P",
  "user_channel":"Telegram",
  "runtime_capability":"Hermes Gateway",
  "product_surface":"Roboticxs Command Surface Policy",
  "raw_hermes_commands_exposed_to_consumers":false,
  "command_surface_policy_required":true,
  "skill_scope_guard_required":true,
  "tool_authority_guard_required":true,
  "memory_center_bridge_required":true,
  "routine_wake_gate_required":true,
  "action_packet_required_for_sensitive_actions":true,
  "telegram_credentials_committed":false,
  "runtime_gateway_start_authorized":false,
  "production_messaging_authorized":false,
  "future_stage_authorized":false
}
```

## Allowed 94P outputs

- documentation of the Telegram MVP on Hermes Gateway contract;
- documentation of gateway boundaries and approval flows;
- tests that assert the contract and roadmap status;
- canonical roadmap update marking 94P as `IMPLEMENTED_PENDING_REVIEW`.

## Non-claims

- no live Hermes Gateway startup;
- no Telegram token, bot secret, credential, webhook URL, or production config;
- no production messaging;
- no real Telegram API sends;
- no full runtime integration;
- no UI;
- no external send/write/publish/payment/destructive execution;
- no 95P or later authorization.
