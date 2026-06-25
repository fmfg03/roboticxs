# Today Command 141P v0.1

## Status

`141P - Today Command v0` is closed committed scope for an owner-requested, read-only Telegram `/today` surface.

## User Story

As Francisco, I want to ask Roboticxs "what matters today?" from Telegram, so I can start the day with a compact, owner-gated view of today's meetings, suggested briefs, memory context, and open admin items without the robot taking action automatically.

## Runtime Surface

- `/today` is owner-gated through the existing Telegram allowlist.
- Authorized `/today` composes existing local/read-only sources only.
- Unauthorized `/today` returns the private bot refusal and does not read Calendar or Memory Center sources.
- Telegram `sendMessage` remains the only external write.

## Inputs

- `138P` proactive meeting suggestion scan from the existing `137P` Calendar context scan path.
- `136P` Telegram Memory Center snapshot from the existing local source bundle.
- Static passive next-step hints derived from those local records.

## Output

The Today response includes:

- stage and status;
- Calendar availability and upcoming meeting-prep context when available;
- owner-requestable `/brief <suggestion_id>` hints from current `138P` suggestions;
- approved and pending Memory Center counts;
- passive next steps;
- explicit disabled boundaries for Calendar writes, memory writes, ProposedMemory writes, model calls, tools, workers, external writes, and proactive outbound sends.

## Authority Boundaries

`141P` does not authorize:

- proactive outbound daily pushes;
- scheduler, cron, reminders, callbacks, or inline buttons;
- follow-up intent creation;
- Memory Center mutation;
- ProposedMemory writes;
- Calendar writes;
- model/tool calls;
- worker dispatch;
- DeerFlow runtime integration;
- new dependencies.

## Failure Behavior

If Calendar is unavailable, `/today` fails closed for Calendar context and still renders local Memory Center visibility. The response must state the Calendar unavailability reason and preserve all no-write boundaries.

## Next Stage Boundary

`143P+` remains unauthorized. `141P` only adds the owner-requested read-only Today command.
