# Roboticxs MVP Artifact Pack

This package contains the initial repo-ready planning artifacts for **Roboticxs.com**.

Roboticxs is the mass-market personal AI robot product in the Agentius / Zaubern ecosystem. It is designed as a low-friction entry product: one personal robot, many skills, visible memory, Telegram-first usage, model routing, token/cost control, and lightweight action boundaries.

## Document Map

| File | Purpose |
|---|---|
| `docs/ROBOTICXS_PROJECT_BRIEF.md` | Source brief and canonical starting context. |
| `docs/PRODUCT_SPEC_v0_1.md` | MVP product definition, user experience, plans, metrics, and constraints. |
| `docs/SKILL_MANIFEST_SCHEMA_v0_1.json` | Machine-readable schema for skill packages and scope guards. |
| `docs/SAFETY_LAYER_SPEC_v0_1.md` | Lightweight consumer-facing action boundary layer. |
| `docs/MODEL_ROUTER_SPEC_v0_1.md` | Model selection, provider abstraction, and routing policy. |
| `docs/TOKEN_COUNTER_SPEC_v0_1.md` | Usage, cost, budget, and margin tracking design. |
| `docs/HERMES_MVP_TECHNICAL_PLAN.md` | Technical implementation plan for a Hermes-based Telegram MVP. |
| `docs/LAUNCH_PAGE_COPY_v0_1.md` | Initial landing-page messaging and section copy. |

## MVP Demo Target

The first demo should prove one narrow loop:

1. User talks to robot through Telegram.
2. User authorizes a small context scan.
3. Robot proposes memories instead of silently storing raw data.
4. User sends a PDF or document.
5. Robot prepares a review and meeting brief.
6. Robot asks before any sensitive action.
7. System logs model route, token usage, estimated cost, and safety decision.

## Strategic Constraint

Do not turn Roboticxs into an enterprise governance product too early. Zaubern should influence the action boundary, but consumer-facing language must stay simple.

## Added in v0.7

- `docs/STAGE_2_VALIDATION_STAGE3_SPEC_REPORT.md` — Codex validation report confirming Stage 2 and specifying Stage 3.
- `docs/CODEX_PROMPT_006_STAGE3_MEMORY_CONTROL_BUILD.md` — Stage 3 build prompt for memory read/control plus Stage 2 safety repairs.

## Added in v0.8

- `docs/STAGE_3_MEMORY_CONTROL_COMPLETION_REPORT.md` — Codex completion report for Stage 3 memory read/control and Stage 2 repairs.
- `docs/CODEX_PROMPT_007_STAGE3_VALIDATION_STAGE4_SPEC.md` — Read-only validation/spec prompt to verify Stage 3 and decide the correct Stage 4 direction.

