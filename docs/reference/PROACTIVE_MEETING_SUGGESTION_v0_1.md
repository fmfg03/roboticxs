# Proactive Meeting Suggestion v0.1

## Status

Stage 138P is a bounded implementation stage.

It adds deterministic local proactive meeting suggestion records and an owner-gated Telegram `/suggest_brief` reply surface.

## Story

As Francisco, I want Roboticxs to notice when an upcoming Calendar meeting likely deserves a brief and suggest the next action, so I can choose whether to ask for a brief without the robot acting automatically.

## Inputs

- Existing 137P Calendar context scan records.
- Existing 133P Google Calendar read-only connector through the 137P scan path.
- Owner-gated Telegram command handling for approved replies.

## Allowed Scope

- Detect meeting-prep context candidates from 137P scan output.
- Render action-only suggestions.
- Add an owner-gated `/suggest_brief` Telegram reply.
- Preserve deterministic local records and bounded output.
- Keep Telegram `sendMessage` replies as the only external write, and only after an owner command.

## Forbidden Scope

- No automatic `/brief` execution.
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

## Closeout

138P is closed committed when the module, Telegram reply path, roadmap registry, and tests all assert the action-only boundary. 139P later added owner-requested suggested meeting brief rendering only, and 140P later added a DeerFlow docs/test-only pattern review only. 141P later added an owner-requested read-only Today command only. 142P and later remain unauthorized.
