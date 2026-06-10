# Guided Routine Packets v0.1

## Purpose

Stage 69P defines a local Guided Routine Packet contract for Roboticxs.

Guided routines reduce cognitive load by preparing short, respectful, one-step-at-a-time scripts for caregiver-approved routines. A routine packet is a guided script, not proof that care happened.

Correct claim:

```text
Roboticxs can prepare caregiver-approved routine packets that guide one step at a time.
```

Forbidden claim:

```text
Roboticxs manages medications, verifies care, or supervises safety.
```

## Scope

69P adds a canonical local packet builder in `app/guided_routines.py`.

This stage prepares routine packets only. It does not schedule reminders, send Telegram messages, send automatic family alerts, execute caregiver actions, store durable routine progress, store sensitive caregiver memory, decide medications, decide dosage or schedule, verify ingestion, perform emergency triage, monitor the user, activate sensors, use voice input/output, activate connectors, use retrieval, open browser/email/WhatsApp, create CRM or lead-gen handoff, or perform external writes.

## Source Register

These sources inform the 69P boundary and routine-design principles. They are references only; they do not authorize clinical behavior.

| Source | Use in 69P |
| --- | --- |
| Alzheimer's Association - Daily Care Plan | Supports simple daily routine structure and caregiver planning boundaries. |
| Alzheimer's Association - Communication and Alzheimer's | Supports short, respectful, non-judgmental instructions. |
| Alzheimer's Association - Home Safety Tips | Supports blocking surveillance and safety-supervision claims. |
| NHS - Medicines: tips for carers | Supports caregiver-supervision boundaries for medication-adjacent help. |
| MedlinePlus - Keeping your medicines organized | Supports medication organization as caregiver-managed, not robot-decided. |
| MedlinePlus - Caregiving medication management | Supports blocking dosage, schedule, and ingestion-verification authority. |
| WHO - Assistive technology | Supports assistive framing without replacing human care. |

## Routine Packet Types

```text
HEARING_AID_ROUTINE
HYGIENE_ROUTINE
HYDRATION_OR_MEAL_ROUTINE
APPOINTMENT_PREPARATION_ROUTINE
HOUSEHOLD_SIMPLE_ROUTINE
CAREGIVER_APPROVED_CUSTOM_ROUTINE
MEDICATION_ADJACENT_CHECKLIST
BLOCKED_MEDICAL_ROUTINE
BLOCKED_SURVEILLANCE_ROUTINE
BLOCKED_EMERGENCY_ROUTINE
```

Allowed local routine packet types:

- `HEARING_AID_ROUTINE`
- `HYGIENE_ROUTINE`
- `HYDRATION_OR_MEAL_ROUTINE`
- `APPOINTMENT_PREPARATION_ROUTINE`
- `HOUSEHOLD_SIMPLE_ROUTINE`
- `CAREGIVER_APPROVED_CUSTOM_ROUTINE`

Medication-adjacent packet type:

- `MEDICATION_ADJACENT_CHECKLIST`

Medication-adjacent checklists are allowed only as supervision-only packet preparation. They require caregiver confirmation and caregiver supervision. They do not authorize medical decisioning, medication schedule management, dosage decisions, or ingestion verification.

Blocked packet types:

- `BLOCKED_MEDICAL_ROUTINE`
- `BLOCKED_SURVEILLANCE_ROUTINE`
- `BLOCKED_EMERGENCY_ROUTINE`

Blocked packet types produce safe blocked packets, not runtime behavior.

## Routine Decisions

```text
PREPARE_ROUTINE_PACKET
PREPARE_WITH_CAREGIVER_CONFIRMATION
PREPARE_MEDICATION_ADJACENT_CHECKLIST
DEFER_TO_CAREGIVER_RELAY
BLOCK_MEDICAL_DECISION
BLOCK_SURVEILLANCE
BLOCK_EMERGENCY
BLOCK_EXTERNAL_ACTION
```

Decision precedence is deterministic:

1. `external_action_requested=True` returns `BLOCK_EXTERNAL_ACTION`.
2. `surveillance_requested=True` returns `BLOCK_SURVEILLANCE`.
3. `emergency_like=True` returns `BLOCK_EMERGENCY`.
4. Medical, dosage, schedule, or ingestion-verification requests return `BLOCK_MEDICAL_DECISION`.
5. `medication_adjacent=True` returns `PREPARE_MEDICATION_ADJACENT_CHECKLIST`.
6. Caregiver context without approval returns `PREPARE_WITH_CAREGIVER_CONFIRMATION`.
7. Otherwise the request returns `PREPARE_ROUTINE_PACKET`.

