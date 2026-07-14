# Roboticxs Action Packet Contract v0.1

Status: 92P implemented pending review.

This document defines the Action Packet contract required when Tool Authority Guard returns `ASK_CONFIRMATION`. It is documentation/spec/test work only and does not implement packet rendering, command routing, gateway changes, connector activation, or external action execution.

## Purpose

An Action Packet is the user-visible approval artifact for a proposed external send, external write, publish, third-party schedule, CRM modification, visual signature, or other confirmable sensitive action.

Every `ASK_CONFIRMATION` must produce an Action Packet before any execution. A confirmation command without an Action Packet is not enough.

## Required fields

Action Packets must include:

- `action`: the exact proposed action class and plain-language action.
- `target`: recipient, external system, URL, record, calendar, CRM object, or publication destination.
- `data_to_be_changed_or_sent`: the complete data, content, fields, message body, attachment list, or schedule details that would be changed or sent.
- `risk_class`: the action class, sensitivity, reversibility, and external visibility.
- `source_context`: the user request, active skill, relevant source document or memory reference, and decision basis.
- `estimated_cost`: expected spend, token use, external fee, time cost, or unknown cost marker.
- `allowed_alternatives`: safer options such as draft only, copy-to-clipboard, manual checklist, or cancel.
- `confirmation_options`: explicit options such as confirm once, revise, draft only, cancel, or escalate.
- `audit_fields`: timestamp, actor, active skill, tool name, decision, policy version, packet id, and future execution receipt id.

No action packet may hide the final user-visible content for an external send/publish/write.

## ActionPacket schema

```json action-packet
{
  "packet_type":"ActionPacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"92P",
  "packet_id":"actpkt_example_001",
  "action":{
    "action_class":"SEND_EXTERNAL_MESSAGE",
    "plain_language":"Send the drafted follow-up email."
  },
  "target":{
    "type":"email_recipient",
    "identifier":"lead@example.com"
  },
  "data_to_be_changed_or_sent":{
    "subject":"Follow-up on Roboticxs demo",
    "body":"Hi Ana, thanks for the call. Here are the next steps we discussed.",
    "attachments":[]
  },
  "risk_class":{
    "external_visibility":"recipient_visible",
    "reversibility":"hard_to_retract",
    "sensitivity":"business_contact"
  },
  "source_context":{
    "user_request":"Send the follow-up to Ana.",
    "active_skill_id":"sales_followup",
    "decision_basis":"SEND_EXTERNAL_MESSAGE requires ASK_CONFIRMATION."
  },
  "estimated_cost":{
    "tokens":"bounded",
    "external_fee":"none_known",
    "unknown_cost":false
  },
  "allowed_alternatives":["DRAFT_ONLY","revise_content","cancel"],
  "confirmation_options":["confirm_once","revise","draft_only","cancel","escalate"],
  "audit_fields":{
    "created_at":"2026-06-14T00:00:00Z",
    "actor":"user",
    "active_skill_id":"sales_followup",
    "tool_name":"email.send",
    "tool_authority_decision":"ASK_CONFIRMATION",
    "policy_version":"ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1",
    "future_execution_receipt_id":null
  },
  "runtime_enforcement_authorized":false
}
```

## Packet rules

The full final message body, publishable content, external write fields, CRM modification, schedule details, or visual signature placement must be visible before confirmation.

If the final content is unknown, hidden, truncated, generated later, or represented only by a summary, the packet is invalid.

`ASK_CONFIRMATION` does not override `BLOCK`; blocked actions must not be converted into Action Packets unless a future explicitly authorized policy changes the block default.

Action Packets do not grant spend/wake authority. Cost Governor remains spend/wake authority.

Action Packets do not write memory. Memory Center remains canonical memory.

Action Packets do not replace Zaubern-lite. Zaubern-lite remains authority layer.

## Non-claims

- no runtime Action Packet renderer;
- no approval command implementation;
- no external execution;
- no connector activation;
- no 93P or later authorization.
