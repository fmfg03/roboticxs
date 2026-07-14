from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_GUARD_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_ACTIVATION_SCOPE_GUARD_v0_1.md"
)
DECISIONS_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_SCOPE_DECISIONS_v0_1.md"
POLICY_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_UPGRADE_AND_REDIRECT_POLICY_v0_1.md"
)


def read_91p_docs() -> str:
    return "\n".join(
        [
            SCOPE_GUARD_DOC.read_text(),
            DECISIONS_DOC.read_text(),
            POLICY_DOC.read_text(),
        ]
    )


def test_block_takes_precedence_over_redirect_or_upgrade():
    text = read_91p_docs()

    assert "`BLOCK` takes precedence over every other decision." in text
    assert "Return `BLOCK` when the request is prohibited, sensitive without valid authority, or listed in SkillManifest blocked topics/actions." in text


def test_prohibited_sensitive_actions_are_blocked_or_deferred_to_authority():
    text = read_91p_docs()

    for blocked in [
        "legal signing or legal acceptance",
        "executing payments",
        "refunds without authority",
        "credential or permission changes",
        "destructive actions",
        "medical, medication, diagnosis, treatment, dosage, or emergency triage decisions",
        "external sends without Action Packet authority",
    ]:
        assert blocked in text


def test_required_block_examples_are_present():
    text = read_91p_docs()

    for required in [
        "| Documents | Sign this contract legally for me | Legal acceptance/signature authority requested | `BLOCK` |",
        "| Finance/Admin | Execute payment | Payment execution requested | `BLOCK` |",
        "| Caregiver | Should I change the medication dose? | Medication ambiguity or medical decision | `BLOCK` |",
        "Caregiver medication ambiguity returns `BLOCK` with escalation fallback to a caregiver, clinician, or emergency service as appropriate.",
        "`ESCALATE` is not a standalone 91P decision; escalation is response guidance attached to `BLOCK`.",
    ]:
        assert required in text


def test_tool_authority_guard_remains_future_92p_scope():
    text = read_91p_docs()

    for required in [
        "Scope Guard does not replace Tool Authority Guard. Tool Authority Guard comes later in 92P.",
        "Tool permissions are not decided in 91P. Tool Authority Guard is 92P+ and remains unauthorized in this pass.",
        "no Tool Authority Guard",
        "no 92P or later authorization",
    ]:
        assert required in text
