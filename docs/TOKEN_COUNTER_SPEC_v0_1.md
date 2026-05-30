# ROBOTICXS — Token Counter and Cost Governor Spec v0.1

> **Product:** Roboticxs.com  
> **Version:** v0.1  
> **Status:** MVP specification  
> **Purpose:** Track model usage, estimate and reconcile cost, enforce budgets, and make AI spend visible.  

---

## 1. Objective

Roboticxs must expose token and cost behavior from day one.

A personal robot should not have unlimited model-spend authority just because it can call an LLM.

The Token Counter and Cost Governor should answer:

- How much did this task cost?
- Which model was used?
- How much budget remains?
- Which tasks are expensive?
- How much waste comes from retries/failures?
- What savings came from routing?

---

## 2. User-Facing UX

Show:

- tokens used this month,
- estimated cost this month,
- cost by robot,
- most expensive tasks,
- model savings from routing,
- budget remaining,
- high-cost confirmation prompts.

Example messages:

> “I can do this in Economy Mode for about $0.02 or Premium Mode for about $0.15.”

> “This task may use a long context window. Estimated cost: $0.45. Continue?”

---

## 3. Data Entities

### TokenUsageEvent

Minimum fields:

```json
{
  "event_id": "tok_123",
  "user_id": "usr_123",
  "workspace_id": "ws_123",
  "robot_id": "rob_123",
  "task_id": "task_123",
  "task_run_id": "run_123",
  "route_id": "route_123",
  "provider": "openai",
  "model": "example-model",
  "task_class": "DRAFTING",
  "input_tokens": 1200,
  "cached_input_tokens": 0,
  "output_tokens": 350,
  "tool_call_count": 1,
  "retry_count": 0,
  "estimated_cost_usd": 0.013,
  "final_cost_usd": 0.012,
  "latency_ms": 2300,
  "status": "success",
  "failure_reason": null,
  "created_at": "2026-05-27T00:00:00Z"
}
```

### BudgetPolicy

```json
{
  "budget_policy_id": "budget_123",
  "user_id": "usr_123",
  "workspace_id": "ws_123",
  "robot_id": "rob_123",
  "plan": "pro",
  "monthly_soft_limit_usd": 25.00,
  "monthly_hard_limit_usd": 40.00,
  "per_task_confirmation_threshold_usd": 0.25,
  "per_task_hard_limit_usd": 2.00,
  "premium_route_confirmation_required": true,
  "long_context_confirmation_required": true,
  "enabled": true
}
```

### BudgetAlert

```json
{
  "alert_id": "alert_123",
  "budget_policy_id": "budget_123",
  "user_id": "usr_123",
  "robot_id": "rob_123",
  "type": "MONTHLY_SOFT_LIMIT_NEAR",
  "severity": "warning",
  "message": "You have used 80% of your monthly AI budget.",
  "created_at": "2026-05-27T00:00:00Z"
}
```

---

## 4. Cost Calculation

Cost estimate:

```text
estimated_cost =
  input_tokens_estimate * input_price
+ cached_input_tokens_estimate * cached_input_price
+ output_tokens_estimate * output_price
+ tool_cost_estimate
```

Actual cost:

```text
final_cost = provider_reported_usage if available
otherwise local_usage_estimate
```

Provider prices must live in a configurable `ModelCatalogEntry` table. Do not hardcode long-term pricing in code.

---

## 5. Budget Decisions

| State | Decision |
|---|---|
| Under threshold | Allow. |
| Above per-task confirmation threshold | Ask confirmation. |
| Above per-task hard limit | Block or ask user to split/reduce task. |
| Near monthly soft limit | Warn. |
| Above monthly soft limit | Ask confirmation for non-essential tasks. |
| Above monthly hard limit | Block paid-provider execution unless BYOK or admin override. |

---

## 6. Retry Waste Tracking

Retries are not free. Track waste from:

- provider failures,
- malformed structured output,
- safety rejections after model generation,
- unnecessary premium model use,
- repeated long-context calls.

Fields:

- `retry_count`,
- `retry_reason`,
- `wasted_input_tokens`,
- `wasted_output_tokens`,
- `wasted_cost_usd`,
- `recoverable_failure`,
- `provider_failure`,
- `prompt_failure`,
- `safety_failure`.

---

## 7. Routing Savings

Track what the router saved compared to default premium routing.

```json
{
  "route_id": "route_123",
  "selected_cost_usd": 0.02,
  "premium_baseline_cost_usd": 0.15,
  "estimated_savings_usd": 0.13,
  "savings_method": "economy_model_selected"
}
```

This supports user trust and internal margin analysis.

---

## 8. Cost Governor Flow

```text
task request
  → token estimate
  → route estimate
  → budget policy check
  → safety decision if budget is exceeded or sensitive
  → execute / ask / block
  → provider usage capture
  → cost reconciliation
  → dashboard update
```

---

## 9. Admin Dashboard Requirements

Admin must see:

- total cost by day/month,
- cost by user,
- cost by robot,
- cost by skill,
- cost by task class,
- cost by provider,
- cost by model,
- retry waste,
- expensive tasks,
- budget overrides,
- margin by plan.

---

## 10. User Dashboard Requirements

User must see:

- monthly usage,
- budget remaining,
- recent expensive tasks,
- active routing mode,
- estimated savings,
- alerts,
- optional BYOK setup.

---

## 11. MVP Acceptance Criteria

The token/cost layer is acceptable when:

1. Every model call creates a usage event.
2. Estimated cost is calculated before execution.
3. Actual usage is reconciled after execution where provider data is available.
4. Per-task confirmation threshold works.
5. Monthly soft and hard limits work.
6. Retry waste is tracked.
7. User can see monthly usage and budget remaining.
8. Admin can inspect cost by provider/model/task class.
