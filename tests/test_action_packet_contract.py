from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_ACTION_PACKET_CONTRACT_v0_1.md"


def test_action_packet_contract_doc_exists_and_is_tied_to_ask_confirmation():
    text = PACKET_DOC.read_text()

    assert PACKET_DOC.is_file()
    assert "Status: 92P implemented pending review." in text
    assert "Every `ASK_CONFIRMATION` must produce an Action Packet before any execution." in text
    assert "A confirmation command without an Action Packet is not enough." in text


def test_action_packet_required_fields_are_complete():
    text = PACKET_DOC.read_text()

    for field in [
        "`action`",
        "`target`",
        "`data_to_be_changed_or_sent`",
        "`risk_class`",
        "`source_context`",
        "`estimated_cost`",
        "`allowed_alternatives`",
        "`confirmation_options`",
        "`audit_fields`",
    ]:
        assert field in text


def test_action_packet_schema_contains_final_user_visible_content():
    text = PACKET_DOC.read_text()

    for required in [
        '"packet_type":"ActionPacket"',
        '"status":"NON_RUNTIME_GOVERNANCE_PACKET"',
        '"stage":"92P"',
        '"action_class":"SEND_EXTERNAL_MESSAGE"',
        '"data_to_be_changed_or_sent"',
        '"subject":"Follow-up on Roboticxs demo"',
        '"body":"Hi Ana, thanks for the call. Here are the next steps we discussed."',
        '"confirmation_options":["confirm_once","revise","draft_only","cancel","escalate"]',
        '"runtime_enforcement_authorized":false',
    ]:
        assert required in text


def test_action_packet_cannot_hide_external_send_publish_or_write_content():
    text = PACKET_DOC.read_text()

    for required in [
        "No action packet may hide the final user-visible content for an external send/publish/write.",
        "The full final message body, publishable content, external write fields, CRM modification, schedule details, or visual signature placement must be visible before confirmation.",
        "If the final content is unknown, hidden, truncated, generated later, or represented only by a summary, the packet is invalid.",
        "`ASK_CONFIRMATION` does not override `BLOCK`; blocked actions must not be converted into Action Packets unless a future explicitly authorized policy changes the block default.",
        "Cost Governor remains spend/wake authority.",
        "Memory Center remains canonical memory.",
        "Zaubern-lite remains authority layer.",
    ]:
        assert required in text
