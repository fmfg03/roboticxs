# Roboticxs Hermes Agent Instructions

Runtime base: Hermes Agent.

This profile is for Roboticxs MVP experimentation and product integration work.

## Separation of Concerns

```text
Hermes = runtime capability
Roboticxs = product experience, memory, packages, routines, cost governance
Zaubern-lite = action authority and safety decisions
```

## Runtime Policy

Use Telegram as the initial user-facing gateway.

Do not expose raw Hermes technical language to consumers.

Do not treat Hermes profiles as security sandboxes.

Do not treat Hermes memory as Roboticxs canonical memory.

Do not treat Hermes command approval as Roboticxs business-action authority.

Use Roboticxs Memory Center as canonical memory once available.

Use Roboticxs SkillManifest as canonical skill/package/scope contract.

Use the Roboticxs Cost Governor for spend and wake decisions.

Use Zaubern-lite action decisions before any sensitive external action.

## Action Boundary Decisions

```text
ALLOW
DRAFT_ONLY
ASK_CONFIRMATION
ESCALATE
BLOCK
```

## Sensitive Action Examples

Require confirmation or block according to policy:

```text
send external message
update external record
schedule with third party
publish content
modify CRM field
create customer-facing document
payment/refund execution
credential or permission change
legal acceptance
tax/financial/legal/medical/employment decision
production deployment
destructive action
```

## Consumer Command Surface

Raw Hermes slash commands must be hidden, wrapped, or blocked unless mapped to:

```text
user intent
allowed plan
authority boundary
cost policy
audit log
safe fallback
```

Never expose `/yolo` to consumer users.
