from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/research/VOXCPM_RESEARCH_PARKING_LOT_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

MANDATORY_SECTIONS = [
    "Status",
    "Decision",
    "Required source references",
    "Why this exists",
    "What upstream materials appear to describe",
    "Potential Roboticxs value",
    "Hard boundaries",
    "Blocked for now",
    "Risk register",
    "Authority implications",
    "Privacy implications",
    "Budget implications",
    "Connector implications",
    "Memory implications",
    "Runtime implications",
    "Future adapter requirements",
    "Open questions",
    "Recommended next stage",
    "Non-claims",
]

REQUIRED_SOURCES = [
    "https://github.com/OpenBMB/VoxCPM",
    "OpenBMB",
    "EXTERNAL_RESEARCH_SOURCE",
    "RESEARCH_ONLY",
    "https://arxiv.org/abs/2509.24650",
    "arXiv:2509.24650",
    "https://arxiv.org/abs/2606.06928",
    "arXiv:2606.06928",
]

BLOCKED_BEHAVIORS = [
    "No runtime integration.",
    "No production dependency.",
    "No development dependency.",
    "No model download.",
    "No model weights.",
    "No inference.",
    "No TTS execution.",
    "No audio generation.",
    "No voice cloning.",
    "No voice design runtime.",
    "No speaker authentication.",
    "No speaker identification.",
    "No Telegram voice handling.",
    "No audio upload handling.",
    "No raw audio storage.",
    "No generated audio storage.",
    "No durable transcript storage.",
    "No background listening.",
    "No streaming audio runtime.",
    "No local web demo.",
    "No server process.",
    "No OpenAI-compatible audio endpoint.",
    "No CUDA, PyTorch, vLLM, Nano-vLLM, ModelScope, or Hugging Face integration.",
    "No connector registration.",
    "No MCP server registration.",
    "No external API calls.",
    "No user-facing commands.",
    "No capability catalog activation.",
    "No automatic roadmap promotion.",
    "No claims that Roboticxs supports VoxCPM or VoxCPM2.",
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


def test_research_note_exists_and_contains_mandatory_sections():
    assert DOC_PATH.is_file()
    text = DOC_PATH.read_text()

    for section in MANDATORY_SECTIONS:
        assert f"## {section}" in text


def test_research_only_decision_and_source_references_are_explicit():
    text = DOC_PATH.read_text()

    assert "VoxCPM is parked as RESEARCH_ONLY." in text
    assert "VoxCPM2 is parked as RESEARCH_ONLY." in text
    assert "The upstream repository is an external research source, not a Roboticxs dependency." in text
    assert "The arXiv papers are source references, not product truth." in text
    assert "Roboticxs approval status: RESEARCH_ONLY." in text
    assert "Source status: EXTERNAL_RESEARCH_SOURCE." in text
    for source in REQUIRED_SOURCES:
        assert source in text


def test_upstream_capabilities_are_labeled_as_research_not_product_truth():
    text = DOC_PATH.read_text()

    for upstream_claim in [
        "tokenizer-free TTS",
        "2B parameter model",
        "30-language support",
        "Voice Design",
        "Controllable Voice Cloning",
        "48kHz audio output",
        "streaming-related claims",
        "Apache-2.0 release",
        "quick-start examples",
    ]:
        assert upstream_claim in text
    assert "upstream public materials" in text
    assert "not verified integration claims" in text
    assert "Roboticxs must avoid claims beyond the exact upstream repository and paper/report sources." in text


def test_hard_boundaries_are_preserved():
    text = DOC_PATH.read_text()

    for required in BLOCKED_BEHAVIORS:
        assert required in text


def test_blocked_runtime_and_dependency_paths_are_explicit():
    text = DOC_PATH.read_text()

    for required in [
        "Installing `voxcpm` is blocked.",
        "Installing `modelscope` for VoxCPM is blocked.",
        "Installing Nano-vLLM or vLLM-Omni for VoxCPM is blocked.",
        "Adding VoxCPM to `pyproject.toml` or any lockfile is blocked.",
        "Downloading `openbmb/VoxCPM2` or any related weights is blocked.",
        "Running repository quick-start examples is blocked.",
        "Running a VoxCPM web demo is blocked.",
        "Running a VoxCPM serving endpoint is blocked.",
        "Processing user audio through VoxCPM is blocked.",
        "Generating synthetic speech is blocked.",
        "Cloning a voice from reference audio is blocked.",
        "Designing a voice from natural-language description is blocked.",
        "Adding Telegram voice-note handling is blocked.",
        "Marking VoxCPM as an approved integration is blocked.",
    ]:
        assert required in text


def test_authority_model_blocks_voice_execution_and_storage_operations():
    text = DOC_PATH.read_text()

    for operation in [
        "READ_EXTERNAL_SOURCE",
        "EVALUATE_VOICE_MODEL",
        "DOWNLOAD_MODEL",
        "RUN_INFERENCE",
        "GENERATE_AUDIO",
        "CLONE_VOICE",
        "STORE_AUDIO",
        "SEND_AUDIO",
        "AUTHENTICATE_SPEAKER",
    ]:
        assert operation in text
    assert "Only `READ_EXTERNAL_SOURCE` and `EVALUATE_VOICE_MODEL` are candidates" in text
    assert "`DOWNLOAD_MODEL`, `RUN_INFERENCE`, `GENERATE_AUDIO`, `CLONE_VOICE`, `STORE_AUDIO`, `SEND_AUDIO`, and `AUTHENTICATE_SPEAKER` remain blocked" in text


def test_no_voxcpm_import_or_runtime_dependency_under_app():
    for path in (REPO_ROOT / "app").rglob("*.py"):
        text = path.read_text()
        normalized = text.lower()
        assert "voxcpm" not in normalized, path


def test_dependency_files_do_not_include_voxcpm():
    for relative in DEPENDENCY_FILES:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        normalized = path.read_text().lower()
        assert "voxcpm" not in normalized, path
        assert "openbmb/voxcpm" not in normalized, path


def test_no_user_facing_voxcpm_command_was_added():
    command_surface_files = [
        REPO_ROOT / "app/command_registry.py",
        REPO_ROOT / "app/orchestrator.py",
        REPO_ROOT / "app/telegram_adapter.py",
        REPO_ROOT / "app/main.py",
    ]

    for path in command_surface_files:
        text = path.read_text().lower()
        assert "voxcpm" not in text, path


def test_roadmap_marks_76p_complete_and_later_gates_without_inventing_86p():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"docs/research/VOXCPM_RESEARCH_PARKING_LOT_v0_1.md"' in text
    assert '"tests/test_voxcpm_research_parking_lot.py"' in text
    assert '"after_commit_next_eligible":null' in text
    assert "No local next eligible implementation stage is authorized after 76P." in text
    assert '"stage_id":"77P","stage_name":"Roadmap Continuation Authorization Gate v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"78P","stage_name":"Hermes Runtime Foundation Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"79P","stage_name":"Telegram Bot Runtime Bootstrap v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED"' in text
    assert '"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"87P"' in text
    assert '"stage_id":"87P","stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"88P"' in text
    assert '"stage_id":"88P","stage_name":"Routine Wake Gate / Zero-Token Preflight v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"89P"' in text
    assert '"stage_id":"89P","stage_name":"Roboticxs Automation Blueprints v0","status":"CLOSED_COMMITTED"' in text
    assert '"after_commit_next_eligible":"90P"' in text
    assert '"stage_id":"90P"' not in text
    assert '"stage_id":"91P"' not in text
    assert '"status":"NEXT_ELIGIBLE"' not in text
