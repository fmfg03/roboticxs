from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/reference/ROBOTICXS_MEMORY_PROJECTION_POLICY_v0_1.md"


def test_memory_projection_policy_doc_exists_and_is_docs_only_93p():
    text = DOC.read_text()

    assert DOC.is_file()
    assert "Status: 93P implemented pending review." in text
    for non_claim in [
        "no live Hermes memory provider integration",
        "no production projection service",
        "no canonical memory writes",
        "no automatic memory approval",
        "no tool/action authorization",
        "no permission expansion",
        "no 94P or later authorization",
    ]:
        assert non_claim in text


def test_projection_eligibility_blocks_unapproved_outdated_and_sensitive_without_policy():
    text = DOC.read_text()

    for required in [
        "approval status is approved",
        "`MemorySensitivity` is permitted by an explicit `MemoryProjectionPolicy`",
        "Rejected memories must not be injected.",
        "Outdated memories must not be injected.",
        "Stale memories must not be injected unless the policy explicitly allows stale review context and labels it as stale.",
        "Sensitive memories must require explicit projection policy.",
        "projection does not authorize a tool/action or expand permissions",
    ]:
        assert required in text


def test_boundary_memory_precedes_preference_and_caregiver_boundaries():
    text = DOC.read_text()

    for required in [
        "Boundary Memory has higher priority than preference memory.",
        "Caregiver escalation boundaries have higher priority than convenience, style, routine, or personalization preferences.",
        "Safety, consent, scope, allowed-use, and escalation constraints have higher priority than personalization.",
        "When memories conflict, choose the most restrictive valid memory and mark the conflict for review rather than blending incompatible facts.",
    ]:
        assert required in text


def test_projection_preserves_source_labels_and_not_fact_preferences():
    text = DOC.read_text()

    for required in [
        "`MemorySource`",
        "approval status",
        "`MemorySensitivity`",
        "`MemoryExpiry`",
        "`MemoryUseConstraint`",
        "Inferences must be labeled as inferences.",
        "Opinions/preferences must not be represented as facts.",
        "Caregiver memories must preserve human escalation boundaries.",
    ]:
        assert required in text
