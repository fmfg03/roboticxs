from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ROBOTICXS_LOOP_HANDOFF_STAGE = "148P"
ROBOTICXS_LOOP_TARGET = "open-loops-completion"
ROBOTICXS_LOOP_PROFILE = "roboticxs_non_authority_loop_v1"
DEFAULT_LABEL = "non_authority_candidate"
DEFAULT_ARTIFACT_ROOT = Path("roboticxs_artifacts/loop_handoffs")
DEFAULT_WORKTREE_ROOT = Path("/tmp/roboticxs_loop_worktrees")
OPEN_LOOPS_COMMAND = ("python3", "-m", "app.open_loops_command")
TEST_COMMAND = ("pytest", "-q")
AUTHORITY_DISABLED_MARKERS = (
    "Read-only: true",
    "Calendar writes: disabled",
    "Memory writes: disabled",
    "ProposedMemory writes: disabled",
    "Follow-up intents: disabled",
    "Reminders/scheduler: disabled",
    "LLM/model calls: disabled",
    "Tools/workers: disabled",
    "External writes: disabled",
    "Proactive outbound: disabled",
    "No external action was taken.",
)
PROTECTED_PATH_PATTERNS = (
    ".secrets/**",
    "*.secret.json",
    "*token*.json",
    "app/google_oauth*",
    "app/file_retrieval_adapter.py",
    "app/real_calendar_meeting_brief.py",
    "app/telegram_adapter.py",
    "app/telegram_runtime.py",
)
GENERATED_PATH_PATTERNS = (
    ".pytest_cache/**",
    "**/.pytest_cache/**",
    "__pycache__/**",
    "**/__pycache__/**",
    "*.pyc",
)


@dataclass(frozen=True, slots=True)
class LoopCommandResult:
    command: tuple[str, ...]
    cwd: str
    exit_code: int
    stdout_tail: str
    stderr_tail: str


@dataclass(frozen=True, slots=True)
class RoboticxsLoopHandoffRecord:
    schema: str
    stage: str
    profile: str
    session_id: str
    target: str
    task: str
    label: str
    status: str
    worktree: str
    artifact_dir: str
    changed_files: tuple[str, ...]
    blocked_authority_attempts: tuple[dict[str, str], ...]
    commands_run: tuple[LoopCommandResult, ...]
    tests_passed: bool
    open_loops_passed: bool
    read_only_boundaries_confirmed: bool
    concrete_diff_present: bool
    completion_condition: dict[str, bool]
    authority_effects: bool
    production_deploy: bool
    external_write: bool
    live_retrieval: bool
    memory_mutation: bool
    telegram_live_send: bool
    promotion_path: str
    created_at: str
    evidence_hash: str


