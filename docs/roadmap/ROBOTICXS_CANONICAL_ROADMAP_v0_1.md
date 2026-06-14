# Roboticxs Canonical Roadmap v0.1

## Purpose

This document materializes the maintainer-approved forward-looking roadmap for Roboticxs.

It is the controlling roadmap for future stage sequencing after Stage 94P implementation. It does not authorize implementation, replace runtime truth, or claim that future sequence entries are implemented locally.

## Source of authority

The forward sequence comes from explicit maintainer direction in the maintainer-approved ChatGPT/web planning thread. Local repository evidence is authoritative only for stages confirmed in the repository.

```json canonical-roadmap-authority
{
  "authority_source":"maintainer_approved_chatgpt_web_planning_thread",
  "local_evidence_scope":"stages_61P_through_94P",
  "forward_sequence_source":"explicit_maintainer_direction",
  "runtime_truth_source":"local_repo",
  "roadmap_inclusion_authorizes_implementation":false
}
```

## Local evidence baseline

The repository confirms these fixed baselines:

- 61P consolidated explicit command routing without adding product behavior.
- 62P created the canonical runtime surface audit.
- 63P froze retrieval-control as local metadata/control-only behavior.
- 64P materialized the canonical roadmap.
- 65P added the Budget Awareness / Cost Authority Guard v0.
- 66P adds the Conversation Continuity Spine v0 as a pure local continuity contract.
- 66P2 defines the Memory Stack Architecture / Criterio Store Spec.
- 67P defines the Caregiver Mode Boundary Spec without runtime caregiver behavior.
- 68P adds the Caregiver Telegram Group Relay v0 as local packet preparation only.
- 69P adds Guided Routine Packets v0 as local routine packet preparation only.
- 70P defines the Voice Notes Intelligence / VibeVoice Spike v0 boundary without voice runtime.
- 71P adds Voice Intake for Caregiver Routines v0 as local transcript-stub processing only.
- 72P adds Research Radar / Last30Days Skill v0 as local request-scoped research packet preparation only.
- 73P adds Understand-Anything + codegraph Factory Skill v0 as local repo-understanding packet preparation only.
- 74P adds ECC Knowledge Compiler Factory Skill v0 as local non-authoritative knowledge compilation packet preparation only.
- 75P parks Agent-Reach as a research-only external reach capability assessment without runtime integration.
- 76P parks VoxCPM and VoxCPM2 as research-only voice-model candidates without runtime integration.
- 77P adds a roadmap continuation authorization gate without selecting the next implementation stage.
- 78P adds the Hermes Runtime Foundation Bootstrap v0 as a minimal local Hermes-compatible runtime foundation with upstream tracking.
- 79P adds the Telegram Bot Runtime Bootstrap v0 as a minimal Telegram text channel foundation that adapts into the Hermes runtime foundation.
- 80P adds the Telegram Conversation Loop v0 as a minimal deterministic local Telegram text conversation loop.
- 81P adds the Telegram Runtime Smoke / Manual Bot Wiring v0 as a safe manual readiness and wiring path.
- 82P adds the Memory Proposal Loop over Telegram v0 as explicit user-approved memory proposal handling.
- 83P adds Active Memory Recall over Telegram v0 as deterministic visibility into approved active memories.
- 84P adds Active Memory Forget over Telegram v0 as deterministic active-memory deactivation by ID over Telegram.
- 85P adds the Hermes Profile / Roboticxs SOUL Rebase v0 as a profile identity and runtime-instruction boundary.
- 86P adds the Hermes Real Settings Baseline v0 as a verified config/reference contract for real Hermes settings and fake-setting rejection.
- 87P adds the Hermes + Agent Skills + Cron Integration Baseline v0 as a documentation/spec/test bridge from Hermes runtime capabilities, Agent Skills packaging, and Hermes cron scheduling to Roboticxs authority layers.
- 88P adds the Routine Wake Gate / Zero-Token Preflight v0 as a documentation/spec/test contract for recurring routine preflight, zero-token no-change skips, no-agent/script-only routines, bounded agent wake context, budget policy, and script-only examples.
- 89P adds Roboticxs Automation Blueprints v0 as documentation/spec/test installable routine templates with portable Agent Skills packaging and explicit authority boundaries.
- 90P adds Roboticxs Command Surface Policy v0 as documentation/spec/test command surface governance for consumer-safe aliases, raw Hermes command blocking, Action Packet approval requirements, and operator-only command boundaries.
- 91P adds Skill Activation Scope Guard v0 as documentation/spec/test governance for active skill scope decisions, redirects, upgrade offers, safe refusals, and prohibited-action blocking.
- 92P adds Hermes Tool Authority Guard v0 as documentation/spec/test governance for action classification, tool authority decisions, Action Packet requirements, and sensitive-action blocking after skill activation and before execution.
- 93P adds Roboticxs Memory Center Bridge v0 as documentation/spec/test governance for projecting approved canonical Roboticxs memory into Hermes runtime context without treating Hermes memory as canonical product memory.
- 94P adds Telegram MVP on Hermes Gateway v0 as documentation/spec/test governance for using Hermes Gateway capability behind the Roboticxs Telegram command surface, scope guard, tool authority guard, memory projection boundary, routine policy, and Action Packet confirmation model.

No local implementation evidence is claimed for any stage after 94P. Stage 89P - Roboticxs Automation Blueprints v0 - is closed committed. Stage 90P - Roboticxs Command Surface Policy v0 - is closed committed. Stage 91P - Skill Activation Scope Guard v0 - is closed committed. Stage 92P - Hermes Tool Authority Guard v0 - is closed committed. Stage 93P - Roboticxs Memory Center Bridge v0 - is closed committed. Stage 94P - Telegram MVP on Hermes Gateway v0 - is implemented pending review as story/spec/test work only. Stage 95P and later are not authorized.

## Canonical stage registry

