# Roboticxs Hermes Config Contract v0.1

## Status

Stage 86P is closed committed.

This contract translates the verified Hermes settings baseline into Roboticxs planning rules. It is a contract for future implementation review, not an implementation of Hermes configuration loading.

## Source Baseline

Primary research reference: `docs/research/HERMES_REAL_SETTINGS_BASELINE_v0_1.md`.

Upstream source inspected: `NousResearch/hermes-agent` at commit `6b76284c7769e0ca80012a5a4b7e22b1cea05b6b`.

Every Hermes key, environment variable, command, and profile behavior referenced by a Roboticxs implementation must cite official Hermes docs or source. Community posts are discovery inputs only.

## Accepted Hermes Surface Classes

Future Roboticxs work may reference a Hermes surface only when it fits one of these classes and has source evidence:

- Config file setting from `config.yaml` or `cli-config.yaml.example`.
- Secret or documented compatibility variable from `.env.example`, source config metadata, or code.
- Profile/home behavior from `HERMES_HOME`, `hermes profile`, or profile-aware source helpers.
- Command behavior from official README, CLI parser source, or docs.
- SOUL/profile identity behavior from official source or profile files.

## Roboticxs Ownership Rules

- `SOUL.md` remains identity/style only.
- `AGENTS.md` and context files remain project/runtime instructions.
- `.env` is for secrets.
- Config files are for non-secret runtime configuration.
- Hermes profiles are state isolation, not business authorization.
- Hermes memory is runtime memory, not Roboticxs canonical memory.
- Hermes command approval is not Roboticxs business-action authority.
- Zaubern-lite remains the authority layer.
- Memory Center remains canonical memory.
- Cost Governor remains spend and wake authority.

## Rejected Settings

The following setting names are rejected for Roboticxs Hermes configuration:

- `MEMORY_BACKEND`
- `SKILLS_WATCH`
- `CONTEXT_PRELOAD`
- `NOTIFICATION_GATEWAY`
- `MEMORY_RETRIEVAL_DEPTH`
- `OUTPUT_PATH`
- `HERMES_MAKE_ME_SMARTER`

Rejection means:

- Do not add them to Roboticxs `.env`, config docs, runtime config models, tests, or product specs as accepted settings.
- Do not treat them as aliases for verified Hermes settings.
- Do not infer support from community examples, screenshots, or generated packets.
- Reopen only through a future approved stage that cites official Hermes docs or source.

## Future Implementation Gate

Before a future stage adds any Hermes-backed runtime setting, it must:

1. Cite the official Hermes source path and inspected commit or docs URL.
2. Classify the setting as secret, non-secret config, profile state, command behavior, or product-owned Roboticxs policy.
3. Preserve the Roboticxs authority boundaries for Zaubern-lite, Memory Center, and Cost Governor.
4. Add negative tests for plausible fake settings introduced by the stage.
5. Update the canonical roadmap only within the approved stage scope.

## Out of Scope

86P does not implement Hermes install automation, Telegram gateway changes, model routing changes, tool interception, automation blueprints, a Memory Center bridge, payment or subscription behavior, UI, or 87P.
