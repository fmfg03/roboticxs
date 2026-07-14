from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_COMMAND_SURFACE_POLICY_v0_1.md"
BLOCKLIST_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_HERMES_RAW_COMMAND_BLOCKLIST_v0_1.md"
ALIASES_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_CONSUMER_COMMAND_ALIASES_v0_1.md"


def read_90p_docs() -> str:
    return "\n".join(
        [
            POLICY_DOC.read_text(),
            BLOCKLIST_DOC.read_text(),
            ALIASES_DOC.read_text(),
        ]
    )


def test_approve_and_deny_require_action_packets_for_sensitive_actions():
    text = read_90p_docs()

    for required in [
        "`/approve` and `/deny` must not approve sensitive actions by raw text alone.",
        "Sensitive approvals require an Action Packet",
        "Refuse sensitive approval without Action Packet.",
        "Refuse sensitive denial without Action Packet reference when applicable.",
        "Approving or denying a sensitive action without an Action Packet is consumer-blocked",
    ]:
        assert required in text


def test_action_packet_contract_contains_authority_cost_audit_and_fallback_fields():
    text = read_90p_docs()

    for field in [
        "action id",
        "user-visible action summary",
        "actor and target",
        "authority boundary",
        "expected external effect",
        "cost or wake implication",
        "audit record location",
        "safe fallback or denial outcome",
    ]:
        assert field in text


def test_zaubern_lite_remains_action_authority_for_sensitive_effects():
    text = read_90p_docs()

    assert "Zaubern-lite remains action authority." in text
    assert "Zaubern-lite Action Packet" in text
    assert "Sensitive actions require Action Packets." in text