```json canonical-stage-registry
[
  {"stage_id":"61P","stage_name":"Command Routing Consolidation v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"c079a96","paths":["docs/reference/COMMAND_ROUTING_CONSOLIDATION_v0_1.md"]},"implementation_authorized":false,"next_action":"Do not reopen except through a separately approved bug or boundary-correction stage."},
  {"stage_id":"62P","stage_name":"Runtime Surface Audit v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"93bcbff","paths":["docs/reference/RUNTIME_SURFACE_AUDIT_v0_1.md"]},"implementation_authorized":false,"next_action":"Use as the source of truth for the audited runtime surface."},
  {"stage_id":"63P","stage_name":"Retrieval Control Freeze v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"86afd53","paths":["docs/reference/RETRIEVAL_CONTROL_FREEZE_v0_1.md"]},"implementation_authorized":false,"next_action":"Keep retrieval-control frozen unless a separately approved stage reopens it."},
  {"stage_id":"64P","stage_name":"Roadmap Canon Materialization v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"2b3c295","paths":["docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Do not reopen except through a separately approved roadmap-canon correction."},
  {"stage_id":"65P","stage_name":"Budget Awareness / Cost Authority Guard v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"d346939","paths":["app/budget_authority.py","docs/reference/BUDGET_AUTHORITY_GUARD_v0_1.md","tests/test_budget_authority_guard.py"]},"implementation_authorized":false,"next_action":"Use as the source of truth for budget authority gating."},
  {"stage_id":"66P","stage_name":"Conversación Horizontal / Continuity Spine v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_66P_closeout","paths":["app/conversation_continuity.py","docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md","tests/test_conversation_continuity_spine.py"]},"implementation_authorized":false,"next_action":"Use as the local continuity-spine baseline and do not reopen except through a separately approved correction stage."},
  {"stage_id":"66P2","stage_name":"Memory Stack Architecture / Criterio Store Spec","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_66P2_closeout","paths":["docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md","tests/test_memory_stack_architecture.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the memory architecture boundary for continuity and criterio; no storage implementation is authorized."},
  {"stage_id":"67P","stage_name":"Caregiver Mode Boundary Spec","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_67P_closeout","paths":["docs/reference/CAREGIVER_MODE_BOUNDARY_SPEC_v0_1.md","tests/test_caregiver_mode_boundary.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the caregiver boundary baseline; no caregiver runtime, relay, routine packet, medication, monitoring, or external action is authorized."},
  {"stage_id":"68P","stage_name":"Caregiver Telegram Group Relay v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_68P_closeout","paths":["app/caregiver_relay.py","docs/reference/CAREGIVER_TELEGRAM_GROUP_RELAY_v0_1.md","tests/test_caregiver_relay.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local caregiver relay packet baseline; no Telegram sending, group management, routine execution, medication, monitoring, emergency handling, sensitive caregiver memory, or external action is authorized."},
  {"stage_id":"69P","stage_name":"Guided Routine Packets v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_69P_closeout","paths":["app/guided_routines.py","docs/reference/GUIDED_ROUTINE_PACKETS_v0_1.md","tests/test_guided_routines.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local guided routine packet baseline; no scheduler, reminders, Telegram sending, routine execution, medication decision, ingestion verification, monitoring, emergency handling, durable routine memory, voice behavior, or external action is authorized."},
  {"stage_id":"70P","stage_name":"Voice Notes Intelligence / VibeVoice Spike","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_70P_closeout","paths":["docs/reference/VOICE_NOTES_INTELLIGENCE_VIBEVOICE_SPIKE_v0_1.md","tests/test_voice_notes_intelligence_spike.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the voice-note intelligence boundary; no voice runtime, ASR inference, TTS, cloned voice, audio storage, durable transcript storage, background listening, caregiver voice runtime, or external send is authorized."},
  {"stage_id":"71P","stage_name":"Voice Intake for Caregiver Routines","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_71P_closeout","paths":["app/voice_caregiver_intake.py","docs/reference/VOICE_INTAKE_FOR_CAREGIVER_ROUTINES_v0_1.md","tests/test_voice_caregiver_intake.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local transcript-stub caregiver voice intake baseline; no audio processing, ASR, Telegram voice handling, TTS, voice clone, speaker authentication, durable transcript storage, routine execution, medication decision, emergency triage, surveillance, or external send is authorized."},
  {"stage_id":"72P","stage_name":"Research Radar / Last30Days Skill","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_72P_closeout","paths":["app/research_radar.py","docs/reference/RESEARCH_RADAR_LAST30DAYS_SKILL_v0_1.md","tests/test_research_radar.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local request-scoped research packet baseline; no live search, scraping, connector activation, browser automation, external API calls, background monitoring, scheduled alerts, memory writes, raw content storage, external actions, CRM, lead-gen, handoff, or 73P behavior is authorized."},
  {"stage_id":"73P","stage_name":"Understand-Anything + codegraph Factory Skill","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_73P_closeout","paths":["app/repo_understanding.py","docs/reference/REPO_UNDERSTANDING_FACTORY_SKILL_v0_1.md","tests/test_repo_understanding.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local repo-understanding packet baseline; no code execution, dependency install, repo clone, MCP server, external tool activation, network access, persistent index, raw source archive, security certification, correctness claim, or 74P behavior is authorized."},
  {"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_74P_closeout","paths":["app/ecc_knowledge_compiler.py","docs/reference/ECC_KNOWLEDGE_COMPILER_FACTORY_SKILL_v0_1.md","tests/test_ecc_knowledge_compiler.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local ECC knowledge compilation packet baseline; no memory writes, proposed-memory writes, retrieval, connectors, network access, user-facing commands, canon auto-apply, or truth conversion is authorized."},
  {"stage_id":"75P","stage_name":"Agent-Reach Research Parking Lot","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_75P_closeout","paths":["docs/research/AGENT_REACH_RESEARCH_PARKING_LOT_v0_1.md","tests/test_agent_reach_research_parking_lot.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local Agent-Reach research parking-lot baseline; no runtime dependency, connector, live retrieval, memory ingestion, automatic source scanning, scraping, cookies, credentials, MCP config, user-facing command, or product support claim is authorized."},
  {"stage_id":"76P","stage_name":"VoxCPM Research Parking Lot","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_76P_closeout","paths":["docs/research/VOXCPM_RESEARCH_PARKING_LOT_v0_1.md","tests/test_voxcpm_research_parking_lot.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local VoxCPM research parking-lot baseline; no dependency, model download, inference, audio generation, voice cloning, audio storage, Telegram voice handling, connector, MCP config, user-facing command, or product support claim is authorized."},
  {"stage_id":"77P","stage_name":"Roadmap Continuation Authorization Gate v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_77P_closeout","paths":["docs/reference/ROADMAP_CONTINUATION_AUTHORIZATION_GATE_v0_1.md","tests/test_roadmap_continuation_authorization_gate.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local roadmap continuation authorization gate; no next implementation stage, 78P, runtime change, product feature, staging, or commit is authorized without explicit maintainer approval."},
  {"stage_id":"78P","stage_name":"Hermes Runtime Foundation Bootstrap v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_78P_closeout","paths":["app/hermes_runtime.py","docs/reference/HERMES_RUNTIME_FOUNDATION_BOOTSTRAP_v0_1.md","docs/reference/HERMES_UPSTREAM_TRACKING_v0_1.md","tests/test_hermes_runtime_foundation.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local Hermes-compatible runtime foundation baseline; no Telegram, caregiver routines, document intake, connectors, retrieval, memory writes, ProposedMemory writes, scheduler, background jobs, shell execution, Hermes dependency install, upstream install script execution, auto-update, staging, commit, or 79P behavior is authorized."},
  {"stage_id":"79P","stage_name":"Telegram Bot Runtime Bootstrap v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_79P_closeout","paths":["app/telegram_runtime.py","app/config.py","app/main.py","docs/reference/TELEGRAM_BOT_RUNTIME_BOOTSTRAP_v0_1.md","tests/test_telegram_runtime_bootstrap.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local Telegram text-channel runtime bootstrap baseline; no caregiver routines, guided routines, document/PDF intake, file downloads, voice, payments, Telegram group relay, proactive/background messages, memory writes, ProposedMemory writes, retrieval, connectors, scheduler, WhatsApp, production deployment, staging, commit, or 80P behavior is authorized."},
  {"stage_id":"80P","stage_name":"Telegram Conversation Loop v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_80P_closeout","paths":["app/telegram_runtime.py","app/main.py","docs/reference/TELEGRAM_CONVERSATION_LOOP_v0_1.md","tests/test_telegram_conversation_loop.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local deterministic Telegram text conversation loop baseline; no real Telegram API delivery, long-term memory, user profile memory, ProposedMemory creation, caregiver behavior, document/file handling, voice, retrieval, connectors, proactive/background messaging, scheduler, deployment, staging, commit, or 81P behavior is authorized."},
  {"stage_id":"81P","stage_name":"Telegram Runtime Smoke / Manual Bot Wiring v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_81P_closeout","paths":["app/config.py","app/telegram_runtime.py","docs/reference/TELEGRAM_RUNTIME_SMOKE_MANUAL_WIRING_v0_1.md","tests/test_telegram_runtime_smoke.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local manual Telegram runtime smoke baseline; no production deployment, automatic webhook registration, real Telegram API calls in tests, committed secrets, caregiver routines, document/file handling, voice, memory writes, ProposedMemory writes, retrieval, connectors, proactive/background messaging, scheduler, staging, commit, or 82P behavior is authorized."},
  {"stage_id":"82P","stage_name":"Memory Proposal Loop over Telegram v0","status":"COMPLETED_FIXED_BASELINE","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_82P_closeout","paths":["app/telegram_runtime.py","app/main.py","app/memory_service.py","docs/reference/TELEGRAM_MEMORY_PROPOSAL_LOOP_v0_1.md","tests/test_telegram_memory_proposal_loop.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local Telegram memory proposal loop baseline; no automatic memory activation, normal-conversation memory extraction, Context Scan, external source scanning, retrieval, connectors, caregiver routines, document/file handling, voice, proactive/background behavior, scheduler, staging, commit, or 83P behavior is authorized."},
  {"stage_id":"83P","stage_name":"Active Memory Recall over Telegram v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"ef9faeb5ed427e2fe4cc04720a50a0a5eadf4d22","commit_message":"feat: add active memory recall over telegram","paths":["app/telegram_runtime.py","app/memory_control.py","docs/reference/TELEGRAM_ACTIVE_MEMORY_RECALL_v0_1.md","tests/test_telegram_memory_proposal_loop.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local active memory recall over Telegram baseline."},
  {"stage_id":"84P","stage_name":"Active Memory Forget over Telegram v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6","commit_message":"feat: add telegram active memory forget","paths":["app/telegram_runtime.py","docs/reference/TELEGRAM_ACTIVE_MEMORY_FORGET_v0_1.md","tests/test_telegram_memory_proposal_loop.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local active memory forget over Telegram baseline."},
  {"stage_id":"85P","stage_name":"Hermes Profile / Roboticxs SOUL Rebase v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"95e23e5438812328f804ba026095237d17f1bf72","commit_message":"docs: add hermes roboticxs soul rebase","paths":["runtime/hermes/SOUL.md","runtime/hermes/AGENTS.md","docs/reference/85P_HERMES_PROFILE_ROBOTICXS_SOUL_REBASE_SPEC_v0_1.md","docs/reference/ROBOTICXS_HERMES_SOUL_v0_1.md","docs/reference/ROBOTICXS_HERMES_PROFILE_REBASE_v0_1.md","tests/test_hermes_soul_contract.py","tests/test_hermes_profile_boundary.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the local Hermes profile and Roboticxs SOUL rebase baseline. 86P is closed committed; do not infer 87P implementation, 88P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"86P","stage_name":"Hermes Real Settings Baseline v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"efb4f5f","commit_message":"docs: add hermes real settings baseline","paths":["docs/research/HERMES_REAL_SETTINGS_BASELINE_v0_1.md","docs/reference/ROBOTICXS_HERMES_CONFIG_CONTRACT_v0_1.md","tests/test_hermes_real_settings_baseline.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the verified Hermes real-settings baseline and config contract. 87P is closed committed; do not infer 88P implementation, 89P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"87P","stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"213a7772aef3a55e03f2284044aba458c752c54e","commit_message":"docs: add hermes agent skills cron baseline","paths":["docs/reference/ROBOTICXS_SKILL_MANIFEST_TO_AGENT_SKILLS_BRIDGE_v0_1.md","docs/reference/ROBOTICXS_HERMES_CRON_ROUTINE_MAPPING_v0_1.md","docs/reference/ROBOTICXS_HERMES_CAPABILITY_SURFACE_AUDIT_v0_1.md","docs/research/HERMES_AGENT_SKILLS_CRON_BASELINE_v0_1.md","tests/test_agent_skills_export_contract.py","tests/test_hermes_cron_routine_mapping.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the Hermes Agent Skills and cron integration baseline. 88P - Routine Wake Gate / Zero-Token Preflight v0 - is closed committed; do not infer 89P implementation, 90P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"88P","stage_name":"Routine Wake Gate / Zero-Token Preflight v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"590305394f57ccfbc729b895b446b052adbc4e6e","commit_message":"docs: add routine wake gate baseline","paths":["docs/reference/ROBOTICXS_ROUTINE_WAKE_GATE_v0_1.md","docs/reference/ROBOTICXS_ROUTINE_COST_POLICY_v0_1.md","docs/reference/ROBOTICXS_SCRIPT_ONLY_ROUTINES_v0_1.md","runtime/hermes/scripts/examples/file_change_gate.py","runtime/hermes/scripts/examples/http_diff_gate.py","runtime/hermes/scripts/examples/external_flag_gate.py","tests/test_routine_wake_gate.py","tests/test_routine_no_agent_mode.py","tests/test_routine_budget_skip.py","tests/test_routine_context_payload.py","tests/test_routine_silent_is_not_cost_control.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the Routine Wake Gate and Zero-Token Preflight baseline. 89P - Roboticxs Automation Blueprints v0 - is closed committed; do not infer 90P implementation, 91P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"89P","stage_name":"Roboticxs Automation Blueprints v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"dc53ef24f2d15ba1d35ce93ec82555e8290dc565","commit_message":"docs: add roboticxs automation blueprints","paths":["docs/reference/ROBOTICXS_AUTOMATION_BLUEPRINTS_v0_1.md","docs/reference/ROBOTICXS_BLUEPRINT_AUTHORITY_BOUNDARIES_v0_1.md","docs/reference/ROBOTICXS_BLUEPRINT_INSTALLATION_CONTRACT_v0_1.md","runtime/hermes/skills/roboticxs-daily-brief/SKILL.md","runtime/hermes/skills/roboticxs-research-radar/SKILL.md","runtime/hermes/skills/roboticxs-caregiver-routine/SKILL.md","tests/test_roboticxs_blueprint_manifest.py","tests/test_roboticxs_blueprint_authority.py","tests/test_roboticxs_blueprint_no_silent_schedule.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py"]},"implementation_authorized":false,"next_action":"Use as the Automation Blueprints baseline. 90P - Roboticxs Command Surface Policy v0 - is closed committed; do not infer 91P implementation, 92P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"90P","stage_name":"Roboticxs Command Surface Policy v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"970e6e9014ec6e7b3031a7d3d412004fdebea815","commit_message":"docs: add roboticxs command surface policy","paths":["docs/reference/ROBOTICXS_COMMAND_SURFACE_POLICY_v0_1.md","docs/reference/ROBOTICXS_CONSUMER_COMMAND_ALIASES_v0_1.md","docs/reference/ROBOTICXS_HERMES_RAW_COMMAND_BLOCKLIST_v0_1.md","tests/test_command_surface_policy.py","tests/test_forbidden_hermes_commands.py","tests/test_consumer_command_aliases.py","tests/test_approval_command_packets.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py","tests/test_roadmap_continuation_authorization_gate.py"]},"implementation_authorized":false,"next_action":"Use as the Command Surface Policy baseline. 91P - Skill Activation Scope Guard v0 - is closed committed; do not infer 92P implementation, 93P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"91P","stage_name":"Skill Activation Scope Guard v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"0f786def035d0c6380f6f511c03313b4d9db3756","commit_message":"docs: add skill activation scope guard","paths":["docs/reference/ROBOTICXS_SKILL_ACTIVATION_SCOPE_GUARD_v0_1.md","docs/reference/ROBOTICXS_SKILL_SCOPE_DECISIONS_v0_1.md","docs/reference/ROBOTICXS_SKILL_UPGRADE_AND_REDIRECT_POLICY_v0_1.md","tests/test_skill_activation_scope_guard.py","tests/test_skill_scope_decisions.py","tests/test_skill_redirect_upgrade_policy.py","tests/test_skill_scope_guard_blocks_prohibited_actions.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py","tests/test_roadmap_continuation_authorization_gate.py"]},"implementation_authorized":false,"next_action":"Use as the Skill Activation Scope Guard baseline. 92P - Hermes Tool Authority Guard v0 - is closed committed; do not infer 93P implementation, 94P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"92P","stage_name":"Hermes Tool Authority Guard v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"ac6d5c4d775367ea9b1774cfe985fedeee7a49cf","commit_message":"docs: add hermes tool authority guard","paths":["docs/reference/ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1.md","docs/reference/ROBOTICXS_TOOL_ACTION_CLASSIFICATION_v0_1.md","docs/reference/ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1.md","docs/reference/ROBOTICXS_TOOL_AUTHORITY_DECISIONS_v0_1.md","tests/test_hermes_tool_authority_guard.py","tests/test_tool_action_classification.py","tests/test_action_packet_contract.py","tests/test_tool_authority_blocks_sensitive_actions.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py","tests/test_roadmap_continuation_authorization_gate.py"]},"implementation_authorized":false,"next_action":"Use as the Hermes Tool Authority Guard baseline. 93P - Roboticxs Memory Center Bridge v0 - is closed committed; do not infer 94P implementation, 95P, or NEXT_ELIGIBLE from this status."},
  {"stage_id":"93P","stage_name":"Roboticxs Memory Center Bridge v0","status":"CLOSED_COMMITTED","authority_source":"local_repo_evidence","local_evidence":{"commit":"65ac8c03fc3305548627ca3162fb71191fcdcbb7","commit_message":"docs: add memory center bridge","paths":["docs/reference/ROBOTICXS_MEMORY_CENTER_BRIDGE_v0_1.md","docs/reference/ROBOTICXS_MEMORY_PROJECTION_POLICY_v0_1.md","docs/reference/ROBOTICXS_MEMORY_WRITEBACK_BOUNDARY_v0_1.md","docs/reference/ROBOTICXS_MEMORY_CONTEXT_INJECTION_CONTRACT_v0_1.md","tests/test_memory_center_bridge.py","tests/test_memory_projection_policy.py","tests/test_memory_writeback_boundary.py","tests/test_memory_context_injection_contract.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py","tests/test_roadmap_continuation_authorization_gate.py"]},"implementation_authorized":false,"next_action":"Use as the Memory Center Bridge baseline. 94P - Telegram MVP on Hermes Gateway v0 - is implemented pending review as story/spec/test work only; do not infer 95P or NEXT_ELIGIBLE from this status."},
  {"stage_id":"94P","stage_name":"Telegram MVP on Hermes Gateway v0","status":"IMPLEMENTED_PENDING_REVIEW","authority_source":"local_repo_evidence","local_evidence":{"commit":"same_commit_as_94P_implementation","commit_message":"docs: add telegram hermes gateway mvp","paths":["docs/reference/ROBOTICXS_TELEGRAM_HERMES_GATEWAY_MVP_v0_1.md","docs/reference/ROBOTICXS_TELEGRAM_GATEWAY_BOUNDARY_v0_1.md","docs/reference/ROBOTICXS_TELEGRAM_ACTION_PACKET_FLOW_v0_1.md","docs/reference/ROBOTICXS_TELEGRAM_MEMORY_ROUTINE_FLOW_v0_1.md","tests/test_telegram_hermes_gateway_mvp.py","tests/test_telegram_gateway_boundary.py","tests/test_telegram_action_packet_flow.py","tests/test_telegram_memory_routine_flow.py","docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md","tests/test_canonical_roadmap.py","tests/test_roadmap_continuation_authorization_gate.py"]},"implementation_authorized":false,"next_action":"Use as the Telegram MVP on Hermes Gateway story/spec/test contract. 95P and later are not authorized; do not infer runtime gateway startup, production Telegram messaging, credentials, UI, or NEXT_ELIGIBLE from this status."}
]
```

