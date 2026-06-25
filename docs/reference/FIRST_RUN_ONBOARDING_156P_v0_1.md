# First-Run Onboarding 156P v0.1

`156P - First-Run Onboarding v0` turns `/start` into the customer-facing first-run orientation for the Telegram product.

## Scope

- show welcome and owner-gated robot identity;
- show what the robot can do now;
- show what still needs setup;
- show approval boundaries;
- offer a first useful action.

## Authority

156P is reply-copy and command-surface orientation only. It does not add new commands, persistence, onboarding state, profile writes, connector activation, OAuth generation, token exchange, Calendar writes, Gmail reads or writes, Memory Center mutation, ProposedMemory writes, model calls, tool calls, worker dispatch, scheduler, proactive outbound sends, billing, deployment, push, merge, PR creation, or external writes beyond approved Telegram replies.

## Product Copy

The `/start` reply must include:

- `Welcome. Your private robot is online.`
- `What I can do now:`
- `What needs setup:`
- `Approval boundaries:`
- `Choose first useful action:`

It must route the owner toward an action instead of a tutorial.
