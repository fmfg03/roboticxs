# Conversation Continuity Spine v0.1

## Purpose

Stage 66P defines Conversacion Horizontal / Continuity Spine v0 for Roboticxs.

Roboticxs should manage continuity, not isolated chats. The v0 continuity spine converts ongoing conversation into classified intent, governed memory candidates, criterio signals, priorities, explicit non-actions, and next-step decisions.

Allowed claim:

```text
Roboticxs helps users turn ongoing conversation into structured memory candidates, useful criterio, safer planning, and clear next steps.
```

Spanish product claim:

```text
Roboticxs convierte la conversacion diaria en memoria gobernada, criterio, prioridades y proximos pasos.
```

## Zaubern Authority Principle

Zaubern governs the authority surface of personal continuity.

Roboticxs owns the conversational user experience: Telegram-compatible conversation, continuity, routines, "que se me paso", "que hago hoy", planning, and bounded proactive suggestions.

Zaubern owns the authority boundary: what can be stored, what requires confirmation, what is fact versus preference versus inference versus strategic opinion, what expires, what may influence planning, what may influence proactive intervention, what must be labeled, what must be blocked, and what must be exportable or auditable.

## Runtime Boundary

66P adds a pure local runtime contract in `app/conversation_continuity.py`.

It does not add database writes, schema migrations, a new durable memory backend, Mirix, vector storage, graph memory, full historical retrieval, connectors, background monitoring, reminders, autonomous execution, external messages, browser execution, email, WhatsApp, CRM, lead-gen, handoff, external skills, caregiver behavior, voice behavior, or Research Radar.

`external_execution_authorized` is always false in 66P.

## Classification Taxonomy

Every meaningful user message should resolve to one primary classification:

```text
CURIOSITY
SIGNAL
CANDIDATE_IDEA
EXECUTION_PRIORITY
ROUTINE
DECISION
OPEN_LOOP
CRISIS_OR_SENSITIVE
CONTEXT_UPDATE
NO_ACTION
```

Only the primary classification controls behavior. Secondary labels may add context, such as `DAILY_START`.

Rules:

- Curiosity does not automatically create a task, story, spec, or roadmap item.
- Signal may be answered or parked.
- Candidate ideas default to backlog unless priority criteria are met.
- Payment, active client delivery, deadline, or committed work becomes execution priority.
- Health, medication, family-care risk, or mental-health sensitive material becomes constrained sensitive context.
- Reflective conversation may remain `NO_ACTION`.

## Next-Step Resolver

Every classified message resolves to one next-step decision:

```text
NO_ACTION
ANSWER_ONLY
NOTE_PROPOSED
MEMORY_UPDATE_PROPOSED
BACKLOG_ITEM
OPEN_LOOP_CREATED
DECISION_RECORDED
STORY_RECOMMENDED
SPEC_RECOMMENDED
EXECUTION_PLAN
ESCALATE_OR_CONFIRM
```

The resolver preserves non-action as valid. It must not turn curiosity into roadmap work, and it must not silently store sensitive inferences.

## Continuity Memory Candidate Contract

66P may produce `ContinuityMemoryCandidate` objects only. It does not choose final storage architecture.

Candidate fields:

```text
content
item_type
reason
authority_level
sensitivity_level
source_event_ref
confirmation_required
confirmed_by_user
expiration_policy
allowed_influence_scope
storage_target
```

Allowed item types:

```text
FACT
PREFERENCE
GOAL
VALUE
RISK
OPERATING_PATTERN
COMMUNICATION_STYLE
PROJECT_CONTEXT
OPEN_LOOP
DECISION
INFERENCE
STRATEGIC_OPINION
```

Authority and storage rules:

- `SYSTEM_INFERENCE` requires confirmation unless the item is `SESSION_ONLY` or `DO_NOT_STORE`.
- `SENSITIVE` requires confirmation and labeling.
- `BLOCKED` must not be stored.
- `STRATEGIC_OPINION` must be labeled as recommendation or opinion, not fact.
- Simple durable facts and preferences may target `EXISTING_MEMORY_PROPOSAL_FLOW`.
- Rich criterio and synthesis may target `FUTURE_CRITERIO_STORE`.
- Session synthesis may target `SESSION_ONLY`.
- Sensitive or unconfirmed inference must not become confirmed truth.

## Daily Start

Daily Start triggers include:

```text
Que hago hoy?
Por donde empiezo?
Estoy atorado
Ayudame a arrancar
```

The Daily Start scaffold includes:

```text
Estado
Arranque
Primera accion
Despues
Evita
Backlog
```

Rules:

- one starting priority;
- no more than three commitments;
- one concrete first action;
- one transition to the next block;
- explicit distractions to avoid;
- backlog parking for non-urgent ideas.

Daily Start is not a calendar, medical, psychological, therapy, coaching, legal, tax, financial, or employment-advice system. It is an execution-start scaffold.

## Priority Gate

New ideas are evaluated against:

1. Cash or active client impact.
2. Roboticxs or Zaubern core relevance.
3. Family, operational, or cognitive risk reduction.
4. Demo, delivery, or sale unblock.
5. Dispersion risk.

The priority gate may say:

```text
Not now.
Backlog.
This is interesting, but not priority.
Start with cash/client/risk before research.
Do not open GitHub, papers, or repos until the current priority closes.
```

Every priority gate result includes classification, recommendation, why, do-now, do-not-do-now, and backlog handling.

## Proactive Intervention Protocol

Roboticxs may proactively suggest an intervention only with evidence of repeated bottleneck, repeated dispersion, missed follow-up, unresolved open loop, dependency gap, priority conflict, or high-leverage opportunity.

Every proactive intervention must include observation, implication, recommendation, what not to do, classification, and authority label.

Sensitive context cannot be used silently. Sensitive inferences must be labeled and confirmation-gated.

## Budget Authority Dependency

66P depends on 65P Budget Authority Guard.

Rules:

- high-cost classification or synthesis must be capped or deferred;
- future-stage behavior remains deferred or blocked;
- 66P must not classify every message through premium reasoning by default;
- long-context synthesis requires a cap, confirmation, or deferral;
- Budget Authority Guard results must be recorded or testable where invoked.

In v0, local deterministic classification can run as simple classification. Future or high-cost continuity work is routed through the 65P guard.

## Memory Stack Boundary

66P defines the semantic and authority contract that future storage must respect.

67P owns Memory Stack Architecture / Criterio Store Spec. 66P does not decide where long-term criterio is stored.

Allowed in 66P:

- produce memory candidates;
- route simple facts and preferences to the existing memory proposal flow;
- route rich criterio to `FUTURE_CRITERIO_STORE`;
- mark sensitive inference as confirmation-required;
- keep synthesis session-only.

Forbidden in 66P:

- new storage backend;
- schema migration;
- direct durable storage;
- Mirix integration;
- vector or graph store;
- full historical cross-thread retrieval.

## Non-Claims

66P does not claim therapeutic, medical, legal, tax, financial, employment, caregiver, or deterministic personal-understanding authority.

Roboticxs must not pressure the user using fear, family, money, or health context. It must not upsell aggressively based on sensitive context. It must not execute external actions without confirmation and a separately approved authority surface.
