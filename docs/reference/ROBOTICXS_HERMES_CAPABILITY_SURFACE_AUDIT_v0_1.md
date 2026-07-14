# Roboticxs Hermes Capability Surface Audit v0.1

Status: 87P implemented pending review.

This audit classifies Hermes surfaces for future Roboticxs integration. It is a reference contract only. It does not change runtime code or authorize 88P+.

## Surface classifications

| Hermes surface | Verified capability | 87P Roboticxs classification |
| --- | --- | --- |
| Hermes agent runtime | Runs agent sessions with tools and model/provider configuration | Runtime capability only; not product authority. |
| Agent Skills | Packages reusable instructions/resources and can be loaded by Hermes | Packaging candidate only; does not enforce authority. |
| Built-in and optional skills | Hermes ships built-in `skills/` and optional `optional-skills/` | Reference-only; no import, install, or activation in 87P. |
| `skills` config | Controls creation nudge interval and external skill directories | Non-secret runtime configuration only. |
| `skills_hub` toolset | Can search/install/manage skills from online registries | Blocked in 87P. No online registry activation. |
| `cronjob` toolset | Can create/list/update/pause/resume/run/remove scheduled jobs | Reference-only in 87P. No cron execution. |
| Hermes cron scheduler | Schedules jobs through `cron/jobs.py` and `cron/scheduler.py` | Mapping input only; Roboticxs Routine remains product object. |
| `[SILENT]` cron marker | Suppresses delivery when output starts with `[SILENT]` | Delivery suppression hint only; not cost control. |
| Hermes `no_agent=True` cron mode | Allows script-only cron jobs upstream | Deferred to 88P+. Not implemented in 87P. |
| Hermes memory/session search | Runtime memory and past-session recall | Runtime memory only; not canonical Roboticxs Memory Center. |
| Hermes profiles | Isolate runtime state such as config, `.env`, memory, sessions, skills, cron, and logs | State isolation only; not business authorization. |
| Gateway/messaging delivery | Hermes can deliver through configured platforms | No Roboticxs external send/update/publish/payment/destructive action without Zaubern-lite and user confirmation. |
| Browser, terminal, file, web, connector, and plugin tools | Tool capabilities exposed through Hermes toolsets and config | Not activated by 87P. Future use requires separate authorization. |

## Authority boundaries

- Hermes is runtime capability, not Roboticxs product.
- Agent Skills packages instructions/resources; it does not enforce authority.
- Roboticxs SkillManifest remains canonical for package, scope, plan, confirmation, blocked actions, and upgrade path.
- Hermes cron schedules work; Roboticxs Routine is the consumer product object.
- Cron `[SILENT]` is not cost control.
- `wakeAgent=false` and no-agent mode belong to 88P, not 87P implementation.
- Hermes memory remains runtime memory, not canonical Roboticxs Memory Center.
- No external send/update/publish/payment/destructive action may be implied without Zaubern-lite authority and user confirmation.
- Zaubern-lite remains the authority layer.
- Memory Center remains canonical memory.
- Cost Governor remains spend/wake authority.

## Explicit non-implementation list

87P does not implement:

- Hermes cron execution;
- cron job creation;
- runtime gateway changes;
- Telegram delivery changes;
- MCP/plugin activation;
- online skill-hub activation;
- blueprints;
- wake-gate execution;
- `wakeAgent=false`;
- Hermes `no_agent=True`;
- Memory Center bridge implementation;
- payment, publish, browser, email, WhatsApp, webhook, or destructive actions;
- 88P+.
