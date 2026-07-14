# Runtime Surface Audit v0.1

## Purpose

This Stage 62P audit is the canonical inventory of the user-reachable Roboticxs runtime surface after command-routing consolidation.

It records current runtime evidence separately from future recommendations. It does not add, remove, freeze, deprecate, or change any command or capability.

Roboticxs is a personal B2C/prosumer robot. Agentius is B2B automation. Zaubern is the deep authority layer.

## Product boundary

The audited runtime is local and user-controlled. Preparation, readouts, proposals, and approval packets do not imply external execution.

Blocked in v0:

- total autonomy
- continuous screen tracking
- scraping with login or cookies
- automatic publishing or direct messages
- cloned voice
- external action without an approval packet

## Audit methodology

Runtime evidence comes from `app/command_registry.py`, `app/orchestrator.py`, their detectors and parsers, their flow handlers, and focused tests.

Each surface has a stable `surface_id`. Aliases and parameterized variants belong to one surface instead of creating duplicate surfaces.

Evidence and recommendation have different meanings:

- `evidence` records whether a surface is implemented, tested, documented, or inferred.
- `classification` describes its current audit category.
- `recommendation` is advisory and belongs to a later stage when it requests review.

The structured inventory below is parsed by consistency tests. Narrative sections are for maintainers and are not treated as brittle snapshots.

## Structured surface inventory

