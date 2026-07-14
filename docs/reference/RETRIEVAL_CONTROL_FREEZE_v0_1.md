# Retrieval Control Freeze v0.1

## Purpose

Stage 63P freezes the retrieval-control surface audited in `RUNTIME_SURFACE_AUDIT_v0_1.md`.

The existing surface is a local metadata/control system. It records retrieval intent, enablement intent, local decisions, policy status, and control readouts. It does not retrieve, download, parse, OCR, review, or externally write file content.

This freeze preserves compatibility without allowing retrieval-control to expand by inertia.

## Taxonomy

Primary `freeze_classification` values for existing `retrieval_control.*` surfaces:

- `PRESERVE_LOCAL_CONTROL_ONLY`
- `FROZEN_VISIBLE_NOT_EXPANDABLE`
- `DEFERRED_CONNECTOR_ARCHITECTURE`

`BLOCKED_V0` is a global behavior-policy category, not a primary surface classification.

`RENAME_LATER` is a `rename_status`, not a primary surface classification. It records naming ambiguity without authorizing a rename or copy change.

## Structured freeze inventory

The structured inventory below is parsed by consistency tests. It contains only the ten `retrieval_control.*` Surface IDs audited in Stage 62P.

```json retrieval-control-freeze-inventory
[
  {"surface_id":"retrieval_control.pending_attempts","current_effect":"Lists local retrieval-attempt metadata and performs no retrieval.","freeze_classification":"PRESERVE_LOCAL_CONTROL_ONLY","visible_status":"VISIBLE","expansion_rule":"Preserve current local metadata readout only; no new commands, aliases, states, content access, or external effects.","rename_status":"RENAME_LATER","future_architecture_boundary":"Any real pending retrieval execution belongs to separately approved connector architecture.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.pending_enablement_requests","current_effect":"Lists pending local enablement-request metadata while retrieval remains disabled.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not add commands, aliases, states, flows, copy promises, or activation behavior.","rename_status":"RENAME_LATER","future_architecture_boundary":"Future connector authorization cannot inherit authority from these local request records.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.enablement_request_history","current_effect":"Reads local enablement-request history while retrieval remains disabled.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not expand history into connector, execution, credential, or external audit behavior.","rename_status":"RENAME_LATER","future_architecture_boundary":"Any connector authorization history requires a separate authority and audit model.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.summary","current_effect":"Summarizes local retrieval-control records and performs no retrieval.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not add new control families, states, aliases, or external-effect claims.","rename_status":"RENAME_LATER","future_architecture_boundary":"A future connector control plane must be designed separately and must not reuse this summary as authority.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.report","current_effect":"Reports local retrieval-control records and performs no retrieval.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not expand into external audit, connector status, or execution reporting.","rename_status":"RENAME_LATER","future_architecture_boundary":"Future connector audit receipts require separate architecture and evidence semantics.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.policy_status","current_effect":"Reports the local retrieval policy signal and performs no retrieval.","freeze_classification":"PRESERVE_LOCAL_CONTROL_ONLY","visible_status":"VISIBLE","expansion_rule":"Preserve current local policy readout only; no implementation-availability, connector, or execution-authority claims.","rename_status":"NONE","future_architecture_boundary":"Future connector availability and authority must be reported separately from this local policy signal.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.request_enablement","current_effect":"Records local enablement-intent metadata and does not enable retrieval.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not make requests activate config, connectors, credentials, retrieval, or external effects.","rename_status":"RENAME_LATER","future_architecture_boundary":"A future connector authorization request requires separate approval and authority semantics.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.resolve_enablement_request","current_effect":"Records a local approval or rejection decision; approval does not change retrieval policy.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not make approval activate policy, connectors, credentials, retrieval, or external effects.","rename_status":"RENAME_LATER","future_architecture_boundary":"Future connector activation requires a separate explicit authority gate and cannot inherit this local approval.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.cancel_attempt","current_effect":"Cancels local retrieval-attempt metadata and performs no retrieval or external action.","freeze_classification":"PRESERVE_LOCAL_CONTROL_ONLY","visible_status":"VISIBLE","expansion_rule":"Preserve current local cancellation control only; no connector cancellation, transport cancellation, or external effects.","rename_status":"RENAME_LATER","future_architecture_boundary":"Future execution cancellation requires separate connector lifecycle and authority semantics.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]},
  {"surface_id":"retrieval_control.preflight","current_effect":"Records disabled-policy preflight metadata and does not retrieve or review file content.","freeze_classification":"FROZEN_VISIBLE_NOT_EXPANDABLE","visible_status":"VISIBLE_COMPATIBILITY","expansion_rule":"Keep visible for compatibility; do not add download, parsing, OCR, review, connector, or execution behavior.","rename_status":"RENAME_LATER","future_architecture_boundary":"Any real retrieval or review requires separately approved connector and content-processing architecture.","test_evidence":["tests/test_file_control.py","tests/test_runtime_surface_audit.py"]}
]
```

