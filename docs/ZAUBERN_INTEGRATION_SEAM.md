# Zaubern Integration Seam

> **Status:** Day 1 evidence and decision boundary; no adapter exists yet.
>
> **Source cutoff:** OpenHuman `61e80bea0dbe92cb45868737a5db56a5a840a0d3`,
> inspected 2026-09-21.

## Chosen seam

The seam is OpenHuman's `ApprovalSecurityMiddleware::wrap_tool` in
`crates/openhuman-core/src/agent/tinyagents/middleware/approval.rs`.

At this point OpenHuman has a concrete `tool` name and JSON `arguments`; it
has not yet called the canonical tool because the middleware invokes the
native execution handler only through `next.run(...)` afterwards.  The
middleware already asks `external_effect_with_args(arguments)`, making this a
per-action rather than merely per-tool decision point.

```text
proposed tinyagents tool call
  -> OpenHuman session/tool policy
  -> Roboticxs authority adapter at approval middleware
  -> Zaubern.evaluate(envelope)
  -> ALLOW | DRAFT_ONLY | ASK_CONFIRMATION | BLOCK | AUTHORITY_UNAVAILABLE
  -> only an allowed, confirmation-bound call reaches next.run(...)
  -> canonical OpenHuman tool execution
  -> terminal receipt/audit projection
```

## Non-negotiable rules

- `AUTHORITY_UNAVAILABLE`, malformed authority response, timeout, stale
  decision, missing actor/robot/action binding, or missing confirmation for an
  `ASK_CONFIRMATION` action means **do not execute**.
- `DELETE` and `PAYMENT` are blocked before native execution in the MVP.
- A `SEND_EMAIL` decision must bind the normalized arguments and
  `execution_id`; a confirmation for one proposal cannot authorize another.
- The only productive external action in scope is the controlled email
  follow-up.  It must have a terminal receipt that distinguishes proposed,
  authorized, dispatched and acknowledged/failed states.
- Neither a Telegram affirmative reply nor an OpenHuman approval record is a
  substitute for Zaubern authority.

## Required Day 3 proof

Tests must prove that each protected class cannot reach a fake native tool
executor without the adapter's appropriate result:

| Class | Zaubern result | Expected native executor calls |
| --- | --- | --- |
| READ | `ALLOW` | 1 |
| DRAFT | `ALLOW` | 1 |
| SEND_EMAIL before confirmation | `ASK_CONFIRMATION` | 0 |
| SEND_EMAIL after valid bound confirmation | `ALLOW` | 1 |
| DELETE | `BLOCK` | 0 |
| PAYMENT | `BLOCK` | 0 |
| Zaubern unavailable | fail closed | 0 |

The suite must cover the normal direct-tool path and the packed/indirect path
if that path can resolve a protected tool.  It must include duplicate and
retry cases before Day 6 hardening is declared complete.

## Why not alter tinyagents

tinyagents owns the loop and tool-call mechanics, while OpenHuman owns policy
and approval.  Changing tinyagents would broaden the upstream fork surface and
would bypass the already-confirmed OpenHuman ownership boundary.  A narrow
OpenHuman middleware change or an equivalent supported extension at this
exact point is therefore the only candidate for Day 3.

## Open question that blocks implementation

The exact supported extension mechanism for registering a Roboticxs middleware
from an embedded host, without carrying a long-lived OpenHuman source fork,
must be demonstrated in the completed baseline.  If OpenHuman exposes no
such extension point, modifying only the middleware assembly is a material
architecture decision and needs a technical-spec checkpoint before Day 3.
