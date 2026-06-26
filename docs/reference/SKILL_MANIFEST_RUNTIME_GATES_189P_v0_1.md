# Skill Manifest Runtime Gates 189P v0.1

Status: 189P implemented pending review.

## Purpose

189P adds a local, deterministic runtime gate that maps customer-facing Telegram commands to explicit Roboticxs product skills.

The gate gives the Telegram product surface a consistent way to say whether a request can be answered locally, needs clarification, belongs to another enabled skill, belongs to an unavailable package, is outside enabled scope, or must be blocked.

## Decisions

- `ANSWER`
- `CLARIFY`
- `REDIRECT`
- `OFFER_UPGRADE`
- `REFUSE_SCOPE`
- `BLOCK`

## Initial Skills

- Basic
- Setup
- Daily Brief
- Meetings
- Documents
- Memory
- Gmail Drafts
- Usage

Each skill declares commands, allowed local action classes, confirmation-required action classes, blocked action classes, upgrade paths, and a safe fallback.

## Runtime Boundary

189P does not authorize execution. It does not grant connector, model, tool, scheduler, billing, persistence, or external-write authority.

The gate always reports the following as disabled:

- external writes;
- connector activation;
- model calls;
- tool calls;
- Memory Center mutation;
- Calendar writes;
- Gmail send or modify;
- payments;
- destructive actions;
- professional legal, medical, tax, or financial decisions.

## Telegram Integration

Telegram `/help` and `/status` expose the active skill gate boundary. Unknown commands are classified through the gate before rendering the fallback command menu.

Existing command behavior remains local and owner-requested. 189P does not make unsupported commands executable.

## Non-claims

- no paid entitlement enforcement;
- no billing or subscription implementation;
- no dynamic LLM intent classification;
- no OAuth or connector activation;
- no Gmail send;
- no Calendar write;
- no Memory Center mutation;
- no file persistence;
- no deployment, push, merge, or PR creation.
