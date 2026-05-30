# ROBOTICXS — Model Router Spec v0.1

> **Product:** Roboticxs.com  
> **Version:** v0.1  
> **Status:** MVP specification  
> **Purpose:** Select the cheapest adequate model for each task while preserving quality, safety, latency, and budget constraints.  

---

## 1. Objective

Roboticxs should not use the most expensive model for every task.

The model router must select a provider/model based on:

- task class,
- required quality,
- context size,
- latency target,
- user plan,
- routing mode,
- budget policy,
- sensitivity level,
- provider availability,
- recent failures.

The product promise:

> “Your robot uses the right model for the task, not the most expensive one by default.”

---

## 2. Supported Providers

Initial abstraction should support:

- OpenAI,
- Anthropic,
- Google,
- OpenRouter,
- Nous Portal,
- NVIDIA NIM,
- local/open-source endpoints where feasible.

Provider support must sit behind one internal interface.

---

## 3. Routing Modes

| Mode | Purpose | Behavior |
|---|---|---|
| Economy | Minimize cost. | Use cheapest reliable model that passes task requirements. |
| Balanced | Default mode. | Optimize quality/cost/latency tradeoff. |
| Premium | Prioritize quality. | Use stronger model when task complexity justifies it. |
| BYOK | User pays provider directly. | Respect user-supplied provider/model preferences. |

---

## 4. Task Classes

| Task Class | Examples | Preferred Model Type |
|---|---|---|
| `SIMPLE_CLASSIFICATION` | tag, route, label, priority | cheapest reliable small model |
| `EXTRACTION` | pull fields, summarize structured docs | low/mid-cost model |
| `DRAFTING` | emails, posts, replies | mid-cost model |
| `RESEARCH` | multi-source synthesis | mid/high model depending on depth |
| `REASONING` | planning, tradeoffs, complex analysis | higher model |
| `TOOL_PLANNING` | multi-step tool use | reliable agent-capable model |
| `SENSITIVE_REVIEW` | legal/finance/admin sensitive review | higher model + disclaimer + escalation |
| `LONG_CONTEXT` | large docs/history | long-context cost-optimized model |
| `CREATIVE` | content ideas, brand language | model selected by style quality |

---

## 5. Router Input

```json
{
  "user_id": "usr_123",
  "workspace_id": "ws_123",
  "robot_id": "rob_123",
  "task_id": "task_123",
  "skill_id": "documents_review",
  "task_class": "SENSITIVE_REVIEW",
  "routing_mode": "balanced",
  "input_token_estimate": 18000,
  "output_token_estimate": 1800,
  "requires_long_context": true,
  "requires_tool_use": false,
  "sensitivity_level": "medium",
  "latency_target_ms": 20000,
  "quality_floor": "high",
  "budget_policy_id": "budget_123",
  "user_model_preferences": {
    "preferred_provider": null,
    "blocked_providers": [],
    "byok_enabled": false
  }
}
```

---

## 6. Router Output

```json
{
  "route_id": "route_123",
  "decision": "SELECTED",
  "provider": "openai",
  "model": "example-model",
  "routing_mode": "balanced",
  "estimated_input_tokens": 18000,
  "estimated_output_tokens": 1800,
  "estimated_cost_usd": 0.42,
  "estimated_latency_ms": 16000,
  "reason_code": "LONG_CONTEXT_HIGH_QUALITY_BALANCED",
  "alternatives": [
    {
      "provider": "provider_b",
      "model": "cheaper-model",
      "estimated_cost_usd": 0.18,
      "rejected_reason": "quality_floor_not_met"
    }
  ],
  "requires_user_confirmation": true,
  "confirmation_reason": "HIGH_COST_ROUTE_REQUIRES_CONFIRMATION"
}
```

---

## 7. Model Catalog Entry

Each model must be stored in a catalog.

```json
{
  "provider": "openai",
  "model": "example-model",
  "display_name": "Example Model",
  "enabled": true,
  "supports_tools": true,
  "supports_vision": true,
  "supports_pdf": false,
  "supports_json_mode": true,
  "max_context_tokens": 128000,
  "input_cost_per_million_tokens_usd": 0.0,
  "cached_input_cost_per_million_tokens_usd": 0.0,
  "output_cost_per_million_tokens_usd": 0.0,
  "latency_tier": "medium",
  "quality_tiers": ["drafting", "reasoning", "sensitive_review"],
  "risk_notes": "Use actual provider pricing in production."
}
```

Pricing must be configurable because provider prices change.

---

## 8. Selection Logic

### Step 1 — Classify Task

The system maps request into `task_class`.

### Step 2 — Determine Requirements

Requirements include:

- context length,
- output length,
- tool use,
- structured output,
- vision/PDF support,
- sensitivity level,
- latency target,
- minimum quality.

### Step 3 — Filter Candidate Models

Remove models that fail hard requirements:

- disabled,
- insufficient context,
- unavailable provider,
- missing required capability,
- blocked by user,
- blocked by plan,
- blocked by budget.

### Step 4 — Score Candidates

Candidate score should combine:

- estimated cost,
- expected quality,
- latency,
- failure rate,
- task fit,
- routing mode preference.

### Step 5 — Apply Budget Governor

If estimated cost exceeds threshold:

- ask confirmation,
- offer cheaper alternative,
- reduce context,
- summarize first,
- block if over hard limit.

### Step 6 — Execute and Log

Every route produces a `ModelRouteDecision` and `TokenUsageEvent`.

---

## 9. Cost Confirmation Rules

Ask user before proceeding when:

- task estimated cost exceeds user threshold,
- task uses long context,
- premium route selected,
- retry would create high waste,
- user is close to monthly budget.

Example:

> “This document is large. Balanced Mode should cost about $0.42. Economy Mode should cost about $0.18 but may miss nuance. Continue with Balanced?”

---

## 10. Fallback Behavior

When selected model fails:

1. Retry once when safe and cheap.
2. Fail over to next compatible provider/model.
3. Log retry cost as waste.
4. Avoid retry storms.
5. Ask user before expensive retry.

---

## 11. Admin Requirements

Admin must see:

- model catalog,
- enabled/disabled providers,
- provider health,
- cost table,
- route decisions,
- task-level model usage,
- cost by task class,
- retry waste,
- model failure rates,
- margin by plan.

---

## 12. MVP Acceptance Criteria

The router is acceptable when:

1. It supports at least two providers behind a common interface.
2. It can route simple classification to a cheaper model.
3. It can route document review to a stronger/long-context model.
4. It estimates cost before execution.
5. It asks confirmation above threshold.
6. It logs route decisions and actual usage.
7. It supports Economy, Balanced, Premium, and BYOK modes at the policy level, even if not all are fully exposed in UI.
