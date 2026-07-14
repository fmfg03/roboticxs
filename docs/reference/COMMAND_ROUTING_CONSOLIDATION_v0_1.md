# Command Routing Consolidation v0.1

## Purpose

This note documents the Stage 61P command-routing refactor.

It is an implementation reference for maintainers, not a product-scope change.

The goal of 61P is to consolidate explicit command dispatch without changing user-visible behavior.

## Routing model after 61P

The routing model after 61P is:

1. `app/orchestrator.py` resolves the flow context.
2. `app/command_registry.py` evaluates explicit text-command routes in declared order.
3. The first matching registry route dispatches its flow handler.
4. If no registry route matches:
   - Telegram document attachment intake still routes directly to file intake.
   - Explicit memory proposal intent extraction still routes to memory proposal flow.
   - Everything else falls through to the general task flow.

## Routes moved into command_registry

The registry now covers these explicit command families:

- action approval exact command
- action approval with trailing task
- web preflight
- capability catalog / capability queries
- attention summary
- robot folder
- super familiar
- usage spend/tokens
- budget status/reset
- budget setters
- file listing and retrieval-control readouts
- request file retrieval enablement
- approve/reject retrieval enablement request `<id>`
- forget file `<id>`
- cancel file retrieval `<id>`
- retrieve file `<id>`
- document listing / forget / review
- memory active listing
- pending memory proposals
- memory help
- `APPROVE` / `REJECT`
- forget memory `<id>`

## Routes intentionally left outside registry and why

These paths remain outside the registry by design:

- Telegram document attachment intake: outside because it is attachment/intake, not text command.
- explicit memory proposal intent extraction: outside because it is intent extraction, not explicit command.
- general fallback: outside because it is the default non-command path.

## Dispatch priority model

Dispatch priority is defined by route order in `REGISTERED_COMMAND_ROUTES`.

The first matching route wins.

This keeps priority explicit for:

- exact-match routes;
- parsed routes with trailing task text;
- parsed routes with IDs;
- command families that could otherwise be swallowed by broader matchers.

When adding or moving an explicit command route:

- preserve current dispatch priority;
- add or update focused tests for exact-match or parsed-match behavior;
- avoid changing product copy unless the stage explicitly approves it.

## No behavior change

Stage 61P does not add commands, product capabilities, or external behavior.

It only consolidates the dispatch path for commands that already existed.

Expected behavior remains:

- exact commands still work;
- parameterized commands still work;
- trailing task parsing still works;
- memory proposal intent extraction still remains outside the registry;
- Telegram attachment intake still remains outside the registry;
- unknown conversational turns still fall through to general task handling.

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

## Validation

Validation executed for this refactor:

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_action_approval_packets.py`
- `python3 -m pytest -q tests/test_file_control.py`
- `python3 -m pytest -q tests/test_telegram_webhook.py`
- `python3 -m pytest -q tests/test_memory_control.py`
- `python3 -m pytest -q tests/test_capability_resolver.py`
- `python3 -m pytest -q`
