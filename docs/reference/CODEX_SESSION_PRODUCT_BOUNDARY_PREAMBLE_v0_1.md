# Codex Session Product Boundary Preamble v0.1

## Purpose

This is a session startup preamble for new Codex sessions.

It is a docs/process reference, not runtime behavior.

It exists to prevent context loss between Codex sessions.

## Product closure

Roboticxs v0 es un robot personal local/controlado por el usuario.

Roboticxs v0 is not:

- CRM
- lead-gen
- pipeline comercial
- handoff a Agentius
- navegador
- conectores activos
- email/WhatsApp
- external writes
- analytics comercial
- automatización empresarial activa

## Current memory/control surfaces

- `AGENTIUS_CANDIDATE = boundary-only`
- `UPGRADE_INTEREST = memoria/interés local del usuario`
- `ProposedMemory PENDING ≠ MemoryItem ACTIVE`
- `APPROVE` guarda como memoria local
- `REJECT` descarta
- `forget memory <id>` elimina memoria local
- `what do you remember` lista memorias activas
- `what memory proposals are pending` lista propuestas pendientes
- `how do I control memory / cómo controlo tu memoria` solo muestra ayuda local
- aliases aceptados para memory help: `memory help`, `what memory commands can i use`, `como controlo tu memoria`, `como controlo lo que recuerdas`

## Recent closed stages

- `50P - Capability Catalog Boundary Annotation`: anoto límites seguros del catálogo de capacidades.
- `51P - Capability Catalog UX Review`: ajusto presentación y lectura del catálogo sin abrir nuevas capacidades.
- `52P - Capability Catalog Spanish Copy Normalization`: normalizo copy español-first del catálogo.
- `53P - Capability Resolver Next-Step Guidance`: agrego guidance local de siguiente paso.
- `54P - Agentius Candidate Boundary Alignment`: dejo `AGENTIUS_CANDIDATE` como boundary-only.
- `55P - Local Upgrade Interest Memory Proposal`: limito `UPGRADE_INTEREST` a memoria/interés local del usuario.
- `56P - Memory Type Visibility / Control Copy Hardening`: refuerzo copy para distinguir tipos de memoria y control local.
- `57P - Pending Memory Review Visibility`: separo propuestas pendientes de memorias activas.
- `58P - Memory Control Command Discoverability`: hago descubrible la ayuda local de control de memoria.

## Operating rules for Codex

- Start with read-only inspection.
- Do not invent repo facts.
- Do not modify files before story/spec approval.
- Do not stage before read-only diff review.
- Do not commit before staged review and explicit approval.
- Do not push, merge, rebase, or amend.
- Keep changes scoped to the approved stage.
- Follow the required process: read-only review -> staged review -> commit -> post-commit validation.
- If a stage appears to require touching orchestrator/routing/flows/schema/config, explain why before implementation.
- No commit sin aprobación explícita.

## Standard validation

Use the standard repo validation block when a stage touches runtime. For docs-only stages, do not invent extra checks.

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_memory_control.py
python3 -m pytest -q tests/test_memory_onboarding.py
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git status --short
git diff -- app/command_registry.py app/capability_catalog.py app/models.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
```

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

## Out of scope

- Do not turn the preamble into runtime logic.
- Do not add enforcement code.
- Do not change app behavior.
- Do not change CI unless separately approved.
- Do not edit `AGENTS.md` unless explicitly approved.
