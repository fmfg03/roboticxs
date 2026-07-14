# Capability Catalog Boundary Annotation v0.1

## 1. Purpose

This document defines Stage 50P Capability Catalog Boundary Annotation. It makes existing capability catalog output clearer about current boundaries without adding capabilities, changing command routing, enforcing registry policy, or enabling external actions.

## 2. Repo-Local Seam

Stage 50P uses the current checkout's actual seam:

```text
app/capability_catalog.py
app/capability_control.py
app/flows/capability_flow.py
app/reply_composer.py
```

The later capability_registry_* modules are not used in this checkout because they are not present here.

## 3. Product-Safe Boundary Types

Stage 50P uses these product-safe boundary types:

- solo lectura local
- borrador / preparación
- preflight / revisión previa
- paquete de aprobación
- requiere aprobación
- planeado
- bloqueado

## 4. Catalog Annotation Rules

- annotate existing entries only
- do not add entries
- do not expose raw diagnostics
- do not imply external execution
- keep wording simple and non-technical

## 5. Non-Claims

This stage does not add new skills.
This stage does not add new commands.
This stage does not add new flows.
This stage does not change command routing.
This stage does not enforce policy.
This stage does not expose internal diagnostics.
This stage does not enable connectors.
This stage does not enable retrieval.
This stage does not enable RAG.
This stage does not enable browser automation.
This stage does not enable provider routing.
This stage does not call models.
This stage does not enable token counting.
This stage does not enforce budgets.
This stage does not send messages.
This stage does not book appointments.
This stage does not checkout or pay.
This stage does not mutate memory.

## 6. Future Alignment

The next defensible step after Stage 50P is either Capability Catalog UX Review v0 or Capability Registry Shadow Runtime Design v0. Direct blocking enforcement is still not the next step.
