# Roboticxs Codex Factory Workflow Validation

## Purpose

This document explains how Roboticxs should manually use the global Codex Factory Workflow Harness validator.

This is a manual validation aid for future Codex work. It is not automation, not CI, and not workflow execution.

## Manual Validator Command

Recommended manual command:

```bash
python3 ~/.codex/skills/codex-factory-workflow-harness/bin/validate_factory_workflow.py --ci --report-out roboticxs_artifacts/codex_factory_workflow/validation_report.v2.json
```

This command is documentation only in v5.

The report artifact should not be created in v5 unless separately approved.

## Recommended Report Path

Recommended future path:

`roboticxs_artifacts/codex_factory_workflow/validation_report.v2.json`

Status:

- candidate only
- not created in v5
- requires separate human approval

## How To Interpret Results

The validator result is evidence about the global Codex Factory Workflow Harness artifacts and their contract discipline.

For Roboticxs manual use, the validator result should be treated as:

- manual validation evidence
- a pre-work or pre-review check
- a structured report about global harness health

It should not be treated as product-runtime authority.

## What The Report Is Not

The validation report is not a workflow receipt, not an authority receipt, not proof of runtime enforcement, and not proof of production safety.

It is also not:

- proof that Roboticxs runtime behavior is safe
- proof that Roboticxs adopted automation
- proof that Roboticxs CI is configured
- proof that authority-sensitive product surfaces are approved for automation

## When To Run

Run the validator manually when:

- a Codex task in Roboticxs is large enough to need explicit workflow discipline
- story/spec/build/validation boundaries need to be checked against the global harness
- a human reviewer wants global harness health before future adoption work

Do not treat validator execution as a substitute for repo-local review.

## Human Approval Before Automation

Human approval is required before moving beyond `local_manual`.

That includes:

- adding a local script
- adding CI
- enabling advisory CI
- enabling blocking CI
- writing the report artifact
- changing the report path

## Authority-Adjacent Product Surfaces

Authority-adjacent product surfaces present in Roboticxs include:

- action approval
- capability control
- command routing
- memory control
- document and file intake control
- retrieval-control surfaces
- web workflow preflight
- budget and token controls
- safety boundaries for payment, credentials, legal, medical, financial, and admin-adjacent requests

## Authority-Sensitive Surfaces Touched By This Adoption

Authority-sensitive surfaces touched by this adoption: none identified.

This stage writes only adoption documentation and does not alter runtime authorization, action approval, capability enforcement, evidence schemas, policy or gate behavior, deployment or release gating, or production behavior.

## Rollback / Removal

If this documentation-only adoption stage must be removed:

- remove `docs/codex_factory_workflow/ADOPTION_PLAN.md`
- remove `docs/codex_factory_workflow/VALIDATION.md`
- do not remove runtime files as part of that rollback
- ignore or remove any future validator report artifact only if a later approved stage created it

## Non-Claims

This stage does not:

- execute workflows
- authorize writes
- create authority receipts
- promote a new authority path
- override AGENTS.md
- create a local validation script
- create CI integration
- change runtime behavior
