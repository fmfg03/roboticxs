from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
WAKE_GATE_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_ROUTINE_WAKE_GATE_v0_1.md"
HTTP_GATE_PATH = REPO_ROOT / "runtime/hermes/scripts/examples/http_diff_gate.py"


def test_wake_agent_context_payload_must_be_bounded_and_policy_gated():
    text = WAKE_GATE_PATH.read_text()

    for required in [
        "When `wakeAgent=true`, `bounded_context` must be minimal, source-scoped, and safe to pass to an agent.",
        "The run still requires budget authorization before Model Router",
        "authority checks before any external effect",
        "Budget policy may return `BLOCK_BUDGET` before Model Router.",
        "`wakeAgent=true` may pass bounded context to an agent only after budget policy allows it.",
    ]:
        assert required in text


def test_http_diff_gate_passes_bounded_context_only_when_changed():
    previous = json.dumps(
        {
            "body_sha256": None,
            "etag": "old",
            "last_modified": None,
            "status_code": "200",
            "type": "http_metadata",
        },
        sort_keys=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(HTTP_GATE_PATH),
            "https://example.test/status",
            "--etag",
            "new",
            "--previous-fingerprint",
            previous,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    packet = json.loads(result.stdout)

    assert packet["decision"] == "WAKE_AGENT"
    assert packet["wakeAgent"] is True
    assert packet["model_router_allowed"] is True
    assert packet["bounded_context"] == {
        "url": "https://example.test/status",
        "changed": True,
        "status_code": "200",
    }
