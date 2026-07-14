# Runtime Doctor / Helper Manager 149P v0.1

`149P - Runtime Doctor / Helper Manager v0` adds a local read-only doctor surface for runtime readiness diagnostics.

The Doctor checks local runtime configuration, environment variable presence, `.secrets` path presence, OAuth JSON shape, Calendar readiness, Gmail readiness, and explicit authority boundaries. It reports only configured/missing/invalid states and machine-readable reasons.

The Doctor does not print secrets, token prefixes, token suffixes, token lengths, credential-derived values, file contents, or secret-bearing URLs.

## Supported Surface

- `python3 -m app.runtime_doctor`
- `python3 -m app.runtime_doctor --json`
- `python3 -m app.runtime_doctor --text`

The surface is local only. It is not a Telegram command in 149P.

## Readiness Boundary

The Doctor may inspect:

- runtime identity/config presence
- Google OAuth client secrets file existence and installed-app JSON shape
- Google Workspace token file existence, stage, access-token presence, refresh-token presence, scopes, and expiry timestamp shape
- Calendar readonly scope readiness
- Gmail metadata and readonly scope readiness
- direct Google token environment presence as `configured_redacted`

The Doctor must not activate connectors, generate OAuth URLs, start callback servers, exchange OAuth codes, refresh tokens, call Google Calendar, call Gmail, call Telegram, call models, execute tools, dispatch workers, mutate Memory Center, persist health history, schedule background runs, bill, deploy, push, merge, or create PRs.

## Secret Handling

Diagnostics may report only whether secret-like values are configured. They must not render raw values, prefixes, suffixes, lengths, file contents, or token-derived values.

## Terminal Condition

`152P+` remains unauthorized. `149P` only adds local read-only readiness diagnostics. `150P` later added customer-facing Telegram product shell copy only. `151P` later improved the customer-facing Meeting Prep Pack product flow only.
