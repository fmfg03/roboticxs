# Roboticxs Telegram Gateway Boundary v0.1

Status: 94P implemented pending review.

This document defines the Telegram and Hermes Gateway boundary for the 94P MVP contract. It is story/spec/test work only and does not implement live gateway routing, webhook registration, Telegram credentials, or production messaging.

## Boundary statement

Telegram is the consumer-facing channel.

Roboticxs is the product command surface.

Hermes Gateway is runtime capability behind the product boundary.

Raw Hermes commands must not be exposed directly to consumer Telegram users. Gateway, config, reload, debug, MCP/plugin, toolset, browser, provider/model, and bypass controls remain operator-only or blocked according to 90P Command Surface Policy.

## Consumer command boundary

Telegram messages may express Roboticxs product intents such as:

- Help;
- Status;
- Usage;
- Routines list;
- Skills list;
- Memory review;
- Stop;
- approve or deny a specific Action Packet.

Telegram messages must not expose raw Hermes operator language as the consumer UX.

Unknown Telegram commands and unverified raw Hermes commands default to blocked consumer exposure.

## Gateway authority boundary

Hermes Gateway capability does not grant:

- skill activation authority;
- tool execution authority;
- memory write authority;
- routine wake authority;
- spend authority;
- caregiver decision authority;
- external send/write/publish/payment/destructive authority.

The future gateway adapter may pass only normalized, policy-checked Roboticxs envelopes into Hermes runtime capability.

## Caregiver and group chat boundary

Caregiver Telegram flows must preserve human escalation boundaries. Medication ambiguity, dosage, missed dose, duplicate dose, side effects, contradictory caregiver context, emergency signals, or professional decisions must escalate or block according to caregiver and Tool Authority Guard boundaries.

Group chat support is allowed only as a documented boundary/spec in 94P. It does not authorize runtime group management, automatic invites, proactive group messages, monitoring, emergency dispatch, or production group relay.

Group chat envelopes must preserve chat identity, actor identity, message thread context, and Action Packet references without committing credentials or exposing private context to unauthorized participants.

## Boundary packet

```json telegram-gateway-boundary-packet
{
  "packet_type":"TelegramGatewayBoundaryPacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"94P",
  "consumer_channel":"Telegram",
  "runtime_layer":"Hermes Gateway",
  "product_command_surface":"Roboticxs",
  "raw_hermes_commands_consumer_visible":false,
  "unknown_commands_default":"BLOCK_CONSUMER",
  "group_chat_runtime_authorized":false,
  "caregiver_escalation_boundary_required":true,
  "credentials_allowed_in_repo":false,
  "runtime_enforcement_authorized":false
}
```

## Non-claims

- no live gateway routing;
- no Telegram webhook registration;
- no Telegram credentials or production config;
- no group chat runtime implementation;
- no caregiver monitoring or emergency handling runtime;
- no raw Hermes command exposure;
- no 95P or later authorization.
