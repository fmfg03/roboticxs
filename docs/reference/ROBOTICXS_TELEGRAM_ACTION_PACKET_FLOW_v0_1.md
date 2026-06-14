# Roboticxs Telegram Action Packet Flow v0.1

Status: 94P implemented pending review.

This document defines how Telegram confirmations must bind to Action Packets when Hermes Gateway capability is used behind Roboticxs. It is story/spec/test work only and does not implement approval command routing, packet rendering, connector activation, or external action execution.

## Purpose

Sensitive actions requested from Telegram must produce visible Action Packets before confirmation.

`/approve` and `/deny` equivalents must be tied to a specific Action Packet. A bare approval, ambiguous reply, emoji reaction, or command without packet identity must not execute a sensitive action.

## Sensitive action rule

No external send, external write, publish, third-party schedule, CRM modification, visual signature, payment, refund, credential change, permission change, legal acceptance, production deploy, destructive action, or professional decision may execute from Telegram without policy and confirmation.

92P Tool Authority Guard remains the classifier. `ASK_CONFIRMATION` must produce an Action Packet. `BLOCK` must not be converted into an Action Packet unless a future explicitly authorized policy changes the block default.

Payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions remain blocked in v0.

## Telegram confirmation flow

1. Telegram user requests an action.
2. 90P Command Surface Policy normalizes the message into a Roboticxs product intent.
3. 91P Skill Activation Scope Guard checks active skill scope.
4. 92P Tool Authority Guard classifies the proposed action.
5. If the decision is `ALLOW`, only safe local behavior may continue.
6. If the decision is `DRAFT_ONLY`, no external effect may execute.
7. If the decision is `ASK_CONFIRMATION`, render a visible Action Packet in Telegram.
8. The user must approve or deny by referencing the packet id or replying in a way that unambiguously binds to one active packet.
9. The confirmation must match the same actor, chat, packet id, proposed action, target, and current packet state.
10. Expired, superseded, hidden, truncated, or ambiguous packets cannot be approved.

## Action packet visibility

Telegram-rendered Action Packets must show the final content or fields that would be sent, written, published, scheduled, or placed. A summary is not enough for external sends, writes, publishing, CRM updates, schedules, or visual signatures.

## TelegramActionPacketFlow schema

```json telegram-action-packet-flow
{
  "packet_type":"TelegramActionPacketFlow",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"94P",
  "channel":"Telegram",
  "action_packet_policy":"ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1",
  "tool_authority_policy":"ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1",
  "confirmation_requires_specific_packet":true,
  "bare_approve_executes_sensitive_action":false,
  "bare_deny_closes_sensitive_action":false,
  "hidden_or_truncated_content_valid":false,
  "blocked_actions_convert_to_packets":false,
  "external_effect_without_confirmation_authorized":false,
  "runtime_execution_authorized":false
}
```

## Non-claims

- no approval command implementation;
- no packet renderer implementation;
- no connector activation;
- no Telegram send/write execution;
- no payment, credential, legal, deploy, destructive, or professional action execution;
- no 95P or later authorization.
