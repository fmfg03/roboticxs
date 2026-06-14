from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_SCOPE_DECISIONS_v0_1.md"


def test_skill_scope_decisions_doc_exists_and_defines_registry():
    text = DECISIONS_DOC.read_text()

    assert DECISIONS_DOC.is_file()
    assert "Status: 91P implemented pending review." in text
    for decision in [
        "| `ANSWER` |",
        "| `CLARIFY` |",
        "| `REDIRECT` |",
        "| `OFFER_UPGRADE` |",
        "| `REFUSE_SCOPE` |",
        "| `BLOCK` |",
    ]:
        assert decision in text


def test_skill_scope_decision_precedence_is_explicit():
    text = DECISIONS_DOC.read_text()

    for required in [
        "`BLOCK` takes precedence over every other decision.",
        "`OFFER_UPGRADE` is used for disabled paid-skill requests only when the request is not prohibited.",
        "`REDIRECT` is used only when another enabled skill is a better match.",
        "`CLARIFY` is used when the active skill can likely help but needs missing inputs, permission, target, or authority state.",
        "`REFUSE_SCOPE` is used for safe out-of-scope requests when no enabled skill redirect applies.",
        "`ANSWER` is used only when the active skill, package, plan, topic, action class, confirmation state, cost policy, and fallback requirements all permit the response.",
    ]:
        assert required in text


def test_required_example_cases_are_mapped_to_expected_decisions():
    text = DECISIONS_DOC.read_text()

    for row in [
        "| `support_json_no_technical_help` | Customer Support | What is JSON? | `REFUSE_SCOPE` |",
        "| `support_json_technical_help_enabled` | Customer Support | What is JSON? | `REDIRECT` |",
        "| `documents_pdf_summary` | Documents | Summarize this PDF. | `ANSWER` |",
        "| `documents_legal_signature` | Documents | Sign this contract legally for me. | `BLOCK` |",
        "| `sales_followup_draft` | Sales | Draft a follow-up to this lead. | `ANSWER` |",
        "| `sales_send_now` | Sales | Send it now. | `CLARIFY` |",
        "| `marketing_calendar_disabled` | Marketing Pack | Make a content calendar. | `OFFER_UPGRADE` |",
        "| `finance_execute_payment` | Finance/Admin | Execute payment. | `BLOCK` |",
        "| `caregiver_medication_ambiguity` | Caregiver | Should I change the medication dose? | `BLOCK` |",
    ]:
        assert row in text


def test_skill_scope_decisions_preserve_manifest_and_tool_guard_boundaries():
    text = DECISIONS_DOC.read_text()

    for required in [
        "Roboticxs SkillManifest remains the canonical source",
        "Agent Skills `description` may help discover likely skill matches but cannot override SkillManifest scope.",
        "Hermes skill activation may load instructions but cannot grant product permission.",
        "The General Assistant skill is the only role allowed to answer general chatbot questions by default.",
        "Tool permissions are not decided in 91P. Tool Authority Guard is 92P+ and remains unauthorized in this pass.",
    ]:
        assert required in text
