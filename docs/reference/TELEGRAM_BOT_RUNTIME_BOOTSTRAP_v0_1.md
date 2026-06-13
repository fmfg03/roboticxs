# Telegram Bot Runtime Bootstrap v0.1

## Status

Stage 79P adds a minimal Telegram bot runtime-channel foundation for Roboticxs.

It adapts Telegram text webhook payloads into the 78P Hermes-compatible runtime foundation and prepares a Telegram text response payload through a local sender abstraction.

## Decision

79P is a runtime-channel foundation stage.

It establishes a Telegram webhook payload parser, minimal message extraction, a safe Telegram configuration boundary, a Telegram-to-Hermes runtime adapter, a Telegram response sender abstraction, and local tests for inbound and outbound behavior.

It does not implement caregiver routines, document intake, voice, proactive triggers, memory creation, `ProposedMemory` writes, retrieval, connectors, scheduled jobs, production deployment, WhatsApp, Telegram payments, Telegram group relay, or full Telegram command UX.

## Why Telegram follows Hermes

78P created the Hermes-compatible runtime foundation. Telegram can now be added as the first MVP channel by converting inbound text into a `HermesRuntimeRequest` and using the local runtime dispatch boundary.

## Runtime channel flow

```text
Telegram update payload
  -> parsed Telegram message
  -> HermesRuntimeRequest
  -> Hermes runtime dispatch
  -> Telegram response payload/client abstraction
```

The 79P flow is local and deterministic in tests.

## Parser scope

The parser supports only Telegram `message` payloads with:

- `message_id`
- `chat.id`
- `from.id`
- non-empty `text`

It extracts optional username, first name, update id, and chat type as metadata.

## Hermes runtime adapter

The adapter converts a parsed Telegram text message into:

- `user_id`: Telegram sender id as text
- `channel`: `telegram`
- `text`: normalized Telegram text
- metadata containing Telegram chat id, message id, username, first name, update id, and chat type

The adapter dispatches through `dispatch_hermes_runtime_request()` from `app.hermes_runtime`.

## Sender abstraction

79P prepares a local Telegram `sendMessage` payload.

It does not call the Telegram API.
It does not create an HTTP client.
It does not expose the bot token.
It records only whether a token is configured.

## Configuration boundary

The Telegram bot token is read through `TELEGRAM_BOT_TOKEN` into `Settings.telegram_bot_token`.

Runtime responses expose only `token_configured`, not the token value.

Tests do not require a real bot token and do not call Telegram.

## Web binding

79P adds a separate minimal FastAPI route:

```text
POST /api/telegram/runtime/webhook
```

This route is intentionally separate from the existing product-oriented `/api/telegram/webhook` path. The new route returns local structured runtime information and a prepared send payload.

## Unsupported payload behavior

Missing messages, missing chat/user/message ids, empty text, documents, files, voice, and audio payloads fail safely with a local unsupported response.

Unsupported payloads do not crash and do not call Hermes dispatch.

## What is intentionally not implemented

- caregiver runtime
- guided routines
- document/PDF receive
- file downloads
- voice messages
- Telegram payments
- Telegram group relay
- proactive/background messages
- `MemoryItem` writes
- `ProposedMemory` writes
- retrieval
- connectors
- scheduler/background jobs
- WhatsApp
- production deployment
- secret exposure
- real Telegram API calls in tests
- full Telegram command UX

## Authority boundaries

Telegram runtime bootstrap does not authorize caregiver behavior.
Telegram runtime bootstrap does not authorize document or file behavior.
Telegram runtime bootstrap does not authorize voice behavior.
Telegram runtime bootstrap does not authorize memory writes.
Telegram runtime bootstrap does not authorize retrieval.
Telegram runtime bootstrap does not authorize connectors.
Telegram runtime bootstrap does not authorize background/proactive messaging.
Telegram runtime bootstrap does not authorize production deployment.
Telegram runtime bootstrap does not authorize 80P as `NEXT_ELIGIBLE`.
Validation pass does not imply staging authority.
Validation pass does not imply commit authority.

## Non-claims

79P does not claim production Telegram bot readiness.
79P does not claim real Telegram API delivery.
79P does not claim caregiver, document, voice, retrieval, connector, memory, scheduler, WhatsApp, or deployment support.
79P does not claim a complete Telegram command UX.
