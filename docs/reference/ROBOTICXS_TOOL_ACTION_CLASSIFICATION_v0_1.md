# Roboticxs Tool Action Classification v0.1

Status: 92P implemented pending review.

This document defines the 92P action-class registry for proposed Hermes tool calls and actions. It is documentation/spec/test work only and does not implement a classifier or enforcement layer.

## Action class registry

| Action class | Meaning | Default decision |
| --- | --- | --- |
| `READ` | Read local or already-authorized context without changing state. | `ALLOW` |
| `SEARCH` | Search within allowed local or approved request-scoped sources. | `ALLOW` |
| `SUMMARIZE` | Summarize allowed input without changing state. | `ALLOW` |
| `CLASSIFY` | Classify allowed input without changing state. | `ALLOW` |
| `DRAFT` | Draft content or proposed changes without execution. | `ALLOW` |
| `ROUTE` | Route internally without external side effects. | `ALLOW` |
| `REMIND` | Prepare a reminder or local reminder draft. | `DRAFT_ONLY` |
| `SCHEDULE_SELF` | Prepare a personal schedule entry that remains local and user-controlled. | `DRAFT_ONLY` |
| `SEND_EXTERNAL_MESSAGE` | Send email, chat, DM, WhatsApp, SMS, or other external communication. | `ASK_CONFIRMATION` |
| `WRITE_EXTERNAL_RECORD` | Write to an external record, database, sheet, ticket, or system. | `ASK_CONFIRMATION` |
| `PUBLISH` | Publish content externally or make it public. | `ASK_CONFIRMATION` |
| `SCHEDULE_WITH_THIRD_PARTY` | Book, reserve, or schedule with another person or service. | `ASK_CONFIRMATION` |
| `MODIFY_CRM` | Create, update, score, assign, or advance CRM records. | `ASK_CONFIRMATION` |
| `PLACE_VISUAL_SIGNATURE` | Place a signature, stamp, approval mark, or identity-like visual marker. | `ASK_CONFIRMATION` |
| `PAY` | Execute payment, initiate charge, submit checkout, or move money. | `BLOCK` |
| `REFUND` | Issue refund, credit, reversal, or compensation. | `BLOCK` |
| `DELETE` | Delete records, files, accounts, content, or external data. | `BLOCK` |
| `CHANGE_CREDENTIALS` | Change passwords, keys, tokens, recovery methods, or authentication factors. | `BLOCK` |
| `CHANGE_PERMISSIONS` | Change access, roles, sharing, ACLs, or authorization settings. | `BLOCK` |
| `LEGAL_ACCEPT` | Accept terms, sign legally, waive rights, or bind the user legally. | `BLOCK` |
| `PRODUCTION_DEPLOY` | Deploy, release, migrate, or change production systems. | `BLOCK` |
| `DESTRUCTIVE_ACTION` | Irreversible, high-impact, or destructive action not otherwise covered. | `BLOCK` |
| `MEDICAL_DECISION` | Medical, medication, diagnosis, treatment, dosage, side-effect, or emergency decision. | `ESCALATE` |
| `LEGAL_DECISION` | Legal advice, legal judgment, or legal strategy decision. | `BLOCK` |
| `TAX_DECISION` | Tax advice, filing choice, tax position, or tax-liability decision. | `BLOCK` |
| `FINANCIAL_DECISION` | Investment, loan, insurance, trading, credit, or material financial decision. | `BLOCK` |
| `EMPLOYMENT_DECISION` | Hiring, firing, discipline, compensation, or employment-rights decision. | `BLOCK` |

## Classification rules

Safe local `READ`, `SEARCH`, `SUMMARIZE`, `CLASSIFY`, `DRAFT`, and `ROUTE` actions may be `ALLOW` only when the active skill, enabled package, user plan, source authorization, and Cost Governor all permit the action.

`REMIND` and `SCHEDULE_SELF` remain local/draft-only in v0 unless a later explicit scheduling authority is approved.

`SEND_EXTERNAL_MESSAGE`, `WRITE_EXTERNAL_RECORD`, `PUBLISH`, `SCHEDULE_WITH_THIRD_PARTY`, `MODIFY_CRM`, and `PLACE_VISUAL_SIGNATURE` require `ASK_CONFIRMATION` or stronger.

`PAY`, `REFUND`, `DELETE`, `CHANGE_CREDENTIALS`, `CHANGE_PERMISSIONS`, `LEGAL_ACCEPT`, `PRODUCTION_DEPLOY`, and `DESTRUCTIVE_ACTION` default to `BLOCK`.

`MEDICAL_DECISION`, `LEGAL_DECISION`, `TAX_DECISION`, `FINANCIAL_DECISION`, and `EMPLOYMENT_DECISION` are professional-decision classes and must not be executed by Hermes tools in v0.

Medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradiction must be classified as `MEDICAL_DECISION` and return `ESCALATE` or `BLOCK` under caregiver boundary.

When one proposed action fits multiple classes, choose the most restrictive decision.

## Non-claims

- no runtime classifier;
- no Hermes interception;
- no connector activation;
- no external action execution;
- no 93P or later authorization.
