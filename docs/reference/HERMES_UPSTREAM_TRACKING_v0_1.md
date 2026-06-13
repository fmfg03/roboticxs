# Hermes Upstream Tracking v0.1

## Status

Stage 78P records Hermes Agent as the external upstream source of record for Roboticxs runtime-foundation alignment.

This document is tracking metadata only. It does not import upstream Hermes code, install Hermes dependencies, execute Hermes scripts, or authorize future Hermes feature adoption.

## Upstream repository

Upstream repository: https://github.com/NousResearch/hermes-agent

## Upstream owner

Upstream owner: NousResearch

## Source status

Project name: Hermes Agent
Source status: EXTERNAL_UPSTREAM_SOURCE

## Roboticxs approval status

Roboticxs approval status: FOUNDATION_REFERENCE_ONLY

Hermes upstream is approved as a foundation reference only. Hermes upstream features, defaults, scripts, dependencies, gateways, connectors, memory patterns, model-routing behavior, or security assumptions do not automatically become Roboticxs behavior.

## Inspected version

- Inspected branch or tag: unknown-not-cloned-in-78P
- Inspected commit SHA: unknown-not-available-locally
- Inspection date: 2026-06-13
- Local compatibility target: Roboticxs Hermes-compatible runtime foundation v0.1

78P does not run network commands, clone upstream Hermes, install Hermes, or execute Hermes install scripts. Commit-level upstream inspection is intentionally deferred to a future explicit maintainer-authorized update-review stage.

## Adopted concepts

- A named runtime foundation boundary.
- A local runtime status/health object.
- A structured request object.
- A structured response object.
- Explicit upstream source tracking.
- Explicit separation between upstream reference and local product authority.

## Not adopted in 78P

- Hermes upstream package import.
- Hermes upstream install scripts.
- Hermes gateways.
- Hermes provider configuration.
- Hermes Telegram, messaging, or channel adapters.
- Hermes memory, scheduler, retrieval, connector, tool, shell, or browser execution behavior.
- Hermes dependency tree.
- Hermes runtime deployment templates.
- Hermes security defaults as automatic Roboticxs defaults.

## Drift risks

- Hermes runtime abstractions may change.
- Hermes gateway or channel patterns may change.
- Hermes model/provider routing may change.
- Hermes memory and skill patterns may change.
- Hermes security or tool-authority assumptions may change.
- Roboticxs may drift if future runtime stages do not periodically review upstream before extending local runtime behavior.

## Update cadence

Default cadence: review Hermes upstream at least once per active Roboticxs runtime sprint.
Trigger review sooner if Hermes releases a major runtime, gateway, Telegram, memory, skill, scheduler, security, or provider-routing update.
Do not auto-update dependencies.
Do not auto-pull upstream code.
Do not run upstream install scripts inside the Roboticxs repo during 78P.

## Update procedure

1. Open a future maintainer-authorized stage for Hermes upstream review.
2. Inspect the upstream repository, branch or tag, and commit SHA in a controlled read-only pass.
3. Compare upstream runtime, gateway, model, skill, scheduler, security, and provider-routing changes against the local Roboticxs compatibility boundary.
4. Document adopted and intentionally rejected concepts.
5. Request story and technical-spec approval before changing local runtime behavior.
6. Run scoped implementation, tests, validation, and separate staging/commit approval if changes are authorized.

## Explicit non-auto-update rule

Hermes upstream changes do not automatically modify Roboticxs runtime.
Hermes upstream changes must be reviewed through a future explicit maintainer-authorized stage before adoption.
Roboticxs should periodically review Hermes upstream so the local foundation does not drift behind important Hermes runtime, gateway, model, skill, or security changes.

Do not auto-update dependencies.
Do not auto-pull upstream code.
Do not execute Hermes upstream install scripts.

## Future adoption gate

Future Hermes upstream adoption requires explicit maintainer authorization.

Any future adoption must preserve Roboticxs authority, cost, memory, safety, credential, connector, retrieval, channel, scheduler, and product-claim boundaries.

## Non-claims

This tracking document does not claim that Roboticxs is running Hermes Agent.
This tracking document does not claim full Hermes compatibility.
This tracking document does not claim the inspected upstream commit is known locally.
This tracking document does not authorize Hermes dependency installation.
This tracking document does not authorize Hermes install script execution.
This tracking document does not authorize Telegram, caregiver, document intake, connector, retrieval, memory-write, scheduler, shell, browser, or deployment behavior.
This tracking document does not authorize staging or commit.
