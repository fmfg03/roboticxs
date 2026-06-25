# DeerFlow Pattern Review / Sandbox Boundary Spike v0.1

## Status

Stage 140P is a docs/test-only pattern review stage.

It evaluates DeerFlow as a technical reference for Roboticxs skills, sub-agents, sandbox execution, IM channels, and memory assumptions. It does not add DeerFlow to Roboticxs runtime, does not install dependencies, and does not replace Hermes.

## Source Evidence

- DeerFlow repository: https://github.com/bytedance/deer-flow
- Local Roboticxs authority references:
- `docs/reference/ROBOTICXS_SKILL_ACTIVATION_SCOPE_GUARD_v0_1.md`
- `docs/reference/ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1.md`
- `docs/reference/ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1.md`
- `docs/reference/PROACTIVE_MEETING_SUGGESTION_v0_1.md`
- `docs/reference/SUGGESTED_MEETING_BRIEF_REQUEST_139P_v0_1.md`

## Runtime Decision

Hermes remains the Roboticxs runtime.

DeerFlow is not a production dependency in 140P. DeerFlow may be used only as a reference for future design decisions unless a later approved stage explicitly authorizes installation, sandbox testing, dependency review, or runtime integration.

## Classification Legend

Allowed classifications:

- `COPY`: safe to replicate as a local design idea.
- `ADAPT`: useful but must be reshaped around the Roboticxs policy chain.
- `DEFER`: useful later, blocked until a future approved authority stage.
- `FORBID`: incompatible with current MVP safety or product boundary.
- `UNKNOWN`: insufficient verified local/source evidence.

## Pattern Review

| Category | DeerFlow pattern | Roboticxs interpretation | Classification | Boundary |
| --- | --- | --- | --- | --- |
| skills | `SKILL.md`-style skill folders with local instructions and supporting assets | Roboticxs should keep self-contained skill packages, but preserve explicit manifest authority and commercial/product metadata | `ADAPT` | Do not replace Roboticxs skill manifest or scope guard |
| skills | Slash-command skill activation | Useful for operator/dev ergonomics, but product commands must remain owner-gated and policy-routed | `ADAPT` | No raw command activation bypassing command policy |
| subagents | Multi-step sub-agent delegation for research, document review, and long tasks | Useful for future research/document-review labs | `DEFER` | Requires authority design before async delegation or worker dispatch |
| subagents | Concurrent task execution | Potentially useful for bounded local research packets | `DEFER` | No worker dispatch, model calls, or external tools in 140P |
| sandbox | Filesystem and command execution sandbox | Valuable as a design reference, high risk operationally | `DEFER` | Must sit behind Scope Guard, Tool Authority Guard, budget guardrails, and approval packets |
| sandbox | Default privileged command/file capabilities | Too broad for the current Roboticxs MVP | `FORBID` | No bash, file-write, provider execution, or sandbox execution is authorized |
| im_channels | Telegram/IM channel abstraction | Useful pattern for avoiding Telegram hardcoding forever | `ADAPT` | Roboticxs owner gate and command policy remain mandatory |
| im_channels | Allow-all user configuration | Unsafe for Roboticxs personal robot operation | `FORBID` | No channel may bypass owner allowlist |
| memory | Local profile, preference, and knowledge persistence | Conceptually aligned with personal robot continuity | `ADAPT` | Roboticxs memory must remain approved, editable, inspectable, and revocable |
| memory | Automatic persistent memory | Incompatible with current Memory Center authority | `FORBID` | No automatic Memory Center mutation or ProposedMemory write |
| embedded_client | In-process client usage for local experiments | Useful for future isolated lab work | `DEFER` | No dependency install, import, or execution in 140P |
| model_config | Broad model provider compatibility | Useful reference for future router ergonomics | `DEFER` | Roboticxs cost governor and model router remain authoritative |

## Copy / Adapt / Defer / Forbid Summary

`COPY`:
- None in 140P without adaptation. DeerFlow ideas are relevant, but Roboticxs authority rules require translation.

`ADAPT`:
- Self-contained skills with local instructions and assets.
- Slash-command ergonomics only behind Roboticxs command policy.
- IM channel abstraction only behind owner gating.
- Memory concepts only behind approved/editable Memory Center rules.

`DEFER`:
- Sub-agent delegation.
- Concurrent task execution.
- Sandbox filesystem and command execution.
- Embedded Python client experiments.
- Broad model provider/router comparison.

`FORBID`:
- DeerFlow as Roboticxs runtime replacement.
- Production dependency addition in 140P.
- Default privileged bash/file-write behavior.
- Allow-all IM/Telegram user configuration.
- Automatic persistent memory.
- Sandbox execution against user data without authority wrappers.

`UNKNOWN`:
- Any upstream DeerFlow behavior not verified from the repository source should remain unknown until a future review pins the exact commit and evidence.

## Forbidden Scope

- No DeerFlow clone.
- No DeerFlow dependency install.
- No production dependency change.
- No runtime integration.
- No Telegram or IM channel replacement.
- No owner-gate relaxation.
- No sandbox execution.
- No filesystem write authority.
- No connector config.
- No Memory Center mutation.
- No ProposedMemory write.
- No model call.
- No tool call.
- No worker dispatch.
- No async delegation.
- No external network behavior.
- No billing or entitlement behavior.
- No change to Hermes as runtime.

## Future Reopen Requirements

A future DeerFlow-related stage requires:

- explicit maintainer authorization;
- pinned upstream source evidence;
- dependency and supply-chain review;
- sandbox authority design;
- owner-gate and channel-auth design;
- memory approval/editability design;
- budget and model-router integration design;
- scoped tests and read-only validation before any runtime integration.

## Closeout

140P is closed committed when this docs/test-only review, canonical roadmap registry, and tests assert that DeerFlow is a reference only, Hermes remains runtime, no DeerFlow dependency or runtime capability is added, and 143P and later remain unauthorized.
