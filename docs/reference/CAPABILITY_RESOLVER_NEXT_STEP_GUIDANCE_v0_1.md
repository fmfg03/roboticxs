# Capability Resolver Next-Step Guidance v0.1

## Purpose

Stage 53P adds a short status-aware next-step guidance line to capability resolver responses.

This stage improves user orientation only.

## Status guidance model

- `AVAILABLE_READ_ONLY`
  - next step points the user to local-only review or preparation
- `NEEDS_APPROVAL`
  - next step preserves explicit approval before save, send, or change
- `AVAILABLE_DRAFT_ONLY`
  - next step preserves preparation or preflight-only behavior
- `PLANNED`
  - next step preserves not-active-today framing
- `BLOCKED`
  - next step offers manual preparation help without softening the block
- `UNKNOWN`
  - next step offers reformulation or review against available capabilities only

## Non-authority

This stage does not add capabilities.

This stage does not add commands.

This stage does not change routing, flows, or orchestration.

This stage does not enable connectors, retrieval, browser automation, Webwright, payments, checkout, bookings, external writes, or model/provider execution.

## Files

- `app/reply_composer.py`
- `tests/test_capability_resolver.py`
- `docs/reference/CAPABILITY_RESOLVER_NEXT_STEP_GUIDANCE_v0_1.md`

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/orchestrator.py app/flows app/command_registry.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```

## Non-goals

- no new capabilities
- no new commands
- no capability-model refactor
- no authority expansion
- no execution changes
