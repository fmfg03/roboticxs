# Repo Understanding Factory Skill v0.1

## Purpose

Stage 73P defines a local Repo Understanding Packet layer inspired by Understand Anything and codegraph. It helps Codex Factory prepare review-only maps for local repositories before deeper implementation work.

73P is a local packet builder only. It does not clone repositories, install dependencies, execute code, start MCP servers, run tree-sitter, create SQLite indexes, activate external tools, call network APIs, archive raw source, certify security, or prove correctness.

Correct claim:

```text
Roboticxs Factory can prepare a repo-understanding packet that maps structure, likely responsibilities, risks, and next inspection questions.
```

Forbidden claim:

```text
Roboticxs Factory fully understands, verifies, secures, or certifies the codebase.
```

Core rule:

```text
A code graph is an aid to inspection, not authority over correctness.
```

## 73P policy

```json repo-understanding-policy
{
  "stage_id":"73P",
  "local_packet_builder_authorized":true,
  "local_files_only":true,
  "code_execution_authorized":false,
  "dependency_install_authorized":false,
  "repo_clone_authorized":false,
  "mcp_server_authorized":false,
  "external_tool_authorized":false,
  "network_access_authorized":false,
  "persistent_index_authorized":false,
  "security_certification_authorized":false,
  "correctness_claim_authorized":false,
  "raw_source_archive_authorized":false
}
```

## Source repo register

Understand Anything and codegraph are architecture references only. They are not dependencies, vendored code sources, install targets, runtime integrations, MCP authorities, indexer authorities, or external tool activations in 73P.

```json repo-understanding-source-register
[
  {
    "source_id":"understand_anything_source_repo",
    "repo_name":"Understand Anything",
    "repo_url":"https://github.com/Lum1104/Understand-Anything",
    "project_site":"https://understand-anything.com/",
    "project_origin":"Egonex / Understand Anything",
    "role":"architecture_reference_only",
    "allowed_use_in_73P":"research_reference_only",
    "dependency_authorized":false,
    "code_vendor_authorized":false,
    "repo_clone_authorized":false,
    "plugin_install_authorized":false,
    "dashboard_runtime_authorized":false,
    "multi_agent_runtime_authorized":false,
    "external_api_authorized":false,
    "external_runtime_authorized":false,
    "mcp_server_authorized":false,
    "persistent_index_authorized":false,
    "network_access_authorized":false,
    "notes":"Architecture reference only; no install, vendoring, clone, dashboard, or multi-agent runtime."
  },
  {
    "source_id":"codegraph_source_repo",
    "repo_name":"codegraph",
    "repo_url":"https://github.com/colbymchenry/codegraph",
    "role":"architecture_reference_only",
    "allowed_use_in_73P":"research_reference_only",
    "dependency_authorized":false,
    "code_vendor_authorized":false,
    "repo_clone_authorized":false,
    "mcp_server_authorized":false,
    "tree_sitter_runtime_authorized":false,
    "sqlite_index_authorized":false,
    "external_api_authorized":false,
    "external_runtime_authorized":false,
    "persistent_index_authorized":false,
    "network_access_authorized":false,
    "notes":"Architecture reference only; no MCP, tree-sitter runtime, SQLite index, or external tooling."
  }
]
```

## Packet contract

```json repo-understanding-packet-contract
{
  "packet_name":"RepoUnderstandingPacket",
  "required_fields":[
    "packet_id",
    "packet_type",
    "repo_decision",
    "repo_scope",
    "requested_focus",
    "file_categories",
    "source_repo_references",
    "budget_class",
    "requires_budget_confirmation",
    "requires_user_confirmation",
    "local_files_only",
    "code_execution_authorized",
    "dependency_install_authorized",
    "repo_clone_authorized",
    "mcp_server_authorized",
    "external_tool_authorized",
    "network_access_authorized",
    "persistent_index_authorized",
    "security_certification_authorized",
    "correctness_claim_authorized",
    "raw_source_archive_authorized",
    "recommended_output_shape",
    "summary_claim_level",
    "uncertainty_required",
    "next_questions",
    "blocked_reason",
    "future_stage_required",
    "created_at"
  ],
  "required_invariants":{
    "local_files_only":true,
    "code_execution_authorized":false,
    "dependency_install_authorized":false,
    "repo_clone_authorized":false,
    "mcp_server_authorized":false,
    "external_tool_authorized":false,
    "network_access_authorized":false,
    "persistent_index_authorized":false,
    "security_certification_authorized":false,
    "correctness_claim_authorized":false,
    "raw_source_archive_authorized":false
  }
}
```

## File category taxonomy

Category assignment is heuristic in 73P. Secret-like paths are flagged and must not be summarized deeply by default. Lockfiles, generated/vendor files, config, schema, migration, script, CI, and dependency manifests are map targets, not execution authority.

```json repo-understanding-file-category-registry
[
  {"file_category":"APP_CODE","allowed_in_73P":true,"deep_summary_by_default":true,"risk_label":"MEDIUM"},
  {"file_category":"TEST_CODE","allowed_in_73P":true,"deep_summary_by_default":true,"risk_label":"MEDIUM"},
  {"file_category":"CONFIG","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"DOCS","allowed_in_73P":true,"deep_summary_by_default":true,"risk_label":"LOW"},
  {"file_category":"SCRIPT","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"MIGRATION","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"SCHEMA","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"LOCKFILE","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"LOW"},
  {"file_category":"DEPENDENCY_MANIFEST","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"CI_PIPELINE","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"AGENT_INSTRUCTION","allowed_in_73P":true,"deep_summary_by_default":true,"risk_label":"HIGH"},
  {"file_category":"SECRET_OR_CREDENTIAL_LIKE","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"HIGH"},
  {"file_category":"GENERATED_OR_VENDOR","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"LOW"},
  {"file_category":"UNKNOWN","allowed_in_73P":true,"deep_summary_by_default":false,"risk_label":"UNKNOWN"}
]
```

