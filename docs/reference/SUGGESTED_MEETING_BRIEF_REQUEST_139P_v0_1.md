# Owner-Requested Suggested Meeting Brief v0.1

## Status

Stage 139P is a bounded implementation stage.

It lets the owner request a deterministic selected meeting brief from a current 138P proactive meeting suggestion by sending `/brief <suggestion_id>`.

## Story

As Francisco, I want to turn a `/suggest_brief` meeting suggestion into an explicit owner-requested brief, so Roboticxs can help me prepare for the selected meeting only after I ask for that brief myself.

## Inputs

- Existing 138P proactive meeting suggestion records.
- Existing 137P Calendar context scan records.
- Existing 133P Google Calendar read-only connector through the 137P scan path.
- Owner-gated Telegram command handling for approved replies.

## Allowed Scope

- Add deterministic selected suggested meeting brief records.
- Revalidate the requested suggestion id against the current 138P suggestion scan.
- Render a selected meeting brief only after an owner sends `/brief <suggestion_id>`.
- Keep bare `/brief` behavior unchanged.
- Preserve deterministic local records and bounded output.
- Keep Telegram `sendMessage` replies as the only external write, and only after an owner command.

## Forbidden Scope

- No automatic `/brief` execution from `/suggest_brief`.
- No proactive outbound Telegram push.
- No callback binding.
- No follow-up intent creation.
- No async delegation.
- No worker dispatch.
- No Memory Center mutation.
- No ProposedMemory write.
- No Calendar create, update, or delete.
- No model call.
- No tool call.
- No external writes beyond approved Telegram replies.
- No new production dependency.
- No persisted suggestion queue.

## Failure Paths

- A missing suggestion id fails closed and renders no selected meeting brief.
- A stale or unknown suggestion id fails closed and renders no selected meeting brief.
- An unavailable Calendar context scan fails closed and renders no selected meeting brief.
- A non-owner Telegram user receives the private bot refusal and does not trigger Calendar reads.

## Closeout

139P is closed committed when the module, Telegram reply path, roadmap registry, and tests all assert the owner-requested boundary, preserve 138P as action-only, and record the new terminal condition that 140P later added a DeerFlow docs/test-only pattern review only. 141P and later remain unauthorized.
