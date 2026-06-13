from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Literal


SourceKind = Literal["LOCAL_DOC", "LOCAL_ARTIFACT", "REPO_UNDERSTANDING_PACKET", "LOCAL_CONTEXT_ARTIFACT"]
ClaimConfidence = Literal["HIGH", "MEDIUM", "LOW", "CONFLICTED", "UNSUPPORTED"]
ClaimLabel = Literal["EXPLICIT", "INFERRED", "UNSUPPORTED"]
RefusalReason = Literal["MISSING_SOURCE", "DISALLOWED_SOURCE", "UNSUPPORTED_SOURCE"]


ALLOWED_SOURCE_KINDS: tuple[SourceKind, ...] = (
    "LOCAL_DOC",
    "LOCAL_ARTIFACT",
    "REPO_UNDERSTANDING_PACKET",
    "LOCAL_CONTEXT_ARTIFACT",
)
SUPPORTED_SUFFIXES = {".md", ".txt", ".json"}


@dataclass(frozen=True, slots=True)
class KnowledgeSourceDescriptor:
    path: str
    source_id: str | None = None
    source_kind: SourceKind = "LOCAL_DOC"


@dataclass(frozen=True, slots=True)
class SourceManifestEntry:
    source_id: str
    source_kind: SourceKind
    path: str
    digest_sha256: str
    byte_length: int
    line_count: int


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    source_id: str
    line_number: int
    digest_sha256: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class CompiledClaim:
    claim_id: str
    text: str
    label: ClaimLabel
    confidence: ClaimConfidence
    evidence_refs: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.evidence_refs:
            raise ValueError("Every compiled claim must carry evidence references.")
        if self.label == "INFERRED" and self.confidence == "HIGH":
            raise ValueError("Inferred claims cannot be high-confidence truth claims.")


@dataclass(frozen=True, slots=True)
class ConflictRecord:
    conflict_id: str
    topic_key: str
    claim_ids: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    status: Literal["UNRESOLVED"] = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class CandidateMemoryNote:
    text: str
    status: Literal["CANDIDATE_ONLY"]
    evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class CandidateCanonDelta:
    text: str
    status: Literal["REQUIRES_APPROVAL"]
    evidence_refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeCompilationRefusal:
    source: str
    reason: RefusalReason
    message: str


@dataclass(frozen=True, slots=True)
class KnowledgeCompilationPacket:
    packet_id: str
    packet_type: Literal["KNOWLEDGE_COMPILATION_PACKET"]
    source_manifest: tuple[SourceManifestEntry, ...]
    source_digests: tuple[tuple[str, str], ...]
    compiled_claims: tuple[CompiledClaim, ...]
    conflicts: tuple[ConflictRecord, ...]
    risks: tuple[str, ...]
    open_questions: tuple[str, ...]
    candidate_memory_notes: tuple[CandidateMemoryNote, ...]
    candidate_canon_deltas: tuple[CandidateCanonDelta, ...]
    non_authoritative: bool
    memory_write_authorized: bool
    proposed_memory_write_authorized: bool
    live_retrieval_authorized: bool
    connector_authorized: bool
    network_access_authorized: bool
    user_facing_command_authorized: bool

    def __post_init__(self) -> None:
        if not self.non_authoritative:
            raise ValueError("74P packets must be non-authoritative.")
        for field_name in (
            "memory_write_authorized",
            "proposed_memory_write_authorized",
            "live_retrieval_authorized",
            "connector_authorized",
            "network_access_authorized",
            "user_facing_command_authorized",
        ):
            if getattr(self, field_name):
                raise ValueError(f"74P cannot authorize {field_name}.")
        for claim in self.compiled_claims:
            if not claim.evidence_refs:
                raise ValueError("Every compiled claim must carry evidence references.")