## Packet Contract

Every routine packet contains:

```text
packet_id
routine_type
routine_decision
title
purpose
intended_user
caregiver_visibility
steps
current_step_index
max_steps
requires_caregiver_confirmation
requires_caregiver_supervision
medication_adjacent
sensitivity_level
session_only_progress
external_send_authorized
background_reminder_authorized
medical_decision_authorized
dosage_decision_authorized
medication_schedule_authorized
ingestion_verification_authorized
emergency_claim_authorized
surveillance_authorized
routine_completion_claim
handoff_relay_packet
blocked_reason
future_stage_required
created_at
```

All 69P packets preserve these invariants:

```text
external_send_authorized = false
background_reminder_authorized = false
medical_decision_authorized = false
dosage_decision_authorized = false
medication_schedule_authorized = false
ingestion_verification_authorized = false
emergency_claim_authorized = false
surveillance_authorized = false
session_only_progress = true
```

## Routine Step Contract

Every step contains:

```text
step_id
step_number
instruction
expected_response_type
requires_user_ack
requires_caregiver_confirmation
can_skip
safety_note
blocked_if
```

Allowed expected response types:

```text
ACK_ONLY
YES_NO
CAREGIVER_CONFIRMATION
FREE_TEXT_NOTE
NO_RESPONSE_REQUIRED
```

Step instructions must be short, concrete, one action at a time, non-judgmental, respectful, not infantilizing, and not clinical unless blocked or caregiver-confirmation gated.

## Default Routine Templates

Hearing aid routine:

```text
1. Please find your hearing aids.
2. Check that they are facing the right direction.
3. Put on the left hearing aid.
4. Put on the right hearing aid.
5. Tell me when you are done.
```

Hydration or meal routine:

```text
1. Please take your glass or meal.
2. Take one small sip or bite.
3. Put it somewhere safe.
4. Tell me when you are done.
```

Appointment preparation routine:

```text
1. Please check the appointment note.
2. Put the needed item in one place.
3. Ask your caregiver if anything is missing.
4. Tell me when you are ready.
```

Simple household routine:

```text
1. Let's do one small step.
2. Pick up the item in front of you.
3. Put it in its usual place.
4. Tell me when you are done.
```

Medication-adjacent checklist:

```text
1. A caregiver must confirm the approved medication list is present.
2. A caregiver must confirm the pillbox or container labels.
3. Follow the caregiver-approved list only.
4. Stop and ask the caregiver if anything is unclear.
```

Medication-adjacent steps require caregiver confirmation where applicable.

## 68P Handoff Boundary

69P may prepare a local 68P `CaregiverRelayPacket` when caregiver confirmation or handoff is needed.

Handoff cases include:

- medication-adjacent routine request;
- caregiver context present without approval;
- sensitive context present;
- emergency-like content;
- user asks for caregiver help.

The handoff packet is local only. No Telegram message is sent.

The handoff packet preserves 68P invariants:

```text
external_send_authorized = false
medical_decision_authorized = false
emergency_claim_authorized = false
routine_execution_authorized = false
```

## Memory Boundary

Routine progress is session-only. 69P does not create durable routine state, caregiver health context storage, medication schedule storage, automatic routine history, inference-as-confirmed-fact, or never-store retention.

Future durable routine memory requires a later approved stage.

## Non-Claims

- Roboticxs does not schedule reminders in 69P.
- Roboticxs does not send Telegram messages automatically in 69P.
- Roboticxs does not send automatic family alerts in 69P.
- Roboticxs does not store caregiver routine progress durably in 69P.
- Roboticxs does not store sensitive caregiver context durably in 69P.
- Roboticxs does not decide medication selection, dosage, schedule, substitution, or ingestion.
- Roboticxs does not verify medication ingestion as fact.
- Roboticxs does not provide emergency response or triage.
- Roboticxs does not continuously monitor the person.
- Roboticxs does not supervise safety.
- Roboticxs does not replace family or professional caregiving.
- Voice behavior is deferred to 70P or later approved stages.

## Validation

- `python3 -m compileall app tests`
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
