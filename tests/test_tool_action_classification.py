from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATION_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_TOOL_ACTION_CLASSIFICATION_v0_1.md"
)


REQUIRED_ACTION_CLASSES = [
    "READ",
    "SEARCH",
    "SUMMARIZE",
    "CLASSIFY",
    "DRAFT",
    "ROUTE",
    "REMIND",
    "SCHEDULE_SELF",
    "SEND_EXTERNAL_MESSAGE",
    "WRITE_EXTERNAL_RECORD",
    "PUBLISH",
    "SCHEDULE_WITH_THIRD_PARTY",
    "MODIFY_CRM",
    "PLACE_VISUAL_SIGNATURE",
    "PAY",
    "REFUND",
    "DELETE",
    "CHANGE_CREDENTIALS",
    "CHANGE_PERMISSIONS",
    "LEGAL_ACCEPT",
    "PRODUCTION_DEPLOY",
    "DESTRUCTIVE_ACTION",
    "MEDICAL_DECISION",
    "LEGAL_DECISION",
    "TAX_DECISION",
    "FINANCIAL_DECISION",
    "EMPLOYMENT_DECISION",
]


def test_tool_action_classification_doc_exists_and_lists_required_classes():
    text = CLASSIFICATION_DOC.read_text()

    assert CLASSIFICATION_DOC.is_file()
    assert "Status: 92P implemented pending review." in text
    for action_class in REQUIRED_ACTION_CLASSES:
        assert f"| `{action_class}` |" in text


def test_safe_local_action_classes_default_to_allow_or_draft_only():
    text = CLASSIFICATION_DOC.read_text()

    for row in [
        "| `READ` | Read local or already-authorized context without changing state. | `ALLOW` |",
        "| `SEARCH` | Search within allowed local or approved request-scoped sources. | `ALLOW` |",
        "| `SUMMARIZE` | Summarize allowed input without changing state. | `ALLOW` |",
        "| `CLASSIFY` | Classify allowed input without changing state. | `ALLOW` |",
        "| `DRAFT` | Draft content or proposed changes without execution. | `ALLOW` |",
        "| `ROUTE` | Route internally without external side effects. | `ALLOW` |",
        "| `REMIND` | Prepare a reminder or local reminder draft. | `DRAFT_ONLY` |",
        "| `SCHEDULE_SELF` | Prepare a personal schedule entry that remains local and user-controlled. | `DRAFT_ONLY` |",
    ]:
        assert row in text


def test_external_state_changing_actions_require_confirmation():
    text = CLASSIFICATION_DOC.read_text()

    for action_class in [
        "SEND_EXTERNAL_MESSAGE",
        "WRITE_EXTERNAL_RECORD",
        "PUBLISH",
        "SCHEDULE_WITH_THIRD_PARTY",
        "MODIFY_CRM",
        "PLACE_VISUAL_SIGNATURE",
    ]:
        assert f"| `{action_class}` |" in text
        assert f"| `{action_class}` |" in text and " | `ASK_CONFIRMATION` |" in text


def test_blocked_and_professional_classes_default_to_block_or_escalate():
    text = CLASSIFICATION_DOC.read_text()

    for action_class in [
        "PAY",
        "REFUND",
        "DELETE",
        "CHANGE_CREDENTIALS",
        "CHANGE_PERMISSIONS",
        "LEGAL_ACCEPT",
        "PRODUCTION_DEPLOY",
        "DESTRUCTIVE_ACTION",
        "LEGAL_DECISION",
        "TAX_DECISION",
        "FINANCIAL_DECISION",
        "EMPLOYMENT_DECISION",
    ]:
        assert f"| `{action_class}` |" in text
        assert f"| `{action_class}` |" in text and " | `BLOCK` |" in text

    assert "| `MEDICAL_DECISION` |" in text
    assert "| `MEDICAL_DECISION` | Medical, medication, diagnosis, treatment, dosage, side-effect, or emergency decision. | `ESCALATE` |" in text
    assert "When one proposed action fits multiple classes, choose the most restrictive decision." in text
