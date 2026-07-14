# Telegram Conversation Loop v0.1

## Status

Stage 80P establishes the first minimal local Telegram conversation loop for Roboticxs.

It builds on the 78P Hermes runtime foundation and the 79P Telegram runtime bootstrap.

## Decision

80P establishes a minimal Telegram conversation loop for Roboticxs.
It builds on the Hermes runtime foundation and Telegram runtime bootstrap.
It supports text-message loop handling only.
It does not implement caregiver routines.
It does not implement document intake.
It does not implement voice handling.
It does not implement memory writes.
It does not implement ProposedMemory writes.
It does not implement retrieval.
It does not implement connectors.
It does not implement proactive messaging.
It does not call the real Telegram API in tests.
It does not authorize production deployment.

## Why this stage exists

79P proved that Telegram text payloads can be parsed, adapted into a `HermesRuntimeRequest`, and converted into a prepared `sendMessage` payload.

80P makes that path minimally usable by returning deterministic safe replies for valid text and predictable safe fallbacks for empty, unsupported, malformed, and runtime-error cases.

## Conversation loop path

```text
Telegram text update
  -> Telegram runtime parser
  -> HermesRuntimeRequest
  -> Hermes runtime dispatch
  -> Telegram reply payload
  -> safe response body for webhook/runtime caller
```

The existing `/api/telegram/runtime/webhook` route uses this loop.

## Supported input

80P supports Telegram `message` payloads with a non-empty text body, `message_id`, `chat.id`, and `from.id`.

The loop preserves chat id, user id, message id, username, first name, update id, and chat type in local response or trace metadata.

## Unsupported input

Documents, files, voice, audio, images, payments, group relay behavior, and empty text are not processed as product work.

Unsupported non-text content returns:

```text
Por ahora solo puedo procesar mensajes de texto.
```

Empty text returns:

```text
No recibí texto para procesar.
```

## Error behavior

Malformed payloads return a safe ignored-update response when no chat id is available.

Runtime dispatch exceptions return a safe fallback message without stack traces.

User-facing responses do not include Python exceptions, tracebacks, file paths, or internal call stacks.

## Trace behavior

80P uses local response metadata only. Task and TaskRun persistence are deferred because the Telegram runtime path is deliberately separate from the older product orchestrator that writes database records.

Trace metadata records:

- stage `80P`
- loop name
- persistence status `deferred`
- external Telegram API call status `false`
- local error code when applicable

## Runtime dispatch behavior

Valid text is converted into a `HermesRuntimeRequest` and dispatched through the 78P Hermes runtime foundation.

The loop returns a deterministic local reply:

```text
Hermes runtime foundation is available. Telegram/channel integration is active. Full skills are not implemented yet.
```

## Telegram response behavior

80P prepares a local Telegram `sendMessage` payload.

It does not call the real Telegram API.
It does not create an HTTP client.
It does not expose the Telegram bot token.

## What is intentionally not implemented

- caregiver routines
- guided routines
- medication logic
- medical advice
- document/PDF intake
- Telegram file download
- Telegram voice message handling
- voice transcription
- outbound real Telegram API calls in tests
- payment handling
- group relay
- proactive/background messaging
- scheduler or cron
- memory writes
- `ProposedMemory` writes
- retrieval
- connectors
- model-router changes
- budget-governor changes
- deployment work
- production secret handling beyond the existing config boundary
- WhatsApp

## Future stages unlocked

80P makes it possible for future approved stages to add a richer Telegram conversation loop, persistence, product skills, safety copy, memory UX, and eventually real delivery behavior.

Those future stages require explicit maintainer authorization.

## Authority boundaries

The conversation loop does not authorize caregiver behavior.
The conversation loop does not authorize document or file handling.
The conversation loop does not authorize voice handling.
The conversation loop does not authorize memory writes.
The conversation loop does not authorize `ProposedMemory` writes.
The conversation loop does not authorize retrieval.
The conversation loop does not authorize connectors.
The conversation loop does not authorize proactive or background messaging.
The conversation loop does not authorize production deployment.
The conversation loop does not authorize 81P as `NEXT_ELIGIBLE`.
Validation pass does not imply staging authority.
Validation pass does not imply commit authority.

## Non-claims

80P does not claim production Telegram readiness.
80P does not claim real Telegram API delivery.
80P does not claim long-term conversation memory.
80P does not claim user profile memory.
80P does not claim caregiver, document, voice, retrieval, connector, scheduler, WhatsApp, or deployment support.
80P does not claim full Telegram command UX.
