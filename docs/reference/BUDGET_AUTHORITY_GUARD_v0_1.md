# Budget Authority Guard v0.1

## Purpose

Stage 65P defines budget as an authority surface for Roboticxs.

Budget authority means permission to consume bounded computational and paid-resource capacity. This stage adds a local guard taxonomy for model spend, long context, retries, tool calls, and future expensive task classes.

This document is a runtime-control reference. It does not add billing, subscriptions, provider reconciliation, connectors, live retrieval, browser execution, email, WhatsApp, CRM, lead-gen, handoff, payment, or external writes.

## Scope

65P adds a canonical local guard surface in `app/budget_authority.py`.

Existing monthly threshold and budget status behavior remains in `app/budget_policy.py`. That module continues to own current local estimated spend thresholds and budget commands. 65P does not stretch it into the new authority taxonomy.

## Decision Taxonomy

The guard returns one of these decisions:

```text
ALLOW
ALLOW_WITH_CAP
ASK_CONFIRMATION
DOWNGRADE_MODEL
DEFER
BLOCK
```

Decision meanings:

- `ALLOW`: task fits current budget authority policy.
- `ALLOW_WITH_CAP`: task may proceed only under local token, model, retry, or tool-call caps.
- `ASK_CONFIRMATION`: task may exceed normal budget authority or require premium resources.
- `DOWNGRADE_MODEL`: task should proceed with a cheaper adequate model unless premium use is confirmed.
- `DEFER`: task is parked because the approved stage or local budget authority does not justify execution now.
- `BLOCK`: task exceeds the allowed local boundary or asks for forbidden execution.

## Structured Result

Every evaluated task returns a structured result with:

```text
decision
task_class
reason
estimated_input_tokens
estimated_output_tokens
estimated_cost
model_tier
cap_applied
confirmation_required
blocked_reason
downgrade_target
retry_cap
tool_call_cap
```

The `estimated_cost` value is based on local estimates only, not billing truth. Roboticxs does not claim invoice accuracy, provider reconciliation, payment enforcement, subscription metering, tax correctness, or accounting correctness.

Allowed claim:

```text
Roboticxs tracks estimated local usage and applies budget guardrails before spending more model/tool resources.
```

## Default Policy

The default v0 policy is local and deterministic:

```json
{
  "policy_id": "default_budget_authority_policy_v0",
  "daily_estimated_cost_cap": 1.0,
  "monthly_estimated_cost_cap": 20.0,
  "premium_model_confirmation_threshold": 0.1,
  "long_context_confirmation_threshold_tokens": 24000,
  "default_retry_cap": 1,
  "default_tool_call_cap": 3,
  "blocked_tool_classes": [
    "EXTERNAL_WRITE",
    "CONNECTOR_EXECUTION",
    "LIVE_RETRIEVAL",
    "PAYMENT_EXECUTION"
  ],
  "allowed_modes": [
    "ECONOMY",
    "BALANCED",
    "PREMIUM_WITH_CONFIRMATION",
    "BYOK"
  ]
}
```

These values are guardrail defaults, not pricing promises.

## Deterministic Precedence

The guard evaluates decisions in this order:

1. Blocked tool classes always return `BLOCK`.
2. Future external skill classes return `BLOCK`.
3. Future staged classes return `DEFER`.
4. Retry cap reached returns `DEFER`.
5. Premium model or premium-cost escalation without confirmation returns `ASK_CONFIRMATION` or `DOWNGRADE_MODEL`.
6. Long context returns `ALLOW_WITH_CAP` unless separately confirmed in a future integration.
7. Tool-call cap exceeded returns `ALLOW_WITH_CAP`.
8. Estimated task cost over the local daily authority cap returns `BLOCK`.
9. Expensive document review returns `ASK_CONFIRMATION`.
10. Default task policy applies.

## Task Class Defaults

