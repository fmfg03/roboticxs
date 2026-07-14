# ROBOTICXS — Brief Additions: Hermes / Routing / Web Task v0.1

> **Project:** Roboticxs.com
> **Document type:** Official addendum to `ROBOTICXS_PROJECT_BRIEF.md`
> **Status:** Planning addendum / Not implemented runtime behavior
> **Date:** 2026-06-01
> **Purpose:** Capture the valid planning additions from the Hermes, LLM routing, low-latency, and Web Task discussion without implying current runtime implementation.

This addendum extends the main project brief. It does not mean the repo already implements Hermes integration, Webwright integration, browser automation, or the future specs referenced below.

## 1. Core framing update

Correct framing:

```text
Hermes = runtime engine / substrate
Roboticxs = product, control plane, memory approval, routing policy, approvals, safety boundaries, and consumer experience
```

Roboticxs should not expose Hermes, MCP, Playwright, terminal execution, model routing internals, or infrastructure concepts to normal users.

User-facing promise remains:

> One personal AI robot that remembers your context, helps with real work, and knows what it is not allowed to do.

## 2. Control plane over runtime

Roboticxs should own the product control plane above Hermes.

That control plane includes:
- user account
- robot profile
- skill subscriptions
- memory approval
- scope guard
- safety layer
- token budget
- model routing policy
- upgrade and opportunity signals

Hermes should be treated as runtime substrate for:
- persistent operation
- scheduled tasks
- skills
- tool connections
- provider calls
- runtime logging

Hermes should not be treated as:
- the consumer UX
- the safety layer
- the memory approval layer
- the authority boundary
- the final orchestration policy

## 3. Memory rule update

Roboticxs does not accept "remember everything" behavior.

Correct memory rule:

> The robot may detect possible memories, but the user approves what becomes durable memory.

Default expectations:
- do not store raw data by default
- store extracted, user-approved facts and preferences
- allow memory edit / forget / pin / outdated labeling
- do not turn browser-task outputs into memory unless approved

## 4. Autonomy translation rule

Hermes-style "runs without you" language should not be used directly in Roboticxs consumer positioning.

Correct Roboticxs framing:
- works on schedule
- prepares useful actions
- asks before doing anything sensitive

Allowed bounded background work:
- scheduled briefs
- reminders
- document preparation
- source monitoring within permission
- recurring admin preparation
- draft generation
- appointment search
- cart or checklist preparation

Not allowed silently:
- payment execution
- legal acceptance
- credential or permission change
- destructive action
- customer-facing send
- production deployment
- regulated professional decisions

## 5. Routing principle update

Roboticxs should use a mixed LLM stack, but the asset is the routing policy, not the model list.

Core rule:

> Route by policy first, model second.

Routing policy should evaluate:
- task class
- risk level
- user plan
- skill scope
- budget remaining
- latency target
- context size
- file type
- required quality
- action class
- provider health
- data sensitivity
- reviewer requirement

Model choice does not decide authority.

## 6. Low-latency routing requirement

Routing should stay near-instant for normal interactions.

Preferred pattern:

```text
User message
  -> fast intent parser
  -> deterministic policy router
  -> only if needed: cheap classifier / safety reviewer / premium escalation
  -> worker model
  -> stream response or move to background
```

Principle:

> Acknowledge immediately, route cheaply, stream when useful, and move long work to bounded background execution.

## 7. Two execution lanes

Roboticxs should separate realtime interaction from background work.

Realtime lane:
- questions
- quick summaries
- memory lookup
- quick drafts
- confirmations

Background lane:
- long document review
- research
- recurring preparation
- browser-task preparation
- async reports

Background work must remain:
- bounded
- auditable
- resumable
- approval-based at sensitive boundaries

## 8. Web Task Worker / Webwright status

Webwright should be treated as an experimental browser task worker candidate.

Correct framing:

```text
Webwright = experimental browser task worker
Roboticxs = user-facing product and safety control plane
```

Status:
- experimental
- sandbox-first
- not live browser automation
- not production-proven

Hard boundaries:
- not permission to execute payments
- not permission to accept legal terms
- not permission to change credentials or account settings
- not permission to perform destructive actions

## 9. Future specs to produce

The following are planned documentation/spec work, not implemented runtime:

- `docs/HERMES_ADAPTER_SPEC_v0_1.md`
- `docs/LATENCY_ROUTING_SPEC_v0_1.md`
- `docs/WEB_TASK_WORKER_SPEC_v0_1.md`

## 10. Demo updates

Updated first demo:

```text
Telegram + Memory Approval + Document Review + Meeting Briefing + Low-Latency Model Routing
```

Second demo candidate:

```text
Telegram + Web Task Worker + Appointment Search + Human Confirmation
```

These are planning targets, not current runtime claims.

## 11. Non-claims

Roboticxs must not claim:
- full autonomy
- automatic durable memory capture
- payment execution
- legal/medical/financial advice
- guaranteed browser workflow success
- that Hermes alone provides safety
- that Webwright is already approved for user-facing workflows

Correct claims:
- Roboticxs can help prepare tasks
- Roboticxs asks before sensitive actions
- Roboticxs lets users approve memory
- Roboticxs routes tasks to cost-appropriate models
- Roboticxs can support bounded scheduled workflows with limits

