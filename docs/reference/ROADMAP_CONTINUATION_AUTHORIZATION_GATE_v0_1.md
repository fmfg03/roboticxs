# Roadmap Continuation Authorization Gate v0.1

## Status

Stage 77P defines a docs-only roadmap governance gate.

This stage creates no Roboticxs product feature, runtime capability, connector, retrieval behavior, memory behavior, model-router behavior, Telegram behavior, API route, dependency, MCP/tool config, staging authority, or commit authority.

## Decision

77P is a roadmap continuation authorization gate.
It does not authorize a product feature.
It does not authorize runtime changes.
It does not authorize connector changes.
It does not authorize retrieval changes.
It does not authorize memory changes.
It does not authorize model-router changes.
It does not authorize user-facing commands.
It does not authorize staging.
It does not authorize commit.
It does not create 78P as NEXT_ELIGIBLE.
No next implementation stage is authorized until a maintainer explicitly chooses one.

## Why this gate exists

After 76P, the roadmap intentionally has no locally authorized next eligible stage. That terminal condition is a control, not a gap.

Without a continuation gate, future Codex runs could infer a new stage from conversation context, research parking lots, validation output, or product priorities. 77P separates roadmap state inspection, candidate option compilation, human authorization, implementation, staging, and commit.

## Current roadmap terminal state

The current terminal stage is 76P, closed at commit `3a03d6c`.

The 76P closeout states that no local next eligible implementation stage is authorized after 76P. 77P records that condition and adds a governance packet for future decisions.

## No authorized next stage rule

No next implementation stage is authorized until a maintainer explicitly chooses one.

No future stage may become `NEXT_ELIGIBLE` from inference, candidate listing, research parking-lot content, previous planning context, test validation, or local implementation convenience.

## Candidate stage representation

Candidate directions may be listed only as `CANDIDATE_ONLY`.

Each candidate must include source evidence, required human authorization, and an explicit block against implementation without authorization.

Candidate listing does not authorize implementation.

## Required human authorization

A future stage becomes eligible only after an explicit maintainer decision names the next stage and its approved scope.

That decision must be followed by the normal factory checkpoints: story approval, technical-spec approval, scoped implementation, tests, validation, and separate staging/commit approval.

## Blocked automatic promotions

The following promotions are blocked:

- `research_parking_lot_to_runtime`
- `candidate_to_next_eligible`
- `conversation_context_to_canon`
- `validation_pass_to_commit_authority`

Research evidence, candidate options, conversation context, and validation output are not roadmap authority by themselves.

## Research parking-lot boundary

Research parking lots remain non-runtime.

Agent-Reach, VoxCPM, VoxCPM2, and any future research parking-lot item must not become a product feature, runtime dependency, connector, retrieval path, memory path, model-router path, user-facing command, or implementation stage unless a maintainer explicitly authorizes that future stage.

## Commit authority boundary

Validation pass does not imply commit authority.

Story approval does not imply staging authority.
Technical-spec approval does not imply staging authority.
Implementation approval does not imply commit authority.
Commit requires separate explicit maintainer approval.

## Allowed outputs

- A local roadmap governance document.
- A local `RoadmapContinuationPacket` schema.
- Candidate next-stage examples labeled `CANDIDATE_ONLY`.
- Mechanical canonical-roadmap updates marking 77P complete.
- Tests enforcing that no unauthorized next stage exists after 77P.

## Forbidden outputs

- No runtime code changes.
- No app behavior changes.
- No new product capability.
- No dependency changes.
- No connector config.
- No retrieval config.
- No memory writes.
- No `ProposedMemory` writes.
- No model-router changes.
- No Telegram changes.
- No API changes.
- No background jobs.
- No MCP/tool config.
- No external network behavior.
- No automatic 78P.
- No staging authority.
- No commit authority.

## RoadmapContinuationPacket schema

```json
{
  "packet_type": "RoadmapContinuationPacket",
  "stage": "77P",
  "status": "NON_RUNTIME_GOVERNANCE_PACKET",
  "current_terminal_stage": "76P",
  "current_terminal_commit": "3a03d6c",
  "next_stage_authorized": false,
  "authorized_next_stage": null,
  "candidate_directions": [
    {
      "candidate_id": "string",
      "title": "string",
      "source_evidence": ["path"],
      "candidate_status": "CANDIDATE_ONLY",
      "requires_human_authorization": true,
      "forbidden_to_implement_without_authorization": true
    }
  ],
  "blocked_promotions": [
    "research_parking_lot_to_runtime",
    "candidate_to_next_eligible",
    "conversation_context_to_canon",
    "validation_pass_to_commit_authority"
  ],
  "required_human_decision": "choose_next_stage_or_stop",
  "commit_authority": false
}
```

This schema is documentation-only in 77P. It does not add runtime models.

## Candidate next-stage examples

| Candidate | Status | Notes |
| --- | --- | --- |
| 78P - Next Roadmap Block Selected by Maintainer | CANDIDATE_ONLY | Placeholder until human decision |
| Voice Provider Boundary Spec | CANDIDATE_ONLY | Could follow VoxCPM research, but not authorized |
| External Reach Adapter Boundary Spec | CANDIDATE_ONLY | Could follow Agent-Reach research, but not authorized |
| Research Parking Lot Index | CANDIDATE_ONLY | Could consolidate research docs |
| Factory Methodology Guard Hardening | CANDIDATE_ONLY | Could strengthen commit/staging enforcement |
| Artifacts Hygiene Policy | CANDIDATE_ONLY | Could handle recurring untracked artifacts/residue |
| Caregiver Safety Runtime Expansion | CANDIDATE_ONLY | Requires explicit caregiver/product decision |
| Roboticxs Launch MVP Consolidation | CANDIDATE_ONLY | Requires roadmap decision |

Listing candidates does not authorize them.

## How a future stage becomes NEXT_ELIGIBLE

A future stage becomes `NEXT_ELIGIBLE` only when a maintainer explicitly selects it and the canonical roadmap is updated to record that selection.

External repositories, research parking lots, validation passes, local tests, previous conversation context, and inferred product priorities cannot independently change roadmap sequence.

## Non-claims

- 77P does not implement a Roboticxs product feature.
- 77P does not authorize the next implementation stage automatically.
- 77P does not authorize Agent-Reach.
- 77P does not authorize VoxCPM or VoxCPM2.
- 77P does not authorize voice.
- 77P does not authorize external reach.
- 77P does not authorize connectors.
- 77P does not authorize retrieval.
- 77P does not authorize memory behavior.
- 77P does not authorize user-facing commands.
- 77P does not authorize staging.
- 77P does not authorize commit.
- 77P does not create 78P as `NEXT_ELIGIBLE`.
