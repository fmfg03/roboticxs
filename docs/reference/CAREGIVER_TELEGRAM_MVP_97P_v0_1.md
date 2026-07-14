# Caregiver Telegram MVP v0

Status: 97P closed committed.

## Purpose

97P proves a narrow deterministic caregiver routine flow over the local Telegram runtime while preserving the 95P Telegram-Hermes policy chain and the 96P Hermes OS runtime contract.

The slice is local only. It prepares `CaregiverRoutinePacket` output, guided routine responses, bounded memory projection, approval-required escalation drafts, `PolicyTrace`, and `TaskRunRecord` evidence. It does not deliver messages or start live runtime infrastructure.

## Runtime Path

`Telegram update -> 95P policy chain -> bounded Memory Center projection -> 97P CaregiverRoutinePacket -> 96P Hermes OS packets -> local response`

97P uses the existing 95P chain before building caregiver output. Blocked medical or raw Hermes requests do not reach the Hermes adapter. Safe local routine prompts may reach only the local adapter stub.

## Actors

97P represents actors distinctly:

- care recipient
- approved caregiver
- owner/admin
- robot

Caregiver and owner/admin roles do not grant access to unrelated owner memory. Memory projection remains bounded, scoped, and non-authority.

## Allowed Local Behavior

- guide an approved routine label one step at a time
- accept simple local confirmations
- repeat a step or pause safely when the user is confused
- prepare an escalation draft for an approved caregiver/admin
- produce an approval-required Action Packet for escalation drafts
- expose local `PolicyTrace` and 96P `TaskRunRecord`

## Boundaries

- no live Telegram sends
- no automatic caregiver sends
- no hidden escalation
- no live Hermes Gateway startup
- no live cron scheduling
- no connector activation
- no external model provider calls
- no browser, email, or WhatsApp execution
- no external writes, payments, publishing, destructive actions, or production credential use
- no sensitive memory expansion
- no medical decisions
- no diagnosis
- no treatment advice
- no medication dosage, schedule, missed-dose, duplicate-dose, or medication-change advice
- no emergency monitoring claim

Medication reminders may reference an approved routine label only. Emergency-like language tells the human to contact local emergency services or a medical professional when immediate risk exists, and states that Roboticxs is not emergency monitoring.

## Implementation Notes

The implementation lives in `app/caregiver_telegram_mvp.py`.

The FastAPI route is `POST /api/telegram/caregiver-mvp/webhook`.

The route returns only deterministic local JSON and records no external effects.

## Validation

- `python3 -m pytest -q tests/test_caregiver_telegram_mvp_97p.py`
- `python3 -m pytest -q tests/test_telegram_policy_chain_95p.py tests/test_hermes_os_runtime_contract_96p.py`
- `python3 -m pytest -q tests/test_canonical_roadmap.py tests/test_roadmap_continuation_authorization_gate.py`
- `python3 -m pytest -q`
- `git diff --check`
