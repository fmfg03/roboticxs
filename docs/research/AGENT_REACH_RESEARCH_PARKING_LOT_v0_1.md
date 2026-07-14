# Agent-Reach Research Parking Lot v0.1

## Status

Stage 75P parks Agent-Reach as `RESEARCH_ONLY`.

This is a local research assessment only. It does not install Agent-Reach, activate Agent-Reach, configure Agent-Reach, or claim Agent-Reach support in Roboticxs.

## Decision

Agent-Reach is parked as RESEARCH_ONLY.
It is not approved as a Roboticxs runtime dependency.
It is not approved as a connector.
It is not approved for live retrieval.
It is not approved for memory ingestion.
It is not approved for automatic source scanning.

## Why this exists

Agent-Reach appears relevant because external reach is a real product gap for agent systems: agents often need to read diverse outside sources without each source requiring a bespoke integration.

Roboticxs can evaluate that idea only under the factory boundary. Having reach does not mean having authority. External source access must be governed before it can become product behavior.

## What Agent-Reach appears to provide

Agent-Reach appears to target external source access and extraction workflows. Candidate surfaces include web pages, social or media sources, transcripts, repository discovery, and source reading for research workflows.

This repository has not installed or executed Agent-Reach. These observations are parking-lot assessment notes, not verified integration claims.

## Potential Roboticxs value

- Web/source reach for research tasks.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- Social/media monitoring.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- YouTube transcript extraction.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- GitHub/repo discovery.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- External source reading for future Research Radar.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- Competitive intelligence.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- Prospect/company research.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review
- Future Agentius/Zaubern research workflows.
  Status: CANDIDATE_ONLY
  Requires: future adapter + authority policy + budget policy + privacy review

## Hard boundaries

- No runtime integration.
- No network calls.
- No connector registration.
- No MCP server registration.
- No scraping capability.
- No credential/cookie handling.
- No memory writes.
- No ProposedMemory writes.
- No retrieval index writes.
- No background monitoring.
- No user-facing commands.
- No automatic roadmap promotion.
- No claims that Roboticxs supports Agent-Reach.

## Blocked for now

- Installing Agent-Reach is blocked.
- Adding Agent-Reach as a dependency is blocked.
- Adding CLI wrappers is blocked.
- Adding MCP configuration is blocked.
- Adding connector configuration is blocked.
- Adding scraping runtime behavior is blocked.
- Adding cookie or credential handling is blocked.
- Adding external search behavior is blocked.
- Adding web, social, or media reading tools is blocked.
- Changing command routing is blocked.
- Changing memory runtime is blocked.
- Changing Context Scan is blocked.
- Changing Proactive Trigger Engine is blocked.
- Creating user-facing Agent-Reach commands is blocked.
- Marking Agent-Reach as an approved integration is blocked.

## Risk register

| Risk | Required treatment |
| --- | --- |
| Terms-of-service risk | Must be reviewed before integration |
| Cookie/credential risk | Blocked until credential boundary exists |
| Privacy risk | Requires user consent and source allowlists |
| Budget risk | Requires cost/usage governor |
| Retrieval contamination | Must not write to retrieval automatically |
| Memory contamination | Must not create memories automatically |
| Source reliability | Must label source confidence |
| Scraping fragility | Must be treated as unstable |
| Platform blocking | Must be expected |
| Compliance ambiguity | Requires review per platform/source |
| Runtime blast radius | Must be adapter-isolated |
| User misunderstanding | UX must say "research source access," not "truth" |

## Authority implications

Any future Agent-Reach-style capability must separate:

```text
READ_SOURCE
SEARCH_SOURCE
EXTRACT_SOURCE
SUMMARIZE_SOURCE
PROPOSE_MEMORY
PROPOSE_ACTION
WRITE_EXTERNAL
PUBLISH_EXTERNAL
```

Only `READ_SOURCE`, `SEARCH_SOURCE`, `EXTRACT_SOURCE`, and `SUMMARIZE_SOURCE` are candidates for future evaluation.

`PROPOSE_MEMORY`, `PROPOSE_ACTION`, `WRITE_EXTERNAL`, and `PUBLISH_EXTERNAL` remain blocked unless future stages define explicit authority policy.

## Privacy implications

Future external reach would need explicit user consent, source allowlists, sensitive-source exclusions, credential boundaries, cookie boundaries, raw-source retention limits, and clear user-visible disclosure when outside sources are accessed.

75P enables none of that behavior.

## Budget implications

Future external reach would need budget limits for request count, source count, token use, paid API use, retries, transcript extraction, crawling depth, and background operations.

75P adds no budget-consuming runtime path.

## Connector implications

Agent-Reach is not approved as a connector.

Any future connector-like adapter would need registration policy, source allowlists, authority scopes, audit logs, consent checks, disable controls, and review before activation.

## Memory implications

Agent-Reach is not approved for memory ingestion.

Future source findings must not create `MemoryItem` records, `ProposedMemory` records, or durable user facts automatically. Any memory proposal path would require a later approved stage and explicit user review.

## Retrieval implications

No live retrieval is enabled.

Future source reading must not write to retrieval indexes automatically, contaminate local retrieval with unreviewed source text, or treat extracted text as canonical truth.

## Future adapter requirements

A future controlled adapter would require:

- explicit story and technical spec approval;
- authority policy for each source operation;
- user consent gates;
- source allowlists and blocklists;
- privacy review;
- budget and rate limits;
- credential and cookie exclusion or a separate approved credential boundary;
- source confidence labels;
- source traceability and audit logs;
- adapter isolation from runtime command routing;
- no memory or retrieval writes without separate approval;
- confirmation before sensitive actions;
- tests that prove blocked operations remain blocked.

## Open questions

- Which source classes would be allowed first, if any?
- Which platforms prohibit the intended access pattern?
- How should source confidence be represented in future research packets?
- What consent UX is required before source access?
- What budget governor is sufficient for multi-source research?
- How should cookies, credentials, and authenticated content remain excluded?
- What retention policy should apply to extracted source text?
- Which future stage would own adapter isolation?

## Recommended next stage

Stage 76P, VoxCPM Research Parking Lot, is the next eligible stage after 75P closes.

Any future Agent-Reach adapter would require a separate stage after explicit story approval, technical-spec approval, authority policy, privacy review, budget policy, tests, and validation.

## Non-claims

- Roboticxs does not support Agent-Reach in runtime.
- Roboticxs does not ship Agent-Reach as a dependency.
- Roboticxs does not expose Agent-Reach as a connector.
- Roboticxs does not perform Agent-Reach live retrieval.
- Roboticxs does not perform Agent-Reach memory ingestion.
- Roboticxs does not perform automatic source scanning through Agent-Reach.
- Roboticxs does not add scraping, cookies, credentials, external search, or network behavior in 75P.
- Roboticxs does not create user-facing Agent-Reach commands in 75P.
- Roboticxs does not canonize Agent-Reach findings automatically.
