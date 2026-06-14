# Roboticxs Script-Only Routines v0.1

Status: 88P implemented pending review.

This document defines no-agent/script-only routine boundaries for 88P. It is documentation/spec/test work only. It does not implement live Hermes cron execution, gateway delivery, connector activation, MCP/plugin activation, or production automation.

## Purpose

Some recurring routines should only compare source state and produce deterministic output. These routines must be able to run without waking the LLM and without invoking Model Router.

## Contract

No-agent/script-only routines never invoke Model Router.

No-agent/script-only routines set `wakeAgent=false`.

No-agent/script-only routines should have zero token usage.

Scripts detect changes; agents judge ambiguous or context-heavy changes only when `WAKE_AGENT` is selected and budget allows.

Scripts must not execute sensitive actions.

Scripts must not write directly to canonical Roboticxs Memory Center.

Failed scripts must produce observable error records.

Hermes memory remains runtime memory, not canonical Roboticxs memory.

## Allowed script-only outcomes

| Outcome | Meaning |
| --- | --- |
| `SKIP_NO_CHANGE` | No meaningful change. No delivery and no LLM wake. |
| `SCRIPT_ONLY_ALERT` | Deterministic alert is available without agent judgment. Delivery remains subject to delivery and authority policy. |
| `BLOCK_BUDGET` | Budget policy blocks any agent wake. Script-only detection may still record the blocked state if permitted. |
| `SCRIPT_ERROR` | Script failed or emitted invalid output. Create an observable error record. |

`WAKE_AGENT` is not script-only. It exits script-only mode and may proceed only through budget, Model Router, and authority gates.

`ESCALATE_AUTHORITY` is not permission to act. It means Zaubern-lite and human confirmation are required before any sensitive external effect.

## Example script classes

- File-change gates compare local file fingerprints.
- HTTP-diff gates compare approved metadata such as ETag, Last-Modified, status code, or content digest.
- External-flag gates compare a declared local or external boolean/status flag.

The example scripts in `runtime/hermes/scripts/examples/` emit deterministic JSON packets. They are examples only and are not wired into a scheduler, gateway, connector, or model route.

## Required error behavior

Script errors must be observable. A routine run should record:

- script name;
- error type;
- safe error message;
- timestamp if available;
- `SCRIPT_ERROR` decision;
- `wakeAgent=false`;
- zero token expectation.

Script errors must not silently fall back to agent wake because that would turn an operational failure into unplanned model spend.

## Forbidden behavior

- no direct canonical Memory Center writes;
- no `ProposedMemory` writes;
- no sensitive external action;
- no model routing;
- no LLM/provider call;
- no Telegram/email/browser/WhatsApp/webhook/payment/publish/destructive effect;
- no connector or MCP activation;
- no plugin activation;
- no 89P or later authorization.
