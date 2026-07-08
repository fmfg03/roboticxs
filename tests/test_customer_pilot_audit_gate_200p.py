from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.customer_pilot_audit_gate import (
    CUSTOMER_PILOT_AUDIT_GATE_STAGE,
    CUSTOMER_PILOT_AUDIT_GATE_STATUS,
    CustomerPilotAuditGateReport,
    build_customer_pilot_audit_gate,
    render_customer_pilot_audit_gate,
)
from app.runnable_telegram_robot_mvp import TelegramRobotConfig, render_command_reply


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CUSTOMER_PILOT_AUDIT_GATE_200P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_200p_builds_complete_customer_pilot_audit_gate():
    report = build_customer_pilot_audit_gate(owner_id="owner-200p", robot_id="robot-200p")

    assert report.stage == CUSTOMER_PILOT_AUDIT_GATE_STAGE
    assert report.status == CUSTOMER_PILOT_AUDIT_GATE_STATUS
    assert len(report.criteria) == 10
    assert [criterion.criterion_id for criterion in report.criteria] == [
        "pilot_pack",
        "daily_brief_context",
        "prep_context",
        "source_trace",
        "cost_routing",
        "suggestion_priority",
        "draft_quality",
        "document_actions",
        "gmail_draft_only",
        "blocked_writes",
    ]
    assert all(criterion.status == "PASS" for criterion in report.criteria)
    assert report.residue_policy == "ignored_generated_scratch"
    assert "roboticxs_artifacts/loop_handoffs/" in report.residue_evidence
    assert report.local_audit_only is True
    assert report.gmail_send_allowed is False
    assert report.gmail_modify_allowed is False
    assert report.calendar_write_allowed is False
    assert report.crm_write_allowed is False
    assert report.whatsapp_allowed is False
    assert report.external_write_allowed is False
    assert report.secrets_redacted is True
    assert report.approval_gate_preserved is True
    assert report.source_trace_preserved is True
    assert report.usage_cost_receipt_visible is True


def test_200p_rendered_audit_gate_shows_all_required_customer_pilot_checks():
    rendered = render_customer_pilot_audit_gate(
        build_customer_pilot_audit_gate(owner_id="owner-200p", robot_id="robot-200p")
    )

    for expected in [
        "Customer Pilot Audit Gate",
        "Stage: 200P",
        "PASS - /pilot_pack exists and guides the demo.",
        "PASS - /daily_brief uses real context or explicit fallback.",
        "PASS - /prep uses Calendar + Gmail + Memory when available.",
        "PASS - Source trace appears in important outputs.",
        "PASS - Cost/routing receipt appears where appropriate.",
        "PASS - Suggestions have priority and reason.",
        "PASS - Drafts have quality metadata.",
        "PASS - Document review proposes safe actions.",
        "PASS - Gmail draft creation remains draft-only.",
        "PASS - Unsafe external writes remain blocked.",
        "Residue policy:",
        "Gmail send: disabled",
        "Calendar writes: disabled",
        "CRM writes: disabled",
        "WhatsApp: disabled",
        "Usage/cost receipt: visible",
    ]:
        assert expected in rendered


def test_200p_telegram_pilot_audit_command_is_customer_visible_without_external_writes():
    report = build_customer_pilot_audit_gate(owner_id="local-owner", robot_id="roboticxs-dev")

    rendered = render_command_reply(
        command="/pilot_audit",
        config=TelegramRobotConfig(
            bot_token="token-200p",
            owner_ids=frozenset({111111111}),
            robot_id="roboticxs-dev",
            owner_id="local-owner",
            poll_timeout_seconds=30,
            poll_limit=10,
            dry_run=False,
            dev_mode=True,
        ),
        customer_pilot_audit_gate=report,
    )

    assert "Customer Pilot Audit Gate" in rendered
    assert "Stage: 200P" in rendered
    assert "External writes: disabled" in rendered
    assert "Approval gate: preserved" in rendered


def test_200p_rejects_failed_criteria_or_authority_expansion():
    report = build_customer_pilot_audit_gate(owner_id="owner-200p", robot_id="robot-200p")
    failed_criterion = replace(report.criteria[0], status="FAIL")

    with pytest.raises(ValueError, match="only closes when every criterion passes"):
        replace(report, criteria=(failed_criterion, *report.criteria[1:]))
    with pytest.raises(ValueError, match="must not expand external action authority"):
        replace(report, calendar_write_allowed=True)
    with pytest.raises(ValueError, match="requires redaction"):
        replace(report, secrets_redacted=False)


def test_200p_ignores_generated_loop_handoffs_instead_of_leaving_residue_ambiguous():
    gitignore = (REPO_ROOT / ".gitignore").read_text()

    assert "roboticxs_artifacts/loop_handoffs/" in gitignore


def test_200p_reference_and_roadmap_close_audit_gate_without_writes():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "200P audits whether 190P-199P form a usable, safe, and demonstrable controlled pilot loop." in reference
    assert "Generated local loop handoffs" in reference
    assert "does not authorize Gmail send" in reference
    assert '"stage_id":"200P","stage_name":"Customer Pilot Audit Gate v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "222P and later remain unauthorized" in roadmap
