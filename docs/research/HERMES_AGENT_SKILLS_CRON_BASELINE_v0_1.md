# Hermes Agent Skills Cron Baseline v0.1

Status: 87P implemented pending review.

This research note records the source-backed Hermes capability baseline for Roboticxs 87P. It is a documentation and contract artifact only. It does not install Hermes, run Hermes cron, modify gateways, create blueprints, activate MCP/plugins, or implement 88P+ behavior.

## Official source baseline

Upstream source inspected:

- Repository: `NousResearch/hermes-agent`
- Local inspection path: `/tmp/hermes-agent-86p`
- Commit: `6b76284c7769e0ca80012a5a4b7e22b1cea05b6b`
- Inspection date: 2026-06-13

Community posts, examples, screenshots, and third-party descriptions are discovery inputs only. They are not authority for 87P.

## Verified Hermes capability facts

- Hermes is a runtime capability surface, not the Roboticxs product authority layer.
- Hermes documents scheduled automations through a built-in cron scheduler and platform delivery.
- Hermes documents an Agent Skills compatible skill system and includes built-in `skills/` plus optional `optional-skills/`.
- Hermes skill slash commands are loaded from `~/.hermes/skills/` by `agent/skill_commands.py` and injected as user messages, not as system prompts.
- Hermes skill frontmatter supports standard fields plus `metadata.hermes.*`, including related skills and config stored under `skills.config.<key>`.
- Hermes config includes a top-level `skills` section for skill creation nudges and external skill directories.
- Hermes toolsets include `skills`, `skills_hub`, and `cronjob`.
- Hermes cron uses `cron/jobs.py` as the job store and `cron/scheduler.py` as the tick loop.
- Hermes agents can schedule jobs through the `cronjob` tool; users can manage jobs through `hermes cron <verb>` or `/cron`.
- Hermes cron supports durations, every-phrases, five-field cron expressions, and ISO one-shot timestamps.
- Hermes cron job fields include prompt, schedule, skills, model/provider override, script, `context_from`, workdir, and delivery targets.
- Hermes cron has a `no_agent=True` script-only mode, but that mode is out of scope for 87P and belongs to later wake/no-agent design.
- Hermes cron can suppress delivery when output starts with `[SILENT]`; output is still saved locally for audit.
- Hermes cron disables protected interactive toolsets in cron context, including `cronjob`, `messaging`, and `clarify`.
- Hermes cron sessions skip memory by default in the upstream scheduler.
- Hermes profiles isolate state such as config, `.env`, memory, sessions, skills, cron, and logs. This remains runtime state isolation, not business authorization.

## Roboticxs interpretation

Hermes capabilities are usable ingredients only after a later authorized implementation stage. Roboticxs product authority remains separate:

- Roboticxs SkillManifest remains canonical for package, scope, plan, confirmation, blocked actions, and upgrade path.
- Agent Skills packages instructions and resources; it does not enforce authority.
- Hermes cron schedules work; Roboticxs Routine is the consumer product object.
- Cron `[SILENT]` is not cost control.
- `wakeAgent=false` and no-agent mode belong to 88P, not 87P implementation.
- Hermes memory remains runtime memory, not canonical Roboticxs Memory Center.
- No external send, update, publish, payment, or destructive action may be implied without Zaubern-lite authority and user confirmation.
- Zaubern-lite remains the authority layer.
- Memory Center remains canonical memory.
- Cost Governor remains spend and wake authority.

## Non-claims

87P does not claim:

- Hermes cron has been executed by Roboticxs.
- Agent Skills have been exported, installed, or loaded by Roboticxs.
- MCP, plugins, external registries, or online skill hubs have been activated.
- Hermes gateway delivery has been changed.
- Telegram, email, browser, WhatsApp, payment, publish, or destructive actions are authorized.
- `wakeAgent=false`, no-agent execution, wake gates, or background spend control are implemented.
- 88P or any later stage is authorized.
