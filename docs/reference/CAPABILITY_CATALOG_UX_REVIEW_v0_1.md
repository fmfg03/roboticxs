# Capability Catalog UX Review v0.1

## 1. Purpose

This document defines Stage 51P Capability Catalog UX Review. It improves the scanability of the capability catalog without changing command routing, adding capabilities, expanding authority, or enabling external actions.

## 2. Relationship to Stage 50P

Stage 50P established the product-safe boundary annotation model.

Stage 51P keeps those same boundaries and improves how they are presented to users.

Stage 50P remains the boundary annotation record.

Stage 51P is the catalog UX refinement layer built on top of that record.

## 3. UX Goals

- make the catalog easier to scan quickly
- show what Robbie can do today before showing what is planned
- separate approval-required items from preparation-only items
- keep explicit safety wording where authority could be misunderstood
- preserve product-safe non-claims

## 4. Section Order

Stage 51P uses this user-comprehension order:

1. Disponible ahora
2. Necesita aprobación
3. Solo preparación / revisión previa
4. Planeado / no activo todavía
5. Bloqueado

## 5. Two-Line Bullet Pattern

Each catalog entry should use:

```text
• Capability name — useful first-line description.
  Límite: plain-language boundary summary.
```

The first line explains what the capability is useful for.

The second line explains the current boundary in non-technical language.

## 6. Global Footer Rationale

Per-entry boundaries improve scanability, but they do not replace a short global reminder.

The global footer exists to prevent users from extrapolating from one capability into payment, checkout, messaging, browser, connector, or other external execution claims.

## 7. Non-Claims

This stage does not add new capabilities.
This stage does not add new commands.
This stage does not change command routing.
This stage does not change flows.
This stage does not enforce policy.
This stage does not expose diagnostics.
This stage does not enable connectors.
This stage does not enable retrieval.
This stage does not enable browser automation.
This stage does not enable provider routing.
This stage does not call models.
This stage does not send messages.
This stage does not book appointments.
This stage does not checkout or pay.
This stage does not write to external systems.

## 8. Future Alignment

The next defensible step after Stage 51P is either a broader Capability Catalog UX polish pass or a separate Capability Registry Shadow Runtime Design stage.

Direct blocking enforcement is still not the next step.
