 # Roboticxs Stage 0 — Read-Only Bootstrap Assessment

  ## 1. Executive Finding

  This is a docs-only planning repo, not an existing app. Evidence: find . -maxdepth 3 -type f | sort shows only README.md, AGENTS.md, docs/*,
  and artifact zips. The MVP is well specified on paper, but there is no implementation, no package manifest, no test harness, no env template,
  and no valid Git checkout. Evidence: find . -maxdepth 3 -type f | sort; git status --short returned fatal: not a git repository.

  ## 2. Repo Facts Verified

  - Product context and MVP scope are documented in docs/ROBOTICXS_PROJECT_BRIEF.md, docs/PRODUCT_SPEC_v0_1.md, and docs/
    HERMES_MVP_TECHNICAL_PLAN.md.
  - Runtime direction is Hermes Agent. Evidence: README.md, AGENTS.md, docs/HERMES_MVP_TECHNICAL_PLAN.md.
  - Skill pattern reference is anthropics/knowledge-work-plugins. Evidence: README.md, AGENTS.md.
  - Canonical interaction channel for MVP is Telegram only. Evidence: docs/PRODUCT_SPEC_v0_1.md, docs/ROBOTICXS_PROJECT_BRIEF.md.
  - Repo-specific contributor guidance exists. Evidence: AGENTS.md.
  - The Git directory is empty/incomplete. Evidence: ls -la .git; git status --short failed.

  ## 3. Canonical Docs Found / Missing

  Found:

  - docs/ROBOTICXS_PROJECT_BRIEF.md
  - docs/PRODUCT_SPEC_v0_1.md
  - docs/SKILL_MANIFEST_SCHEMA_v0_1.json
  - docs/SAFETY_LAYER_SPEC_v0_1.md
  - docs/MODEL_ROUTER_SPEC_v0_1.md
  - docs/TOKEN_COUNTER_SPEC_v0_1.md
  - docs/HERMES_MVP_TECHNICAL_PLAN.md
  - docs/LAUNCH_PAGE_COPY_v0_1.md

  Missing:

  - No implementation files, manifests, lockfiles, Docker files, .env.example, or tests/. Evidence: find . -maxdepth 3 -type f | sort.

  ## 4. Current Stack Assessment

  - Repo type: docs-only repo. Evidence: find . -maxdepth 3 -type f | sort.
  - Stack present in code: none. Evidence: no package.json, pyproject.toml, requirements.txt, src/, app/, or tests/ in find . -maxdepth 3 -type
    f | sort.
  - Package manager: none present. Evidence: no pnpm-lock.yaml, package-lock.json, or yarn.lock.
  - Test framework: none present. Evidence: no test files or test config in find . -maxdepth 3 -type f | sort.
  - Environment/config pattern: none present. Evidence: no .env.example, compose file, or runtime config file.
  - Existing instructions: yes, in AGENTS.md and README.md.
  - Implementation direction in docs: Hermes-based backend with Telegram webhook, model routing, safety, and token logging. Evidence: docs/
    HERMES_MVP_TECHNICAL_PLAN.md.

  ## 5. MVP Pillar Coverage Matrix

  ┌──────────────────────────────────┬─────────────────┬─────────────────────────────────────────────────────────────────────────┬─────────────┐
  │ Pillar                           │ Status          │ Evidence                                                                │ Notes       │
  ├──────────────────────────────────┼─────────────────┼─────────────────────────────────────────────────────────────────────────┼─────────────┤
  │ Telegram interface               │ DOCUMENTED_ONLY │ docs/PRODUCT_SPEC_v0_1.md, docs/HERMES_MVP_TECHNICAL_PLAN.md            │ No adapter/ │
  │                                  │                 │                                                                         │ webhook     │
  │                                  │                 │                                                                         │ implementat │
  │                                  │                 │                                                                         │ ion exists. │
  │ Memory Center                    │ DOCUMENTED_ONLY │ docs/PRODUCT_SPEC_v0_1.md, docs/HERMES_MVP_TECHNICAL_PLAN.md            │ Data model  │
  │                                  │                 │                                                                         │ and         │
  │                                  │                 │                                                                         │ responsibil │
  │                                  │                 │                                                                         │ ities are   │
  │                                  │                 │                                                                         │ specified.  │
  │ Context Scan                     │ DOCUMENTED_ONLY │ docs/ROBOTICXS_PROJECT_BRIEF.md, docs/HERMES_MVP_TECHNICAL_PLAN.md      │ Explicit    │
  │                                  │                 │                                                                         │ “proposed   │
  │                                  │                 │                                                                         │ memories”   │
  │                                  │                 │                                                                         │ flow is     │
  │                                  │                 │                                                                         │ documented. │
  │ Skill Registry                   │ DOCUMENTED_ONLY │ docs/HERMES_MVP_TECHNICAL_PLAN.md                                       │ No runtime  │
  │                                  │                 │                                                                         │ loader      │
  │                                  │                 │                                                                         │ exists in   │
  │                                  │                 │                                                                         │ repo.       │
  │ Skill Manifest loader            │ DOCUMENTED_ONLY │ docs/SKILL_MANIFEST_SCHEMA_v0_1.json, docs/HERMES_MVP_TECHNICAL_PLAN.md │ Schema      │
  │                                  │                 │                                                                         │ exists;     │
  │                                  │                 │                                                                         │ loader does │
  │                                  │                 │                                                                         │ not.        │
  │ Scope Guard                      │ DOCUMENTED_ONLY │ docs/PRODUCT_SPEC_v0_1.md, docs/HERMES_MVP_TECHNICAL_PLAN.md            │ Scope       │
  │                                  │                 │                                                                         │ decisions   │
  │                                  │                 │                                                                         │ are         │
  │                                  │                 │                                                                         │ defined,    │
  │                                  │                 │                                                                         │ not         │
  │                                  │                 │                                                                         │ implemented │
  │                                  │                 │                                                                         │ .           │
  │ Proactive Trigger Engine         │ DOCUMENTED_ONLY │ docs/ROBOTICXS_PROJECT_BRIEF.md                                         │ Mentioned   │
  │                                  │                 │                                                                         │ in product  │
  │                                  │                 │                                                                         │ docs, not   │
  │                                  │                 │                                                                         │ yet carried │
  │                                  │                 │                                                                         │ into a      │
  │                                  │                 │                                                                         │ concrete    │
  │                                  │                 │                                                                         │ module list │
  │                                  │                 │                                                                         │ for Stage   │
  │                                  │                 │                                                                         │ 1.          │
  │ Model provider abstraction       │ DOCUMENTED_ONLY │ docs/MODEL_ROUTER_SPEC_v0_1.md                                          │ Supported   │
  │                                  │                 │                                                                         │ providers   │
  │                                  │                 │                                                                         │ and         │
  │                                  │                 │                                                                         │ internal    │
  │                                  │                 │                                                                         │ interface   │
  │                                  │                 │                                                                         │ are         │
  │                                  │                 │                                                                         │ specified.  │
  │ Model Router                     │ DOCUMENTED_ONLY │ docs/MODEL_ROUTER_SPEC_v0_1.md, docs/HERMES_MVP_TECHNICAL_PLAN.md       │ Input/      │
  │                                  │                 │                                                                         │ output      │
  │                                  │                 │                                                                         │ contract    │
  │                                  │                 │                                                                         │ exists.     │
  │ Token Counter                    │ DOCUMENTED_ONLY │ docs/TOKEN_COUNTER_SPEC_v0_1.md                                         │ Event       │
  │                                  │                 │                                                                         │ schema and  │
  │                                  │                 │                                                                         │ acceptance  │
  │                                  │                 │                                                                         │ criteria    │
  │                                  │                 │                                                                         │ exist.      │
  │ Cost Governor                    │ DOCUMENTED_ONLY │ docs/TOKEN_COUNTER_SPEC_v0_1.md, docs/MODEL_ROUTER_SPEC_v0_1.md         │ Budget      │
  │                                  │                 │                                                                         │ thresholds  │
  │                                  │                 │                                                                         │ are         │
  │                                  │                 │                                                                         │ specified.  │
  │ Budget Policy                    │ DOCUMENTED_ONLY │ docs/TOKEN_COUNTER_SPEC_v0_1.md                                         │ BudgetPolic │
  │                                  │                 │                                                                         │ y and       │
  │                                  │                 │                                                                         │ BudgetAlert │
  │                                  │                 │                                                                         │ are         │
  │                                  │                 │                                                                         │ defined.    │
  │ Lightweight Zaubern Safety Layer │ DOCUMENTED_ONLY │ docs/SAFETY_LAYER_SPEC_v0_1.md, docs/HERMES_MVP_TECHNICAL_PLAN.md       │ Action      │
  │                                  │                 │                                                                         │ classes and │
  │                                  │                 │                                                                         │ decision    │
  │                                  │                 │                                                                         │ envelope    │
  │                                  │                 │                                                                         │ are         │
  │                                  │                 │                                                                         │ specified.  │
  │ Documents/PDF skill              │ DOCUMENTED_ONLY │ docs/PRODUCT_SPEC_v0_1.md, docs/SKILL_MANIFEST_SCHEMA_v0_1.json         │ Product and │
  │                                  │                 │                                                                         │ schema      │
  │                                  │                 │                                                                         │ cover it;   │
  │                                  │                 │                                                                         │ no          │
  │                                  │                 │                                                                         │ extractor   │
  │                                  │                 │                                                                         │ or skill    │
  │                                  │                 │                                                                         │ package     │
  │                                  │                 │                                                                         │ exists.     │
  │ Admin usage dashboard            │ DOCUMENTED_ONLY │ docs/PRODUCT_SPEC_v0_1.md, docs/TOKEN_COUNTER_SPEC_v0_1.md              │ MVP allows  │
  │                                  │                 │                                                                         │ a basic     │
  │                                  │                 │                                                                         │ admin view  │
  │                                  │                 │                                                                         │ or logs     │
  │                                  │                 │                                                                         │ only.       │
  └──────────────────────────────────┴─────────────────┴─────────────────────────────────────────────────────────────────────────┴─────────────┘

  ## 6. Recommended First Slice

  Smallest correct Stage 1 slice:

  1. Telegram webhook intake.
  2. User and robot lookup stub.
  3. Task and task-run persistence.
  4. Basic skill scope decision using one skill manifest.
  5. Safety check on proposed response/action.
  6. Model route estimate stub.
  7. Token usage event logging.
  8. Telegram response back to user.

  Reason: this matches the preferred narrow MVP loop in the prompt and the architecture path in docs/HERMES_MVP_TECHNICAL_PLAN.md without
  prematurely building PDF ingestion, proactive triggers, or full memory scanning.

  ## 7. First User Story Proposal

  As a Roboticxs user, I can send a message to my personal robot through Telegram and receive a scoped response that records the task, applies a
  safety decision, and logs estimated model usage.

  ## 8. Acceptance Criteria

  - A Telegram webhook endpoint receives a text message and normalizes it into a task request.
  - The system resolves or creates a local user/robot association for the Telegram sender.
  - The request is checked against one active skill manifest and returns a scope decision.
  - The system generates a safety decision envelope before any external action is considered.
  - The system generates one model-route estimate record and one token-usage event record for the task.
  - The user receives a Telegram reply that reflects the scope and safety decision.
  - No PDF parsing, connector sync, or proactive trigger logic is required in this stage.
  - Evidence basis: docs/HERMES_MVP_TECHNICAL_PLAN.md, docs/SAFETY_LAYER_SPEC_v0_1.md, docs/MODEL_ROUTER_SPEC_v0_1.md, docs/
    TOKEN_COUNTER_SPEC_v0_1.md.

  ## 9. Non-Goals

  - PDF upload and extraction.
  - Durable memory approval UX.
  - Email/calendar connectors.
  - Proactive trigger engine.
  - Admin dashboard UI.
  - Multi-provider live routing.
  - Payments, record writes, or other external side effects.

  ## 10. First Technical Spec Proposal

  - Data model additions:
      - users, robots, tasks, task_runs, skill_manifests, model_route_decisions, token_usage_events, safety_decisions.
      - Defer context_scans, proposed_memories, budget_alerts, and PDF-specific entities unless the first slice expands.
  - Service/module boundaries:
      - Telegram adapter
      - Robot orchestrator
      - Skill manifest loader
      - Scope guard
      - Safety checker
      - Model router estimator
      - Token/cost logger
      - Persistence layer
  - API/webhook endpoints:
      - POST /api/telegram/webhook
      - Optional read-only debug endpoint for task lookup if needed during local bootstrap.
  - Safety decision interface:
      - Input/output should follow the action envelope and decision payload in docs/SAFETY_LAYER_SPEC_v0_1.md.
  - Model routing interface:
      - Use the router input/output shape from docs/MODEL_ROUTER_SPEC_v0_1.md, but allow a single stub provider/model for Stage 1.
  - Token/cost event interface:
      - Persist TokenUsageEvent fields from docs/TOKEN_COUNTER_SPEC_v0_1.md with estimated values first; final reconciliation can remain
        stubbed.
  - Telegram interaction path:
      - webhook -> normalize -> user/robot lookup -> scope check -> safety check -> route estimate -> task persistence -> reply.
  - Test cases:
      - inbound Telegram text request
      - out-of-scope request returns scope fallback
      - blocked action returns BLOCK
      - confirmation-required action returns ASK_CONFIRMATION
      - successful low-risk request logs route and token event
  - Implementation sequence:
      1. Establish actual app scaffold and package/runtime manifest.
      2. Add persistence schema for minimal tables.
      3. Build Telegram webhook intake.
      4. Add manifest loader and one starter skill.
      5. Add safety decision service.
      6. Add route estimator and token logger.
      7. Add tests around the end-to-end text flow.
  - Rollback plan:
      - Feature-flag the Telegram webhook path.
      - Keep route estimation and safety logic isolated so they can be disabled independently.
      - If persistence is unstable, fall back to logging-only mode for local bootstrap.

  ## 11. Likely Files To Change Later

  No implementation paths exist yet. Stage 1 will need to create, at minimum:

  - one runtime manifest: pyproject.toml or package.json
  - one env template: .env.example
  - one app entrypoint tree: src/ or app/
  - one tests tree: tests/
  - one manifest/seed location for starter skills
    This is a proposal, not a confirmed repo structure. Evidence: none of these files or directories exist in find . -maxdepth 3 -type f | sort.

  ## 12. Test Strategy

  - Start with service-level and request-path tests around the Telegram text flow.
  - Validate pure functions first: scope decision, safety decision mapping, route estimation, token event creation.
  - Add one end-to-end webhook test that proves task creation, safety decision, route estimate, and reply composition.
  - Do not start with PDF, OCR, or multi-provider integration tests; they are outside the first slice.

  ## 13. Risks / Unknowns

  - Blocking: there is no valid Git repo state. Evidence: git status --short failed and .git is effectively empty.
  - Blocking: the implementation language is unresolved in repo docs. docs/HERMES_MVP_TECHNICAL_PLAN.md allows Node.js/TypeScript or
    Python/FastAPI, but the repo does not choose one.
  - Blocking: no database choice is confirmed.
  - Risk: building PDF flow first would widen scope before the base Telegram-task-safety loop exists.
  - Risk: conflating Hermes runtime concerns with plugin/skill packaging concerns would create the wrong abstraction boundary. Evidence:
    AGENTS.md.

  ## 14. Human Approval Questions

  - Confirm the Stage 1 runtime choice. Default recommendation: Python/FastAPI if that gives the cleanest Hermes integration path.
  - Confirm the minimal persistence choice. Default recommendation: start with the smallest local relational setup that can later map cleanly to
    Postgres.

  ## 15. Next Codex Prompt Recommendation

  Use a Stage 1 build prompt that does only this approved slice: scaffold the real app runtime, add minimal persistence, implement POST /api/
  telegram/webhook, load one starter skill manifest, apply one safety decision, create one model-route estimate, log one token-usage event, and
  cover that text-only path with tests.
