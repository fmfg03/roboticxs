from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_BLUEPRINT_AUTHORITY_BOUNDARIES_v0_1.md"
SKILL_ROOT = REPO_ROOT / "runtime/hermes/skills"
BLUEPRINT_PACKAGES = [
    "roboticxs-daily-brief",
    "roboticxs-research-radar",
    "roboticxs-caregiver-routine",
]


def test_blueprint_authority_doc_blocks_sensitive_actions_and_decision_classes():
    text = AUTHORITY_DOC.read_text()

    for prohibited in [
        "schedule silently",
        "write canonical Roboticxs Memory Center directly",
        "send external messages without confirmation",
        "execute payments",
        "execute refunds",
        "change credentials",
        "change permissions",
        "accept legal terms",
        "run production deploys",
        "perform destructive actions",
        "perform legal decisions",
        "perform medical decisions",
        "perform tax decisions",
        "perform financial decisions",
        "perform employment decisions",
        "perform identity decisions",
    ]:
        assert prohibited in text


def test_blueprint_authority_doc_allows_proposed_memory_only_not_canonical_memory():
    text = AUTHORITY_DOC.read_text()

    assert "Blueprint outputs may create `ProposedMemory` candidates" in text
    assert "Blueprint outputs must never write canonical memory automatically." in text
    assert "Hermes memory remains runtime memory, not canonical Roboticxs Memory Center." in text


def test_each_initial_blueprint_skill_restates_authority_boundaries():
    for package in BLUEPRINT_PACKAGES:
        text = (SKILL_ROOT / package / "SKILL.md").read_text()

        for required in [
            "It must not schedule silently.",
            "It must not write canonical Roboticxs Memory Center directly.",
            "without confirmation",
            "It must not execute payments, refunds, credential changes, permission changes, legal acceptance, production deploys, or destructive actions.",
            "Outputs may create `ProposedMemory` candidates only; never canonical memory automatically.",
            "Hermes remains runtime capability.",
            "Agent Skills remains portable packaging.",
            "Roboticxs SkillManifest remains product/package/scope authority.",
            "Zaubern-lite remains action authority.",
            "90P+ are not authorized.",
        ]:
            assert required in text