```json runtime-surface-inventory
[
  {"surface_id":"approval.action_approval_packet","route_source":"command_registry","route_name":"action_approval_packet","priority":0,"matcher_kind":"parsed_exact_or_trailing_text","commands_or_patterns":["approval packet","prepare approval","prepare approval for <task>","Spanish aliases and trailing-task variants"],"handler_or_flow":"process_action_approval_packet","effect_boundary":"Creates a local preparation/approval packet; does not execute or send the requested action.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_action_approval_packets.py"]},
  {"surface_id":"web.preflight","route_source":"command_registry","route_name":"web_preflight","priority":1,"matcher_kind":"exact_or_alias","commands_or_patterns":["preflight web","revisar tarea web","evaluar trámite web","web workflow preflight","check web workflow"],"handler_or_flow":"process_web_preflight","effect_boundary":"Evaluates a proposed web task locally; no browser or external execution.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_web_preflight.py"]},
  {"surface_id":"capability.catalog","route_source":"command_registry","route_name":"capability_catalog","priority":2,"matcher_kind":"exact_or_alias","commands_or_patterns":["qué puedes hacer","qué habilidades tienes","habilidades","skill catalog","what can you do","what skills do you have"],"handler_or_flow":"process_capability_catalog","effect_boundary":"Returns the active local capability catalog; does not activate a capability.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_capability_resolver.py"]},
  {"surface_id":"capability.query","route_source":"command_registry","route_name":"capability_query","priority":3,"matcher_kind":"parsed_pattern","commands_or_patterns":["puedes ayudarme con <task>","puedes hacer <task>","puedes <task>","can you help me with <task>","can you <task>"],"handler_or_flow":"process_capability_query","effect_boundary":"Resolves capability guidance locally; does not perform the requested task.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_capability_resolver.py"]},
  {"surface_id":"attention.summary","route_source":"command_registry","route_name":"attention_summary","priority":4,"matcher_kind":"exact_or_alias","commands_or_patterns":["qué se me pasó","what did i miss","qué necesita mi atención"],"handler_or_flow":"process_attention_summary","effect_boundary":"Summarizes local robot records that may need attention.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_attention_summary.py"]},
  {"surface_id":"robot_folder.summary","route_source":"command_registry","route_name":"robot_folder","priority":5,"matcher_kind":"exact_or_alias","commands_or_patterns":["robot folder","mi información importante","lo que robbie sabe","what does robbie know"],"handler_or_flow":"process_robot_folder","effect_boundary":"Summarizes local robot-held information.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_robot_folder.py"]},
  {"surface_id":"super_familiar.prepare","route_source":"command_registry","route_name":"super_familiar","priority":6,"matcher_kind":"exact_or_alias","commands_or_patterns":["súper familiar","super familiar","preparar súper familiar","lista del súper familiar","family groceries"],"handler_or_flow":"process_super_familiar","effect_boundary":"Prepares a local family-grocery artifact; no checkout or purchase.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_super_familiar.py"]},
  {"surface_id":"usage.spend","route_source":"command_registry","route_name":"usage_spend","priority":7,"matcher_kind":"exact","commands_or_patterns":["what did you spend"],"handler_or_flow":"process_usage_spend","effect_boundary":"Reads local estimated usage-cost records.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_usage_reporting.py"]},
  {"surface_id":"usage.tokens","route_source":"command_registry","route_name":"usage_tokens","priority":8,"matcher_kind":"exact","commands_or_patterns":["show token usage"],"handler_or_flow":"process_usage_tokens","effect_boundary":"Reads local token-usage records.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_usage_reporting.py","tests/test_token_usage.py"]},
  {"surface_id":"budget.status","route_source":"command_registry","route_name":"budget_status","priority":9,"matcher_kind":"exact","commands_or_patterns":["show budget status"],"handler_or_flow":"process_budget_status","effect_boundary":"Reads the local budget policy and estimated usage posture.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_budget_policy.py"]},
  {"surface_id":"budget.reset","route_source":"command_registry","route_name":"budget_policy_reset","priority":10,"matcher_kind":"exact_or_alias","commands_or_patterns":["reset budget policy","restore default budget policy"],"handler_or_flow":"process_budget_policy_reset","effect_boundary":"Resets the user's local budget policy.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_budget_policy.py"]},
  {"surface_id":"file_control.list_received","route_source":"command_registry","route_name":"file_listing","priority":11,"matcher_kind":"exact","commands_or_patterns":["what files did you receive"],"handler_or_flow":"process_file_listing","effect_boundary":"Lists retained local file metadata only.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.pending_attempts","route_source":"command_registry","route_name":"pending_file_retrievals","priority":12,"matcher_kind":"exact","commands_or_patterns":["what file retrievals are pending"],"handler_or_flow":"process_pending_file_retrieval_listing","effect_boundary":"Lists local retrieval-attempt metadata; performs no retrieval.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.pending_enablement_requests","route_source":"command_registry","route_name":"pending_file_retrieval_enablement_requests","priority":13,"matcher_kind":"exact","commands_or_patterns":["what retrieval enablement requests are pending"],"handler_or_flow":"process_pending_file_retrieval_enablement_request_listing","effect_boundary":"Lists local enablement-request metadata; retrieval remains disabled.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.enablement_request_history","route_source":"command_registry","route_name":"file_retrieval_enablement_request_history","priority":14,"matcher_kind":"exact_or_alias","commands_or_patterns":["what retrieval enablement requests do you have","show retrieval enablement request history"],"handler_or_flow":"process_file_retrieval_enablement_request_history","effect_boundary":"Reads local enablement-request history; retrieval remains disabled.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.summary","route_source":"command_registry","route_name":"file_retrieval_control_summary","priority":15,"matcher_kind":"exact_or_alias","commands_or_patterns":["show retrieval control summary","show file retrieval controls"],"handler_or_flow":"process_file_retrieval_control_summary","effect_boundary":"Summarizes local retrieval-control records; performs no retrieval.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.report","route_source":"command_registry","route_name":"file_retrieval_control_report","priority":16,"matcher_kind":"exact_or_alias","commands_or_patterns":["show retrieval control report","show file retrieval audit report"],"handler_or_flow":"process_file_retrieval_control_report","effect_boundary":"Reports local retrieval-control records; performs no retrieval.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.policy_status","route_source":"command_registry","route_name":"file_retrieval_policy_status","priority":17,"matcher_kind":"exact_or_alias","commands_or_patterns":["show file retrieval status","show retrieval policy"],"handler_or_flow":"process_file_retrieval_policy_status","effect_boundary":"Reports disabled retrieval policy; performs no retrieval.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.request_enablement","route_source":"command_registry","route_name":"file_retrieval_enablement_request","priority":18,"matcher_kind":"exact_or_alias","commands_or_patterns":["request file retrieval enablement","request retrieval enablement"],"handler_or_flow":"process_file_retrieval_enablement_request","effect_boundary":"Records local request metadata; does not enable retrieval.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"budget.set_limit","route_source":"command_registry","route_name":"budget_limit_update","priority":19,"matcher_kind":"parsed_parameter","commands_or_patterns":["set budget limit <amount>"],"handler_or_flow":"process_budget_limit_update","effect_boundary":"Updates the user's local budget policy.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_budget_policy.py"]},
  {"surface_id":"budget.set_warn_threshold","route_source":"command_registry","route_name":"budget_warn_threshold_update","priority":20,"matcher_kind":"parsed_parameter","commands_or_patterns":["set budget warn threshold <percent>"],"handler_or_flow":"process_budget_warn_threshold_update","effect_boundary":"Updates the user's local budget warning threshold.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_budget_policy.py"]},
  {"surface_id":"budget.set_block_threshold","route_source":"command_registry","route_name":"budget_block_threshold_update","priority":21,"matcher_kind":"parsed_parameter","commands_or_patterns":["set budget block threshold <percent>"],"handler_or_flow":"process_budget_block_threshold_update","effect_boundary":"Updates the user's local budget block threshold.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_budget_policy.py"]},
  {"surface_id":"retrieval_control.resolve_enablement_request","route_source":"command_registry","route_name":"file_retrieval_enablement_resolution","priority":22,"matcher_kind":"parsed_id_and_decision","commands_or_patterns":["approve retrieval enablement request <id>","reject retrieval enablement request <id>"],"handler_or_flow":"process_file_retrieval_enablement_request_resolution","effect_boundary":"Records a local decision; approval does not change retrieval policy.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"file_control.forget","route_source":"command_registry","route_name":"file_forget","priority":23,"matcher_kind":"parsed_id","commands_or_patterns":["forget file <id>"],"handler_or_flow":"process_file_forget","effect_boundary":"Marks retained local file metadata as forgotten.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.cancel_attempt","route_source":"command_registry","route_name":"file_retrieval_cancel","priority":24,"matcher_kind":"parsed_id","commands_or_patterns":["cancel file retrieval <id>"],"handler_or_flow":"process_file_retrieval_cancel","effect_boundary":"Cancels local retrieval-attempt metadata; performs no retrieval or external action.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"retrieval_control.preflight","route_source":"command_registry","route_name":"file_retrieval_preflight","priority":25,"matcher_kind":"parsed_id_or_prepare_pattern","commands_or_patterns":["retrieve file <id>","prepare file <id> for review"],"handler_or_flow":"process_file_retrieval_preflight","effect_boundary":"Records a disabled-policy preflight; does not retrieve or review file content.","evidence":["implemented","tested","documented"],"classification":"FREEZE_CANDIDATE","recommendation":"review_in_63P","test_refs":["tests/test_file_control.py"]},
  {"surface_id":"document_history.list","route_source":"command_registry","route_name":"document_listing","priority":26,"matcher_kind":"exact","commands_or_patterns":["what documents did you review"],"handler_or_flow":"process_document_listing","effect_boundary":"Lists local draft document-review records.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_document_control.py"]},
  {"surface_id":"document_history.forget","route_source":"command_registry","route_name":"document_forget","priority":27,"matcher_kind":"parsed_id","commands_or_patterns":["forget document <id>"],"handler_or_flow":"process_document_forget","effect_boundary":"Marks a local draft document-review record as forgotten.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_document_control.py"]},
  {"surface_id":"document_review.prepare","route_source":"command_registry","route_name":"document_review","priority":28,"matcher_kind":"parsed_prefix_and_text","commands_or_patterns":["review document: <text>","summarize document: <text>","mark risks in document: <text>","prepare notes from document: <text>"],"handler_or_flow":"process_document_review","effect_boundary":"Creates a local draft review; does not provide professional advice or external action.","evidence":["implemented","tested"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_document_review.py"]},
  {"surface_id":"memory_control.what_do_you_remember","route_source":"command_registry","route_name":"memory_listing","priority":29,"matcher_kind":"exact","commands_or_patterns":["what do you remember"],"handler_or_flow":"process_memory_listing","effect_boundary":"Lists active local approved memories.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py"]},
  {"surface_id":"memory_control.help","route_source":"command_registry","route_name":"memory_control_help","priority":30,"matcher_kind":"exact_or_alias","commands_or_patterns":["how do i control memory","memory help","what memory commands can i use","cómo controlo tu memoria","como controlo lo que recuerdas"],"handler_or_flow":"process_memory_control_help","effect_boundary":"Explains local memory controls; creates no memory or proposal.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py"]},
  {"surface_id":"memory_control.pending_proposals","route_source":"command_registry","route_name":"pending_memory_review","priority":31,"matcher_kind":"exact","commands_or_patterns":["what memory proposals are pending"],"handler_or_flow":"process_pending_memory_review","effect_boundary":"Lists pending local memory proposals, not active memories.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py"]},
  {"surface_id":"memory_control.forget","route_source":"command_registry","route_name":"memory_forget","priority":32,"matcher_kind":"parsed_id","commands_or_patterns":["forget memory <id>"],"handler_or_flow":"process_memory_forget","effect_boundary":"Marks an active local memory as forgotten.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py"]},
  {"surface_id":"memory_control.proposal_decision","route_source":"command_registry","route_name":"memory_decision","priority":33,"matcher_kind":"exact_or_alias","commands_or_patterns":["APPROVE","REJECT"],"handler_or_flow":"process_memory_decision","effect_boundary":"Approves the latest pending proposal into local memory or rejects it.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py","tests/test_telegram_webhook.py"]},
  {"surface_id":"telegram.attachment_intake","route_source":"orchestrator","route_name":null,"priority":null,"matcher_kind":"attachment","commands_or_patterns":["Telegram document attachment"],"handler_or_flow":"process_file_intake","effect_boundary":"Records local attachment metadata; does not download, parse, OCR, or review content.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_file_intake.py","tests/test_telegram_webhook.py"]},
  {"surface_id":"memory_proposal.explicit_intent","route_source":"orchestrator","route_name":null,"priority":null,"matcher_kind":"intent_extraction","commands_or_patterns":["Explicit memory-intent prefixes and profile patterns"],"handler_or_flow":"process_memory_proposal","effect_boundary":"Creates a ProposedMemory in PENDING state; does not create active memory without APPROVE.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_memory_control.py","tests/test_telegram_webhook.py"]},
  {"surface_id":"fallback.general_task","route_source":"orchestrator","route_name":null,"priority":null,"matcher_kind":"fallback","commands_or_patterns":["Any text not matched by an earlier route"],"handler_or_flow":"process_general_task","effect_boundary":"Processes the default local conversational task path.","evidence":["implemented","tested","documented"],"classification":"RUNTIME_CONTRACT","recommendation":"preserve","test_refs":["tests/test_telegram_webhook.py","tests/test_action_approval_packets.py"]}
]
```

