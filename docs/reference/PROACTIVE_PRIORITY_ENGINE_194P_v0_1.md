# Proactive Priority Engine 194P v0.1

Status: 194P implemented pending review.

## Purpose

194P classifies suggestion inbox items as `P0`, `P1`, `P2`, or `P3` with explicit reason codes, confidence, source trace, and safe next action.

The engine improves signal quality and trust without sending messages, executing actions, binding callbacks, or calling models.

## Behavior

Suggestion inbox rendering includes:

- priority;
- confidence;
- reason codes;
- safe next action;
- priority source trace.

## Boundaries

194P does not authorize:

- proactive outbound sends;
- scheduler;
- callbacks;
- worker dispatch;
- connector activation;
- Calendar writes;
- Gmail send;
- Gmail archive, label, delete, or thread modification;
- Memory Center mutation;
- model calls;
- tool calls;
- external writes;
- deployment, push, merge, or PR creation.

## Non-claims

- no draft quality engine;
- no memory intelligence;
- no document-to-action flow;
- no cost-aware model routing v1;
- no customer pilot docs pack.