def compile_knowledge_packet(
    sources: list[str | KnowledgeSourceDescriptor],
    *,
    repo_root: str | Path | None = None,
    allowed_roots: tuple[str, ...] = ("docs", "artifacts", "roboticxs_artifacts"),
) -> KnowledgeCompilationPacket | KnowledgeCompilationRefusal:
    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    descriptors = [_coerce_source_descriptor(source) for source in sources]
    resolved_sources: list[tuple[KnowledgeSourceDescriptor, Path]] = []

    for descriptor in sorted(descriptors, key=lambda item: (item.path, item.source_id or "", item.source_kind)):
        refusal = _validate_source_descriptor(descriptor=descriptor, root=root, allowed_roots=allowed_roots)
        if refusal is not None:
            return refusal
        resolved_sources.append((descriptor, (root / descriptor.path).resolve()))

    manifest_entries: list[SourceManifestEntry] = []
    claims: list[CompiledClaim] = []
    candidate_memory_notes: list[CandidateMemoryNote] = []
    candidate_canon_deltas: list[CandidateCanonDelta] = []

    for descriptor, path in resolved_sources:
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("utf-8")
        digest = sha256(raw_bytes).hexdigest()
        source_id = descriptor.source_id or _source_id_for_path(path.relative_to(root).as_posix())
        lines = text.splitlines()
        manifest_entries.append(
            SourceManifestEntry(
                source_id=source_id,
                source_kind=descriptor.source_kind,
                path=path.relative_to(root).as_posix(),
                digest_sha256=digest,
                byte_length=len(raw_bytes),
                line_count=len(lines),
            )
        )
        for line_number, line in enumerate(lines, start=1):
            claim_text = _claim_text_from_line(line)
            if claim_text is None:
                continue
            evidence = EvidenceRef(
                source_id=source_id,
                line_number=line_number,
                digest_sha256=digest,
                excerpt=claim_text,
            )
            label = _claim_label(claim_text)
            claim = CompiledClaim(
                claim_id=_stable_id("claim", source_id, str(line_number), claim_text),
                text=claim_text,
                label=label,
                confidence=_confidence_for_claim(claim_text, label),
                evidence_refs=(evidence,),
            )
            claims.append(claim)
            if _looks_like_memory_candidate(claim_text):
                candidate_memory_notes.append(
                    CandidateMemoryNote(text=claim_text, status="CANDIDATE_ONLY", evidence_refs=(evidence,))
                )
            if _looks_like_canon_delta(claim_text):
                candidate_canon_deltas.append(
                    CandidateCanonDelta(text=claim_text, status="REQUIRES_APPROVAL", evidence_refs=(evidence,))
                )

    conflicts = _detect_conflicts(claims)
    conflicted_claim_ids = {claim_id for conflict in conflicts for claim_id in conflict.claim_ids}
    final_claims = tuple(
        _mark_conflicted_claim(claim) if claim.claim_id in conflicted_claim_ids else claim for claim in claims
    )

    packet_digest = sha256(
        "|".join(f"{entry.source_id}:{entry.digest_sha256}" for entry in manifest_entries).encode("utf-8")
    ).hexdigest()[:16]
    return KnowledgeCompilationPacket(
        packet_id=f"knowledge_compilation_{packet_digest}",
        packet_type="KNOWLEDGE_COMPILATION_PACKET",
        source_manifest=tuple(manifest_entries),
        source_digests=tuple((entry.source_id, entry.digest_sha256) for entry in manifest_entries),
        compiled_claims=final_claims,
        conflicts=conflicts,
        risks=_risks_for_packet(final_claims, conflicts),
        open_questions=_open_questions_for_packet(final_claims, conflicts),
        candidate_memory_notes=tuple(candidate_memory_notes),
        candidate_canon_deltas=tuple(candidate_canon_deltas),
        non_authoritative=True,
        memory_write_authorized=False,
        proposed_memory_write_authorized=False,
        live_retrieval_authorized=False,
        connector_authorized=False,
        network_access_authorized=False,
        user_facing_command_authorized=False,
    )


def _coerce_source_descriptor(source: str | KnowledgeSourceDescriptor) -> KnowledgeSourceDescriptor:
    if isinstance(source, KnowledgeSourceDescriptor):
        return source
    return KnowledgeSourceDescriptor(path=source)


def _validate_source_descriptor(
    *,
    descriptor: KnowledgeSourceDescriptor,
    root: Path,
    allowed_roots: tuple[str, ...],
) -> KnowledgeCompilationRefusal | None:
    if descriptor.source_kind not in ALLOWED_SOURCE_KINDS:
        return KnowledgeCompilationRefusal(
            source=descriptor.path,
            reason="UNSUPPORTED_SOURCE",
            message=f"Unsupported 74P source kind: {descriptor.source_kind}.",
        )
    path = (root / descriptor.path).resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return KnowledgeCompilationRefusal(
            source=descriptor.path,
            reason="DISALLOWED_SOURCE",
            message="74P sources must stay inside the local repo root and approved roots.",
        )
    if not any(relative.parts and relative.parts[0] == allowed_root for allowed_root in allowed_roots):
        return KnowledgeCompilationRefusal(
            source=descriptor.path,
            reason="DISALLOWED_SOURCE",
            message=f"74P sources must stay under approved roots: {', '.join(allowed_roots)}.",
        )
    if not path.exists() or not path.is_file():
        return KnowledgeCompilationRefusal(
            source=descriptor.path,
            reason="MISSING_SOURCE",
            message="74P source does not exist or is not a file.",
        )
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return KnowledgeCompilationRefusal(
            source=descriptor.path,
            reason="UNSUPPORTED_SOURCE",
            message=f"Unsupported 74P source suffix: {path.suffix or '<none>'}.",
        )
    return None


