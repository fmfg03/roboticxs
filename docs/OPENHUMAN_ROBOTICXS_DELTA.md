# OpenHuman → Roboticxs Delta

> **Status:** Day 1 classification only.  The list deliberately contains only
> `KEEP`, `WRAP`, `MODIFY`, and `BUILD`.
>
> **Source cutoff:** OpenHuman `61e80bea0dbe92cb45868737a5db56a5a840a0d3`,
> inspected 2026-09-21.

## KEEP

- `tinyagents` agent loop, tool-call dialect, tool catalogue rendering and
  replay.
- OpenHuman's execution policy, canonical tool contract, sandbox and timeout
  mechanisms.
- `openhuman_embed::Runtime -> Agent` as the integration API.
- Telegram transport and its existing approval reply surface.
- Durable workflows/checkpoints/resume over tinyflows.
- Memory host/TinyMemory, authorized connector plumbing, model routing, and
  cost/progress accounting.

## WRAP

- Roboticxs identity, one robot, product configuration, branding, policies
  and skill assets around an embedded OpenHuman runtime.
- Roboticxs Context Scan product flow over only Gmail, Calendar and Documents;
  the wrapper selects the authorized sources and presents provenance.
- Roboticxs memory lifecycle: discovered context becomes a candidate; only a
  user `APPROVE`, `EDIT`, or `REJECT` creates trusted Roboticxs memory.
- Meeting Briefing composition and Telegram copy, using upstream retrieval,
  memory and workflow primitives rather than replacing them.
- Read-only/low-risk action classification and a Roboticxs audit projection.

## MODIFY

- The external-effect boundary must become fail-closed for protected actions.
  At the confirmed tool-middleware seam, an unavailable Zaubern authority
  result must prevent `next.run(...)`; the current absent-global-gate path is
  not sufficient.
- OpenHuman's native approval decision must be subordinated to a fresh Zaubern
  decision bound to the proposed tool call and the user confirmation.  A
  confirmation alone must never authorize `send_email`.
- The minimum protected-action intercept coverage must include direct native
  tool calls and any indirect/packed tool route that reaches the canonical
  adapter.  This is a testable modification, not a claim that the current
  middleware proves it already.

## BUILD

- A Roboticxs authority adapter and minimal envelope:

  ```json
  {
    "actor": "...",
    "robot": "...",
    "action": "...",
    "resource": "...",
    "arguments": {},
    "context": {},
    "risk_class": "...",
    "execution_id": "..."
  }
  ```

- The minimal decision mapping: `READ -> ALLOW`, `DRAFT -> ALLOW`,
  `SEND_EMAIL -> ASK_CONFIRMATION`, `DELETE -> BLOCK`, and `PAYMENT -> BLOCK`.
- Binding between proposed action, Zaubern decision, confirmation, execution
  attempt and terminal effect receipt, including idempotency/retry semantics.
- A narrow Meeting Briefing skill/workflow and acceptance tests for the six
  binary demo checks.

## Explicitly not in this delta

- Billing, Stripe, subscriptions, marketplace, WhatsApp, mobile, multiple
  robots, full Agentius, full Zaubern enterprise protocol, commercial site,
  dashboard polish, mass connector rollout, provider optimization, or a
  migration away from OpenHuman components.

## Governing upstream rule

> Do not improve OpenHuman merely because its architecture differs from the
> architecture we would have designed. Modify upstream behavior only when a
> concrete Roboticxs requirement cannot be satisfied by configuration or
> composition.
