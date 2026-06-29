# Premium Telegram UX Shell 191P v0.1

Status: 191P implemented pending review.

## Purpose

191P upgrades the Telegram product shell from a flat command list to a grouped control surface.

It organizes customer-facing commands by intent:

- Today
- Prep
- Pilot
- Suggestions
- Drafts
- Memory
- Documents
- Usage
- Status

## State labels

The shell uses only these customer-visible state labels:

- `ready`
- `needs setup`
- `blocked`
- `draft-only`
- `approval-required`

## Telegram surfaces

191P updates:

- `/start`
- `/help`
- `/status`
- startup report metadata

It does not change command execution behavior.

## Boundaries

191P does not authorize:

- Gmail send;
- Gmail archive, label, delete, or thread modification;
- Calendar writes;
- OAuth URL generation;
- token exchange;
- token refresh;
- connector activation;
- Memory Center mutation;
- model calls;
- tool calls;
- workers;
- scheduler;
- billing;
- payments;
- deployment, push, merge, or PR creation.

## Non-claims

- no real Telegram buttons;
- no callback handlers;
- no persistence;
- no cache;
- no ranking;
- no priority engine;
- no draft quality engine;
- no memory intelligence;
- no document-to-action flow;
- no cost-aware model routing v1.
