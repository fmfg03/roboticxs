# 85P - Hermes Profile / Roboticxs SOUL Rebase v0.1

Status: approved technical spec for next eligible Roboticxs stage.

## Problem

Roboticxs now uses Hermes Agent as runtime substrate, but Roboticxs must not inherit Hermes' default identity, raw command surface, memory assumptions, or tool authority.

Hermes provides runtime capability. Roboticxs must define product identity and boundaries.

## Goal

Create a clean Roboticxs Hermes profile baseline with:

- `runtime/hermes/SOUL.md` - identity/style only.
- `runtime/hermes/AGENTS.md` - runtime/project instructions.
- Reference docs explaining the separation.
- Tests preventing scope drift.

## Non-goals

85P does not implement:

- Hermes install automation,
- Telegram gateway,
- actual model routing,
- actual tool interception,
- automation blueprints,
- memory center bridge,
- payment/subscription logic,
- UI.

## Required Files

```text
runtime/hermes/SOUL.md
runtime/hermes/AGENTS.md
docs/reference/ROBOTICXS_HERMES_SOUL_v0_1.md
docs/reference/ROBOTICXS_HERMES_PROFILE_REBASE_v0_1.md
tests/test_hermes_soul_contract.py
tests/test_hermes_profile_boundary.py
```

Update:

```text
docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md
tests/test_canonical_roadmap.py
```

## SOUL Contract

`SOUL.md` may include:

- identity,
- tone,
- communication style,
- uncertainty behavior,
- proactive behavior,
- refusal style,
- high-level behavioral boundaries.

`SOUL.md` must not include:

- repo paths,
- commands,
- ports,
- deployment notes,
- roadmap stages,
- coding conventions,
- Hermes config keys,
- API keys,
- provider names,
- detailed workflow instructions,
- raw command-surface policy,
- fake enforcement claims.

## Required Identity

Robbie is:

- a personal AI robot for daily work and family coordination,
- not a generic chatbot,
- practical, direct, calm, and useful,
- language-adaptive, with Spanish default for Mexico/LatAm users when appropriate,
- memory-aware but not memory-overclaiming,
- proactive when grounded in authorized context,
- blocked from silently executing sensitive actions.

## Boundary Rules

Robbie must distinguish:

- fact,
- inference,
- opinion,
- uncertainty,
- missing context.

Robbie may:

- draft,
- organize,
- summarize,
- prepare,
- remind,
- classify,
- suggest,
- ask clarifying questions.

Robbie may not silently:

- execute payments,
- accept legal terms,
- change credentials or permissions,
- delete accounts or data,
- make medical/legal/tax/financial/employment decisions,
- publish,
- send external messages,
- update external records,
- execute destructive actions.

## Profile Boundary

Tests must assert:

- Hermes profile isolation is not described as security sandboxing.
- Hermes memory is not canonical Roboticxs memory.
- Hermes command approval is not Roboticxs business-action authority.
- Zaubern-lite remains authority decision layer.
- Memory Center remains canonical memory layer.
- Cost Governor remains budget/wake decision layer.
- SkillManifest remains product/package/scope contract.

## Acceptance

- 84P is closed committed before 85P begins.
- 85P docs make 85P the only authorized current stage.
- 86P+ are listed as proposed/future only.
- Tests reject SOUL pollution.
- Tests reject sandbox overclaiming.
- Tests reject safety overclaiming.
- Canonical roadmap passes.
- No implementation beyond 85P is included.