## Canonical product-spine stage

CH-01 is materialized as Stage 66P, a foundational product-spine baseline. It is additive and does not authorize storage, connectors, retrieval, browser/email/WhatsApp behavior, CRM, lead-gen, handoff, external writes, caregiver behavior, voice behavior, or Research Radar.

```json canonical-product-spine-stage
{
  "spine_id":"CH-01",
  "stage_id":"66P",
  "stage_name":"Conversación Horizontal / Continuity Spine v0",
  "status":"COMPLETED_FIXED_BASELINE",
  "rationale":"Defines continuity across conversations before later caregiver, voice, research, and advanced-skill stages.",
  "scope_signals":[
    "conversation_classification",
    "selective_notes",
    "user_criterio",
    "priority_gate",
    "que_hago_hoy_mode",
    "proactive_intervention_rules",
    "cross_topic_synthesis",
    "next_step_resolver",
    "zaubern_authority_checks"
  ],
  "implementation_authorized":false,
  "baseline_paths":[
    "app/conversation_continuity.py",
    "docs/reference/CONVERSATION_CONTINUITY_SPINE_v0_1.md",
    "tests/test_conversation_continuity_spine.py"
  ],
  "next_stage":"66P2"
}
```

## 66P2 continuation stage

66P2 is a continuation of 66P, not a feature expansion. It defines the memory architecture boundary for continuity and criterio.

