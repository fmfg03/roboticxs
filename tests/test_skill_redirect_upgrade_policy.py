from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_UPGRADE_AND_REDIRECT_POLICY_v0_1.md"
)


def test_redirect_upgrade_policy_doc_exists_and_is_reference_only():
    text = POLICY_DOC.read_text()

    assert POLICY_DOC.is_file()
    assert "Status: 91P implemented pending review." in text
    for non_claim in [
        "no subscription or payment implementation",
        "no runtime redirect",
        "no gateway changes",
        "no production enforcement code",
        "no Tool Authority Guard",
        "no UI",
        "no 92P or later authorization",
    ]:
        assert non_claim in text


def test_redirect_requires_another_enabled_skill_and_manifest_authority():
    text = POLICY_DOC.read_text()

    for required in [
        "Return `REDIRECT` when all are true:",
        "another enabled Roboticxs skill is the correct owner",
        "the target skill's SkillManifest allows the topic/action class",
        "the user plan already includes the target skill",
        'Example: Customer Support receives "What is JSON?" while Technical Help is enabled. Decision: `REDIRECT`.',
    ]:
        assert required in text


def test_upgrade_requires_disabled_paid_skill_and_no_fake_capability():
    text = POLICY_DOC.read_text()

    for required in [
        "Return `OFFER_UPGRADE` when all are true:",
        "the request belongs to a disabled paid skill or unavailable package",
        "the relevant package has an approved upgrade path in SkillManifest",
        "Upgrade copy must not claim that Roboticxs can already perform the paid-skill task.",
        "Example: Marketing Pack is disabled and the user asks for a content calendar. Decision: `OFFER_UPGRADE`.",
    ]:
        assert required in text


def test_clarify_and_refuse_scope_are_separate_from_execution():
    text = POLICY_DOC.read_text()

    for required in [
        "Return `CLARIFY` when the active skill likely owns the request but key details are missing.",
        "ambiguous \"send it now\" style requests",
        "Clarification must not execute an external action.",
        "Return `REFUSE_SCOPE` when the request is safe but outside the active skill",
        "Refusal must include a safe fallback",
    ]:
        assert required in text
