# Local Upgrade Interest Memory Proposal v0.1

## Purpose

Stage 55P lets Robbie prepare a local pending memory proposal when the user explicitly asks to save upgrade interest related to Agentius.

This is not lead capture.

This is not a handoff.

This is not CRM activity.

## Rule

Robbie may prepare a local upgrade-interest memory proposal only after an explicit user request in the same message.

That proposal stays pending until the user replies with the existing approval flow.

Nothing becomes active memory until explicit `APPROVE`.

The proposed note should preserve a minimal useful description of the user's interest from that same message when it can be derived safely.

## Local-Only Boundary

This stage is local only.

It does not:

- create a lead
- create a pipeline record
- notify anyone
- hand off to Agentius
- sync to CRM
- use connectors
- open a browser
- send email or WhatsApp
- write to external systems

## Runtime Shape

Stage 55P reuses the existing local memory seam:

- `ProposedMemory` with `PENDING`
- existing `APPROVE` / `REJECT`
- `MemoryItem` only after approval
- existing local listing
- existing local forget flow

No new capability is added to the catalog.

`AGENTIUS_CANDIDATE` remains boundary-only.

## In Scope

- explicit same-message interest requests only
- local pending proposal only
- local approval or rejection only
- visible local memory listing after approval
- deletable local memory after approval
- clear no-claims copy

## Out of Scope

- auto-save
- inferred follow-up from a previous turn
- lead creation
- CRM sync
- notifications
- handoff
- connectors
- browser automation
- external writes
- schema migration
- catalog changes
- routing redesign

## Files

- `app/memory_extraction.py`
- `app/reply_composer.py`
- `tests/test_memory_onboarding.py`
- `tests/test_capability_resolver.py`
- `docs/reference/LOCAL_UPGRADE_INTEREST_SIGNAL_v0_1.md`

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_memory_onboarding.py
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/orchestrator.py app/flows app/command_registry.py app/capability_catalog.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```
