from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_packet(path: Path, previous_sha256: str | None) -> dict:
    try:
        current_sha256 = fingerprint_file(path)
    except OSError as exc:
        return {
            "decision": "SCRIPT_ERROR",
            "wakeAgent": False,
            "token_expectation": 0,
            "model_router_allowed": False,
            "observable_error": {
                "script": "file_change_gate.py",
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            },
        }

    changed = previous_sha256 is not None and current_sha256 != previous_sha256
    return {
        "decision": "WAKE_AGENT" if changed else "SKIP_NO_CHANGE",
        "wakeAgent": changed,
        "token_expectation": "bounded_by_budget_policy" if changed else 0,
        "model_router_allowed": changed,
        "source_fingerprints": [
            {
                "type": "file_sha256",
                "path": str(path),
                "sha256": current_sha256,
            }
        ],
        "bounded_context": {"path": str(path), "changed": True} if changed else None,
        "observable_error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Example file-change wake gate.")
    parser.add_argument("path")
    parser.add_argument("--previous-sha256")
    args = parser.parse_args()

    print(json.dumps(build_packet(Path(args.path), args.previous_sha256), sort_keys=True))


if __name__ == "__main__":
    main()
