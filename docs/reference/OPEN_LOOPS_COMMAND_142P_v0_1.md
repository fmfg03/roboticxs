# Open Loops Command 142P v0.1

## Status

`142P - Open Loops Command v0` is closed committed scope for an owner-requested, read-only Telegram `/loops` surface.

## User Story

As Francisco, I want to ask Roboticxs `/loops` from Telegram, so I can see a compact read-only list of unresolved items that may need my attention without the robot creating tasks, follow-ups, memory, reminders, or external actions.

## Runtime Surface

- `/loops` is owner-gated through the existing Telegram allowlist.
- Authorized `/loops` composes existing local/read-only sources only.
- Unauthorized `/loops` returns the private bot refusal and does not read Calendar or Memory Center sources.
- Telegram `sendMessage` remains the only external write.

## Inputs

- Pending memory proposal visibility from the existing `136P` Telegram Memory Center snapshot.
- Current owner-requestable meeting suggestions from the existing `138P` proactive meeting suggestion scan.
- Calendar unavailable status when the read-only Calendar path fails closed.

## Output

The Open Loops response includes:

- stage and status;
- pending memory proposal loops, explicitly marked as not facts;
- owner-requestable meeting suggestion loops;
- Calendar availability or failure status;
- passive next-step hints for existing commands such as `/memory_pending`, `/suggest_brief`, and `/brief <suggestion_id>`;
- explicit disabled boundaries for Calendar writes, Memory Center writes, ProposedMemory writes, follow-up intents, reminders/scheduler, model calls, tools, workers, external writes, and proactive outbound sends.

## Authority Boundaries

`142P` does not authorize:

- task database or persistence;
- follow-up intent creation;
- reminders, scheduler, cron, callbacks, or inline buttons;
- Memory Center mutation;
- ProposedMemory writes;
- Calendar writes;
- model/tool calls;
- worker dispatch;
- DeerFlow runtime integration;
- new dependencies.

## Failure Behavior

If Calendar is unavailable, `/loops` fails closed for Calendar context and still renders local pending Memory Center visibility. The response must state the Calendar unavailability reason and preserve all no-write boundaries.

If no local loops exist and Calendar is available, `/loops` returns an empty state and states that no action was taken.

## Next Stage Boundary

`143P+` remains unauthorized. `142P` only adds the owner-requested read-only Open Loops command.
