# Controlled Live Pilot Baseline 190P v0.1

Status: 190P implemented pending review.

## Purpose

190P adds an owner-requested controlled pilot receipt that demonstrates the first connected Roboticxs customer flow:

`/daily_brief -> /prep -> suggestion -> draft -> approval -> Gmail draft creation -> source receipt -> usage receipt`

The receipt composes existing closed-stage capabilities. It does not create a new autonomous runtime or grant new execution authority.

## Pilot surface

Telegram exposes `/pilot` as a controlled owner-requested receipt.

The command renders:

- daily brief step;
- meeting prep step;
- proactive suggestion;
- draft intent;
- local draft queue;
- owner confirmation receipt;
- Gmail draft creation receipt;
- source trace receipt;
- usage/cost ledger receipt;
- explicit safety boundaries.

## Modes

`fixture`: Used when no live Gmail draft client is injected. It produces deterministic local evidence and a fixture Gmail draft id.

`live_capable`: Used when a Gmail draft client or Gmail draft token context is injected. It may create a Gmail draft through the already-approved 185P path after an explicit 178P approval receipt. It must never send email.

## Boundaries

190P does not authorize:

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

- no Premium Telegram UX shell;
- no fast path cache;
- no smart context ranking;
- no proactive priority engine;
- no draft quality engine;
- no memory intelligence;
- no document-to-action flow;
- no cost-aware model routing v1;
- no customer pilot docs pack.
