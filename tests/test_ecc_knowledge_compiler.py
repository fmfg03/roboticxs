from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import sys

from app.db import init_db
from app.ecc_knowledge_compiler import (
    KnowledgeCompilationPacket,
    KnowledgeCompilationRefusal,
    KnowledgeSourceDescriptor,
    compile_knowledge_packet,
)
from app.models import MemoryItem, ProposedMemory
from sqlalchemy import func, select


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs/reference/ECC_KNOWLEDGE_COMPILER_FACTORY_SKILL_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "packet_type",
    "source_manifest",
    "source_digests",
    "compiled_claims",
    "conflicts",
    "risks",
    "open_questions",
    "candidate_memory_notes",
    "candidate_canon_deltas",
    "non_authoritative",
    "memory_write_authorized",
    "proposed_memory_write_authorized",
    "live_retrieval_authorized",
    "connector_authorized",
    "network_access_authorized",
    "user_facing_command_authorized",
}


def write_source(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def assert_packet(packet: KnowledgeCompilationPacket | KnowledgeCompilationRefusal) -> KnowledgeCompilationPacket:
    assert isinstance(packet, KnowledgeCompilationPacket)
    return packet


def test_compile_allowed_local_docs_and_artifacts_into_packet(tmp_path: Path):
    write_source(
        tmp_path,
        "docs/source.md",
        """
# Local doc
- Retrieval is disabled.
- The local compiler should preserve source evidence.
""",
    )
    write_source(
        tmp_path,
        "artifacts/context/repo_packet.md",
        """
# Repo packet
- Repo understanding packet is local context.
""",
    )

    packet = assert_packet(
        compile_knowledge_packet(
            [
                "docs/source.md",
                KnowledgeSourceDescriptor(
                    path="artifacts/context/repo_packet.md",
                    source_id="repo_context_packet",
                    source_kind="REPO_UNDERSTANDING_PACKET",
                ),
            ],
            repo_root=tmp_path,
        )
    )

    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_type == "KNOWLEDGE_COMPILATION_PACKET"
    assert packet.non_authoritative is True
    assert [entry.path for entry in packet.source_manifest] == [
        "artifacts/context/repo_packet.md",
        "docs/source.md",
    ]
    assert packet.source_manifest[0].source_kind == "REPO_UNDERSTANDING_PACKET"
    assert packet.source_manifest[0].source_id == "repo_context_packet"
    assert len(packet.compiled_claims) >= 2


def test_reject_source_outside_allowlisted_roots(tmp_path: Path):
    write_source(tmp_path, "app/private.md", "- Private runtime note is not an approved 74P source.")

    refusal = compile_knowledge_packet(["app/private.md"], repo_root=tmp_path)

    assert isinstance(refusal, KnowledgeCompilationRefusal)
    assert refusal.reason == "DISALLOWED_SOURCE"
    assert "approved roots" in refusal.message


def test_missing_and_unsupported_sources_return_clear_refusals(tmp_path: Path):
    missing = compile_knowledge_packet(["docs/missing.md"], repo_root=tmp_path)
    assert isinstance(missing, KnowledgeCompilationRefusal)
    assert missing.reason == "MISSING_SOURCE"

    write_source(tmp_path, "docs/binary.bin", "Retrieval is disabled.")
    unsupported = compile_knowledge_packet(["docs/binary.bin"], repo_root=tmp_path)
    assert isinstance(unsupported, KnowledgeCompilationRefusal)
    assert unsupported.reason == "UNSUPPORTED_SOURCE"


def test_include_source_digests_and_evidence_refs(tmp_path: Path):
    source_path = write_source(tmp_path, "docs/source.md", "- Budget guard is local.\n")

    packet = assert_packet(compile_knowledge_packet(["docs/source.md"], repo_root=tmp_path))

    assert packet.source_manifest[0].digest_sha256
    assert packet.source_manifest[0].digest_sha256 == packet.source_digests[0][1]
    assert packet.source_manifest[0].byte_length == len(source_path.read_bytes())
    claim = packet.compiled_claims[0]
    assert claim.evidence_refs
    assert claim.evidence_refs[0].source_id == packet.source_manifest[0].source_id
    assert claim.evidence_refs[0].line_number == 1
    assert claim.evidence_refs[0].digest_sha256 == packet.source_manifest[0].digest_sha256


def test_label_unsupported_inferred_and_conflicted_claims(tmp_path: Path):
    write_source(
        tmp_path,
        "docs/source.md",
        """
- Retrieval is enabled.
- Retrieval is disabled.
- Memory candidate should stay inert.
- Unsupported claim has no evidence.
""",
    )

    packet = assert_packet(compile_knowledge_packet(["docs/source.md"], repo_root=tmp_path))

    claims_by_text = {claim.text: claim for claim in packet.compiled_claims}
    assert claims_by_text["Memory candidate should stay inert."].label == "INFERRED"
    assert claims_by_text["Memory candidate should stay inert."].confidence == "LOW"
    assert claims_by_text["Unsupported claim has no evidence."].label == "UNSUPPORTED"
    assert claims_by_text["Unsupported claim has no evidence."].confidence == "UNSUPPORTED"
    assert claims_by_text["Retrieval is enabled."].confidence == "CONFLICTED"
    assert claims_by_text["Retrieval is disabled."].confidence == "CONFLICTED"
    assert packet.conflicts
    assert packet.conflicts[0].status == "UNRESOLVED"


def test_preserve_conflicts_instead_of_overwriting(tmp_path: Path):
    write_source(
        tmp_path,
        "docs/source.md",
        """
- Connector is authorized.
- Connector is not authorized.
""",
    )

    packet = assert_packet(compile_knowledge_packet(["docs/source.md"], repo_root=tmp_path))

    assert len(packet.conflicts) == 1
    conflict_claim_ids = set(packet.conflicts[0].claim_ids)
    assert {claim.claim_id for claim in packet.compiled_claims} == conflict_claim_ids
    assert {claim.text for claim in packet.compiled_claims} == {
        "Connector is authorized.",
        "Connector is not authorized.",
    }


def test_no_memory_or_proposed_memory_writes(tmp_path: Path):
    write_source(tmp_path, "docs/source.md", "- Memory candidate should remain candidate only.\n")
    db = init_db(f"sqlite:///{tmp_path / 'test.db'}")

    before = _memory_counts(db)
    packet = assert_packet(compile_knowledge_packet(["docs/source.md"], repo_root=tmp_path))
    after = _memory_counts(db)

    assert before == after == {"memories": 0, "proposals": 0}
    assert packet.memory_write_authorized is False
    assert packet.proposed_memory_write_authorized is False
    assert packet.candidate_memory_notes
    assert {note.status for note in packet.candidate_memory_notes} == {"CANDIDATE_ONLY"}


def test_no_connector_retrieval_network_dependency_is_introduced():
    module_path = REPO_ROOT / "app/ecc_knowledge_compiler.py"
    text = module_path.read_text()

    for forbidden in [
        "requests",
        "httpx",
        "urllib",
        "socket",
        "app.db",
        "app.models",
        "MemoryItem",
        "ProposedMemory",
    ]:
        assert forbidden not in text


def test_candidate_canon_deltas_require_approval(tmp_path: Path):
    write_source(tmp_path, "docs/source.md", "- Stage 75P is next eligible after 74P.\n")

    packet = assert_packet(compile_knowledge_packet(["docs/source.md"], repo_root=tmp_path))

    assert packet.candidate_canon_deltas
    assert {delta.status for delta in packet.candidate_canon_deltas} == {"REQUIRES_APPROVAL"}
    assert packet.user_facing_command_authorized is False


def test_deterministic_packet_output_for_same_inputs(tmp_path: Path):
    write_source(tmp_path, "docs/b.md", "- B source is local.\n")
    write_source(tmp_path, "docs/a.md", "- A source is local.\n")

    first = compile_knowledge_packet(["docs/b.md", "docs/a.md"], repo_root=tmp_path)
    second = compile_knowledge_packet(["docs/a.md", "docs/b.md"], repo_root=tmp_path)

    assert first == second


def test_docs_contain_required_boundary_language():
    text = DOC_PATH.read_text()

    for required in [
        "Stage 74P defines a local-only ECC Knowledge Compiler factory skill",
        "A knowledge compilation packet is evidence-indexed synthesis, not authority.",
        "Roboticxs Factory does not write `MemoryItem` records in 74P.",
        "Roboticxs Factory does not write `ProposedMemory` runtime records in 74P.",
        "Roboticxs Factory does not activate live retrieval in 74P.",
        "Roboticxs Factory does not add connectors in 74P.",
        "Roboticxs Factory does not call web, network, APIs, MCP, Gmail, Drive, Notion, or external tools in 74P.",
        "Roboticxs Factory does not convert synthesis into truth in 74P.",
        "Roboticxs Factory does not resolve conflicting sources silently in 74P.",
        "Candidate canon deltas are inert packet text only",
        "75P Agent-Reach Research Parking Lot becomes the next eligible stage",
    ]:
        assert required in text


def test_roadmap_marks_74p_completed_and_75p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"app/ecc_knowledge_compiler.py"' in text
    assert '"docs/reference/ECC_KNOWLEDGE_COMPILER_FACTORY_SKILL_v0_1.md"' in text
    assert '"tests/test_ecc_knowledge_compiler.py"' in text
    assert '"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"after_commit_next_eligible":"76P"' in text


def _memory_counts(db) -> dict[str, int]:
    with db.session() as session:
        return {
            "memories": session.scalar(select(func.count()).select_from(MemoryItem)),
            "proposals": session.scalar(select(func.count()).select_from(ProposedMemory)),
        }
