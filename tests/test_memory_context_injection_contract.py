from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/reference/ROBOTICXS_MEMORY_CONTEXT_INJECTION_CONTRACT_v0_1.md"


def test_memory_context_injection_contract_doc_exists_and_is_docs_only_93p():
    text = DOC.read_text()

    assert DOC.is_file()
    assert "Status: 93P implemented pending review." in text
    for non_claim in [
        "no live context injection",
        "no live Hermes memory provider integration",
        "no runtime gateway changes",
        "no production memory sync",
        "no canonical memory writes",
        "no tool/action authorization",
        "no permission expansion",
        "no 94P or later authorization",
    ]:
        assert non_claim in text


def test_memory_context_block_preserves_projection_metadata():
    text = DOC.read_text()

    for required in [
        "`MemoryContextBlock` is the runtime-safe representation of selected `MemoryProjection` records.",
        "source of truth set to Roboticxs Memory Center",
        "runtime target set to Hermes context",
        "projection policy id",
        "Each injected projection must preserve source, approval status, scope, sensitivity, expiry/staleness, and allowed-use constraints.",
        "Outdated or rejected memories must not be injected.",
        "Sensitive memories must require explicit projection policy.",
        "Boundary Memory must be ordered before preference memory.",
    ]:
        assert required in text


def test_memory_context_block_labels_inference_preference_and_caregiver_boundaries():
    text = DOC.read_text()

    for required in [
        "Inferences must be labeled as inferences.",
        "Opinions/preferences must not be represented as facts.",
        "Caregiver memories must preserve human escalation boundaries.",
    ]:
        assert required in text


def test_memory_context_block_is_not_authority():
    text = DOC.read_text()

    for required in [
        "Memory projection must not override Tool Authority Guard, Scope Guard, Cost Governor, or Zaubern-lite decisions.",
        "No projection may authorize a tool/action.",
        "No projection may silently expand a user's permissions.",
        "No `MemoryContextBlock` may claim that Hermes runtime memory is canonical product memory.",
        '"packet_type":"MemoryContextBlock"',
        '"status":"NON_AUTHORITY_RUNTIME_CONTEXT"',
        '"stage":"93P"',
        '"source_of_truth":"Roboticxs Memory Center"',
        '"runtime_target":"Hermes context"',
        '"tool_action_authorization":false',
        '"permission_expansion_authorized":false',
        '"future_stage_authorized":false',
    ]:
        assert required in text
