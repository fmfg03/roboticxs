from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from app.roboticxs_loop_handoff import ROBOTICXS_LOOP_TARGET, load_loop_evidence, start_roboticxs_loop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="roboticxs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    loop_parser = subparsers.add_parser("loop", help="Roboticxs non-authority loop harness")
    loop_subparsers = loop_parser.add_subparsers(dest="loop_command", required=True)

    start_parser = loop_subparsers.add_parser("start", help="Start a roboticxs loop/handoff session")
    start_parser.add_argument("task")
    start_parser.add_argument("--target", default=ROBOTICXS_LOOP_TARGET)
    start_parser.add_argument("--session-id")
    start_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")

    evidence_parser = loop_subparsers.add_parser("evidence", help="Read a loop evidence bundle")
    evidence_parser.add_argument("session_id")
    evidence_parser.add_argument("--format", choices=("json", "markdown"), default="json")

    args = parser.parse_args(argv)
    try:
        if args.command == "loop" and args.loop_command == "start":
            record = start_roboticxs_loop(task=args.task, target=args.target, session_id=args.session_id)
            payload = asdict(record)
            if args.format == "json":
                print(json.dumps(payload, indent=2))
            else:
                print(_render_start(record.session_id, record.status, record.worktree, record.artifact_dir))
            return 0
        if args.command == "loop" and args.loop_command == "evidence":
            evidence = load_loop_evidence(session_id=args.session_id)
            if args.format == "json":
                print(json.dumps(evidence, indent=2))
            else:
                print(_render_evidence(evidence))
            return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print("Unsupported roboticxs command", file=sys.stderr)
    return 1


def _render_start(session_id: str, status: str, worktree: str, artifact_dir: str) -> str:
    return "\n".join(
        [
            "Roboticxs Loop",
            "",
            f"Session: {session_id}",
            f"Status: {status}",
            f"Worktree: {worktree}",
            f"Artifacts: {artifact_dir}",
            "Label: non_authority_candidate",
            "Promotion: human_review_required",
        ]
    )


def _render_evidence(evidence: dict) -> str:
    return "\n".join(
        [
            "Roboticxs Loop Evidence",
            "",
            f"Session: {evidence['session_id']}",
            f"Target: {evidence['target']}",
            f"Status: {evidence['status']}",
            f"Label: {evidence['label']}",
            f"Evidence: {evidence['evidence_hash']}",
            f"Promotion: {evidence['promotion_path']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