Allowed scope:

- story/spec for memory architecture;
- docs/tests only by default;
- inventory existing memory surfaces;
- map `ContinuityMemoryCandidate` from 66P to current and future storage targets;
- define authority, sensitivity, confirmation, expiration, export, deletion, and influence rules.

Forbidden scope:

- no storage migration;
- no new backend;
- no Mirix implementation;
- no vector store;
- no graph store;
- no external retrieval;
- no connector;
- no caregiver behavior.

## Stage 66P completion transition

The stage registry records the 66P closeout sequence state. Stage 66P2 is the sole next eligible stage after 66P.

```json stage-66p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"66P2",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 66P closeout does not authorize memory storage implementation. It permits 66P2 story and technical-spec drafting only.

## Stage 66P2 completion transition

The stage registry records the 66P2 closeout sequence state. Stage 67P is the sole next eligible stage after 66P2.

```json stage-66p2-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"67P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 66P2 closeout does not authorize memory storage implementation, Mirix, retrieval, connectors, or caregiver behavior. It permits 67P story drafting only.

## Stage 67P completion transition

The stage registry records the 67P closeout sequence state. Stage 68P is the sole next eligible stage after 67P.

```json stage-67p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"68P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 67P closeout does not authorize caregiver runtime behavior, Telegram relay, Guided Routine Packets, medication reminders, monitoring, external messages, or sensitive caregiver memory storage. It permits 68P story drafting only.

## Stage 68P completion transition

The stage registry records the 68P closeout sequence state. Stage 69P is the sole next eligible stage after 68P.

```json stage-68p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"69P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 68P closeout authorizes local caregiver relay packet preparation only. It does not authorize Telegram sending, Telegram group management, Guided Routine Packets, medication reminders, monitoring, emergency handling, sensitive caregiver memory storage, connectors, retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, or external writes. It permits 69P story drafting only.

## Stage 69P completion transition

The stage registry records the 69P closeout sequence state. Stage 70P is the sole next eligible stage after 69P.

```json stage-69p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"70P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 69P closeout authorizes local guided routine packet preparation only. It does not authorize scheduler/background reminders, Telegram sending, caregiver runtime execution, medication decisions, dosage or schedule management, ingestion verification, emergency triage, monitoring, sensors, durable routine progress, sensitive caregiver memory storage, voice behavior, connectors, retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, or external writes. It permits 70P story drafting only.

## Stage 70P completion transition

The stage registry records the 70P closeout sequence state. Stage 71P is the sole next eligible stage after 70P.

```json stage-70p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"71P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 70P closeout authorizes a source-backed voice-note intelligence architecture boundary only. It does not authorize audio upload handling, Telegram voice attachment processing, ASR inference, VibeVoice or Whisper dependency installation, model download, model weights, external audio API calls, TTS, cloned voice, speaker identification, voice authentication, continuous listening, background transcription, raw audio storage, durable transcript storage, caregiver voice runtime, medication decisions, emergency triage, external sends, connectors, retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, or external writes. It permits 71P bounded caregiver voice intake story drafting only.

