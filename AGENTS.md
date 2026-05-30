# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a planning and specification workspace for `Roboticxs.com`, not an implementation repo yet. Treat `docs/ROBOTICXS_PROJECT_BRIEF.md` as the product context baseline and use the other files in `docs/` as the canonical MVP specs:

- `docs/PRODUCT_SPEC_v0_1.md`
- `docs/HERMES_MVP_TECHNICAL_PLAN.md`
- `docs/SAFETY_LAYER_SPEC_v0_1.md`
- `docs/MODEL_ROUTER_SPEC_v0_1.md`
- `docs/TOKEN_COUNTER_SPEC_v0_1.md`
- `docs/SKILL_MANIFEST_SCHEMA_v0_1.json`

Keep new product, architecture, and schema artifacts under `docs/`. Do not scatter planning files at repo root unless they are entrypoints like `README.md`.

Implementation direction already decided:
- Runtime/framework base: `Hermes Agent`
- Skill model reference: `anthropics/knowledge-work-plugins`

When code is added, keep the skills layer structurally separate from the Hermes orchestration/runtime layer.

## Build, Test, and Development Commands
No package manager, runtime, or executable dev workflow is confirmed in this repo yet. Do not invent commands such as `npm test`, `pnpm dev`, or `pytest` in code, docs, or reviews until the stack is actually created.

If implementation starts, document the real commands here and in `README.md`, for example install, dev server, test, lint, and build commands.

## Coding Style & Naming Conventions
Until code exists, follow the repo’s document conventions:

- Use explicit, versioned filenames such as `*_v0_1.md` and `*_SCHEMA.json`.
- Reuse product terms exactly as specified: `Memory Center`, `Context Scan`, `Scope Guard`, `Model Router`, `Token Counter`, `Safety Layer`.
- Prefer precise names over abbreviations in specs, schemas, and API descriptions.

For future implementation:
- Model skill packages after the file-based plugin structure used in `knowledge-work-plugins` (`manifest`, commands, skills, connector config).
- Keep Roboticxs product terminology distinct from upstream plugin/framework names in user-facing copy.

## Testing Guidelines
There is no test framework configured yet. For now, validation means checking consistency across the brief, product spec, and technical plan. When code is introduced, add tests with the feature and document the exact command used to run them.

## Architecture Overview
The confirmed MVP path is `Telegram -> robot orchestration -> memory -> scope guard -> model router -> safety decision -> token log`. Keep these concerns separated. Do not merge safety, routing, and memory logic into one vague module.

Hermes is the execution framework. The plugin-inspired skills layer defines domain behavior, manifests, commands, and tool wiring. Do not collapse those two concerns into one abstraction.

## Commit & Pull Request Guidelines
Git history is not available from this checkout, so no commit convention is confirmed. Use short imperative subjects such as `Add product spec index` or `Define skill manifest schema`.

PRs should include scope, linked spec sections, affected files, and any unresolved unknowns or risks.
