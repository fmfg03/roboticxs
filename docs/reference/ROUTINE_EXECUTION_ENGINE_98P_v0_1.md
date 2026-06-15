# Routine Execution Engine Skeleton v0

Status: 98P closed committed.

## Purpose

98P proves that Roboticxs can represent and execute routines as local, deterministic, governed task runs without external side effects.

The skeleton builds on:

- 95P Telegram-Hermes policy chain runtime
- 96P Hermes OS runtime contract
- 97P Caregiver Telegram MVP slice

## Runtime Path

`RoutineDefinition -> Telegram update -> 95P policy chain -> 96P Hermes OS contract -> optional 97P caregiver packet -> RoutineRun -> local delivery object`

Policy-chain routing happens before Hermes OS packet binding. Blocked and approval-required actions do not reach the Hermes adapter.

## Local Packets

98P defines:

- `RoutineDefinition`
- `RoutineRun`
- `RoutinePreflight`
- `LocalRoutineDelivery`
- `RoutineAuditEvent`

Routine states are:

- pending
- running
- completed
- skipped
- needs_confirmation
- blocked
- failed

The skeleton records final states deterministically and includes preflight/audit trail evidence.

## Boundaries

- no live scheduler
- no live cron
- no live Telegram sends
- no automatic delivery
- no automatic caregiver alerts
- no hidden escalation
- no live Hermes Gateway startup
- no connector activation
- no external model provider calls
- no browser, email, or WhatsApp execution
- no external writes, payments, publishing, destructive actions, or production credential usage
- no medical decisions, diagnosis, treatment advice, medication changes, or emergency monitoring
- no sensitive memory expansion
- no silent routine installation or execution

## Validation

- `python3 -m pytest -q tests/test_routine_execution_engine_98p.py`
- `python3 -m pytest -q tests/test_telegram_policy_chain_95p.py tests/test_hermes_os_runtime_contract_96p.py tests/test_caregiver_telegram_mvp_97p.py`
- `python3 -m pytest -q tests/test_canonical_roadmap.py tests/test_roadmap_continuation_authorization_gate.py`
- `python3 -m pytest -q`
- `git diff --check`