## Stage 71P completion transition

The stage registry records the 71P closeout sequence state. Stage 72P is the sole next eligible stage after 71P.

```json stage-71p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"72P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 71P closeout authorizes local transcript-stub caregiver voice intake only. It does not authorize audio upload handling, Telegram voice attachment processing, ASR inference, VibeVoice or Whisper dependency installation, model download, model weights, external transcription APIs, TTS, cloned voice, speaker identification, voice authentication, continuous listening, background transcription, raw audio storage, durable transcript storage, caregiver voice runtime execution, medication decisions, emergency triage, surveillance, external sends, connectors, retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, external writes, or 72P Research Radar behavior. It permits 72P bounded Research Radar / Last30Days Skill story drafting only.

## Stage 72P completion transition

The stage registry records the 72P closeout sequence state. Stage 73P is the sole next eligible stage after 72P.

```json stage-72p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"73P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 72P closeout authorizes local request-scoped research packet preparation only. It does not authorize live web search, scraping, Reddit/X/YouTube/Hacker News/Polymarket clients, ScrapeCreators, yt-dlp, browser automation, connector retrieval, external API calls, background jobs, scheduled monitoring, push alerts, persistent watchlists, durable source storage, raw content archives, user-profile enrichment from public data, cross-thread retrieval, memory writes, publishing, CRM, lead-gen, handoff, external writes, or 73P Understand-Anything/codegraph behavior. It permits 73P bounded Understand-Anything + codegraph Factory Skill story drafting only.

## Stage 73P completion transition

The stage registry records the 73P closeout sequence state. Stage 74P is the sole next eligible stage after 73P.

```json stage-73p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"74P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 73P closeout authorizes local repo-understanding packet preparation only. It does not authorize Understand Anything installation, codegraph installation, dependency install, code vendoring, repository clone, MCP server activation, tree-sitter runtime, SQLite index, graph database, dashboard, multi-agent pipeline, arbitrary code execution, shell execution, build/test execution, network access, external API calls, persistent repo index, raw source archive, security certification, correctness proof, connector retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, external writes, or 74P ECC behavior. It permits 74P bounded ECC Knowledge Compiler Factory Skill story drafting only.

## Stage 74P completion transition

The stage registry records the 74P closeout sequence state. Stage 75P is the sole next eligible stage after 74P.

```json stage-74p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"75P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 74P closeout authorizes local non-authoritative knowledge compilation packet preparation only. It does not authorize `MemoryItem` writes, `ProposedMemory` writes, live retrieval, connectors, web, network, APIs, MCP, Gmail, Drive, Notion, external tools, semantic canon rewrites, truth conversion, silent conflict resolution, user-facing commands, runtime expansion, or 75P Agent-Reach behavior. It permits 75P bounded Agent-Reach research parking-lot story drafting only.

## Stage 75P completion transition

The stage registry records the 75P closeout sequence state. Stage 76P is the sole next eligible stage after 75P.

```json stage-75p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":"76P",
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 75P closeout parks Agent-Reach as research-only external reach assessment. It does not authorize Agent-Reach installation, runtime dependency use, connector activation, live retrieval, automatic source scanning, scraping, credential or cookie handling, MCP configuration, command routing changes, memory ingestion, retrieval index writes, background monitoring, user-facing commands, product support claims, automatic roadmap promotion, or 76P VoxCPM behavior. It permits 76P bounded VoxCPM research parking-lot story drafting only.

## Stage 76P completion transition

The stage registry records the 76P closeout sequence state. No local next eligible implementation stage is authorized after 76P.

```json stage-76p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

The 76P closeout parks VoxCPM and VoxCPM2 as research-only voice-model candidates. It does not authorize dependency installation, model download, model weights, inference, TTS execution, audio generation, voice design, voice cloning, speaker identification, speaker authentication, Telegram voice handling, audio upload handling, raw audio storage, generated audio storage, durable transcript storage, background listening, streaming audio runtime, local web demos, serving endpoints, CUDA/PyTorch/vLLM/Nano-vLLM/ModelScope/Hugging Face integration, connectors, MCP configuration, external APIs, user-facing commands, product support claims, automatic roadmap promotion, or any implementation-stage behavior. It permits 77P roadmap continuation authorization gate story/spec/build only after explicit maintainer approval.

## Stage 77P completion transition

The stage registry records the 77P closeout sequence state. No local next eligible implementation stage is authorized after 77P.

```json stage-77p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

No next implementation stage is authorized until a maintainer explicitly chooses one. The 77P closeout does not create 78P as `NEXT_ELIGIBLE`, does not authorize product features, does not authorize runtime changes, does not promote research parking lots to runtime, does not convert candidate examples into canon, and does not grant staging or commit authority.

## Stage 78P completion transition

The stage registry records the 78P closeout sequence state. No local next eligible implementation stage is authorized after 78P.

```json stage-78p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

78P adds a minimal local Hermes-compatible runtime foundation and upstream tracking artifacts. It does not authorize Telegram, caregiver routines, document intake, connectors, retrieval, automatic memory creation, `ProposedMemory` writes, scheduler or background jobs, shell execution, Hermes dependency installation, Hermes upstream install script execution, automatic upstream updates, product support claims, staging, commit authority, or any 79P behavior.

## Stage 79P completion transition

The stage registry records the 79P closeout sequence state. No local next eligible implementation stage is authorized after 79P.

```json stage-79p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

79P adds a minimal Telegram text-channel runtime bootstrap that parses local Telegram webhook payloads, adapts them into the Hermes runtime foundation, and prepares a local `sendMessage` payload without calling Telegram. It does not authorize caregiver routines, guided routines, document/PDF intake, file downloads, voice, payments, Telegram group relay, proactive/background messages, memory writes, `ProposedMemory` writes, retrieval, connectors, scheduler/background jobs, WhatsApp, production deployment, full Telegram command UX, staging, commit authority, or any 80P behavior.

## Stage 80P completion transition

The stage registry records the 80P closeout sequence state. No local next eligible implementation stage is authorized after 80P.

```json stage-80p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

80P adds a minimal local Telegram text conversation loop that parses a Telegram update, dispatches through the Hermes runtime foundation, and returns a deterministic safe local webhook response. It does not authorize real outbound Telegram API delivery, long-term conversation memory, user profile memory, `ProposedMemory` creation, caregiver behavior, document/file handling, voice handling, retrieval, connectors, proactive/background messaging, scheduler, production deployment, staging, commit authority, or any 81P behavior.

## Stage 81P completion transition

The stage registry records the 81P closeout sequence state. No local next eligible implementation stage is authorized after 81P.

```json stage-81p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

81P adds a safe manual Telegram runtime smoke path that documents required environment variables, evaluates local readiness with redacted diagnostics, and provides manual webhook and smoke checklists. It does not authorize production deployment, automatic webhook registration, real Telegram API calls in tests, committed Telegram secrets, caregiver behavior, document/file handling, voice handling, memory writes, `ProposedMemory` writes, retrieval, connectors, proactive/background messaging, scheduler, staging, commit authority, or any 82P behavior.

## Stage 82P completion transition

The stage registry records the 82P closeout sequence state. No local next eligible implementation stage is authorized after 82P.

```json stage-82p-completion-transition
{
  "closeout_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_status":"COMPLETED_FIXED_BASELINE",
  "after_commit_next_eligible":null,
  "transition_requires_commit":true,
  "implementation_authorized":false
}
```

82P adds a Telegram memory proposal loop that creates inert proposed-memory candidates only from explicit user memory intent, shows deterministic approval/rejection instructions, and creates active memory only after explicit approval. It does not authorize automatic memory activation, normal-conversation memory extraction, Context Scan, external source scanning, retrieval, connectors, caregiver behavior, document/file handling, voice handling, proactive/background behavior, scheduler, staging, commit authority, or any 83P behavior.

## Stage 83P closeout transition

The stage registry records the 83P committed closeout state.

```json stage-83p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"ef9faeb5ed427e2fe4cc04720a50a0a5eadf4d22",
  "commit_message":"feat: add active memory recall over telegram",
  "after_commit_next_eligible":null,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

