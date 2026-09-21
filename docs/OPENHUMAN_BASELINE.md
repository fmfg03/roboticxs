# OpenHuman Baseline

> **Status:** Day 1 investigation in progress; no Roboticxs product code or
> upstream source has been modified.
>
> **Cutoff:** 2026-09-21
>
> **Upstream:** `https://github.com/tinyhumansai/openhuman`
>
> **Pinned revision:** `61e80bea0dbe92cb45868737a5db56a5a840a0d3`

## Reproducible checkout

The checkout is at `upstream/openhuman`, cloned shallowly with recursive
submodules.  The toolchain required by the upstream was installed locally:

- Rust/Cargo `1.96.1`.
- Node `22.22.2` and pnpm `10.10.0`, matching the pinned package-manager
  declaration.
- `pnpm install --frozen-lockfile` completed before the Rust baseline.

The relevant upstream commands are run from `upstream/openhuman` and long Rust
commands use the upstream `scripts/ci-cancel-aware.sh` wrapper.

| Check | Command | Result |
| --- | --- | --- |
| Dependency installation | `pnpm install --frozen-lockfile` | PASS |
| Workspace type/build check | `cargo check --manifest-path Cargo.toml` | PASS |
| Standalone CLI build | `cargo build --manifest-path Cargo.toml -p openhuman-cli --bin openhuman-core` | PASS |
| CLI launch smoke | `./target/debug/openhuman-core --help` | PASS; the CLI exposed its `run`, `flows`, `memory`, `channels`, `approval`, `cost`, and related namespaces |
| Telegram approval surface | `cargo test -p openhuman --lib approval_request_sends_telegram_message_with_recorded_context` | PASS (1 passed) |
| Workflow pauses downstream work | `cargo test -p openhuman --lib flows_run_reports_pending_approval_and_blocks_downstream` | PASS (1 passed) |
| Mismatched resume approval refusal | `cargo test -p openhuman --lib flows_resume_with_mismatched_approvals_is_rejected` | PASS (1 passed) |

This is a baseline, not a production installation: no login, provider key,
OAuth connector, Telegram token, or external service has been configured.

## Confirmed architecture map

| Requested concern | Confirmed OpenHuman owner | Evidence path |
| --- | --- | --- |
| Agent runtime | tinyagents loop, invoked by OpenHuman's agent harness | `crates/openhuman-core/src/agent/tinyagents/`, `crates/openhuman-core/src/agent/harness/` |
| Embed seam | one `openhuman_embed::Runtime`, then independently configured `Agent`s | `crates/openhuman-embed/src/runtime/`, `crates/openhuman-embed/src/agent/` |
| Memory | OpenHuman host layer over vendored tinymemory | `crates/openhuman-core/src/memory/`, `vendor/tinymemory/` |
| Connectors | OpenHuman integration layer and vendored tinyconnectors bus | `crates/openhuman-core/src/integrations/`, `vendor/tinyconnectors/` |
| Telegram | OpenHuman channel runtime; vendor transport is tinychannels | `crates/openhuman-core/src/channels/providers/telegram/`, `vendor/tinychannels/` |
| Workflows | OpenHuman flows domain over tinyflows; durable runs and resume paths | `crates/openhuman-core/src/flows/`, `vendor/tinyflows/` |
| Tool execution | canonical tinytools contracts are adapted into tinyagents | `crates/openhuman-core/src/agent/tinyagents/tools.rs` |
| Approval gate | OpenHuman tool middleware plus `security::approval::ApprovalGate` | `crates/openhuman-core/src/agent/tinyagents/middleware/approval.rs`, `crates/openhuman-core/src/security/approval/` |
| Model routing | OpenHuman inference/routing domains | `crates/openhuman-core/src/inference/`, `crates/openhuman-core/src/routing/` |
| Cost accounting | agent cost and progress-tracing projections | `crates/openhuman-core/src/agent/cost.rs`, `crates/openhuman-core/src/agent/progress_tracing/` |

## Tool execution path: confirmed

For a normal agent turn, the mechanically confirmed path is:

```text
tinyagents selects tool + arguments
  -> OpenHuman ToolPolicyMiddleware (session/tool-scope decision)
  -> OpenHuman ApprovalSecurityMiddleware
  -> CanonicalSharedToolAdapter
  -> canonical tinytools Tool::execute_with_context(...)
  -> tool-specific implementation
```

The approval middleware classifies per invocation through
`Tool::external_effect_with_args(arguments)`, rather than relying on a
tool-wide label.  It runs before `next.run(...)`, so an adapter inserted at
this seam can decide before the native tool implementation is called.

## Baseline risks that affect the sprint

1. **Fail-open when OpenHuman's global approval gate is absent.** The current
   approval middleware logs that the external-effect tool will run without
   interactive approval when `ApprovalGate::try_global()` returns `None`.
   This is incompatible with Roboticxs' Day 3/6 fail-closed invariant and is
   the first concrete delta to address.
2. **Native approval is not Zaubern authority.** Its outcome is human approval
   and OpenHuman audit state, not a Zaubern decision or effect receipt.
3. **Telegram approval surface is specifically implemented.** Upstream notes
   other channel surfaces are not equivalent; the sprint should prove Telegram
   only and not generalize that proof.
4. **An embedded runtime is a real public seam, but not proof that all desktop
   services should be booted in a Roboticxs process.** The embed builder calls
   out that cron, heartbeat, and the memory queue can corrupt shared state if
   a second core is started carelessly.

No product modification is authorized by this document.  The executable
baseline gate is now satisfied; focused upstream approval/workflow tests are
recorded above. Each focused test emitted five pre-existing upstream unused
import warnings; none failed and no upstream source was changed.

## Day 2 status: BLOCKED_UPSTREAM

`repro/openhuman-embed-policy` independently reproduced a public embedding
failure at the pinned SHA. The pure embed path with both `Access::readonly()`
and `Access::full()`, and the public `openhuman_tinyhumans::RuntimeBuilder`
path, each reject `Agent.turn("say pong").send()` before the local provider
receives a request. Each case has zero tools and zero provider calls.

Issue: https://github.com/tinyhumansai/openhuman/issues/6404
