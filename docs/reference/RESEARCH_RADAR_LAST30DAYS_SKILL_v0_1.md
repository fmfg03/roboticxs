# Research Radar / Last30Days Skill v0.1

## Purpose

Stage 72P defines a local Research Radar packet layer inspired by Last30Days-style recent research workflows. It helps Roboticxs prepare a request-scoped research plan for what changed recently around a topic.

72P is a local packet builder only. It does not run live search, scrape platforms, activate connectors, call external APIs, run browser automation, schedule alerts, monitor topics in the background, store raw content, write memory, publish, send alerts, or create CRM/lead-gen handoffs.

Correct claim:

```text
Roboticxs can prepare a recent-research packet that defines what to look for, where to look, what evidence is required, and what boundaries apply.
```

Forbidden claim:

```text
Roboticxs continuously monitors the web and social platforms for you.
```

Core rule:

```text
A research packet is a scoped request, not a background crawler.
```

## 72P policy

```json research-radar-policy
{
  "stage_id":"72P",
  "local_packet_builder_authorized":true,
  "live_access_authorized":false,
  "scraping_authorized":false,
  "background_monitoring_authorized":false,
  "external_api_authorized":false,
  "browser_automation_authorized":false,
  "connector_authorized":false,
  "scheduled_alerts_authorized":false,
  "memory_write_authorized":false,
  "raw_content_storage_authorized":false,
  "external_action_authorized":false
}
```

## Source repo register

The Last30Days skill is recorded as inspiration and architecture reference only. It is not a dependency, vendored code source, live scraping authority, external API authority, or integration target in 72P.

```json research-radar-source-repo-register
[
  {
    "source_id":"last30days_skill_source_repo",
    "repo":"https://github.com/mvanhorn/last30days-skill",
    "owner":"mvanhorn",
    "role":"inspiration / architecture reference only",
    "allowed_use_in_72P":"research_reference_only",
    "dependency_authorized":false,
    "code_vendor_authorized":false,
    "live_scraping_authorized":false,
    "external_api_authorized":false,
    "reason":"72P defines Roboticxs' bounded research-radar packet contract before any live research or skill integration."
  }
]
```

## Packet contract

```json research-radar-packet-contract
{
  "packet_name":"ResearchRadarPacket",
  "required_fields":[
    "packet_id",
    "packet_type",
    "research_decision",
    "topic",
    "freshness_window",
    "source_categories",
    "source_quality_requirements",
    "source_risk_labels",
    "budget_class",
    "requires_budget_confirmation",
    "requires_user_confirmation",
    "live_access_authorized",
    "scraping_authorized",
    "background_monitoring_authorized",
    "external_action_authorized",
    "connector_authorized",
    "memory_write_authorized",
    "raw_content_storage_authorized",
    "summary_claim_level",
    "uncertainty_required",
    "recommended_output_shape",
    "downstream_decision",
    "blocked_reason",
    "future_stage_required",
    "created_at"
  ],
  "required_invariants":{
    "live_access_authorized":false,
    "scraping_authorized":false,
    "background_monitoring_authorized":false,
    "external_action_authorized":false,
    "connector_authorized":false,
    "memory_write_authorized":false,
    "raw_content_storage_authorized":false
  }
}
```

## Freshness windows

```json research-radar-freshness-window-policy
[
  {"freshness_window":"LAST_7_DAYS","allowed_in_72P":true,"requires_user_confirmation":false,"notes":"Useful for fast-moving trends."},
  {"freshness_window":"LAST_14_DAYS","allowed_in_72P":true,"requires_user_confirmation":false,"notes":"Useful for short trend checks."},
  {"freshness_window":"LAST_30_DAYS","allowed_in_72P":true,"requires_user_confirmation":false,"notes":"Default for recent-research requests."},
  {"freshness_window":"LAST_60_DAYS","allowed_in_72P":true,"requires_user_confirmation":false,"notes":"Broader packet; still no live access."},
  {"freshness_window":"CUSTOM_RANGE_REQUIRES_CONFIRMATION","allowed_in_72P":true,"requires_user_confirmation":true,"notes":"Custom ranges require confirmation and may belong to another research mode."}
]
```

