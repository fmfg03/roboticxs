from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = REPO_ROOT / "runtime/hermes/AGENTS.md"
PROFILE_DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_PROFILE_REBASE_v0_1.md"
SOUL_PATH = REPO_ROOT / "runtime/hermes/SOUL.md"


def test_agents_file_contains_runtime_project_instructions_not_identity_copy():
    text = AGENTS_PATH.read_text()

    for required in [
        "# Roboticxs Hermes Agent Instructions",
        "Runtime base: Hermes Agent.",
        "Separation of Concerns",
        "Hermes = runtime capability",
        "Roboticxs = product experience, memory, packages, routines, cost governance",
        "Zaubern-lite = action authority and safety decisions",
        "Do not expose raw Hermes technical language to consumers.",
        "Do not treat Hermes profiles as security sandboxes.",
        "Do not treat Hermes memory as Roboticxs canonical memory.",
        "Do not treat Hermes command approval as Roboticxs business-action authority.",
    ]:
        assert required in text

    assert "You are Robbie" not in text


def test_profile_rebase_doc_preserves_product_owned_layers():
    text = PROFILE_DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Runtime Files",
        "Required Product-owned Layers",
        "Hermes Boundary Rules",
        "Consumer Command Surface",
        "What Is Intentionally Not Implemented",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "Stage 85P is implemented pending review.",
        "Hermes Agent is the runtime substrate.",
        "Roboticxs remains the product layer.",
        "Roboticxs Memory Center remains the canonical memory layer.",
        "Roboticxs SkillManifest remains the product/package/scope contract.",
        "Roboticxs Cost Governor remains the spend and wake decision layer.",
        "Zaubern-lite remains the action authority and safety decision layer.",
    ]:
        assert required in text


def test_profile_boundary_rejects_sandbox_memory_and_authority_overclaims():
    combined = "\n".join(
        [
            AGENTS_PATH.read_text(),
            PROFILE_DOC_PATH.read_text(),
        ]
    )

    for required in [
        "Hermes profiles are state isolation, not business authorization and not security sandboxing.",
        "Hermes memory is runtime memory, not Roboticxs canonical memory.",
        "Hermes command approval is not Roboticxs business-action authority.",
    ]:
        assert required in combined

    forbidden_overclaims = [
        "Hermes profiles are security sandboxes",
        "Hermes memory is canonical Roboticxs memory",
        "Hermes command approval is Roboticxs business-action authority",
        "Agent Skills allowed-tools is enforcement",
    ]
    for forbidden in forbidden_overclaims:
        assert forbidden not in combined


def test_raw_hermes_command_surface_requires_product_mapping():
    text = PROFILE_DOC_PATH.read_text()

    for required in [
        "No raw Hermes command is exposed to consumer users unless Roboticxs maps it to:",
        "user intent",
        "allowed plan",
        "authority boundary",
        "cost policy",
        "audit log",
        "safe fallback",
        "`/yolo` must never be exposed to consumer users.",
    ]:
        assert required in text


def test_85p_does_not_add_runtime_integration_behavior_to_profile_files():
    combined = "\n".join(
        [
            AGENTS_PATH.read_text(),
            PROFILE_DOC_PATH.read_text(),
            SOUL_PATH.read_text(),
        ]
    ).lower()

    forbidden_runtime_claims = [
        "installed hermes",
        "telegram gateway is implemented",
        "model routing is implemented",
        "tool interception is implemented",
        "automation blueprints are implemented",
        "memory center bridge is implemented",
    ]
    for forbidden in forbidden_runtime_claims:
        assert forbidden not in combined
