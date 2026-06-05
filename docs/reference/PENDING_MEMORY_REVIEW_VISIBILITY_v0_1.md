# Pending Memory Review Visibility v0.1

## Purpose

Stage 57P adds a local review surface for pending memory proposals so the user can inspect what still needs approval without confusing it with active memory.

## Scope

This stage adds a local pending-memory review command:

- `what memory proposals are pending`

This stage keeps existing behavior for:

- `what do you remember` for active memory only
- `APPROVE` / `REJECT`
- proposal expiration
- local-only memory storage

## Visibility Rule

Pending memory proposals must appear separately from active memories.

Active memories must not appear in pending review.

Pending proposals must not appear in active memory listing.

## Pending Upgrade Interest Rule

Pending `UPGRADE_INTEREST` proposals must display as:

- `Interés local pendiente`

They must remain local pending proposals only and must not imply:

- lead
- CRM
- pipeline
- handoff
- notificación
- external writes

`CRM` may still appear inside the proposal content when it is only the user's review topic.

## Empty State

If there are no pending proposals, Robbie must answer:

- `No tienes propuestas de memoria pendientes.`

## Out of Scope

- new schema
- new storage model
- capability catalog changes
- `AGENTIUS_CANDIDATE` changes
- connectors
- browser automation
- CRM sync
- handoff
- notifications
- external writes

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_memory_control.py
python3 -m pytest -q tests/test_memory_onboarding.py
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/orchestrator.py app/command_registry.py app/capability_catalog.py app/models.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```
