from __future__ import annotations

from app.skill_manifest_runtime_gates import (
    SKILL_MANIFEST_RUNTIME_GATES_STAGE,
    build_default_skill_runtime_manifests,
    classify_command_for_skill_gate,
    classify_skill_runtime_gate,
    map_command_to_skill,
    render_skill_runtime_gate_decision,
    render_skill_runtime_manifest_summary,
    SkillRuntimeGateRequest,
)


def test_189p_default_manifests_cover_customer_product_skills():
    manifests = build_default_skill_runtime_manifests()
    by_id = {manifest.skill_id: manifest for manifest in manifests}

    assert set(by_id) == {
        "basic",
        "setup",
        "daily_brief",
        "meetings",
        "documents",
        "memory",
        "gmail_drafts",
        "usage",
    }
    assert all(manifest.stage == SKILL_MANIFEST_RUNTIME_GATES_STAGE for manifest in manifests)
    assert all(manifest.commands for manifest in manifests)
    assert all(manifest.allowed_action_classes for manifest in manifests)
    assert all(manifest.safe_fallback for manifest in manifests)


def test_189p_maps_main_telegram_commands_to_skill_manifests():
    expected = {
        "/start": "basic",
        "/help": "basic",
        "/pilot": "basic",
        "/pilot_pack": "basic",
        "/pilot_audit": "basic",
        "/live_smoke": "basic",
        "/founder_loop": "basic",
        "/feedback": "basic",
        "/feedback_ledger": "basic",
        "/founder_outcome": "basic",
        "/suggestion_quality": "meetings",
        "/prep_quality": "meetings",
        "/status": "setup",
        "/checkup": "setup",
        "/setup": "setup",
        "/today": "daily_brief",
        "/daily_brief": "daily_brief",
        "/prep": "meetings",
        "/document": "documents",
        "/memory": "memory",
        "/memory_review": "memory",
        "/memory_approve": "memory",
        "/memory_wrong": "memory",
        "/memory_stale": "memory",
        "/memory_duplicate": "memory",
        "/memory_merge": "memory",
        "/memory_never_use": "memory",
        "/drafts": "gmail_drafts",
        "/draft_approve": "gmail_drafts",
        "/draft_revise": "gmail_drafts",
        "/export_email": "gmail_drafts",
        "/usage": "usage",
    }

    for command, skill_id in expected.items():
        assert map_command_to_skill(command) == skill_id


def test_189p_known_command_answers_inside_skill_boundary_without_authority():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/usage",
        raw_text="/usage",
    )

    assert record.decision == "ANSWER"
    assert record.skill_id == "usage"
    assert record.execution_authorized is False
    assert record.external_write_allowed is False
    assert record.connector_activation_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False


def test_189p_targeted_command_without_target_clarifies():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/prep",
        raw_text="/prep",
    )

    assert record.decision == "CLARIFY"
    assert record.skill_id == "meetings"
    assert record.reason_code == "command_requires_target_argument"


def test_189p_active_skill_redirects_to_command_owner_skill():
    record = classify_skill_runtime_gate(
        SkillRuntimeGateRequest(
            owner_id="owner-189p",
            robot_id="robot-189p",
            command="/prep",
            raw_text="/prep suggestion-123",
            active_skill_id="basic",
        )
    )

    assert record.decision == "REDIRECT"
    assert record.skill_id == "basic"
    assert record.target_skill_id == "meetings"


def test_189p_unknown_paid_area_offers_upgrade_without_claiming_execution():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/crm",
        raw_text="/crm update this lead",
    )

    assert record.decision == "OFFER_UPGRADE"
    assert record.execution_authorized is False
    assert record.external_write_allowed is False


def test_189p_safe_unknown_command_refuses_scope():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/weather",
        raw_text="/weather tomorrow",
    )

    assert record.decision == "REFUSE_SCOPE"
    assert record.skill_id == "basic"


def test_189p_sensitive_or_destructive_request_blocks():
    record = classify_skill_runtime_gate(
        SkillRuntimeGateRequest(
            owner_id="owner-189p",
            robot_id="robot-189p",
            command="/document",
            raw_text="/document sign this contract legally",
            requested_action_class="LEGAL_ACCEPTANCE",
        )
    )

    assert record.decision == "BLOCK"
    assert record.blocked is True
    assert record.calendar_write_allowed is False
    assert record.gmail_send_allowed is False
    assert record.memory_center_mutation_allowed is False


def test_189p_gmail_draft_command_requires_confirmation_without_send_permission():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/export_email",
        raw_text="/export_email confirmation-123",
    )

    assert record.decision == "ANSWER"
    assert record.skill_id == "gmail_drafts"
    assert record.requires_confirmation is True
    assert "WRITE_EXTERNAL_RECORD" in record.confirmation_required_actions
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False


def test_189p_rendered_gate_and_summary_are_secret_free():
    record = classify_command_for_skill_gate(
        owner_id="owner-189p",
        robot_id="robot-189p",
        command="/unknown",
        raw_text="/unknown",
    )
    rendered = render_skill_runtime_gate_decision(record)
    summary = "\n".join(render_skill_runtime_manifest_summary())

    assert "Skill Runtime Gate" in rendered
    assert "Execution authorized: false" in rendered
    assert "External writes: disabled" in rendered
    assert "Gmail send/modify: disabled" in rendered
    assert "secret" not in rendered.lower()
    assert "- Gmail Drafts:" in summary
