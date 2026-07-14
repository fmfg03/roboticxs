from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_TOOL_AUTHORITY_DECISIONS_v0_1.md"
)
GUARD_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1.md"
)
CLASSIFICATION_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_TOOL_ACTION_CLASSIFICATION_v0_1.md"
)


def read_92p_docs() -> str:
    return "\n".join(
        [
            DECISIONS_DOC.read_text(),
            GUARD_DOC.read_text(),
            CLASSIFICATION_DOC.read_text(),
        ]
    )


def test_tool_authority_decision_registry_is_complete():
    text = DECISIONS_DOC.read_text()

    assert DECISIONS_DOC.is_file()
    for decision in [
        "| `ALLOW` |",
        "| `DRAFT_ONLY` |",
        "| `ASK_CONFIRMATION` |",
        "| `ESCALATE` |",
        "| `BLOCK` |",
    ]:
        assert decision in text


def test_block_and_escalate_precedence_is_explicit():
    text = DECISIONS_DOC.read_text()

    for required in [
        "`BLOCK` takes precedence over every other decision.",
        "`ESCALATE` takes precedence over `ASK_CONFIRMATION`, `DRAFT_ONLY`, and `ALLOW` when caregiver, medication, emergency, or professional-review ambiguity is present.",
        "`ASK_CONFIRMATION` is required before any confirmable external send, external write, publish, third-party schedule, CRM modification, or visual signature.",
        "`ALLOW` is limited to safe local read/search/summarize/classify/draft/route actions within enabled scope and budget.",
    ]:
        assert required in text


def test_required_sensitive_actions_block_or_escalate():
    text = read_92p_docs()

    for row in [
        "| `pay_invoice` | `PAY` | `BLOCK` |",
        "| `issue_refund` | `REFUND` | `BLOCK` |",
        "| `delete_record` | `DELETE` | `BLOCK` |",
        "| `change_password` | `CHANGE_CREDENTIALS` | `BLOCK` |",
        "| `change_access` | `CHANGE_PERMISSIONS` | `BLOCK` |",
        "| `accept_terms` | `LEGAL_ACCEPT` | `BLOCK` |",
        "| `deploy_prod` | `PRODUCTION_DEPLOY` | `BLOCK` |",
        "| `destructive_reset` | `DESTRUCTIVE_ACTION` | `BLOCK` |",
        "| `missed_dose` | `MEDICAL_DECISION` | `ESCALATE` |",
        "| `legal_strategy` | `LEGAL_DECISION` | `BLOCK` |",
        "| `tax_position` | `TAX_DECISION` | `BLOCK` |",
        "| `investment_trade` | `FINANCIAL_DECISION` | `BLOCK` |",
        "| `fire_employee` | `EMPLOYMENT_DECISION` | `BLOCK` |",
    ]:
        assert row in text

    for required in [
        "Medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradiction must `ESCALATE` or `BLOCK` under caregiver boundary.",
        "Payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions must default to `BLOCK` unless a future explicitly authorized policy says otherwise.",
    ]:
        assert required in text


def test_confirmable_external_actions_require_action_packets():
    text = read_92p_docs()

    for row in [
        "| `send_email` | `SEND_EXTERNAL_MESSAGE` | `ASK_CONFIRMATION` |",
        "| `write_ticket` | `WRITE_EXTERNAL_RECORD` | `ASK_CONFIRMATION` |",
        "| `publish_post` | `PUBLISH` | `ASK_CONFIRMATION` |",
        "| `book_vendor` | `SCHEDULE_WITH_THIRD_PARTY` | `ASK_CONFIRMATION` |",
        "| `update_crm` | `MODIFY_CRM` | `ASK_CONFIRMATION` |",
        "| `stamp_signature` | `PLACE_VISUAL_SIGNATURE` | `ASK_CONFIRMATION` |",
    ]:
        assert row in text

    assert "Every `ASK_CONFIRMATION` must produce an Action Packet." in text
