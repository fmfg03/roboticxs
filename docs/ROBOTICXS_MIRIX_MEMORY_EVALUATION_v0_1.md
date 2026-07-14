# Roboticxs MIRIX Memory Evaluation v0.1

Status: Research note / planned evaluation only. Not implemented runtime behavior.

## 1. Purpose

This note evaluates whether Zaubern's `MIRIX` should remain:
- backlog only,
- a planned future adapter,
- or rejected for Roboticxs MVP.

It does not change the current Roboticxs runtime or memory model.

## 2. Current repo-confirmed MIRIX role

Based on current Zaubern repo inspection, `MIRIX Core` appears to function primarily as a memory and continuity plane, not merely as anomaly detection.

Current repo-confirmed signals include:
- multiple memory types and storage backends,
- store/query/context interfaces,
- active context assembly,
- historical retrieval,
- service-level memory integration for workflow assessments.

The strongest current evidence came from:
- `/root/zaubern/services/mirix-core/README.md`
- `/root/zaubern/services/workflow-fit-assessment/mirix_integration.py`

## 3. Confirmed capabilities

Repo-confirmed or strongly evidenced today:
- memory type separation such as core, episodic, semantic, procedural, resource, and knowledge-oriented memory,
- storage strategy across PostgreSQL, Redis, vector-style memory, and file/storage layers,
- bounded context assembly for task execution,
- retrieval of historical memory for later analysis,
- multi-service use as an internal memory system,
- practical HTTP interfaces for storing and querying memory entries.

[Inferencia basada en repo inspection] `MIRIX` is best understood as a memory/continuity backend candidate, not a user-facing product concept.

## 4. Mixed-maturity / experimental capabilities

The repo also contains a broader MIRIX layer around:
- behavioral pattern analysis,
- consciousness drift metrics,
- cross-agent correlation,
- memory-enhanced policy or compliance enrichment.

These capabilities should not be treated as Roboticxs canon yet.

Reasons:
- some of the architecture material uses grand-theory framing rather than product-safe operational language,
- some analyzer code appears placeholder or mixed-maturity,
- current evidence is stronger for MIRIX as memory infrastructure than for MIRIX as a stable policy/correlation engine.

This means Roboticxs should explicitly separate:
- MIRIX memory core,
- MIRIX analyzer/enrichment layer.

## 5. Fit against the Roboticxs memory model

Roboticxs product surface should remain:
- Memory Center
- Robot Folder
- Mi informacion importante
- Lo que Robbie sabe
- approved / editable / forgettable memory

`MIRIX` should not be exposed as product branding.

If adopted later, the fit is internal:
- approved memory storage,
- structured memory types,
- active context assembly,
- historical retrieval,
- context bundling,
- continuity across tasks,
- possible tenant isolation by `user_id` / `robot_id` if supported or extensible without violating Roboticxs policy boundaries.

## 6. What should remain local in MVP

For Roboticxs MVP, the following should remain local-first:
- approved memory decisions,
- user-visible memory editing and forgetting,
- Memory Center / Robot Folder product semantics,
- source policy,
- action boundary policy,
- bounded background-work policy,
- local auditability for what Robbie knows and why.

MVP should not depend on MIRIX adoption.

## 7. Migration / adapter considerations

Questions that still need explicit technical validation before any adapter work:
- whether MIRIX can cleanly isolate by `user_id` and `robot_id`,
- whether approved-memory policy can be enforced without raw-capture defaults,
- whether memory entries can be edited, forgotten, exported, or marked outdated,
- whether bounded context bundles can be generated without pulling in mixed-maturity analyzer behavior,
- what minimum adapter surface Roboticxs would actually need.

[Inferencia basada en repo inspection] A sensible migration path would be:
1. keep Roboticxs local approved memory for MVP,
2. formalize Roboticxs memory policy and Robot Folder semantics,
3. evaluate a narrow MIRIX adapter for storage/query/context only,
4. keep analyzer/correlation/drift features out of the first integration path.

## 8. Recommendation

Recommendation: Planned adapter after MVP

Rationale:
- keep Roboticxs local approved memory for MVP,
- keep Memory Center / Robot Folder as the user-facing surface,
- evaluate MIRIX as an internal backend option only,
- do not expose MIRIX to users,
- do not adopt MIRIX analyzer, drift, correlation, or policy-enrichment layers into Roboticxs canon yet.