```text
GENERAL_TASK                    ALLOW_WITH_CAP
SIMPLE_CLASSIFICATION           ALLOW
MEMORY_PROPOSAL                 ALLOW_WITH_CAP
MEMORY_DECISION                 ALLOW
FILE_INTAKE                     ALLOW_WITH_CAP
DOCUMENT_REVIEW                 ASK_CONFIRMATION when long or expensive; otherwise ALLOW_WITH_CAP
ATTENTION_SUMMARY               ALLOW_WITH_CAP
ROBOT_FOLDER                    ALLOW_WITH_CAP
SUPER_FAMILIAR                  ALLOW_WITH_CAP
WEB_PREFLIGHT                   ALLOW_WITH_CAP
ACTION_APPROVAL_PACKET          ALLOW_WITH_CAP
RETRIEVAL_CONTROL               ALLOW local metadata only
USAGE_REPORTING                 ALLOW
CONVERSATION_CONTINUITY_FUTURE  DEFER
CAREGIVER_FUTURE                DEFER
VOICE_FUTURE                    DEFER
RESEARCH_RADAR_FUTURE           DEFER
EXTERNAL_SKILL_FUTURE           BLOCK unless separately approved later
```

## Premium Model Guard

Premium model use cannot silently `ALLOW`.

If a task requests a premium model tier, premium mode, or an estimated cost at or above the premium confirmation threshold, and confirmation is absent, the guard returns `ASK_CONFIRMATION` or `DOWNGRADE_MODEL`.

Current router `WARN` metadata is not authority approval.

User-facing copy should stay neutral:

```text
This looks like a premium-model task. I need confirmation before using that tier.
```

```text
Esto parece requerir un modelo premium. Necesito confirmación antes de usar ese nivel.
```

## Retry Guard

Retries are local policy decisions only in v0.

65P defines a default retry cap and reports repeated failure waste as budget pressure. It does not implement retry execution, background work, queues, or external retries.

User-facing copy:

```text
I stopped because the retry cap was reached. The next step is to simplify the task or approve another attempt.
```

```text
Me detuve porque se alcanzó el límite de reintentos. El siguiente paso es simplificar la tarea o aprobar otro intento.
```

## Tool-Call Guard

Tool calls are local policy decisions only in v0.

Local metadata/control commands may be evaluated by the guard. Blocked tool classes always return `BLOCK`:

```text
EXTERNAL_WRITE
CONNECTOR_EXECUTION
LIVE_RETRIEVAL
PAYMENT_EXECUTION
```

Tool-call placeholders do not authorize connector execution.

## Long Context Warning

If a task crosses the long-context threshold, the guard applies a cap or requires confirmation.

User-facing copy:

```text
This may require a long context window and higher model spend. I can continue in capped mode or wait for confirmation.
```

```text
Esto puede usar una ventana de contexto grande y subir el costo. Puedo hacerlo en modo limitado o esperar tu confirmación.
```

## Future Stage Guardrails

65P binds future stages without implementing them:

- CH-01 / `CONVERSATION_CONTINUITY_FUTURE` returns `DEFER`.
- Caregiver / `CAREGIVER_FUTURE` returns `DEFER`.
- Voice / `VOICE_FUTURE` returns `DEFER`.
- Research Radar / `RESEARCH_RADAR_FUTURE` returns `DEFER`.
- External skills / `EXTERNAL_SKILL_FUTURE` returns `BLOCK` unless separately approved later.

CH-01 cannot classify every message through expensive reasoning by default. Caregiver cannot run unlimited proactive checks. Voice cannot transcribe without budget caps. Research Radar cannot continuously scan the open web or sources. External skills cannot call tools without budget and tool-call caps.

## Non-Authorization

65P does not authorize:

- CH-01 behavior
- Caregiver behavior
- Voice processing
- Research Radar
- external skills
- connectors
- live retrieval
- browser execution
- email
- WhatsApp
- CRM
- lead-gen
- handoff
- payment
- external writes

65P does not authorize connector, browser, retrieval, email, WhatsApp, CRM, lead-gen, pipeline, payment, handoff, or external write execution through any budget decision.

## Validation

Required validation:

```bash
python3 -m compileall app tests
python3 -m pytest -q tests/test_budget_authority_guard.py
python3 -m pytest -q tests/test_canonical_roadmap.py
python3 -m pytest -q tests/test_runtime_surface_audit.py
python3 -m pytest -q tests/test_retrieval_control_freeze.py
python3 -m pytest -q
git diff -- app
git diff --check
git status --short
```
