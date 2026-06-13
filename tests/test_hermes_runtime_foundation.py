from __future__ import annotations

import dataclasses
from pathlib import Path
import subprocess

from app.hermes_runtime import (
    HERMES_PROJECT_NAME,
    HERMES_SOURCE_STATUS,
    HERMES_UPSTREAM_OWNER,
    HERMES_UPSTREAM_REPOSITORY,
    ROBOTICXS_APPROVAL_STATUS,
    HermesRuntimeRequest,
    HermesRuntimeResponse,
    HermesRuntimeStatus,
    dispatch_hermes_runtime_request,
    get_hermes_runtime_status,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DOC_PATH = REPO_ROOT / "docs/reference/HERMES_RUNTIME_FOUNDATION_BOOTSTRAP_v0_1.md"
UPSTREAM_DOC_PATH = REPO_ROOT / "docs/reference/HERMES_UPSTREAM_TRACKING_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
RUNTIME_PATH = REPO_ROOT / "app/hermes_runtime.py"

REQUIRED_RUNTIME_SECTIONS = [
    "Status",
    "Decision",
    "Why Hermes comes first",
    "Upstream source",
    "Runtime foundation scope",
    "Local compatibility boundary",
    "Minimal runtime interface",
    "Dispatch behavior",
    "Health/status behavior",
    "What is intentionally not implemented",
    "Future Telegram dependency",
    "Future caregiver dependency",
    "Authority boundaries",
    "Non-claims",
]

REQUIRED_UPSTREAM_SECTIONS = [
    "Status",
    "Upstream repository",
    "Upstream owner",
    "Source status",
    "Roboticxs approval status",
    "Inspected version",
    "Adopted concepts",
    "Not adopted in 78P",
    "Drift risks",
    "Update cadence",
    "Update procedure",
    "Explicit non-auto-update rule",
    "Future adoption gate",
    "Non-claims",
]

REQUIRED_DECISION_LINES = [
    "78P establishes the Hermes runtime foundation for Roboticxs.",
    "It does not implement Telegram.",
    "It does not implement caregiver routines.",
    "It does not implement document intake.",
    "It does not implement connectors.",
    "It does not implement retrieval.",
    "It does not create memory automatically.",
    "It does not import Hermes wholesale.",
    "It does not execute Hermes upstream install scripts.",
    "It does not auto-update from Hermes upstream.",
    "It creates a local compatibility boundary for future runtime stages.",
]

DEPENDENCY_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
]


def changed_files_under(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_runtime_foundation_module_exists_and_uses_frozen_dataclasses():
    assert RUNTIME_PATH.is_file()

    for runtime_type in [HermesRuntimeStatus, HermesRuntimeRequest, HermesRuntimeResponse]:
        assert dataclasses.is_dataclass(runtime_type)
        assert runtime_type.__dataclass_params__.frozen is True


def test_runtime_status_returns_available_hermes_compatible_foundation():
    status = get_hermes_runtime_status()

    assert isinstance(status, HermesRuntimeStatus)
    assert "Hermes-compatible" in status.runtime_name
    assert status.status == "available"
    assert status.upstream_repository == HERMES_UPSTREAM_REPOSITORY
    assert status.compatibility_status == ROBOTICXS_APPROVAL_STATUS
    assert status.orchestrator_available is False
    assert status.metadata["upstream_owner"] == HERMES_UPSTREAM_OWNER
    assert status.metadata["project_name"] == HERMES_PROJECT_NAME
    assert status.metadata["source_status"] == HERMES_SOURCE_STATUS


def test_dispatch_accepts_minimal_request_and_returns_structured_response_without_telegram():
    request = HermesRuntimeRequest(
        user_id="local-user",
        channel="local",
        text="hello runtime",
        metadata={"trace": "test"},
    )

    response = dispatch_hermes_runtime_request(request)

    assert isinstance(response, HermesRuntimeResponse)
    assert response.status == "ok"
    assert response.task_id is None
    assert response.safety_decision is None
    assert "Telegram/channel integration is not implemented yet." in response.text
    assert response.metadata["telegram_required"] == "false"
    assert response.metadata["network_required"] == "false"


def test_dispatch_rejects_empty_text_without_side_effects():
    response = dispatch_hermes_runtime_request(
        HermesRuntimeRequest(user_id="local-user", channel="local", text="   ", metadata={})
    )

    assert response.status == "rejected"
    assert response.task_id is None
    assert response.safety_decision is None
    assert response.metadata["side_effects"] == "none"


def test_dispatch_boundary_disables_memory_retrieval_connector_and_shell_paths():
    response = dispatch_hermes_runtime_request(
        HermesRuntimeRequest(user_id="u1", channel="local", text="status", metadata={})
    )

    assert response.metadata["memory_write"] == "false"
    assert response.metadata["proposed_memory_write"] == "false"
    assert response.metadata["retrieval"] == "false"
    assert response.metadata["connector"] == "false"
    assert response.metadata["shell_execution"] == "false"


def test_runtime_module_does_not_import_network_connector_or_subprocess_paths():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "process_telegram_message(",
        "memory_extraction",
        "file_retrieval_adapter",
        "telegram_adapter",
    ]:
        assert forbidden not in text