def _claim_text_from_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith(("```", "|", "#")):
        return None
    stripped = re.sub(r"^[-*]\s+", "", stripped)
    stripped = re.sub(r"^\d+\.\s+", "", stripped)
    if len(stripped) < 12:
        return None
    lowered = stripped.lower()
    claim_markers = (
        " is ",
        " are ",
        " must ",
        " should ",
        " does ",
        " do not ",
        " no ",
        " next eligible",
        "requires approval",
        "candidate",
        "unsupported",
        "conflict",
    )
    if any(marker in lowered for marker in claim_markers):
        return stripped
    return None


def _claim_label(text: str) -> ClaimLabel:
    lowered = text.lower()
    if any(marker in lowered for marker in ("unsupported", "not backed", "no evidence")):
        return "UNSUPPORTED"
    if any(marker in lowered for marker in ("likely", "may ", "might", "should", "candidate", "proposed", "planned", "future")):
        return "INFERRED"
    return "EXPLICIT"


def _confidence_for_claim(text: str, label: ClaimLabel) -> ClaimConfidence:
    if label == "UNSUPPORTED":
        return "UNSUPPORTED"
    if label == "INFERRED":
        return "LOW"
    if any(marker in text.lower() for marker in ("risk", "unknown", "conflict")):
        return "MEDIUM"
    return "HIGH"


def _looks_like_memory_candidate(text: str) -> bool:
    lowered = text.lower()
    return "memory" in lowered or "remember" in lowered


def _looks_like_canon_delta(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("canonical roadmap", "canon", "stage ", "next eligible"))


def _detect_conflicts(claims: list[CompiledClaim]) -> tuple[ConflictRecord, ...]:
    by_topic: dict[str, list[CompiledClaim]] = {}
    for claim in claims:
        topic = _topic_key(claim.text)
        if topic:
            by_topic.setdefault(topic, []).append(claim)

    conflicts: list[ConflictRecord] = []
    for topic, topic_claims in sorted(by_topic.items()):
        polarities = {_polarity(claim.text) for claim in topic_claims}
        if "AFFIRM" in polarities and "NEGATE" in polarities:
            evidence_refs = tuple(ref for claim in topic_claims for ref in claim.evidence_refs)
            claim_ids = tuple(claim.claim_id for claim in topic_claims)
            conflicts.append(
                ConflictRecord(
                    conflict_id=_stable_id("conflict", topic, *claim_ids),
                    topic_key=topic,
                    claim_ids=claim_ids,
                    evidence_refs=evidence_refs,
                )
            )
    return tuple(conflicts)


def _topic_key(text: str) -> str:
    lowered = text.lower()
    normalized = re.sub(r"\b(is|are|must|should|does|do|not|no|authorized|enabled|disabled|allowed|blocked)\b", " ", lowered)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    words = [word for word in normalized.split() if word not in {"the", "a", "an", "in", "for", "to", "by"}]
    return " ".join(words[:6])


def _polarity(text: str) -> Literal["AFFIRM", "NEGATE", "NEUTRAL"]:
    lowered = text.lower()
    if any(marker in lowered for marker in (" not ", " no ", "disabled", "blocked", "forbidden", "unauthorized")):
        return "NEGATE"
    if any(marker in lowered for marker in (" is ", " are ", "enabled", "allowed", "authorized")):
        return "AFFIRM"
    return "NEUTRAL"


def _mark_conflicted_claim(claim: CompiledClaim) -> CompiledClaim:
    return CompiledClaim(
        claim_id=claim.claim_id,
        text=claim.text,
        label=claim.label,
        confidence="CONFLICTED",
        evidence_refs=claim.evidence_refs,
    )


def _risks_for_packet(claims: tuple[CompiledClaim, ...], conflicts: tuple[ConflictRecord, ...]) -> tuple[str, ...]:
    risks: list[str] = ["KnowledgeCompilationPacket is non-authoritative synthesis, not truth."]
    if conflicts:
        risks.append("Conflicting source evidence is unresolved and requires human review.")
    if any(claim.label == "UNSUPPORTED" for claim in claims):
        risks.append("Unsupported claims are retained as unsupported, not promoted to fact.")
    if any(claim.label == "INFERRED" for claim in claims):
        risks.append("Inferred claims require approval before canon or memory changes.")
    return tuple(risks)


def _open_questions_for_packet(
    claims: tuple[CompiledClaim, ...],
    conflicts: tuple[ConflictRecord, ...],
) -> tuple[str, ...]:
    questions: list[str] = []
    if conflicts:
        questions.append("Which conflicting source should govern after human review?")
    if any(claim.label == "UNSUPPORTED" for claim in claims):
        questions.append("Which unsupported claims should be removed or backed with approved evidence?")
    if not claims:
        questions.append("Which approved local sources should be added before compiling claims?")
    return tuple(questions)


def _source_id_for_path(path: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_").lower()
    return normalized or "local_source"


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
