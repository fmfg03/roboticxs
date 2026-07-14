from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/reference/ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1.md"


def test_memory_center_bridge_doc_exists_and_is_docs_only_93p():
    text = DOC.read_text()

    assert DOC.is_file()
    assert "Status: 93P implemented pending review." in text
    for non_claim in [
        "no live Hermes memory provider integration",
        "no runtime gateway changes",
        "no production memory sync",
        "no canonical memory writes",
        "no UI",
        "no tool/action authorization",
        "no 94P or later authorization",
    ]:
        assert non_claim in text


def test_memory_center_bridge_defines_required_entities():
    text = DOC.read_text()

    for entity in [
        "`MemoryItem`",
        "`MemoryProjection`",
        "`MemoryProjectionPolicy`",
        "`MemoryContextBlock`",
        "`ProposedMemory`",
        "`MemoryWritebackRequest`",
        "`MemorySensitivity`",
        "`MemoryUseConstraint`",
        "`MemoryExpiry`",
        "`MemorySource`",
    ]:
        assert entity in text


def test_memory_center_bridge_preserves_canonical_authority_invariants():
    text = DOC.read_text()

    for invariant in [
        "Roboticxs Memory Center is canonical.",
        "Hermes memory is runtime memory, not canonical product memory.",
        "Approved Roboticxs `MemoryItem` records may be projected into Hermes runtime context.",
        "Hermes runtime output may propose memory candidates, but must not write canonical memory directly.",
        "Projection must preserve source, approval status, scope, sensitivity, expiry/staleness, and allowed-use constraints.",
        "Memory projection must not override Tool Authority Guard, Scope Guard, Cost Governor, or Zaubern-lite decisions.",
        "No projection may authorize a tool/action.",
        "No projection may silently expand a user's permissions.",
        "94P+ must remain not authorized.",
    ]:
        assert invariant in text


def test_memory_bridge_packet_is_non_runtime_governance_only():
    text = DOC.read_text()

    for required in [
        '"packet_type":"MemoryBridgeContractPacket"',
        '"status":"NON_RUNTIME_GOVERNANCE_PACKET"',
        '"stage":"93P"',
        '"canonical_memory_source":"Roboticxs Memory Center"',
        '"runtime_memory_role":"Hermes runtime memory only"',
        '"canonical_write_authorized":false',
        '"tool_authority_authorized":false',
        '"future_stage_authorized":false',
    ]:
        assert required in text