## Routes intentionally outside the registry

- `telegram.attachment_intake` remains outside because it is attachment intake, not a text command.
- `memory_proposal.explicit_intent` remains outside because it is intent extraction, not an explicit command.
- `fallback.general_task` remains outside because it is the default non-command path.

These paths run after registered command dispatch, in the order listed above.

## Freeze candidates for Stage 63P

All surfaces with the `retrieval_control.` prefix are `FREEZE_CANDIDATE` entries for review in Stage 63P.

This audit does not decide which retrieval-control commands become runtime contract, internal/dev only, or deferred. Retrieval remains disabled and no audited surface performs live retrieval.

## Legacy, experimental, ambiguous, and blocked surfaces

No reachable command route is classified as `LEGACY_CANDIDATE`, `EXPERIMENTAL`, `INTERNAL_DEV_ONLY`, `AMBIGUOUS_REVIEW_REQUIRED`, or `BLOCKED` by this audit.

That absence is an audit result, not a permanent product decision. Historical or roadmap-only documentation is not runtime evidence.

## Boundary-sensitive surfaces

The following surfaces require particular care because their wording could be confused with external execution:

- `approval.action_approval_packet`
- `web.preflight`
- all `retrieval_control.*` surfaces
- `document_review.prepare`
- `memory_proposal.explicit_intent`

Their recorded effect boundaries are part of the current runtime evidence. They do not grant external authority.

## Non-claims

- no lead
- no CRM
- no pipeline
- no handoff
- no notificación
- no connectors
- no browser
- no email/WhatsApp
- no external writes

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git status --short`