83P adds deterministic active-memory recall to the Telegram runtime webhook. It lists only approved active local memories for the resolved Telegram user and active robot, returns safe empty states, preserves 82P proposal/approval/rejection precedence, and does not mutate memory on recall. It does not authorize retrieval, Context Scan, connectors, caregiver behavior, document/file handling, voice handling, proactive/background behavior, scheduler, staging, commit authority, or `NEXT_ELIGIBLE`.

## Stage 84P closeout transition

The stage registry records the 84P committed closeout state.

```json stage-84p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"1b5875db2cc0864a7aa02ac80b5b60507ca0a0a6",
  "commit_message":"feat: add telegram active memory forget",
  "after_commit_next_eligible":"85P",
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

84P adds deterministic active-memory forget commands to the Telegram runtime webhook. It transitions only scoped `ACTIVE` memory to `FORGOTTEN` for the resolved Telegram user and active robot, returns identical safe failure text for missing, inactive, invalid, already-forgotten, and foreign IDs, and extends active memory recall output to include memory IDs. It does not authorize retrieval, Context Scan, connectors, caregiver behavior, document/file handling, voice handling, proactive/background behavior, scheduler, staging, commit authority, 85P, or `NEXT_ELIGIBLE`.

## Stage 85P closeout transition

The stage registry records the 85P committed closeout state. At 85P closeout, Stage 86P became next eligible for story/spec work only; current 86P status is recorded separately below.

```json stage-85p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"95e23e5438812328f804ba026095237d17f1bf72",
  "commit_message":"docs: add hermes roboticxs soul rebase",
  "after_commit_next_eligible":"86P",
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

85P adds the Roboticxs Hermes profile identity boundary. `runtime/hermes/SOUL.md` is identity/style only, `runtime/hermes/AGENTS.md` contains runtime/project instructions, and reference docs preserve the boundary that Hermes profiles are not security sandboxes, Hermes memory is not Roboticxs canonical memory, and Hermes command approval is not Roboticxs business-action authority. It does not authorize Hermes install automation, Telegram gateway changes, model routing, tool interception, automation blueprints, memory center bridge, payment or subscription logic, UI, 87P, or `NEXT_ELIGIBLE`.

## Stage 86P closeout transition

The stage registry records the 86P committed closeout state. Stage 87P - Hermes + Agent Skills + Cron Integration Baseline v0 - is closed committed. Stage 88P status is recorded separately below.

```json stage-86p-implementation-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"efb4f5f",
  "commit_message":"docs: add hermes real settings baseline",
  "after_commit_next_eligible":"87P",
  "next_eligible_stage_name":"Hermes + Agent Skills + Cron Integration Baseline v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_88p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

86P adds a verified Hermes real-settings research baseline and a Roboticxs Hermes config contract. It records official upstream source evidence for real Hermes config files, environment-variable boundaries, commands, profile behavior, SOUL/AGENTS roles, and rejects fake settings such as `MEMORY_BACKEND`, `SKILLS_WATCH`, `CONTEXT_PRELOAD`, `NOTIFICATION_GATEWAY`, `MEMORY_RETRIEVAL_DEPTH`, `OUTPUT_PATH`, and `HERMES_MAKE_ME_SMARTER`. It preserves that `SOUL.md` is identity/style only, `.env` is for secrets, config files are for non-secret runtime configuration, Hermes profiles are state isolation rather than business authorization, Hermes memory is not Roboticxs canonical memory, Hermes command approval is not Roboticxs business-action authority, Zaubern-lite remains the authority layer, Memory Center remains canonical memory, and Cost Governor remains spend/wake authority. It does not authorize Hermes install automation, Telegram gateway changes, model routing, tool interception, automation blueprints, Memory Center bridge implementation, payment or subscription logic, UI, 88P, or `NEXT_ELIGIBLE`.

## Stage 87P implementation transition

The stage registry records the 87P committed closeout state. Stage 88P - Routine Wake Gate / Zero-Token Preflight v0 - is closed committed. Stage 89P status is recorded separately below.

```json stage-87p-implementation-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"213a7772aef3a55e03f2284044aba458c752c54e",
  "commit_message":"docs: add hermes agent skills cron baseline",
  "after_commit_next_eligible":"88P",
  "next_eligible_stage_name":"Routine Wake Gate / Zero-Token Preflight v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_91p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

87P creates a documentation/spec/test baseline for using Hermes runtime capabilities, Agent Skills packaging, and Hermes cron scheduling without confusing capability with product authority. Hermes is runtime capability, not Roboticxs product. Agent Skills packages instructions/resources; it does not enforce authority. Roboticxs SkillManifest remains canonical for package, scope, plan, confirmation, blocked actions, and upgrade path. Hermes cron schedules work; Roboticxs Routine is the consumer product object. Cron `[SILENT]` is not cost control. `wakeAgent=false` and no-agent mode are defined by 88P, not 87P implementation. Hermes memory remains runtime memory, not canonical Roboticxs Memory Center. No external send/update/publish/payment/destructive action may be implied without Zaubern-lite authority and user confirmation. 87P does not authorize actual Hermes cron execution, runtime gateway changes, blueprints, wake-gate execution, MCP/plugin activation, 90P, or `NEXT_ELIGIBLE`.

## Stage 88P closeout transition

The stage registry records the 88P committed closeout state. Stage 89P - Roboticxs Automation Blueprints v0 - is closed committed. Stage 90P status is recorded separately below.

```json stage-88p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"590305394f57ccfbc729b895b446b052adbc4e6e",
  "commit_message":"docs: add routine wake gate baseline",
  "after_commit_next_eligible":"89P",
  "next_eligible_stage_name":"Roboticxs Automation Blueprints v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_91p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

88P defines the Routine Wake Gate / Zero-Token Preflight contract. Scripts detect; agents judge; Zaubern-lite authorizes; humans confirm sensitive actions. `wakeAgent=false` means the LLM should not run and token usage should be zero. `wakeAgent=true` may pass bounded context to an agent run only after budget policy allows it. No-agent/script-only routines never invoke Model Router. `[SILENT]` suppresses delivery only and is not cost control. Every recurring routine must declare a wake policy and budget policy. Scripts must not write directly to canonical Roboticxs Memory Center, must not execute sensitive actions, and failed scripts must produce observable error records. Hermes memory remains runtime memory, not canonical Roboticxs memory. 88P does not authorize live Hermes cron execution, runtime gateway changes, production scheduling, MCP/plugin activation, 91P, or `NEXT_ELIGIBLE`.

## Stage 89P closeout transition

The stage registry records the 89P committed closeout state. Stage 90P - Roboticxs Command Surface Policy v0 - is closed committed. Stage 91P - Skill Activation Scope Guard v0 - is next eligible for story/spec work only and is not implemented. Stage 92P and later are not authorized.

```json stage-89p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"dc53ef24f2d15ba1d35ce93ec82555e8290dc565",
  "commit_message":"docs: add roboticxs automation blueprints",
  "after_commit_next_eligible":"90P",
  "next_eligible_stage_name":"Roboticxs Command Surface Policy v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_91p_next_eligible_after_90p_closeout":true,
  "stage_91p_implemented":false,
  "stage_92p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

