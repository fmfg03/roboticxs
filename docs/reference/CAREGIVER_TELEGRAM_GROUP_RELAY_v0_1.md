# Caregiver Telegram Group Relay v0.1

## Purpose

Stage 68P defines a local caregiver relay packet contract for Roboticxs.

The relay exists to coordinate humans, not replace them. Roboticxs can prepare caregiver-visible relay messages for human review and confirmation. It does not monitor the person and alert family automatically.

## Scope

68P adds a canonical local guard surface in `app/caregiver_relay.py`.

This stage prepares relay packets only. It does not send Telegram messages, manage Telegram groups, execute caregiver routines, decide medications, perform emergency triage, monitor the user, store durable sensitive caregiver memory, activate connectors, use retrieval, open browser/email/WhatsApp, create CRM or lead-gen handoff, or perform external writes.

## Relay Packet Types

```text
CAREGIVER_STATUS_NOTE
CAREGIVER_CONFIRMATION_REQUEST
ROUTINE_NEEDS_ATTENTION_DRAFT
CAREGIVER_HANDOFF_DRAFT
SENSITIVE_CONTEXT_REVIEW_REQUEST
BLOCKED_MEDICAL_REQUEST_NOTICE
BLOCKED_SURVEILLANCE_NOTICE
BLOCKED_EXTERNAL_ACTION_NOTICE
```

Allowed local preparation in 68P:

- `CAREGIVER_STATUS_NOTE`
- `CAREGIVER_CONFIRMATION_REQUEST`
- `ROUTINE_NEEDS_ATTENTION_DRAFT`
- `CAREGIVER_HANDOFF_DRAFT`
- `SENSITIVE_CONTEXT_REVIEW_REQUEST`

Blocked or notice-only packet types:

- `BLOCKED_MEDICAL_REQUEST_NOTICE`
- `BLOCKED_SURVEILLANCE_NOTICE`
- `BLOCKED_EXTERNAL_ACTION_NOTICE`

Blocked packet types produce a safe notice. They do not execute the blocked action.

## Relay Decisions

```text
PREPARE_DRAFT
ASK_CAREGIVER_CONFIRMATION
REDACT_AND_PREPARE
ESCALATE_TO_HUMAN_CAREGIVER
BLOCK_MEDICAL
BLOCK_SURVEILLANCE
BLOCK_EXTERNAL_ACTION
DEFER_TO_GUIDED_ROUTINE_PACKETS
```

Decision precedence is deterministic:

1. `external_action_requested=True` returns `BLOCK_EXTERNAL_ACTION`.
2. `surveillance_requested=True` returns `BLOCK_SURVEILLANCE`.
3. `medical_decision_requested=True` returns `BLOCK_MEDICAL`.
4. `emergency_like=True` returns `ESCALATE_TO_HUMAN_CAREGIVER`.
5. `routine_execution_requested=True` returns `DEFER_TO_GUIDED_ROUTINE_PACKETS`.
6. `medication_adjacent=True` returns `ASK_CAREGIVER_CONFIRMATION`.
7. `sensitive_context_present=True` or `never_store_or_share=True` returns `REDACT_AND_PREPARE`.
8. Otherwise the request returns `PREPARE_DRAFT`.

## Packet Contract

Every relay packet contains:

```text
packet_id
packet_type
relay_decision
source_robot_id
target_context
caregiver_visibility
summary
requested_human_action
sensitivity_level
requires_confirmation
external_send_authorized
medical_decision_authorized
emergency_claim_authorized
routine_execution_authorized
redaction_required
blocked_reason
future_stage_required
created_at
```

All 68P packets preserve these invariants:

```text
external_send_authorized = false
medical_decision_authorized = false
emergency_claim_authorized = false
routine_execution_authorized = false
```

## Target Contexts

Allowed target contexts for packet preparation:

```text
CAREGIVER_ROBOT
FAMILY_GROUP_DRAFT
HUMAN_CAREGIVER_REVIEW
SESSION_ONLY
```

Blocked target behavior:

```text
AUTO_SEND_TO_GROUP
AUTO_SEND_TO_CAREGIVER
AUTO_ALERT_EMERGENCY
AUTO_CONTACT_THIRD_PARTY
```

68P may prepare drafts for human review, but must not send them.

## Sensitive Content Handling

Sensitive caregiver content includes health status, cognitive impairment notes, medication-adjacent details, family supervision notes, distress, confusion, wandering, fall or emergency-like language, private family context, and caregiver burden or conflict.

Rules:

- Sensitive context must be labeled.
- Sensitive context must not be broadcast automatically.
- Sensitive context may require redaction.
- Sensitive context may require caregiver confirmation.
- Never-store data is session-only and must not appear in relay drafts except as a blocked or redacted notice.
- No durable sensitive caregiver memory is created in 68P.

## Boundary Examples

Allowed neutral summary:

```text
Caregiver review may be needed.
```

Medication-adjacent uncertainty:

```text
Medication-adjacent uncertainty was reported. A human caregiver should verify using the approved process.
```

Emergency-like language:

```text
This looks emergency-like. Contact a human caregiver or emergency services.
```

Surveillance request:

```text
This request is blocked because continuous monitoring is outside Roboticxs v0.
```

Forbidden claims:

```text
Medication was taken.
The person is safe.
Emergency handled.
Monitoring active.
Alert sent.
```

## Future Telegram Boundary

Future Telegram integration may consume these packets only after a later approved story and technical spec. 68P does not authorize actual Telegram sending, Telegram group membership management, automatic caregiver alerts, emergency notifications, caregiver routine execution, medication reminders, voice intake, background monitoring, sensors, connectors, retrieval, browser/email/WhatsApp, CRM, lead-gen, handoff, or external writes.

Guided Routine Packets are deferred to 69P.

## Non-Claims

- Roboticxs does not send Telegram messages automatically in 68P.
- Roboticxs does not manage Telegram groups in 68P.
- Roboticxs does not execute caregiver routines in 68P.
- Roboticxs does not decide medication dosage, schedule, ingestion, or treatment.
- Roboticxs does not provide emergency response or triage.
- Roboticxs does not continuously monitor the person.
- Roboticxs does not contact family members automatically.
- Roboticxs does not store sensitive caregiver context durably in 68P.

## Validation

- `python3 -m compileall app tests`
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
