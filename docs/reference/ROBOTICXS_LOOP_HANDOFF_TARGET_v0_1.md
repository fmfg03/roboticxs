# Roboticxs Loop Handoff Target v0.1

## Status

`148P - Factory Loop Handoff Harness v0` defines a local non-authority loop target for Roboticxs open-loop completion work.

This target does not authorize live retrieval, external writes, Calendar writes, Telegram live sends,
memory mutation, provider execution, billing, release, or deploy.

## Command

```bash
roboticxs loop start "<task>" --target open-loops-completion
```

Source equivalent:

```bash
python3 -m app.roboticxs_loop_cli loop start "<task>" --target open-loops-completion
```

## Completion Condition

A session is `finished` only when all checks are true:

- `pytest -q` passes.
- `python3 -m app.open_loops_command` exits cleanly.
- The Open Loops output confirms all read-only/no-authority markers.
- No protected boundary path changes are detected.
- The isolated worktree contains a concrete diff.

If any check fails, the session is `incomplete` and still emits handoff artifacts.

## Handoff Artifacts

Each session writes:

```text
roboticxs_artifacts/loop_handoffs/<session_id>/evidence.json
roboticxs_artifacts/loop_handoffs/<session_id>/handoff.md
roboticxs_artifacts/loop_handoffs/<session_id>/risk_diff.md
```

All outputs are `non_authority_candidate` and require human review before merge or promotion.
