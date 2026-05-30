# CODEX PROMPT 001 — Roboticxs Read-Only Bootstrap Assessment

You are operating under the Codex Factory Protocol.

This is **Stage 0: read-only repo assessment** for the Roboticxs project.

Do **not** implement features.
Do **not** edit files.
Do **not** create files.
Do **not** run destructive commands.
Do **not** install dependencies.
Do **not** generate a full application.

Your job is to inspect the repository, establish verified facts, identify gaps, and propose the smallest correct first implementation plan for human approval.

---

## 1. Project Context

Roboticxs.com is the mass-market B2C / prosumer entry product in the Agentius / Zaubern ecosystem.

Roboticxs is not Agentius.
Roboticxs is not Zaubern.

Roboticxs is a personal AI robot product built on Hermes Agent. The product should feel simple, useful, personal, and safe.

Strategic chain:

```text
Roboticxs
Personal AI robot / daily AI adoption
        ↓
Agentius
Business workflow automation / governed agentic operations
        ↓
Zaubern
Execution authority / governance for high-consequence workflows
```

Core product thesis:

> One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.

Important product rule:

> One robot, many skills.

Do not design Roboticxs as a catalog of separate robots. The user has one personal robot with memory, personality, context, skill packages, model routing, token budget, action limits, and safety checks.

MVP interaction channel: **Telegram only**.

Do not introduce WhatsApp in the MVP.

---

## 2. Canonical Documents to Read First

Inspect these files if present:

```text
docs/ROBOTICXS_PROJECT_BRIEF.md
docs/PRODUCT_SPEC_v0_1.md
docs/SKILL_MANIFEST_SCHEMA_v0_1.json
docs/SAFETY_LAYER_SPEC_v0_1.md
docs/MODEL_ROUTER_SPEC_v0_1.md
docs/TOKEN_COUNTER_SPEC_v0_1.md
docs/HERMES_MVP_TECHNICAL_PLAN.md
docs/LAUNCH_PAGE_COPY_v0_1.md
```

If any file is missing, report it. Do not invent its contents.

Also inspect existing repo guidance if present:

```text
AGENTS.md
README.md
package.json
pnpm-lock.yaml
package-lock.json
yarn.lock
pyproject.toml
requirements.txt
Dockerfile
docker-compose.yml
.env.example
src/
app/
services/
docs/
tests/
```

---

## 3. Allowed Read-Only Commands

You may run read-only inspection commands such as:

```bash
pwd
ls
find . -maxdepth 4 -type f | sort
git status --short
git branch --show-current
git log --oneline -5
cat <file>
sed -n '1,220p' <file>
rg "<term>" .
node --version
npm --version
pnpm --version
python --version
```

Only run commands needed to understand the repo.

---

## 4. Forbidden Actions

Do not run:

```bash
npm install
pnpm install
yarn install
pip install
poetry install
npm run build
npm run dev
pnpm dev
pytest
rm
mv
cp
mkdir
touch
cat > file
python scripts that modify files
any formatter that rewrites files
any code generation command
```

Do not modify the working tree.

If you believe a write action is needed, describe it as a proposed next step instead of doing it.

---

## 5. What to Determine

Produce a repo-grounded assessment covering:

### A. Repository State

- Is this an empty repo, docs-only repo, or existing app?
- What stack is present, if any?
- What package manager appears to be used?
- What test framework appears to be used?
- What environment/config pattern appears to be used?
- Are there existing instructions in AGENTS.md or README.md?

### B. Product Alignment

Verify whether the repo currently supports or documents the MVP pillars:

- Telegram interface
- Memory Center
- Context Scan
- Skill Registry
- Skill Manifest loader
- Scope Guard
- Proactive Trigger Engine
- Model provider abstraction
- Model Router
- Token Counter
- Cost Governor
- Budget Policy
- Lightweight Zaubern Safety Layer
- Documents/PDF skill
- Admin usage dashboard

Classify each as:

```text
CONFIRMED_IN_REPO
DOCUMENTED_ONLY
MISSING
UNCLEAR
```

### C. Architecture Recommendation

Based only on repo facts and the canonical docs, recommend the first implementation architecture.

Do not overbuild.

Prefer the narrowest MVP slice:

```text
Telegram command intake
→ user/robot lookup
→ memory read/write skeleton
→ skill scope check
→ document or meeting task stub
→ model route decision stub
→ token usage event logging
→ safety decision before external action
```

### D. First User Story Candidate

Propose exactly one first user story.

Preferred story unless repo facts make it impossible:

> As a Roboticxs user, I can send a message to my personal robot through Telegram and receive a scoped response that records the task, applies a safety decision, and logs estimated model usage.

Include:

- user story
- acceptance criteria
- non-goals
- files likely to change in the next stage
- risks
- test strategy

### E. First Technical Spec Candidate

Draft a technical spec proposal for the first implementation stage.

The spec must include:

- data model additions or tables needed
- service/module boundaries
- API or webhook endpoints
- safety decision interface
- model routing interface
- token/cost event interface
- Telegram interaction path
- test cases
- implementation sequence
- rollback plan

Do not write code yet.

### F. Questions for Human Approval

Ask only questions that block implementation.

Do not ask generic preference questions.

If a reasonable default exists, state the default and proceed with the proposal.

---

## 6. Required Output Format

Return exactly this structure:

```markdown
# Roboticxs Stage 0 — Read-Only Bootstrap Assessment

## 1. Executive Finding

## 2. Repo Facts Verified

## 3. Canonical Docs Found / Missing

## 4. Current Stack Assessment

## 5. MVP Pillar Coverage Matrix

| Pillar | Status | Evidence | Notes |
|---|---|---|---|

## 6. Recommended First Slice

## 7. First User Story Proposal

## 8. Acceptance Criteria

## 9. Non-Goals

## 10. First Technical Spec Proposal

## 11. Likely Files To Change Later

## 12. Test Strategy

## 13. Risks / Unknowns

## 14. Human Approval Questions

## 15. Next Codex Prompt Recommendation
```

---

## 7. Evidence Discipline

Every factual claim about the repo must cite a file path or command output.

Examples:

```text
Confirmed: package manager appears to be pnpm because pnpm-lock.yaml exists.
Evidence: ./pnpm-lock.yaml

Missing: no Telegram adapter found.
Evidence: `find . -maxdepth 4 -type f | sort` and `rg "telegram|bot" .` returned no implementation file.
```

Do not rely on memory.
Do not rely on assumptions.
Do not infer unverified stack details.

---

## 8. Boundary

This prompt is successful only if it produces a clear, repo-grounded Stage 0 assessment and a proposed Stage 1 implementation plan.

Any code changes before human approval are a protocol violation.