89P defines Roboticxs Automation Blueprints as user-installable `Routine` templates, not silently scheduled cron jobs. Each blueprint must declare name, description, package, inputs, schedule policy, source authorization, wake policy, skill binding, model/budget policy, delivery target, authority boundary, memory sink policy, and confirmation behavior. Recurring blueprints must reference the 88P wake-gate policy where feasible. Blueprint outputs may create `ProposedMemory` candidates but never canonical memory automatically. Hermes remains runtime capability, Agent Skills remains portable packaging, Roboticxs SkillManifest remains product/package/scope authority, and Zaubern-lite remains action authority. 89P does not authorize live Hermes cron execution, production scheduling, gateway changes, actual MCP/plugin activation, UI, 91P, or `NEXT_ELIGIBLE`.

## Stage 90P closeout transition

The stage registry records the 90P committed closeout state. Stage 91P - Skill Activation Scope Guard v0 - is closed committed. Stage 92P - Hermes Tool Authority Guard v0 - is next eligible for story/spec work only and is not implemented. Stage 93P and later are not authorized.

```json stage-90p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"970e6e9014ec6e7b3031a7d3d412004fdebea815",
  "commit_message":"docs: add roboticxs command surface policy",
  "after_commit_next_eligible":"91P",
  "next_eligible_stage_name":"Skill Activation Scope Guard v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_92p_next_eligible_after_91p_closeout":true,
  "stage_92p_implemented":false,
  "stage_93p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

90P defines the consumer-safe command surface policy for raw Hermes slash commands, CLI commands, tool controls, model controls, gateway controls, MCP/plugin controls, and dangerous bypass commands. End-user commands must use Roboticxs product language and map to user intent, allowed plan, authority boundary, cost policy, audit log, and safe fallback before exposure. `/approve` and `/deny` require Action Packets for sensitive actions. `/yolo` is never consumer-visible. Hermes capability does not equal Roboticxs permission. Zaubern-lite remains action authority, Cost Governor remains spend/wake authority, and Memory Center remains canonical memory. 90P does not authorize live command routing, runtime gateway changes, production enforcement code, MCP/plugin activation, UI, 92P, or `NEXT_ELIGIBLE`.

## Stage 91P closeout transition

The stage registry records the 91P committed closeout state. Stage 92P - Hermes Tool Authority Guard v0 - is closed committed. Stage 93P - Roboticxs Memory Center Bridge v0 - is next eligible for story/spec work only and is not implemented. Stage 94P and later are not authorized.

```json stage-91p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"0f786def035d0c6380f6f511c03313b4d9db3756",
  "commit_message":"docs: add skill activation scope guard",
  "after_commit_next_eligible":"92P",
  "next_eligible_stage_name":"Hermes Tool Authority Guard v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_93p_next_eligible_after_92p_closeout":true,
  "stage_93p_implemented":false,
  "stage_94p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

91P defines the Skill Activation Scope Guard contract. It decides whether a request should be answered by the active skill, clarified, redirected to another enabled skill, offered as an upgrade, refused as out-of-scope, or blocked as prohibited. Roboticxs SkillManifest remains canonical for scope, package, plan, confirmation, blocked actions, escalation, fallback, and upgrade paths. Agent Skills `description` helps discovery but does not decide authority. Hermes skill activation is runtime capability, not product permission. Disabled paid-skill requests return `OFFER_UPGRADE`, requests belonging to another enabled skill return `REDIRECT`, ambiguous in-scope requests return `CLARIFY`, safe out-of-scope requests return `REFUSE_SCOPE`, and prohibited/sensitive actions return `BLOCK` or defer to Zaubern-lite authority rules. 91P does not authorize live runtime routing, gateway changes, production enforcement code, payment/subscription logic, UI, 93P, or `NEXT_ELIGIBLE`.

## Stage 92P closeout transition

The stage registry records the 92P committed closeout state. Stage 93P - Roboticxs Memory Center Bridge v0 - is closed committed. Stage 94P - Telegram MVP on Hermes Gateway v0 - is next eligible for story/spec work only and is not implemented. Stage 95P and later are not authorized.

