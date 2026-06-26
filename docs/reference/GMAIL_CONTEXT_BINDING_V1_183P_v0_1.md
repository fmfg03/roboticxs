# Gmail Context Binding v1 183P v0.1

`183P - Gmail Context Binding v1` binds existing Gmail read-only metadata context into `/daily_brief` and `/prep`.

183P is read-only Gmail context binding only. It reuses the existing Gmail read-only context scan and adds source trace receipts so the user can see Gmail status, safe thread refs, context signals, and disabled write boundaries.

## Scope

- Add shared Gmail source trace rendering.
- Attach Gmail source trace to `/daily_brief`.
- Attach Gmail source trace to `/prep`.
- Preserve Calendar source trace from 182P.
- Fail closed with `/checkup` guidance when Gmail is unavailable.
- Keep Gmail reads metadata/read-only.

## Source trace

Source trace includes:

- Gmail connection status.
- query.
- message count.
- safe thread refs with thread id, message id, and subject.
- bounded signal refs.
- blocked reason when unavailable.
- writes disabled marker.

Source trace must not include access tokens, refresh tokens, client secrets, Authorization headers, raw environment values, or full email bodies.

## Boundaries

183P does not authorize:

- Gmail draft creation;
- Gmail send/modify/archive/label/delete;
- OAuth URL generation;
- OAuth token exchange;
- OAuth token refresh;
- Calendar create/update/delete;
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

186P and later remain unauthorized.
