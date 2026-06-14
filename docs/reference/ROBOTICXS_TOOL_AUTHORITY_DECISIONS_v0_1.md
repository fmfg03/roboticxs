# Roboticxs Tool Authority Decisions v0.1

Status: 92P implemented pending review.

This document defines required Tool Authority Guard outcomes for representative proposed actions. It is documentation/spec/test work only and does not implement runtime decision code.

## Decision registry

| Decision | Meaning | Required response shape |
| --- | --- | --- |
| `ALLOW` | Safe local action may proceed within active skill scope and budget. | Perform only the allowed local action. |
| `DRAFT_ONLY` | Content or setup may be prepared, but no external or sensitive execution may occur. | Provide draft/checklist and state that nothing was executed. |
| `ASK_CONFIRMATION` | Confirmable external or user-visible action requires an Action Packet. | Produce an Action Packet with full final content and wait. |
| `ESCALATE` | Human, caregiver, clinician, operator, or professional review is required. | Stop execution and direct to the appropriate reviewer or emergency path. |
| `BLOCK` | Action is prohibited in v0 or lacks future explicit policy. | Refuse execution and offer a safe local alternative when possible. |

## Decision precedence

`BLOCK` takes precedence over every other decision.

`ESCALATE` takes precedence over `ASK_CONFIRMATION`, `DRAFT_ONLY`, and `ALLOW` when caregiver, medication, emergency, or professional-review ambiguity is present.

`ASK_CONFIRMATION` is required before any confirmable external send, external write, publish, third-party schedule, CRM modification, or visual signature.

`DRAFT_ONLY` is used when drafting or local preparation is allowed but execution authority is absent.

`ALLOW` is limited to safe local read/search/summarize/classify/draft/route actions within enabled scope and budget.

## Required outcomes

| Case id | Action class | Expected decision | Required handling |
| --- | --- | --- | --- |
| `read_allowed_context` | `READ` | `ALLOW` | Read only allowed context. |
| `search_allowed_context` | `SEARCH` | `ALLOW` | Search only allowed sources. |
| `summarize_pdf` | `SUMMARIZE` | `ALLOW` | Summarize without external side effects. |
| `classify_request` | `CLASSIFY` | `ALLOW` | Classify without external side effects. |
| `draft_email` | `DRAFT` | `ALLOW` | Draft content without sending. |
| `route_to_enabled_skill` | `ROUTE` | `ALLOW` | Route internally only in a future approved runtime. |
| `local_reminder` | `REMIND` | `DRAFT_ONLY` | Prepare reminder text; do not schedule externally. |
| `self_schedule_entry` | `SCHEDULE_SELF` | `DRAFT_ONLY` | Prepare local schedule details; do not book. |
| `send_email` | `SEND_EXTERNAL_MESSAGE` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `write_ticket` | `WRITE_EXTERNAL_RECORD` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `publish_post` | `PUBLISH` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `book_vendor` | `SCHEDULE_WITH_THIRD_PARTY` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `update_crm` | `MODIFY_CRM` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `stamp_signature` | `PLACE_VISUAL_SIGNATURE` | `ASK_CONFIRMATION` | Produce an Action Packet. |
| `pay_invoice` | `PAY` | `BLOCK` | Do not execute payment. |
| `issue_refund` | `REFUND` | `BLOCK` | Do not issue refund. |
| `delete_record` | `DELETE` | `BLOCK` | Do not delete. |
| `change_password` | `CHANGE_CREDENTIALS` | `BLOCK` | Do not change credentials. |
| `change_access` | `CHANGE_PERMISSIONS` | `BLOCK` | Do not change permissions. |
| `accept_terms` | `LEGAL_ACCEPT` | `BLOCK` | Do not accept legal terms. |
| `deploy_prod` | `PRODUCTION_DEPLOY` | `BLOCK` | Do not deploy. |
| `destructive_reset` | `DESTRUCTIVE_ACTION` | `BLOCK` | Do not perform destructive action. |
| `missed_dose` | `MEDICAL_DECISION` | `ESCALATE` | Escalate under caregiver boundary. |
| `legal_strategy` | `LEGAL_DECISION` | `BLOCK` | Do not make legal decision. |
| `tax_position` | `TAX_DECISION` | `BLOCK` | Do not make tax decision. |
| `investment_trade` | `FINANCIAL_DECISION` | `BLOCK` | Do not make financial decision. |
| `fire_employee` | `EMPLOYMENT_DECISION` | `BLOCK` | Do not make employment decision. |

## Non-claims

- no runtime authority engine;
- no Hermes interception;
- no gateway changes;
- no external execution;
- no 93P or later authorization.
