# Telegram Runtime Smoke / Manual Bot Wiring v0.1

## Status

Stage 81P establishes a safe manual Telegram runtime smoke path.

It builds on the 78P Hermes runtime foundation, the 79P Telegram runtime bootstrap, and the 80P Telegram conversation loop.

## Decision

81P establishes a safe manual Telegram runtime smoke path.
It does not implement production deployment.
It does not automatically register Telegram webhooks.
It does not call the real Telegram API in tests.
It does not commit Telegram secrets.
It does not implement caregiver routines.
It does not implement document intake.
It does not implement memory writes.
It does not implement ProposedMemory writes.
It does not implement retrieval.
It does not implement connectors.
It does not implement proactive messaging.

## Why this stage exists

Roboticxs can now parse Telegram text updates, dispatch them through the local Hermes runtime foundation, and prepare a deterministic Telegram reply payload.

Before adding memory, caregiver routines, documents, voice, retrieval, connectors, proactive behavior, or deployment automation, the operator needs a safe manual path to wire a real Telegram bot token and public webhook URL without exposing secrets or claiming production readiness.

## Required environment variables

- `TELEGRAM_BOT_TOKEN`: real Telegram bot token, configured only in the local runtime environment.
- `TELEGRAM_PUBLIC_WEBHOOK_URL`: public HTTPS URL that Telegram can call and that routes to `/api/telegram/runtime/webhook`.

Example shape:

```text
TELEGRAM_PUBLIC_WEBHOOK_URL=https://example.com/api/telegram/runtime/webhook
```

Do not commit `.env` files, bot tokens, shell history, terminal transcripts with secrets, or Telegram API responses that include secrets.

## Secret handling rules

The bot token is treated as a secret.

Diagnostics may report only whether the token is configured.
Diagnostics must not print the raw token, token prefix, token suffix, token length, or token embedded in a URL.
Webhook URLs that contain the token are invalid for 81P readiness.

## Webhook path

The runtime webhook path is:

```text
POST /api/telegram/runtime/webhook
```

This is the 80P Telegram conversation loop route. It is separate from the older product-oriented `/api/telegram/webhook` route.

## Manual webhook setup checklist

1. Create or select a Telegram bot through BotFather outside this repository.
2. Configure `TELEGRAM_BOT_TOKEN` in the local runtime environment.
3. Expose the local app through an operator-managed HTTPS URL if needed.
4. Configure `TELEGRAM_PUBLIC_WEBHOOK_URL` so it ends with `/api/telegram/runtime/webhook`.
5. Verify local readiness through the 81P readiness helper before wiring Telegram.
6. Manually register the webhook outside the repo using the Telegram API or Telegram tooling.
7. Do not paste the bot token into committed files, docs, test fixtures, or issue comments.

Optional tunnel tools such as ngrok or cloudflared may be used manually by the operator. 81P does not add automation for them.

## Manual smoke checklist

1. Start the local app using the current project command known to the operator.
2. Confirm `TELEGRAM_BOT_TOKEN` is configured in the process environment.
3. Confirm `TELEGRAM_PUBLIC_WEBHOOK_URL` is a public HTTPS URL for `/api/telegram/runtime/webhook`.
4. Run the local readiness check and confirm the token is redacted.
5. Manually set the Telegram webhook outside the repository.
6. Send `hola` to the bot.
7. Confirm the 80P deterministic conversation-loop reply is returned.
8. Confirm no memory, document, voice, retrieval, connector, proactive, or caregiver behavior occurs.

## Readiness behavior

Readiness is local only.

The readiness helper reports ready only when:

- `TELEGRAM_BOT_TOKEN` is configured.
- `TELEGRAM_PUBLIC_WEBHOOK_URL` is configured.
- `TELEGRAM_PUBLIC_WEBHOOK_URL` starts with `https://`.
- `TELEGRAM_PUBLIC_WEBHOOK_URL` ends with `/api/telegram/runtime/webhook`.
- `TELEGRAM_PUBLIC_WEBHOOK_URL` does not contain the bot token.

Missing token/config fails safely with machine-readable failure reasons.

## Redacted diagnostics

Diagnostics include:

- stage `81P`
- runtime webhook path
- token status as `configured_redacted` or `missing`
- webhook URL configured status
- webhook URL validity
- external Telegram API call status `false`
- automatic webhook registration status `false`
- production deployment status `false`

Diagnostics do not include the raw bot token.

## What is intentionally not implemented

- production deployment
- automatic Telegram webhook registration
- real Telegram API calls in tests
- committed bot tokens
- `.env` secret files
- deploy scripts
- Docker or cloud deployment
- ngrok or cloudflared automation
- caregiver routines
- guided routines
- medication logic
- document/PDF intake
- Telegram file download
- voice/audio handling
- memory writes
- `ProposedMemory` writes
- retrieval
- connectors
- proactive/background messaging
- scheduler
- WhatsApp

## Failure modes

- Missing `TELEGRAM_BOT_TOKEN` returns `telegram_bot_token_missing`.
- Missing `TELEGRAM_PUBLIC_WEBHOOK_URL` returns `telegram_public_webhook_url_missing`.
- Non-HTTPS, malformed, wrong-path, whitespace-containing, or token-containing webhook URLs return `telegram_public_webhook_url_invalid`.
- Runtime webhook payload failures continue to use the 80P safe conversation-loop fallbacks.

## Future stages unlocked

81P makes it possible for a future approved stage to add stronger operational smoke tooling, deployment-specific checks, or real webhook registration.

Those future stages require explicit maintainer authorization.

## Authority boundaries

The smoke path does not authorize production deployment.
The smoke path does not authorize automatic webhook registration.
The smoke path does not authorize real Telegram API calls in tests.
The smoke path does not authorize committed credentials.
The smoke path does not authorize caregiver behavior.
The smoke path does not authorize document or file handling.
The smoke path does not authorize voice handling.
The smoke path does not authorize memory writes.
The smoke path does not authorize `ProposedMemory` writes.
The smoke path does not authorize retrieval.
The smoke path does not authorize connectors.
The smoke path does not authorize proactive or background messaging.
The smoke path does not authorize 82P as `NEXT_ELIGIBLE`.
Validation pass does not imply staging authority.
Validation pass does not imply commit authority.

## Non-claims

81P does not claim production Telegram readiness.
81P does not claim deployment readiness.
81P does not claim webhook registration automation.
81P does not claim real outbound Telegram API delivery.
81P does not claim long-term conversation memory.
81P does not claim caregiver, document, voice, retrieval, connector, scheduler, WhatsApp, or proactive messaging support.
