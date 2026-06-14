from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_GUARD_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_SKILL_ACTIVATION_SCOPE_GUARD_v0_1.md"
)


def test_skill_activation_scope_guard_doc_exists_and_is_docs_only_91p():
    text = SCOPE_GUARD_DOC.read_text()

    assert SCOPE_GUARD_DOC.is_file()
    assert "Status: 91P implemented pending review." in text
    for non_claim in [
        "no live runtime routing",
        "no gateway changes",
        "no production enforcement code",
        "no payment/subscription logic",
        "no Tool Authority Guard",
        "no UI",
        "no 92P or later authorization",
    ]:
        assert non_claim in text


def test_skill_activation_scope_guard_decision_vocabulary_is_complete():
    text = SCOPE_GUARD_DOC.read_text()

    for decision in [
        "`ANSWER`",
        "`CLARIFY`",
        "`REDIRECT`",
        "`OFFER_UPGRADE`",
        "`REFUSE_SCOPE`",
        "`BLOCK`",
    ]:
        assert decision in text


def test_skill_activation_scope_guard_preserves_authority_invariants():
    text = SCOPE_GUARD_DOC.read_text()

    for invariant in [
        "Roboticxs SkillManifest remains canonical for scope, package, plan, confirmation, blocked actions, escalation, fallback, and upgrade paths.",
        "Agent Skills `description` helps discovery but does not decide authority.",
        "Hermes skill activation is runtime capability, not product permission.",
        "A skill may answer only if the user request fits enabled package scope and allowed topics/actions.",
        "A skill must not answer general chatbot questions while operating inside a role skill unless the General Assistant skill is active.",
        "Disabled paid-skill requests must return `OFFER_UPGRADE`, not fake capability.",
        "Requests belonging to another enabled skill must return `REDIRECT`.",
        "Ambiguous in-scope requests must return `CLARIFY`.",
        "Out-of-scope but non-dangerous requests must return `REFUSE_SCOPE` with safe fallback.",
        "Prohibited/sensitive actions must return `BLOCK` or defer to Zaubern-lite authority rules.",
        "Scope Guard does not replace Tool Authority Guard. Tool Authority Guard comes later in 92P.",
        "Memory Center remains canonical memory.",
        "Cost Governor remains spend/wake authority.",
    ]:
        assert invariant in text


def test_skill_activation_scope_packet_is_non_runtime_governance_only():
    text = SCOPE_GUARD_DOC.read_text()

    for required in [
        '"packet_type":"SkillActivationScopePacket"',
        '"status":"NON_RUNTIME_GOVERNANCE_PACKET"',
        '"stage":"91P"',
        '"decision":"ANSWER"',
        '"authority_source":"Roboticxs SkillManifest"',
        '"runtime_enforcement_authorized":false',
    ]:
        assert required in text
