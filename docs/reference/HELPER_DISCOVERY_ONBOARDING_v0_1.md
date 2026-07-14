# Helper Discovery Onboarding v0.1

## Purpose

Allow an explicitly permitted Telegram user to receive an independent Robbie and complete a consent-based discovery interview. The interview identifies where Robbie can reduce cognitive or administrative load without inheriting the founder's memory or authority.

## Access model

- `ROBOTICXS_OWNER_ID` remains the founder and administrative owner.
- `ROBOTICXS_TELEGRAM_ALLOWED_USER_IDS` contains additional conversation users.
- A configured founder owner is required; without it, the webhook fails closed.
- Additional users receive separate `User`, `Robot`, `ConversationTurn`, `MemoryItem`, and `HelperDiscoverySession` scopes.
- Additional users are accepted only in private Telegram chats; group messages fail closed.

## Interview

For an allowed non-owner, `/start` begins a five-question interview:

1. Situation to improve.
2. Recurring load or missed work.
3. People and responsibilities involved.
4. Desired kinds of help.
5. Boundaries on action, storage, and sharing.

The interview asks one question per message. `/pausar`, `/continuar`, and `/cancelar` control the session.

## Consent and retention

- No substantive answer is stored before explicit consent.
- Consented interview answers are temporary and expire after 24 hours.
- Cancellation or expiration clears the temporary answers.
- Completion presents a summary and proposed forms of help.
- The summary is not active memory.
- `GUARDAR PERFIL` creates a `ProposedMemory`; the existing explicit memory approval command is still required before it becomes active.

## Safety boundaries

- No diagnosis or medical decision.
- No medication instruction or validation.
- No external action authority.
- No automatic sharing with the founder, family, caregiver, or another robot.
- No cross-user memory or conversation lookup.

## Production configuration

```text
ROBOTICXS_OWNER_ID=<founder Telegram id>
ROBOTICXS_TELEGRAM_ALLOWED_USER_IDS=<comma-separated Telegram user ids>
ROBOTICXS_HELPER_DISCOVERY_ENABLED=true
```

Telegram bot credentials and concrete user IDs remain deployment secrets/configuration and are not committed.
