from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/reference/ROBOTICXS_MEMORY_WRITEBACK_BOUNDARY_v0_1.md"


def test_memory_writeback_boundary_doc_exists_and_is_docs_only_93p():
    text = DOC.read_text()

    assert DOC.is_file()
    assert "Status: 93P implemented pending review." in text
    for non_claim in [
        "no canonical memory writes",
        "no production memory sync",
        "no live Hermes memory provider integration",
        "no automatic approval",
        "no UI",
        "no tool/action authorization",
        "no 94P or later authorization",
    ]:
        assert non_claim in text


def test_hermes_output_may_only_propose_memory_candidates():
    text = DOC.read_text()

    for required in [
        "Hermes runtime output may produce `ProposedMemory` candidates.",
        "Hermes runtime output must not write canonical memory directly.",
        "A `MemoryWritebackRequest` is a review request for a `ProposedMemory`, not a canonical memory write.",
        "Only Roboticxs Memory Center may accept, reject, modify, expire, or deactivate canonical `MemoryItem` records through a separately authorized product path.",
    ]:
        assert required in text


def test_writeback_preserves_labels_sensitivity_and_caregiver_boundaries():
    text = DOC.read_text()

    for required in [
        "`MemorySource`",
        "proposed `MemorySensitivity`",
        "proposed `MemoryUseConstraint`",
        "proposed `MemoryExpiry`",
        "whether the proposal is a fact, inference, opinion, or preference",
        "Inferences must be labeled as inferences.",
        "Opinions/preferences must not be represented as facts.",
        "Caregiver proposed memories must preserve human escalation boundaries and must not downgrade caregiver or clinician review.",
    ]:
        assert required in text


def test_writeback_request_schema_denies_canonical_writes():
    text = DOC.read_text()

    for required in [
        '"packet_type":"MemoryWritebackRequest"',
        '"status":"NON_CANONICAL_REVIEW_REQUEST"',
        '"stage":"93P"',
        '"canonical_write_authorized":false',
        '"requires_user_review":true',
        '"source":"hermes_runtime_output"',
        '"future_stage_authorized":false',
    ]:
        assert required in text
