# Hermes Real Settings Baseline v0.1

## Status

Stage 86P is closed committed.

This is a verified research baseline for Hermes Agent configuration surfaces that Roboticxs may reference later. It is not a runtime integration, dependency install, upstream adoption, gateway change, model-routing change, memory bridge, or product authorization layer.

## Purpose

Roboticxs must not build Hermes integration plans from rumors, community screenshots, obsolete packets, or plausible-looking setting names.

This baseline records only settings, files, commands, and profile behavior backed by official Hermes Agent documentation or source at the inspected upstream commit.

## Inspected Upstream

- Repository: https://github.com/NousResearch/hermes-agent
- Owner: NousResearch
- Inspected commit: `6b76284c7769e0ca80012a5a4b7e22b1cea05b6b`
- Inspection date: 2026-06-14
- Authority type: official upstream source

Community posts, planning chat, and screenshots may be used only as discovery inputs. They are not authority for a Hermes setting, environment variable, command, or profile behavior unless confirmed by official upstream documentation or source.

## Official Source Evidence

The following official upstream files were inspected:

- `README.md`
  - Records user commands including `hermes`, `hermes model`, `hermes tools`, `hermes config set`, `hermes gateway`, `hermes setup`, `hermes update`, and `hermes doctor`.
  - Records shared slash commands including `/new`, `/reset`, `/model`, `/personality`, `/retry`, `/undo`, `/compress`, `/usage`, `/insights`, `/skills`, `/stop`, `/platforms`, `/status`, and `/sethome`.
- `cli-config.yaml.example`
  - Documents non-secret configuration under YAML sections such as `model`, `terminal`, `browser`, `tool_loop_guardrails`, `compression`, `auxiliary`, `memory`, `session_reset`, `streaming`, `skills`, `agent`, and `platform_toolsets`.
  - Documents memory keys under `memory`: `memory_enabled`, `user_profile_enabled`, `memory_char_limit`, `user_char_limit`, `nudge_interval`, and `flush_min_turns`.
  - Documents skill configuration under `skills`: `creation_nudge_interval` and `external_dirs`.
- `.env.example`
  - Documents environment variables for credentials and selected compatibility overrides.
  - States that the default model is configured in `~/.hermes/config.yaml` and that `LLM_MODEL` is no longer read from `.env`.
  - States that terminal backend and terminal cwd are usually configured in `config.yaml`, with selected legacy override variables available only when needed.
- `AGENTS.md`
  - States that user config is `~/.hermes/config.yaml` for settings and `~/.hermes/.env` for API keys only.
  - States that new `HERMES_*` environment variables for non-secret config are rejected and that behavioral settings belong in `config.yaml`.
  - Lists non-exhaustive top-level `config.yaml` sections: `model`, `agent`, `terminal`, `compression`, `display`, `stt`, `tts`, `memory`, `security`, `delegation`, `smart_model_routing`, `checkpoints`, `auxiliary`, `curator`, `skills`, `gateway`, `logging`, `cron`, `profiles`, `plugins`, and `honcho`.
  - States that Hermes profiles are multiple isolated instances, each with its own `HERMES_HOME` directory for config, API keys, memory, sessions, skills, gateway, and related state.
- `hermes_constants.py`
  - Defines `HERMES_HOME` as the environment variable used to resolve the Hermes home directory.
  - Defines `get_config_path()` as `HERMES_HOME/config.yaml`.
  - Defines `get_env_path()` as `HERMES_HOME/.env`.
  - Defines profile-aware helpers such as `get_hermes_home()`, `display_hermes_home()`, and `get_subprocess_home()`.
- `hermes_cli/subcommands/profile.py`
  - Defines `hermes profile` actions including `list`, `use`, `create`, `delete`, `describe`, `show`, `alias`, `rename`, `export`, `import`, `install`, `update`, and `info`.

## Verified Configuration Surfaces

Roboticxs may reference these Hermes surfaces as verified only in the narrow sense below:

- `config.yaml` is the primary non-secret user configuration file under `HERMES_HOME`.
- `.env` is for secrets such as API keys, tokens, and passwords, plus documented compatibility overrides.
- `HERMES_HOME` is the profile/home location mechanism used by Hermes source.
- `SOUL.md` is profile identity/personality content and must not become Roboticxs runtime policy.
- `AGENTS.md` is developer/runtime instruction content and must not become consumer product copy.
- `hermes config set` is the documented command for setting individual config values.
- `hermes model`, `hermes tools`, `hermes gateway`, `hermes setup`, `hermes update`, and `hermes doctor` are documented commands.
- `hermes profile` is a documented profile-management command family.
- Hermes profiles isolate Hermes state by separate `HERMES_HOME` directories. This is state isolation, not business authorization.
- Hermes memory is Hermes runtime memory. It is not Roboticxs canonical memory.
- Hermes command approval and tool configuration are Hermes runtime controls. They are not Roboticxs business-action authority.

## Rejected Fake Settings

The following names are not accepted Roboticxs Hermes configuration keys or environment variables unless a future stage cites official source that proves otherwise:

- `MEMORY_BACKEND`
- `SKILLS_WATCH`
- `CONTEXT_PRELOAD`
- `NOTIFICATION_GATEWAY`
- `MEMORY_RETRIEVAL_DEPTH`
- `OUTPUT_PATH`
- `HERMES_MAKE_ME_SMARTER`

`OUTPUT_PATH` appears in upstream repository maintenance scripts for generated website artifacts, but that occurrence is not a Hermes user/runtime config key and must not be promoted into Roboticxs runtime configuration.

## Roboticxs Baseline Rules

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

## Non-claims

This baseline does not claim Roboticxs has installed Hermes Agent.
This baseline does not claim full Hermes compatibility.
This baseline does not authorize Hermes dependency installation.
This baseline does not authorize model-router changes.
This baseline does not authorize Telegram gateway changes.
This baseline does not authorize connectors, browser automation, shell execution, scheduler behavior, proactive messaging, or external actions.
This baseline does not authorize 87P or any later stage.