def test_required_runtime_document_exists_and_contains_mandatory_sections_and_decisions():
    assert RUNTIME_DOC_PATH.is_file()
    text = RUNTIME_DOC_PATH.read_text()

    for section in REQUIRED_RUNTIME_SECTIONS:
        assert f"## {section}" in text
    for line in REQUIRED_DECISION_LINES:
        assert line in text


def test_required_upstream_tracking_document_exists_and_contains_source_labels():
    assert UPSTREAM_DOC_PATH.is_file()
    text = UPSTREAM_DOC_PATH.read_text()

    for section in REQUIRED_UPSTREAM_SECTIONS:
        assert f"## {section}" in text
    for required in [
        f"Upstream repository: {HERMES_UPSTREAM_REPOSITORY}",
        f"Upstream owner: {HERMES_UPSTREAM_OWNER}",
        f"Project name: {HERMES_PROJECT_NAME}",
        f"Source status: {HERMES_SOURCE_STATUS}",
        f"Roboticxs approval status: {ROBOTICXS_APPROVAL_STATUS}",
    ]:
        assert required in text


def test_upstream_tracking_preserves_non_auto_update_and_future_adoption_gate():
    text = UPSTREAM_DOC_PATH.read_text()

    assert "Hermes upstream changes do not automatically modify Roboticxs runtime." in text
    assert (
        "Hermes upstream changes must be reviewed through a future explicit maintainer-authorized stage before adoption."
        in text
    )
    assert "Future Hermes upstream adoption requires explicit maintainer authorization." in text
    assert "Do not auto-update dependencies." in text
    assert "Do not auto-pull upstream code." in text
    assert "Do not run upstream install scripts inside the Roboticxs repo during 78P." in text


def test_no_hermes_dependency_or_upstream_installer_action_was_added():
    changed_dependency_files = changed_files_under(*DEPENDENCY_FILES)
    combined_text = "\n".join(
        path.read_text()
        for path in [RUNTIME_PATH, RUNTIME_DOC_PATH, UPSTREAM_DOC_PATH]
    )

    assert changed_dependency_files == []
    assert "pip install hermes-agent" not in combined_text
    assert "uv add hermes-agent" not in combined_text
    assert "npm install" not in combined_text
    assert "curl https://hermes-agent.nousresearch.com/install.sh | bash" not in combined_text
    assert "iex (irm https://hermes-agent.nousresearch.com/install.ps1)" not in combined_text


def test_no_telegram_caregiver_document_background_or_connector_runtime_was_added():
    changed = changed_files_under("app", "docs", "tests")

    assert "app/telegram_adapter.py" not in changed
    assert "app/caregiver_relay.py" not in changed
    assert "app/guided_routines.py" not in changed
    assert "app/document_control.py" not in changed
    assert "app/file_intake_control.py" not in changed
    assert "app/file_retrieval_adapter.py" not in changed
    assert all("connector" not in path.lower() for path in changed)


def test_roadmap_marks_78p_complete_and_later_stages_without_inventing_86p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"78P","stage_name":"Hermes Runtime Foundation Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/reference/HERMES_RUNTIME_FOUNDATION_BOOTSTRAP_v0_1.md"' in text
    assert '"docs/reference/HERMES_UPSTREAM_TRACKING_v0_1.md"' in text
    assert '"app/hermes_runtime.py"' in text
    assert '"tests/test_hermes_runtime_foundation.py"' in text
    assert '"stage_id":"79P","stage_name":"Telegram Bot Runtime Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"IMPLEMENTED_PENDING_REVIEW"' in text
    assert '"stage_id":"87P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
    assert '"after_commit_next_eligible":null' in text
