# Roboticxs Blueprint Installation Contract v0.1

Status: 89P implemented pending review.

This document defines the installation contract for Roboticxs Automation Blueprints. It is documentation/spec/test work only. It does not implement an installer, UI, live Hermes cron execution, production scheduler, gateway changes, or actual MCP/plugin activation.

## Installation contract

Installing a blueprint means preparing a draft `Routine` template for user review.

Installing a blueprint does not schedule the routine.

Installing a blueprint does not activate Agent Skills, MCP servers, plugins, connectors, gateways, cron jobs, or external delivery.

Installing a blueprint does not grant source authorization, model budget authorization, delivery authorization, memory-write authorization, or external-action authorization.

## Required installation states

| State | Meaning |
| --- | --- |
| `AVAILABLE_TEMPLATE` | Blueprint package exists as a portable template. |
| `DRAFT_ROUTINE` | User has selected the template, but no schedule or authority has been granted. |
| `PENDING_USER_CONFIGURATION` | Required inputs, source authorization, wake policy, budget policy, delivery target, or confirmations are incomplete. |
| `READY_FOR_REVIEW` | A complete routine draft is ready for explicit user review. |
| `INSTALLED_NOT_SCHEDULED` | User accepted the template as a routine draft, but no schedule has been activated. |

## Required user review

Before a blueprint can become a recurring routine, the user must review:

- name;
- description;
- package;
- inputs;
- schedule policy;
- source authorization;
- wake policy;
- skill binding;
- model/budget policy;
- delivery target;
- authority boundary;
- memory sink policy;
- confirmation behavior.

Recurring blueprints must reference the 88P wake-gate policy where feasible.

## Non-claims

- no silent schedule;
- no live routine execution;
- no production scheduler;
- no external delivery;
- no canonical Memory Center auto-write;
- no UI;
- no 90P or later authorization.
