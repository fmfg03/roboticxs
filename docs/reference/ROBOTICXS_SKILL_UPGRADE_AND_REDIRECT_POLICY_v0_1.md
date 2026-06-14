# Roboticxs Skill Upgrade and Redirect Policy v0.1

Status: 91P implemented pending review.

This document defines when Skill Activation Scope Guard returns `REDIRECT`, `OFFER_UPGRADE`, `REFUSE_SCOPE`, `CLARIFY`, or `BLOCK` around skill boundaries. It is a reference contract only and does not implement routing, subscriptions, billing, payments, gateway behavior, or UI.

## Redirect policy

Return `REDIRECT` when all are true:

- the active skill should not answer the request;
- another enabled Roboticxs skill is the correct owner;
- the target skill's SkillManifest allows the topic/action class;
- no prohibited topic or blocked action class applies;
- the user plan already includes the target skill.

Redirect copy must name the target product skill, not raw Hermes or Agent Skills internals.

Example: Customer Support receives "What is JSON?" while Technical Help is enabled. Decision: `REDIRECT`.

## Upgrade policy

Return `OFFER_UPGRADE` when all are true:

- the request belongs to a disabled paid skill or unavailable package;
- the relevant package has an approved upgrade path in SkillManifest;
- the request is not prohibited or sensitive without authority;
- no enabled skill can handle it.

Upgrade copy must not claim that Roboticxs can already perform the paid-skill task. It may say the feature is available through an upgrade path when that path exists.

Example: Marketing Pack is disabled and the user asks for a content calendar. Decision: `OFFER_UPGRADE`.

## Clarification policy

Return `CLARIFY` when the active skill likely owns the request but key details are missing.

Clarification is required for:

- missing document, lead, customer, recipient, channel, date, amount, or target;
- ambiguous "send it now" style requests;
- missing Action Packet reference for a sensitive action where a draft or clarification may still be safe;
- unclear plan/package state.

Clarification must not execute an external action.

## Refusal policy

Return `REFUSE_SCOPE` when the request is safe but outside the active skill and no enabled redirect or upgrade path applies.

Refusal must include a safe fallback that names what the active skill can help with.

Example: Customer Support receives "What is JSON?" and Technical Help is not enabled. Decision: `REFUSE_SCOPE`.

## Block policy

Return `BLOCK` when the request is prohibited, sensitive without valid authority, or listed in SkillManifest blocked topics/actions.

Blocked examples include:

- legal signing or legal acceptance;
- executing payments;
- refunds without authority;
- credential or permission changes;
- destructive actions;
- medical, medication, diagnosis, treatment, dosage, or emergency triage decisions;
- external sends without Action Packet authority when no safe clarification path applies.

Caregiver medication ambiguity returns `BLOCK` with escalation fallback to a caregiver, clinician, or emergency service as appropriate. `ESCALATE` is not a standalone 91P decision; escalation is response guidance attached to `BLOCK`.

## Authority preservation

Zaubern-lite remains authority for external/business actions.

Memory Center remains canonical memory.

Cost Governor remains spend/wake authority.

SkillManifest remains canonical for upgrade paths and redirect ownership.

Agent Skills `description` and Hermes activation state cannot convert disabled scope into active permission.

## Non-claims

- no subscription or payment implementation;
- no runtime redirect;
- no gateway changes;
- no production enforcement code;
- no Tool Authority Guard;
- no UI;
- no 92P or later authorization.
