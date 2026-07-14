# ECC Knowledge Compiler Factory Skill v0.1

## Purpose

Stage 74P defines a local-only ECC Knowledge Compiler factory skill for compiling knowledge from approved local sources into a non-authoritative packet.

The compiler is a factory support layer, not a Roboticxs user-facing runtime feature. It compiles local source evidence into a `KnowledgeCompilationPacket` that preserves source manifests, stable digests, evidence references, confidence labels, conflicts, risks, open questions, inert candidate memory notes, and candidate canon deltas.

Correct claim:

```text
Roboticxs Factory can prepare a non-authoritative knowledge compilation packet from approved local sources.
```

Forbidden claim:

```text
Roboticxs turns local synthesis into canonical truth or durable memory.
```

Core rule:

```text
A knowledge compilation packet is evidence-indexed synthesis, not authority.
```

## 74P policy

```json ecc-knowledge-compiler-policy
{
  "stage_id":"74P",
  "local_compilation_authorized":true,
  "approved_source_roots":["docs","artifacts","roboticxs_artifacts"],
  "memory_write_authorized":false,
  "proposed_memory_write_authorized":false,
  "live_retrieval_authorized":false,
  "connector_authorized":false,
  "network_access_authorized":false,
  "external_api_authorized":false,
  "mcp_authorized":false,
  "user_facing_command_authorized":false,
  "canon_delta_auto_apply_authorized":false
}
```

## Source contract

Inputs must be local file paths or structured source descriptors. Supported source kinds are:

```json ecc-knowledge-source-kinds
[
  "LOCAL_DOC",
  "LOCAL_ARTIFACT",
  "REPO_UNDERSTANDING_PACKET",
  "LOCAL_CONTEXT_ARTIFACT"
]
```

Sources must stay under approved roots. Sources outside the approved roots, missing sources, and unsupported suffixes return explicit refusal objects.

Supported suffixes are `.md`, `.txt`, and `.json`.

## Packet contract

```json ecc-knowledge-compilation-packet-contract
{
  "packet_name":"KnowledgeCompilationPacket",
  "required_fields":[
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
    "user_facing_command_authorized"
  ],
  "required_invariants":{
    "packet_type":"KNOWLEDGE_COMPILATION_PACKET",
    "non_authoritative":true,
    "memory_write_authorized":false,
    "proposed_memory_write_authorized":false,
    "live_retrieval_authorized":false,
    "connector_authorized":false,
    "network_access_authorized":false,
    "user_facing_command_authorized":false,
    "every_compiled_claim_has_evidence_refs":true,
    "every_inferred_claim_is_labeled_INFERRED":true,
    "candidate_memory_notes_status":"CANDIDATE_ONLY",
    "candidate_canon_deltas_status":"REQUIRES_APPROVAL"
  }
}
```

## Evidence and confidence rules

- Every source manifest entry includes a stable SHA-256 digest.
- Every compiled claim carries at least one evidence reference.
- Evidence references include source ID, line number, source digest, and excerpt.
- Inferred claims are labeled `INFERRED` and cannot be high-confidence truth claims.
- Unsupported claims are retained as `UNSUPPORTED`, not promoted to fact.
- Conflicting evidence produces conflict records with `UNRESOLVED` status.
- Conflicts are preserved instead of overwritten or silently resolved.

## Candidate deltas

Candidate memory notes are inert packet text only:

```json ecc-candidate-memory-note-policy
{
  "status":"CANDIDATE_ONLY",
  "writes_memory":false,
  "writes_proposed_memory":false,
  "requires_future_user_approval":true
}
```

Candidate canon deltas are inert packet text only:

```json ecc-candidate-canon-delta-policy
{
  "status":"REQUIRES_APPROVAL",
  "auto_applies_to_roadmap":false,
  "requires_future_story_spec_tests_validation":true
}
```

## Refusal behavior

The compiler returns a `KnowledgeCompilationRefusal` for:

- `MISSING_SOURCE`
- `DISALLOWED_SOURCE`
- `UNSUPPORTED_SOURCE`

Refusals do not create packets, memory records, proposed memory records, external calls, connector activity, retrieval activity, or roadmap changes.

## Required non-claims

- Roboticxs Factory does not write `MemoryItem` records in 74P.
- Roboticxs Factory does not write `ProposedMemory` runtime records in 74P.
- Roboticxs Factory does not activate live retrieval in 74P.
- Roboticxs Factory does not add connectors in 74P.
- Roboticxs Factory does not call web, network, APIs, MCP, Gmail, Drive, Notion, or external tools in 74P.
- Roboticxs Factory does not rewrite canonical roadmap content semantically in 74P.
- Roboticxs Factory does not convert synthesis into truth in 74P.
- Roboticxs Factory does not resolve conflicting sources silently in 74P.
- Roboticxs Factory does not add user-facing commands in 74P.
- Roboticxs Factory does not expand runtime behavior in 74P.

## Closeout transition

After 74P closes, 75P Agent-Reach Research Parking Lot becomes the next eligible stage. 74P does not implement 75P behavior.

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_ecc_knowledge_compiler.py`
- `python3 -m pytest -q tests/test_canonical_roadmap.py`
- `python3 -m pytest -q`
- `git diff --check`
- `git status --short`
