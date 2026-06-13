# Hermes Runtime Foundation Bootstrap v0.1

## Status

Stage 78P establishes a minimal local Hermes-compatible runtime foundation for Roboticxs.

This is a runtime-foundation stage, not a Telegram, caregiver, document intake, connector, retrieval, memory-write, scheduler, or deployment stage.

## Decision

78P establishes the Hermes runtime foundation for Roboticxs.
It does not implement Telegram.
It does not implement caregiver routines.
It does not implement document intake.
It does not implement connectors.
It does not implement retrieval.
It does not create memory automatically.
It does not import Hermes wholesale.
It does not execute Hermes upstream install scripts.
It does not auto-update from Hermes upstream.
It creates a local compatibility boundary for future runtime stages.

## Why Hermes comes first

Roboticxs needs a stable runtime foundation before later product stages add Telegram, caregiver routines, document intake, proactive triggers, memory UX, or skill packages.

The foundation lets Roboticxs align with Hermes Agent concepts while preserving Roboticxs authority, cost, memory, safety, and product boundaries.

## Upstream source

Upstream repository: https://github.com/NousResearch/hermes-agent
Upstream owner: NousResearch
Project name: Hermes Agent
Source status: EXTERNAL_UPSTREAM_SOURCE
Roboticxs approval status: FOUNDATION_REFERENCE_ONLY

Hermes upstream is a reference source for runtime design. It is not automatic authority over Roboticxs runtime.

## Runtime foundation scope

78P adds a small standard-library runtime module at `app/hermes_runtime.py`.

The module provides:

- `HermesRuntimeStatus`
- `HermesRuntimeRequest`
- `HermesRuntimeResponse`
- `get_hermes_runtime_status()`
- `dispatch_hermes_runtime_request()`

The implementation is local, deterministic, and does not require network access, Telegram, connectors, retrieval, memory writes, shell execution, dependency installation, or upstream Hermes code.

## Local compatibility boundary

The 78P architecture boundary is:

```text
Hermes upstream concepts
        ↓
Roboticxs compatibility boundary
        ↓
Roboticxs runtime runner
        ↓
Roboticxs orchestrator / task / memory / budget / safety layers
        ↓
Telegram and product skills in later stages
```

The current local orchestrator is Telegram/session/settings based and can create user, robot, task, route, token, and safety records. 78P therefore does not call that orchestrator from the Hermes runtime dispatch path. It records the adapter boundary and returns a deterministic foundation response.

## Minimal runtime interface

The local runtime interface uses frozen dataclasses:

```python
HermesRuntimeStatus
HermesRuntimeRequest
HermesRuntimeResponse
```

The status object reports runtime availability, upstream repository metadata, compatibility status, and whether a safe orchestrator adapter is available.

The request object accepts local text, user, channel, and metadata fields.

The response object returns a structured status, response text, optional task id, optional safety decision, and metadata.

## Dispatch behavior

78P supports only a deterministic local dispatch path:

```text
input text
  -> Hermes runtime request object
  -> local compatibility boundary
  -> structured runtime response
```

For non-empty input, the dispatch response is:

```text
Hermes runtime foundation is available. Telegram/channel integration is not implemented yet.
```

Empty text is rejected locally without side effects.

## Health/status behavior

`get_hermes_runtime_status()` returns an available local foundation status.

The status includes:

- runtime name
- local availability
- upstream repository URL
- upstream owner
- Hermes project name
- source status
- Roboticxs approval status
- explicit flags showing Telegram, memory writes, retrieval, and connectors are not enabled

## What is intentionally not implemented

- Telegram implementation
- Discord, Slack, WhatsApp, or Signal implementation
- caregiver routines
- document/PDF intake
- voice
- Agent-Reach
- VoxCPM
- connectors
- live retrieval
- automatic memory creation
- `ProposedMemory` writes
- database migrations
- scheduler, cron, or background jobs
- autonomous skill creation
- browser/computer-use
- shell execution feature
- Hermes dependency installation
- Hermes upstream install script execution
- credential handling
- cloud or Docker deployment

## Future Telegram dependency

Future Telegram work should depend on this runtime foundation only after a later maintainer-authorized stage defines the Telegram channel adapter, authority checks, persistence behavior, and tests.

78P does not add Telegram handler behavior and does not change `/api/telegram/webhook`.

## Future caregiver dependency

Future caregiver stages may use this runtime foundation only after explicit maintainer authorization for caregiver runtime behavior, sensitive memory boundaries, routine execution rules, and safety checks.

78P does not add caregiver runtime behavior.

## Authority boundaries

- Hermes upstream is a reference, not automatic authority.
- Hermes upstream code is not imported wholesale.
- Hermes install scripts are not executed.
- Hermes new releases do not auto-change Roboticxs.
- Hermes features do not become Roboticxs product claims.
- Runtime foundation does not mean external channel support.
- Runtime foundation does not mean autonomous tool authority.
- Runtime foundation does not mean memory write authority.
- Runtime foundation does not mean scheduler/background authority.
- Runtime foundation does not mean connector authority.
- Validation pass does not imply staging authority.
- Validation pass does not imply commit authority.

## Non-claims

78P does not claim full Hermes compatibility.
78P does not claim production readiness.
78P does not claim Telegram support.
78P does not claim caregiver support.
78P does not claim document intake support.
78P does not claim connector support.
78P does not claim retrieval support.
78P does not claim memory-write support.
78P does not claim scheduler support.
78P does not claim background-job support.
78P does not authorize 79P as `NEXT_ELIGIBLE`.
