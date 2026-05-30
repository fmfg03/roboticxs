from __future__ import annotations

from app.safety import evaluate_safety


def test_safety_blocks_payments():
    result = evaluate_safety("Please pay this invoice today", "BLOCK")
    assert result["decision"] == "BLOCK"


def test_safety_requires_confirmation_for_external_send():
    result = evaluate_safety("Send this follow-up email to Victor", "ANSWER")
    assert result["decision"] == "ASK_CONFIRMATION"


def test_safety_escalates_professional_advice():
    result = evaluate_safety("I need tax advice for this expense", "REFUSE_SCOPE")
    assert result["decision"] == "ESCALATE"
