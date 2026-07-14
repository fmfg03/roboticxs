# Roboticxs Hermes Profile Rebase v0.1

## Status

Stage 85P is implemented pending review.

This document records the Roboticxs Hermes profile boundary. It does not authorize staging, commit, 86P, `NEXT_ELIGIBLE`, or any Hermes runtime integration beyond the 85P profile baseline.

## Decision

Hermes Agent is the runtime substrate. Roboticxs remains the product layer.

The Roboticxs Hermes profile separates:

```text
Hermes = runtime capability
Roboticxs = product experience, memory, packages, routines, cost governance
Zaubern-lite = action authority and safety decisions
```

## Runtime Files

`runtime/hermes/SOUL.md` contains Robbie identity and style only.

`runtime/hermes/AGENTS.md` contains project/runtime instructions for the Roboticxs Hermes profile.

## Required Product-owned Layers

Roboticxs Memory Center remains the canonical memory layer.

Roboticxs SkillManifest remains the product/package/scope contract.

Roboticxs Cost Governor remains the spend and wake decision layer.

Zaubern-lite remains the action authority and safety decision layer.

## Hermes Boundary Rules

Hermes profiles are state isolation, not business authorization and not security sandboxing.

Hermes memory is runtime memory, not Roboticxs canonical memory.

Hermes command approval is not Roboticxs business-action authority.

Agent Skills package behavior and instructions; they do not replace Roboticxs package, scope, cost, or authority policy.

## Consumer Command Surface

No raw Hermes command is exposed to consumer users unless Roboticxs maps it to:

```text
user intent
allowed plan
authority boundary
cost policy
audit log
safe fallback
```

Raw Hermes technical language should be hidden, wrapped, or blocked for consumer users.

`/yolo` must never be exposed to consumer users.

## What Is Intentionally Not Implemented

- Hermes install automation
- Telegram gateway changes
- model routing changes
- tool interception
- automation blueprints
- memory center bridge
- payment or subscription logic
- UI
- 86P
- `NEXT_ELIGIBLE`

## Non-claims

85P is not a runtime integration stage.

85P is not a security certification.

85P is not a tool enforcement layer.

85P is not a Memory Center implementation.

85P is only the Roboticxs Hermes profile identity and boundary baseline.
