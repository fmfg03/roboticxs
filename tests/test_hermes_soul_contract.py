from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOUL_PATH = REPO_ROOT / "runtime/hermes/SOUL.md"
SOUL_DOC_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_SOUL_v0_1.md"
SPEC_PATH = REPO_ROOT / "docs/reference/85P_HERMES_PROFILE_ROBOTICXS_SOUL_REBASE_SPEC_v0_1.md"


def test_soul_file_exists_and_defines_robbie_identity_and_voice():
    text = SOUL_PATH.read_text()

    for required in [
        "# Roboticxs Soul",
        "You are Robbie",
        "personal AI robot",
        "everyday work and family coordination",
        "not a generic chatbot",
        "practical, direct, calm, and useful",
        "Speak in the user's language by default",
        "Spanish is the default",
        "Distinguish fact, inference, opinion, uncertainty, and missing context",
    ]:
        assert required in text


def test_soul_file_is_identity_style_only_without_project_or_runtime_instructions():
    text = SOUL_PATH.read_text()
    lower_text = text.lower()

    forbidden_literals = [
        "runtime/hermes",
        "docs/",
        "tests/",
        "python3",
        "pytest",
        "git ",
        "localhost",
        "api key",
        "token=",
        "config.yaml",
        ".env",
        "roadmap",
        "stage ",
        "85p",
        "hermes profile",
        "slash command",
        "raw hermes",
        "allowed-tools",
        "sandbox",
    ]
    for forbidden in forbidden_literals:
        assert forbidden not in lower_text


def test_soul_file_sets_sensitive_action_and_decision_boundaries_without_fake_enforcement():
    text = SOUL_PATH.read_text()
    lower_text = text.lower()

    for required in [
        "Ask before sensitive actions",
        "Draft and prepare before executing",
        "Do not silently send external messages",
        "Do not execute payments",
        "credential changes",
        "permission changes",
        "legal acceptance",
        "destructive actions",
        "Do not make medical, legal, tax, financial, employment, or identity decisions",
    ]:
        assert required in text

    forbidden_claims = [
        "guarantee",
        "compliant by default",
        "secure sandbox",
        "safety enforcement layer",
        "legally valid",
    ]
    for forbidden in forbidden_claims:
        assert forbidden not in lower_text


def test_soul_reference_doc_records_contract_and_non_claims():
    text = SOUL_DOC_PATH.read_text()

    for section in [
        "Status",
        "Decision",
        "Identity",
        "Voice",
        "Allowed SOUL Content",
        "Disallowed SOUL Content",
        "Product Boundaries",
        "Non-claims",
    ]:
        assert f"## {section}" in text

    for required in [
        "Stage 85P is implemented pending review.",
        "identity and style only",
        "must not include",
        "repo paths",
        "commands",
        "Hermes config keys",
        "fake enforcement claims",
        "does not make Hermes profiles security sandboxes",
        "does not make Hermes memory canonical Roboticxs memory",
        "does not make Hermes command approval Roboticxs business-action authority",
    ]:
        assert required in text


def test_approved_85p_spec_is_present_and_keeps_86p_out_of_scope():
    text = SPEC_PATH.read_text()

    assert "# 85P - Hermes Profile / Roboticxs SOUL Rebase v0.1" in text
    assert "Status: approved technical spec" in text
    assert "85P does not implement" in text
    assert "86P+ are listed as proposed/future only" in text