No existing surface is classified `DEFERRED_CONNECTOR_ARCHITECTURE`. That classification is reserved for a future surface designed under a separately approved connector architecture.

## Blocked v0 behaviors

The following behavior-policy categories are `BLOCKED_V0`:

```json blocked-v0-behaviors
[
  "telegram_getfile_calls",
  "file_download",
  "pdf_parsing",
  "ocr",
  "raw_byte_storage",
  "extracted_content_storage",
  "content_review_without_content_access",
  "browser_retrieval",
  "connector_activation",
  "credential_or_cookie_handling",
  "external_writes",
  "local_intent_or_approval_as_execution_authority"
]
```

These are blocked behaviors, not classifications applied to existing visible surfaces.

## Deferred connector architecture

Real retrieval is deferred. It requires a separately approved architecture before any runtime implementation.

```json deferred-connector-requirements
[
  "connector_authorization_and_revocation",
  "credential_isolation",
  "explicit_user_confirmation_before_external_effects",
  "retrieval_execution_lifecycle",
  "content_retention_policy",
  "audit_receipts",
  "failure_and_retry_behavior",
  "provider_and_transport_boundaries",
  "authority_and_data_boundary_tests"
]
```

Current retrieval-control records are not connector authorization, execution authority, or proof that retrieval is available.

## Approval intent vs activation

The commands `request file retrieval enablement`, `approve retrieval enablement request <id>`, and `reject retrieval enablement request <id>` record local intent or a local decision only.

```json approval-intent-policy
{
  "request_meaning":"local_intent_record_only",
  "approval_meaning":"local_approval_pending_future_policy_change_only",
  "approval_status":"APPROVED_PENDING_POLICY_CHANGE",
  "denied_implications":[
    "does_not_enable_retrieval",
    "does_not_change_configuration",
    "does_not_authorize_connector",
    "does_not_authorize_credentials",
    "does_not_execute_retrieval",
    "does_not_grant_external_authority"
  ]
}
```

`APPROVED_PENDING_POLICY_CHANGE` is evidence of local intent, not activation authority.

## `live_retrieval_enabled` ambiguity

`Settings.file_retrieval_enabled` defaults to `False`. The mock-only adapter can report `live_retrieval_enabled=True` and `ENABLED_BY_POLICY` while also reporting `LIVE_RETRIEVAL_IMPLEMENTATION_NOT_AVAILABLE`.

```json live-retrieval-enabled-policy
{
  "meaning":"policy_or_configuration_signal_only",
  "default":false,
  "does_not_mean":[
    "implementation_available",
    "execution_authorized",
    "connector_active",
    "credentials_available",
    "retrieval_will_execute"
  ],
  "runtime_change_authorized_by_63P":false
}
```

This stage documents the ambiguity. It does not change configuration, adapter behavior, replies, commands, or runtime.

## Reopening rule

The freeze may be reopened only by a separately approved stage that identifies the affected Surface IDs, explains the authority and data boundaries, and explicitly approves any runtime, connector, config, schema, storage, command, alias, or copy change.

Bug fixes that preserve a `PRESERVE_LOCAL_CONTROL_ONLY` effect still require their own approved stage.

## Non-claims

- no retrieval execution
- no connectors
- no browser
- no email/WhatsApp
- no CRM
- no lead-gen
- no external writes
- no new product features

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_retrieval_control_freeze.py`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q tests/test_file_control.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git status --short`
