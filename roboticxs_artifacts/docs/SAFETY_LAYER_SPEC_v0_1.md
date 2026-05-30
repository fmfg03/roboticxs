# ROBOTICXS — Lightweight Safety Layer Spec v0.1

> **Product:** Roboticxs.com  
> **Version:** v0.1  
> **Status:** MVP specification  
> **Purpose:** Prevent the personal robot from doing prohibited or sensitive actions without explicit boundaries.  

---

## 1. Objective

Roboticxs needs a lightweight action-boundary layer from the start.

The goal is not to expose enterprise governance. The goal is to stop the robot from silently doing things that users, families, professionals, or small businesses should explicitly approve.

The consumer-facing promise:

> “Tú decides qué puede hacer tu robot. Las acciones sensibles requieren confirmación.”

---

## 2. Design Principles

1. **Draft before execution.** The robot can prepare work before it can act externally.
2. **Confirm sensitive actions.** External messages, record updates, publication, scheduling with others, and customer-facing changes need confirmation.
3. **Block prohibited actions.** Payments, refunds, account deletion, credential changes, legal acceptance, and professional decisions are blocked by default.
4. **Keep language simple.** Do not expose SAL, DSSE, deterministic policy, or enterprise governance terms to consumers.
5. **Treat budget as authority.** Model spend is an action surface. The robot cannot spend unlimited tokens silently.
6. **Keep logs.** Every safety decision must be inspectable by admin and, where useful, visible to the user.

---

## 3. Decision Types

| Decision | Meaning | Example UX |
|---|---|---|
| `ALLOW` | Safe to complete inside current limits. | “Done.” |
| `DRAFT_ONLY` | Robot may prepare but not execute externally. | “I prepared the draft. Review it before sending.” |
| `ASK_CONFIRMATION` | Robot must ask before continuing. | “This sends an external message. Confirm before I send it.” |
| `ESCALATE` | Requires human/professional review or higher workflow. | “This needs review before action. I can prepare a checklist.” |
| `BLOCK` | Action cannot be performed. | “This action is blocked by your robot limits.” |

---

## 4. Action Classes

### Allowed by Default

- `READ`
- `SEARCH_APPROVED_CONTEXT`
- `CLASSIFY`
- `SUMMARIZE`
- `DRAFT`
- `DRAFT_NOTIFY`
- `REMIND`
- `ROUTE`
- `PREPARE`
- `SUGGEST`

### Confirmation Required by Default

- `SEND_NOTIFY`
- `WRITE_EXTERNAL_RECORD`
- `SCHEDULE_WITH_THIRD_PARTY`
- `PUBLISH`
- `MODIFY_CRM_FIELD`
- `CREATE_CUSTOMER_FACING_DOCUMENT`
- `STORE_NEW_MEMORY`
- `USE_SENSITIVE_MEMORY`
- `HIGH_COST_MODEL_ROUTE`

### Blocked by Default

- `PAY`
- `REFUND`
- `DELETE_ACCOUNT`
- `DELETE_EXTERNAL_RECORD`
- `CHANGE_CREDENTIAL`
- `CHANGE_PERMISSION`
- `CHANGE_VENDOR_BANK_DETAILS`
- `LEGAL_ACCEPTANCE`
- `TAX_DECISION`
- `FINANCIAL_DECISION`
- `MEDICAL_DECISION`
- `EMPLOYMENT_DECISION`
- `PRODUCTION_DEPLOYMENT`
- `DESTRUCTIVE_ACTION`

---

## 5. Safety Check Input

Every proposed action should be normalized into an action envelope.

```json
{
  "user_id": "usr_123",
  "workspace_id": "ws_123",
  "robot_id": "rob_123",
  "task_id": "task_123",
  "skill_id": "documents_review",
  "source_channel": "telegram",
  "requested_action": "send reviewed NDA comments to Victor",
  "action_class": "SEND_NOTIFY",
  "target_system": "email",
  "target_recipient_type": "external_contact",
  "uses_memory": true,
  "uses_sensitive_memory": false,
  "estimated_cost_usd": 0.08,
  "user_confirmed": false,
  "skill_manifest_version": "0.1",
  "timestamp": "2026-05-27T00:00:00Z"
}
```

---

## 6. Safety Check Output

```json
{
  "decision": "ASK_CONFIRMATION",
  "reason_code": "EXTERNAL_MESSAGE_REQUIRES_CONFIRMATION",
  "user_message": "I can draft this, but I need your confirmation before sending it to Victor.",
  "allowed_next_actions": ["DRAFT_ONLY", "ASK_USER_CONFIRMATION"],
  "log_level": "info",
  "requires_user_confirmation": true,
  "blocked": false
}
```

