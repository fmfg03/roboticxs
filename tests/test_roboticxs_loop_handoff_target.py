from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.roboticxs_loop_handoff import load_loop_evidence, start_roboticxs_loop


def init_git_repo(path: Path, *, smoke_body: str = "assert True\n") -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts='-q'\n", encoding="utf-8")
    app_dir = path / "app"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("", encoding="utf-8")
    (app_dir / "open_loops_command.py").write_text(
        "def main():\n"
        "    print('Open Loops')\n"
        "    print('Read-only: true')\n"
        "    print('Calendar writes: disabled')\n"
        "    print('Memory writes: disabled')\n"
        "    print('ProposedMemory writes: disabled')\n"
        "    print('Follow-up intents: disabled')\n"
        "    print('Reminders/scheduler: disabled')\n"
        "    print('LLM/model calls: disabled')\n"
        "    print('Tools/workers: disabled')\n"
        "    print('External writes: disabled')\n"
        "    print('Proactive outbound: disabled')\n"
        "    print('No external action was taken.')\n"
        "if __name__ == '__main__': main()\n",
        encoding="utf-8",
    )
    tests_dir = path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_smoke.py").write_text(
        f"from pathlib import Path\n\n\ndef test_smoke():\n    {smoke_body}",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True)


def remove_worktree(repo: Path, worktree: str) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", "--force", worktree], cwd=repo, check=False)


def test_loop_start_creates_non_authority_handoff_for_incomplete_empty_diff(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)

    record = start_roboticxs_loop(
        task="draft open loops completion",
        session_id="loop_test",
        repo_root=repo,
        artifact_root=tmp_path / "artifacts",
        worktree_root=tmp_path / "worktrees",
    )
    try:
        assert record.profile == "roboticxs_non_authority_loop_v1"
        assert record.stage == "148P"
        assert record.label == "non_authority_candidate"
        assert record.status == "incomplete"
        assert record.tests_passed is True
        assert record.open_loops_passed is True
        assert record.read_only_boundaries_confirmed is True
        assert record.concrete_diff_present is False
        assert record.authority_effects is False
        assert record.external_write is False
        assert Path(record.artifact_dir, "evidence.json").exists()
        assert Path(record.artifact_dir, "handoff.md").exists()
        assert Path(record.artifact_dir, "risk_diff.md").exists()

        loaded = load_loop_evidence(session_id="loop_test", repo_root=repo, artifact_root=tmp_path / "artifacts")
        assert loaded["session_id"] == "loop_test"
        assert loaded["promotion_path"] == "human_review_required"
    finally:
        remove_worktree(repo, record.worktree)


def test_loop_evidence_serializes_commands_and_hash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)

    record = start_roboticxs_loop(
        task="verify evidence shape",
        session_id="loop_evidence",
        repo_root=repo,
        artifact_root=tmp_path / "artifacts",
        worktree_root=tmp_path / "worktrees",
    )
    try:
        evidence_path = Path(record.artifact_dir) / "evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert evidence["schema"] == "roboticxs_loop_handoff_v1"
        assert evidence["stage"] == "148P"
        assert evidence["evidence_hash"].startswith("sha256:")
        assert [command["command"] for command in evidence["commands_run"]] == [
            ["pytest", "-q"],
            ["python3", "-m", "app.open_loops_command"],
        ]
    finally:
        remove_worktree(repo, record.worktree)


def test_loop_blocks_protected_boundary_path_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, smoke_body="Path('app/telegram_runtime.py').write_text('mutation', encoding='utf-8')\n")

    record = start_roboticxs_loop(
        task="verify protected boundary block",
        session_id="loop_block",
        repo_root=repo,
        artifact_root=tmp_path / "artifacts",
        worktree_root=tmp_path / "worktrees",
    )
    try:
        assert record.status == "incomplete"
        assert record.tests_passed is True
        assert record.open_loops_passed is True
        assert record.blocked_authority_attempts == (
            {
                "decision": "BLOCK",
                "path": "app/telegram_runtime.py",
                "matched_pattern": "app/telegram_runtime.py",
                "reason": "protected_runtime_or_secret_boundary",
            },
        )
        assert record.concrete_diff_present is True
    finally:
        remove_worktree(repo, record.worktree)