## Source category registry

`allowed_in_72P` means allowed in a research plan, not live accessed.

```json research-radar-source-category-registry
[
  {"source_category":"WEB_SEARCH_RESULTS","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"UNKNOWN","source_risk_default":"MEDIUM","notes":"Planning category only; no live web search is authorized in 72P."},
  {"source_category":"OFFICIAL_SOURCE","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"OFFICIAL","source_risk_default":"LOW","notes":"Official sources are higher-quality planning targets, not live-access authority."},
  {"source_category":"GITHUB_REPOSITORY","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"HIGH_SIGNAL","source_risk_default":"MEDIUM","notes":"Repository signals require later live-access authorization before inspection."},
  {"source_category":"REDDIT_PUBLIC_DISCUSSION","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":true,"source_quality_default":"SOCIAL_SIGNAL","source_risk_default":"NOISY","notes":"Social discussion is signal, not fact."},
  {"source_category":"X_PUBLIC_DISCUSSION","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":true,"source_quality_default":"SOCIAL_SIGNAL","source_risk_default":"NOISY","notes":"X discussion is noisy public signal, not proof."},
  {"source_category":"YOUTUBE_PUBLIC_CONTENT","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":true,"source_quality_default":"SOCIAL_SIGNAL","source_risk_default":"NOISY","notes":"Video/community signal requires later explicit access authority."},
  {"source_category":"HACKER_NEWS_DISCUSSION","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":true,"source_quality_default":"SOCIAL_SIGNAL","source_risk_default":"NOISY","notes":"Discussion signal is not source-of-truth evidence."},
  {"source_category":"POLYMARKET_PUBLIC_MARKET","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":true,"source_quality_default":"SOCIAL_SIGNAL","source_risk_default":"POTENTIALLY_MANIPULATED","notes":"Market odds are not truth and may be manipulated."},
  {"source_category":"NEWS_ARTICLE","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"HIGH_SIGNAL","source_risk_default":"MEDIUM","notes":"News articles require source comparison and publication-date checks."},
  {"source_category":"BLOG_POST","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"LOW_SIGNAL","source_risk_default":"UNVERIFIED","notes":"Blog posts are not primary by default."},
  {"source_category":"PAPER_OR_PREPRINT","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"PRIMARY","source_risk_default":"MEDIUM","notes":"Papers/preprints still require recency and venue/context review."},
  {"source_category":"COMPANY_DOCS","allowed_in_72P":true,"requires_live_access":true,"requires_user_confirmation":false,"source_quality_default":"OFFICIAL","source_risk_default":"MEDIUM","notes":"Company docs are official for company claims only."},
  {"source_category":"USER_PROVIDED_SOURCES","allowed_in_72P":true,"requires_live_access":false,"requires_user_confirmation":false,"source_quality_default":"HIGH_SIGNAL","source_risk_default":"MEDIUM","notes":"User-provided sources must be labeled as user-provided."}
]
```

## Decisions

```json research-radar-decision-registry
[
  {"decision_id":"BLOCK_EXTERNAL_ACTION","precedence":1,"allowed_effect":"local_block_notice_only","forbidden_effect":["external_send","publishing","alerts","third_party_contact"],"requires_human_review":true},
  {"decision_id":"BLOCK_BACKGROUND_MONITORING","precedence":2,"allowed_effect":"local_block_notice_only","forbidden_effect":["watchlists","scheduled_monitoring","push_alerts"],"requires_human_review":true},
  {"decision_id":"BLOCK_UNAPPROVED_SCRAPING","precedence":3,"allowed_effect":"local_block_notice_only","forbidden_effect":["scraping","raw_content_collection","platform_clients"],"requires_human_review":true},
  {"decision_id":"REQUIRE_BUDGET_CONFIRMATION","precedence":4,"allowed_effect":"budget_confirmation_prompt_only","forbidden_effect":["unbounded_model_loop","background_research"],"requires_human_review":true},
  {"decision_id":"ASK_CLARIFICATION","precedence":5,"allowed_effect":"scope_question_only","forbidden_effect":["live_access","memory_write"],"requires_human_review":false},
  {"decision_id":"PREPARE_CONTENT_BRIEF_PACKET","precedence":6,"allowed_effect":"content_brief_structure_only","forbidden_effect":["live_findings","publishing"],"requires_human_review":true},
  {"decision_id":"PREPARE_RESEARCH_PACKET","precedence":7,"allowed_effect":"research_plan_only","forbidden_effect":["live_findings","scraping"],"requires_human_review":true},
  {"decision_id":"PREPARE_SOURCE_PLAN_ONLY","precedence":8,"allowed_effect":"source_plan_only","forbidden_effect":["live_access"],"requires_human_review":false},
  {"decision_id":"DEFER_TO_FUTURE_CONNECTOR_STAGE","precedence":9,"allowed_effect":"defer_notice_only","forbidden_effect":["connector_activation"],"requires_human_review":true}
]
```

