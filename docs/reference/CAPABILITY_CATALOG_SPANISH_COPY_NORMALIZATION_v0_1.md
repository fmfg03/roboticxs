# Capability Catalog Spanish Copy Normalization v0.1

This document defines Stage 52P Capability Catalog Spanish Copy Normalization.

## Purpose

Stage 52P normalizes the visible capability catalog UX to Spanish-first copy for non-technical users.

## Scope

This stage changes visible catalog names only.

It does not:
- change internal capability IDs
- change commands or triggers
- change routing
- change flows
- change behavior
- expand authority

## Preserved Internals

The following internal IDs remain in English:
- `action_approval_packets`
- `web_workflow_preflight`
- `skill_activation`
- `connectors`

Existing triggers also remain unchanged, including English triggers such as:
- `approval packet`
- `prepare approval`
- `web workflow preflight`
- `check web workflow`

## Visible Translations Applied

- `Action Approval Packets` -> `Paquetes de aprobación de acciones`
- `Web Workflow Preflight` -> `Revisión previa de tareas web`
- `Skill activation` -> `Activación de habilidades`
- `Connectors` -> `Conectores`

## Non-Claims

This stage does not add capabilities.

This stage does not change command matching.

This stage does not change capability boundaries.

This stage does not enable connectors, browser automation, retrieval, provider routing, payments, sends, bookings, or external writes.

## Future Alignment

The next defensible step after Stage 52P is another bounded product-surface cleanup, not a capability-model refactor.