def start_roboticxs_loop(
    *,
    task: str,
    target: str = ROBOTICXS_LOOP_TARGET,
    session_id: str | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    worktree_root: Path | None = None,
) -> RoboticxsLoopHandoffRecord:
    repo_root = (repo_root or Path.cwd()).resolve()
    if target != ROBOTICXS_LOOP_TARGET:
        raise ValueError(f"Unsupported roboticxs loop target: {target}")
    if not task.strip():
        raise ValueError("Roboticxs loop task must be non-empty.")
    session_id = session_id or f"rx_loop_{uuid4().hex[:12]}"
    artifact_root = _resolve_artifact_root(repo_root, artifact_root)
    worktree_root = _resolve_worktree_root(worktree_root)
    artifact_dir = artifact_root / _slug(session_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    worktree = _create_worktree(repo_root=repo_root, worktree_root=worktree_root, session_id=session_id)

    commands_run = (
        _run_command(TEST_COMMAND, cwd=worktree),
        _run_command(OPEN_LOOPS_COMMAND, cwd=worktree),
    )
    changed_files = _changed_files(worktree)
    blocked_attempts = tuple(_protected_path_attempts(changed_files))
    tests_passed = commands_run[0].exit_code == 0
    open_loops_passed = commands_run[1].exit_code == 0
    read_only_confirmed = _read_only_boundaries_confirmed(commands_run[1].stdout_tail)
    concrete_diff_present = bool(changed_files)
    completion_condition = {
        "tests_passed": tests_passed,
        "open_loops_passed": open_loops_passed,
        "read_only_boundaries_confirmed": read_only_confirmed,
        "no_blocked_authority_attempts": not blocked_attempts,
        "concrete_diff_present": concrete_diff_present,
    }
    status = "finished" if all(completion_condition.values()) else "incomplete"
    record = _record(
        session_id=session_id,
        target=target,
        task=task,
        status=status,
        worktree=worktree,
        artifact_dir=artifact_dir,
        changed_files=changed_files,
        blocked_attempts=blocked_attempts,
        commands_run=commands_run,
        tests_passed=tests_passed,
        open_loops_passed=open_loops_passed,
        read_only_boundaries_confirmed=read_only_confirmed,
        concrete_diff_present=concrete_diff_present,
        completion_condition=completion_condition,
    )
    _write_artifacts(record)
    return record


def load_loop_evidence(*, session_id: str, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict:
    repo_root = (repo_root or Path.cwd()).resolve()
    artifact_dir = _resolve_artifact_root(repo_root, artifact_root) / _slug(session_id)
    evidence_path = artifact_dir / "evidence.json"
    if not evidence_path.exists():
        raise FileNotFoundError(f"Roboticxs loop evidence not found: {evidence_path}")
    return json.loads(evidence_path.read_text(encoding="utf-8"))


def _resolve_artifact_root(repo_root: Path, artifact_root: Path | None) -> Path:
    override = os.getenv("ROBOTICXS_LOOP_ARTIFACT_ROOT")
    root = Path(override) if override else artifact_root or DEFAULT_ARTIFACT_ROOT
    if root.is_absolute():
        return root
    return repo_root / root


def _resolve_worktree_root(worktree_root: Path | None) -> Path:
    override = os.getenv("ROBOTICXS_LOOP_WORKTREE_ROOT")
    return Path(override) if override else worktree_root or DEFAULT_WORKTREE_ROOT


def _create_worktree(*, repo_root: Path, worktree_root: Path, session_id: str) -> Path:
    worktree_root.mkdir(parents=True, exist_ok=True)
    worktree = worktree_root / f"roboticxs_{_slug(session_id)}"
    if worktree.exists():
        raise FileExistsError(f"Roboticxs loop worktree already exists: {worktree}")
    result = subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git worktree add failed")
    return worktree


def _run_command(command: tuple[str, ...], *, cwd: Path) -> LoopCommandResult:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return LoopCommandResult(
        command=command,
        cwd=str(cwd),
        exit_code=result.returncode,
        stdout_tail=_tail(result.stdout),
        stderr_tail=_tail(result.stderr),
    )


def _changed_files(worktree: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ()
    files: list[str] = []
    for line in result.stdout.splitlines():
        if line.strip():
            path = line[3:].strip()
            if not _is_generated_path(path):
                files.append(path)
    return tuple(sorted(files))


def _is_generated_path(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in GENERATED_PATH_PATTERNS)


def _protected_path_attempts(changed_files: tuple[str, ...]) -> list[dict[str, str]]:
    blocked: list[dict[str, str]] = []
    for path in changed_files:
        for pattern in PROTECTED_PATH_PATTERNS:
            if fnmatch.fnmatch(path, pattern):
                blocked.append(
                    {
                        "decision": "BLOCK",
                        "path": path,
                        "matched_pattern": pattern,
                        "reason": "protected_runtime_or_secret_boundary",
                    }
                )
                break
    return blocked


def _read_only_boundaries_confirmed(open_loops_output: str) -> bool:
    return all(marker in open_loops_output for marker in AUTHORITY_DISABLED_MARKERS)


def _record(
    *,
    session_id: str,
    target: str,
    task: str,
    status: str,
    worktree: Path,
    artifact_dir: Path,
    changed_files: tuple[str, ...],
    blocked_attempts: tuple[dict[str, str], ...],
    commands_run: tuple[LoopCommandResult, ...],
    tests_passed: bool,
    open_loops_passed: bool,
    read_only_boundaries_confirmed: bool,
    concrete_diff_present: bool,
    completion_condition: dict[str, bool],
) -> RoboticxsLoopHandoffRecord:
    base = {
        "schema": "roboticxs_loop_handoff_v1",
        "stage": ROBOTICXS_LOOP_HANDOFF_STAGE,
        "profile": ROBOTICXS_LOOP_PROFILE,
        "session_id": session_id,
        "target": target,
        "task": task,
        "label": DEFAULT_LABEL,
        "status": status,
        "worktree": str(worktree),
        "artifact_dir": str(artifact_dir),
        "changed_files": changed_files,
        "blocked_authority_attempts": blocked_attempts,
        "commands_run": tuple(asdict(command) for command in commands_run),
        "tests_passed": tests_passed,
        "open_loops_passed": open_loops_passed,
        "read_only_boundaries_confirmed": read_only_boundaries_confirmed,
        "concrete_diff_present": concrete_diff_present,
        "completion_condition": completion_condition,
        "authority_effects": False,
        "production_deploy": False,
        "external_write": False,
        "live_retrieval": False,
        "memory_mutation": False,
        "telegram_live_send": False,
        "promotion_path": "human_review_required",
        "created_at": _now(),
    }
    return RoboticxsLoopHandoffRecord(
        commands_run=commands_run,
        evidence_hash=_hash({**base, "commands_run": base["commands_run"]}),
        **{key: value for key, value in base.items() if key != "commands_run"},
    )


def _write_artifacts(record: RoboticxsLoopHandoffRecord) -> None:
    artifact_dir = Path(record.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    evidence = asdict(record)
    (artifact_dir / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (artifact_dir / "handoff.md").write_text(_render_handoff(record), encoding="utf-8")
    (artifact_dir / "risk_diff.md").write_text(_render_risk_diff(record), encoding="utf-8")


def _render_handoff(record: RoboticxsLoopHandoffRecord) -> str:
    commands = "\n".join(
        f"- `{' '.join(command.command)}` exit `{command.exit_code}`" for command in record.commands_run
    )
    return (
        "# Roboticxs Loop Handoff\n\n"
        f"- Stage: `{record.stage}`\n"
        f"- Session: `{record.session_id}`\n"
        f"- Target: `{record.target}`\n"
        f"- Status: `{record.status}`\n"
        f"- Task: {record.task}\n"
        f"- Worktree: `{record.worktree}`\n"
        f"- Label: `{record.label}`\n"
        f"- Promotion path: `{record.promotion_path}`\n\n"
        "## Completion Condition\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in record.completion_condition.items())
        + "\n\n## Commands\n\n"
        + commands
        + "\n\n## Changed Files\n\n"
        + ("\n".join(f"- `{path}`" for path in record.changed_files) if record.changed_files else "- No concrete diff present yet.")
        + "\n"
    )


def _render_risk_diff(record: RoboticxsLoopHandoffRecord) -> str:
    blocked = record.blocked_authority_attempts
    blocked_lines = (
        "\n".join(f"- BLOCK `{item['path']}` via `{item['matched_pattern']}`" for item in blocked)
        if blocked
        else "- No protected-boundary path changes detected."
    )
    return (
        "# Roboticxs Loop Risk Diff\n\n"
        f"- Stage: `{record.stage}`\n"
        f"- Session: `{record.session_id}`\n"
        f"- Status: `{record.status}`\n"
        "- Authority effects: `false`\n"
        "- External writes: `false`\n"
        "- Live retrieval: `false`\n"
        "- Memory mutation: `false`\n"
        "- Telegram live send: `false`\n\n"
        "## Blocked / Risky Boundary Attempts\n\n"
        f"{blocked_lines}\n"
    )


def _tail(value: str, limit: int = 6000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
