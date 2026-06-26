# Calendar Context Binding v1 182P v0.1

`182P - Calendar Context Binding v1` binds existing Google Calendar read-only context into the customer-facing Telegram flows for `/today`, `/daily_brief`, and `/prep`.

182P is read-only Calendar binding only. It reuses the existing Google Calendar read-only connector and adds source trace receipts so the user can see what Calendar source was used, what event refs were considered, and which writes remain disabled.

## Scope

- Add shared Calendar source trace rendering.
- Attach source trace to `/today`.
- Attach source trace to `/daily_brief`.
- Attach source trace to `/prep`.
- Fail closed with `/checkup` guidance when Calendar is unavailable.
- Keep Calendar reads read-only.

## Source trace

Source trace includes:

- Calendar connection status.
- Calendar id.
- read window.
- safe event refs with event id, summary, and start time.
- blocked reason when unavailable.
- writes disabled marker.

Source trace must not include access tokens, refresh tokens, client secrets, Authorization headers, raw environment values, or OAuth payloads.

## Boundaries

182P does not authorize:

- Gmail context binding;
- Gmail draft creation;
- Gmail send/modify/archive/label/delete;
- Calendar create/update/delete;
- OAuth URL generation;
- OAuth token exchange;
- OAuth token refresh;
- connector activation beyond existing read-only owner-requested Calendar reads;
- document parsing;
- local file writes;
- Memory Store writes;
- Memory Center mutation;
- model calls;
- tool calls;
- worker dispatch;
- scheduler/proactive sends;
- external writes;
- deployment, push, merge, or PR creation.

188P and later remain unauthorized.
