# Roboticxs Hermes Tool Authority Guard v0.1

Status: 92P implemented pending review.

This document defines the Hermes Tool Authority Guard contract. It is story/spec/test work only. It does not implement live Hermes interception, gateway changes, production enforcement code, MCP/plugin activation, connector activation, or UI.

## Purpose

The Hermes Tool Authority Guard classifies and gates proposed Hermes tool calls and external actions after skill activation but before execution.

It prevents Hermes tool availability, Agent Skills instructions, or active skill context from being mistaken for Roboticxs permission. It also defines when a proposed action can proceed locally, when it must become a draft only, when the user must confirm through an Action Packet, when human/professional escalation is required, and when the action must be blocked.

## Decision vocabulary

`ALLOW`: The proposed action is safe, local, within enabled scope, within budget, and does not change external state or require a sensitive authority path.

`DRAFT_ONLY`: The agent may prepare content, a checklist, or a proposed change, but must not send, publish, write, schedule, pay, delete, deploy, accept, or otherwise execute the action.

`ASK_CONFIRMATION`: The proposed action may affect external state or user-visible output and requires an Action Packet before any execution.

`ESCALATE`: The proposed action requires caregiver, clinician, legal, tax, financial, employment, operator, or other human review before any further action.

`BLOCK`: The proposed action is prohibited in v0 or lacks an explicitly authorized future policy.

## Authority invariants

Hermes tool availability is capability, not permission.

Agent Skills instructions are not authority.

Scope Guard does not authorize execution; it only decides skill participation.

Tool Authority Guard runs after skill activation and before any sensitive action.

Safe read/search/summarize/classify/draft actions may be `ALLOW` when within enabled scope and budget.

External sends, writes, publishing, third-party scheduling, CRM modification, and visual signatures require `ASK_CONFIRMATION` or stronger.

Payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions must default to `BLOCK` unless a future explicitly authorized policy says otherwise.

Medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradiction must `ESCALATE` or `BLOCK` under caregiver boundary.

Every `ASK_CONFIRMATION` must produce an Action Packet.

No action packet may hide the final user-visible content for an external send/publish/write.

Cost Governor remains spend/wake authority.

Memory Center remains canonical memory.

Zaubern-lite remains authority layer.

93P+ must remain not authorized.

## Decision order

1. Verify the active skill is enabled and in scope. If not, return to Scope Guard behavior.
2. Classify the proposed tool call or action using the 92P action-class registry.
3. Apply explicit v0 block defaults for payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions.
4. Apply caregiver escalation for medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradictory caregiver context.
5. Require `ASK_CONFIRMATION` and an Action Packet for external sends, external writes, publishing, third-party scheduling, CRM modification, or visual signatures.
6. Allow safe local read/search/summarize/classify/draft actions only when scope and budget permit.
7. Preserve Cost Governor, Memory Center, and Zaubern-lite authority boundaries.

## ToolAuthorityGuardPacket schema

```json tool-authority-guard-packet
{
  "packet_type":"ToolAuthorityGuardPacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"92P",
  "active_skill_id":"sales_followup",
  "proposed_action_class":"SEND_EXTERNAL_MESSAGE",
  "proposed_tool":"email.send",
  "target":"lead@example.com",
  "decision":"ASK_CONFIRMATION",
  "decision_reason":"External message delivery requires an Action Packet before execution.",
  "requires_action_packet":true,
  "action_packet_contract":"ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1",
  "runtime_enforcement_authorized":false,
  "future_stage_authorized":false
}
```

## Example cases

| Case id | Proposed action | Action class | Decision |
| --- | --- | --- | --- |
| `local_doc_summary` | Summarize uploaded PDF text for the user | `SUMMARIZE` | `ALLOW` |
| `draft_lead_followup` | Draft a follow-up email without sending | `DRAFT` | `ALLOW` |
| `send_lead_followup` | Send the drafted email to a lead | `SEND_EXTERNAL_MESSAGE` | `ASK_CONFIRMATION` |
| `write_crm_note` | Write a note into an external CRM | `WRITE_EXTERNAL_RECORD` | `ASK_CONFIRMATION` |
| `publish_social_post` | Publish approved social copy | `PUBLISH` | `ASK_CONFIRMATION` |
| `schedule_vendor_call` | Book a meeting with a third party | `SCHEDULE_WITH_THIRD_PARTY` | `ASK_CONFIRMATION` |
| `place_visual_signature` | Place a visible signature or stamp | `PLACE_VISUAL_SIGNATURE` | `ASK_CONFIRMATION` |
| `execute_payment` | Pay an invoice | `PAY` | `BLOCK` |
| `refund_customer` | Issue a refund | `REFUND` | `BLOCK` |
| `change_password` | Change a password | `CHANGE_CREDENTIALS` | `BLOCK` |
| `change_permissions` | Change user permissions | `CHANGE_PERMISSIONS` | `BLOCK` |
| `accept_contract` | Accept legal terms or sign legally | `LEGAL_ACCEPT` | `BLOCK` |
| `deploy_prod` | Deploy to production | `PRODUCTION_DEPLOY` | `BLOCK` |
| `delete_account` | Delete an account or record | `DESTRUCTIVE_ACTION` | `BLOCK` |
| `missed_medication_dose` | Decide what to do after a missed dose | `MEDICAL_DECISION` | `ESCALATE` |

## Non-claims

- no live Hermes interception;
- no gateway changes;
- no production enforcement code;
- no MCP/plugin activation;
- no connector activation;
- no UI;
- no live external action execution;
- no 93P or later authorization.
