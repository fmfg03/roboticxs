from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD_DOC = (
    REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_TOOL_AUTHORITY_GUARD_v0_1.md"
)


def test_hermes_tool_authority_guard_doc_exists_and_is_docs_only_92p():
    text = GUARD_DOC.read_text()

    assert GUARD_DOC.is_file()
    assert "Status: 92P implemented pending review." in text
    for non_claim in [
        "no live Hermes interception",
        "no gateway changes",
        "no production enforcement code",
        "no MCP/plugin activation",
        "no connector activation",
        "no UI",
        "no live external action execution",
        "no 93P or later authorization",
    ]:
        assert non_claim in text


def test_tool_authority_guard_decision_vocabulary_is_complete():
    text = GUARD_DOC.read_text()

    for decision in [
        "`ALLOW`",
        "`DRAFT_ONLY`",
        "`ASK_CONFIRMATION`",
        "`ESCALATE`",
        "`BLOCK`",
    ]:
        assert decision in text


def test_tool_authority_guard_preserves_authority_invariants():
    text = GUARD_DOC.read_text()

    for invariant in [
        "Hermes tool availability is capability, not permission.",
        "Agent Skills instructions are not authority.",
        "Scope Guard does not authorize execution; it only decides skill participation.",
        "Tool Authority Guard runs after skill activation and before any sensitive action.",
        "Safe read/search/summarize/classify/draft actions may be `ALLOW` when within enabled scope and budget.",
        "External sends, writes, publishing, third-party scheduling, CRM modification, and visual signatures require `ASK_CONFIRMATION` or stronger.",
        "Payments, refunds, credential changes, permission changes, legal acceptance, production deploys, destructive actions, and professional decisions must default to `BLOCK` unless a future explicitly authorized policy says otherwise.",
        "Medication ambiguity, dosage, missed dose, duplicate dose, side effects, or contradiction must `ESCALATE` or `BLOCK` under caregiver boundary.",
        "Every `ASK_CONFIRMATION` must produce an Action Packet.",
        "No action packet may hide the final user-visible content for an external send/publish/write.",
        "Cost Governor remains spend/wake authority.",
        "Memory Center remains canonical memory.",
        "Zaubern-lite remains authority layer.",
        "93P+ must remain not authorized.",
    ]:
        assert invariant in text


def test_tool_authority_guard_packet_is_non_runtime_governance_only():
    text = GUARD_DOC.read_text()

    for required in [
        '"packet_type":"ToolAuthorityGuardPacket"',
        '"status":"NON_RUNTIME_GOVERNANCE_PACKET"',
        '"stage":"92P"',
        '"proposed_action_class":"SEND_EXTERNAL_MESSAGE"',
        '"decision":"ASK_CONFIRMATION"',
        '"requires_action_packet":true',
        '"runtime_enforcement_authorized":false',
        '"future_stage_authorized":false',
    ]:
        assert required in text
