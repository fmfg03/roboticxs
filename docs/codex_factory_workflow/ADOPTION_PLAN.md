# Roboticxs Codex Factory Workflow Harness Adoption Plan

## Status

Approved documentation-only adoption stage for `local_manual`.

This stage documents how Roboticxs should manually use the global Codex Factory Workflow Harness validator.

It does not install CI, does not add scripts, and does not change runtime behavior.

## Adoption Mode

`local_manual`

No other adoption mode is approved in this stage.

Not approved here:

- `local_scripted`
- `ci_non_blocking`
- `ci_blocking`

## Boundary

This adoption plan documents local manual use of the global Codex Factory Workflow Harness validator for Roboticxs. It does not install CI, does not add scripts, does not execute workflows, does not authorize writes, does not create authority receipts, does not promote a new authority path, and does not override AGENTS.md, repo-local instructions, or human approval checkpoints.

## Why Local Manual First

Roboticxs has a real Python runtime, a dirty workspace from prior work, authority-adjacent product surfaces, and no clearly confirmed CI integration surface in this stage.

`local_manual` is the safest first adoption mode because it:

- adds no CI behavior
- adds no local script
- adds no blocking gate
- keeps human review in the loop
- allows manual validator use without changing runtime or policy surfaces

## Repo Context

Confirmed repo facts in the adoption dry run:

- Roboticxs lives at `/root/roboticxs`
- it contains a real runtime under `app/`
- it contains tests under `tests/`
- it uses `pyproject.toml` with `pytest`
- it already uses `docs/` heavily for product and runtime documentation
- it already uses `roboticxs_artifacts/` as an artifact/archive convention

The local `AGENTS.md` remains authoritative for repo-specific behavior.

## Authority-Adjacent Product Surfaces

Roboticxs contains authority-adjacent product surfaces. These are present in the repo and require caution in future stages:

- command registry
- orchestrator
- capability catalog and capability control
- action approval control and approval packet semantics
- web workflow preflight control and policy
- budget and token controls
- memory control and memory extraction
- robot folder control
- document control and review
- file intake control
- retrieval adapter and retrieval enablement surfaces
- safety boundaries for legal, medical, financial, payment, credential, and admin-adjacent tasks

## Adoption-Touched Authority-Sensitive Surfaces

Authority-sensitive surfaces touched by this adoption: none identified.

Roboticxs contains authority-adjacent product surfaces. The local manual validator adoption documented here does not touch authority-sensitive runtime surfaces.

This stage only adds adoption documentation. It does not alter runtime authorization, action approval logic, capability enforcement, evidence schemas, policy or gate behavior, deployment or release gating, or production behavior.

## Human Approval Requirements

Human approval is required before:

- adding project-local scripts
- adding CI
- enabling non-blocking CI
- enabling blocking CI
- changing the report path convention
- touching `AGENTS.md`
- touching runtime code
- touching tests
- touching deployment config
- touching package or build config

## Approved Files For This Stage

Approved in this stage:

- `docs/codex_factory_workflow/ADOPTION_PLAN.md`
- `docs/codex_factory_workflow/VALIDATION.md`

No other repo path is approved for v5 writes.

## Candidate Future Files

Candidate only. Not created in v5. Requires separate human approval.

- `roboticxs_artifacts/codex_factory_workflow/validation_report.v2.json`
- `scripts/validate-codex-factory-workflow.sh`
- `.github/workflows/codex-factory-workflow-validation.yml`

## Report Path Convention

Recommended path for a future approved manual report:

`roboticxs_artifacts/codex_factory_workflow/validation_report.v2.json`

Status:

- candidate only
- not created in v5
- requires human approval before write

Reason:

Roboticxs already uses `roboticxs_artifacts/` as a repo-local artifact convention, so this is a better fit than introducing a new artifact root.

## Rollback Plan

If this adoption stage needs to be removed later:

- files_to_remove:
  - `docs/codex_factory_workflow/ADOPTION_PLAN.md`
  - `docs/codex_factory_workflow/VALIDATION.md`
- files_to_restore:
  - none expected for this stage
- ci_steps_to_disable:
  - none
- report_artifacts_to_ignore_or_remove:
  - future `roboticxs_artifacts/codex_factory_workflow/validation_report.v2.json` if later created in a separate approved stage
- owner:
  - Roboticxs operator
- rollback_command_or_manual_steps:
  - remove the two adoption docs
  - do not touch runtime, tests, deployment, or secrets

## Non-Claims

This stage does not claim:

- Roboticxs CI adopted the validator
- Roboticxs has a local validation script
- Roboticxs workflow execution changed
- Roboticxs runtime enforcement changed
- Roboticxs authority path is closed
- Roboticxs authority receipt exists
- Roboticxs production safety changed
- the validation report is proof of runtime enforcement
- the validation report is proof of production safety