---

## 7. Reason Codes

### Allow

- `IN_SCOPE_LOW_RISK`
- `READ_ONLY_APPROVED_CONTEXT`
- `DRAFT_ONLY_ALLOWED`
- `SUMMARY_ALLOWED`
- `REMINDER_ALLOWED`

### Confirmation

- `EXTERNAL_MESSAGE_REQUIRES_CONFIRMATION`
- `EXTERNAL_RECORD_CHANGE_REQUIRES_CONFIRMATION`
- `PUBLISH_REQUIRES_CONFIRMATION`
- `THIRD_PARTY_SCHEDULING_REQUIRES_CONFIRMATION`
- `MEMORY_WRITE_REQUIRES_APPROVAL`
- `SENSITIVE_MEMORY_USE_REQUIRES_CONFIRMATION`
- `HIGH_COST_ROUTE_REQUIRES_CONFIRMATION`

### Escalate

- `PROFESSIONAL_REVIEW_RECOMMENDED`
- `LEGAL_OR_CONTRACTUAL_INTERPRETATION`
- `FINANCIAL_OR_TAX_COMPLEXITY`
- `EMPLOYMENT_OR_HR_RISK`
- `HIGH_IMPACT_BUSINESS_WORKFLOW`

### Block

- `PAYMENT_EXECUTION_BLOCKED`
- `REFUND_EXECUTION_BLOCKED`
- `ACCOUNT_DELETION_BLOCKED`
- `CREDENTIAL_CHANGE_BLOCKED`
- `PERMISSION_CHANGE_BLOCKED`
- `LEGAL_ACCEPTANCE_BLOCKED`
- `PROFESSIONAL_DECISION_BLOCKED`
- `DESTRUCTIVE_ACTION_BLOCKED`
- `OUT_OF_SCOPE_SKILL_REQUEST`
- `BUDGET_LIMIT_EXCEEDED`

---

## 8. Memory Boundary Rules

The robot may propose memory. It must not silently store durable memory from source scans unless the user explicitly approves.

### Memory Decision Types

- `PROPOSE_MEMORY`
- `APPROVE_MEMORY`
- `EDIT_MEMORY`
- `REJECT_MEMORY`
- `FORGET_MEMORY`
- `PIN_MEMORY`
- `MARK_OUTDATED`
- `ASK_BEFORE_USING`
- `NEVER_USE_FOR_DECISIONS`

### Default Rule

```text
temporary scan → extracted context → proposed memories → user approval → durable memory
```

---

## 9. Budget Boundary Rules

The robot must check budget before expensive routes.

Ask confirmation when:

- estimated task cost exceeds user threshold,
- monthly budget remaining is low,
- long-context task is required,
- premium route is selected while economy route exists,
- retry count creates waste.

Block when:

- user budget is exhausted,
- workspace budget is exhausted,
- provider cap is reached,
- task is likely to exceed hard cost ceiling.

---

## 10. Skill Scope Interaction

Safety layer depends on skill manifest scope.

```text
User request
  → skill scope classifier
  → action-class mapper
  → budget check
  → safety decision
  → response or execution
```

A request can be technically safe but still out of skill scope. In that case, the scope guard decides whether to redirect, offer upgrade, refuse scope, or block.

---

## 11. User-Facing Language

### Good

- “I can draft this, but I need your confirmation before sending.”
- “This changes an external record. Confirm before I continue.”
- “I cannot execute payments. I can prepare a payment checklist.”
- “This action is blocked by your robot limits.”
- “This looks like a business workflow. Agentius can turn it into a governed workflow.”

### Avoid

- “SAL policy blocked this.”
- “DSSE signing is required.”
- “The deterministic authority layer denied execution.”
- “This failed conformity requirements.”

---

## 12. Logging Requirements

Every decision must create a `SafetyDecision` event.

Minimum fields:

- decision ID,
- user ID,
- workspace ID,
- robot ID,
- task ID,
- skill ID,
- action class,
- decision,
- reason code,
- target system,
- estimated cost,
- confirmation state,
- timestamp,
- model route ID if applicable,
- raw request hash or reference,
- user-facing message.

---

## 13. MVP Acceptance Criteria

The safety layer is acceptable when:

1. It blocks default prohibited actions.
2. It requires confirmation for external messages and external writes.
3. It prevents durable memory writes without approval.
4. It blocks or asks before high-cost routes.
5. It produces simple consumer-facing explanations.
6. It logs all decisions.
7. It does not expose enterprise Zaubern vocabulary in consumer UX.
