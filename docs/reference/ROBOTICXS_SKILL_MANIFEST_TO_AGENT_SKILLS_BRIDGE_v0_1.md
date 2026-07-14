# Roboticxs SkillManifest to Agent Skills Bridge v0.1

Status: 87P implemented pending review.

This bridge defines how Roboticxs may later package skill instructions/resources for Hermes Agent Skills without transferring product authority to Hermes. It is documentation/spec/test work only.

## Contract

Roboticxs SkillManifest remains canonical for package, scope, plan, confirmation, blocked actions, and upgrade path.

Agent Skills packages instructions and resources; it does not enforce authority.

Hermes is runtime capability, not Roboticxs product. A future Agent Skill export may make Roboticxs instructions easier for Hermes to load, but the export cannot decide what is authorized, confirmed, blocked, billable, canonical memory, or safe to execute.

## Mapping

| Roboticxs SkillManifest surface | Agent Skills package surface | 87P authority rule |
| --- | --- | --- |
| `package` | Skill name, directory, and frontmatter identity | Packaging only. The Roboticxs package remains canonical. |
| `description` | Skill summary/description | Helpful instruction text only. It is not an authority claim. |
| `scope_decisions` | Skill instructions and examples | The exported text may describe scope, but Roboticxs Scope Guard remains authoritative. |
| plan/decision policy | Skill instructions | The SkillManifest plan rules remain canonical. Agent Skills cannot replace plan authority. |
| `confirmation_required` | Warnings or steps in skill instructions | Confirmation still comes from Roboticxs authority gates and user confirmation. |
| `blocked_topics` and `blocked_action_classes` | Warnings or prohibited-action notes | Blocked actions remain enforced by Roboticxs authority layers, not by the package format. |
| `upgrade_paths` | Related-skill notes or follow-up guidance | Upgrade path remains canonical in SkillManifest. |
| resources/examples | Agent Skills resources or markdown sections | Resources are support material only. |
| connector/tool notes | Skill instructions | No connector, MCP, plugin, or external tool activation is authorized in 87P. |

## Export rules

- A generated Agent Skill may include Roboticxs instructions, examples, reference links, and non-secret resources.
- A generated Agent Skill must preserve package, scope, plan, confirmation, blocked actions, and upgrade path from the SkillManifest.
- A generated Agent Skill must state that it is not an authority layer.
- A generated Agent Skill must not move secrets into skill files.
- A generated Agent Skill must not activate connectors, MCP servers, plugins, cron jobs, gateways, payments, publishing, or destructive tools.
- A generated Agent Skill must not write to Memory Center, Hermes memory, or any durable store as part of 87P.

## Forbidden interpretations

- Agent Skills do not replace Roboticxs SkillManifest.
- Agent Skills do not enforce authority.
- Agent Skills do not grant external action permission.
- Agent Skills do not bypass Zaubern-lite.
- Agent Skills do not become canonical memory.
- Agent Skills do not authorize 88P+.

## Boundary with existing Roboticxs layers

- Zaubern-lite remains authority for external/business actions.
- Memory Center remains canonical memory.
- Cost Governor remains spend and wake authority.
- Hermes memory remains runtime memory.
- `.env` remains for secrets.
- Config files remain for non-secret runtime configuration.
- `SOUL.md` remains identity/style only.
- `AGENTS.md` and context files remain project/runtime instructions.
