# Smart Context Ranking 193P v0.1

Status: 193P implemented pending review.

## Purpose

193P ranks Calendar, Gmail, Memory, and Document context before rendering customer-facing prep and daily brief outputs.

The ranking is deterministic, local, and transparent. It shows why each item was prioritized instead of returning unordered aggregation.

## Behavior

Ranked context items include:

- source type;
- source id;
- title;
- score;
- reason codes;
- source trace;
- safe next action.

`/daily_brief` and `/prep` append a `Prioritized context` section when rankable context is available.

## Boundaries

193P does not authorize:

- connector activation;
- new connector reads beyond the command's existing read-only path;
- Calendar writes;
- Gmail send;
- Gmail archive, label, delete, or thread modification;
- Memory Center mutation;
- model calls;
- tool calls;
- workers;
- scheduler;
- billing;
- payments;
- deployment, push, merge, or PR creation.

## Non-claims

- no proactive priority engine;
- no draft quality engine;
- no memory intelligence;
- no document-to-action flow;
- no cost-aware model routing v1;
- no customer pilot docs pack.