## Decisions

```json repo-understanding-decision-registry
[
  {"decision_id":"BLOCK_CODE_EXECUTION","precedence":1,"allowed_effect":"local_block_notice_only","forbidden_effect":["code_execution","test_execution","safety_certification","correctness_proof"],"requires_human_review":true},
  {"decision_id":"BLOCK_DEPENDENCY_INSTALL","precedence":2,"allowed_effect":"local_block_notice_only","forbidden_effect":["package_install","tool_install","vendoring"],"requires_human_review":true},
  {"decision_id":"BLOCK_REPO_CLONE","precedence":3,"allowed_effect":"local_block_notice_only","forbidden_effect":["repo_clone","hidden_source_acquisition"],"requires_human_review":true},
  {"decision_id":"BLOCK_EXTERNAL_TOOL","precedence":4,"allowed_effect":"local_block_notice_only","forbidden_effect":["mcp_server","external_tool","network_access"],"requires_human_review":true},
  {"decision_id":"REQUIRE_BUDGET_CONFIRMATION","precedence":5,"allowed_effect":"budget_confirmation_prompt_only","forbidden_effect":["unbounded_context_expansion","background_indexing"],"requires_human_review":true},
  {"decision_id":"ASK_CLARIFICATION","precedence":6,"allowed_effect":"scope_question_only","forbidden_effect":["execution","indexing"],"requires_human_review":false},
  {"decision_id":"PREPARE_SYMBOL_MAP_PLAN","precedence":7,"allowed_effect":"symbol_plan_only","forbidden_effect":["parser_runtime","persistent_index"],"requires_human_review":false},
  {"decision_id":"PREPARE_DEPENDENCY_MAP_PLAN","precedence":8,"allowed_effect":"dependency_plan_only","forbidden_effect":["dependency_install","vulnerability_certification"],"requires_human_review":false},
  {"decision_id":"PREPARE_TEST_MAP_PACKET","precedence":9,"allowed_effect":"test_map_only","forbidden_effect":["test_execution"],"requires_human_review":false},
  {"decision_id":"PREPARE_RISK_MAP_PACKET","precedence":10,"allowed_effect":"risk_map_only","forbidden_effect":["security_certification"],"requires_human_review":false},
  {"decision_id":"PREPARE_FILE_SCOPE_PACKET","precedence":11,"allowed_effect":"file_scope_plan_only","forbidden_effect":["deep_parser_runtime"],"requires_human_review":false},
  {"decision_id":"PREPARE_REPO_UNDERSTANDING_PACKET","precedence":12,"allowed_effect":"repo_map_only","forbidden_effect":["full_understanding_claim"],"requires_human_review":false},
  {"decision_id":"DEFER_TO_FUTURE_INDEXER_STAGE","precedence":13,"allowed_effect":"future_stage_handoff_only","forbidden_effect":["persistent_index"],"requires_human_review":true}
]
```

## Budget policy

```json repo-understanding-budget-class-policy
[
  {"budget_class":"REPO_UNDERSTANDING_LIGHT","requires_budget_confirmation":false,"notes":"Simple local repo map."},
  {"budget_class":"REPO_UNDERSTANDING_STANDARD","requires_budget_confirmation":false,"notes":"Focused local map or plan."},
  {"budget_class":"REPO_UNDERSTANDING_LARGE","requires_budget_confirmation":true,"notes":"Large repo analysis needs explicit budget confirmation."},
  {"budget_class":"REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED","requires_budget_confirmation":true,"notes":"Multi-agent repo analysis is deferred and requires approval."},
  {"budget_class":"REPO_INDEXER_DEFERRED","requires_budget_confirmation":true,"notes":"Persistent graph/indexer behavior is deferred to a future stage."}
]
```

## Output shape policy

73P output is a map, plan, handoff, question list, or blocked notice. It is not a generated graph index.

Allowed output shapes:

```text
REPO_MAP
FILE_SCOPE_PLAN
SYMBOL_MAP_PLAN_OUTPUT
DEPENDENCY_MAP_PLAN_OUTPUT
TEST_MAP
DOCS_MAP
RISK_MAP
FACTORY_HANDOFF
QUESTION_LIST
BLOCKED_NOTICE
```

## Required non-claims

- Roboticxs Factory does not execute code in 73P.
- Roboticxs Factory does not install dependencies in 73P.
- Roboticxs Factory does not clone repositories in 73P.
- Roboticxs Factory does not start an MCP server in 73P.
- Roboticxs Factory does not vendor Understand Anything or codegraph in 73P.
- Roboticxs Factory does not create a persistent repo index in 73P.
- Roboticxs Factory does not certify security or correctness in 73P.
- Roboticxs Factory does not claim full codebase understanding in 73P.
- Roboticxs Factory does not run tree-sitter in 73P.
- Roboticxs Factory does not create a SQLite index in 73P.
- Roboticxs Factory does not launch a dashboard in 73P.
- Roboticxs Factory does not run a multi-agent repo pipeline in 73P.
- Roboticxs Factory does not use network access in 73P.
- Roboticxs Factory does not archive raw source in 73P.

## Closeout transition

After 73P closes, 74P ECC Knowledge Compiler Factory Skill becomes the next eligible stage. 73P does not implement 74P behavior.

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_repo_understanding.py`
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
