from __future__ import annotations

from app.scope_guard import decide_scope
from app.skills import load_skill_manifest_file


def test_scope_guard_answers_meeting_requests():
    manifest = load_skill_manifest_file()
    assert decide_scope("Help me prepare for my meeting tomorrow", manifest) == "ANSWER"


def test_scope_guard_refuses_professional_advice():
    manifest = load_skill_manifest_file()
    assert decide_scope("I need legal advice for this contract", manifest) == "REFUSE_SCOPE"


def test_scope_guard_blocks_account_actions():
    manifest = load_skill_manifest_file()
    assert decide_scope("Delete my account right now", manifest) == "BLOCK"