```json stage-92p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"ac6d5c4d775367ea9b1774cfe985fedeee7a49cf",
  "commit_message":"docs: add hermes tool authority guard",
  "after_commit_next_eligible":"93P",
  "next_eligible_stage_name":"Roboticxs Memory Center Bridge v0",
  "next_eligible_implementation_status":"CLOSED_COMMITTED",
  "stage_94p_next_eligible_after_93p_closeout":true,
  "stage_94p_implemented_pending_review":true,
  "stage_95p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

92P defines the Hermes Tool Authority Guard contract. It classifies and gates proposed Hermes tool calls and actions after skill activation but before execution. Hermes tool availability is capability, not permission. Agent Skills instructions are not authority. Scope Guard does not authorize execution; it only decides skill participation. Safe read/search/summarize/classify/draft actions may be `ALLOW` when within enabled scope and budget. External sends, writes, publishing, third-party scheduling, CRM modification, and visual signatures require `ASK_CONFIRMATION` or stronger and every `ASK_CONFIRMATION` must produce an Action Packet. Payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions default to `BLOCK` unless a future explicitly authorized policy says otherwise. Medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradiction must `ESCALATE` or `BLOCK` under caregiver boundary. Cost Governor remains spend/wake authority, Memory Center remains canonical memory, and Zaubern-lite remains authority layer. 92P does not authorize live Hermes interception, gateway changes, production enforcement code, MCP/plugin activation, UI, 94P, or `NEXT_ELIGIBLE`.

## Stage 93P closeout transition

The stage registry records the 93P committed closeout state. Stage 94P - Telegram MVP on Hermes Gateway v0 - is implemented pending review as story/spec/test work only. Stage 95P and later are not authorized.

```json stage-93p-closeout-transition
{
  "closeout_status":"CLOSED_COMMITTED",
  "commit":"65ac8c03fc3305548627ca3162fb71191fcdcbb7",
  "commit_message":"docs: add memory center bridge",
  "after_commit_next_eligible":"94P",
  "next_eligible_stage_name":"Telegram MVP on Hermes Gateway v0",
  "next_eligible_implementation_status":"IMPLEMENTED_PENDING_REVIEW",
  "stage_94p_implemented_pending_review":true,
  "stage_95p_and_later_authorized":false,
  "transition_requires_commit":false,
  "implementation_authorized":false
}
```

93P defines the Roboticxs Memory Center Bridge contract. Roboticxs Memory Center remains canonical product memory. Hermes memory remains runtime memory only. Approved Roboticxs `MemoryItem` records may be projected into Hermes runtime context through `MemoryProjectionPolicy` and `MemoryContextBlock` constraints, but projection must preserve source, approval status, scope, sensitivity, expiry/staleness, and allowed-use constraints. Hermes runtime output may propose `ProposedMemory` candidates through a `MemoryWritebackRequest`, but must not write canonical memory directly. Boundary Memory has higher priority than preference memory. Sensitive memories require explicit projection policy. Outdated or rejected memories must not be injected. Inferences must be labeled as inferences, opinions/preferences must not be represented as facts, and caregiver memories must preserve human escalation boundaries. Memory projection does not override Tool Authority Guard, Scope Guard, Cost Governor, or Zaubern-lite decisions. No projection may authorize a tool/action or silently expand a user's permissions. 93P does not authorize live Hermes memory provider integration, runtime gateway changes, production memory sync, UI, 94P implementation, 95P, or `NEXT_ELIGIBLE`.

## Stage 94P implementation transition

The stage registry records the 94P implemented pending review state. Stage 95P and later are not authorized. No stage is next eligible after 94P without explicit maintainer direction.

```json stage-94p-implementation-transition
{
  "implementation_status":"IMPLEMENTED_PENDING_REVIEW",
  "commit":"same_commit_as_94P_implementation",
  "commit_message":"docs: add telegram hermes gateway mvp",
  "implemented_stage":"94P",
  "implemented_stage_name":"Telegram MVP on Hermes Gateway v0",
  "stage_95p_and_later_authorized":false,
  "next_eligible_stage":null,
  "runtime_gateway_start_authorized":false,
  "production_messaging_authorized":false,
  "telegram_credentials_authorized":false,
  "implementation_authorized":false
}
```

94P defines the Telegram MVP on Hermes Gateway contract. Telegram is the MVP user-facing channel. Hermes Gateway is runtime capability, not the product UX. Raw Hermes commands must not be exposed directly to consumer users. Telegram messages must pass through Roboticxs Command Surface Policy, Skill Activation Scope Guard, Tool Authority Guard, Memory Center Bridge, Routine Wake Gate, and Automation Blueprint boundaries before any future runtime capability may act. Sensitive Telegram actions must produce visible Action Packets before confirmation, and `/approve` or `/deny` equivalents must reference a specific Action Packet. 94P does not authorize live Hermes Gateway startup, Telegram credentials, production messaging, full runtime integration, UI, external send/write/publish/payment/destructive execution, 95P, or `NEXT_ELIGIBLE`.

## Sequencing and authorization rules

```json roadmap-sequencing-rules
[
  "no_stage_is_next_eligible_after_94P_without_explicit_maintainer_direction",
  "eligibility_permits_story_drafting_only",
  "roadmap_inclusion_never_authorizes_implementation",
  "every_stage_requires_story_approval",
  "every_stage_requires_technical_spec_approval",
  "runtime_implementation_requires_separately_approved_scoped_build_tests_and_validation",
  "stage_83P_is_closed_committed_after_metadata_reconciliation",
  "stage_84P_is_closed_committed_after_active_memory_forget_closeout",
  "stage_85P_is_closed_committed_after_hermes_soul_rebase_closeout",
  "stage_86P_is_closed_committed_after_hermes_real_settings_baseline_closeout",
  "stage_87P_is_closed_committed_after_hermes_agent_skills_cron_baseline_closeout",
  "stage_88P_is_closed_committed_after_routine_wake_gate_closeout",
  "stage_89P_is_closed_committed_after_automation_blueprints_closeout",
  "stage_90P_is_closed_committed_after_command_surface_policy_closeout",
  "stage_91P_is_closed_committed_after_skill_activation_scope_guard_closeout",
  "stage_92P_is_closed_committed_after_tool_authority_guard_closeout",
  "stage_93P_is_closed_committed_after_memory_center_bridge_closeout",
  "stage_94P_is_implemented_pending_review_after_maintainer_direction",
  "do_not_invent_95P_without_explicit_maintainer_direction_in_repo_evidence",
  "sequence_changes_require_explicit_maintainer_approval_and_canonical_roadmap_update",
  "external_repositories_and_recent_planning_threads_cannot_independently_change_sequence"
]
```

## Deferred-candidate registry

Deferred and radar candidates require future story approval and technical-spec approval. They are not runtime base or implementation authorization.

```json deferred-candidate-registry
[
  {"candidate_id":"connector_architecture","name":"Connector architecture","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","authority_and_data_boundary_design","scoped_build_tests_and_validation"],"implementation_authorized":false},
  {"candidate_id":"live_retrieval","name":"Live retrieval","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","63P_freeze_reopening_approval","connector_authority_design"],"implementation_authorized":false},
  {"candidate_id":"browser_email_whatsapp_execution","name":"Browser, email, or WhatsApp execution","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","external_action_authority_design","approval_packet_enforcement"],"implementation_authorized":false},
  {"candidate_id":"external_skills","name":"External skills","classification":"DEFERRED","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","supply_chain_and_authority_review","scoped_build_tests_and_validation"],"implementation_authorized":false},
  {"candidate_id":"agent_reach","name":"Agent-Reach","classification":"PARKING_LOT","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","external_action_boundary_review"],"implementation_authorized":false},
  {"candidate_id":"voxcpm","name":"VoxCPM","classification":"PARKING_LOT","authority_source":"explicit_maintainer_direction","reopen_requirements":["explicit_story_approval","technical_spec_approval","voice_strategy_decision","privacy_and_authority_review"],"implementation_authorized":false}
]
```

## Blocked-v0 registry

Blocked-v0 behavior remains blocked even when related work appears in the sequence or deferred registry.

```json canonical-blocked-v0-registry
[
  {"blocked_id":"total_autonomy","behavior":"Total autonomy","reason":"Roboticxs v0 remains user-controlled and bounded.","reopen_requirements":["explicit_product_boundary_change","story_and_spec_approval","authority_model_review"],"implementation_authorized":false},
  {"blocked_id":"continuous_screen_tracking","behavior":"Continuous screen tracking","reason":"Continuous observation exceeds the approved v0 privacy and authority boundary.","reopen_requirements":["explicit_product_boundary_change","privacy_review","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"authenticated_scraping","behavior":"Scraping with login or cookies","reason":"Credentialed scraping and session authority are outside v0.","reopen_requirements":["explicit_product_boundary_change","credential_and_connector_architecture","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"automatic_publishing_or_direct_messages","behavior":"Automatic publishing or direct messages","reason":"External communication requires explicit authority not present in v0.","reopen_requirements":["explicit_product_boundary_change","approval_packet_enforcement","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"cloned_voice","behavior":"Cloned voice","reason":"Voice cloning is outside the approved v0 privacy and identity boundary.","reopen_requirements":["explicit_product_boundary_change","identity_and_privacy_review","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"external_action_without_approval_packet","behavior":"External action without approval packet","reason":"Nothing important may happen externally without explicit user approval.","reopen_requirements":["not_reopenable_within_v0"],"implementation_authorized":false},
  {"blocked_id":"connector_activation","behavior":"Connector activation","reason":"No connector architecture or activation authority is approved in v0.","reopen_requirements":["explicit_product_boundary_change","connector_architecture_approval","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"live_retrieval_execution","behavior":"Live retrieval execution","reason":"Stage 63P freezes retrieval-control as metadata and control only.","reopen_requirements":["63P_freeze_reopening_approval","connector_architecture_approval","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"browser_email_whatsapp_execution","behavior":"Browser, email, or WhatsApp execution","reason":"These external execution surfaces are outside v0.","reopen_requirements":["explicit_product_boundary_change","external_action_authority_design","story_and_spec_approval"],"implementation_authorized":false},
  {"blocked_id":"crm_lead_pipeline_handoff","behavior":"CRM, lead generation, pipeline, or handoff","reason":"Roboticxs is a personal robot, not Agentius or a commercial pipeline product.","reopen_requirements":["not_reopenable_within_roboticxs_v0"],"implementation_authorized":false},
  {"blocked_id":"external_writes","behavior":"External writes","reason":"External writes require authority and connector architecture not present in v0.","reopen_requirements":["explicit_product_boundary_change","connector_and_external_action_authority_design","story_and_spec_approval"],"implementation_authorized":false}
]
```

## Reopening and change control

Roadmap inclusion is not implementation approval. Every stage requires story approval, technical-spec approval, scoped implementation approval, tests, and validation.

Sequence changes require explicit maintainer approval and an update to this canonical roadmap. External repositories, planning threads, and historical documents cannot independently change the sequence.

## Non-claims

- no feature work
- no connectors
- no live retrieval
- no browser/email/WhatsApp execution
- no caregiver runtime beyond local 68P relay packet and 69P guided routine packet preparation
- no voice runtime implementation
- no live Research Radar execution beyond local 72P packet preparation
- no repo-understanding execution beyond local 73P packet preparation
- no external skills
- no CRM
- no lead-gen
- no pipeline
- no handoff
- no external writes

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_canonical_roadmap.py`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q tests/test_retrieval_control_freeze.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git diff --check`
- `git status --short`
