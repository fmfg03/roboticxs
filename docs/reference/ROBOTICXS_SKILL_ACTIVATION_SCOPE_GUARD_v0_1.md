# Roboticxs Skill Activation Scope Guard v0.1

Status: 91P implemented pending review.

This document defines the Skill Activation Scope Guard contract. It is story/spec/test work only. It does not implement live runtime routing, gateway changes, production enforcement code, payment/subscription logic, Tool Authority Guard, or UI.

## Purpose

The Skill Activation Scope Guard decides whether a user request should be answered by the active skill, clarified, redirected to another enabled skill, offered as an upgrade, refused as out of scope, or blocked as prohibited.

It prevents an active role skill from becoming a general chatbot, prevents disabled paid packages from pretending to exist, and preserves product authority boundaries when Hermes or Agent Skills can technically load a skill.

## Decision vocabulary

`ANSWER`: The request fits the active enabled skill package, allowed topics, allowed actions, plan, confirmation, cost, and safety boundaries.

`CLARIFY`: The request appears in scope but lacks necessary context, target, document, recipient, permission, or action detail.

`REDIRECT`: The request belongs to another enabled Roboticxs skill package.

`OFFER_UPGRADE`: The request belongs to a disabled or unavailable paid skill/package and may be offered as an upgrade path without claiming capability.

`REFUSE_SCOPE`: The request is outside the active skill scope and is not dangerous. Return a safe fallback in product language.

`BLOCK`: The request is prohibited, sensitive without authority, or belongs to a blocked topic/action class. Block or defer to Zaubern-lite authority rules where appropriate.

## Authority invariants

Roboticxs SkillManifest remains canonical for scope, package, plan, confirmation, blocked actions, escalation, fallback, and upgrade paths.

Agent Skills `description` helps discovery but does not decide authority.

Hermes skill activation is runtime capability, not product permission.

A skill may answer only if the user request fits enabled package scope and allowed topics/actions.

A skill must not answer general chatbot questions while operating inside a role skill unless the General Assistant skill is active.

Disabled paid-skill requests must return `OFFER_UPGRADE`, not fake capability.

Requests belonging to another enabled skill must return `REDIRECT`.

Ambiguous in-scope requests must return `CLARIFY`.

Out-of-scope but non-dangerous requests must return `REFUSE_SCOPE` with safe fallback.

Prohibited/sensitive actions must return `BLOCK` or defer to Zaubern-lite authority rules.

Scope Guard does not replace Tool Authority Guard. Tool Authority Guard comes later in 92P.

Memory Center remains canonical memory.

Cost Governor remains spend/wake authority.

## Scope decision algorithm

The future runtime decision order must preserve this precedence:

1. Check explicit prohibited topics and blocked action classes from SkillManifest. Return `BLOCK`.
2. Check whether a sensitive action requires Zaubern-lite or an Action Packet. Return `BLOCK` or `CLARIFY` according to the authority state.
3. Check whether the active skill is enabled for the user plan and package. If disabled but available as paid skill, return `OFFER_UPGRADE`.
4. Check whether the request belongs to another enabled skill. Return `REDIRECT`.
5. Check whether the request fits the active skill allowed topics and allowed action classes. Return `ANSWER`.
6. Check whether the request is likely in scope but missing key details. Return `CLARIFY`.
7. For safe but out-of-scope requests, return `REFUSE_SCOPE` with fallback.

## SkillActivationScopePacket schema

```json skill-activation-scope-packet
{
  "packet_type":"SkillActivationScopePacket",
  "status":"NON_RUNTIME_GOVERNANCE_PACKET",
  "stage":"91P",
  "active_skill_id":"documents_review",
  "active_package":"documents",
  "request_summary":"Summarize this uploaded PDF.",
  "enabled_skill_ids":["documents_review","sales_assistant"],
  "disabled_skill_ids":["marketing_pack"],
  "decision":"ANSWER",
  "decision_reason":"Request matches enabled Documents skill allowed topics and allowed SUMMARIZE action.",
  "authority_source":"Roboticxs SkillManifest",
  "requires_clarification":false,
  "requires_upgrade":false,
  "requires_action_packet":false,
  "safe_fallback":"I can help summarize the document, but I cannot sign it or provide legal advice.",
  "runtime_enforcement_authorized":false
}
```

## Example cases

| Active skill | Request | Condition | Decision |
| --- | --- | --- | --- |
| Customer Support | What is JSON? | Technical Help is not enabled | `REFUSE_SCOPE` |
| Customer Support | What is JSON? | Technical Help is enabled | `REDIRECT` |
| Documents | Summarize this PDF | Document summary within enabled package | `ANSWER` |
| Documents | Sign this contract legally for me | Legal acceptance/signature authority requested | `BLOCK` |
| Sales | Draft a follow-up to this lead | Drafting within Sales package | `ANSWER` |
| Sales | Send it now | Missing recipient/channel/Action Packet authority | `CLARIFY` |
| Marketing Pack | Make a content calendar | Marketing Pack disabled | `OFFER_UPGRADE` |
| Finance/Admin | Execute payment | Payment execution requested | `BLOCK` |
| Caregiver | Should I change the medication dose? | Medication ambiguity or medical decision | `BLOCK` |

## Non-claims

- no live runtime routing;
- no gateway changes;
- no production enforcement code;
- no payment/subscription logic;
- no Tool Authority Guard;
- no UI;
- no 92P or later authorization.
