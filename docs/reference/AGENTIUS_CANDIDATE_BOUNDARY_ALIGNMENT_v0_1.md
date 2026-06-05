# Agentius Candidate Boundary Alignment v0.1

## Purpose

Stage 54P aligns `AGENTIUS_CANDIDATE` as a boundary-only classification in Roboticxs v0.

This stage clarifies product separation between:

- Roboticxs v0 as a personal robot
- Agentius as business workflow automation territory
- Zaubern as a future authority layer for higher-consequence workflows

## Boundary Rule

If a request is about CRM, clients, pipeline, sales, team coordination, or business workflow automation, Robbie may classify it as `AGENTIUS_CANDIDATE`.

That classification is boundary-only.

It is not an active Roboticxs capability.

It does not create a lead, save a candidate, notify anyone, trigger a handoff, connect a CRM, use a connector, open a browser, send email or WhatsApp, or write to external systems.

## Catalog Visibility

`AGENTIUS_CANDIDATE` does not appear in `qué puedes hacer` / `what can you do`.

It may appear only in reference documentation and in direct boundary responses when the user asks for business automation territory.

## Allowed Response Shape

The response may:

- explain that the request fits Agentius territory better than a personal robot task
- state that no active business automation runs in Roboticxs v0
- offer safe local reformulation
- offer a manual summary or checklist

## Non-Goals

This stage does not:

- add capabilities
- add commands
- change routing
- change flows
- change orchestrator behavior
- add persistence
- add analytics or event tracking
- add CRM access
- add connectors
- add browser automation
- add email or WhatsApp execution
- add external writes
- expand authority

## Files

- `app/reply_composer.py`
- `tests/test_capability_resolver.py`
- `docs/reference/AGENTIUS_CANDIDATE_BOUNDARY_ALIGNMENT_v0_1.md`

## Validation

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_capability_resolver.py
python3 -m pytest -q
git diff -- app/orchestrator.py app/flows app/command_registry.py
git diff -- pyproject.toml requirements.txt package.json Dockerfile docker-compose.yml .env.example
git status --short
```
