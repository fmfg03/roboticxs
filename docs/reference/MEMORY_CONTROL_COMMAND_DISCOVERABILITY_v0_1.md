# Memory Control Command Discoverability v0.1

## Purpose

Stage 58P adds a local help surface so the user can discover how memory control works without guessing commands.

## Command Surface

Canonical command:

- `how do i control memory`

Supported explicit help requests may also include:

- `memory help`
- `what memory commands can i use`
- `como controlo tu memoria`
- `como controlo lo que recuerdas`

Supported Spanish-first help phrasing also includes:

- `cómo controlo tu memoria`
- `cómo controlo lo que recuerdas`

## Commands Explained

- Ver memorias activas: `what do you remember`
- Ver propuestas pendientes: `what memory proposals are pending`
- Aprobar una propuesta pendiente: `APPROVE`
- Rechazar una propuesta pendiente: `REJECT`
- Olvidar una memoria activa: `forget memory <id>`

Una propuesta pendiente todavía no está guardada como memoria local activa.

`APPROVE` la guarda como memoria local.

`REJECT` la descarta.

`forget memory <id>` elimina una memoria local activa.

## Local Boundary

This help surface is discoverability only.

It does not create memory, approve memory, reject memory, delete memory, inspect external systems, or execute actions.

## Non-claims

- no lead
- no CRM
- no pipeline
- no handoff
- no notificación
- no connectors
- no browser
- no email/WhatsApp
- no external writes

## Out of Scope

- new memory storage
- new memory state
- schema changes
- capability catalog changes
- CRM sync
- handoff
- notifications
- analytics
- external writes

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_memory_control.py
python3 -m pytest -q tests/test_memory_onboarding.py
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/command_registry.py app/capability_catalog.py app/models.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```