## Budget policy

```json research-radar-budget-class-policy
[
  {"budget_class":"RESEARCH_LIGHT","requires_budget_confirmation":false,"notes":"Simple local source plan."},
  {"budget_class":"RESEARCH_STANDARD","requires_budget_confirmation":false,"notes":"Deeper local packet, still no live access."},
  {"budget_class":"RESEARCH_DEEP","requires_budget_confirmation":true,"notes":"Deep research needs budget confirmation before any future live work."},
  {"budget_class":"RESEARCH_SOCIAL_MULTI_SOURCE","requires_budget_confirmation":true,"notes":"Social multi-source research needs budget confirmation and source-risk warnings."},
  {"budget_class":"RESEARCH_LONG_CONTEXT","requires_budget_confirmation":true,"notes":"Long-context research needs confirmation."},
  {"budget_class":"RESEARCH_BLOCKED_BACKGROUND","requires_budget_confirmation":false,"notes":"Background monitoring is blocked."}
]
```

## Output shape policy

72P output is a plan or structure, not live findings.

Allowed output shapes:

```text
SOURCE_PLAN
RECENT_SIGNAL_SUMMARY
CONTENT_BRIEF
STRATEGY_NOTE
QUESTION_LIST
RESEARCH_PROMPT
NO_ACTION_NOTICE
BLOCKED_NOTICE
```

## Memory and evidence boundary

Research insight is not memory by default. No packet writes memory directly. Any memory candidate requires review. Social content is signal, not fact. Engagement metrics are not truth. Market odds are not truth. Blog posts are not primary unless author/source authority is established. GitHub stars are not quality proof. User-provided sources must be labeled as user-provided.

## Required non-claims

- Roboticxs does not scrape Reddit, X, YouTube, Hacker News, Polymarket, or the web in 72P.
- Roboticxs does not continuously monitor topics in 72P.
- Roboticxs does not call external research APIs in 72P.
- Roboticxs does not run browser automation in 72P.
- Roboticxs does not store raw source content in 72P.
- Roboticxs does not treat social engagement as truth.
- Roboticxs does not write research insights to memory automatically.
- Roboticxs does not send alerts automatically.
- Roboticxs does not activate connectors for Research Radar in 72P.
- Roboticxs does not vendor or depend on `mvanhorn/last30days-skill` in 72P.

## Closeout transition

After 72P closes, 73P Understand-Anything + codegraph Factory Skill becomes the next eligible stage. 72P does not implement 73P behavior.

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_research_radar.py`
- `python3 -m pytest -q tests/test_voice_caregiver_intake.py`
- `python3 -m pytest -q tests/test_voice_notes_intelligence_spike.py`
- `python3 -m pytest -q tests/test_guided_routines.py`
- `python3 -m pytest -q tests/test_caregiver_relay.py`
- `python3 -m pytest -q tests/test_caregiver_mode_boundary.py`
- `python3 -m pytest -q tests/test_memory_stack_architecture.py`
- `python3 -m pytest -q tests/test_conversation_continuity_spine.py`
- `python3 -m pytest -q tests/test_budget_authority_guard.py`
- `python3 -m pytest -q tests/test_canonical_roadmap.py`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q tests/test_retrieval_control_freeze.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git diff --check`
- `git status --short`
