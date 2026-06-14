# Roboticxs Consumer Command Aliases v0.1

Status: 90P implemented pending review.

This document defines the consumer-facing alias vocabulary for the 90P command surface policy. It is a reference contract only and does not implement parsing, routing, UI, gateway behavior, or runtime enforcement.

## Alias requirements

Consumer aliases must:

- use Roboticxs product language;
- hide raw Hermes operator language;
- preserve the 90P policy class;
- map to user intent;
- name the relevant authority boundary;
- name the cost policy where cost or wake decisions are possible;
- produce an audit log when executed by a future approved implementation;
- provide a safe fallback when the action is blocked or unavailable.

## Consumer aliases

| Consumer phrase | Underlying surface | Policy class | Required authority | Required safe fallback |
| --- | --- | --- | --- | --- |
| `help` | `help` | `EXPOSE` | Scope Guard | Show safe Roboticxs commands only. |
| `status` | `status` | `EXPOSE` | Scope Guard | Explain unavailable status fields without exposing operator commands. |
| `usage` | `usage` | `EXPOSE` | Cost Governor | Show spend/wake state available to the user. |
| `approve` | `approve` | `EXPOSE` | Zaubern-lite Action Packet | Refuse sensitive approval without Action Packet. |
| `deny` | `deny` | `EXPOSE` | Zaubern-lite Action Packet | Refuse sensitive denial without Action Packet reference when applicable. |
| `routines list` | `routines list` | `EXPOSE` | Routine authority | List routines without raw cron controls. |
| `skills list` | `skills list` | `EXPOSE` | SkillManifest package authority | List only safe Roboticxs Skill Packages. |
| `memory review` | `memory review` | `EXPOSE` | Memory Center | Show review state without Hermes memory controls. |
| `stop` | `stop` | `EXPOSE` | Scope Guard | Stop/cancel only supported local flow. |
| `routines` | `/cron` | `WRAP` | Routine + Cost Governor + Zaubern-lite where sensitive | Offer Roboticxs Routine flows, not raw cron controls. |
| `habilidades` | `/skills` | `WRAP` | SkillManifest package authority | Show Skill Packages, not raw skill hub controls. |
| `skill packages` | `/skills`, `/bundles` | `WRAP` | SkillManifest package authority | Block install/activation unless future approved scope grants it. |
| `economy` | `/model` | `WRAP` | Model Router + Cost Governor | Select only approved economy tier when future routing permits. |
| `balanced` | `/model` | `WRAP` | Model Router + Cost Governor | Select only approved balanced tier when future routing permits. |
| `premium` | `/model` | `WRAP` | Model Router + Cost Governor | Require cost visibility and approved plan before use. |
| `send approved handoff` | `/handoff` | `WRAP` | Zaubern-lite + approved channel | Refuse direct external platform handoff. |
| `mode` | `/personality` | `WRAP` | Product-approved mode catalog | Refuse freeform profile mutation. |
| `conversation history` | `/sessions` | `WRAP` | Conversation continuity + Memory Center | Show bounded history only. |
| `continue conversation` | `/resume` | `WRAP` | Conversation continuity | Continue only authorized context. |

## Forbidden consumer aliases

No consumer alias may expose:

- `/yolo`;
- raw `/config`;
- raw `/reload`;
- raw `/reload-mcp`;
- raw `/plugins`;
- browser connect controls;
- raw `/toolsets`;
- raw `/debug`;
- raw `/profile`;
- raw `/platforms`;
- raw `/gateway`;
- raw `/codex-runtime`;
- raw `/branch`;
- raw `/rollback`;
- arbitrary tool enable/disable;
- arbitrary MCP reload;
- unrestricted model/provider switching;
- direct external platform handoff;
- any unverified raw Hermes command.

## Non-claims

- no parser changes;
- no runtime command registry changes;
- no Telegram command changes;
- no gateway changes;
- no UI;
- no 92P or later authorization.
