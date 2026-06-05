# Memory Type Visibility / Control Copy Hardening v0.1

## Purpose

Stage 56P hardens visible memory-control copy so approved `UPGRADE_INTEREST` entries read as local user memory, not as a commercial state.

## Scope

This stage keeps the existing local memory controls:

- existing `what do you remember` listing
- existing `forget memory <id>` deletion path
- existing approved `MemoryItem` storage

It does not add commands, storage, schema, routing, catalog entries, or new capabilities.

## Listing Boundary

Approved `UPGRADE_INTEREST` memories must appear as local user memory with the label:

- `Interés local`

The listing must stay clear and must not imply:

- lead
- CRM
- pipeline
- oportunidad comercial
- enviado a Agentius
- handoff
- notificación
- CRM conectado
- external writes

`CRM` may still appear inside the user-provided memory content when it is only the subject the user wants to review later, but not as a connected CRM, touched CRM, synced CRM, or commercial record.

## Non-claims

- no lead
- no CRM
- no pipeline
- no handoff
- no notificación
- no external writes

## Delete Boundary

Deleting any memory through `forget memory <id>` must confirm removal as local memory only.

The delete confirmation must not imply removal of:

- a lead
- a pipeline item
- a CRM record
- a handoff
- a notification

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_memory_control.py
python3 -m pytest -q tests/test_memory_onboarding.py
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/orchestrator.py app/command_registry.py app/capability_catalog.py
git diff -- app/flows ':!app/flows/memory_flow.py'
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```
